import Foundation
import Combine
import AVFoundation
import Speech

// MARK: - 语音模式状态
enum VoiceModeState: Equatable {
    case idle                    // 待机：等待用户说话
    case listening               // 监听中：正在识别用户语音
    case processing              // 处理中：发送到后端，等待AI回复
    case aiSpeaking              // 播报中：AI正在播报回复
    case error(String)           // 错误状态
    
    var displayText: String {
        switch self {
        case .idle:
            return "点击开始语音对话"
        case .listening:
            return "正在聆听..."
        case .processing:
            return "正在思考..."
        case .aiSpeaking:
            return "点击或说话打断"
        case .error(let message):
            return message
        }
    }
    
    var isActive: Bool {
        switch self {
        case .listening, .processing, .aiSpeaking:
            return true
        default:
            return false
        }
    }
}

// MARK: - 语音模式 ViewModel
@MainActor
class VoiceModeViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var state: VoiceModeState = .idle
    @Published var recognizedText: String = ""
    @Published var aiResponseText: String = ""
    @Published var audioLevel: Float = 0
    @Published var isMicrophoneMuted: Bool = false
    @Published var showExitConfirmation: Bool = false
    
    // MARK: - Services
    private let speechService = RealtimeSpeechService()
    private let ttsService = SpeechSynthesisService()
    private let voiceActivityDetector = VoiceActivityDetector()
    
    // MARK: - Callbacks
    var onDismiss: (() -> Void)?
    var onSendMessage: ((String) async -> String?)?
    var onImageRequest: ((ImageSourceType) -> Void)?
    
    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()
    private var isVoiceActivityMonitoring = false
    
    // MARK: - Initialization
    init() {
        setupBindings()
        setupCallbacks()
    }
    
    deinit {
        // 注意：deinit 中不能调用 MainActor 隔离的方法
        // 服务会在各自的 deinit 中自动清理
    }
    
    // MARK: - Setup
    private func setupBindings() {
        // 语音识别状态绑定
        speechService.$recognizedText
            .receive(on: DispatchQueue.main)
            .sink { [weak self] text in
                self?.recognizedText = text
            }
            .store(in: &cancellables)
        
        speechService.$audioLevel
            .receive(on: DispatchQueue.main)
            .sink { [weak self] level in
                guard let self = self, !self.isMicrophoneMuted else { return }
                self.audioLevel = level
            }
            .store(in: &cancellables)
        
        // TTS 状态绑定
        ttsService.$isSpeaking
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isSpeaking in
                guard let self = self else { return }
                if isSpeaking && self.state != .aiSpeaking {
                    self.state = .aiSpeaking
                    self.startVoiceActivityMonitoring()
                } else if !isSpeaking && self.state == .aiSpeaking {
                    self.state = .idle
                    self.stopVoiceActivityMonitoring()
                }
            }
            .store(in: &cancellables)
    }
    
    private func setupCallbacks() {
        // 语音识别错误监听（使用 Combine 订阅 @Published var error）
        speechService.$error
            .compactMap { $0 }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] error in
                self?.handleError(error)
            }
            .store(in: &cancellables)

        // 智能打断回调
        voiceActivityDetector.onVoiceStart = { [weak self] in
            Task { @MainActor in
                self?.handleVoiceActivityDetected()
            }
        }
    }
    
    // MARK: - Public Methods
    
    /// 请求权限
    func requestPermissions() async -> Bool {
        let granted = await speechService.requestAuthorization()
        if !granted {
            state = .error("请在设置中开启麦克风和语音识别权限")
        }
        return granted
    }
    
    /// 开始语音模式
    func startVoiceMode() async {
        guard await requestPermissions() else { return }
        
        do {
            try speechService.startContinuousRecognition(
                onPartialResult: { [weak self] text in
                    Task { @MainActor in
                        self?.recognizedText = text
                    }
                },
                onFinalResult: { [weak self] text in
                    Task { @MainActor in
                        await self?.handleFinalRecognition(text)
                    }
                }
            )
            state = .listening
            print("[VoiceModeViewModel] ✅ 语音模式已启动")
        } catch {
            handleError(error)
        }
    }
    
    /// 停止语音模式
    func stopVoiceMode() {
        cleanup()
        state = .idle
        recognizedText = ""
        aiResponseText = ""
        print("[VoiceModeViewModel] ⏹ 语音模式已停止")
    }
    
    /// 切换麦克风静音
    func toggleMicrophone() {
        isMicrophoneMuted.toggle()

        if isMicrophoneMuted {
            audioLevel = 0
            // 静音时暂停识别
            if speechService.isRecording {
                speechService.stopRecognition()
            }
        } else if state == .idle || state == .listening {
            // 取消静音时恢复识别
            Task {
                await startVoiceMode()
            }
        }

        print("[VoiceModeViewModel] 🎤 麦克风\(isMicrophoneMuted ? "已静音" : "已打开")")
    }
    
    /// 打断 AI 播报
    func interruptAISpeaking() {
        if state == .aiSpeaking {
            ttsService.stop()
            stopVoiceActivityMonitoring()

            // 重新开始录音
            if !isMicrophoneMuted {
                Task {
                    await startVoiceMode()
                }
            } else {
                state = .idle
            }
        }
    }
    
    /// 请求拍照
    func requestCamera() {
        onImageRequest?(.camera)
    }
    
    /// 请求相册
    func requestPhotoLibrary() {
        onImageRequest?(.photoLibrary)
    }
    
    /// 请求退出
    func requestExit() {
        showExitConfirmation = true
    }
    
    /// 确认退出
    func confirmExit() {
        showExitConfirmation = false
        stopVoiceMode()
        onDismiss?()
    }
    
    /// 取消退出
    func cancelExit() {
        showExitConfirmation = false
    }
    
    // MARK: - Private Methods
    
    private func handleFinalRecognition(_ text: String) async {
        print("[VoiceModeViewModel] 📝 收到最终识别结果: \(text)")
        guard !text.isEmpty else {
            print("[VoiceModeViewModel] ⚠️ 识别结果为空，跳过发送")
            return
        }
        
        // 停止录音
        speechService.stopRecognition()
        state = .processing
        
        print("[VoiceModeViewModel] 📤 准备发送消息到后端...")
        print("[VoiceModeViewModel] 📤 onSendMessage 回调是否存在: \(onSendMessage != nil)")
        
        // 发送消息到后端
        if let sendMessage = onSendMessage {
            print("[VoiceModeViewModel] 📤 正在调用 onSendMessage...")
            if let response = await sendMessage(text) {
                print("[VoiceModeViewModel] ✅ 收到AI回复: \(response.prefix(50))...")
                aiResponseText = response

                // 播报 AI 回复（传入回调）
                ttsService.speak(
                    text: response,
                    onFinish: { [weak self] in
                        Task { @MainActor in
                            self?.handleTTSFinished()
                        }
                    }
                )
            } else {
                print("[VoiceModeViewModel] ⚠️ AI回复为空")
                // 没有回复，重新开始录音
                if !isMicrophoneMuted {
                    await startVoiceMode()
                } else {
                    state = .idle
                }
            }
        } else {
            print("[VoiceModeViewModel] ❌ onSendMessage 回调未设置!")
            // 没有回调，重新开始录音
            if !isMicrophoneMuted {
                await startVoiceMode()
            } else {
                state = .idle
            }
        }
        
        // 清空识别文本
        recognizedText = ""
    }
    
    private func handleTTSFinished() {
        // 播报完成，重新开始录音
        if !isMicrophoneMuted {
            Task {
                await startVoiceMode()
            }
        } else {
            state = .idle
        }
    }

    private func handleVoiceActivityDetected() {
        // 检测到用户说话，打断 AI 播报
        if state == .aiSpeaking {
            print("[VoiceModeViewModel] 🎤 检测到用户说话，打断AI播报")
            interruptAISpeaking()
        }
    }
    
    private func handleError(_ error: Error) {
        state = .error(error.localizedDescription)
        print("[VoiceModeViewModel] ❌ 错误: \(error.localizedDescription)")
    }
    
    private func startVoiceActivityMonitoring() {
        guard !isVoiceActivityMonitoring else { return }
        
        do {
            try voiceActivityDetector.startMonitoring()
            isVoiceActivityMonitoring = true
            print("[VoiceModeViewModel] 👂 开始语音活动监听（智能打断）")
        } catch {
            print("[VoiceModeViewModel] ⚠️ 无法启动语音活动监听: \(error)")
        }
    }
    
    private func stopVoiceActivityMonitoring() {
        guard isVoiceActivityMonitoring else { return }
        
        voiceActivityDetector.stopMonitoring()
        isVoiceActivityMonitoring = false
        print("[VoiceModeViewModel] 🔇 停止语音活动监听")
    }
    
    private func cleanup() {
        speechService.stopRecognition()
        ttsService.stop()
        stopVoiceActivityMonitoring()
        cancellables.removeAll()
    }
}

// MARK: - Image Source Type
enum ImageSourceType {
    case camera
    case photoLibrary
}
