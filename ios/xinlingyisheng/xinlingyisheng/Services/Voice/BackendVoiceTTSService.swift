import Foundation
import AVFoundation
import Combine
import Starscream

// MARK: - Backend Voice TTS Configuration
/// 后端 TTS 服务配置
struct BackendVoiceTTSConfig {
    /// 后端 WebSocket 基础地址
    let baseURL: String
    /// 用户认证 token
    let token: String
    /// 音色
    let voice: BackendVoiceVoice

    static let `default` = BackendVoiceTTSConfig(
        baseURL: BackendVoiceConfig.baseURL,
        token: BackendVoiceConfig.defaultToken,
        voice: .cherry
    )
}

// MARK: - Backend Voice
enum BackendVoiceVoice: String {
    case cherry = "Cherry"
    case xiaoyun = "Xiaoyun"
    case xiaohan = "Xiaohan"
    case xiaomeng = "Xiaomeng"
    case xiaoxiao = "Xiaoxiao"
    case xiaoyan = "Xiaoyan"

    var displayName: String {
        switch self {
        case .cherry: return "Cherry (对话女声)"
        case .xiaoyun: return "小云 (温柔女声)"
        case .xiaohan: return "小涵 (活泼女声)"
        case .xiaomeng: return "小梦 (可爱女声)"
        case .xiaoxiao: return "晓晓 (知性女声)"
        case .xiaoyan: return "小燕 (自然女声)"
        }
    }
}

// MARK: - Backend Voice TTS Service
/// 后端 TTS 语音合成服务 (长连接模式)
/// 连接后端 /ws/voice/tts 端点，不暴露 API Key
@MainActor
class BackendVoiceTTSService: NSObject, ObservableObject {

    // MARK: - Published State
    @Published var isPlaying = false
    @Published var isConnecting = false
    @Published var isConnected = false

    // MARK: - Callbacks
    var onSynthesisComplete: (() -> Void)?
    var onError: ((Error) -> Void)?
    var onAudioChunk: ((Data) -> Void)?

    // MARK: - Private Properties
    private let config: BackendVoiceTTSConfig
    private var webSocket: Starscream.WebSocket?

    // 流式播放器
    private var pcmPlayer: StreamingPCMPlayer?
    private var synthesisCompletionHandler: (() -> Void)?

    // MARK: - Init
    init(config: BackendVoiceTTSConfig = .default) {
        self.config = config
        super.init()
    }

    deinit {
        // 清理资源
        webSocket?.disconnect()
        webSocket = nil
    }

    // MARK: - Public Methods

    /// 启动 TTS 长连接
    func start() async throws {
        guard !isConnected else { return }

        print("[BackendVoiceTTS] 启动 TTS 长连接")

        isConnecting = true

        // 构建 WebSocket URL
        var components = URLComponents(string: config.baseURL)!
        components.path = "/ws/voice/tts"
        components.queryItems = [
            URLQueryItem(name: "token", value: config.token)
        ]

        guard let url = components.url else {
            throw BackendVoiceTTSError.invalidURL
        }

        print("[BackendVoiceTTS] 连接: \(url.absoluteString)")

        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 5_000_000_000)

        guard isConnected else {
            throw BackendVoiceTTSError.connectionFailed
        }

