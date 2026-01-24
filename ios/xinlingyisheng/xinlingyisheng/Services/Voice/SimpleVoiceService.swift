import Foundation
import AVFoundation
import Combine
import Starscream

@preconcurrency import AVFAudio

// MARK: - Simple Voice Service (Singleton)
/// 简化版语音服务 - ASR 持续监听 + TTS 独立播放，互不干扰
/// 使用单例模式确保全局只有一个实例
@MainActor
class SimpleVoiceService: NSObject, ObservableObject {

    // MARK: - Singleton
    static let shared = SimpleVoiceService()

    // MARK: - Published State
    @Published var state: VoiceState = .idle
    @Published var recognizedText: String = ""

    // MARK: - Callbacks
    var onPartialResult: ((String) -> Void)?
    var onFinalResult: ((String) -> Void)?
    var onTTSEnded: (() -> Void)?
    var onError: ((VoiceError) -> Void)?

    // MARK: - Configuration
    private let baseURL: String
    private let token: String

    // MARK: - ASR Components
    private var asrWebSocket: Starscream.WebSocket?
    private var audioEngine: AVAudioEngine?
    private var inputNode: AVAudioInputNode?
    private let asrBufferSize: AVAudioFrameCount = 1024

    // MARK: - TTS Components
    private var ttsWebSocket: Starscream.WebSocket?
    private var audioPlayerNode = AVAudioPlayerNode()
    private var ttsAudioEngine: AVAudioEngine?
    private let ttsFormat: AVAudioFormat

    // MARK: - Debug Counters (非隔离用于音频线程访问)
    private nonisolated(unsafe) var audioSendCount = 0
    private var audioTapCount = 0

    // MARK: - State Flags (非隔离用于音频线程访问)
    private nonisolated(unsafe) private(set) var isASRConnected = false
    private nonisolated(unsafe) private(set) var isTTSConnected = false
    private var isTTSSpeaking = false
    private var pendingTTSBuffers = 0  // 待播放的 buffer 数量
    private var isTapInstalled = false  // tap 是否已安装（防止重复安装）

    // MARK: - Connection Continuation
    private var asrContinuation: CheckedContinuation<Void, Error>?
    private var ttsContinuation: CheckedContinuation<Void, Error>?

    // MARK: - Init (private for singleton)
    private override init() {
        self.baseURL = BackendVoiceConfig.baseURL
        self.token = BackendVoiceConfig.defaultToken

        // TTS 音频格式: 24kHz, 单声道, 16-bit PCM
        self.ttsFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: 24000,
            channels: 1,
            interleaved: false
        )!

