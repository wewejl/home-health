import Foundation
import AVFoundation
import Combine
import Starscream

// MARK: - Streaming Audio Player
/// 流式音频播放器 - 使用 AVAudioEngine 实现 PCM 流式播放
@MainActor
private class StreamingAudioPlayer: NSObject {
    // MARK: - Configuration
    private let sampleRate: Double = 24000.0
    private let channels: UInt32 = 1
    private let primeBufferFrames: AVAudioFrameCount = 12000  // 500ms @ 24kHz 预热
    private let maxBufferFrames: AVAudioFrameCount = 72000    // 3秒最大缓冲

    // MARK: - AVAudio Engine Components
    private let audioEngine: AVAudioEngine
    private let playerNode: AVAudioPlayerNode
    private let audioFormat: AVAudioFormat

    // MARK: - Ring Buffer
    private var ringBuffer: [Int16] = []
    private var bufferLock = NSLock()
    private var readHead = 0
    private var writeHead = 0
    private var totalWritten = 0
    private var totalRead = 0

    // MARK: - State
    private(set) var isPlaying = false
    private(set) var isPrimed = false
    private var hasFinished = false
    private var silenceBuffer: AVAudioPCMBuffer?
    private var scheduledBuffersCount = 0  // 跟踪待播放的缓冲区数量

    // MARK: - Callbacks
    var onPlaybackFinished: (() -> Void)?
    var onError: ((Error) -> Void)?

    // MARK: - Computed Properties
    private var bufferSize: Int {
        Int(maxBufferFrames)
    }

    var availableFrames: Int {
        bufferLock.lock()
        defer { bufferLock.unlock() }
        return totalWritten - totalRead
    }

    var bufferLevel: Double {
        Double(availableFrames) / Double(bufferSize)
    }

    // MARK: - Init
    override init() {
        // 创建音频格式：24kHz, 单声道, Int16
        self.audioFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: sampleRate,
            channels: channels,
            interleaved: false
       )!

        self.audioEngine = AVAudioEngine()
        self.playerNode = AVAudioPlayerNode()

        super.init()

        // 初始化环形缓冲区
        ringBuffer = Array(repeating: 0, count: bufferSize)

        // 创建 silence 缓冲区
        if let silence = AVAudioPCMBuffer(pcmFormat: audioFormat, frameCapacity: 4800) {
            silence.frameLength = 4800
            // 填充静音数据
            if let channelData = silence.int16ChannelData {
                for frame in 0..<Int(silence.frameLength) {
                    channelData[0][frame] = 0
                }
            }
            silenceBuffer = silence
        }

        // 连接节点
        audioEngine.attach(playerNode)
        audioEngine.connect(playerNode, to: audioEngine.mainMixerNode, format: audioFormat)

