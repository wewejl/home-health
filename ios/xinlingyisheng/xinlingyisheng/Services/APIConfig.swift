import Foundation

// MARK: - API Configuration
/// API 配置（使用 SecurityConfig 获取值）
enum APIConfig {

    // MARK: - Base URLs

    /// 基础 URL（从 SecurityConfig 获取）
    static var baseURL: String {
        return SecurityConfig.apiBaseURL
    }

    /// WebSocket 基础 URL（从 SecurityConfig 获取）
    static var websocketBaseURL: String {
        return SecurityConfig.websocketBaseURL
    }

    // MARK: - Timeouts

    /// 请求超时时间
    static let requestTimeout: TimeInterval = 30

    /// 流式响应超时时间（AI 对话可能需要更长时间）
    static let streamTimeout: TimeInterval = 300

    // MARK: - Environment Info

    static let environmentName: String = "Production"

    // MARK: - Endpoints

    enum Endpoints {
        // Auth
        static let login = "/auth/login"
        static let sendCode = "/auth/send-code"
        static let me = "/auth/me"
        static let profile = "/auth/profile"
        static let refresh = "/auth/refresh"
        static let checkPhone = "/auth/check-phone"
        static let loginPassword = "/auth/login-password"
        static let registerPassword = "/auth/register-password"
        static let setPassword = "/auth/password/set"
        static let resetPassword = "/auth/password/reset"

        // Departments & Doctors
        static let departments = "/departments"
        static func doctors(departmentId: Int) -> String {
            return "/departments/\(departmentId)/doctors"
        }

        // Sessions (多智能体架构)
        static let sessions = "/sessions"
        static func messages(sessionId: String) -> String {
            return "/sessions/\(sessionId)/messages"
        }
        static let agents = "/sessions/agents"
        static func agentCapabilities(agentType: String) -> String {
            return "/sessions/agents/\(agentType)/capabilities"
        }

        // Diseases
        static let diseases = "/diseases"
        static let diseasesSearch = "/diseases/search"
        static let diseasesHot = "/diseases/hot"
        static let departmentsWithDiseases = "/diseases/departments-with-diseases"
        static func diseaseDetail(diseaseId: Int) -> String {
            return "/diseases/\(diseaseId)"
        }
        static func diseaseDetailMedLive(diseaseId: Int) -> String {
            return "/diseases/\(diseaseId)/medlive"
        }
        static func diseaseByWikiId(wikiId: String) -> String {
            return "/diseases/wiki-id/\(wikiId)"
        }

        // Drugs
        static let drugsCategories = "/drugs/categories"
        static let drugsSearch = "/drugs/search"
        static let drugsHot = "/drugs/hot"
        static func drugDetail(drugId: Int) -> String {
            return "/drugs/\(drugId)"
        }

        // Medical Events
        static let medicalEvents = "/medical-events"
        static func medicalEventDetail(eventId: String) -> String {
            return "/medical-events/\(eventId)"
        }
        static func medicalEventAttachments(eventId: String) -> String {
            return "/medical-events/\(eventId)/attachments"
        }
        static func medicalEventNotes(eventId: String) -> String {
            return "/medical-events/\(eventId)/notes"
        }

        // AI APIs
        static let aiSummary = "/ai/summary"
        static func aiSummaryGet(eventId: String) -> String {
            return "/ai/summary/\(eventId)"
        }
        static let aiAnalyzeRelation = "/ai/analyze-relation"
        static let aiSmartAggregate = "/ai/smart-aggregate"
        static let aiFindRelated = "/ai/find-related"
        static let aiMergeEvents = "/ai/merge-events"
        static let aiTranscribe = "/ai/transcribe"
        static let aiTranscribeUpload = "/ai/transcribe/upload"
        static func aiTranscribeStatus(taskId: String) -> String {
            return "/ai/transcribe/\(taskId)"
        }

        // Medical Orders
        static let medicalOrders = "/medical-orders"
        static let medicalTasks = "/medical-orders/tasks"
        static let compliance = "/medical-orders/compliance"
        static let alerts = "/medical-orders/alerts"
        static let familyBonds = "/medical-orders/family-bonds"
    }
}

// MARK: - Backend Voice Configuration (已弃用 - 使用 SecureWebSocketService)
@available(*, deprecated, message: "Use SecureWebSocketService instead")
enum BackendVoiceConfig {
    @available(*, deprecated, message: "Hardcoded tokens removed. Use AuthManager.")
    static var defaultToken: String {
        fatalError("BackendVoiceConfig.defaultToken is deprecated. Use AuthManager.shared.token")
    }

    static let asrPath = "/ws/voice/asr"

    @available(*, deprecated, message: "Use SecureWebSocketService.connect instead")
    static var asrURL: String {
        fatalError("BackendVoiceConfig.asrURL is deprecated. Use SecureWebSocketService")
    }

    @available(*, deprecated, message: "Use SecurityConfig.apiBaseURL instead")
    static var baseURL: String {
        return SecurityConfig.apiBaseURL
    }
}

// MARK: - Aliyun Configuration
/// 阿里云服务配置
enum AliyunConfig {
    /// FSMN-VAD 模型路径（在应用包内）
    static let fsmnVADModelPath = "Models/damo/speech_fsmn_vad_zh-cn-16k-common-onnx/model_quant.onnx"

    /// 是否启用 FSMN-VAD（ONNX 推理）
    static var enableFSMNVAD: Bool {
        return ProcessInfo.processInfo.environment["ENABLE_FSMN_VAD"] == "true"
            || true  // 默认启用
    }
}
