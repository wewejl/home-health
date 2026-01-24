import Foundation
import AVFoundation
import Combine

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

    // MARK: - Private Properties
    private var audioRecorder: AVAudioRecorder?
    private var recordingTimer: Timer?
    private var levelTimer: Timer?
    private var recordingURL: URL?

    // MARK: - Recording Methods

    func startRecording() {
        // 请求麦克风权限
        if #available(iOS 17.0, *) {
            AVAudioApplication.requestRecordPermission { [weak self] allowed in
                Task { @MainActor in
                    if allowed {
                        await self?.beginRecording()
                    } else {
                        self?.errorMessage = "需要麦克风权限才能录音"
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
                    }
                }
            }
        }
    }

    private func beginRecording() async {
        let audioSession = AVAudioSession.sharedInstance()

        do {
            try audioSession.setCategory(.playAndRecord, mode: .default)
            try audioSession.setActive(true)

            // 创建录音文件路径
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let fileName = "recording_\(Date().timeIntervalSince1970).m4a"
            recordingURL = documentsPath.appendingPathComponent(fileName)

            guard let url = recordingURL else { return }

            // 录音设置
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 44100,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]

            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.record()

            isRecording = true
            recordingDuration = 0
            errorMessage = nil

            // 启动计时器
            recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    self.recordingDuration += 0.1
                }
            }

            // 启动音量监测
            levelTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    self.audioRecorder?.updateMeters()
                    let level = self.audioRecorder?.averagePower(forChannel: 0) ?? -160
                    let normalizedLevel = max(0, (level + 60) / 60)
                    self.audioLevel = normalizedLevel
                }
            }

            print("[Voice] 🎙️ Recording started")

        } catch {
            errorMessage = "录音失败: \(error.localizedDescription)"
            print("[Voice] ❌ Recording error: \(error)")
        }
    }

    func stopRecording() {
        audioRecorder?.stop()
        recordingTimer?.invalidate()
        levelTimer?.invalidate()
        recordingTimer = nil
        levelTimer = nil
        isRecording = false
        audioLevel = 0

        print("[Voice] 🎙️ Recording stopped, duration: \(recordingDuration)s")

        // 自动转写
        if let url = recordingURL {
            Task {
                await transcribeRecording(at: url)
            }
        }
    }

    func cancelRecording() {
        audioRecorder?.stop()
        recordingTimer?.invalidate()
        levelTimer?.invalidate()
        recordingTimer = nil
        levelTimer = nil
        isRecording = false
        audioLevel = 0
        recordingDuration = 0

        // 删除录音文件
        if let url = recordingURL {
            try? FileManager.default.removeItem(at: url)
        }
        recordingURL = nil

        print("[Voice] 🎙️ Recording cancelled")
    }

    // MARK: - Transcription Methods

    private func transcribeRecording(at url: URL) async {
        isTranscribing = true
        errorMessage = nil

        do {
            let audioData = try Data(contentsOf: url)
            let fileName = url.lastPathComponent

            print("[Voice] 📤 Uploading audio for transcription...")

            let response = try await AIService.shared.transcribeAudioFile(
                audioData: audioData,
                fileName: fileName,
                language: "zh",
                extractSymptoms: true
            )

            transcriptionResult = response
            transcribedText = response.text ?? ""
            extractedSymptoms = response.extracted_symptoms ?? []

            print("[Voice] ✅ Transcription completed: \(transcribedText.prefix(50))...")

            // 删除临时文件
            try? FileManager.default.removeItem(at: url)

        } catch {
            errorMessage = "转写失败: \(error.localizedDescription)"
            print("[Voice] ❌ Transcription error: \(error)")
        }

        isTranscribing = false
    }

    /// 使用 Base64 转写
    func transcribeBase64(_ base64String: String) async {
        isTranscribing = true
        errorMessage = nil

        do {
            let response = try await AIService.shared.transcribeAudioBase64(
                audioBase64: base64String,
                language: "zh",
                extractSymptoms: true
            )

            transcriptionResult = response
            transcribedText = response.text ?? ""
            extractedSymptoms = response.extracted_symptoms ?? []

        } catch {
            errorMessage = "转写失败: \(error.localizedDescription)"
        }

        isTranscribing = false
    }

    /// 使用 URL 转写
    func transcribeURL(_ audioUrl: String) async {
        isTranscribing = true
        errorMessage = nil

        do {
            let response = try await AIService.shared.transcribeAudioURL(
                audioUrl: audioUrl,
                language: "zh",
                extractSymptoms: true
            )

            transcriptionResult = response
            transcribedText = response.text ?? ""
            extractedSymptoms = response.extracted_symptoms ?? []

        } catch {
            errorMessage = "转写失败: \(error.localizedDescription)"
        }

        isTranscribing = false
    }

    /// 获取转写任务状态（轮询用）
    func checkTranscriptionStatus(taskId: String) async -> TranscribeStatusResponse? {
        do {
            return try await AIService.shared.getTranscriptionStatus(taskId: taskId)
        } catch {
            print("[Voice] Failed to check status: \(error)")
            return nil
        }
    }

    // MARK: - Utility

    func reset() {
        transcriptionResult = nil
        transcribedText = ""
        extractedSymptoms = []
        errorMessage = nil
        recordingDuration = 0
    }

    var formattedDuration: String {
        let minutes = Int(recordingDuration) / 60
        let seconds = Int(recordingDuration) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
}