        // 监听播放完成
        audioEngine.mainMixerNode.installTap(
            onBus: 0,
            bufferSize: 1024,
            format: audioFormat
        ) { [weak self] buffer, _ in
            guard let self = self else { return }
            // 检查是否播放完成
            if self.hasFinished && self.availableFrames == 0 && self.isPlaying {
                Task { @MainActor in
                    self.stop()
                    self.onPlaybackFinished?()
                }
            }
        }
    }

    deinit {
        // 在 deinit 中无法使用 @MainActor，直接清理
        playerNode.stop()
        audioEngine.stop()
    }

    // MARK: - Public Methods

    /// 开始播放
    func start() throws {
        guard !isPlaying else { return }

        // 配置音频会话
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .default)
        try audioSession.setActive(true)

        // 启动引擎
        audioEngine.prepare()
        try audioEngine.start()

        playerNode.play()
        isPlaying = true
        isPrimed = false
        hasFinished = false
        scheduledBuffersCount = 0

        print("[StreamingAudioPlayer] 播放器已启动，格式: \(sampleRate)Hz, Int16")
    }

    /// 写入 PCM 数据
    func writePCM(_ data: Data) {
        bufferLock.lock()
        defer { bufferLock.unlock() }

        // 将 Data 转换为 [Int16]
        let frames = data.count / MemoryLayout<Int16>.stride
        data.withUnsafeBytes { rawBuffer in
            guard let baseAddr = rawBuffer.baseAddress?.assumingMemoryBound(to: Int16.self) else {
                return
            }

            for i in 0..<frames {
                ringBuffer[writeHead] = baseAddr[i]
                writeHead = (writeHead + 1) % bufferSize
                totalWritten += 1
            }
        }

        // 检查是否达到预热阈值
        if !isPrimed && availableFrames >= Int(primeBufferFrames) {
            isPrimed = true
            Task { @MainActor in
                self.scheduleBuffers()
            }
        } else if isPrimed {
            Task { @MainActor in
                self.scheduleBuffers()
            }
        }
    }

    /// 标记输入完成
    func markInputFinished() {
        hasFinished = true
        print("[StreamingAudioPlayer] 输入完成标记")
    }

    /// 停止播放
    func stop() {
        guard isPlaying else { return }

        playerNode.stop()
        audioEngine.stop()

        isPlaying = false
        isPrimed = false

        // 重置缓冲区
        bufferLock.lock()
        readHead = 0
        writeHead = 0
        totalWritten = 0
        totalRead = 0
        bufferLock.unlock()

        print("[StreamingAudioPlayer] 播放器已停止")
    }

    // MARK: - Private Methods

    /// 调度音频缓冲区到播放节点
    private func scheduleBuffers() {
        guard isPlaying, isPrimed else { return }

        // 如果缓冲区太满，等待
        if scheduledBuffersCount >= 3 {
            return
        }

        // 读取一帧数据
        guard let buffer = readFrames(frameCount: 4800) else {  // 200ms
            return
        }

        scheduledBuffersCount += 1
        playerNode.scheduleBuffer(buffer) { [weak self] in
            // 播放完这块后，继续调度
            guard let self = self else { return }
            self.scheduledBuffersCount -= 1
            Task { @MainActor in
                self.scheduleBuffers()
            }
        }
    }

    /// 从环形缓冲区读取帧
    private func readFrames(frameCount: AVAudioFrameCount) -> AVAudioPCMBuffer? {
        bufferLock.lock()
        defer { bufferLock.unlock() }

        guard let buffer = AVAudioPCMBuffer(pcmFormat: audioFormat, frameCapacity: frameCount) else {
            return nil
        }

        let actualFrames = min(frameCount, AVAudioFrameCount(availableFrames))
        guard actualFrames > 0 else {
            // 没有数据，返回 silence 避免断流
            return hasFinished ? nil : silenceBuffer
        }

        buffer.frameLength = actualFrames

        guard let channelData = buffer.int16ChannelData else {
            return nil
        }

        // 读取数据
        for i in 0..<Int(actualFrames) {
            channelData[0][i] = ringBuffer[readHead]
            readHead = (readHead + 1) % bufferSize
            totalRead += 1
        }

        return buffer
    }
}

// MARK: - CosyVoice Configuration
/// CosyVoice TTS 配置
struct CosyVoiceConfig {
    /// API Key
    let apiKey: String
    /// WebSocket 端点
    let endpoint: String
    /// 模型类型
    let model: CosyVoiceModel
    /// 音色
    let voice: CosyVoiceVoice

    /// 从 BackendASRConfig 创建默认配置
    static let `default` = CosyVoiceConfig(
        apiKey: BackendASRConfig.apiKey,
        endpoint: "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
        model: .v3Flash,
        voice: .longanyang
    )
}

// MARK: - CosyVoice Model
/// CosyVoice 模型类型
enum CosyVoiceModel: String, CaseIterable {
    case v1 = "cosyvoice-v1"
    case v2 = "cosyvoice-v2"
    case v3Flash = "cosyvoice-v3-flash"
    case v3Plus = "cosyvoice-v3-plus"

    var displayName: String {
        switch self {
        case .v1: return "CosyVoice V1"
        case .v2: return "CosyVoice V2"
        case .v3Flash: return "CosyVoice V3 Flash"
        case .v3Plus: return "CosyVoice V3 Plus"
        }
    }
}

// MARK: - CosyVoice Voice
/// CosyVoice 音色
enum CosyVoiceVoice: String, CaseIterable {
    case longanyang = "longanyang"
    case zhibei = "zhibei"
    case zhichu = "zhichu_v2"
    case longxiaochun = "longxiaochun_v2"
    case aijia = "aijia_v2"
    case longwan = "longwan"

    var displayName: String {
        switch self {
        case .longanyang: return "龙安"
        case .zhibei: return "志北"
        case .zhichu: return "知楚"
        case .longxiaochun: return "龙小春"
        case .aijia: return "爱佳"
        case .longwan: return "龙湾"
        }
    }

    func isCompatible(with model: CosyVoiceModel) -> Bool {
        switch model {
        case .v1:
            return self == .longwan
        case .v2:
            return self == .zhichu || self == .longxiaochun || self == .aijia
        case .v3Flash, .v3Plus:
            return self == .longanyang || self == .zhibei
        }
    }
}

