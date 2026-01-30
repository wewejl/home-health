//
//  PressAndHoldVoiceService.swift
//  灵犀医生
//
//  按住说话风格的语音服务，类似微信交互
//  - 按住开始录音识别
//  - 松开发送识别文字
//  - 上滑取消
//  - 按住时自动停止 TTS 播放
//  - 支持静音模式
//

import Foundation
import AVFoundation
import Combine
import Starscream

// MARK: - 按住说话状态
/// 按住说话状态枚举
enum PressAndHoldVoiceState: Equatable {
    /// 空闲，等待操作
    case idle
    /// 正在录音识别
    case listening
    /// 正在发送/等待 AI 回复
    case processing
    /// AI 正在播报
    case speaking
    /// 错误状态
    case error(String)

    var displayText: String {
        switch self {
        case .idle: return "按住说话"
        case .listening: return "松开发送"
        case .processing: return "正在处理..."
        case .speaking: return "正在回复..."
        case .error(let msg): return msg
        }
    }

    static func == (lhs: PressAndHoldVoiceState, rhs: PressAndHoldVoiceState) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle), (.listening, .listening), (.processing, .processing), (.speaking, .speaking):
            return true
        case (.error(let e1), .error(let e2)):
            return e1 == e2
        default:
            return false
        }
    }
}

// MARK: - 按住说话语音服务
/// 按住说话风格的语音服务，类似微信
@MainActor
class PressAndHoldVoiceService: NSObject, ObservableObject {

    // MARK: - Singleton
    static let shared = PressAndHoldVoiceService()

    // MARK: - Published State
    @Published var state: PressAndHoldVoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var isMuted: Bool = false  // 静音开关

    // MARK: - Callbacks
    var onPartialResult: ((String) -> Void)?
    var onFinalResult: ((String) -> Void)?
    var onTTSEnded: (() -> Void)?
    var onError: ((String) -> Void)?

    // MARK: - Configuration
    private let baseURL: String
    private let token: String

    // MARK: - ASR Components
    private var asrWebSocket: Starscream.WebSocket?
    private var asrWebSocketDelegate: PressAndHoldASRWebSocketDelegate?
    private var audioEngine: AVAudioEngine?
    private var inputNode: AVAudioInputNode?

    // MARK: - 音频转换
    private var audioConverter: AVAudioConverter?
    private var converterInputFormat: AVAudioFormat?

