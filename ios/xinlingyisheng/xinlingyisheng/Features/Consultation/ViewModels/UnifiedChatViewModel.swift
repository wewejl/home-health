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
enum InputMode {
    case text   // 文字输入模式
    case voice  // 按住说话模式
}

// MARK: - 统一聊天 ViewModel
/// 能力驱动的统一聊天视图模型
/// 根据智能体能力动态渲染功能按钮，支持多科室适配
///
/// 架构说明：
/// 内部使用三个服务类来分离职责：
/// - ChatSessionService: 会话管理、智能体能力、病历生成
/// - ChatMessageService: 消息列表、发送消息、图片处理
/// - ChatVoiceInputService: 语音识别、按住说话
///
/// 对外保持原有的 @Published 属性接口，避免 SwiftUI 编译器类型检查问题
@MainActor
class UnifiedChatViewModel: ObservableObject {
    // MARK: - 内部服务（不对外暴露为 @Published）
    private let sessionService: ChatSessionService
    private let messageService: ChatMessageService
    // MARK: - 初始化

    init() {
        sessionService = ChatSessionService()
        messageService = ChatMessageService()

        setupVoiceBindings()

        // 监听服务变化，同步到本 ViewModel
        setupServiceBindings()
    }

    nonisolated deinit {
        AppLogger.debug("[UnifiedChatVM] deinit")
    }

    /// 主动清理语音绑定（在视图消失时调用）
    func cleanupVoiceBindings() {
        // 语音绑定清理已移至 VoiceInputViewModel
        AppLogger.cleanup("[UnifiedChatVM] 语音绑定已清理")
    }

    /// 完整清理资源（在视图完全消失时调用）
    func cleanup() {
        messageService.clearMessages()
        inputMode = .text
        isVoiceMode = false
        AppLogger.cleanup("[UnifiedChatVM] 完整资源清理完成")
    }

    // MARK: - 服务绑定（将服务状态同步到 ViewModel）

    private func setupServiceBindings() {
        // 监听 sessionService 的变化
        sessionService.$sessionId.assign(to: &$sessionId)
        sessionService.$agentType.assign(to: &$agentType)
        sessionService.$capabilities.assign(to: &$capabilities)
        sessionService.$currentDoctorId.assign(to: &$currentDoctorId)
        sessionService.$currentDepartment.assign(to: &$currentDepartment)
        sessionService.$isLoading.assign(to: &$isLoading)
        sessionService.$isConversationCompleted.assign(to: &$isConversationCompleted)
        sessionService.$eventId.assign(to: &$eventId)
        sessionService.$isNewEvent.assign(to: &$isNewEvent)
        sessionService.$shouldShowDossierPrompt.assign(to: &$shouldShowDossierPrompt)
        sessionService.$showGenerateConfirmation.assign(to: &$showGenerateConfirmation)
        sessionService.$generateConfirmationMessage.assign(to: &$generateConfirmationMessage)
        sessionService.$errorMessage.assign(to: &$errorMessage)
        sessionService.$showError.assign(to: &$showError)

        // 监听 messageService 的变化
        messageService.$messages.assign(to: &$messages)
        messageService.$isSending.assign(to: &$isSending)
        messageService.$isUploadingImage.assign(to: &$isUploadingImage)
        messageService.$isAnalyzing.assign(to: &$isAnalyzing)
        messageService.$streamingContent.assign(to: &$streamingContent)
        messageService.$streamingMessageId.assign(to: &$streamingMessageId)
        messageService.$currentActionMode.assign(to: &$currentActionMode)
        messageService.$adviceHistory.assign(to: &$adviceHistory)
        messageService.$diagnosisCard.assign(to: &$diagnosisCard)
        messageService.$knowledgeRefs.assign(to: &$knowledgeRefs)
        messageService.$reasoningSteps.assign(to: &$reasoningSteps)
    }

    // MARK: - 会话状态（对外接口）
    @Published var sessionId: String?
    @Published var agentType: AgentType?
    @Published var capabilities: AgentCapabilities?
    @Published var currentDoctorId: Int?
    @Published var currentDepartment: String?
    @Published var isLoading = false

    // MARK: - 消息状态（对外接口）
    @Published var messages: [UnifiedChatMessage] = []
    @Published var isSending = false
    @Published var isUploadingImage = false
    @Published var isAnalyzing = false

