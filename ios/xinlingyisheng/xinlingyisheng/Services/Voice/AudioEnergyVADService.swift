import Foundation
import AVFoundation
import Accelerate
import Combine

// MARK: - Audio Energy VAD Configuration
/// 音频能量 VAD 配置
struct AudioEnergyVADConfig {
    /// 能量阈值（0.0-1.0），低于此值认为是静音
    let energyThreshold: Float
    /// 确认说话需要的连续帧数
    let speechConfirmationFrames: Int
    /// 确认静音需要的连续帧数
    let silenceConfirmationFrames: Int
    /// 采样率
    let sampleRate: Double
    /// 帧时长（秒）
    let frameDuration: Double

    /// 默认配置
    static let `default` = AudioEnergyVADConfig(
        energyThreshold: 0.08,          // 能量阈值（更高，只响应明显声音）
        speechConfirmationFrames: 16,   // 约 400ms 确认说话（避免误触发）
        silenceConfirmationFrames: 20,  // 约 500ms 确认静音
        sampleRate: 16000,
        frameDuration: 0.025            // 25ms 每帧
    )

    /// 快速响应配置
    static let responsive = AudioEnergyVADConfig(
        energyThreshold: 0.015,
        speechConfirmationFrames: 2,
        silenceConfirmationFrames: 6,
        sampleRate: 16000,
        frameDuration: 0.025
    )
}

// MARK: - Audio Energy VAD Service
/// 基于音频能量的语音活动检测服务
/// 注意：此服务不创建自己的音频引擎，而是从 BackendASRService 接收音频数据
/// 这样可以避免多个音频引擎同时监听输入节点导致的格式冲突
@MainActor
class AudioEnergyVADService: NSObject {

    // MARK: - Published State
    @Published var isDetecting = false
    @Published var currentEnergyLevel: Float = 0
    @Published var hasVoiceActivity: Bool = false

    // MARK: - Callbacks
    var onVoiceActivityDetected: ((Bool) -> Void)?
    var onSpeechStarted: (() -> Void)?
    var onSpeechEnded: (() -> Void)?
    var onInterruptionConfirmed: (() -> Void)?

    // MARK: - Private Properties
    private let config: AudioEnergyVADConfig

    // VAD 状态
    private var consecutiveSpeechFrames = 0
    private var consecutiveSilenceFrames = 0
    private var isInSpeech = false

    // AI 播报状态标志
    private var isAISpeakingMode: Bool = false

    // 音频电平计算
    private var audioLevel: Float = 0
    private let audioLevelUpdateInterval: Int = 4  // 每4帧更新一次电平

    // 帧计数器
    private var frameCounter = 0
    private let framesPerEnergyUpdate = 4  // 每4帧更新一次电平显示

    // MARK: - Init
    init(config: AudioEnergyVADConfig = .default) {
        self.config = config
        super.init()
    }

    deinit {
        // 不再需要清理音频引擎，因为我们不拥有它
    }

    // MARK: - Public Methods

    /// 启动 VAD 检测（仅标记状态，音频数据由外部提供）
    func start() throws {
        guard !isDetecting else { return }

        print("[AudioEnergyVAD] VAD 检测已就绪，等待外部音频数据")
        isDetecting = true
    }

    /// 停止 VAD 检测
    func stop() {
        guard isDetecting else { return }

        print("[AudioEnergyVAD] 停止 VAD 检测")
        isDetecting = false
        reset()
    }

    /// 处理外部音频缓冲区（由 BackendASRService 提供）
    /// - Parameter buffer: 音频缓冲区
    func processExternalAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        guard isDetecting else { return }

        guard let channelData = buffer.floatChannelData else { return }

        let frameCount = Int(buffer.frameLength)
        let data = channelData.pointee

        // 计算 RMS 能量
        var sum: Float = 0
        vDSP_measqv(data, 1, &sum, vDSP_Length(frameCount))
        let rms = sqrt(sum)
        let normalizedEnergy = min(rms * 10, 1.0)  // 归一化并放大

        // 更新状态（减少更新频率以提升性能）
        frameCounter += 1
        if frameCounter >= framesPerEnergyUpdate {
            frameCounter = 0
            currentEnergyLevel = normalizedEnergy
        }

        // VAD 检测
        let hasSpeech = normalizedEnergy > config.energyThreshold
        updateVADState(hasSpeech: hasSpeech)
    }

    /// 处理外部 PCM 数据（由 BackendASRService 提供）
    /// - Parameters:
    ///   - pcmData: PCM16 格式的音频数据
    ///   - frameCount: 帧数
    func processExternalPCMData(_ pcmData: Data, frameCount: Int) {
        guard isDetecting else { return }

        // 计算 RMS 能量
        var sum: Float = 0
        pcmData.withUnsafeBytes { rawBuffer in
            guard let baseAddress = rawBuffer.baseAddress else { return }

            let int16Ptr = baseAddress.assumingMemoryBound(to: Int16.self)

            for i in 0..<frameCount {
                let sample = Float(Int16(bigEndian: int16Ptr[i])) / Float(Int16.max)
                sum += sample * sample
            }
        }

        let rms = sqrt(sum / Float(frameCount))
        let normalizedEnergy = min(rms * 10, 1.0)

        // 更新状态
        frameCounter += 1
        if frameCounter >= framesPerEnergyUpdate {
            frameCounter = 0
            currentEnergyLevel = normalizedEnergy
        }

        // VAD 检测
        let hasSpeech = normalizedEnergy > config.energyThreshold
        updateVADState(hasSpeech: hasSpeech)
    }

    /// 重置 VAD 状态
    func reset() {
        consecutiveSpeechFrames = 0
        consecutiveSilenceFrames = 0
        isInSpeech = false
        hasVoiceActivity = false
    }

    /// 进入 AI 播报状态（准备检测打断）
    func enterAISpeakingMode() {
        isAISpeakingMode = true
        isInSpeech = false
        consecutiveSpeechFrames = 0  // 重置计数器
        print("[AudioEnergyVAD] 进入 AI 播报模式，开始监听打断")
    }

    /// 退出 AI 播报状态
    func exitAISpeakingMode() {
        isAISpeakingMode = false
        isInSpeech = false
        consecutiveSpeechFrames = 0
        print("[AudioEnergyVAD] 退出 AI 播报模式")
    }

    // MARK: - Private Methods

    private func updateVADState(hasSpeech: Bool) {
        var newState: Bool? = nil

        if hasSpeech {
            consecutiveSpeechFrames += 1
            consecutiveSilenceFrames = 0

            // 检测到说话开始
            if !isInSpeech && consecutiveSpeechFrames >= config.speechConfirmationFrames {
                isInSpeech = true
                newState = true
                hasVoiceActivity = true
                onSpeechStarted?()
                print("[AudioEnergyVAD] 检测到说话开始")

                // 打断检测：AI 播报时检测到用户说话
                if isAISpeakingMode {
                    onInterruptionConfirmed?()
                    print("[AudioEnergyVAD] ✅ 检测到打断（用户说话）")
                }
            }

        } else {
            consecutiveSilenceFrames += 1

            // 检测到说话结束
            if isInSpeech && consecutiveSilenceFrames >= config.silenceConfirmationFrames {
                isInSpeech = false
                newState = false
                hasVoiceActivity = false
                onSpeechEnded?()
                print("[AudioEnergyVAD] 检测到说话结束")
            }
        }

        // 回调当前状态
        if let state = newState {
            onVoiceActivityDetected?(state)
        }
    }
}