    // MARK: - TTS Components
    private var ttsWebSocket: Starscream.WebSocket?
    private var ttsWebSocketDelegate: PressAndHoldTTSWebSocketDelegate?
    private var audioPlayerNode = AVAudioPlayerNode()
    private var ttsAudioEngine: AVAudioEngine?
    private var ttsFormat: AVAudioFormat
    private var isTTSSpeaking = false
    private var pendingTTSBuffers = 0
    private var isTapInstalled = false
    private var isStopping = false
    private var asrConnected = false  // ASR 连接状态
    private var ttsConnected = false  // TTS 连接状态

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
            sampleRate: VoiceConfig.ttsSampleRate,
            channels: VoiceConfig.ttsChannels,
            interleaved: false
        )!

        super.init()
        #if DEBUG
        print("[PressAndHoldVoiceService] 单例初始化完成")
        #endif
    }

    deinit {
        // deinit 中不能调用 async 方法，直接清理
        asrWebSocket?.delegate = nil
        asrWebSocket?.disconnect()
        ttsWebSocket?.delegate = nil
        ttsWebSocket?.disconnect()
    }

    // MARK: - Public Methods

    /// 连接语音服务
    func connect() async throws {
        #if DEBUG
        print("[PressAndHoldVoiceService] 连接语音服务")
        #endif

        isStopping = false

        // 启动 ASR 和 TTS
        async let asr: Void = connectASR()
        async let tts: Void = connectTTS()

        try await asr
        try await tts

        // 启动音频引擎
        try startAudioEngine()

        state = .idle
        #if DEBUG
        print("[PressAndHoldVoiceService] 语音服务已连接")
        #endif
    }

    /// 断开连接
    func disconnect() {
        #if DEBUG
        print("[PressAndHoldVoiceService] 断开语音服务")
        #endif

        isStopping = true

        // 清理 continuations
        asrContinuation?.resume(throwing: WebSocketVoiceError.disconnected)
        asrContinuation = nil
        ttsContinuation?.resume(throwing: WebSocketVoiceError.disconnected)
        ttsContinuation = nil

        // 断开 WebSocket
        asrWebSocket?.delegate = nil
        asrWebSocket?.disconnect()
        asrWebSocket = nil
        asrWebSocketDelegate = nil
        asrConnected = false

        ttsWebSocket?.delegate = nil
        ttsWebSocket?.disconnect()
        ttsWebSocket = nil
        ttsWebSocketDelegate = nil
        ttsConnected = false

        // 停止音频引擎
        stopTTSAudio()
        inputNode?.removeTap(onBus: 0)
        audioEngine?.stop()

        // 清理引用
        audioEngine = nil
        inputNode = nil
        audioConverter = nil
        converterInputFormat = nil

        // 清理状态
        recognizedText = ""
        state = .idle
        isTapInstalled = false
    }

    /// 开始录音（按住按钮时调用）
    func startRecording() async throws {
        guard case .idle = state else {
            #if DEBUG
            print("[PressAndHoldVoiceService] 当前状态不允许录音: \(state)")
            #endif
            return
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] 开始录音")
        #endif

        // 检查麦克风权限
        try await checkMicrophonePermission()

        // 如果未连接，先连接
        if !asrConnected || asrWebSocket == nil {
            try await connect()
        }

        // 停止 TTS 播放（打断）
        if isTTSSpeaking {
            stopTTSAudio()
        }

        // 安装录音 tap
        installAudioTap()

        state = .listening
        recognizedText = ""
    }

    /// 检查麦克风权限
    private func checkMicrophonePermission() async throws {
        let audioSession = AVAudioSession.sharedInstance()

        // 检查当前权限状态
        let micStatus = audioSession.recordPermission

        if micStatus == .denied {
            state = .error("需要麦克风权限")
            onError?("需要麦克风权限才能使用语音功能")
            throw WebSocketVoiceError.microphonePermissionDenied
        } else if micStatus == .undetermined {
            // 请求权限
            await audioSession.requestRecordPermission { granted in
                if !granted {
                    Task { @MainActor [weak self] in
                        self?.state = .error("需要麦克风权限")
                        self?.onError?("需要麦克风权限才能使用语音功能")
                    }
                }
            }
            // 等待用户响应
            try await Task.sleep(nanoseconds: VoiceConfig.micPermissionWaitTime)

            // 再次检查
            if audioSession.recordPermission == .denied {
                throw WebSocketVoiceError.microphonePermissionDenied
            }
        }
    }

    /// 停止录音并获取最终结果（松开按钮时调用）
    func stopRecording() async -> String? {
        guard case .listening = state else {
            return nil
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] 停止录音")
        #endif

        state = .processing

        // 移除录音 tap
        removeAudioTap()

        // 等待一小段时间让 ASR 完成最后的结果
        try? await Task.sleep(nanoseconds: VoiceConfig.stopRecordingWaitTime)

        let finalText = recognizedText

        if !finalText.isEmpty {
            onFinalResult?(finalText)
            #if DEBUG
            print("[PressAndHoldVoiceService] 识别结果: \(finalText)")
            #endif
        }

        state = .idle
        return finalText.isEmpty ? nil : finalText
    }

    /// 取消录音（上滑时调用）
    func cancelRecording() {
        guard case .listening = state else {
            return
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] 取消录音")
        #endif

        removeAudioTap()
        recognizedText = ""
        state = .idle
    }

    /// 播报 AI 回复
    func speak(_ text: String) async throws {
        guard !isStopping else { return }
        guard !text.isEmpty else { return }
        guard !isMuted else {
            #if DEBUG
            print("[PressAndHoldVoiceService] 已静音，跳过播报")
            #endif
            // 静音状态下直接回调完成
            onTTSEnded?()
            return
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] 播报: \(text.prefix(50))...")
        #endif

        // 如果 TTS 未连接，重新连接
        if !ttsConnected || ttsWebSocket == nil {
            try await connectTTS()
            try startTTSEngine()
        }

        isTTSSpeaking = true
        state = .speaking
        pendingTTSBuffers = 0

        // 发送合成请求
        let request: [String: Any] = [
            "action": "speak",
            "text": text,
            "voice": VoiceConfig.defaultVoice
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: request),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            throw WebSocketVoiceError.synthesisFailed(underlying: NSError(domain: "PressAndHoldVoice", code: -1))
        }

        ttsWebSocket?.write(string: jsonString)
    }

    /// 停止 TTS 播放
    func stopTTSAudio() {
        guard isTTSSpeaking else { return }

        #if DEBUG
        print("[PressAndHoldVoiceService] 停止 TTS 播放")
        #endif

        isTTSSpeaking = false
        audioPlayerNode.stop()

        if let engine = ttsAudioEngine {
            engine.detach(audioPlayerNode)
        }

        ttsAudioEngine?.stop()
        pendingTTSBuffers = 0
        state = .idle
    }

    /// 切换静音状态
    func toggleMute() {
        isMuted.toggle()
        #if DEBUG
        print("[PressAndHoldVoiceService] 静音\(isMuted ? "开启" : "关闭")")
        #endif

        // 如果正在播放，停止它
        if isMuted && isTTSSpeaking {
            stopTTSAudio()
        }
    }

    // MARK: - Private Methods - ASR

    private func connectASR() async throws {
        var components = URLComponents(string: baseURL)!
        components.path = "/ws/voice/asr"
        components.queryItems = [URLQueryItem(name: "token", value: token)]

        guard let url = components.url else {
            throw WebSocketVoiceError.invalidURL
        }

        // 转换为 ws:// 协议
        let wsURLString = url.absoluteString
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")

        guard let wsURL = URL(string: wsURLString) else {
            throw WebSocketVoiceError.invalidURL
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] ASR 连接: \(wsURL.absoluteString)")
        #endif

        try await withCheckedThrowingContinuation { continuation in
            asrContinuation = continuation
            asrWebSocket = Starscream.WebSocket(request: URLRequest(url: wsURL))
            asrWebSocketDelegate = PressAndHoldASRWebSocketDelegate(voiceService: self)
            asrWebSocket?.delegate = asrWebSocketDelegate
            asrWebSocket?.connect()
        }

        asrConnected = true
        asrContinuation = nil
        #if DEBUG
        print("[PressAndHoldVoiceService] ASR 连接成功")
        #endif
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

        if let engine = audioEngine, engine.isRunning {
            #if DEBUG
            print("[PressAndHoldVoiceService] 音频引擎已在运行")
            #endif
            return
        }

        audioEngine?.stop()
        inputNode?.removeTap(onBus: 0)

        audioEngine = AVAudioEngine()
        inputNode = audioEngine?.inputNode

        guard let inputNode = inputNode else {
            throw WebSocketVoiceError.audioEngineNotFound
        }

        let inputFormat = inputNode.outputFormat(forBus: 0)
        #if DEBUG
        print("[PressAndHoldVoiceService] 输入节点格式:")
        print("  - 采样率: \(inputFormat.sampleRate) Hz")
        print("  - 声道数: \(inputFormat.channelCount)")
        #endif

        try audioEngine?.start()
        #if DEBUG
        print("[PressAndHoldVoiceService] 音频引擎已启动, isRunning: \(audioEngine?.isRunning ?? false)")
        #endif
    }

    private func installAudioTap() {
        guard let inputNode = inputNode,
              let audioEngine = audioEngine,
              audioEngine.isRunning else {
            #if DEBUG
            print("[PressAndHoldVoiceService] 无法安装 tap：引擎未运行")
            #endif
            return
        }

        if isTapInstalled {
            #if DEBUG
            print("[PressAndHoldVoiceService] Tap 已安装，跳过")
            #endif
            return
        }

        let inputFormat = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(
            onBus: 0,
            bufferSize: VoiceConfig.asrBufferSize,
            format: inputFormat
        ) { [weak self] buffer, _ in
            guard let self = self else { return }
            self.processAndSendAudio(buffer)
        }

        isTapInstalled = true
        #if DEBUG
        print("[PressAndHoldVoiceService] 录音 tap 已安装")
        #endif
    }

    private func removeAudioTap() {
        inputNode?.removeTap(onBus: 0)
        isTapInstalled = false
        #if DEBUG
        print("[PressAndHoldVoiceService] 录音 tap 已移除")
        #endif
    }

    private func processAndSendAudio(_ buffer: AVAudioPCMBuffer) {
        let frameCount = buffer.frameLength
        if frameCount == 0 {
            return
        }

        guard let pcmData = convertToPCM16(buffer) else { return }

        // 发送 PCM 数据到后端
        asrWebSocket?.write(data: pcmData)
    }

    private func convertToPCM16(_ buffer: AVAudioPCMBuffer) -> Data? {
        let inputFormat = buffer.format

        // 如果已经是 16kHz 单声道，直接转换
        if inputFormat.sampleRate == VoiceConfig.asrSampleRate && inputFormat.channelCount == 1 {
            return convertFloat32ToInt16(buffer)
        }

        // 多声道 → 单声道
        let monoBuffer = inputFormat.channelCount > 1 ? downmixToMono(buffer) : buffer

        // 重采样到 16kHz
        let resampled: AVAudioPCMBuffer
        if monoBuffer.format.sampleRate != VoiceConfig.asrSampleRate {
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
            pcmFormat: AVAudioFormat(
                commonFormat: .pcmFormatFloat32,
                sampleRate: buffer.format.sampleRate,
                channels: 1,
                interleaved: false
            )!,
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
        let targetFormat = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: VoiceConfig.asrSampleRate,
            channels: 1,
            interleaved: false
        )!

        let formatChanged = converterInputFormat == nil ||
            converterInputFormat?.sampleRate != buffer.format.sampleRate ||
            converterInputFormat?.channelCount != buffer.format.channelCount

        if formatChanged || audioConverter == nil {
            audioConverter = AVAudioConverter(from: buffer.format, to: targetFormat)
            converterInputFormat = buffer.format
        }

        guard let converter = audioConverter else {
            return nil
        }

        let ratio = VoiceConfig.asrSampleRate / buffer.format.sampleRate
        let outputFrameCount = AVAudioFrameCount(ceil(Double(buffer.frameLength) * ratio))

        guard let outputBuffer = AVAudioPCMBuffer(
            pcmFormat: targetFormat,
            frameCapacity: outputFrameCount
        ) else {
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

    private func connectTTS() async throws {
        var components = URLComponents(string: baseURL)!
        components.path = "/ws/voice/tts"
        components.queryItems = [URLQueryItem(name: "token", value: token)]

        guard let url = components.url else {
            throw WebSocketVoiceError.invalidURL
        }

        // 转换为 ws:// 协议
        let wsURLString = url.absoluteString
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")

        guard let wsURL = URL(string: wsURLString) else {
            throw WebSocketVoiceError.invalidURL
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] TTS 连接: \(wsURL.absoluteString)")
        #endif

        try await withCheckedThrowingContinuation { continuation in
            ttsContinuation = continuation
            ttsWebSocket = Starscream.WebSocket(request: URLRequest(url: wsURL))
            ttsWebSocketDelegate = PressAndHoldTTSWebSocketDelegate(voiceService: self)
            ttsWebSocket?.delegate = ttsWebSocketDelegate
            ttsWebSocket?.connect()
        }

        ttsConnected = true
        ttsContinuation = nil
        #if DEBUG
        print("[PressAndHoldVoiceService] TTS 连接成功")
        #endif
    }

    private func startTTSEngine() throws {
        if let oldEngine = ttsAudioEngine {
            oldEngine.detach(audioPlayerNode)
        }

        ttsAudioEngine = AVAudioEngine()
        ttsAudioEngine?.attach(audioPlayerNode)
        ttsAudioEngine?.connect(audioPlayerNode, to: ttsAudioEngine!.mainMixerNode, format: ttsFormat)

        try ttsAudioEngine?.start()
        audioPlayerNode.play()

        #if DEBUG
        print("[PressAndHoldVoiceService] TTS 引擎已启动")
        #endif
    }

    func playTTSAudio(_ data: Data) {
        guard ttsAudioEngine != nil, !isStopping else { return }

        guard pendingTTSBuffers < VoiceConfig.maxPendingTTSBuffers else {
            return
        }

        let frameCount = data.count / 2
        guard let buffer = AVAudioPCMBuffer(
            pcmFormat: ttsFormat,
            frameCapacity: AVAudioFrameCount(frameCount)
        ) else {
            return
        }

        buffer.frameLength = AVAudioFrameCount(frameCount)

        guard let channelData = buffer.int16ChannelData else { return }

        data.withUnsafeBytes { rawPtr in
            guard let baseAddr = rawPtr.baseAddress?.assumingMemoryBound(to: Int16.self) else {
                return
            }
            for i in 0..<Int(frameCount) {
                channelData[0][i] = baseAddr[i]
            }
        }

        pendingTTSBuffers += 1

        audioPlayerNode.scheduleBuffer(buffer, completionCallbackType: .dataPlayedBack) { [weak self] _ in
            guard let self = self else { return }

            Task { @MainActor in
                guard !self.isStopping else { return }

                self.pendingTTSBuffers -= 1

                if self.pendingTTSBuffers == 0 && self.isTTSSpeaking {
                    #if DEBUG
                    print("[PressAndHoldVoiceService] TTS 播放完成")
                    #endif

                    self.isTTSSpeaking = false
                    self.state = .idle
                    self.onTTSEnded?()
                }
            }
        }
    }
}

// MARK: - ASR WebSocket Delegate
class PressAndHoldASRWebSocketDelegate: NSObject, WebSocketDelegate {
    private weak var voiceService: PressAndHoldVoiceService?

    init(voiceService: PressAndHoldVoiceService) {
        self.voiceService = voiceService
        super.init()
    }

    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        Task { @MainActor in
            guard let voiceService = self.voiceService else { return }

            switch event {
            case .connected:
                #if DEBUG
                print("[ASRDelegate] ASR WebSocket 已连接")
                #endif
                await voiceService.handleASRConnected()

            case .disconnected(let reason, let code):
                #if DEBUG
                print("[ASRDelegate] ASR 断开: \(reason), code: \(code)")
                #endif
                await voiceService.handleASRDisconnected()

            case .text(let text):
                await voiceService.handleASRTextMessage(text)

            case .error(let error):
                let errorMsg = error?.localizedDescription ?? "未知"
                #if DEBUG
                print("[ASRDelegate] ASR WebSocket 错误: \(errorMsg)")
                #endif
                await voiceService.handleASRError(errorMsg)

            default:
                break
            }
        }
    }
}

