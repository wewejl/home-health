import Foundation
import UIKit
import Combine

/// 消息管理服务
/// 负责：消息列表管理、发送消息、图片处理
@MainActor
class ChatMessageService: ObservableObject {
    // MARK: - 消息状态
    @Published var messages: [UnifiedChatMessage] = []
    @Published var isSending = false
    @Published var isUploadingImage = false
    @Published var isAnalyzing = false

    // MARK: - 流式输出
    @Published var streamingContent = ""
    @Published var streamingMessageId: UUID?

    // MARK: - 错误处理
    @Published var errorMessage: String?
    @Published var showError = false

    // MARK: - 当前动作模式
    @Published var currentActionMode: AgentAction?

    // MARK: - 诊断展示增强状态
    @Published var adviceHistory: [AdviceEntry] = []
    @Published var diagnosisCard: AgentDiagnosisCard?
    @Published var knowledgeRefs: [KnowledgeRef] = []
    @Published var reasoningSteps: [String] = []

    // MARK: - 内存管理
    private let maxMessageCount = 200
    private let maxImageMessagesInMemory = 10

    // MARK: - 私有属性
    private let apiService = APIService.shared
    private let localImageManager = LocalImageManager.shared

    // MARK: - 消息管理

    func loadHistoryMessages(_ historyMessages: [MessageModel], sessionId: String?) {
        messages.removeAll()

        var loadedImageCount = 0

        for msg in historyMessages {
            var message = UnifiedChatMessage(
                content: msg.content,
                isFromUser: msg.sender == "user",
                timestamp: msg.created_at,
                serverMessageId: msg.id
            )

            if msg.message_type == "image" && loadedImageCount < maxImageMessagesInMemory {
                if let sessionId = sessionId {
                    let localImages = localImageManager.getImages(forSession: sessionId)
                    if let matchingImage = localImages.first(where: { abs($0.createdAt.timeIntervalSince(msg.created_at)) < 60 }),
                       let image = localImageManager.loadImage(byId: matchingImage.id) {
                        message.messageType = .image(image)
                        message.localImageId = matchingImage.id
                        loadedImageCount += 1
                    }
                }
            }

            messages.append(message)
        }

        print("[ChatMessageService] 加载历史消息: \(messages.count) 条（图片: \(loadedImageCount) 张）")
    }

    func clearMessages() {
        messages.removeAll()
    }

    // MARK: - 发送消息

