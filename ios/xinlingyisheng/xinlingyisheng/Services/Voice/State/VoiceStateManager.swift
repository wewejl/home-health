import Foundation
import Combine

// MARK: - Voice State Manager
/// 语音状态管理器（状态机）
@MainActor
class VoiceStateManager: ObservableObject {

    // MARK: - Published State
    @Published var state: VoiceState = .idle

    // MARK: - State History
    private var stateHistory: [VoiceState] = []
    private let maxHistoryLength = 10

    // MARK: - Events
    var onStateChange: ((VoiceState, VoiceState) -> Void)?

    // MARK: - Initialization
    init() {
        recordState(.idle)
    }

    // MARK: - Public Methods

    /// 过渡到新状态
    func transition(to newState: VoiceState) {
        let oldState = state

        // 验证状态转换是否合法
        guard isValidTransition(from: oldState, to: newState) else {
            print("[VoiceStateManager] 非法状态转换: \(oldState) -> \(newState)")
            return
        }

        // 执行状态转换
        state = newState
        recordState(newState)

        print("[VoiceStateManager] 状态转换: \(oldState) -> \(newState)")

        // 触发回调
        onStateChange?(oldState, newState)
    }

    /// 重置到空闲状态
    func reset() {
        transition(to: .idle)
    }

    /// 是否可以开始识别
    var canStartListening: Bool {
        switch state {
        case .idle, .error:
            return true
        default:
            return false
        }
    }

    /// 是否可以打断 AI 播报
    var canInterruptAI: Bool {
        switch state {
        case .aiSpeaking:
            return true
        default:
            return false
        }
    }

    /// 是否正在监听
    var isListening: Bool {
        switch state {
        case .listening:
            return true
        default:
            return false
        }
    }

    /// 是否 AI 正在播报
    var isAISpeaking: Bool {
        switch state {
        case .aiSpeaking:
            return true
        default:
            return false
        }
    }

    /// 是否处于错误状态
    var isInError: Bool {
        switch state {
        case .error:
            return true
        default:
            return false
        }
    }

    // MARK: - State Transition Helpers

    /// 开始监听
    func startListening() {
        transition(to: .listening)
    }

    /// 停止监听
    func stopListening() {
        transition(to: .idle)
    }

    /// 开始处理
    func startProcessing() {
        transition(to: .processing)
    }

    /// AI 开始播报
    func startAISpeaking() {
        transition(to: .aiSpeaking)
    }

    /// AI 停止播报
    func stopAISpeaking() {
        transition(to: .idle)
    }

    /// 进入错误状态
    func enterError(_ error: VoiceError) {
        transition(to: .error(error))
    }

    // MARK: - Private Methods

    /// 验证状态转换是否合法
    private func isValidTransition(from: VoiceState, to: VoiceState) -> Bool {
        switch (from, to) {
        // 合法转换
        case (.idle, .listening),
             (.idle, .error),
             (.listening, .idle),
             (.listening, .processing),
             (.listening, .error),
             (.processing, .listening),
             (.processing, .aiSpeaking),
             (.processing, .idle),
             (.processing, .error),
             (.aiSpeaking, .listening),  // 打断
             (.aiSpeaking, .idle),
             (.aiSpeaking, .error),
             (.error, .idle),
             (.error, .listening):
            return true

        // 非法转换
        default:
            return false
        }
    }

    /// 记录状态历史
    private func recordState(_ state: VoiceState) {
        stateHistory.append(state)
        if stateHistory.count > maxHistoryLength {
            stateHistory.removeFirst()
        }
    }

    /// 获取状态历史
    func getStateHistory() -> [VoiceState] {
        return stateHistory
    }
}

// MARK: - State Transition Diagram
/*
 ┌─────────────┐
 │    idle     │
 └──────┬──────┘
        │ start()
        ▼
 ┌─────────────┐     processing     ┌──────────────┐
 │  listening  │ ──────────────────▶│  processing  │
 └──────┬──────┘                   └───────┬──────┘
        │                                   │
        │ stop()                            │ AI reply
        ▼                                   ▼
 ┌─────────────┐                   ┌──────────────┐
 │    idle     │◀──────────────────│  aiSpeaking  │
 └─────────────┘    user interrupt │              │
                                   └──────────────┘

 所有状态都可以转换到 error
 error 可以转换到 idle 或 listening
 */