// MARK: - TTS WebSocket Delegate
class PressAndHoldTTSWebSocketDelegate: NSObject, WebSocketDelegate {
    private weak var voiceService: PressAndHoldVoiceService?

    init(voiceService: PressAndHoldVoiceService) {
        self.voiceService = voiceService
        super.init()
    }

    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        Task { @MainActor in
            guard let voiceService = self.voiceService else { return }

            switch event {
            case .connected:
                #if DEBUG
                print("[TTSDelegate] TTS WebSocket 已连接")
                #endif
                await voiceService.handleTTSConnected()

            case .disconnected(let reason, let code):
                #if DEBUG
                print("[TTSDelegate] TTS 断开: \(reason), code: \(code)")
                #endif
                await voiceService.handleTTSDisconnected()

            case .text(let text):
                await voiceService.handleTTSTextMessage(text)

            case .binary(let data):
                voiceService.playTTSAudio(data)

            case .error(let error):
                let errorMsg = error?.localizedDescription ?? "未知"
                #if DEBUG
                print("[TTSDelegate] TTS WebSocket 错误: \(errorMsg)")
                #endif
                await voiceService.handleTTSError(errorMsg)

            default:
                break
            }
        }
    }
}

// MARK: - PressAndHoldVoiceService Delegate 处理方法
extension PressAndHoldVoiceService {

