import Foundation
import Combine

/// 会话管理服务
/// 负责：会话创建、恢复、状态管理、智能体能力管理
@MainActor
class ChatSessionService {
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

        currentDoctorId = doctorId
        currentDepartment = department

        print("[ChatSessionService] initializeSession - doctorId: \(String(describing: doctorId)), department: \(String(describing: department))")

        if let doctorId = doctorId {
            let activeSessionId = sessionStateManager.getActiveSession(doctorId: doctorId)

            if let existingSessionId = activeSessionId {
                print("[ChatSessionService] 发现活跃会话: \(existingSessionId)")
                self.sessionId = existingSessionId
                await loadCapabilities()
                return
            }
        }

        print("[ChatSessionService] 没有活跃会话，创建新会话")
        await createNewSession(doctorId: doctorId, department: department)
    }

    /// 创建新会话
    func createNewSession(doctorId: Int?, department: String?) async {
        isLoading = true
        defer { isLoading = false }

        do {
            let inferredAgentType = inferAgentType(from: department)

            let session = try await apiService.createSession(
                doctorId: doctorId,
                agentType: inferredAgentType
            )

            sessionId = session.sessionId
            agentType = AgentType(rawValue: session.agentType)

            if let type = agentType {
                capabilities = try await apiService.getAgentCapabilities(type)
            }

            if let doctorId = doctorId {
                sessionStateManager.saveActiveSession(doctorId: doctorId, sessionId: session.sessionId)
            }

            print("[ChatSessionService] 已创建新会话: \(session.sessionId)")

        } catch {
            handleError(error)
        }
    }

    /// 手动新建对话
    func startNewConversation() async {
        if let doctorId = currentDoctorId {
            sessionStateManager.clearActiveSession(doctorId: doctorId)
        }

        isConversationCompleted = false
        shouldShowDossierPrompt = false
        eventId = nil

        await createNewSession(doctorId: currentDoctorId, department: currentDepartment)
    }

    // MARK: - 智能体能力

    private func loadCapabilities() async {
        guard let type = agentType else { return }
        do {
            capabilities = try await apiService.getAgentCapabilities(type)
        } catch {
            print("[ChatSessionService] 加载能力失败: \(error)")
        }
    }

    func inferAgentType(from department: String?) -> AgentType? {
        guard let dept = department else { return nil }
        if dept.contains("皮肤") { return .dermatology }
        if dept.contains("心内") || dept.contains("心血管") { return .cardiology }
        if dept.contains("骨科") || dept.contains("骨伤") { return .orthopedics }
        return .general
    }

    func supportsAction(_ action: AgentAction) -> Bool {
        guard let capabilities = capabilities else { return false }
        return capabilities.actions.contains(action.rawValue)
    }

    func supportsImageUpload() -> Bool {
        return capabilities?.supportsImageUpload ?? false
    }

    var availableActions: [AgentAction] {
        guard let capabilities = capabilities else { return [] }
        return capabilities.actions.compactMap { AgentAction(rawValue: $0) }
            .filter { $0 != .conversation }
    }

    // MARK: - 病历生成

    func requestGenerateDossier(messageCount: Int, canGenerate: Bool) async -> Bool {
        guard !canGenerate else {
            errorMessage = "对话信息不足，请继续描述您的症状（至少需要3轮对话）"
            showError = true
            return false
        }

        if messageCount < 8 {
            generateConfirmationMessage = "当前对话较少，生成的病历可能不够详细。是否继续生成？"
            showGenerateConfirmation = true
            return false
        }

        return await manuallyGenerateDossier()
    }

    func confirmGenerateDossier() async {
        showGenerateConfirmation = false
        _ = await manuallyGenerateDossier()
    }

    func cancelGenerateDossier() {
        showGenerateConfirmation = false
    }

    private func manuallyGenerateDossier() async -> Bool {
        guard let sessionId = sessionId else { return false }
        guard let agentType = agentType else { return false }

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

            print("[ChatSessionService] 病历生成成功: eventId=\(response.event_id)")
            return true
        } catch {
            handleError(error)
            return false
        }
    }

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
