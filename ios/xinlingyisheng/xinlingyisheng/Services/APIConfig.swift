import Foundation

enum APIConfig {
    // MARK: - Environment Configuration
    enum Environment {
        case development
        case production

        var baseURL: String {
            switch self {
            case .development:
                return "http://123.206.232.231/api"
            case .production:
                return "http://123.206.232.231/api"
            }
        }
    }
    
    // 当前环境配置 - 切换此处即可切换环境
    static let currentEnvironment: Environment = .development
    
    // 基础 URL
    static var baseURL: String {
        return currentEnvironment.baseURL
    }
    
    // 请求超时时间
    static let requestTimeout: TimeInterval = 30
    
    // MARK: - Feature Flags
    // 验证码功能开关 - false时隐藏验证码相关UI（临时方案，待接入真实短信服务后启用）
    static let enableSMSVerification: Bool = false
    
    enum Endpoints {
        static let login = "/auth/login"
        static let sendCode = "/auth/send-code"
        static let me = "/auth/me"
        static let profile = "/auth/profile"
        static let refresh = "/auth/refresh"
        // 密码认证
        static let checkPhone = "/auth/check-phone"
        static let loginPassword = "/auth/login-password"
        static let registerPassword = "/auth/register-password"
        static let setPassword = "/auth/password/set"
        static let resetPassword = "/auth/password/reset"
        static let departments = "/departments"
        static func doctors(departmentId: Int) -> String {
            return "/departments/\(departmentId)/doctors"
        }
        static let sessions = "/sessions"
        static func messages(sessionId: String) -> String {
            return "/sessions/\(sessionId)/messages"
        }
        // Unified Agent endpoints
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
        
        // Drugs
        static let drugsCategories = "/drugs/categories"
        static let drugsSearch = "/drugs/search"
        static let drugsHot = "/drugs/hot"
        static func drugDetail(drugId: Int) -> String {
            return "/drugs/\(drugId)"
        }
        
        // Medical Events (病历资料夹)
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
    }
}

enum SpeechAPIConfig {
    static let baseURL: String = "http://123.206.232.231/api/v1"
    enum Endpoints {
        static let transcription = "/transcriptions"
    }
}
