import Foundation
import Combine
import UIKit
import AVFoundation

// MARK: - 图片来源类型
enum ImageSourceType {
    case camera
    case photoLibrary
}

// MARK: - 输入模式
/// 输入模式：文字或语音
/// 这个状态保存在 ViewModel 中，确保在整个会话中保持不变
enum InputMode {
    case text   // 文字输入模式
    case voice  // 按住说话模式
}

// MARK: - 统一聊天 ViewModel
/// 能力驱动的统一聊天视图模型
/// 根据智能体能力动态渲染功能按钮，支持多科室适配
@MainActor
class UnifiedChatViewModel: ObservableObject {
    // MARK: - Initialization & Cleanup

    init() {
        // 使用单例语音服务
        // 不需要在这里初始化，因为使用的是单例
        setupVoiceBindings()
    }

    nonisolated deinit {
        print("[UnifiedChatVM] deinit")
        // 不在这里清理 voiceService 回调，因为 deinit 非 @MainActor 隔离
        // 应该在视图消失时主动调用 cleanupVoiceBindings()
    }

    /// 主动清理语音绑定（在视图消失时调用）
    /// 必须在视图生命周期结束时主动调用，deinit 无法访问 @MainActor 属性
    @MainActor
    func cleanupVoiceBindings() {
        voiceCancellables.removeAll()
        pressAndHoldVoiceService.onPartialResult = nil
        pressAndHoldVoiceService.onFinalResult = nil
        // onTTSEnded 已移除（TTS 功能已废弃）
        pressAndHoldVoiceService.onError = nil
        print("[UnifiedChatVM] 语音绑定已清理")
    }

    /// 完整清理资源（在视图完全消失时调用）
    @MainActor
    func cleanup() {
        // 1. 停止语音服务
        pressAndHoldVoiceService.disconnect()

        // 2. 清理语音绑定
        cleanupVoiceBindings()

        // 3. 清理回调
        onVoiceImageRequest = nil

        // 4. 清理消息（释放图片内存）
        messages.removeAll()

        // 5. 重置状态
        inputMode = .text
        isVoiceMode = false
        voiceState = .idle

        print("[UnifiedChatVM] 完整资源清理完成")
    }

    // MARK: - 会话状态
    @Published var sessionId: String?
    @Published var agentType: AgentType?
    @Published var capabilities: AgentCapabilities?
    @Published var currentDoctorId: Int?
    @Published var currentDepartment: String?

    // MARK: - 消息
    @Published var messages: [UnifiedChatMessage] = []
    @Published var isLoading = false
    @Published var isSending = false

    // MARK: - 内存管理：最大消息数量限制（防止内存无限增长）
    private let maxMessageCount = 200
    private let maxImageMessagesInMemory = 10  // 内存中最多保留 10 张图片
    
    // MARK: - 流式输出
    @Published var streamingContent = ""
    @Published var streamingMessageId: UUID?
    
    // MARK: - 错误处理
    @Published var errorMessage: String?
    @Published var showError = false
    
    // MARK: - 当前动作模式
    @Published var currentActionMode: AgentAction?
    @Published var isUploadingImage = false
    @Published var isAnalyzing = false
    
    // MARK: - 高风险警告
    @Published var showRiskAlert = false
    @Published var riskAlertMessage = ""
    
    // MARK: - 对话完成与病历生成
    @Published var isConversationCompleted = false
    @Published var eventId: String?
    @Published var isNewEvent = false
    @Published var shouldShowDossierPrompt = false
    
    // MARK: - 智能病历按钮
    @Published var showGenerateConfirmation = false
    @Published var generateConfirmationMessage = ""
    
    // MARK: - 诊断展示增强
    @Published var adviceHistory: [AdviceEntry] = []
    @Published var diagnosisCard: DiagnosisCard?
    @Published var knowledgeRefs: [KnowledgeRef] = []
    @Published var reasoningSteps: [String] = []
    
    // MARK: - 输入模式
    @Published var inputMode: InputMode = .text

