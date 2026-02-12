import Foundation
import Combine
import UIKit

/// 消息管理 ViewModel
/// 负责：消息列表管理、发送消息、图片处理、流式输出
@MainActor
class ChatMessageViewModel: ObservableObject {
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

    // MARK: - 高风险警告
    @Published var showRiskAlert = false
    @Published var riskAlertMessage = ""

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

    /// 加载历史消息
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

            // 如果消息是图片类型，尝试从本地加载（限制数量）
            if msg.message_type == "image" && loadedImageCount < maxImageMessagesInMemory {
                if let sessionId = sessionId {
                    let localImages = localImageManager.getImages(forSession: sessionId)
                    // 按时间匹配最近的图片
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

        print("[ChatMessageVM] 加载历史消息: \(messages.count) 条（图片: \(loadedImageCount) 张）")
    }

    /// 清空消息
    func clearMessages() {
        messages.removeAll()
    }

    // MARK: - 发送消息

    /// 发送文本消息
    func sendMessage(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async {
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !attachments.isEmpty else { return }

        // 清除之前所有消息的快捷选项
        for index in messages.indices {
            messages[index].quickOptions = []
        }

        // 添加用户消息
        let userMessage = UnifiedChatMessage.userMessage(content, attachments: attachments)
        messages.append(userMessage)

        // 内存管理：如果消息数量超过限制，删除最旧的消息
        trimMessagesIfNeeded()

        isSending = true

        // 创建流式加载消息
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

    /// 处理选中的图片
    func handleSelectedImage(_ image: UIImage, sessionId: String, action: AgentAction) async {
        guard let action = currentActionMode else {
            print("[ChatMessageVM] ❌ currentActionMode 为 nil, 无法处理图片")
            return
        }

        print("[ChatMessageVM] ✅ 开始处理图片, action: \(action.rawValue)")
        isUploadingImage = true

        do {
            // 1. 图片尺寸检查和缩放
            let processedImage = resizeImageIfNeeded(image, maxDimension: 2048)

            // 2. 保存图片到本地
            let imageRecord = localImageManager.saveImage(
                processedImage,
                sessionId: sessionId,
                note: action.uploadDescription
            )

            // 3. 插入用户图片消息 (带本地ID)
            let imageMessage = UnifiedChatMessage.imageMessage(
                processedImage,
                content: action.uploadDescription,
                localImageId: imageRecord?.id
            )
            messages.append(imageMessage)

            // 4. 将图片转为 base64
            guard let imageData = processedImage.jpegData(compressionQuality: 0.7) else {
                throw APIError.serverError("图片处理失败")
            }

            // 5. 检查文件大小 (最大 5MB)
            let maxSize = 5 * 1024 * 1024
            if imageData.count > maxSize {
                throw APIError.serverError("图片过大，请选择小于5MB的图片")
            }

            let base64String = imageData.base64EncodedString()
            let attachment = MessageAttachment.imageAttachment(base64: base64String)

            print("[ChatMessageVM] 📦 图片处理完成 - 大小: \(imageData.count) bytes")

            isUploadingImage = false
            isAnalyzing = true

            // 添加加载中消息
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

            // 发送分析请求
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

    /// 图片尺寸缩放
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

        print("[ChatMessageVM] 图片已缩放: \(size) -> \(newSize)")
        return resizedImage ?? image
    }

    // MARK: - 流式响应处理

    private func handleChunk(_ chunk: String) {
        streamingContent += chunk

        // 更新流式消息
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

    private func handleComplete(_ response: AgentResponse) {
        streamingMessageId = nil
        streamingContent = ""
        isSending = false

        // 替换为最终消息
        if let lastIndex = messages.indices.last,
           !messages[lastIndex].isFromUser {
            messages[lastIndex] = UnifiedChatMessage(
                content: response.message,
                isFromUser: false,
                messageType: .text,
                quickOptions: response.quickOptions ?? []
            )
        }

        // 更新诊断展示增强字段
        updateDiagnosticFields(from: response)

        // 检查对话是否完成
        if response.stage == "completed" || response.shouldShowDossierPrompt == true {
            // 通知会话 ViewModel（通过回调）
        }
    }

    private func handleAnalysisComplete(_ response: AgentResponse) {
        // 移除加载消息
        if let messageId = streamingMessageId {
            messages.removeAll { $0.id == messageId }
        }

        streamingMessageId = nil
        streamingContent = ""
        isAnalyzing = false
        currentActionMode = nil

        // 添加结果消息
        let resultMessage = UnifiedChatMessage(
            content: response.message,
            isFromUser: false,
            messageType: response.structuredData != nil
                ? .structuredResult(response.structuredData!)
                : .text,
            quickOptions: response.quickOptions ?? []
        )
        messages.append(resultMessage)

        // 更新诊断字段
        updateDiagnosticFields(from: response)
    }

    private func handleStreamError(_ error: Error) {
        isSending = false
        streamingMessageId = nil
        handleError(error)
    }

    private func handleAnalysisError(_ error: Error) {
        // 移除加载消息
        if let messageId = streamingMessageId {
            messages.removeAll { $0.id == messageId }
        }

        streamingMessageId = nil
        streamingContent = ""
        isAnalyzing = false

        handleError(error)
    }

    /// 更新诊断展示增强字段
    private func updateDiagnosticFields(from response: UnifiedMessageResponse) {
        if let history = response.adviceHistory {
            adviceHistory = history
        }
        if let card = response.diagnosisCard {
            diagnosisCard = card
        }
        if let refs = response.knowledgeRefs {
            knowledgeRefs = refs
        }
        if let steps = response.reasoningSteps {
            reasoningSteps = steps
        }
    }

    // MARK: - 内存管理

    /// 当消息数量超过限制时，删除最旧的消息
    private func trimMessagesIfNeeded() {
        // 1. 首先检查并限制图片消息数量
        let imageMessages = messages.filter { isImageMessage($0) }
        if imageMessages.count > maxImageMessagesInMemory {
            let excessImageCount = imageMessages.count - maxImageMessagesInMemory
            var imagesToRemove = Set<UUID>()
            for msg in imageMessages.prefix(excessImageCount) {
                imagesToRemove.insert(msg.id)
            }
            messages.removeAll { imagesToRemove.contains($0.id) }
            print("[ChatMessageVM] ⚠️ 删除了 \(excessImageCount) 条旧图片消息")
        }

        // 2. 然后检查总消息数量
        if messages.count > maxMessageCount {
            let excessCount = messages.count - maxMessageCount
            messages.removeFirst(excessCount)
            print("[ChatMessageVM] ⚠️ 删除了 \(excessCount) 条旧消息")
        }
    }

    /// 检查消息是否为图片类型
    private func isImageMessage(_ message: UnifiedChatMessage) -> Bool {
        if case .image = message.messageType {
            return true
        }
        return false
    }

    // MARK: - 辅助方法

    /// 判断是否可以生成病历
    func canGenerateDossier(isConversationCompleted: Bool) -> Bool {
        if isConversationCompleted { return true }
        guard messages.count >= 5 else { return false }
        let userMessages = messages.filter { $0.isFromUser }
        return userMessages.count >= 3
    }

    /// 病历按钮的提示文字
    func dossierButtonTooltip(canGenerate: Bool) -> String {
        if canGenerate {
            return "根据本次对话生成结构化病历"
        } else {
            return "请继续对话收集更多信息后再生成病历（至少需要3轮对话）"
        }
    }

    // MARK: - 错误处理

    func handleError(_ error: Error) {
        if let apiError = error as? APIError {
            errorMessage = apiError.errorDescription
        } else {
            errorMessage = "发生错误，请重试"
        }
        showError = true
    }
}
