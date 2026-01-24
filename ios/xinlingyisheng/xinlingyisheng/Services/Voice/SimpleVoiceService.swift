import Foundation
import AVFoundation
import Combine
import Starscream

// MARK: - Simple Voice Service
/// 简化版语音服务 - 核心逻辑：ASR 持续监听 + TTS 流式播放 + 有结果就停
@MainActor
class SimpleVoiceService: NSObject, ObservableObject {

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

    // MARK: - State Flags
    private(set) var isASRConnected = false
    private(set) var isTTSConnected = false
    private var isTTSSpeaking = false

    // MARK: - Init
    init(baseURL: String? = nil, token: String? = nil) {
        self.baseURL = baseURL ?? BackendVoiceConfig.baseURL
        self.token = token ?? BackendVoiceConfig.defaultToken

        // TTS 音频格式: 24kHz, 单声道, 16-bit PCM
        self.ttsFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: 24000,
            channels: 1,
            interleaved: false
        )!

        super.init()
        print("[SimpleVoiceService] 初始化完成")
    }

    deinit {
        Task { @MainActor in
            stop()
        }
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

    /// 停止 TTS 播放（核心逻辑：收到 ASR 结果就调用此方法）
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

    private func startASR() async throws {
        var components = URLComponents(string: baseURL)!
        components.path = "/ws/voice/asr"
        components.queryItems = [URLQueryItem(name: "token", value: token)]

        guard let url = components.url else {
            throw VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -1))
        }

        print("[SimpleVoiceService] ASR 连接: \(url.absoluteString)")

        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        asrWebSocket = WebSocket(request: request)
        asrWebSocket?.delegate = self
        asrWebSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 5_000_000_000)

        guard isASRConnected else {
            throw VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -2))
        }

        print("[SimpleVoiceService] ASR 连接成功")
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

        // 安装 tap
        inputNode.installTap(
            onBus: 0,
            bufferSize: asrBufferSize,
            format: nil
        ) { [weak self] buffer, _ in
            self?.processAndSendAudio(buffer)
        }

        try audioEngine?.start()
        print("[SimpleVoiceService] 音频引擎已启动")
    }

    private func processAndSendAudio(_ buffer: AVAudioPCMBuffer) {
        guard let pcmData = convertToPCM16(buffer) else { return }
        asrWebSocket?.write(data: pcmData)
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

        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        ttsWebSocket = WebSocket(request: request)
        ttsWebSocket?.delegate = self
        ttsWebSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 5_000_000_000)

        guard isTTSConnected else {
            throw VoiceError.recognitionFailed(underlying: NSError(domain: "SimpleVoice", code: -2))
        }

        // 初始化播放器
        ttsAudioEngine = AVAudioEngine()
        ttsAudioEngine?.attach(audioPlayerNode)
        ttsAudioEngine?.connect(audioPlayerNode, to: ttsAudioEngine!.mainMixerNode, format: ttsFormat)

        try ttsAudioEngine?.start()
        audioPlayerNode.play()

        print("[SimpleVoiceService] TTS 连接成功，播放器已启动")
    }

    private func playTTSAudio(_ data: Data) {
        guard isTTSSpeaking, ttsAudioEngine != nil else { return }

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

        // 调度播放
        audioPlayerNode.scheduleBuffer(buffer)
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
                } else if client === ttsWebSocket {
                    print("[SimpleVoiceService] TTS WebSocket 已连接")
                    isTTSConnected = true
                }

            case .disconnected(let reason, let code):
                if client === asrWebSocket {
                    print("[SimpleVoiceService] ASR 断开: \(reason)")
                    isASRConnected = false
                } else if client === ttsWebSocket {
                    print("[SimpleVoiceService] TTS 断开: \(reason)")
                    isTTSConnected = false
                }

            case .text(let text):
                handleTextMessage(text, from: client)

            case .binary(let data):
                if client === ttsWebSocket {
                    // TTS 音频数据
                    playTTSAudio(data)
                }

            case .error(let error):
                print("[SimpleVoiceService] WebSocket 错误: \(error?.localizedDescription ?? "未知")")

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

                    // 核心逻辑：收到任何 ASR 结果就停止 TTS
                    if isTTSSpeaking {
                        print("[SimpleVoiceService] 检测到语音，停止 TTS")
                        stopTTS()
                        onTTSEnded?()
                    }
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
                print("[SimpleVoiceService] TTS 完成")
                isTTSSpeaking = false
                state = .listening
                onTTSEnded?()

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