    // MARK: - 流式输出（对外接口）
    @Published var streamingContent = ""
    @Published var streamingMessageId: UUID?

    // MARK: - 错误处理（对外接口）
    @Published var errorMessage: String?
    @Published var showError = false

    // MARK: - 当前动作模式（对外接口）
    @Published var currentActionMode: AgentAction?

    // MARK: - 高风险警告（对外接口）
    @Published var showRiskAlert = false
    @Published var riskAlertMessage = ""

    // MARK: - 对话完成与病历生成（对外接口）
    @Published var isConversationCompleted = false
    @Published var eventId: String?
    @Published var isNewEvent = false
    @Published var shouldShowDossierPrompt = false

    // MARK: - 智能病历按钮（对外接口）
    @Published var showGenerateConfirmation = false
    @Published var generateConfirmationMessage = ""

    // MARK: - 诊断展示增强（对外接口）
    @Published var adviceHistory: [AdviceEntry] = []
    @Published var diagnosisCard: AgentDiagnosisCard?
    @Published var knowledgeRefs: [KnowledgeRef] = []
    @Published var reasoningSteps: [String] = []

    // MARK: - 输入模式（对外接口）
    @Published var inputMode: InputMode = .text

    // MARK: - 语音模式属性（对外接口）
    @Published var isVoiceMode: Bool = false
    @Published var voiceState: VoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var aiResponseText: String = ""
    @Published var audioLevel: Float = 0
    @Published var isMicrophoneMuted: Bool = false
    @Published var showExitConfirmation: Bool = false

    // MARK: - 语音模式回调
    var onVoiceImageRequest: ((ImageSourceType) -> Void)?

    // MARK: - 计算属性（转发到服务）

    var canGenerateDossier: Bool {
        return messageService.canGenerateDossier(isConversationCompleted: isConversationCompleted)
    }

    var dossierButtonTooltip: String {
        return messageService.dossierButtonTooltip(canGenerate: canGenerateDossier)
    }

    var availableActions: [AgentAction] {
        return sessionService.availableActions
    }

    // MARK: - 私有属性（保留原有代码兼容）

    private let maxMessageCount = 200
    private let maxImageMessagesInMemory = 10
    private let apiService = APIService.shared
    private let localImageManager = LocalImageManager.shared
    private let sessionStateManager = SessionStateManager.shared

    private var pressAndHoldVoiceService: PressAndHoldVoiceService {
        return .shared
    }
    private var voiceCancellables = Set<AnyCancellable>()

    // MARK: - 会话管理方法

    func initializeSession(doctorId: Int?, department: String?) async {
        await sessionService.initializeSession(doctorId: doctorId, department: department)

        // 加载历史消息
        if let sessionId = sessionService.sessionId {
            let apiService = APIService.shared
            do {
                let historyResponse = try await apiService.getMessages(sessionId: sessionId, limit: 50)
                messageService.loadHistoryMessages(historyResponse.messages, sessionId: sessionId)
            } catch {
                print("[UnifiedChatVM] 加载历史消息失败: \(error.localizedDescription)")
            }
        }
    }

    func loadExistingSession(sessionId: String) async {
        sessionService.sessionId = sessionId

        let apiService = APIService.shared
        do {
            let historyResponse = try await apiService.getMessages(sessionId: sessionId, limit: 50)

            let inferredAgentType = sessionService.inferAgentType(from: sessionService.currentDepartment)
            sessionService.agentType = inferredAgentType

            if let type = sessionService.agentType {
                sessionService.capabilities = try await apiService.getAgentCapabilities(type)
            }

            messageService.loadHistoryMessages(historyResponse.messages, sessionId: sessionId)

            print("[UnifiedChatVM] 已恢复会话: \(sessionId), 消息数: \(messages.count)")

        } catch {
            print("[UnifiedChatVM] 恢复会话失败，创建新会话")
            await createNewSession(doctorId: sessionService.currentDoctorId, department: sessionService.currentDepartment)
        }
    }

    func createNewSession(doctorId: Int?, department: String?) async {
        await sessionService.createNewSession(doctorId: doctorId, department: department)
        messageService.clearMessages()
    }

