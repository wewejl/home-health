import Foundation
import AVFoundation
import Combine

// MARK: - 转写配置
struct TranscriptionConfig {
    static let uploadTimeout: TimeInterval = 60.0       // 上传超时时间
    static let maxRetries: Int = 2                       // 最大重试次数
    static let retryDelay: TimeInterval = 1.0           // 重试延迟
    static let maxRecordingDuration: TimeInterval = 600  // 最大录音时长 (10分钟)
    static let timerInterval: TimeInterval = 0.1         // 计时器间隔
}

// MARK: - 转写进度
@MainActor
class TranscriptionProgress: ObservableObject {
    @Published var uploadProgress: Double = 0      // 0.0 ~ 1.0
    @Published var isUploading: Bool = false
    @Published var currentRetry: Int = 0

    func reset() {
        uploadProgress = 0
        isUploading = false
        currentRetry = 0
    }
}

// MARK: - 语音转写 ViewModel
@MainActor
class VoiceTranscriptionViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var isRecording: Bool = false
    @Published var isTranscribing: Bool = false
    @Published var transcriptionResult: TranscribeResponse?
    @Published var transcribedText: String = ""
    @Published var extractedSymptoms: [String] = []
    @Published var errorMessage: String?
    @Published var recordingDuration: TimeInterval = 0
    @Published var audioLevel: Float = 0

    // MARK: - 进度追踪
    @Published var progress = TranscriptionProgress()

    // MARK: - 任务取消
    private var transcribeTask: Task<Void, Never>?

    // MARK: - Private Properties
    private var audioRecorder: AVAudioRecorder?
    private var recordingTimer: Timer?
    private var audioSessionObserver: NSObjectProtocol?
    private var recordingURL: URL?
    private var currentLanguage: RecognitionLanguage = .auto

    // MARK: - 常量
    private enum Constants {
        static let audioLevelUpdateInterval: TimeInterval = 0.1  // 音量级别更新间隔（降低频率）
        static let minAudioLevel: Float = -60.0                    // 最小音频分贝值
    }

    // MARK: - Language Settings
    /// 设置识别语言
    func setLanguage(_ language: RecognitionLanguage) {
        currentLanguage = language
        print("[Voice] Language set to: \(language.displayName)")
    }

    /// 获取当前语言
    func getLanguage() -> RecognitionLanguage {
        return currentLanguage
    }

    // MARK: - Recording Methods

    func startRecording() {
        // 取消之前的转写任务
        cancelTranscription()

        // 请求麦克风权限
        if #available(iOS 17.0, *) {
            AVAudioApplication.requestRecordPermission { [weak self] allowed in
                Task { @MainActor in
                    if allowed {
                        await self?.beginRecording()
                    } else {
                        self?.errorMessage = "需要麦克风权限才能录音"
                        print("[Voice] ⚠️ Microphone permission denied")
                    }
                }
            }
        } else {
            AVAudioSession.sharedInstance().requestRecordPermission { [weak self] allowed in
                Task { @MainActor in
                    if allowed {
                        await self?.beginRecording()
                    } else {
                        self?.errorMessage = "需要麦克风权限才能录音"
                        print("[Voice] ⚠️ Microphone permission denied")
                    }
                }
            }
        }
    }

    private func beginRecording() async {
        let audioSession = AVAudioSession.sharedInstance()

        do {
            // 配置音频会话 - 优化为语音聊天模式
            try audioSession.setCategory(
                .playAndRecord,
                mode: .voiceChat
            )
            try audioSession.setActive(true)

            // 监听音频会话中断（如来电）
            setupAudioSessionInterruptionObserver()

            // 创建录音文件路径
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let fileName = "recording_\(Date().timeIntervalSince1970).m4a"
            recordingURL = documentsPath.appendingPathComponent(fileName)

            guard let url = recordingURL else {
                errorMessage = "无法创建录音文件路径"
                cleanupAudioSession()
                return
            }

            // 录音设置 - 统一使用 16kHz 采样率
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: VoiceConfig.asrSampleRate,  // 16000 Hz
                AVNumberOfChannelsKey: VoiceConfig.asrChannels,  // 1
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]

            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.record()

            isRecording = true
            recordingDuration = 0
            errorMessage = nil
            audioLevel = 0

            // 启动计时器（合并计时和音量监测）
            startMonitoring()

            print("[Voice] ✅ Recording started")

        } catch {
            errorMessage = "录音失败: \(error.localizedDescription)"
            print("[Voice] ❌ Recording error: \(error)")

            // 清理已创建的资源
            cleanupResources()
            cleanupAudioSession()
        }
    }

    func stopRecording() {
        guard isRecording else { return }

        audioRecorder?.stop()
        stopMonitoring()
        isRecording = false
        audioLevel = 0

        print("[Voice] 🎙️ Recording stopped, duration: \(recordingDuration)s")

        // 自动转写
        if let url = recordingURL {
            Task {
                await transcribeRecording(at: url, withRetry: true)
            }
        }
    }

    func cancelRecording() {
        stopMonitoring()
        audioRecorder?.stop()
        isRecording = false
        audioLevel = 0
        recordingDuration = 0

        // 删除录音文件
        deleteRecordingFile()

        recordingURL = nil
        errorMessage = nil

        // 重置音频会话
        cleanupAudioSession()

        print("[Voice] 🎙️ Recording cancelled")
    }

    // MARK: - 监控方法

    /// 启动计时和音量监测（合并为一个 Timer）
    private func startMonitoring() {
        // 所有 MainActor 操作都在 Task 内完成，避免并发警告
        recordingTimer = Timer.scheduledTimer(withTimeInterval: Constants.audioLevelUpdateInterval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self, self.isRecording else { return }

                // 更新计时
                self.recordingDuration += Constants.audioLevelUpdateInterval

                // 检查最大时长
                if self.recordingDuration >= TranscriptionConfig.maxRecordingDuration {
                    print("[Voice] ⏱️ Max recording duration reached")
                    self.stopRecording()
                    return
                }

                // 更新音量级别
                self.audioRecorder?.updateMeters()
                let level = self.audioRecorder?.averagePower(forChannel: 0) ?? Constants.minAudioLevel
                let normalizedLevel = max(0, (level - Constants.minAudioLevel) / abs(Constants.minAudioLevel))
                self.audioLevel = normalizedLevel
            }
        }

        // 确保 Timer 在 RunLoop 中运行
        RunLoop.current.add(recordingTimer!, forMode: .common)
    }

    /// 停止监控
    private func stopMonitoring() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }

    /// 设置音频会话中断监听
    private func setupAudioSessionInterruptionObserver() {
        audioSessionObserver = NotificationCenter.default.addObserver(
            forName: AVAudioSession.interruptionNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.handleAudioSessionInterruption()
            }
        }
    }

    /// 处理音频会话中断
    private func handleAudioSessionInterruption() {
        if isRecording {
            print("[Voice] ⚠️ Audio session interrupted, pausing recording")
            audioRecorder?.pause()
        }
    }

    // MARK: - Transcription Methods

    /// 转写录音文件（带重试和超时控制）
    private func transcribeRecording(at url: URL, withRetry: Bool = false) async {
        // 取消之前的任务
        cancelTranscription()

        // 创建新任务
        transcribeTask = Task {
            await performTranscription(at: url, withRetry: withRetry)
        }

        await transcribeTask?.value
    }

    /// 执行转写（支持取消）
    private func performTranscription(at url: URL, withRetry: Bool) async {
        isTranscribing = true
        errorMessage = nil
        progress.reset()

        do {
            // 检查取消
            guard !Task.isCancelled else { return }

            let audioData = try Data(contentsOf: url)
            let fileName = url.lastPathComponent

            print("[Voice] 📤 Uploading audio for transcription...")
            print("[Voice] 🌐 Language: \(currentLanguage.displayName)")
            print("[Voice] 📊 File size: \(audioData.count / 1024)KB")

            progress.isUploading = true
            progress.uploadProgress = 0.1

            // 执行转写（带重试）
            let response: TranscribeResponse
            if withRetry {
                response = try await transcribeWithRetry(
                    audioData: audioData,
                    fileName: fileName
                )
            } else {
                response = try await AIService.shared.transcribeAudioFile(
                    audioData: audioData,
                    fileName: fileName,
                    language: currentLanguage.rawValue,
                    extractSymptoms: true
                )
            }

            // 检查取消
            guard !Task.isCancelled else {
                print("[Voice] ⚠️ Transcription cancelled by user")
                return
            }

            progress.uploadProgress = 1.0
            progress.isUploading = false

            transcriptionResult = response
            transcribedText = response.text ?? ""
            extractedSymptoms = response.extracted_symptoms ?? []

            print("[Voice] ✅ Transcription completed")
            print("[Voice] 📝 Text: \(transcribedText.prefix(50))...")
            if !extractedSymptoms.isEmpty {
                print("[Voice] 🏥 Symptoms: \(extractedSymptoms.joined(separator: ", "))")
            }

            // 删除临时文件
            deleteRecordingFile(at: url)

        } catch let error as CancellationError {
            errorMessage = "转写已取消"
            print("[Voice] ⚠️ Transcription cancelled: \(error)")
            progress.reset()

        } catch {
            errorMessage = "转写失败: \(error.localizedDescription)"
            print("[Voice] ❌ Transcription error: \(error)")
            progress.reset()

            // 转写失败时也尝试删除临时文件
            deleteRecordingFile(at: url)
        }

        isTranscribing = false
        transcribeTask = nil
    }

    /// 带重试的转写
    private func transcribeWithRetry(
        audioData: Data,
        fileName: String
    ) async throws -> TranscribeResponse {
        var lastError: Error?

        for attempt in 0..<TranscriptionConfig.maxRetries {
            do {
                progress.currentRetry = attempt

                // 调用 API
                let response = try await AIService.shared.transcribeAudioFile(
                    audioData: audioData,
                    fileName: fileName,
                    language: currentLanguage.rawValue,
                    extractSymptoms: true
                )

                // 成功则返回
                if attempt > 0 {
                    print("[Voice] ✅ Retry \(attempt) succeeded")
                }
                progress.currentRetry = 0
                return response

            } catch {
                lastError = error
                print("[Voice] ⚠️ Attempt \(attempt + 1) failed: \(error.localizedDescription)")

                // 最后一次尝试失败，不再重试
                if attempt < TranscriptionConfig.maxRetries - 1 {
                    // 等待后重试
                    try await Task.sleep(nanoseconds: UInt64(TranscriptionConfig.retryDelay * 1_000_000_000))
                }
            }
        }

        // 如果所有重试都失败，抛出最后一个错误
        if let error = lastError {
            throw error
        }

        // 不应该到达这里
        throw NSError(domain: "TranscriptionError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Unknown error"])
    }

    /// 使用 Base64 转写（支持取消）
    func transcribeBase64(_ base64String: String) async {
        cancelTranscription()

        transcribeTask = Task {
            isTranscribing = true
            errorMessage = nil

            do {
                print("[Voice] 🌐 Language: \(currentLanguage.displayName)")

                let response = try await AIService.shared.transcribeAudioBase64(
                    audioBase64: base64String,
                    language: currentLanguage.rawValue,
                    extractSymptoms: true
                )

                guard !Task.isCancelled else { return }

                transcriptionResult = response
                transcribedText = response.text ?? ""
                extractedSymptoms = response.extracted_symptoms ?? []

            } catch is CancellationError {
                errorMessage = "转写已取消"
            } catch {
                errorMessage = "转写失败: \(error.localizedDescription)"
                print("[Voice] ❌ Transcription error: \(error)")
            }

            isTranscribing = false
        }

        await transcribeTask?.value
    }

    /// 使用 URL 转写（支持取消）
    func transcribeURL(_ audioUrl: String) async {
        cancelTranscription()

        transcribeTask = Task {
            isTranscribing = true
            errorMessage = nil

            do {
                print("[Voice] 🌐 Language: \(currentLanguage.displayName)")

                let response = try await AIService.shared.transcribeAudioURL(
                    audioUrl: audioUrl,
                    language: currentLanguage.rawValue,
                    extractSymptoms: true
                )

                guard !Task.isCancelled else { return }

                transcriptionResult = response
                transcribedText = response.text ?? ""
                extractedSymptoms = response.extracted_symptoms ?? []

            } catch is CancellationError {
                errorMessage = "转写已取消"
            } catch {
                errorMessage = "转写失败: \(error.localizedDescription)"
                print("[Voice] ❌ Transcription error: \(error)")
            }

            isTranscribing = false
        }

        await transcribeTask?.value
    }

    /// 获取转写任务状态（支持取消）
    func checkTranscriptionStatus(taskId: String) async -> TranscribeStatusResponse? {
        do {
            return try await AIService.shared.getTranscriptionStatus(taskId: taskId)
        } catch {
            print("[Voice] ❌ Failed to check status: \(error.localizedDescription)")
            return nil
        }
    }

    /// 取消当前转写任务
    func cancelTranscription() {
        transcribeTask?.cancel()
        transcribeTask = nil
        isTranscribing = false
        progress.reset()
        print("[Voice] ⚠️ Transcription cancelled")
    }

    // MARK: - Utility Methods

    /// 重置状态
    func reset() {
        cancelTranscription()
        transcriptionResult = nil
        transcribedText = ""
        extractedSymptoms = []
        errorMessage = nil
        recordingDuration = 0
        audioLevel = 0
    }

    /// 格式化的录音时长
    var formattedDuration: String {
        let minutes = Int(recordingDuration) / 60
        let seconds = Int(recordingDuration) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    /// 删除录音文件
    private func deleteRecordingFile(at url: URL? = nil) {
        let fileURL = url ?? recordingURL
        guard let fileURL = fileURL else { return }

        do {
            try FileManager.default.removeItem(at: fileURL)
            print("[Voice] ✅ Temporary file deleted: \(fileURL.lastPathComponent)")
        } catch {
            print("[Voice] ⚠️ Failed to delete temporary file: \(error.localizedDescription)")
        }

        if url == nil {
            recordingURL = nil
        }
    }

    /// 清理资源
    private func cleanupResources() {
        stopMonitoring()
        audioRecorder?.stop()
        audioRecorder = nil

        if let observer = audioSessionObserver {
            NotificationCenter.default.removeObserver(observer)
            audioSessionObserver = nil
        }
    }

    /// 清理音频会话
    private func cleanupAudioSession() {
        do {
            try AVAudioSession.sharedInstance().setActive(false)
            print("[Voice] ✅ Audio session deactivated")
        } catch {
            print("[Voice] ⚠️ Failed to deactivate audio session: \(error.localizedDescription)")
        }
    }

    // MARK: - Cleanup

    deinit {
        // 取消所有任务
        transcribeTask?.cancel()
        transcribeTask = nil

        // 清理资源
        recordingTimer?.invalidate()
        recordingTimer = nil

        audioRecorder?.stop()
        audioRecorder = nil

        // 移除通知观察者
        if let observer = audioSessionObserver {
            NotificationCenter.default.removeObserver(observer)
            audioSessionObserver = nil
        }

        // 清理音频会话
        do {
            try AVAudioSession.sharedInstance().setActive(false)
        } catch {
            print("[VoiceTranscriptionVM] ⚠️ Failed to deactivate audio session in deinit")
        }

        print("[VoiceTranscriptionVM] deinit - All resources cleaned up")
    }
}

// MARK: - Transcription Error Types
enum TranscriptionError: LocalizedError {
    case timeout
    case cancelled
    case networkError(String)

    var errorDescription: String? {
        switch self {
        case .timeout:
            return "操作超时，请检查网络连接"
        case .cancelled:
            return "操作已取消"
        case .networkError(let message):
            return "网络错误: \(message)"
        }
    }

    var failureReason: String? {
        return errorDescription
    }
}
