import Foundation

// MARK: - Recognition Language
/// 语音识别支持的语言
enum RecognitionLanguage: String, Codable, CaseIterable {
    /// 自动检测（推荐）
    case auto = "auto"
    /// 中文（普通话）
    case chinese = "zh"
    /// 英语
    case english = "en"
    /// 粤语
    case cantonese = "yue"
    /// 四川话
    case sichuanese = "sichuanese"
    /// 日语
    case japanese = "ja"
    /// 韩语
    case korean = "ko"

    /// 显示名称
    var displayName: String {
        switch self {
        case .auto: return "自动检测"
        case .chinese: return "中文"
        case .english: return "English"
        case .cantonese: return "粤语"
        case .sichuanese: return "四川话"
        case .japanese: return "日本語"
        case .korean: return "한국어"
        }
    }

    /// 本地化标识符（用于系统级语音识别）
    var localeIdentifier: String? {
        switch self {
        case .auto: return nil
        case .chinese: return "zh-CN"
        case .english: return "en-US"
        case .cantonese: return "zh-HK"
        case .sichuanese: return "zh-CN"
        case .japanese: return "ja-JP"
        case .korean: return "ko-KR"
        }
    }

    /// 默认语言
    static let `default`: RecognitionLanguage = .chinese
}

// MARK: - Detected Language Info
/// 检测到的语言信息
struct DetectedLanguageInfo: Codable {
    /// 语言代码
    let code: String
    /// 置信度 (0-1)
    let confidence: Double
    /// 语言名称
    var name: String {
        RecognitionLanguage.allCases.first { $0.rawValue == code }?.displayName ?? code
    }
}

// MARK: - Transcription Response
struct TranscriptionResponse: Codable {
    let text: String
    let detectedLanguage: String?
    let confidence: Double?
    let durationMs: Int?
    let segments: [TranscriptionSegment]?

    enum CodingKeys: String, CodingKey {
        case text
        case detectedLanguage = "detected_language"
        case confidence
        case durationMs = "duration_ms"
        case segments
    }

    /// 解析后的检测语言信息
    var detectedLanguageInfo: DetectedLanguageInfo? {
        guard let code = detectedLanguage else { return nil }
        return DetectedLanguageInfo(code: code, confidence: confidence ?? 0.0)
    }

    /// 识别到的语言枚举
    var recognizedLanguage: RecognitionLanguage? {
        guard let code = detectedLanguage else { return nil }
        return RecognitionLanguage(rawValue: code)
    }
}

struct TranscriptionSegment: Codable, Identifiable {
    let startMs: Int?
    let endMs: Int?
    let text: String
    let confidence: Double?
    
    var id: UUID { UUID() }
    
    enum CodingKeys: String, CodingKey {
        case startMs = "start_ms"
        case endMs = "end_ms"
        case text
        case confidence
    }
}
