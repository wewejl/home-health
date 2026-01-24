import Foundation
import AVFoundation

// MARK: - Voice State
/// 语音状态枚举
enum VoiceState: Equatable {
    case idle                    // 待机：等待用户说话
    case listening               // 监听中：正在识别用户语音
    case processing              // 处理中：发送到后端，等待AI回复
    case aiSpeaking              // 播报中：AI正在播报回复
    case error(VoiceError)       // 错误状态

    var displayText: String {
        switch self {
        case .idle:
            return "点击开始语音对话"
        case .listening:
            return "正在聆听..."
        case .processing:
            return "正在思考..."
        case .aiSpeaking:
            return "AI 播报中，说话可打断"
        case .error(let message):
            return message.localizedDescription
        }
    }

    var isActive: Bool {
        switch self {
        case .listening, .processing, .aiSpeaking:
            return true
        default:
            return false
        }
    }

    static func == (lhs: VoiceState, rhs: VoiceState) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle),
             (.listening, .listening),
             (.processing, .processing),
             (.aiSpeaking, .aiSpeaking):
            return true
        case (.error(let e1), .error(let e2)):
            return e1.localizedDescription == e2.localizedDescription
        default:
            return false
        }
    }
}

// MARK: - Voice Error
/// 语音服务错误类型
enum VoiceError: LocalizedError {
    case permissionDenied                    // 权限被拒绝
    case audioSessionFailed(underlying: Error) // 音频会话失败
    case recognitionFailed(underlying: Error)  // 语音识别失败
    case vadInitializationFailed              // VAD 初始化失败
    case audioEngineFailed                     // 音频引擎失败
    case microphoneUnavailable                 // 麦克风不可用

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "请在设置中开启麦克风和语音识别权限"
        case .audioSessionFailed(let error):
            return "音频会话失败: \(error.localizedDescription)"
        case .recognitionFailed(let error):
            return "语音识别失败: \(error.localizedDescription)"
        case .vadInitializationFailed:
            return "语音检测服务初始化失败"
        case .audioEngineFailed:
            return "音频引擎启动失败"
        case .microphoneUnavailable:
            return "麦克风不可用，请检查设备连接"
        }
    }
}

// MARK: - Audio Configuration
/// 音频配置
struct AudioConfiguration {
    /// 缓冲区大小（越大回调频率越低，但延迟越高）
    let bufferSize: AVAudioFrameCount
    /// 采样率（16kHz 最适合语音识别）
    let sampleRate: Double
    /// 声道数
    let channels: UInt32
    /// UI 更新间隔（秒）
    let uiUpdateInterval: TimeInterval

    /// 默认配置（优化后）
    static let `default` = AudioConfiguration(
        bufferSize: 4096,
        sampleRate: 16000,
        channels: 1,
        uiUpdateInterval: 0.1  // 100ms
    )

    /// 高质量配置（更低的延迟）
    static let highQuality = AudioConfiguration(
        bufferSize: 2048,
        sampleRate: 16000,
        channels: 1,
        uiUpdateInterval: 0.05  // 50ms
    )

    /// 低功耗配置（更高的延迟，更低的功耗）
    static let lowPower = AudioConfiguration(
        bufferSize: 8192,
        sampleRate: 16000,
        channels: 1,
        uiUpdateInterval: 0.15  // 150ms
    )
}

// MARK: - VAD Configuration
/// VAD 配置
struct VADConfiguration {
    /// WebRTC VAD 模式（0=严格, 1=低, 2=中, 3=高）
    let mode: Int32
    /// 确认打断所需的持续语音时间（秒）
    let interruptionConfirmationDuration: TimeInterval
    /// VAD 帧大小（必须是 WebRTC 支持的值: 80, 160, 240, 320, 480, 640）
    let frameSize: Int
    /// 语音结束后等待时间（秒）- 检测到静音后等待多久才确认说话结束
    let silenceWaitDuration: TimeInterval
    /// ASR 最终结果超时时间（秒）- 调用 endAudio() 后等待 isFinal 的最长时间
    let asrFinalTimeout: TimeInterval

    /// 默认配置
    static let `default` = VADConfiguration(
        mode: 2,                              // 中等敏感度
        interruptionConfirmationDuration: 0.5,  // 0.5 秒确认打断
        frameSize: 480,                       // 30ms @ 16kHz
        silenceWaitDuration: 1.5,             // 1.5秒静音确认
        asrFinalTimeout: 3.0                  // 3秒超时保护
    )

    /// 快速响应配置（更低延迟，可能误判）
    static let responsive = VADConfiguration(
        mode: 2,
        interruptionConfirmationDuration: 0.3,
        frameSize: 480,
        silenceWaitDuration: 0.8,
        asrFinalTimeout: 2.0
    )

    /// 高准确度配置（更高准确度，延迟更大）
    static let accurate = VADConfiguration(
        mode: 1,
        interruptionConfirmationDuration: 0.8,
        frameSize: 480,
        silenceWaitDuration: 2.0,
        asrFinalTimeout: 4.0
    )
}
