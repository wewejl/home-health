import Foundation
import AVFoundation
import Combine
import Starscream

// MARK: - Qwen TTS Realtime Configuration
/// Qwen TTS Realtime 配置
struct QwenTTSConfig {
    /// API Key (DashScope)
    let apiKey: String
    /// WebSocket 端点
    let endpoint: String
    /// 模型版本
    let model: QwenTTSModel
    /// 音色
    let voice: QwenVoice

    static let `default` = QwenTTSConfig(
        apiKey: BackendASRConfig.apiKey,
        endpoint: "wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
        model: .flash,
        voice: .cherry
    )
}

// MARK: - Qwen TTS Model
enum QwenTTSModel: String {
    case flash = "qwen3-tts-flash-realtime"
}

// MARK: - Qwen Voice
enum QwenVoice: String {
    case cherry = "Cherry"
    case aida = "Aida"
    case amelia = "Amelia"
    case ben = "Ben"
    case charlie = "Charlie"
    case daniel = "Daniel"
    case emma = "Emma"
    case flora = "Flora"
    case grace = "Grace"
    case hannah = "Hannah"
    case jenny = "Jenny"
    case john = "John"
    case kenny = "Kenny"
    case liliana = "Liliana"
    case lisa = "Lisa"
    case mallory = "Mallory"
    case nancy = "Nancy"
    case oliver = "Oliver"
    case patrick = "Patrick"
    case robert = "Robert"
    case ryan = "Ryan"
    case stephanie = "Stephanie"
    case steve = "Steve"
    case tim = "Tim"
    case yansong = "Yansong"
    case xiaoyun = "Xiaoyun"
    case xiaohan = "Xiaohan"
    case xiaomeng = "Xiaomeng"
    case xiaoxiao = "Xiaoxiao"
    case xiaoyan = "Xiaoyan"
    case xiaofen = "Xiaofen"

    var displayName: String {
        switch self {
        case .cherry: return "Cherry (对话女声)"
        case .xiaoyun: return "小云 (温柔女声)"
        case .xiaohan: return "小涵 (活泼女声)"
        case .xiaomeng: return "小梦 (可爱女声)"
        case .xiaoxiao: return "晓晓 (知性女声)"
        case .xiaoyan: return "小燕 (自然女声)"
        default: return rawValue
        }
    }
}

// MARK: - Simple PCM Player
/// 简单的 PCM 播放器 - 使用 AVAudioEngine
@MainActor
private class SimplePCMPlayer: NSObject {
    private let sampleRate: Double = 24000.0
    private let channels: UInt32 = 1
    private let audioFormat: AVAudioFormat

    private let audioEngine = AVAudioEngine()
    private let playerNode = AVAudioPlayerNode()

    private var isPlaying = false
    private var hasFinished = false

    var onPlaybackFinished: (() -> Void)?
    var onError: ((Error) -> Void)?

    override init() {
        self.audioFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: sampleRate,
            channels: channels,
            interleaved: false
        )!
        super.init()

        audioEngine.attach(playerNode)
        audioEngine.connect(playerNode, to: audioEngine.mainMixerNode, format: audioFormat)
    }

    func start() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .default)
        try audioSession.setActive(true)

        audioEngine.prepare()
        try audioEngine.start()

        playerNode.play()
        isPlaying = true
        hasFinished = false

        print("[SimplePCMPlayer] 已启动，格式: 24kHz Int16 单声道")
    }

    func writePCM(_ data: Data) {
        guard isPlaying else { return }

        guard let buffer = AVAudioPCMBuffer(
            pcmFormat: audioFormat,
            frameCapacity: AVAudioFrameCount(data.count / 2)
        ) else {
            return
        }

        buffer.frameLength = AVAudioFrameCount(data.count / 2)

        guard let channelData = buffer.int16ChannelData else { return }

        data.withUnsafeBytes { rawBuffer in
            guard let baseAddr = rawBuffer.baseAddress?.assumingMemoryBound(to: Int16.self) else {
                return
            }

            for i in 0..<Int(buffer.frameLength) {
                channelData[0][i] = baseAddr[i]
            }
        }

        playerNode.scheduleBuffer(buffer)
    }

    func markInputFinished() {
        hasFinished = true
        print("[SimplePCMPlayer] 输入完成")

        // 播放完缓冲后检查完成
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            if self?.hasFinished == true {
                self?.stop()
                self?.onPlaybackFinished?()
            }
        }
    }

    func stop() {
        guard isPlaying else { return }

        playerNode.stop()
        audioEngine.stop()
        isPlaying = false

        print("[SimplePCMPlayer] 已停止")
    }
}

