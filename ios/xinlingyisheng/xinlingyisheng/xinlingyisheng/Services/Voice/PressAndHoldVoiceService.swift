//
//  PressAndHoldVoiceService.swift
//  灵犀医生
//
//  按住说话风格的语音服务，类似微信交互
//  - 按住开始录音识别
//  - 松开发送识别文字
//  - 上滑取消
//  - 支持语言切换
//
//  注: TTS (Text-to-Speech) 功能已移除
//

import Foundation
@preconcurrency import AVFoundation
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
    /// 错误状态
    case error(String)

    var displayText: String {
        switch self {
        case .idle: return "按住说话"
        case .listening: return "松开发送"
        case .processing: return "正在处理..."
        case .error(let msg): return msg
        }
    }

    static func == (lhs: PressAndHoldVoiceState, rhs: PressAndHoldVoiceState) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle), (.listening, .listening), (.processing, .processing):
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

    // MARK: - Callbacks
    var onPartialResult: ((String) -> Void)?
    var onFinalResult: ((String) -> Void)?
    var onError: ((String) -> Void)?

    // MARK: - Configuration
    private var baseURL: String {
        return SecurityConfig.apiBaseURL
    }

    private var token: String? {
        return AuthManager.shared.token
    }

    // MARK: - ASR Components
    private var asrWebSocket: Starscream.WebSocket?
    private var asrWebSocketDelegate: PressAndHoldASRWebSocketDelegate?
    private var audioEngine: AVAudioEngine?
    private var inputNode: AVAudioInputNode?

    // MARK: - 音频转换
    private var audioConverter: AVAudioConverter?
    private var converterInputFormat: AVAudioFormat?

    // MARK: - 状态变量
    private var isTapInstalled = false
    private var isStopping = false
    private var asrConnected = false  // ASR 连接状态
    private var hasReceivedFinalResult = false  // 是否已收到 ASR 最终结果
    private var currentLanguage: RecognitionLanguage = .auto  // 当前识别语言

    // MARK: - 心跳保活相关
    private var heartbeatTask: Task<Void, Never>?
    private let heartbeatInterval: UInt64 = 30_000_000_000  // 30秒

    // MARK: - 空闲超时相关
    private var idleTimeoutTask: Task<Void, Never>?
    private let idleTimeoutSeconds: TimeInterval = 300  // 5分钟
    private var lastActivityTime: Date = Date()

    // MARK: - Connection Continuation
    private var asrContinuation: CheckedContinuation<Void, Error>?
    private var finalResultContinuation: CheckedContinuation<String, Never>?

    // MARK: - Init (private for singleton)
    private override init() {
        super.init()
        #if DEBUG
        print("[PressAndHoldVoiceService] 单例初始化完成")
        #endif
    }

    deinit {
        // deinit 中不能调用 async 方法，直接清理
        asrWebSocket?.delegate = nil
        asrWebSocket?.disconnect()
    }

    // MARK: - Public Methods

    /// 连接语音服务
    func connect() async throws {
        #if DEBUG
        print("[PressAndHoldVoiceService] 连接语音服务")
        #endif

        isStopping = false

        // 仅启动 ASR（TTS 已移除）
        try await connectASR()

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

        // 停止心跳
        heartbeatTask?.cancel()
        heartbeatTask = nil

        // 停止空闲超时任务
        idleTimeoutTask?.cancel()
        idleTimeoutTask = nil

        // 清理 continuations
        asrContinuation?.resume(throwing: WebSocketVoiceError.disconnected)
        asrContinuation = nil
        finalResultContinuation?.resume(returning: "")
        finalResultContinuation = nil

        // 断开 WebSocket
        asrWebSocket?.delegate = nil
        asrWebSocket?.disconnect()
        asrWebSocket = nil
        asrWebSocketDelegate = nil
        asrConnected = false

        // 停止音频引擎
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

        // 重置空闲计时器（用户活动）
        resetIdleTimer()

        // 安装录音 tap
        installAudioTap()

        // 重置标志
        hasReceivedFinalResult = false

        state = .listening
        recognizedText = ""
    }

    /// 检查麦克风权限
    private func checkMicrophonePermission() async throws {
        if #available(iOS 17.0, *) {
            // iOS 17+ 使用 AVAudioApplication
            let micStatus = AVAudioApplication.shared.recordPermission

            if micStatus == .denied {
                state = .error("需要麦克风权限")
                onError?("需要麦克风权限才能使用语音功能")
                throw WebSocketVoiceError.microphonePermissionDenied
            } else if micStatus == .undetermined {
                // 请求权限
                AVAudioApplication.requestRecordPermission { granted in
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
                if AVAudioApplication.shared.recordPermission == .denied {
                    throw WebSocketVoiceError.microphonePermissionDenied
                }
            }
        } else {
            // iOS 17 之前使用 AVAudioSession
            let audioSession = AVAudioSession.sharedInstance()
            let micStatus = audioSession.recordPermission

            if micStatus == .denied {
                state = .error("需要麦克风权限")
                onError?("需要麦克风权限才能使用语音功能")
                throw WebSocketVoiceError.microphonePermissionDenied
            } else if micStatus == .undetermined {
                // 请求权限
                audioSession.requestRecordPermission { granted in
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
    }

    /// 停止录音并获取最终结果（松开按钮时调用）
    func stopRecording() async -> String? {
        guard case .listening = state else {
            return nil
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] 停止录音, hasReceivedFinalResult: \(hasReceivedFinalResult)")
        #endif

        state = .processing

        // 重置空闲计时器（用户活动）
        resetIdleTimer()

        // 移除录音 tap
        removeAudioTap()

        // 如果已经收到 ASR 最终结果，直接返回
        if hasReceivedFinalResult {
            let finalText = recognizedText
            state = .idle
            #if DEBUG
            print("[PressAndHoldVoiceService] 已有最终结果，直接返回: \(finalText)")
            #endif
            return finalText.isEmpty ? nil : finalText
        }

        // 使用 Continuation 等待 ASR 最终结果
        // 移除 3 秒短超时，改用 30 秒保护超时
        // 正常情况下后端应该在几秒内返回结果
        let result = await withCheckedContinuation { continuation in
            self.finalResultContinuation = continuation

            // 设置保护超时任务（30 秒）
            Task { @MainActor [weak self] in
                try? await Task.sleep(nanoseconds: 30_000_000_000)  // 30秒保护超时
                guard let self = self else { return }

                // 如果还在等待（后端 30 秒都没响应），强制结束
                if self.finalResultContinuation != nil {
                    self.finalResultContinuation = nil
                    self.state = .idle
                    #if DEBUG
                    print("[PressAndHoldVoiceService] 等待最终结果超时（30秒）")
                    #endif
                    continuation.resume(returning: "")
                }
            }
        }

        state = .idle
        return result.isEmpty ? nil : result
    }

    /// 取消录音（上滑时调用）
    func cancelRecording() {
        guard case .listening = state else {
            return
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] 取消录音")
        #endif

        // 清理 continuation（如果正在等待）
        finalResultContinuation?.resume(returning: "")
        finalResultContinuation = nil

        removeAudioTap()
        recognizedText = ""
        state = .idle
    }

    /// 设置识别语言
    func setLanguage(_ language: RecognitionLanguage) {
        currentLanguage = language
        #if DEBUG
        print("[PressAndHoldVoiceService] 语言设置为: \(language.displayName)")
        #endif
    }

    /// 获取当前语言
    func getLanguage() -> RecognitionLanguage {
        return currentLanguage
    }

    // MARK: - Private Methods - ASR

    private func connectASR() async throws {
        // ⚡ 安全改进：从 AuthManager 获取 Token
        guard let authToken = token else {
            throw WebSocketVoiceError.unauthorized
        }

        // 构建带语言参数的 URL
        let urlString = baseURL + "/ws/voice/asr?language=\(currentLanguage.rawValue)"

        // 转换为 ws:// 协议
        let wsURLString = urlString
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")

        guard let wsURL = URL(string: wsURLString) else {
            throw WebSocketVoiceError.invalidURL
        }

        // 创建 URLRequest，将 Token 放在 Header 中
        var request = URLRequest(url: wsURL)
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")

        #if DEBUG
        print("[PressAndHoldVoiceService] ASR 连接: \(wsURL.absoluteString)")
        print("[PressAndHoldVoiceService] 使用 Header 认证 (Bearer Token)")
        #endif

        try await withCheckedThrowingContinuation { continuation in
            asrContinuation = continuation
            asrWebSocket = Starscream.WebSocket(request: request)
            asrWebSocketDelegate = PressAndHoldASRWebSocketDelegate(voiceService: self)
            asrWebSocket?.delegate = asrWebSocketDelegate
            asrWebSocket?.connect()
        }

        asrConnected = true
        asrContinuation = nil

        // 连接成功后启动心跳
        startHeartbeat()

        // 连接成功后重置空闲计时器
        resetIdleTimer()

        #if DEBUG
        print("[PressAndHoldVoiceService] ASR 连接成功，心跳已启动")
        #endif
    }

    // MARK: - 心跳保活
    /// 启动心跳保活机制
    private func startHeartbeat() {
        // 停止之前的心跳任务
        heartbeatTask?.cancel()

        heartbeatTask = Task { @MainActor [weak self] in
            while !Task.isCancelled && self?.asrConnected == true {
                try? await Task.sleep(nanoseconds: self?.heartbeatInterval ?? 30_000_000_000)

                guard let self = self, self.asrConnected, !Task.isCancelled else {
                    break
                }

                // 发送心跳 ping
                let pingMessage: [String: Any] = ["action": "ping"]
                if let jsonData = try? JSONSerialization.data(withJSONObject: pingMessage),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    self.asrWebSocket?.write(string: jsonString)
                    #if DEBUG
                    print("[PressAndHoldVoiceService] 发送心跳 ping")
                    #endif
                }
            }
        }
    }

    // MARK: - 空闲超时
    /// 重置空闲计时器
    private func resetIdleTimer() {
        lastActivityTime = Date()

        // 取消之前的超时任务
        idleTimeoutTask?.cancel()

        // 启动新的超时任务
        idleTimeoutTask = Task { @MainActor [weak self] in
            guard let self = self else { return }

            // 等待超时时间
            try? await Task.sleep(nanoseconds: UInt64(self.idleTimeoutSeconds * 1_000_000_000))

            // 检查是否真的超时了（可能有新活动重置了计时器）
            let now = Date()
            let elapsed = now.timeIntervalSince(self.lastActivityTime)

            if elapsed >= self.idleTimeoutSeconds && self.asrConnected {
                #if DEBUG
                print("[PressAndHoldVoiceService] 空闲超时（\(Int(elapsed))秒），自动断开连接")
                #endif

                // 只有在 idle 状态时才断开（避免录音中断开）
                if case .idle = self.state {
                    self.disconnect()
                }
            }
        }
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

        // 发送 start 命令到后端（后端协议要求）
        let startCommand: [String: Any] = [
            "action": "start",
            "format": "pcm"
        ]
        if let jsonData = try? JSONSerialization.data(withJSONObject: startCommand),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            asrWebSocket?.write(string: jsonString)
            #if DEBUG
            print("[PressAndHoldVoiceService] 发送 ASR start 命令")
            #endif
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

        // 发送 finish 命令到后端（后端协议要求）
        let finishCommand: [String: Any] = [
            "action": "finish"
        ]
        if let jsonData = try? JSONSerialization.data(withJSONObject: finishCommand),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            asrWebSocket?.write(string: jsonString)
            #if DEBUG
            print("[PressAndHoldVoiceService] 发送 ASR finish 命令")
            #endif
        }

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
                voiceService.handleASRConnected()

            case .disconnected(let reason, let code):
                #if DEBUG
                print("[ASRDelegate] ASR 断开: \(reason), code: \(code)")
                #endif
                voiceService.handleASRDisconnected()

            case .text(let text):
                voiceService.handleASRTextMessage(text)

            case .error(let error):
                let errorMsg = error?.localizedDescription ?? "未知"
                #if DEBUG
                print("[ASRDelegate] ASR WebSocket 错误: \(errorMsg)")
                #endif
                voiceService.handleASRError(errorMsg)

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

        #if DEBUG
        print("[PressAndHoldVoiceService] ASR WebSocket 已连接")
        #endif
    }

    // ASR 断开
    func handleASRDisconnected() {
        asrConnected = false

        // 停止心跳
        heartbeatTask?.cancel()
        heartbeatTask = nil

        // 停止空闲超时任务
        idleTimeoutTask?.cancel()
        idleTimeoutTask = nil

        // 只在连接等待时 resume，避免干扰已建立的连接
        if let continuation = asrContinuation {
            asrContinuation = nil
            continuation.resume(throwing: WebSocketVoiceError.disconnected)
        }

        // 如果不是主动停止，尝试自动重连
        if !isStopping && state != .idle {
            #if DEBUG
            print("[PressAndHoldVoiceService] 连接意外断开，3秒后尝试重连")
            #endif

            Task { @MainActor [weak self] in
                try? await Task.sleep(nanoseconds: 3_000_000_000)
                guard let self = self, !self.isStopping else { return }

                do {
                    try await self.connect()
                    #if DEBUG
                    print("[PressAndHoldVoiceService] 自动重连成功")
                    #endif
                } catch {
                    #if DEBUG
                    print("[PressAndHoldVoiceService] 自动重连失败: \(error)")
                    #endif
                    self.state = .error("连接失败")
                }
            }
        }

        #if DEBUG
        print("[PressAndHoldVoiceService] ASR 断开")
        #endif
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
                hasReceivedFinalResult = true  // 标记已收到最终结果

                // 如果 stopRecording() 正在等待，恢复 continuation
                if let continuation = finalResultContinuation {
                    finalResultContinuation = nil
                    continuation.resume(returning: text)
                    #if DEBUG
                    print("[PressAndHoldVoiceService] 通过 Continuation 返回最终结果: \(text)")
                    #endif
                } else {
                    // 如果没有在等待（已超时或已返回），忽略延迟的结果
                    // 这样可以防止超时后 ASR 结果到达时触发回调，导致状态混乱
                    #if DEBUG
                    print("[PressAndHoldVoiceService] 收到 ASR 最终结果但无等待，已忽略: \(text)")
                    #endif
                }
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
}