    // MARK: - 语音模式属性
    @Published var isVoiceMode: Bool = false
    @Published var voiceState: VoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var aiResponseText: String = ""
    @Published var audioLevel: Float = 0
    @Published var isMicrophoneMuted: Bool = false
    @Published var showExitConfirmation: Bool = false

    // MARK: - 语音连接状态（移除，不再需要）

    // 语音模式回调
    var onVoiceImageRequest: ((ImageSourceType) -> Void)?
    
    /// 判断是否可以生成病历
    /// 至少需要5条消息（用户3条 + AI 2条）才能生成有意义的病历
    var canGenerateDossier: Bool {
        // 如果对话已完成，始终可以生成
        if isConversationCompleted { return true }
        
        // 至少需要5条消息
        guard messages.count >= 5 else { return false }
        
        // 检查是否有足够的用户消息
        let userMessages = messages.filter { $0.isFromUser }
        return userMessages.count >= 3
    }
    
    /// 病历按钮的提示文字
    var dossierButtonTooltip: String {
        if canGenerateDossier {
            return "根据本次对话生成结构化病历"
        } else {
            return "请继续对话收集更多信息后再生成病历（至少需要3轮对话）"
        }
    }
    
    private let apiService = APIService.shared
    private let medicalEventService = MedicalEventAPIService.shared
    private let localImageManager = LocalImageManager.shared
    private let sessionStateManager = SessionStateManager.shared

    // MARK: - 语音服务
    private var pressAndHoldVoiceService: PressAndHoldVoiceService {
        return .shared
    }
    private var voiceCancellables = Set<AnyCancellable>()

    // MARK: - 初始化会话
    func initializeSession(doctorId: Int?, department: String?) async {
        isLoading = true
        defer { isLoading = false }

        // 保存当前医生和科室信息
        currentDoctorId = doctorId
        currentDepartment = department

        print("[UnifiedChatVM] initializeSession called - doctorId: \(String(describing: doctorId)), department: \(String(describing: department))")

        // 1. 检查是否有活跃会话
        if let doctorId = doctorId {
            let activeSessionId = sessionStateManager.getActiveSession(doctorId: doctorId)
            print("[UnifiedChatVM] 检查活跃会话 - doctorId: \(doctorId), activeSessionId: \(String(describing: activeSessionId))")

            if let sessionId = activeSessionId {
                // 尝试恢复活跃会话
                print("[UnifiedChatVM] 发现活跃会话: \(sessionId)")
                await loadExistingSession(sessionId: sessionId)
                return
            }
        }

        // 2. 创建新会话
        print("[UnifiedChatVM] 没有活跃会话，创建新会话")
        await createNewSession(doctorId: doctorId, department: department)
    }
    
    // MARK: - 加载现有会话
    func loadExistingSession(sessionId: String) async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            // 1. 获取会话消息历史
            let historyResponse = try await apiService.getMessages(sessionId: sessionId, limit: 50)
            
            self.sessionId = sessionId
            
            // 2. 推断智能体类型
            let inferredAgentType = inferAgentType(from: currentDepartment)
            agentType = inferredAgentType
            
            // 3. 获取智能体能力
            if let type = agentType {
                capabilities = try await apiService.getAgentCapabilities(type)
            }
            
            // 4. 加载历史消息
            loadHistoryMessages(historyResponse.messages)
            
