import Foundation
import AVFoundation
import Combine
import Starscream

// MARK: - Backend ASR Service Configuration
/// 后端 ASR 服务配置
struct BackendASRServiceConfig {
    /// 后端 WebSocket 地址（仅基础地址，路径由 start() 方法添加）
    var baseURL: String
    /// 阿里云 API Key
    var apiKey: String
    /// 采样率
    var sampleRate: Int
    /// 音频格式
    var format: String

    /// 从 BackendASRConfig 创建默认配置
    /// 注意：使用 BackendASRConfig.baseURL（基础地址），而不是 webSocketURL（完整 URL）
    /// 因为 start() 方法会自己添加路径和参数
    static let `default` = BackendASRServiceConfig(
        baseURL: BackendASRConfig.baseURL,  // http://127.0.0.1:8100
        apiKey: BackendASRConfig.apiKey,
        sampleRate: BackendASRConfig.sampleRate,
        format: BackendASRConfig.format
    )
}

// MARK: - Backend ASR Service
/// 后端 FunASR 语音识别服务
/// 通过 WebSocket 连接后端，由后端调用阿里云 FunASR API
/// 此服务也负责向 AudioEnergyVADService 提供音频数据
@MainActor
class BackendASRService: NSObject, ObservableObject {

    // MARK: - Published State
    @Published var isConnecting = false
    @Published var isConnected = false
    @Published var recognizedText = ""
    @Published var errorMessage: String?

    // MARK: - Callbacks
    var onPartialResult: ((String) -> Void)?
    var onFinalResult: ((String) -> Void)?
    var onError: ((Error) -> Void)?
    var onConnectionChanged: ((Bool) -> Void)?

    // MARK: - VAD Integration
    /// 关联的 VAD 服务，用于接收音频数据进行语音活动检测
    var vadService: AudioEnergyVADService?

    // MARK: - Private Properties
    private let config: BackendASRServiceConfig
    private var webSocket: Starscream.WebSocket?
    private var audioEngine: AVAudioEngine?
    private var inputNode: AVAudioInputNode?

