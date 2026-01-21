import Foundation
import AVFoundation
import Combine

// MARK: - 语音活动检测器（智能打断）
/// 用于检测用户是否开始说话，实现智能打断 AI 播报功能
class VoiceActivityDetector: ObservableObject {
    // MARK: - Published Properties
    @Published var isMonitoring = false
    @Published var currentVolume: Float = 0
    @Published var isVoiceDetected = false
    
    // MARK: - Configuration
    var volumeThreshold: Float = 0.08          // 音量阈值
    var minimumDuration: TimeInterval = 0.2    // 最小持续时间（秒）
    var silenceTimeout: TimeInterval = 0.5     // 静音超时（秒）
    
    // MARK: - Callbacks
    var onVoiceStart: (() -> Void)?            // 检测到用户开始说话
    var onVoiceEnd: (() -> Void)?              // 检测到用户停止说话
    
    // MARK: - Private Properties
    private var audioEngine: AVAudioEngine?
    private var voiceStartTime: Date?
    private var lastVoiceTime: Date?
    private var checkTimer: Timer?
    
    // MARK: - Initialization
    init() {}
    
    deinit {
        stopMonitoring()
    }
    
    // MARK: - Public Methods
    
    /// 开始监听麦克风音量
    func startMonitoring() throws {
        guard !isMonitoring else { return }
        
        // 配置音频会话为 playAndRecord 模式，允许在 TTS 播放时同时录音
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetooth, .mixWithOthers])
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        print("[VoiceActivityDetector] 🔧 音频会话已配置为 playAndRecord 模式")
        
        // 创建新的 AudioEngine
        audioEngine = AVAudioEngine()
        guard let audioEngine = audioEngine else {
            throw VoiceActivityError.engineCreationFailed
        }
        
        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        
        // 安装音频 Tap
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            self?.processAudioBuffer(buffer)
        }
        
        audioEngine.prepare()
        try audioEngine.start()
        
        isMonitoring = true
        startCheckTimer()
        
        print("[VoiceActivityDetector] ✅ 开始监听")
    }
    
    /// 停止监听
    func stopMonitoring() {
        checkTimer?.invalidate()
        checkTimer = nil
        
        if let audioEngine = audioEngine {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        audioEngine = nil
        
        voiceStartTime = nil
        lastVoiceTime = nil
        
        DispatchQueue.main.async {
            self.isMonitoring = false
            self.currentVolume = 0
            self.isVoiceDetected = false
        }
        
        print("[VoiceActivityDetector] ⏹ 停止监听")
    }
    
    /// 暂停监听（不释放资源）
    func pauseMonitoring() {
        audioEngine?.pause()
        checkTimer?.invalidate()
        checkTimer = nil
        
        DispatchQueue.main.async {
            self.isMonitoring = false
        }
        
        print("[VoiceActivityDetector] ⏸ 暂停监听")
    }
    
    /// 恢复监听
    func resumeMonitoring() throws {
        guard let audioEngine = audioEngine else {
            try startMonitoring()
            return
        }
        
        try audioEngine.start()
        startCheckTimer()
        
        DispatchQueue.main.async {
            self.isMonitoring = true
        }
        
        print("[VoiceActivityDetector] ▶️ 恢复监听")
    }
    
    // MARK: - Private Methods
    
    private func processAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        let frameLength = Int(buffer.frameLength)
        
        // 计算 RMS 音量
        var sum: Float = 0
        for i in 0..<frameLength {
            let sample = channelData[i]
            sum += sample * sample
        }
        let rms = sqrt(sum / Float(frameLength))
        
        DispatchQueue.main.async {
            self.currentVolume = min(rms * 5, 1.0)  // 归一化到 0-1
        }
        
        // 检测语音活动
        if rms > volumeThreshold {
            handleVoiceDetected()
        }
    }
    
    private func handleVoiceDetected() {
        let now = Date()
        lastVoiceTime = now
        
        if voiceStartTime == nil {
            voiceStartTime = now
        } else if now.timeIntervalSince(voiceStartTime!) >= minimumDuration {
            // 持续时间超过阈值，确认检测到语音
            if !isVoiceDetected {
                DispatchQueue.main.async {
                    self.isVoiceDetected = true
                    self.onVoiceStart?()
                    print("[VoiceActivityDetector] 🎤 检测到用户说话")
                }
            }
        }
    }
    
    private func startCheckTimer() {
        checkTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            self?.checkSilence()
        }
    }
    
    private func checkSilence() {
        guard let lastVoice = lastVoiceTime else { return }
        
        let silenceDuration = Date().timeIntervalSince(lastVoice)
        
        if silenceDuration >= silenceTimeout {
            // 静音超时，重置状态
            voiceStartTime = nil
            
            if isVoiceDetected {
                DispatchQueue.main.async {
                    self.isVoiceDetected = false
                    self.onVoiceEnd?()
                    print("[VoiceActivityDetector] 🔇 用户停止说话")
                }
            }
        }
    }
}

// MARK: - Error Types
enum VoiceActivityError: Error, LocalizedError {
    case engineCreationFailed
    case permissionDenied
    
    var errorDescription: String? {
        switch self {
        case .engineCreationFailed:
            return "无法创建音频引擎"
        case .permissionDenied:
            return "麦克风权限被拒绝"
        }
    }
}