        print("[BackendVoiceTTS] 长连接已建立")
        isConnecting = false
    }

    /// 流式合成并播放 (复用长连接)
    func synthesizeAndPlay(text: String) async throws {
        guard !text.isEmpty else { return }

        print("[BackendVoiceTTS] 合成: \(text.prefix(50))...")

        // 确保已连接
        if !isConnected {
            print("[BackendVoiceTTS] 连接未建立，尝试连接...")
            try await start()
        }

        // 创建流式播放器 (24kHz, 单声道, 16-bit)
        let player = StreamingPCMPlayer(sampleRate: 24000, channels: 1)
        player.onPlaybackFinished = { [weak self] in
            self?.isPlaying = false
            self?.onSynthesisComplete?()
            print("[BackendVoiceTTS] 播放完成")
        }
        player.onError = { [weak self] error in
            self?.isPlaying = false
            self?.onError?(error)
        }
        self.pcmPlayer = player

        try player.start()

        // 发送合成请求 (长连接协议)
        try await performSynthesis(text: text)
    }

    /// 停止合成并关闭连接
    func stop() {
        print("[BackendVoiceTTS] 停止并关闭连接")

        isPlaying = false
        isConnected = false
        isConnecting = false

        pcmPlayer?.stop()
        pcmPlayer = nil

        webSocket?.disconnect()
        webSocket = nil
    }

    /// 停止当前播放，但保持连接
    func stopPlaying() {
        pcmPlayer?.stop()
        pcmPlayer = nil
        isPlaying = false
    }

    // MARK: - Private Methods

    /// 执行语音合成 (长连接协议)
    private func performSynthesis(text: String) async throws {
        try await withCheckedThrowingContinuation { continuation in
            self.synthesisCompletionHandler = {
                self.synthesisCompletionHandler = nil
                self.isPlaying = false
                continuation.resume()
            }

            Task { @MainActor in
                // 发送合成请求 (长连接协议格式)
                let request: [String: Any] = [
                    "action": "speak",
                    "text": text,
                    "voice": config.voice.rawValue
                ]

                if let jsonData = try? JSONSerialization.data(withJSONObject: request, options: []),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    webSocket?.write(string: jsonString)
                    print("[BackendVoiceTTS] 已发送合成请求")
                }
            }

            // 超时保护
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                if self.synthesisCompletionHandler != nil {
                    continuation.resume(throwing: BackendVoiceTTSError.synthesisFailed("合成超时"))
                }
            }
        }
    }
}

// MARK: - Backend Voice TTS Error
enum BackendVoiceTTSError: LocalizedError {
    case invalidURL
    case connectionFailed
    case synthesisFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "无效的 URL"
        case .connectionFailed:
            return "WebSocket 连接失败"
        case .synthesisFailed(let message):
            return "语音合成失败: \(message)"
        }
    }
}

// MARK: - WebSocket Delegate
extension BackendVoiceTTSService: WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        // 确保所有 UI 相关操作在主线程执行
        Task { @MainActor in
            switch event {
            case .connected:
                print("[BackendVoiceTTS] WebSocket 已连接")
                isConnected = true
                isConnecting = false

            case .disconnected(let reason, let code):
                print("[BackendVoiceTTS] WebSocket 断开: \(reason) (code: \(code))")
                isConnected = false
                isConnecting = false

            case .binary(let data):
                // 二进制音频数据 - 直接送入播放器
                pcmPlayer?.writePCM(data)
                onAudioChunk?(data)

            case .text(let text):
                handleTextMessage(text)

            case .ping(_), .pong(_), .viabilityChanged(_), .reconnectSuggested(_), .cancelled:
                break

            case .peerClosed:
                isConnected = false
                isConnecting = false

            case .error(let error):
                print("[BackendVoiceTTS] WebSocket 错误: \(error?.localizedDescription ?? "未知")")
                isConnected = false
                isConnecting = false
            }
        }
    }

    private func handleTextMessage(_ text: String) {
        guard !text.isEmpty else { return }

        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }

        guard let eventType = json["event"] as? String else { return }

        switch eventType {
        case "tts_ready":
            print("[BackendVoiceTTS] 后端准备就绪 (长连接已建立)")

        case "tts_finished":
            print("[BackendVoiceTTS] 音频传输完成")
            pcmPlayer?.markInputFinished()
            synthesisCompletionHandler?()

        case "error":
            let errorMsg = json["message"] as? String ?? "未知错误"
            print("[BackendVoiceTTS] 错误: \(errorMsg)")
            onError?(BackendVoiceTTSError.synthesisFailed(errorMsg))
            synthesisCompletionHandler?()

        default:
            print("[BackendVoiceTTS] 未知事件: \(eventType)")
        }
    }
}