            print("[UnifiedChatVM] 已恢复会话: \(sessionId), 消息数: \(messages.count)")
            
        } catch {
            print("[UnifiedChatVM] 恢复会话失败，创建新会话")
            // 恢复失败，创建新会话
            await createNewSession(doctorId: currentDoctorId, department: currentDepartment)
        }
    }
    
    // MARK: - 创建新会话
    func createNewSession(doctorId: Int?, department: String?) async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            // 推断智能体类型
            let inferredAgentType = inferAgentType(from: department)
            
            // 创建会话
            let session = try await apiService.createUnifiedSession(
                doctorId: doctorId,
                agentType: inferredAgentType
            )
            
            sessionId = session.sessionId
            agentType = AgentType(rawValue: session.agentType)
            
            // 获取智能体能力
            if let type = agentType {
                capabilities = try await apiService.getAgentCapabilities(type)
                print("[UnifiedChatVM] Capabilities loaded: \(capabilities?.actions ?? [])")
            }
            
            // 清空消息列表
            messages.removeAll()
            
            // 保存为活跃会话
            if let doctorId = doctorId {
                sessionStateManager.saveActiveSession(doctorId: doctorId, sessionId: session.sessionId)
            }
            
            print("[UnifiedChatVM] 已创建新会话: \(session.sessionId)")
            
        } catch {
            handleError(error)
        }
    }
    
    // MARK: - 手动新建对话
    func startNewConversation() async {
        // 清除当前活跃会话
        if let doctorId = currentDoctorId {
            sessionStateManager.clearActiveSession(doctorId: doctorId)
        }
        
        // 重置状态
        isConversationCompleted = false
        shouldShowDossierPrompt = false
        eventId = nil
        
        // 创建新会话
        await createNewSession(doctorId: currentDoctorId, department: currentDepartment)
    }
    
    // MARK: - 加载历史消息
    /// 加载历史消息，限制加载的图片数量以控制内存使用
    private func loadHistoryMessages(_ historyMessages: [MessageModel]) {
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
                // 尝试从会话的本地图片中查找
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

        print("[UnifiedChatVM] 加载历史消息: \(messages.count) 条（图片: \(loadedImageCount) 张）")
    }
    
    // MARK: - 发送消息
    func sendMessage(
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async {
        guard let sessionId = sessionId else { return }
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !attachments.isEmpty else { return }

        // 清除之前所有消息的快捷选项
        for index in messages.indices {
            messages[index].quickOptions = []
        }

        // 添加用户消息
        let userMessage = UnifiedChatMessage.userMessage(content, attachments: attachments)
        messages.append(userMessage)

        // 内存管理：如果消息数量超过限制，删除最旧的消息（保留最近200条）
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
    
    // MARK: - 触发动作
    func triggerAction(_ action: AgentAction) {
        print("[UnifiedChatVM] 🎯 triggerAction 被调用, action: \(action.rawValue)")
        currentActionMode = action
        print("[UnifiedChatVM] ✅ currentActionMode 已设置为: \(action.rawValue)")
        
        // 根据动作类型插入提示消息
        let tipContent: String
        switch action {
        case .analyzeSkin:
            tipContent = "请上传皮肤照片进行分析"
        case .interpretReport:
            tipContent = "请上传检查报告进行解读"
        case .interpretECG:
            tipContent = "请上传心电图进行解读"
        default:
            print("[UnifiedChatVM] ⚠️ 不支持的 action 类型: \(action.rawValue)")
            return
        }
        
        let tipMessage = UnifiedChatMessage(
            content: tipContent,
            isFromUser: false,
            messageType: .text
        )
        messages.append(tipMessage)
        print("[UnifiedChatVM] 💬 已添加提示消息: \(tipContent)")
    }
    
    // MARK: - 处理图片选择
    func handleSelectedImage(_ image: UIImage) async {
        print("[UnifiedChatVM] 📸 handleSelectedImage 被调用")
        print("[UnifiedChatVM] currentActionMode: \(String(describing: currentActionMode))")
        print("[UnifiedChatVM] sessionId: \(String(describing: sessionId))")
        
        guard let action = currentActionMode else {
            print("[UnifiedChatVM] ❌ currentActionMode 为 nil, 无法处理图片")
            return
        }
        guard let sessionId = sessionId else {
            print("[UnifiedChatVM] ❌ sessionId 为 nil, 无法处理图片")
            return
        }
        
        print("[UnifiedChatVM] ✅ 开始处理图片, action: \(action.rawValue)")
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
            
            // 4. 将图片转为 base64 (压缩质量 0.7，在质量和内存使用间平衡)
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
            
            print("[UnifiedChatVM] 📦 图片处理完成:")
            print("[UnifiedChatVM]   - 图片大小: \(imageData.count) bytes")
            print("[UnifiedChatVM]   - Base64长度: \(base64String.count) chars")
            print("[UnifiedChatVM]   - Attachment类型: \(attachment.type)")
            
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
            
            print("[UnifiedChatVM] 🚀 准备发送API请求:")
            print("[UnifiedChatVM]   - sessionId: \(sessionId)")
            print("[UnifiedChatVM]   - content: \(action.analysisPrompt)")
            print("[UnifiedChatVM]   - action: \(action.rawValue)")
            print("[UnifiedChatVM]   - attachments数量: 1")
            
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
    
    // MARK: - 图片尺寸缩放
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
        
        print("[UnifiedChatVM] 图片已缩放: \(size) -> \(newSize)")
        return resizedImage ?? image
    }
    
    // MARK: - 动态功能检查
    func supportsAction(_ action: AgentAction) -> Bool {
        guard let capabilities = capabilities else { return false }
        return capabilities.actions.contains(action.rawValue)
    }
    
    func supportsImageUpload() -> Bool {
        return capabilities?.supportsImageUpload ?? false
    }
    
    /// 获取当前智能体支持的动作列表
    var availableActions: [AgentAction] {
        guard let capabilities = capabilities else { return [] }
        return capabilities.actions.compactMap { AgentAction(rawValue: $0) }
            .filter { $0 != .conversation } // 排除基础对话
    }
    
    // MARK: - 私有方法
    
    private func inferAgentType(from department: String?) -> AgentType? {
        guard let dept = department else { return nil }
        
        if dept.contains("皮肤") { return .dermatology }
        if dept.contains("心内") || dept.contains("心血管") { return .cardiology }
        if dept.contains("骨科") || dept.contains("骨伤") { return .orthopedics }
        
        return .general
    }
    
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
    
    private func handleComplete(_ response: UnifiedMessageResponse) {
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
        // === 调试日志：数据接收 ===
        print("[DEBUG] handleComplete 收到响应")
        print("[DEBUG] - adviceHistory: \(response.adviceHistory?.count ?? 0) 条")
        print("[DEBUG] - diagnosisCard: \(response.diagnosisCard != nil ? "有" : "无")")
        print("[DEBUG] - knowledgeRefs: \(response.knowledgeRefs?.count ?? 0) 条")
        print("[DEBUG] - reasoningSteps: \(response.reasoningSteps?.count ?? 0) 步")
        // === 日志结束 ===
        
        if let history = response.adviceHistory {
            adviceHistory = history
            // === 调试日志 ===
            print("[DEBUG] 已更新 adviceHistory: \(history.count) 条")
            for (i, adv) in history.enumerated() {
                print("[DEBUG] - [\(i)] \(adv.title)")
            }
            // === 日志结束 ===
        }
        if let card = response.diagnosisCard {
            diagnosisCard = card
            // === 调试日志 ===
            print("[DEBUG] 已更新 diagnosisCard:")
            print("[DEBUG] - summary: \(card.summary)")
            print("[DEBUG] - conditions: \(card.conditions.count) 个")
            print("[DEBUG] - riskLevel: \(card.riskLevel)")
            // === 日志结束 ===
        } else {
            // === 调试日志 ===
            print("[DEBUG] API 响应中没有 diagnosisCard")
            // === 日志结束 ===
        }
        if let refs = response.knowledgeRefs {
            knowledgeRefs = refs
            print("[DEBUG] 已更新 knowledgeRefs: \(refs.count) 条")
        }
        if let steps = response.reasoningSteps {
            reasoningSteps = steps
            print("[DEBUG] 已更新 reasoningSteps: \(steps.count) 步")
        }
        
        // 检查对话是否完成
        if response.stage == "completed" || response.shouldShowDossierPrompt == true {
            isConversationCompleted = true
            eventId = response.eventId
            isNewEvent = response.isNewEvent ?? false
            shouldShowDossierPrompt = response.shouldShowDossierPrompt ?? false
        }
    }
    
    private func handleAnalysisComplete(_ response: UnifiedMessageResponse) {
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
    
    private func handleError(_ error: Error) {
        if let apiError = error as? APIError {
            errorMessage = apiError.errorDescription
        } else {
            errorMessage = "发生错误，请重试"
        }
        showError = true
    }

    // MARK: - 内存管理：清理旧消息
    /// 当消息数量超过限制时，删除最旧的消息以控制内存使用
    /// 图片消息占用大量内存，需要额外限制
    private func trimMessagesIfNeeded() {
        // 1. 首先检查并限制图片消息数量（图片占用大量内存）
        let imageMessages = messages.filter { isImageMessage($0) }
        if imageMessages.count > maxImageMessagesInMemory {
            // 找出并删除最旧的图片消息（保留最新的 maxImageMessagesInMemory 张）
            let excessImageCount = imageMessages.count - maxImageMessagesInMemory
            var imagesToRemove = Set<UUID>()
            for msg in imageMessages.prefix(excessImageCount) {
                imagesToRemove.insert(msg.id)
            }
            messages.removeAll { imagesToRemove.contains($0.id) }
            print("[UnifiedChatVM] ⚠️ 删除了 \(excessImageCount) 条旧图片消息以释放内存")
        }

        // 2. 然后检查总消息数量
        if messages.count > maxMessageCount {
            let excessCount = messages.count - maxMessageCount
            messages.removeFirst(excessCount)
            print("[UnifiedChatVM] ⚠️ 删除了 \(excessCount) 条旧消息（当前: \(messages.count)/\(maxMessageCount)）")
        }
    }

    /// 检查消息是否为图片类型
    private func isImageMessage(_ message: UnifiedChatMessage) -> Bool {
        if case .image = message.messageType {
            return true
        }
        return false
    }

    // MARK: - 请求生成病历（带确认）
    func requestGenerateDossier() {
        // 检查是否可以生成
        if !canGenerateDossier {
            errorMessage = "对话信息不足，请继续描述您的症状（至少需要3轮对话）"
            showError = true
            return
        }
        
        // 如果消息较少，显示确认对话框
        if messages.count < 8 {
            generateConfirmationMessage = "当前对话较少，生成的病历可能不够详细。是否继续生成？"
            showGenerateConfirmation = true
        } else {
            // 直接生成
            Task {
                await manuallyGenerateDossier()
            }
        }
    }
    
    /// 确认生成病历
    func confirmGenerateDossier() {
        showGenerateConfirmation = false
        Task {
            await manuallyGenerateDossier()
        }
    }
    
    /// 取消生成病历
    func cancelGenerateDossier() {
        showGenerateConfirmation = false
    }
    
    // MARK: - 手动生成病历（内部方法）
    private func manuallyGenerateDossier() async {
        guard let sessionId = sessionId else { return }
        guard let agentType = agentType else { return }
        
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await medicalEventService.aggregateSession(
                sessionId: sessionId,
                sessionType: agentType.rawValue
            )
            
            eventId = response.event_id
            isNewEvent = response.is_new_event
            shouldShowDossierPrompt = true
            isConversationCompleted = true
            
            print("[UnifiedChatVM] 病历生成成功: eventId=\(response.event_id), isNew=\(response.is_new_event)")
        } catch {
            handleError(error)
        }
    }
    
    // MARK: - 继续对话
    func continueConversation() {
        isConversationCompleted = false
        shouldShowDossierPrompt = false
    }
    
    // 移除前端欢迎语逻辑，由后端智能体统一管理
    // 当用户发送第一条消息时，后端会根据 agent state 决定是否返回问候语
    
    // MARK: - 语音模式方法

    /// 初始化语音服务绑定
    func setupVoiceBindings() {
        // 设置 PressAndHoldVoiceService 回调
        pressAndHoldVoiceService.onPartialResult = { [weak self] text in
            Task { @MainActor in
                self?.recognizedText = text
            }
        }

        pressAndHoldVoiceService.onFinalResult = { [weak self] text in
            Task { @MainActor in
                await self?.handleFinalRecognition(text)
            }
        }

        pressAndHoldVoiceService.onError = { [weak self] error in
            Task { @MainActor in
                self?.errorMessage = error
                self?.showError = true
            }
        }

        // 绑定状态变化
        pressAndHoldVoiceService.$state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] newState in
                guard let self = self else { return }
                // 将 PressAndHoldVoiceState 映射到 VoiceState
                switch newState {
                case .idle:
                    self.voiceState = .idle
                case .listening:
                    self.voiceState = .listening
                case .processing:
                    self.voiceState = .processing
                case .error(let msg):
                    self.voiceState = .error(VoiceError.recognitionFailed(underlying: NSError(domain: "Voice", code: -1, userInfo: [NSLocalizedDescriptionKey: msg])))
                }
                // .speaking 状态已移除（TTS 功能已废弃）
            }
            .store(in: &voiceCancellables)
    }

    // MARK: - 按住说话方法

    /// 开始按住说话录音
    func startPressAndHoldRecording() async {
        do {
            try await pressAndHoldVoiceService.startRecording()
        } catch {
            print("[UnifiedChatVM] 开始录音失败: \(error)")
        }
    }

    /// 停止按住说话录音并发送
    func stopPressAndHoldRecording() async {
        guard let text = await pressAndHoldVoiceService.stopRecording() else {
            return
        }

        // 发送消息
        await sendMessage(content: text)

        // TTS 播报功能已移除，不再等待 AI 回复并播报
    }

    /// 取消按住说话录音
    func cancelPressAndHoldRecording() async {
        pressAndHoldVoiceService.cancelRecording()
    }

    /// 切换静音状态（已移除 TTS 功能，此方法已废弃）
    func toggleVoiceMute(_ muted: Bool) {
        // TTS 功能已移除，静音功能不再需要
        print("[UnifiedChatVM] 静音功能已废弃（TTS 已移除）")
    }

    /// 处理语音打断（保留供兼容）
    private func handleVoiceInterruption() {
        print("[UnifiedChatVM] 检测到用户打断")
    }

    // MARK: - 私有语音方法

    private func handleFinalRecognition(_ text: String) async {
        print("[UnifiedChatVM] 收到最终识别结果: \(text)")
        guard !text.isEmpty else {
            print("[UnifiedChatVM] 识别结果为空，跳过发送")
            return
        }
    }

    // waitForAIResponseAndSpeak() 方法已移除（TTS 功能已废弃）

    private func handleVoiceError(_ error: Error) {
        if let voiceError = error as? VoiceError {
            voiceState = .error(voiceError)
        } else {
            voiceState = .error(VoiceError.recognitionFailed(underlying: error))
        }
        print("[UnifiedChatVM] 语音错误: \(error.localizedDescription)")
    }
}

// MARK: - AgentAction UI 扩展（仅添加未定义的属性）
extension AgentAction {
    var icon: String {
        switch self {
        case .conversation: return "message"
        case .analyzeSkin: return "camera.fill"
        case .interpretReport: return "doc.text.fill"
        case .interpretECG: return "waveform.path.ecg"
        }
    }
    
    var uploadDescription: String {
        switch self {
        case .analyzeSkin: return "📷 已上传皮肤照片"
        case .interpretReport: return "📄 已上传检查报告"
        case .interpretECG: return "📊 已上传心电图"
        default: return "已上传图片"
        }
    }
    
    var analysisPrompt: String {
        switch self {
        case .analyzeSkin: return "请分析这张皮肤照片"
        case .interpretReport: return "请解读这份检查报告"
        case .interpretECG: return "请解读这份心电图"
        default: return ""
        }
    }
}
