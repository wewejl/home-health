import Foundation

enum APIConfig {
    // MARK: - Environment Configuration
    enum Environment {
        case development
        case production

        var baseURL: String {
            switch self {
            case .development:
                // 开发环境：使用本地服务器或测试服务器
                // 优先从环境变量读取，否则使用默认值
                // 注意：iOS 模拟器需要使用 127.0.0.1 而非 localhost
                return ProcessInfo.processInfo.environment["API_BASE_URL"]
                    ?? "http://127.0.0.1:8100"
            case .production:
                // 生产环境：使用生产服务器
                return ProcessInfo.processInfo.environment["API_BASE_URL"]
                    ?? "http://123.206.232.231/api"
            }
        }

        var isDebug: Bool {
            switch self {
            case .development: return true
            case .production: return false
            }
        }
    }

    // 当前环境配置 - 开发环境使用本地服务器
    static let currentEnvironment: Environment = .development

    // 基础 URL
    static var baseURL: String {
        return currentEnvironment.baseURL
    }

    // 请求超时时间
    static let requestTimeout: TimeInterval = 30

    // 流式响应超时时间（AI 对话可能需要更长时间）
    static let streamTimeout: TimeInterval = 300

    // MARK: - Environment Info
    static let environmentName: String = "Production"
    
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
        // MedLive 格式
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

        // Medical Orders (医嘱执行监督)
        static let medicalOrders = "/medical-orders"
        static let medicalTasks = "/medical-orders/tasks"
        static let compliance = "/medical-orders/compliance"
        static let alerts = "/medical-orders/alerts"
        static let familyBonds = "/medical-orders/family-bonds"
    }
}

enum SpeechAPIConfig {
    static let baseURL: String = {
        // 语音识别 API 基础 URL
        let apiBase = ProcessInfo.processInfo.environment["API_BASE_URL"]
            ?? "http://123.206.232.231/api"
        return apiBase + "/v1"
    }()

    enum Endpoints {
        static let transcription = "/transcriptions"
    }
}

// MARK: - Aliyun Configuration
/// 阿里云服务配置
enum AliyunConfig {
    /// CosyVoice TTS API Key
    static var cosyVoiceAPIKey: String {
        return ProcessInfo.processInfo.environment["ALIYUN_API_KEY"]
            ?? ""  // 从环境变量或配置文件读取
    }

    /// CosyVoice TTS WebSocket 端点
    static let cosyVoiceEndpoint = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

    /// 默认 CosyVoice 模型
    static let defaultCosyVoiceModel: CosyVoiceModel = .v2

    /// 默认 CosyVoice 音色
    static let defaultCosyVoiceVoice: CosyVoiceVoice = .longxiaochun

    /// FSMN-VAD 模型路径（在应用包内）
    static let fsmnVADModelPath = "Models/damo/speech_fsmn_vad_zh-cn-16k-common-onnx/model_quant.onnx"

    /// 是否启用 FSMN-VAD（ONNX 推理）
    static var enableFSMNVAD: Bool {
        return ProcessInfo.processInfo.environment["ENABLE_FSMN_VAD"] == "true"
            || true  // 默认启用
    }

    /// 是否启用 CosyVoice TTS（需要 API Key）
    static var enableCosyVoiceTTS: Bool {
        return !cosyVoiceAPIKey.isEmpty
    }
}

// MARK: - CosyVoice Enums (re-exported for convenience)
typealias CosyVoiceModelType = CosyVoiceModel
typealias CosyVoiceVoiceType = CosyVoiceVoice

// MARK: - Backend Voice Configuration
/// 后端语音服务配置 (统一的后端转发服务)
enum BackendVoiceConfig {
    /// 后端 WebSocket 基础地址
    static var baseURL: String {
        return ProcessInfo.processInfo.environment["BACKEND_URL"]
            ?? APIConfig.baseURL
    }

    /// 默认认证 token
    static var defaultToken: String {
        return ProcessInfo.processInfo.environment["AUTH_TOKEN"]
            ?? "test_1"
    }

    /// ASR WebSocket 端点路径
    static let asrPath = "/ws/voice/asr"

    /// TTS WebSocket 端点路径
    static let ttsPath = "/ws/voice/tts"

    /// 完整 ASR WebSocket URL
    static var asrURL: String {
        var components = URLComponents(string: baseURL)!
        components.path = asrPath
        components.queryItems = [
            URLQueryItem(name: "token", value: defaultToken)
        ]
        return components.url!.absoluteString.replacingOccurrences(of: "http", with: "ws")
    }

    /// 完整 TTS WebSocket URL
    static var ttsURL: String {
        var components = URLComponents(string: baseURL)!
        components.path = ttsPath
        components.queryItems = [
            URLQueryItem(name: "token", value: defaultToken)
        ]
        return components.url!.absoluteString.replacingOccurrences(of: "http", with: "ws")
    }
}

// MARK: - Backend ASR Configuration (Legacy - 使用 BackendVoiceConfig 替代)
/// 后端 ASR 服务配置 (FunASR) - 已废弃，请使用 BackendVoiceConfig
enum BackendASRConfig {
    /// 后端 WebSocket 基础地址
    static var baseURL: String {
        return ProcessInfo.processInfo.environment["BACKEND_URL"]
            ?? APIConfig.baseURL
    }

    /// 阿里云 DashScope API Key (已移至后端，前端不需要)
    static var apiKey: String {
        // 不再在前端存储 API Key
        return ""
    }

    /// WebSocket 端点路径 (已废弃)
    static let webSocketPath = "/funasr/ws"

    /// 完整 WebSocket URL (已废弃)
    static var webSocketURL: String {
        var components = URLComponents(string: baseURL)!
        components.path = webSocketPath
        components.queryItems = [
            URLQueryItem(name: "api_key", value: ""),
            URLQueryItem(name: "sample_rate", value: "16000"),
            URLQueryItem(name: "format", value: "pcm")
        ]
        return components.url!.absoluteString.replacingOccurrences(of: "http", with: "ws")
    }

    /// 采样率
    static let sampleRate: Int = 16000

    /// 音频格式
    static let format: String = "pcm"
}