    // ASR 连接成功
    func handleASRConnected() {
        asrContinuation?.resume()
        asrContinuation = nil  // 立即清空，防止重复 resume
        asrConnected = true
    }

    // ASR 断开
    func handleASRDisconnected() {
        asrConnected = false
        asrContinuation?.resume(throwing: WebSocketVoiceError.disconnected)
        asrContinuation = nil  // 立即清空
    }

    // ASR 文本消息
    func handleASRTextMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let event = json["event"] as? String else {
            return
        }

        switch event {
        case VoiceEvent.asrReady.eventName:
            #if DEBUG
            print("[PressAndHoldVoiceService] ASR 就绪")
            #endif

        case VoiceEvent.asrPartial.eventName:
            if let text = json["text"] as? String, !text.isEmpty {
                recognizedText = text
                onPartialResult?(text)
            }

        case VoiceEvent.asrFinal.eventName:
            if let text = json["text"] as? String, !text.isEmpty {
                recognizedText = text
            }

        case VoiceEvent.asrRoundComplete.eventName:
            #if DEBUG
            print("[PressAndHoldVoiceService] 一轮识别完成")
            #endif

        case "error":
            if let message = json["message"] as? String {
                #if DEBUG
                print("[PressAndHoldVoiceService] ASR 错误: \(message)")
                #endif
                onError?(message)
            }

        default:
            break
        }
    }

    // ASR 错误
    func handleASRError(_ errorMsg: String) {
        asrConnected = false
        asrContinuation?.resume(throwing: WebSocketVoiceError.recognitionFailed(underlying: NSError(domain: "ASR", code: -1, userInfo: [NSLocalizedDescriptionKey: errorMsg])))
        asrContinuation = nil  // 立即清空
        onError?(errorMsg)
    }

    // TTS 连接成功
    func handleTTSConnected() {
        ttsContinuation?.resume()
        ttsContinuation = nil  // 立即清空，防止重复 resume
        ttsConnected = true
    }

    // TTS 断开
    func handleTTSDisconnected() {
        ttsConnected = false
        ttsContinuation?.resume(throwing: WebSocketVoiceError.disconnected)
        ttsContinuation = nil  // 立即清空
    }

    // TTS 文本消息
    func handleTTSTextMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let event = json["event"] as? String else {
            return
        }

        switch event {
        case VoiceEvent.ttsReady.eventName:
            #if DEBUG
            print("[PressAndHoldVoiceService] TTS 就绪")
            #endif

        case VoiceEvent.ttsFinished.eventName:
            #if DEBUG
            print("[PressAndHoldVoiceService] TTS 音频传输完成")
            #endif

        case "error":
            if let message = json["message"] as? String {
                #if DEBUG
                print("[PressAndHoldVoiceService] TTS 错误: \(message)")
                #endif
            }
            isTTSSpeaking = false
            state = .idle

        default:
            break
        }
    }

    // TTS 错误
    func handleTTSError(_ errorMsg: String) {
        ttsConnected = false
        ttsContinuation?.resume(throwing: WebSocketVoiceError.synthesisFailed(underlying: NSError(domain: "TTS", code: -1, userInfo: [NSLocalizedDescriptionKey: errorMsg])))
        ttsContinuation = nil  // 立即清空
        onError?(errorMsg)
    }
}