// MARK: - CosyVoice TTS Service
/// CosyVoice 云端 TTS 服务
/// 使用 PCM 格式 + AVAudioEngine 实现真正的流式播放
@MainActor
class CosyVoiceTTSService: NSObject, ObservableObject {

    // MARK: - Published State
    @Published var isPlaying = false
    @Published var isConnecting = false

    // MARK: - Callbacks
    var onSynthesisComplete: (() -> Void)?
    var onError: ((Error) -> Void)?

    // MARK: - Private Properties
    private let config: CosyVoiceConfig
    private var webSocket: Starscream.WebSocket?
    private var isSynthesizing = false
    private var isWebSocketConnected = false

    // 协议状态
    private var taskStarted = false
    private var taskID: String = ""

    // 流式播放器
    private var streamingPlayer: StreamingAudioPlayer?
    private var synthesisCompletionHandler: (() -> Void)?

    // MARK: - Init
    init(config: CosyVoiceConfig = .default) {
        self.config = config
        super.init()
    }

    deinit {
        Task { @MainActor in
            self.stop()
        }
    }

    // MARK: - Public Methods

    /// 流式合成并播放
    /// - Parameter text: 要合成的文本
    func synthesizeAndPlay(text: String) async throws {
        guard !text.isEmpty else { return }

        print("[CosyVoiceTTS] 开始流式合成文本: \(text.prefix(50))...")

        // 创建流式播放器
        let player = StreamingAudioPlayer()
        player.onPlaybackFinished = { [weak self] in
            self?.isPlaying = false
            self?.onSynthesisComplete?()
            print("[CosyVoiceTTS] 播放完成")
        }
        player.onError = { [weak self] error in
            self?.isPlaying = false
            self?.onError?(error)
        }
        self.streamingPlayer = player

        // 启动播放器（预热状态）
        try player.start()

        // 连接 WebSocket
        try await connectWebSocket()

        // 执行合成
        try await performSynthesis(text: text, model: config.model, voice: config.voice)

        print("[CosyVoiceTTS] 合成完成")
    }

    /// 停止合成
    func stop() {
        print("[CosyVoiceTTS] 停止合成")

        isSynthesizing = false
        streamingPlayer?.stop()
        streamingPlayer = nil
        webSocket?.disconnect()

        isPlaying = false
    }

    // MARK: - Private Methods

    private func connectWebSocket() async throws {
        guard !isWebSocketConnected else { return }

        taskID = UUID().uuidString

        var request = URLRequest(url: URL(string: config.endpoint)!)
        request.setValue("Bearer \(config.apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("enable", forHTTPHeaderField: "X-DashScope-DataInspection")

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 2_000_000_000)

        guard isWebSocketConnected else {
            throw CosyVoiceError.connectionFailed
        }

        print("[CosyVoiceTTS] WebSocket 已连接")
    }

    private func disconnectWebSocket() {
        isWebSocketConnected = false
        taskStarted = false
        webSocket?.disconnect()
        webSocket = nil
    }