    func sendMessage(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async {
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !attachments.isEmpty else { return }

        // 清除快捷选项
        for index in messages.indices {
            messages[index].quickOptions = []
        }

        // 添加用户消息
        let userMessage = UnifiedChatMessage.userMessage(content, attachments: attachments)
        messages.append(userMessage)

        trimMessagesIfNeeded()

        isSending = true

        let loadingMessage = UnifiedChatMessage.loadingMessage()
        streamingMessageId = loadingMessage.id
        streamingContent = ""
        messages.append(loadingMessage)

        await apiService.sendUnifiedMessageStreaming(
            sessionId: sessionId,
            content: content,
            attachments: attachments,
            action: action,
            onChunk: { [weak self] chunk in
                Task { @MainActor in self?.handleChunk(chunk) }
            },
            onComplete: { [weak self] response in
                Task { @MainActor in self?.handleComplete(response) }
            },
            onError: { [weak self] error in
                Task { @MainActor in self?.handleStreamError(error) }
            }
        )
    }

    // MARK: - 图片处理

    func handleSelectedImage(_ image: UIImage, sessionId: String, action: AgentAction) async {
        isUploadingImage = true

        do {
            let processedImage = resizeImageIfNeeded(image, maxDimension: 2048)

            let imageRecord = localImageManager.saveImage(
                processedImage,
                sessionId: sessionId,
                note: action.uploadDescription
            )

            let imageMessage = UnifiedChatMessage.imageMessage(
                processedImage,
                content: action.uploadDescription,
                localImageId: imageRecord?.id
            )
            messages.append(imageMessage)

            guard let imageData = processedImage.jpegData(compressionQuality: 0.7) else {
                throw APIError.serverError("图片处理失败")
            }

            let maxSize = 5 * 1024 * 1024
            if imageData.count > maxSize {
                throw APIError.serverError("图片过大，请选择小于5MB的图片")
            }

            let base64String = imageData.base64EncodedString()
            let attachment = MessageAttachment.imageAttachment(base64: base64String)

            isUploadingImage = false
            isAnalyzing = true

            let loadingId = UUID()
            streamingMessageId = loadingId
            streamingContent = ""
            let loadingMessage = UnifiedChatMessage(
                id: loadingId,
                content: "正在分析中...",
                isFromUser: false,
                messageType: .loading
            )
            messages.append(loadingMessage)

            await apiService.sendUnifiedMessageStreaming(
                sessionId: sessionId,
                content: action.analysisPrompt,
                attachments: [attachment],
                action: action,
                onChunk: { [weak self] chunk in
                    Task { @MainActor in self?.handleChunk(chunk) }
                },
                onComplete: { [weak self] response in
                    Task { @MainActor in self?.handleAnalysisComplete(response) }
                },
                onError: { [weak self] error in
                    Task { @MainActor in self?.handleAnalysisError(error) }
                }
            )
        } catch {
            isUploadingImage = false
            handleError(error)
        }
    }

    private func resizeImageIfNeeded(_ image: UIImage, maxDimension: CGFloat) -> UIImage {
        let size = image.size
        if size.width <= maxDimension && size.height <= maxDimension {
            return image
        }

        let ratio = min(maxDimension / size.width, maxDimension / size.height)
        let newSize = CGSize(width: size.width * ratio, height: size.height * ratio)

        UIGraphicsBeginImageContextWithOptions(newSize, false, 1.0)
        image.draw(in: CGRect(origin: .zero, size: newSize))
        let resizedImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()

        return resizedImage ?? image
    }

    // MARK: - 流式响应处理

    private func handleChunk(_ chunk: String) {
        streamingContent += chunk

        if let id = streamingMessageId,
           let index = messages.firstIndex(where: { $0.id == id }) {
            messages[index] = UnifiedChatMessage(
                id: id,
                content: streamingContent,
                isFromUser: false,
                messageType: .text
            )
        }
    }

    private func handleComplete(_ response: UnifiedMessageResponse) {
        streamingMessageId = nil
        streamingContent = ""
        isSending = false

        if let lastIndex = messages.indices.last,
           !messages[lastIndex].isFromUser {
            let quickOpts = (response.quickOptions ?? []).map { QuickOption(text: $0, value: $0) }
            // 🆕 传入思考状态
            messages[lastIndex] = UnifiedChatMessage(
                content: response.message,
                isFromUser: false,
                messageType: .text,
                quickOptions: quickOpts,
                thinkingState: response.thinkingState
            )
        }

        updateDiagnosticFields(from: response)
    }

    private func handleAnalysisComplete(_ response: UnifiedMessageResponse) {
        if let messageId = streamingMessageId {
            messages.removeAll { $0.id == messageId }
        }

        streamingMessageId = nil
        streamingContent = ""
        isAnalyzing = false
        currentActionMode = nil

        let quickOpts = (response.quickOptions ?? []).map { QuickOption(text: $0, value: $0) }
        // 🆕 传入思考状态
        let resultMessage = UnifiedChatMessage(
            content: response.message,
            isFromUser: false,
            messageType: response.structuredData != nil
                ? .structuredResult(response.structuredData!)
                : .text,
            quickOptions: quickOpts,
            thinkingState: response.thinkingState
        )
        messages.append(resultMessage)

        updateDiagnosticFields(from: response)
    }

    private func handleStreamError(_ error: Error) {
        isSending = false
        streamingMessageId = nil
        handleError(error)
    }

    private func handleAnalysisError(_ error: Error) {
        if let messageId = streamingMessageId {
            messages.removeAll { $0.id == messageId }
        }

        streamingMessageId = nil
        streamingContent = ""
        isAnalyzing = false

        handleError(error)
    }

    private func updateDiagnosticFields(from response: UnifiedMessageResponse) {
        if let history = response.adviceHistory {
            adviceHistory = history
        }
        if let card = response.diagnosisCard {
            // 转换 DiagnosisCard 到 AgentDiagnosisCard
            diagnosisCard = AgentDiagnosisCard(
                summary: card.summary,
                conditions: card.conditions.map { condition in
                    AgentDiagnosisCondition(name: condition.name, confidence: condition.confidence, rationale: condition.rationale)
                },
                riskLevel: card.riskLevel,
                needOfflineVisit: card.needOfflineVisit,
                urgency: card.urgency,
                carePlan: card.carePlan,
                references: card.references,
                reasoningSteps: card.reasoningSteps
            )
        }
        if let refs = response.knowledgeRefs {
            knowledgeRefs = refs
        }
        if let steps = response.reasoningSteps {
            reasoningSteps = steps
        }
    }

    // MARK: - 内存管理

    private func trimMessagesIfNeeded() {
        let imageMessages = messages.filter { isImageMessage($0) }
        if imageMessages.count > maxImageMessagesInMemory {
            let excessImageCount = imageMessages.count - maxImageMessagesInMemory
            var imagesToRemove = Set<UUID>()
            for msg in imageMessages.prefix(excessImageCount) {
                imagesToRemove.insert(msg.id)
            }
            messages.removeAll { imagesToRemove.contains($0.id) }
        }

        if messages.count > maxMessageCount {
            let excessCount = messages.count - maxMessageCount
            messages.removeFirst(excessCount)
        }
    }

    private func isImageMessage(_ message: UnifiedChatMessage) -> Bool {
        if case .image = message.messageType {
            return true
        }
        return false
    }

    // MARK: - 辅助方法

    func canGenerateDossier(isConversationCompleted: Bool) -> Bool {
        if isConversationCompleted { return true }
        guard messages.count >= 5 else { return false }
        let userMessages = messages.filter { $0.isFromUser }
        return userMessages.count >= 3
    }

    func dossierButtonTooltip(canGenerate: Bool) -> String {
        if canGenerate {
            return "根据本次对话生成结构化病历"
        } else {
            return "请继续对话收集更多信息后再生成病历（至少需要3轮对话）"
        }
    }

    func handleError(_ error: Error) {
        if let apiError = error as? APIError {
            errorMessage = apiError.errorDescription
        } else {
            errorMessage = "发生错误，请重试"
        }
        showError = true
    }
}