        super.init()
        print("[SimpleVoiceService] 单例初始化完成")
    }

    deinit {
        // 直接清理，不使用 async（deinit 不能是 async）
        asrWebSocket?.disconnect()
        ttsWebSocket?.disconnect()
        audioEngine?.stop()
        ttsAudioEngine?.stop()
    }

    // MARK: - Public Methods

    /// 启动语音服务（ASR 和 TTS）
    func start() async throws {
        print("[SimpleVoiceService] 启动语音服务")

        // 启动 ASR
        try await startASR()

        // 启动 TTS
        try await startTTS()

        // 启动音频采集
        try startAudioEngine()

        state = .listening
        print("[SimpleVoiceService] 语音服务已启动")
    }

    /// 停止语音服务
    func stop() {
        print("[SimpleVoiceService] 停止语音服务")

        // 停止 ASR
        asrWebSocket?.disconnect()
        asrWebSocket = nil
        isASRConnected = false

        // 停止 TTS
        stopTTS()

        // 停止音频引擎
        audioEngine?.stop()
        inputNode?.removeTap(onBus: 0)

        // 清理状态
        recognizedText = ""
        state = .idle
    }

    /// 播报 AI 回复
    func speak(_ text: String) async throws {
        guard !text.isEmpty else { return }

        if !isTTSConnected {
            print("[SimpleVoiceService] TTS 未连接，尝试重连...")
            try await startTTS()
        }

        print("[SimpleVoiceService] 播报: \(text.prefix(50))...")
        isTTSSpeaking = true
        state = .aiSpeaking
        pendingTTSBuffers = 0  // 重置计数器

        // 发送合成请求
        let request: [String: Any] = [
            "action": "speak",
            "text": text,
            "voice": "Cherry"
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: request),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            throw VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -1))
        }

        ttsWebSocket?.write(string: jsonString)
    }

    /// 暂停 ASR 录音并断开连接（识别完成后调用）
    func pauseRecording() {
        inputNode?.removeTap(onBus: 0)
        isTapInstalled = false

        // 主动断开 ASR 连接（用完就断）
        asrWebSocket?.disconnect()
        asrWebSocket = nil
        isASRConnected = false

        print("[SimpleVoiceService] ASR 已断开（识别完成）")
    }

    /// 开始新一轮识别（需要时重新连接）
    func startRecording() async throws {
        // 如果 ASR 未连接，重新连接
        if !isASRConnected {
            print("[SimpleVoiceService] 重新连接 ASR")
            try await startASR()
        }

        // 恢复录音 tap
        resumeASRRecording()
    }

    /// 停止 TTS 播放
    func stopTTS() {
        guard isTTSSpeaking else { return }

        print("[SimpleVoiceService] 停止 TTS 播放")
        isTTSSpeaking = false

        // 停止播放器
        audioPlayerNode.stop()
        ttsAudioEngine?.stop()

        state = isASRConnected ? .listening : .idle
    }

    // MARK: - Private Methods - ASR

    /// 恢复 ASR 录音（TTS 播放完成后调用）
    private func resumeASRRecording() {
        guard let inputNode = inputNode, let audioEngine = audioEngine, audioEngine.isRunning else {
            return
        }

        // 防止重复安装 tap
        if isTapInstalled {
            print("[SimpleVoiceService] Tap 已存在，跳过安装")
            return
        }

        let inputFormat = inputNode.outputFormat(forBus: 0)

        // 重新安装 tap
        inputNode.installTap(
            onBus: 0,
            bufferSize: asrBufferSize,
            format: inputFormat
        ) { [weak self] buffer, _ in
            guard let self = self else { return }
            self.processAndSendAudio(buffer)
        }

        isTapInstalled = true
        print("[SimpleVoiceService] ASR 录音已恢复")
    }

    private func startASR() async throws {
        var components = URLComponents(string: baseURL)!
        components.path = "/ws/voice/asr"
        components.queryItems = [URLQueryItem(name: "token", value: token)]

        guard let url = components.url else {
            throw VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -1))
        }

        print("[SimpleVoiceService] ASR 连接: \(url.absoluteString)")

        // 使用 continuation 等待连接成功（无超时限制）
        try await withCheckedThrowingContinuation { continuation in
            asrContinuation = continuation
            asrWebSocket = WebSocket(request: URLRequest(url: url))
            asrWebSocket?.delegate = self
            asrWebSocket?.connect()
        }

        print("[SimpleVoiceService] ASR 连接成功")
        asrContinuation = nil
    }

    private func startAudioEngine() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(
            .playAndRecord,
            mode: .measurement,
            options: [.defaultToSpeaker, .allowBluetoothHFP]
        )
        try audioSession.setPreferredSampleRate(48000)
        try audioSession.setPreferredInputNumberOfChannels(1)
        try audioSession.setActive(true)

        audioEngine = AVAudioEngine()
        inputNode = audioEngine?.inputNode

        guard let inputNode = inputNode else {
            throw VoiceError.microphoneUnavailable
        }

        // 打印输入格式信息
        let inputFormat = inputNode.outputFormat(forBus: 0)
        print("[SimpleVoiceService] 输入格式: \(inputFormat.sampleRate)Hz, \(inputFormat.channelCount)ch")

        // 安装 tap
        inputNode.installTap(
            onBus: 0,
            bufferSize: asrBufferSize,
            format: inputFormat
        ) { [weak self] buffer, _ in
            guard let self else { return }

            // 调试：确认 tap 被触发
            self.audioTapCount += 1
            if self.audioTapCount <= 5 {
                print("[SimpleVoiceService] Tap 被触发 #\(self.audioTapCount), buffer 大小: \(buffer.frameLength)")
            }

            self.processAndSendAudio(buffer)
        }

        isTapInstalled = true

        try audioEngine?.start()
        print("[SimpleVoiceService] 音频引擎已启动，running: \(audioEngine?.isRunning ?? false)")
    }

    private func processAndSendAudio(_ buffer: AVAudioPCMBuffer) {
        guard let pcmData = convertToPCM16(buffer) else { return }

        // 检查 WebSocket 连接状态
        guard isASRConnected else { return }

        // 使用 Starscream 的 write 方法发送二进制数据
        asrWebSocket?.write(data: pcmData)

        // 调试：定期打印发送状态（每100次打印一次）
        audioSendCount += 1
        if audioSendCount % 100 == 0 {
            print("[SimpleVoiceService] 已发送 \(audioSendCount) 个音频块，大小: \(pcmData.count) bytes")
        }
    }

    private func convertToPCM16(_ buffer: AVAudioPCMBuffer) -> Data? {
        let inputFormat = buffer.format

        // 如果已经是 16kHz 单声道，直接转换
        if inputFormat.sampleRate == 16000 && inputFormat.channelCount == 1 {
            return convertFloat32ToInt16(buffer)
        }

        // 多声道 → 单声道
        let monoBuffer = inputFormat.channelCount > 1 ? downmixToMono(buffer) : buffer

        // 重采样到 16kHz
        let resampled: AVAudioPCMBuffer
        if monoBuffer.format.sampleRate != 16000 {
            guard let res = resampleTo16kHz(monoBuffer) else {
                return convertFloat32ToInt16(monoBuffer)
            }
            resampled = res
        } else {
            resampled = monoBuffer
        }

        return convertFloat32ToInt16(resampled)
    }

    private func downmixToMono(_ buffer: AVAudioPCMBuffer) -> AVAudioPCMBuffer {
        guard let channelData = buffer.floatChannelData else { return buffer }

        let frameCount = Int(buffer.frameLength)
        let channelCount = Int(buffer.format.channelCount)

        guard let monoBuffer = AVAudioPCMBuffer(
            pcmFormat: AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: buffer.format.sampleRate, channels: 1, interleaved: false)!,
            frameCapacity: AVAudioFrameCount(frameCount)
        ) else {
            return buffer
        }

        monoBuffer.frameLength = buffer.frameLength
        guard let monoData = monoBuffer.floatChannelData else { return buffer }

        for i in 0..<frameCount {
            var sum: Float = 0
            for ch in 0..<channelCount {
                sum += channelData[ch][i]
            }
            monoData[0][i] = sum / Float(channelCount)
        }

        return monoBuffer
    }

    private func resampleTo16kHz(_ buffer: AVAudioPCMBuffer) -> AVAudioPCMBuffer? {
        let targetFormat = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16000, channels: 1, interleaved: false)!
        guard let converter = AVAudioConverter(from: buffer.format, to: targetFormat) else {
            return nil
        }

        let ratio = 16000.0 / buffer.format.sampleRate
        let outputFrameCount = AVAudioFrameCount(ceil(Double(buffer.frameLength) * ratio))

        guard let outputBuffer = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: outputFrameCount) else {
            return nil
        }

        var error: NSError?
        let status = converter.convert(to: outputBuffer, error: &error) { _, inputStatus in
            inputStatus.pointee = .haveData
            return buffer
        }

        return status == .error ? nil : outputBuffer
    }

    private func convertFloat32ToInt16(_ buffer: AVAudioPCMBuffer) -> Data? {
        guard let channelData = buffer.floatChannelData else { return nil }

        let frameCount = Int(buffer.frameLength)
        var pcmData = Data(capacity: frameCount * 2)

        for i in 0..<frameCount {
            let sample = channelData.pointee[i]
            let clamped = max(-1.0, min(1.0, sample))
            var pcm = Int16(clamped * Float(Int16.max))
            withUnsafeBytes(of: &pcm) { ptr in
                pcmData.append(ptr.bindMemory(to: UInt8.self))
            }
        }

        return pcmData
    }

    // MARK: - Private Methods - TTS

    private func startTTS() async throws {
        var components = URLComponents(string: baseURL)!
        components.path = "/ws/voice/tts"
        components.queryItems = [URLQueryItem(name: "token", value: token)]

        guard let url = components.url else {
            throw VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -1))
        }

        print("[SimpleVoiceService] TTS 连接: \(url.absoluteString)")

        // 使用 continuation 等待连接成功（无超时限制）
        try await withCheckedThrowingContinuation { continuation in
            ttsContinuation = continuation
            let request = URLRequest(url: url)
            ttsWebSocket = WebSocket(request: request)
            ttsWebSocket?.delegate = self
            ttsWebSocket?.connect()
        }

        // 初始化播放器
        ttsAudioEngine = AVAudioEngine()
        ttsAudioEngine?.attach(audioPlayerNode)
        ttsAudioEngine?.connect(audioPlayerNode, to: ttsAudioEngine!.mainMixerNode, format: ttsFormat)

        try ttsAudioEngine?.start()
        audioPlayerNode.play()

        print("[SimpleVoiceService] TTS 连接成功，播放器已启动")
        ttsContinuation = nil
    }

    private func playTTSAudio(_ data: Data) {
        // 只检查播放器是否存在
        guard ttsAudioEngine != nil else { return }

        // 创建音频缓冲区
        let frameCount = data.count / 2  // 16-bit = 2 bytes per sample
        guard let buffer = AVAudioPCMBuffer(pcmFormat: ttsFormat, frameCapacity: AVAudioFrameCount(frameCount)) else {
            return
        }

        buffer.frameLength = AVAudioFrameCount(frameCount)

        guard let channelData = buffer.int16ChannelData else { return }

        // 复制数据
        data.withUnsafeBytes { rawPtr in
            guard let baseAddr = rawPtr.baseAddress?.assumingMemoryBound(to: Int16.self) else {
                return
            }
            for i in 0..<Int(frameCount) {
                channelData[0][i] = baseAddr[i]
            }
        }

        // 增加待播放计数
        pendingTTSBuffers += 1

        // 捕获需要在主线程执行的回调
        let onBufferCompleted: @Sendable () -> Void = { [weak self] in
            guard let self = self else { return }

            Task { @MainActor in
                self.pendingTTSBuffers -= 1

                // 最后一个 buffer 播放完成
                if self.pendingTTSBuffers == 0 && self.isTTSSpeaking {
                    print("[SimpleVoiceService] 所有 TTS 音频播放完成")

                    self.isTTSSpeaking = false
                    self.state = .listening
                    self.onTTSEnded?()

                    // TTS 播放完成，重新连接 ASR 开始下一轮识别
                    try? await self.startRecording()
                }
            }
        }

        // 调度播放，带完成回调
        audioPlayerNode.scheduleBuffer(buffer, completionCallbackType: .dataPlayedBack) { _ in
            onBufferCompleted()
        }
    }
}