    func startNewConversation() async {
        await sessionService.startNewConversation()
        messageService.clearMessages()
    }

    // MARK: - 消息管理方法

    func sendMessage(
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async {
        guard let sessionId = sessionService.sessionId else { return }
        await messageService.sendMessage(
            sessionId: sessionId,
            content: content,
            attachments: attachments,
            action: action
        )
    }

    func triggerAction(_ action: AgentAction) {
        print("[UnifiedChatVM] 🎯 triggerAction 被调用, action: \(action.rawValue)")
        messageService.currentActionMode = action

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
        messageService.messages.append(tipMessage)
    }

    func handleSelectedImage(_ image: UIImage) async {
        guard let sessionId = sessionService.sessionId else {
            print("[UnifiedChatVM] ❌ sessionId 为 nil, 无法处理图片")
            return
        }
        guard let action = messageService.currentActionMode else {
            print("[UnifiedChatVM] ❌ currentActionMode 为 nil, 无法处理图片")
            return
        }

        await messageService.handleSelectedImage(image, sessionId: sessionId, action: action)
    }

    // MARK: - 语音输入方法

    func startPressAndHoldRecording() async {
        do {
            try await pressAndHoldVoiceService.startRecording()
        } catch {
            print("[UnifiedChatVM] 开始录音失败: \(error)")
        }
    }

    func stopPressAndHoldRecording() async {
        if let text = await pressAndHoldVoiceService.stopRecording() {
            await sendMessage(content: text)
        }
    }

    func cancelPressAndHoldRecording() {
        pressAndHoldVoiceService.cancelRecording()
    }

    func toggleVoiceMute(_ muted: Bool) {
        // 已移除 TTS 功能，静音功能不再需要
    }

    // MARK: - 智能体能力方法

    func supportsAction(_ action: AgentAction) -> Bool {
        return sessionService.supportsAction(action)
    }

    func supportsImageUpload() -> Bool {
        return sessionService.supportsImageUpload()
    }

    // MARK: - 病历生成方法

    func requestGenerateDossier() {
        let canGenerate = messageService.canGenerateDossier(isConversationCompleted: isConversationCompleted)
        Task {
            let started = await sessionService.requestGenerateDossier(
                messageCount: messageService.messages.count,
                canGenerate: canGenerate
            )
            if !started {
                errorMessage = sessionService.errorMessage
                showError = sessionService.showError
            }
        }
    }

    func confirmGenerateDossier() {
        Task {
            await sessionService.confirmGenerateDossier()
        }
    }

    func cancelGenerateDossier() {
        sessionService.cancelGenerateDossier()
    }

    func continueConversation() {
        sessionService.continueConversation()
    }

    // MARK: - 语音绑定设置（保留原有代码）

    private func setupVoiceBindings() {
        // 保留原有的绑定设置（用于兼容）
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

        pressAndHoldVoiceService.$state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] newState in
                guard let self = self else { return }
                switch newState {
                case .idle:
                    self.voiceState = .idle
                case .listening:
                    self.voiceState = .listening
                case .processing:
                    self.voiceState = .processing
                case .error(let msg):
                    self.voiceState = .error(VoiceError.recognitionFailed(underlying: NSError(domain: "Voice", code: -1, userInfo: [NSLocalizedDescriptionKey: msg])))
                case .unauthorized:
                    self.voiceState = .error(VoiceError.unauthorized)
                }
            }
            .store(in: &voiceCancellables)
    }

    private func handleFinalRecognition(_ text: String) async {
        print("[UnifiedChatVM] 收到最终识别结果: \(text)")
    }

    // MARK: - 保留的私有方法（用于原有功能）

    private func loadHistoryMessages(_ historyMessages: [MessageModel]) {
        messageService.loadHistoryMessages(historyMessages, sessionId: sessionService.sessionId)
    }

    private func inferAgentType(from department: String?) -> AgentType? {
        return sessionService.inferAgentType(from: department)
    }

    private func trimMessagesIfNeeded() {
        // 由 messageService 内部处理
    }

    private func isImageMessage(_ message: UnifiedChatMessage) -> Bool {
        if case .image = message.messageType {
            return true
        }
        return false
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
}

// MARK: - AgentAction UI 扩展
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