// MARK: - Qwen TTS Realtime Service
/// Qwen TTS Realtime 服务
/// 协议更简单，首包延迟更低 (~400ms)
@MainActor
class QwenTTSRealtimeService: NSObject, ObservableObject {

    // MARK: - Published State
    @Published var isPlaying = false
    @Published var isConnecting = false

    // MARK: - Callbacks
    var onSynthesisComplete: (() -> Void)?
    var onError: ((Error) -> Void)?

    // MARK: - Private Properties
    private let config: QwenTTSConfig
    private var webSocket: Starscream.WebSocket?
    private var isWebSocketConnected = false

    // 流式播放器
    private var pcmPlayer: SimplePCMPlayer?

    // 会话状态
    private var sessionCreated = false
    private var synthesisCompletionHandler: (() -> Void)?

    // MARK: - Init
    init(config: QwenTTSConfig? = nil) {
        self.config = config ?? QwenTTSConfig(
            apiKey: BackendASRConfig.apiKey,
            endpoint: "wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
            model: .flash,
            voice: .cherry
        )
        super.init()
    }

    deinit {
        Task { @MainActor in
            self.stop()
        }
    }

    // MARK: - Public Methods

    /// 流式合成并播放
    func synthesizeAndPlay(text: String) async throws {
        guard !text.isEmpty else { return }

        print("[QwenTTS] 开始合成: \(text.prefix(50))...")

        // 创建播放器
        let player = SimplePCMPlayer()
        player.onPlaybackFinished = { [weak self] in
            self?.isPlaying = false
            self?.onSynthesisComplete?()
            print("[QwenTTS] 播放完成")
        }
        player.onError = { [weak self] error in
            self?.isPlaying = false
            self?.onError?(error)
        }
        self.pcmPlayer = player

        try player.start()

        // 连接 WebSocket
        try await connectWebSocket()

        // 执行合成
        try await performSynthesis(text: text)

        print("[QwenTTS] 合成完成")
    }

    /// 停止合成
    func stop() {
        print("[QwenTTS] 停止合成")

        pcmPlayer?.stop()
        pcmPlayer = nil
        webSocket?.disconnect()

        isPlaying = false
    }

    // MARK: - Private Methods

    private func connectWebSocket() async throws {
        guard !isWebSocketConnected else { return }

        // 在 URL 中添加模型参数
        let urlString = "\(config.endpoint)?model=\(config.model.rawValue)"
        guard let url = URL(string: urlString) else {
            throw QwenTTSError.connectionFailed
        }

        var request = URLRequest(url: url)
        request.setValue("Bearer \(config.apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("enable", forHTTPHeaderField: "X-DashScope-DataInspection")

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 3_000_000_000)

        guard isWebSocketConnected else {
            throw QwenTTSError.connectionFailed
        }

        print("[QwenTTS] WebSocket 已连接")
    }

    private func disconnectWebSocket() {
        isWebSocketConnected = false
        sessionCreated = false
        webSocket?.disconnect()
        webSocket = nil
    }

