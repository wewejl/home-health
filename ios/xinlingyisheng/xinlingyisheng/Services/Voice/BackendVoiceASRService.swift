import Foundation
import Combine
import Starscream

@preconcurrency import AVFoundation

// MARK: - Backend Voice ASR Configuration
/// 后端 ASR 服务配置
struct BackendVoiceASRConfig {
    /// 后端 WebSocket 基础地址
    let baseURL: String
    /// 用户认证 token
    let token: String
    /// 采样率
    let sampleRate: Int
    /// 音频格式
    let format: String

    static let `default` = BackendVoiceASRConfig(
        baseURL: BackendVoiceConfig.baseURL,
        token: BackendVoiceConfig.defaultToken,
        sampleRate: 16000,
        format: "pcm"
    )
}

// MARK: - Backend Voice ASR Service
/// 后端 ASR 语音识别服务
/// 连接后端 /ws/voice/asr 端点，不暴露 API Key
@MainActor
class BackendVoiceASRService: NSObject, ObservableObject {

    // MARK: - Published State
    @Published var isConnecting = false
    @Published var isConnected = false
    @Published var isRecognizing = false
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
    private let config: BackendVoiceASRConfig
    private var webSocket: Starscream.WebSocket?

    // 音频引擎
    private var audioEngine: AVAudioEngine?
    private var inputNode: AVAudioInputNode?

    // 缓冲区设置
    private let bufferSize: AVAudioFrameCount = 1024

    // MARK: - Reconnection (自动重连)
    /// 是否应该自动重连（用户未主动停止）
    private var shouldAutoReconnect = false

    // MARK: - Pause State
    /// 是否处于暂停状态（不发送数据到后端，但继续采集给 VAD）
    private var isPaused = false

    // MARK: - Init
    init(config: BackendVoiceASRConfig = .default) {
        self.config = config
        super.init()
    }

    deinit {
        // 同步清理 WebSocket 连接
        webSocket?.disconnect()
        webSocket = nil
    }

    // MARK: - Public Methods

    /// 启动识别
    func start() async throws {
        guard !isConnected else { return }

        print("[BackendVoiceASR] 启动语音识别")

        // 启用自动重连
        shouldAutoReconnect = true
        isConnecting = true

        // 构建 WebSocket URL
        var components = URLComponents(string: config.baseURL)!
        components.path = "/ws/voice/asr"
        components.queryItems = [
            URLQueryItem(name: "token", value: config.token)
        ]

        guard let url = components.url else {
            throw BackendVoiceASRError.recognitionFailed(underlying: NSError(
                domain: "BackendVoiceASR",
                code: -1,
                userInfo: [NSLocalizedDescriptionKey: "无效的 URL"]
            ))
        }

        print("[BackendVoiceASR] 连接: \(url.absoluteString)")

        // 创建 WebSocket
        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 5_000_000_000)

        if !isConnected && isConnecting {
            try await Task.sleep(nanoseconds: 2_000_000_000)
        }

        if !isConnected {
            throw BackendVoiceASRError.recognitionFailed(underlying: NSError(
                domain: "BackendVoiceASR",
                code: -2,
                userInfo: [NSLocalizedDescriptionKey: "连接超时"]
            ))
        }

