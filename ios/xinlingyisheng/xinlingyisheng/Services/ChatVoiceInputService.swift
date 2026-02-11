import Foundation
import Combine
import AVFoundation

/// 语音输入服务
/// 负责：语音识别、语音状态管理、按住说话功能
@MainActor
class ChatVoiceInputService: ObservableObject {
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
        print("[ChatVoiceInputService] deinit")
    }

    /// 主动清理语音绑定（在视图消失时调用）
    func cleanupVoiceBindings() {
        voiceCancellables.removeAll()
        pressAndHoldVoiceService.onPartialResult = nil
        pressAndHoldVoiceService.onFinalResult = nil
        pressAndHoldVoiceService.onError = nil
        print("[ChatVoiceInputService] 语音绑定已清理")
    }

    /// 完整清理资源（在视图完全消失时调用）
    func cleanup() {
        pressAndHoldVoiceService.disconnect()
        cleanupVoiceBindings()
        recognizedText = ""
        voiceState = .idle
        print("[ChatVoiceInputService] 完整资源清理完成")
    }

    // MARK: - 语音服务绑定

    private func setupVoiceBindings() {
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

        pressAndHoldVoiceService.$state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] newState in
                guard let self = self else { return }
                switch newState {
                case .idle:
                    self.voiceState = .idle
                case .listening:
                    self.voiceState = .listening
                case .processing:
                    self.voiceState = .processing
                case .error(let msg):
                    self.voiceState = .error(VoiceError.recognitionFailed(underlying: NSError(domain: "Voice", code: -1, userInfo: [NSLocalizedDescriptionKey: msg])))
                }
            }
            .store(in: &voiceCancellables)
    }

    // MARK: - 按住说话方法

    func startPressAndHoldRecording() async {
        do {
            try await pressAndHoldVoiceService.startRecording()
        } catch {
            print("[ChatVoiceInputService] 开始录音失败: \(error)")
        }
    }

    func stopPressAndHoldRecording() async -> String? {
        let text = await pressAndHoldVoiceService.stopRecording()

        if let finalText = text, !finalText.isEmpty {
            await onFinalResult?(finalText)
        }

        return text
    }

    func cancelPressAndHoldRecording() {
        pressAndHoldVoiceService.cancelRecording()
    }

    /// 切换静音状态（已移除 TTS 功能，此方法保留以保持向后兼容）
    func toggleVoiceMute(_ muted: Bool) {
        print("[ChatVoiceInputService] 静音功能已废弃（TTS 已移除）")
    }

    // MARK: - 私有方法

    private func handleFinalRecognition(_ text: String) async {
        print("[ChatVoiceInputService] 收到最终识别结果: \(text)")
        guard !text.isEmpty else {
            print("[ChatVoiceInputService] 识别结果为空，跳过发送")
            return
        }
    }
}