    /// 执行语音合成
    private func performSynthesis(text: String) async throws {
        try await withCheckedThrowingContinuation { continuation in
            self.synthesisCompletionHandler = {
                self.synthesisCompletionHandler = nil
                continuation.resume()
            }

            Task { @MainActor in
                // 1. session.update - 配置会话
                self.sendSessionUpdate()

                // 2. 等待 session.updated
                var waited = 0
                while !self.sessionCreated && waited < 50 {
                    try? await Task.sleep(nanoseconds: 100_000_000)
                    waited += 1
                }

                guard self.sessionCreated else {
                    continuation.resume(throwing: QwenTTSError.synthesisFailed("等待 session.created 超时"))
                    return
                }

                // 3. input_text_buffer.append - 发送文本
                self.sendAppendText(text)

                // 4. 短暂延迟后 finish
                try? await Task.sleep(nanoseconds: 100_000_000)
                self.sendFinish()
            }

            // 超时保护
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                if self.synthesisCompletionHandler != nil {
                    continuation.resume(throwing: QwenTTSError.synthesisFailed("合成超时"))
                }
            }
        }
    }

    /// 发送 session.update 事件
    private func sendSessionUpdate() {
        let event: [String: Any] = [
            "type": "session.update",
            "session": [
                "voice": config.voice.rawValue,
                "response_format": "pcm",  // 使用 "pcm" 而不是 "pcm_24000hz_mono_16bit"
                "mode": "server_commit"
            ]
        ]

        sendEvent(event)
        print("[QwenTTS] 发送 session.update")
    }

    /// 发送 input_text_buffer.append 事件
    private func sendAppendText(_ text: String) {
        let event: [String: Any] = [
            "type": "input_text_buffer.append",
            "text": text
        ]

        sendEvent(event)
        print("[QwenTTS] 发送 input_text_buffer.append: \(text.prefix(30))...")
    }

    /// 发送 session.finish 事件
    private func sendFinish() {
        let event: [String: Any] = [
            "type": "session.finish"
        ]

        sendEvent(event)
        print("[QwenTTS] 发送 session.finish")
    }

    private func sendEvent(_ event: [String: Any]) {
        guard let jsonData = try? JSONSerialization.data(withJSONObject: event, options: []),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            return
        }
        webSocket?.write(string: jsonString)
    }

    /// 处理接收到的音频数据
    private func handleAudioDelta(_ base64Data: String) {
        guard let data = Data(base64Encoded: base64Data) else {
            print("[QwenTTS] base64 解码失败")
            return
        }

        pcmPlayer?.writePCM(data)
        print("[QwenTTS] 收到音频: \(data.count) bytes")
    }
}

// MARK: - Qwen TTS Error
enum QwenTTSError: LocalizedError {
    case connectionFailed
    case synthesisFailed(String)

    var errorDescription: String? {
        switch self {
        case .connectionFailed:
            return "WebSocket 连接失败"
        case .synthesisFailed(let message):
            return "语音合成失败: \(message)"
        }
    }
}

// MARK: - WebSocket Delegate
extension QwenTTSRealtimeService: Starscream.WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: Starscream.WebSocketClient) {
        switch event {
        case .connected:
            print("[QwenTTS] WebSocket 已连接")
            isWebSocketConnected = true

        case .disconnected(let reason, let code):
            print("[QwenTTS] WebSocket 断开: \(reason) (code: \(code))")
            isWebSocketConnected = false

        case .binary(_):
            // 不处理二进制
            break

        case .text(let text):
            handleTextMessage(text)

        case .ping(_), .pong(_), .viabilityChanged(_), .reconnectSuggested(_), .cancelled:
            break

        case .peerClosed:
            isWebSocketConnected = false
            break

        case .error(let error):
            print("[QwenTTS] WebSocket 错误: \(error?.localizedDescription ?? "未知")")
            isWebSocketConnected = false
        }
    }

    private func handleTextMessage(_ text: String) {
        guard !text.isEmpty else { return }

        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }

        guard let eventType = json["type"] as? String else { return }

        switch eventType {
        case "session.created":
            print("[QwenTTS] session.created")
            sessionCreated = true

        case "session.updated":
            print("[QwenTTS] session.updated")

        case "input_text_buffer.committed":
            print("[QwenTTS] input_text_buffer.committed")

        case "response.audio.delta":
            if let delta = json["delta"] as? String {
                handleAudioDelta(delta)
            }

        case "response.audio.done":
            print("[QwenTTS] response.audio.done")

        case "response.done":
            print("[QwenTTS] response.done")

        case "session.finished":
            print("[QwenTTS] session.finished")
            pcmPlayer?.markInputFinished()
            synthesisCompletionHandler?()

        case "error":
            let errorMsg = json["message"] as? String ?? "未知错误"
            print("[QwenTTS] 错误: \(errorMsg)")
            onError?(QwenTTSError.synthesisFailed(errorMsg))

        default:
            print("[QwenTTS] 未知事件: \(eventType)")
        }
    }
}