// MARK: - Streaming PCM Player
/// 流式 PCM 播放器
@MainActor
private class StreamingPCMPlayer: NSObject {

    private let sampleRate: Double
    private let channels: UInt32
    private let audioFormat: AVAudioFormat

    private let audioEngine = AVAudioEngine()
    private let playerNode = AVAudioPlayerNode()

    private var isPlaying = false
    private var audioBuffer: Data = Data()
    private var inputFinished = false  // 输入是否已完成
    private var pendingBuffers = 0     // 待播放的缓冲区数量

    // 检查播放完成的定时器
    private var finishCheckTimer: Timer?

    var onPlaybackFinished: (() -> Void)?
    var onError: ((Error) -> Void)?

    init(sampleRate: Double, channels: UInt32) {
        self.sampleRate = sampleRate
        self.channels = channels

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

    deinit {
        // 清理定时器
        finishCheckTimer?.invalidate()
        finishCheckTimer = nil
    }

    func start() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .default)
        try audioSession.setActive(true)

        audioEngine.prepare()
        try audioEngine.start()

        playerNode.play()
        isPlaying = true
        pendingBuffers = 0

        print("[StreamingPCMPlayer] 播放器已启动 (\(sampleRate)Hz, \(channels)ch)")
    }

    func writePCM(_ data: Data) {
        guard isPlaying else { return }

        // 将数据添加到缓冲区
        audioBuffer.append(data)

        // 尝试调度播放
        scheduleBuffer()
    }

    func markInputFinished() {
        // 标记输入已完成，启动完成检查
        inputFinished = true
        startFinishCheck()
    }

    func stop() {
        guard isPlaying else { return }

        playerNode.stop()
        audioEngine.stop()

        isPlaying = false
        audioBuffer.removeAll()
        inputFinished = false
        pendingBuffers = 0

        finishCheckTimer?.invalidate()
        finishCheckTimer = nil

        print("[StreamingPCMPlayer] 播放器已停止")
    }

    private func scheduleBuffer() {
        guard isPlaying, !audioBuffer.isEmpty else { return }

        // 每次调度一小块数据
        let chunkSize = 4800 * 2  // 约 200ms @ 24kHz
        let dataSize = min(audioBuffer.count, chunkSize)

        guard let buffer = AVAudioPCMBuffer(
            pcmFormat: audioFormat,
            frameCapacity: AVAudioFrameCount(dataSize / 2)
        ) else {
            return
        }

        buffer.frameLength = AVAudioFrameCount(dataSize / 2)

        guard let channelData = buffer.int16ChannelData else { return }

        // 复制数据到缓冲区
        audioBuffer.withUnsafeBytes { rawPtr in
            guard let baseAddr = rawPtr.baseAddress?.assumingMemoryBound(to: Int16.self) else {
                return
            }
            for i in 0..<Int(buffer.frameLength) {
                channelData[0][i] = baseAddr[i]
            }
        }

        // 从缓冲区移除已调度的数据
        audioBuffer.removeFirst(dataSize)

        // 增加待播放计数
        pendingBuffers += 1

        // 调度播放
        playerNode.scheduleBuffer(buffer) { [weak self] in
            // 播放完成回调
            self?.pendingBuffers -= 1
            // 播放完成后，尝试调度下一块
            self?.scheduleBuffer()
        }
    }

    private func startFinishCheck() {
        // 定期检查是否播放完成
        finishCheckTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self else { return }

            // 播放完成的条件：输入已完成 + 缓冲区为空 + 没有待播放的缓冲区
            if self.inputFinished && self.audioBuffer.isEmpty && self.pendingBuffers == 0 {
                print("[StreamingPCMPlayer] 播放完成检测: inputFinished=\(self.inputFinished), bufferEmpty=\(self.audioBuffer.isEmpty), pending=\(self.pendingBuffers)")
                self.onPlaybackFinished?()
                self.finishCheckTimer?.invalidate()
                self.finishCheckTimer = nil
            }
        }
    }
}
