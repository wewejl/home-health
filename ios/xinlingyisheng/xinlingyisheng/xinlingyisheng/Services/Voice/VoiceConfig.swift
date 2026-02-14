//
//  VoiceConfig.swift
//  灵犀医生
//
// 语音服务配置常量
//
//  注: TTS (Text-to-Speech) 功能已移除
//

import Foundation
import AVFoundation

// MARK: - 语音服务配置
/// 语音服务相关的配置常量
struct VoiceConfig {

    // MARK: - ASR 配置
    /// ASR 采样率 (Hz)
    static let asrSampleRate: Double = 16000

    /// ASR 声道数
    static let asrChannels: UInt32 = 1

    /// ASR 音频格式
    static let asrFormat = AudioFormatID(kAudioFormatLinearPCM)

    /// 音频缓冲区大小
    static let asrBufferSize: AVAudioFrameCount = 1024

    // MARK: - 超时配置
    /// 心跳间隔 (秒)
    static let heartbeatInterval: TimeInterval = 0.1

    /// 请求超时时间 (秒)
    static let requestTimeout: TimeInterval = 300.0

    /// 麦克风权限等待时间 (纳秒)
    static let micPermissionWaitTime: UInt64 = 500_000_000 // 500ms

    /// 停止录音后的等待时间 (纳秒)
    static let stopRecordingWaitTime: UInt64 = 300_000_000 // 300ms
}

// MARK: - WebSocket 语音事件
/// WebSocket 语音服务事件类型 (用于与后端通信)
enum VoiceEvent {
    case asrReady
    case asrPartial
    case asrFinal
    case asrRoundComplete
    case asrRoundReady
    case error(String)

    var eventName: String {
        switch self {
        case .asrReady: return "asr_ready"
        case .asrPartial: return "asr_partial"
        case .asrFinal: return "asr_final"
        case .asrRoundComplete: return "asr_round_complete"
        case .asrRoundReady: return "asr_round_ready"
        case .error: return "error"
        }
    }
}

// MARK: - WebSocket 语音错误扩展
/// WebSocket 语音服务错误类型扩展 (用于与后端通信，扩展 VoiceTypes.swift 的 VoiceError)
enum WebSocketVoiceError: Error {
    case microphonePermissionDenied
    case microphonePermissionUndetermined
    case audioEngineStartFailed
    case audioEngineNotFound
    case invalidURL
    case connectionFailed(underlying: Error)
    case recognitionFailed(underlying: Error)
    case disconnected
    case timeout
    case unauthorized

    var localizedDescription: String {
        switch self {
        case .microphonePermissionDenied:
            return "需要麦克风权限才能使用语音功能"
        case .microphonePermissionUndetermined:
            return "需要麦克风权限才能使用语音功能"
        case .audioEngineStartFailed:
            return "无法启动音频引擎"
        case .audioEngineNotFound:
            return "无法访问麦克风"
        case .invalidURL:
            return "语音服务地址无效"
        case .connectionFailed(let error):
            return "连接失败: \(error.localizedDescription)"
        case .recognitionFailed(let error):
            return "语音识别失败: \(error.localizedDescription)"
        case .disconnected:
            return "连接已断开"
        case .timeout:
            return "请求超时"
        case .unauthorized:
            return "未授权"
        }
    }

    var errorDescription: String? {
        localizedDescription
    }
}