        print("[BackendVoiceASR] 连接成功")
    }

    /// 停止识别
    func stop() {
        print("[BackendVoiceASR] 停止识别")

        // 禁用自动重连
        shouldAutoReconnect = false

        isConnecting = false
        isConnected = false
        isRecognizing = false

        // 停止音频采集
        inputNode?.removeTap(onBus: 0)
        audioEngine?.stop()

        // 关闭 WebSocket
        webSocket?.disconnect()
        webSocket = nil

        recognizedText = ""
    }

    /// 暂停识别
    /// 注意：此方法用于 TTS 播报期间，不发送数据到后端但继续采集给 VAD
    func pause() {
        print("[BackendVoiceASR] 暂停识别（TTS 播报期间）- 继续采集给 VAD")

        // 设置暂停标志（不发送数据到后端）
        isPaused = true

        // 注意：不停止音频引擎，继续采集以支持 VAD 打断检测
    }

    /// 恢复识别
    func resume() async {
        print("[BackendVoiceASR] 恢复识别")

        // 清除暂停标志
        isPaused = false

        // 检查连接状态，如果断开则自动重连
        if !isConnected && shouldAutoReconnect {
            print("[BackendVoiceASR] 连接已断开，尝试重连...")
            do {
                try await reconnect()
            } catch {
                print("[BackendVoiceASR] 重连失败: \(error)")
                // 重连失败，仍然尝试恢复音频引擎
            }
        }

        guard let engine = audioEngine else { return }

        if !engine.isRunning {
            // 引擎未运行，重新启动
            do {
                try startAudioEngine()
            } catch {
                print("[BackendVoiceASR] 恢复音频引擎失败: \(error)")
            }
        }
        // 注意：音频引擎一直在运行（为了 VAD），不需要重新启动
    }

    /// 安装音频 tap
    private func installAudioTap(on inputNode: AVAudioInputNode) {
        inputNode.installTap(
            onBus: 0,
            bufferSize: bufferSize,
            format: nil  // 让系统使用硬件实际格式
        ) { [weak self] buffer, _ in
            guard let self = self else { return }

            // 转换并发送音频数据
            self.processAndSendAudio(buffer)
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

        audioEngine = AVAudioEngine()
        inputNode = audioEngine?.inputNode

        guard let inputNode = inputNode else {
            throw BackendVoiceASRError.microphoneUnavailable
        }

        let sessionSampleRate = audioSession.sampleRate
        print("[BackendVoiceASR] 音频会话采样率: \(sessionSampleRate) Hz")

        // 安装 tap，使用 nil format 让系统自动匹配
        installAudioTap(on: inputNode)

        // 启动引擎
        try audioEngine?.start()

        print("[BackendVoiceASR] 音频引擎已启动")
    }

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
            print("[BackendVoiceASR] 重采样失败: \(error?.localizedDescription ?? "未知错误")")
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

    private func sendAudioData(_ data: Data) {
        guard isConnected else { return }

        // 暂停状态下不发送数据到后端（但 VAD 继续处理）
        guard !isPaused else { return }

        // 发送二进制音频数据
        webSocket?.write(data: data)
    }

    // MARK: - Reconnection Methods

    /// 重连 WebSocket
    private func reconnect() async throws {
        print("[BackendVoiceASR] 开始重连...")

        // 清理旧连接
        webSocket?.disconnect()
        webSocket = nil
        isConnected = false

        // 构建 WebSocket URL
        var components = URLComponents(string: config.baseURL)!
        components.path = "/ws/voice/asr"
        components.queryItems = [
            URLQueryItem(name: "token", value: config.token)
        ]

        guard let url = components.url else {
            throw BackendVoiceASRError.recognitionFailed(underlying: NSError(
                domain: "BackendVoiceASR",
                code: -1,
                userInfo: [NSLocalizedDescriptionKey: "无效的 URL"]
            ))
        }

        // 创建 WebSocket
        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // 等待连接
        try await Task.sleep(nanoseconds: 5_000_000_000)

        if !isConnected {
            throw BackendVoiceASRError.recognitionFailed(underlying: NSError(
                domain: "BackendVoiceASR",
                code: -3,
                userInfo: [NSLocalizedDescriptionKey: "重连超时"]
            ))
        }

        print("[BackendVoiceASR] 重连成功")
    }
}

// MARK: - WebSocket Delegate
extension BackendVoiceASRService: WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        // 确保所有 UI 相关操作在主线程执行
        Task { @MainActor in
            switch event {
            case .connected:
                print("[BackendVoiceASR] WebSocket 已连接")
                isConnected = true
                isConnecting = false
                onConnectionChanged?(true)

                // 连接成功后启动音频引擎
                try? startAudioEngine()

            case .disconnected(let reason, let code):
                print("[BackendVoiceASR] WebSocket 断开: \(reason) (code: \(code))")
                isConnected = false
                isConnecting = false
                onConnectionChanged?(false)

            case .text(let text):
                handleTextMessage(text)

            case .binary(_):
                // ASR 不处理二进制（只有我们发送音频）
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

            case .error(let error):
                print("[BackendVoiceASR] WebSocket 错误: \(error?.localizedDescription ?? "未知错误")")
                isConnected = false
                if let err = error {
                    onError?(err)
                }
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
        case "asr_ready":
            print("[BackendVoiceASR] 识别服务已就绪")
            isRecognizing = true

        case "asr_partial":
            if let text = json["text"] as? String {
                recognizedText = text
                onPartialResult?(text)
            }

        case "asr_final":
            if let text = json["text"] as? String {
                recognizedText = text
                onFinalResult?(text)
                print("[BackendVoiceASR] 最终结果: \(text)")
            }

        case "error":
            if let error = json["message"] as? String {
                errorMessage = error
                print("[BackendVoiceASR] 错误: \(error)")
            }

        default:
            print("[BackendVoiceASR] 未知事件: \(event)")
        }
    }
}

// MARK: - Backend Voice Error
enum BackendVoiceASRError: LocalizedError {
    case microphoneUnavailable
    case recognitionFailed(underlying: Error)

    var errorDescription: String? {
        switch self {
        case .microphoneUnavailable:
            return "麦克风不可用"
        case .recognitionFailed(let error):
            return "语音识别失败: \(error.localizedDescription)"
        }
    }
}
