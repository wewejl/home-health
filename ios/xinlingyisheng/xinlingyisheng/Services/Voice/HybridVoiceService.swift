import Foundation
import AVFoundation
import Combine

// MARK: - Hybrid Voice Service (后端代理)
/// 语音服务 - 使用后端代理转发到阿里云
/// 安全性：API Key 只保存在后端，iOS 客户端通过 token 认证
@MainActor
class HybridVoiceService: NSObject, ObservableObject {

    // MARK: - Published State
    @Published var voiceState: VoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var audioLevel: Float = 0

    // MARK: - Callbacks
    var onPartialResult: ((String) -> Void)?
    var onFinalResult: ((String) -> Void)?
    var onVoiceInterruption: (() -> Void)?
    var onError: ((VoiceError) -> Void)?

    // MARK: - Services (后端代理)
    private var backendASRService: BackendVoiceASRService?
    private var backendTTS: BackendVoiceTTSService?
    private var vadService: AudioEnergyVADService?

    // MARK: - Configuration
    private let backendASRConfig: BackendVoiceASRConfig
    private let backendTTSConfig: BackendVoiceTTSConfig

    // MARK: - State
    private(set) var isMicrophoneMuted: Bool = false
    private var isAISpeaking: Bool = false
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Init
    init(
        asrConfig: BackendVoiceASRConfig? = nil,
        ttsConfig: BackendVoiceTTSConfig? = nil
    ) {
        // 使用默认值（在 MainActor 上下文中初始化）
        self.backendASRConfig = asrConfig ?? BackendVoiceASRConfig(
            baseURL: BackendVoiceConfig.baseURL,
            token: BackendVoiceConfig.defaultToken,
            sampleRate: 16000,
            format: "pcm"
        )
        self.backendTTSConfig = ttsConfig ?? BackendVoiceTTSConfig(
            baseURL: BackendVoiceConfig.baseURL,
            token: BackendVoiceConfig.defaultToken,
            voice: .cherry
        )

        // 初始化 VAD
        self.vadService = AudioEnergyVADService()

        // 初始化后端 ASR 服务（连接后端代理）
        self.backendASRService = BackendVoiceASRService(config: backendASRConfig)

        // 将 VAD 服务连接到 ASR 服务，共享音频数据
        self.backendASRService?.vadService = self.vadService

        // 初始化后端 TTS 服务（连接后端代理）
        self.backendTTS = BackendVoiceTTSService(config: backendTTSConfig)

        super.init()

        setupBindings()
        print("[HybridVoice] 初始化完成 - 后端代理模式 (API Key 已隐藏)")
    }

    deinit {
        // 同步清理资源，不创建异步 Task 避免 deinit 问题
        cancellables.removeAll()
        backendASRService = nil
        backendTTS = nil
        vadService = nil
    }

    // MARK: - Public Methods

    /// 启动语音服务
    func start() async throws {
        print("[HybridVoice] 启动后端代理语音识别服务")

        // 启动 VAD
        if let vad = vadService {
            do {
                try vad.start()
            } catch {
                print("[HybridVoice] ⚠️ VAD 启动失败: \(error.localizedDescription)")
                // VAD 失败不影响核心功能，继续执行
            }
        }

        // 启动后端 ASR
        guard let backend = backendASRService else {
            throw VoiceError.recognitionFailed(underlying: NSError(
                domain: "HybridVoice",
                code: -1,
                userInfo: [NSLocalizedDescriptionKey: "后端 ASR 服务未初始化"]
            ))
        }
        try await backend.start()

        // 启动后端 TTS 长连接
        guard let tts = backendTTS else {
            throw VoiceError.recognitionFailed(underlying: NSError(
                domain: "HybridVoice",
                code: -2,
                userInfo: [NSLocalizedDescriptionKey: "后端 TTS 服务未初始化"]
            ))
        }
        do {
            try await tts.start()
            print("[HybridVoice] TTS 长连接已建立")
        } catch {
            print("[HybridVoice] ⚠️ TTS 长连接启动失败: \(error.localizedDescription)")
            // TTS 失败不影响 ASR，继续执行
        }

        updateState(.listening)
        print("[HybridVoice] 后端代理语音服务已启动")
    }

    /// 停止语音服务
    func stop() {
        print("[HybridVoice] 停止语音服务")

        // 停止所有服务
        backendASRService?.stop()
        backendTTS?.stop()
        vadService?.stop()

        // 清理回调
        onPartialResult = nil
        onFinalResult = nil
        onVoiceInterruption = nil
        onError = nil

        // 清理 Combine 订阅
        cancellables.removeAll()

        // 清理状态
        recognizedText = ""
        audioLevel = 0
        isAISpeaking = false
        isMicrophoneMuted = false

        updateState(.idle)

        print("[HybridVoice] 语音服务已停止")
    }

    /// 切换麦克风静音
    func toggleMute() {
        isMicrophoneMuted.toggle()

        if isMicrophoneMuted {
            // 静音：暂停 ASR 和 VAD
            backendASRService?.pause()
            vadService?.stop()
            audioLevel = 0
            print("[HybridVoice] 麦克风已静音")
        } else {
            // 取消静音：恢复 ASR（异步重连）
            Task { @MainActor in
                await backendASRService?.resume()
            }

            // 只在非 AI 播报状态时重新启动 VAD
            if !isAISpeaking {
                if let vad = vadService {
                    do {
                        try vad.start()
                    } catch {
                        print("[HybridVoice] VAD 启动失败: \(error.localizedDescription)")
                    }
                }
            }
            print("[HybridVoice] 麦克风已取消静音")
        }
    }