    // 目标格式 (16kHz, 单声道, Int16)
    private var targetFormat: AVAudioFormat {
        AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: Double(config.sampleRate),
            channels: 1,
            interleaved: false
        )!
    }

    // 音频转换器
    private var converter: AVAudioConverter?

    // 缓冲区设置
    private let bufferSize: AVAudioFrameCount = 1024  // 使用较小的缓冲区

    // MARK: - Init
    init(config: BackendASRServiceConfig = .default) {
        self.config = config
        super.init()
    }

    deinit {
        // deinit 不能直接调用 @MainActor 方法
        Task { @MainActor in
            self.stop()
        }
    }

    // MARK: - Public Methods

    /// 启动识别
    func start() async throws {
        guard !isConnected else { return }

        print("[BackendASR] 启动语音识别")

        isConnecting = true

        // 构建 WebSocket URL
        var components = URLComponents(string: config.baseURL)!
        components.path = "/funasr/ws"
        components.queryItems = [
            URLQueryItem(name: "api_key", value: config.apiKey),
            URLQueryItem(name: "sample_rate", value: String(config.sampleRate)),
            URLQueryItem(name: "format", value: config.format)
        ]

        guard let url = components.url else {
            throw NSError(domain: "BackendASR", code: -1, userInfo: [
                NSLocalizedDescriptionKey: "无效的 URL"
            ])
        }

        print("[BackendASR] 连接: \(url.absoluteString)")

        // 创建 WebSocket
        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // 等待连接（简单超时处理）
        try await Task.sleep(nanoseconds: 3_000_000_000)  // 3秒超时

        if !isConnected && isConnecting {
            // 如果还在连接中，再等一会
            try await Task.sleep(nanoseconds: 2_000_000_000)
        }

        if !isConnected {
            throw NSError(domain: "BackendASR", code: -2, userInfo: [
                NSLocalizedDescriptionKey: "连接超时"
            ])
        }

        print("[BackendASR] 连接成功")
    }

    /// 停止识别
    func stop() {
        print("[BackendASR] 停止识别")

        isConnecting = false
        isConnected = false

        // 停止音频采集
        inputNode?.removeTap(onBus: 0)
        audioEngine?.stop()

        // 关闭 WebSocket
        webSocket?.disconnect()
        webSocket = nil

        recognizedText = ""
    }

    /// 暂停识别
    func pause() {
        audioEngine?.pause()
    }

    /// 恢复识别
    func resume() {
        guard let engine = audioEngine else { return }
        if !engine.isRunning {
            try? engine.start()
        }
    }

    // MARK: - Private Methods

    private func startAudioEngine() throws {
        // 配置音频会话
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(
            .playAndRecord,
            mode: .measurement,
            options: [.defaultToSpeaker, .allowBluetooth]
        )

        // 设置首选采样率和声道数
        try audioSession.setPreferredSampleRate(48000)
        try audioSession.setPreferredInputNumberOfChannels(1)
        try audioSession.setActive(true)

        // 关键修复：在启动引擎后再获取格式
        // 1. 先用 nil format 安装 tap（引擎会使用实际硬件格式）
        // 2. 启动引擎
        // 3. 在回调中处理实际收到的格式

        audioEngine = AVAudioEngine()
        inputNode = audioEngine?.inputNode

        guard let inputNode = inputNode else {
            throw VoiceError.microphoneUnavailable
        }

        let sessionSampleRate = audioSession.sampleRate
        print("[BackendASR] 音频会话采样率: \(sessionSampleRate) Hz")

        // 安装 tap，使用 nil format 让系统自动匹配
        inputNode.installTap(
            onBus: 0,
            bufferSize: bufferSize,
            format: nil  // 让系统使用硬件实际格式
        ) { [weak self] buffer, _ in
            guard let self = self else { return }

            // 首次收到音频时记录实际格式
            if self.audioFormat == nil {
                print("[BackendASR] 实际收到音频格式: \(buffer.format)")
                self.audioFormat = buffer.format
            }

            // 转换并发送音频数据
            self.processAndSendAudio(buffer)
        }

        // 启动引擎
        try audioEngine?.start()

        print("[BackendASR] 音频引擎已启动")
    }

    // 用于存储首次收到的实际音频格式
    private var audioFormat: AVAudioFormat?

    private func processAndSendAudio(_ buffer: AVAudioPCMBuffer) {
        guard let pcmData = convertToPCM(buffer) else { return }

        // 发送到 WebSocket
        sendAudioData(pcmData)
    }

    private func convertToPCM(_ buffer: AVAudioPCMBuffer) -> Data? {
        let inputFormat = buffer.format

        // 如果输入已经是单声道 16kHz Float32，直接转换
        if inputFormat.sampleRate == 16000 && inputFormat.channelCount == 1 {
            return convertFloat32ToInt16Data(buffer)
        }

        // 目标格式: 单声道 16kHz Float32
        let intermediateFormat = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: 16000,
            channels: 1,
            interleaved: false
        )!

        // 首先处理多声道情况（如果输入是立体声，先降混为单声道）
        let monoBuffer: AVAudioPCMBuffer
        if inputFormat.channelCount > 1 {
            monoBuffer = downmixToMono(buffer)
        } else {
            monoBuffer = buffer
        }

        // 然后重采样到 16kHz
        let resampledBuffer: AVAudioPCMBuffer
        if monoBuffer.format.sampleRate != 16000 {
            guard let resampled = resampleTo16kHz(monoBuffer) else {
                return convertFloat32ToInt16Data(monoBuffer)
            }
            resampledBuffer = resampled
        } else {
            resampledBuffer = monoBuffer
        }

        // 最后转换为 Int16 PCM
        return convertFloat32ToInt16Data(resampledBuffer)
    }

    /// 将多声道音频降混为单声道
    private func downmixToMono(_ buffer: AVAudioPCMBuffer) -> AVAudioPCMBuffer {
        let inputFormat = buffer.format
        guard let channelData = buffer.floatChannelData else { return buffer }

        let frameCount = Int(buffer.frameLength)
        let channelCount = Int(inputFormat.channelCount)

        // 创建单声道缓冲区
        guard let monoBuffer = AVAudioPCMBuffer(
            pcmFormat: AVAudioFormat(
                commonFormat: .pcmFormatFloat32,
                sampleRate: inputFormat.sampleRate,
                channels: 1,
                interleaved: false
            )!,
            frameCapacity: AVAudioFrameCount(frameCount)
        ) else {
            return buffer
        }

        monoBuffer.frameLength = buffer.frameLength
        guard let monoData = monoBuffer.floatChannelData else { return buffer }

        // 降混：取所有声道的平均值
        for i in 0..<frameCount {
            var sum: Float = 0
            for ch in 0..<channelCount {
                sum += channelData[ch][i]
            }
            monoData[0][i] = sum / Float(channelCount)
        }

        return monoBuffer
    }

    /// 重采样到 16kHz
    private func resampleTo16kHz(_ buffer: AVAudioPCMBuffer) -> AVAudioPCMBuffer? {
        let targetFormat = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: 16000,
            channels: 1,
            interleaved: false
        )!

        guard let converter = AVAudioConverter(from: buffer.format, to: targetFormat) else {
            return nil
        }

        let ratio = 16000.0 / buffer.format.sampleRate
        let outputFrameCount = AVAudioFrameCount(ceil(Double(buffer.frameLength) * ratio))

        guard let outputBuffer = AVAudioPCMBuffer(
            pcmFormat: targetFormat,
            frameCapacity: outputFrameCount
        ) else {
            return nil
        }

        var error: NSError?
        let status = converter.convert(
            to: outputBuffer,
            error: &error
        ) { _, inputStatus in
            inputStatus.pointee = .haveData
            return buffer
        }

        if status == .error {
            print("[BackendASR] 重采样失败: \(error?.localizedDescription ?? "未知错误")")
            return nil
        }

        return outputBuffer
    }

    private func convertFloat32ToInt16Data(_ buffer: AVAudioPCMBuffer) -> Data? {
        guard let channelData = buffer.floatChannelData else { return nil }

        let frameCount = Int(buffer.frameLength)
        var pcmData = Data(capacity: frameCount * 2)  // 16-bit PCM

        for i in 0..<frameCount {
            let sample = channelData.pointee[i]
            let clamped = max(-1.0, min(1.0, sample))
            var pcm = Int16(clamped * Float(Int16.max))
            withUnsafeBytes(of: &pcm) { ptr in
                pcmData.append(ptr.bindMemory(to: UInt8.self))
            }
        }

        // 同时也向 VAD 服务传递音频数据
        vadService?.processExternalPCMData(pcmData, frameCount: frameCount)

        return pcmData
    }

    private func convertInt16BufferToData(_ buffer: AVAudioPCMBuffer) -> Data? {
        guard let channelData = buffer.int16ChannelData else { return nil }

        let frameCount = Int(buffer.frameLength)
        var pcmData = Data(capacity: frameCount * 2)

        for i in 0..<frameCount {
            var sample = channelData.pointee[i]
            withUnsafeBytes(of: &sample) { ptr in
                pcmData.append(ptr.bindMemory(to: UInt8.self))
            }
        }

        // 同时也向 VAD 服务传递音频数据
        vadService?.processExternalPCMData(pcmData, frameCount: frameCount)

        return pcmData
    }

    private func sendAudioData(_ data: Data) {
        guard isConnected else { return }

        // 发送二进制音频数据
        webSocket?.write(data: data)
    }

    private func handleTextResult(_ text: String, isFinal: Bool) {
        recognizedText = text

        if isFinal {
            onFinalResult?(text)
        } else {
            onPartialResult?(text)
        }
    }
}

