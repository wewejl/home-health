import Foundation
import Combine

/// 会话管理 ViewModel
/// 负责：会话创建、恢复、状态管理、智能体能力管理
@MainActor
class ChatSessionViewModel: ObservableObject {
    // MARK: - 会话状态
    @Published var sessionId: String?
    @Published var agentType: AgentType?
    @Published var capabilities: AgentCapabilities?
    @Published var currentDoctorId: Int?
    @Published var currentDepartment: String?
    @Published var isLoading = false

    // MARK: - 对话完成与病历生成状态
    @Published var isConversationCompleted = false
    @Published var eventId: String?
    @Published var isNewEvent = false
    @Published var shouldShowDossierPrompt = false

    // MARK: - 诊断展示增强状态
    @Published var adviceHistory: [AdviceEntry] = []
    @Published var diagnosisCard: AgentDiagnosisCard?
    @Published var knowledgeRefs: [KnowledgeRef] = []
    @Published var reasoningSteps: [String] = []

    // MARK: - 智能病历确认
    @Published var showGenerateConfirmation = false
    @Published var generateConfirmationMessage = ""

    // MARK: - 错误处理
    @Published var errorMessage: String?
    @Published var showError = false

    // MARK: - 私有属性
    private let apiService = APIService.shared
    private let medicalEventService = MedicalEventAPIService.shared
    private let sessionStateManager = SessionStateManager.shared

    // MARK: - 初始化会话

    /// 初始化会话
    func initializeSession(doctorId: Int?, department: String?) async {
        isLoading = true
        defer { isLoading = false }

        // 保存当前医生和科室信息
        currentDoctorId = doctorId
        currentDepartment = department

        print("[ChatSessionVM] initializeSession - doctorId: \(String(describing: doctorId)), department: \(String(describing: department))")

        // 1. 检查是否有活跃会话
        if let doctorId = doctorId {
            let activeSessionId = sessionStateManager.getActiveSession(doctorId: doctorId)

            if let sessionId = activeSessionId {
                print("[ChatSessionVM] 发现活跃会话: \(sessionId)")
                await loadExistingSession(sessionId: sessionId)
                return
            }
        }

        // 2. 创建新会话
        print("[ChatSessionVM] 没有活跃会话，创建新会话")
        await createNewSession(doctorId: doctorId, department: department)
    }

    /// 加载现有会话
    func loadExistingSession(sessionId: String) async {
        isLoading = true
        defer { isLoading = false }

        do {
            // 1. 获取智能体能力
            let inferredAgentType = inferAgentType(from: currentDepartment)
            agentType = inferredAgentType

            if let type = agentType {
                capabilities = try await apiService.getAgentCapabilities(type)
            }

            self.sessionId = sessionId

            print("[ChatSessionVM] 已恢复会话: \(sessionId)")

        } catch {
            print("[ChatSessionVM] 恢复会话失败: \(error.localizedDescription)")
            handleError(error)
        }
    }

    /// 创建新会话
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
                print("[ChatSessionVM] Capabilities loaded: \(capabilities?.actions ?? [])")
            }

            // 保存为活跃会话
            if let doctorId = doctorId {
                sessionStateManager.saveActiveSession(doctorId: doctorId, sessionId: session.sessionId)
            }

            print("[ChatSessionVM] 已创建新会话: \(session.sessionId)")

        } catch {
            handleError(error)
        }
    }

    /// 手动新建对话
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

    // MARK: - 智能体能力

    /// 推断智能体类型
    func inferAgentType(from department: String?) -> AgentType? {
        guard let dept = department else { return nil }

        if dept.contains("皮肤") { return .dermatology }
        if dept.contains("心内") || dept.contains("心血管") { return .cardiology }
        if dept.contains("骨科") || dept.contains("骨伤") { return .orthopedics }

        return .general
    }

    /// 检查是否支持特定动作
    func supportsAction(_ action: AgentAction) -> Bool {
        guard let capabilities = capabilities else { return false }
        return capabilities.actions.contains(action.rawValue)
    }

    /// 是否支持图片上传
    func supportsImageUpload() -> Bool {
        return capabilities?.supportsImageUpload ?? false
    }

    /// 获取当前智能体支持的动作列表
    var availableActions: [AgentAction] {
        guard let capabilities = capabilities else { return [] }
        return capabilities.actions.compactMap { AgentAction(rawValue: $0) }
            .filter { $0 != .conversation }
    }

    // MARK: - 病历生成

    /// 请求生成病历（带确认）
    func requestGenerateDossier(messageCount: Int) {
        // 如果消息较少，显示确认对话框
        if messageCount < 8 {
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
    func confirmGenerateDossier() async {
        showGenerateConfirmation = false
        await manuallyGenerateDossier()
    }

    /// 取消生成病历
    func cancelGenerateDossier() {
        showGenerateConfirmation = false
    }

    /// 手动生成病历（内部方法）
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

            print("[ChatSessionVM] 病历生成成功: eventId=\(response.event_id), isNew=\(response.is_new_event)")
        } catch {
            handleError(error)
        }
    }

    /// 继续对话
    func continueConversation() {
        isConversationCompleted = false
        shouldShowDossierPrompt = false
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