    /// 进入 AI 播报状态
    func enterAISpeaking() {
        print("[HybridVoice] 进入 AI 播报状态")

        isAISpeaking = true
        vadService?.enterAISpeakingMode()
        backendASRService?.pause()

        updateState(.aiSpeaking)
    }

    /// 退出 AI 播报状态
    func exitAISpeaking() {
        print("[HybridVoice] 退出 AI 播报状态")

        isAISpeaking = false
        vadService?.exitAISpeakingMode()

        if !isMicrophoneMuted {
            Task { @MainActor in
                await backendASRService?.resume()
            }
        }

        updateState(.listening)
    }

    /// 播报 AI 回复（使用后端 TTS 代理）
    func speakAIResponse(_ text: String, completion: @escaping () -> Void) {
        guard !text.isEmpty else {
            exitAISpeaking()
            completion()
            return
        }

        print("[HybridVoice] 播报 AI 回复（后端 TTS 代理），字数: \(text.count)")
        enterAISpeaking()

        // 设置 TTS 完成回调
        backendTTS?.onSynthesisComplete = { [weak self] in
            print("[HybridVoice] TTS 播放完成")
            self?.exitAISpeaking()
            completion()
        }

        // 使用后端 TTS 代理
        Task { @MainActor in
            do {
                try await backendTTS?.synthesizeAndPlay(text: text)
            } catch {
                print("[HybridVoice] TTS 失败: \(error)")
                self.exitAISpeaking()
                completion()
            }
        }
    }

    /// 停止播报
    func stopSpeaking() {
        backendTTS?.stop()
        exitAISpeaking()
    }

    // MARK: - Private Methods

    private func setupBindings() {
        // Backend ASR 绑定
        if let backend = backendASRService {
            backend.$isConnecting
                .receive(on: DispatchQueue.main)
                .sink { [weak self] connecting in
                    if connecting {
                        self?.updateState(.processing)
                    }
                }
                .store(in: &cancellables)

            backend.$isConnected
                .receive(on: DispatchQueue.main)
                .sink { [weak self] connected in
                    if connected {
                        self?.updateState(.listening)
                    }
                }
                .store(in: &cancellables)

            backend.onPartialResult = { [weak self] text in
                self?.recognizedText = text
                self?.onPartialResult?(text)
            }

            backend.onFinalResult = { [weak self] text in
                guard let self = self else { return }
                print("[HybridVoice] 后端 ASR 最终结果: \(text)")
                self.onFinalResult?(text)
                self.recognizedText = ""
            }

            backend.onError = { [weak self] error in
                guard let self = self else { return }
                let voiceError = VoiceError.recognitionFailed(underlying: error)
                self.onError?(voiceError)
                self.updateState(.error(voiceError))
            }
        }

        // VAD Service 绑定
        if let vad = vadService {
            vad.$currentEnergyLevel
                .receive(on: DispatchQueue.main)
                .sink { [weak self] level in
                    self?.audioLevel = level
                }
                .store(in: &cancellables)

            vad.onSpeechStarted = { [weak self] in
                guard let self = self else { return }
                if self.isAISpeaking {
                    print("[HybridVoice] VAD 检测到说话（AI 播报中）- 可能触发打断")
                } else {
                    self.updateState(.listening)
                }
            }

            vad.onSpeechEnded = { [weak self] in
                guard let self = self else { return }
                if self.voiceState == .listening {
                    print("[HybridVoice] VAD 检测到说话结束")
                    // 后端 ASR 会自动返回最终结果
                }
            }

            vad.onInterruptionConfirmed = { [weak self] in
                guard let self = self else { return }
                if self.isAISpeaking {
                    print("[HybridVoice] VAD 确认打断")
                    self.handleInterruption()
                }
            }
        }

        // 后端 TTS 绑定
        if let tts = backendTTS {
            tts.$isPlaying
                .receive(on: DispatchQueue.main)
                .sink { [weak self] isPlaying in
                    guard let self = self else { return }
                    if isPlaying && !self.isAISpeaking {
                        self.enterAISpeaking()
                    }
                }
                .store(in: &cancellables)
        }
    }

    private func updateState(_ newState: VoiceState) {
        voiceState = newState
    }

    private func handleInterruption() {
        print("[HybridVoice] 处理打断")

        // 停止 TTS
        backendTTS?.stop()

        // 触发打断回调
        onVoiceInterruption?()

        // 使用 exitAISpeaking 来正确清理状态（包含 resume）
        // 这会重置 VAD 的 AI 播报模式标志
        exitAISpeaking()

        // 回到监听状态
        if isMicrophoneMuted {
            updateState(.idle)
        }
    }
}

// MARK: - 以下是已注释的 Apple Speech/TTS 代码（保留用于参考）
/*
// MARK: - ASR Mode
enum ASRMode {
    case apple      // Apple Speech (本地)
    case backend    // Backend FunASR (阿里云)

    var displayName: String {
        switch self {
        case .apple: return "Apple Speech"
        case .backend: return "阿里云 FunASR"
        }
    }
}
*/