// MARK: - WebSocket Delegate
extension BackendASRService: Starscream.WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: Starscream.WebSocketClient) {
        switch event {
        case .connected:
            print("[BackendASR] WebSocket 已连接")
            isConnected = true
            isConnecting = false
            onConnectionChanged?(true)

            // 连接成功后启动音频引擎
            try? startAudioEngine()

        case .disconnected(let reason, let code):
            print("[BackendASR] WebSocket 断开: \(reason) (code: \(code))")
            isConnected = false
            isConnecting = false
            onConnectionChanged?(false)

        case .text(let text):
            handleTextMessage(text)

        case .binary(let data):
            // FunASR 使用文本协议，不处理二进制
            break

        case .ping(_):
            break

        case .pong(_):
            break

        case .viabilityChanged(_):
            break

        case .reconnectSuggested(_):
            break

        case .cancelled:
            break

        case .peerClosed:
            isConnected = false
            isConnecting = false
            onConnectionChanged?(false)
            break

        case .error(let error):
            print("[BackendASR] WebSocket 错误: \(error?.localizedDescription ?? "未知错误")")
            isConnected = false
            if let err = error {
                onError?(err)
            }
        }
    }

    private func handleTextMessage(_ text: String) {
        guard !text.isEmpty else { return }

        // 解析 JSON 消息
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }

        guard let event = json["event"] as? String else { return }

        switch event {
        case "task_started":
            print("[BackendASR] 任务已启动")

        case "result":
            if let text = json["text"] as? String {
                handleTextResult(text, isFinal: false)
            }

        case "sentence_end":
            if let text = json["text"] as? String {
                handleTextResult(text, isFinal: true)
                print("[BackendASR] 最终结果: \(text)")
            }

        case "error":
            if let error = json["error"] as? String {
                errorMessage = error
                print("[BackendASR] 错误: \(error)")
            }

        default:
            print("[BackendASR] 未知事件: \(event)")
        }
    }
}
