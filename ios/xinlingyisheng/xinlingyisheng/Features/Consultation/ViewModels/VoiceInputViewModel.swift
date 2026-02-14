import Foundation
import Combine
import AVFoundation

/// 语音输入 ViewModel
/// 负责：语音识别、语音状态管理、按住说话功能
@MainActor
class VoiceInputViewModel: ObservableObject {
    // MARK: - 语音状态
    @Published var voiceState: VoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var audioLevel: Float = 0
    @Published var showExitConfirmation: Bool = false

    // MARK: - 错误处理
    @Published var errorMessage: String?
    @Published var showError = false

    // MARK: - 语音服务
    private var pressAndHoldVoiceService: PressAndHoldVoiceService {
        return .shared
    }
    private var voiceCancellables = Set<AnyCancellable>()

    // MARK: - 回调
    var onFinalResult: ((String) async -> Void)?

    // MARK: - 初始化

    init() {
        setupVoiceBindings()
    }

    nonisolated deinit {
        print("[VoiceInputVM] deinit")
    }

    /// 主动清理语音绑定（在视图消失时调用）
    func cleanupVoiceBindings() {
        voiceCancellables.removeAll()
        pressAndHoldVoiceService.onPartialResult = nil
        pressAndHoldVoiceService.onFinalResult = nil
        pressAndHoldVoiceService.onError = nil
        print("[VoiceInputVM] 语音绑定已清理")
    }

    /// 完整清理资源（在视图完全消失时调用）
    func cleanup() {
        // 1. 停止语音服务
        pressAndHoldVoiceService.disconnect()

        // 2. 清理语音绑定
        cleanupVoiceBindings()

        // 3. 重置状态
        recognizedText = ""
        voiceState = .idle

        print("[VoiceInputVM] 完整资源清理完成")
    }

    // MARK: - 语音服务绑定

    /// 初始化语音服务绑定
    private func setupVoiceBindings() {
        // 设置 PressAndHoldVoiceService 回调
        pressAndHoldVoiceService.onPartialResult = { [weak self] text in
            Task { @MainActor in
                self?.recognizedText = text
            }
        }

        pressAndHoldVoiceService.onFinalResult = { [weak self] text in
            Task { @MainActor in
                await self?.handleFinalRecognition(text)
            }
        }

        pressAndHoldVoiceService.onError = { [weak self] error in
            Task { @MainActor in
                self?.errorMessage = error
                self?.showError = true
            }
        }

        // 绑定状态变化
        pressAndHoldVoiceService.$state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] newState in
                guard let self = self else { return }
                // 将 PressAndHoldVoiceState 映射到 VoiceState
                switch newState {
                case .idle:
                    self.voiceState = .idle
                case .listening:
                    self.voiceState = .listening
                case .processing:
                    self.voiceState = .processing
                case .unauthorized:
                    self.voiceState = .error(VoiceError.unauthorized)
                case .error(let msg):
                    self.voiceState = .error(VoiceError.recognitionFailed(underlying: NSError(domain: "Voice", code: -1, userInfo: [NSLocalizedDescriptionKey: msg])))
                }
            }
            .store(in: &voiceCancellables)
    }

    // MARK: - 按住说话方法

    /// 开始按住说话录音
    func startPressAndHoldRecording() async {
        do {
            try await pressAndHoldVoiceService.startRecording()
        } catch {
            print("[VoiceInputVM] 开始录音失败: \(error)")
        }
    }

    /// 停止按住说话录音并发送
    func stopPressAndHoldRecording() async -> String? {
        let text = await pressAndHoldVoiceService.stopRecording()

        // 调用回调处理最终结果
        if let finalText = text, !finalText.isEmpty {
            await onFinalResult?(finalText)
        }

        return text
    }

    /// 取消按住说话录音
    func cancelPressAndHoldRecording() {
        pressAndHoldVoiceService.cancelRecording()
    }

    /// 切换静音状态（已移除 TTS 功能，此方法保留以保持向后兼容）
    func toggleVoiceMute(_ muted: Bool) {
        // TTS 功能已移除，静音功能不再需要
        print("[VoiceInputVM] 静音功能已废弃（TTS 已移除）")
    }

    // MARK: - 私有方法

    private func handleFinalRecognition(_ text: String) async {
        print("[VoiceInputVM] 收到最终识别结果: \(text)")
        guard !text.isEmpty else {
            print("[VoiceInputVM] 识别结果为空，跳过发送")
            return
        }

        // 调用回调发送消息
        await onFinalResult?(text)
    }

    private func handleVoiceError(_ error: Error) {
        if let voiceError = error as? VoiceError {
            voiceState = .error(voiceError)
        } else {
            voiceState = .error(VoiceError.recognitionFailed(underlying: error))
        }
        print("[VoiceInputVM] 语音错误: \(error.localizedDescription)")
    }
}