    /// 执行语音合成
    private func performSynthesis(
        text: String,
        model: CosyVoiceModel,
        voice: CosyVoiceVoice
    ) async throws {
        return try await withCheckedThrowingContinuation { continuation in
            // 设置完成回调
            self.synthesisCompletionHandler = {
                self.synthesisCompletionHandler = nil
                continuation.resume()
            }

            // 在后台任务中执行协议流程
            Task { @MainActor in
                do {
                    // 1. 发送 run-task 指令
                    self.sendRunTask(model: model, voice: voice)

                    // 2. 等待 task-started
                    var waited = 0
                    while !self.taskStarted && waited < 50 {
                        try? await Task.sleep(nanoseconds: 100_000_000)
                        waited += 1
                    }

                    guard self.taskStarted else {
                        continuation.resume(throwing: CosyVoiceError.synthesisFailed("等待 task-started 超时"))
                        return
                    }

                    // 3. 发送 continue-task 指令
                    self.sendContinueTask(text: text)

                    // 4. 短暂延迟后发送 finish-task
                    try? await Task.sleep(nanoseconds: 500_000_000)
                    self.sendFinishTask()

                } catch {
                    continuation.resume(throwing: CosyVoiceError.synthesisFailed(error.localizedDescription))
                }
            }

            // 超时保护
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                if self.synthesisCompletionHandler != nil {
                    continuation.resume(throwing: CosyVoiceError.synthesisFailed("合成超时"))
                }
            }
        }
    }

    /// 发送 run-task 指令
    private func sendRunTask(model: CosyVoiceModel, voice: CosyVoiceVoice) {
        let runTask: [String: Any] = [
            "header": [
                "action": "run-task",
                "task_id": taskID,
                "streaming": "duplex"
            ],
            "payload": [
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "model": model.rawValue,
                "parameters": [
                    "text_type": "PlainText",
                    "voice": voice.rawValue,
                    "format": "pcm",           // 改为 PCM 格式，支持流式播放
                    "sample_rate": 24000,      // 24kHz 采样率
                    "audio_format": "raw",     // 原始 PCM（无头部）
                    "volume": 50,
                    "rate": 1.0,
                    "pitch": 1.0
                ],
                "input": [String: String]()
            ]
        ]

        if let jsonData = try? JSONSerialization.data(withJSONObject: runTask, options: []),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            webSocket?.write(string: jsonString)
            print("[CosyVoiceTTS] 发送 run-task: \(model.rawValue), voice: \(voice.rawValue), format: pcm, sample_rate: 24000")
        }
    }

    /// 发送 continue-task 指令
    private func sendContinueTask(text: String) {
        let continueTask: [String: Any] = [
            "header": [
                "action": "continue-task",
                "task_id": taskID,
                "streaming": "duplex"
            ],
            "payload": [
                "input": [
                    "text": text
                ]
            ]
        ]

        if let jsonData = try? JSONSerialization.data(withJSONObject: continueTask, options: []),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            webSocket?.write(string: jsonString)
            print("[CosyVoiceTTS] 发送 continue-task，文本: \(text.prefix(30))...")
        }
    }

    /// 发送 finish-task 指令
    private func sendFinishTask() {
        let finishTask: [String: Any] = [
            "header": [
                "action": "finish-task",
                "task_id": taskID,
                "streaming": "duplex"
            ],
            "payload": [
                "input": [String: String]()
            ]
        ]

        if let jsonData = try? JSONSerialization.data(withJSONObject: finishTask, options: []),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            webSocket?.write(string: jsonString)
            print("[CosyVoiceTTS] 发送 finish-task")
        }
    }

    /// 处理接收到的音频数据 - 流式写入播放器
    private func handleAudioData(_ data: Data) {
        streamingPlayer?.writePCM(data)
        print("[CosyVoiceTTS] 收到 PCM 音频块: \(data.count) bytes")
    }
}

// MARK: - CosyVoice Error
enum CosyVoiceError: LocalizedError {
    case invalidAPIKey
    case connectionFailed
    case synthesisFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidAPIKey:
            return "API Key 无效"
        case .connectionFailed:
            return "WebSocket 连接失败"
        case .synthesisFailed(let message):
            return "语音合成失败: \(message)"
        }
    }
}

// MARK: - WebSocket Delegate
extension CosyVoiceTTSService: Starscream.WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: Starscream.WebSocketClient) {
        switch event {
        case .connected:
            print("[CosyVoiceTTS] WebSocket 已连接")
            isWebSocketConnected = true

        case .disconnected(let reason, let code):
            print("[CosyVoiceTTS] WebSocket 断开: \(reason) (code: \(code))")
            isWebSocketConnected = false

        case .binary(let data):
            handleAudioData(data)

        case .text(let text):
            handleTextMessage(text)

        case .ping(_), .pong(_), .viabilityChanged(_), .reconnectSuggested(_), .cancelled:
            break

        case .peerClosed:
            isWebSocketConnected = false
            break

        case .error(let error):
            print("[CosyVoiceTTS] WebSocket 错误: \(error?.localizedDescription ?? "未知错误")")
            isWebSocketConnected = false
        }
    }

    private func handleTextMessage(_ text: String) {
        guard !text.isEmpty else { return }

        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }

        guard let header = json["header"] as? [String: Any],
              let event = header["event"] as? String else {
            return
        }

        switch event {
        case "task-started":
            print("[CosyVoiceTTS] Task started")
            taskStarted = true

        case "task-finished":
            print("[CosyVoiceTTS] Task finished")
            // 标记输入完成，播放器会自动播放完缓冲区内容
            streamingPlayer?.markInputFinished()
            synthesisCompletionHandler?()

        case "task-failed":
            let errorMsg = header["error_message"] as? String ?? "未知错误"
            print("[CosyVoiceTTS] Task failed: \(errorMsg)")
            onError?(CosyVoiceError.synthesisFailed(errorMsg))
            synthesisCompletionHandler?()

        default:
            break
        }
    }
}