// MARK: - WebSocket Delegate (ASR)
extension SimpleVoiceService: WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        Task { @MainActor in
            switch event {
            case .connected:
                if client === asrWebSocket {
                    print("[SimpleVoiceService] ASR WebSocket 已连接")
                    isASRConnected = true
                    state = .listening
                    // 立即恢复 continuation，不再等待
                    asrContinuation?.resume()
                } else if client === ttsWebSocket {
                    print("[SimpleVoiceService] TTS WebSocket 已连接")
                    isTTSConnected = true
                    // 立即恢复 continuation，不再等待
                    ttsContinuation?.resume()
                }

            case .disconnected(let reason, let code):
                if client === asrWebSocket {
                    print("[SimpleVoiceService] ASR 断开: \(reason), code: \(code)")
                    isASRConnected = false
                    // 如果还在等待连接，抛出错误
                    asrContinuation?.resume(throwing: VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -3, userInfo: [NSLocalizedDescriptionKey: "ASR 连接断开: \(reason)"])))
                    // 已断开，等待下次 startRecording() 时重新连接
                } else if client === ttsWebSocket {
                    print("[SimpleVoiceService] TTS 断开: \(reason), code: \(code)")
                    isTTSConnected = false
                    // 如果还在等待连接，抛出错误
                    ttsContinuation?.resume(throwing: VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -3, userInfo: [NSLocalizedDescriptionKey: "TTS 连接断开: \(reason)"])))
                }

            case .text(let text):
                handleTextMessage(text, from: client)

            case .binary(let data):
                if client === ttsWebSocket {
                    // TTS 音频数据
                    playTTSAudio(data)
                }

            case .error(let error):
                let errorMsg = error?.localizedDescription ?? "未知"
                print("[SimpleVoiceService] WebSocket 错误: \(errorMsg)")
                // 如果还在等待连接，抛出错误
                if client === asrWebSocket {
                    asrContinuation?.resume(throwing: VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -4, userInfo: [NSLocalizedDescriptionKey: "ASR 错误: \(errorMsg)"])))
                } else if client === ttsWebSocket {
                    ttsContinuation?.resume(throwing: VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -4, userInfo: [NSLocalizedDescriptionKey: "TTS 错误: \(errorMsg)"])))
                }

            default:
                break
            }
        }
    }

    private func handleTextMessage(_ text: String, from client: WebSocketClient) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let event = json["event"] as? String else {
            return
        }

        if client === asrWebSocket {
            // ASR 事件
            switch event {
            case "asr_ready":
                print("[SimpleVoiceService] ASR 就绪")

            case "asr_partial":
                if let text = json["text"] as? String, !text.isEmpty {
                    recognizedText = text
                    onPartialResult?(text)
                }

            case "asr_final":
                if let text = json["text"] as? String, !text.isEmpty {
                    recognizedText = text
                    onFinalResult?(text)
                    print("[SimpleVoiceService] ASR 最终: \(text)")
                }

            case "error":
                if let message = json["message"] as? String {
                    print("[SimpleVoiceService] ASR 错误: \(message)")
                }

            default:
                break
            }

        } else if client === ttsWebSocket {
            // TTS 事件
            switch event {
            case "tts_ready":
                print("[SimpleVoiceService] TTS 就绪")

            case "tts_finished":
                print("[SimpleVoiceService] TTS 音频传输完成 (待播放 buffer: \(pendingTTSBuffers))")
                // 注意：此时音频可能还在播放，不等 pendingTTSBuffers 归零
                // 真正的播放完成由 AVAudioPlayerNode 完成回调处理

            case "error":
                if let message = json["message"] as? String {
                    print("[SimpleVoiceService] TTS 错误: \(message)")
                }
                isTTSSpeaking = false
                state = .listening

            default:
                break
            }
        }
    }
}
