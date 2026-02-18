//
//  SimpleSpeechInputService.swift
//  灵犀医生
//
//  简化的语音输入服务 - 点击式录音
//  统一使用阿里云 ASR (通过后端 HTTP API)
//

import Foundation
import AVFoundation
import Combine

// MARK: - 语音输入状态
enum SpeechInputState {
    case idle
    case recording
    case processing
    case error(String)

    var displayText: String {
        switch self {
        case .idle: return "点击开始语音输入"
        case .recording: return "正在录音..."
        case .processing: return "正在识别..."
        case .error(let msg): return msg
        }
    }
}

// MARK: - 语音输入服务
/// 简化的语音输入服务，用于点击式语音输入
/// 统一使用后端阿里云 ASR (HTTP API /ai/transcribe)
@MainActor
class SimpleSpeechInputService: ObservableObject {

    // MARK: - Published 属性
    @Published var isRecording = false
    @Published var isUploading = false
    @Published var recognizedText = ""
    @Published var errorMessage: String?
    @Published var recordingDuration: TimeInterval = 0

    // MARK: - 私有属性
    private var audioRecorder: AVAudioRecorder?
    private var recordingURL: URL?
    private var recordingTimer: Timer?
    private var transcribeTask: Task<Void, Never>?

    // MARK: - 常量
    private enum Constants {
        static let audioLevelUpdateInterval: TimeInterval = 0.1
        static let maxRecordingDuration: TimeInterval = 60  // 最大录音时长 60秒
    }

    // MARK: - 单例
    static let shared = SimpleSpeechInputService()

    // MARK: - 初始化
    private init() {}

    // MARK: - 请求麦克风权限
    func requestAuthorization() async -> Bool {
        // iOS 17+ 使用 AVAudioApplication API
        if #available(iOS 17.0, *) {
            let appStatus = AVAudioApplication.shared.recordPermission

            switch appStatus {
            case .denied:
                errorMessage = "麦克风权限被拒绝，请在设置中开启"
                return false
            case .undetermined:
                let granted = await AVAudioApplication.requestRecordPermission()
                if !granted {
                    errorMessage = "麦克风权限被拒绝"
                }
                return granted
            case .granted:
                return true
            @unknown default:
                return true
            }
        } else {
            // iOS 17 之前使用 AVAudioSession API
            let sessionStatus = AVAudioSession.sharedInstance().recordPermission

            switch sessionStatus {
            case .denied:
                errorMessage = "麦克风权限被拒绝，请在设置中开启"
                return false
            case .undetermined:
                let audioSession = AVAudioSession.sharedInstance()
                return await withCheckedContinuation { continuation in
                    audioSession.requestRecordPermission { granted in
                        continuation.resume(returning: granted)
                    }
                }
            case .granted:
                return true
            @unknown default:
                return true
            }
        }
    }

    // MARK: - 开始录音识别
    func startRecording() async {
        if isRecording {
            stopRecording()
            return
        }

        // 取消之前的转写任务
        transcribeTask?.cancel()

        // 检查权限
        guard await requestAuthorization() else { return }

        // 重置状态
        recognizedText = ""
        errorMessage = nil
        recordingDuration = 0

        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .voiceChat)
            try audioSession.setActive(true)

            // 创建录音文件路径
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let fileName = "speech_input_\(Date().timeIntervalSince1970).m4a"
            recordingURL = documentsPath.appendingPathComponent(fileName)

            guard let url = recordingURL else {
                errorMessage = "无法创建录音文件路径"
                throw NSError(domain: "SpeechInput", code: -1)
            }

            // 录音设置 - 16kHz 采样率 (阿里云 ASR 要求)
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 16000,  // 阿里云 ASR 要求 16kHz
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]

            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.record()

            isRecording = true

            // 启动计时器
            startRecordingTimer()

            print("[SimpleSpeechInput] 开始录音")

        } catch {
            errorMessage = "录音启动失败: \(error.localizedDescription)"
            print("[SimpleSpeechInput] 录音启动失败: \(error)")
        }
    }

    // MARK: - 停止录音识别
    func stopRecording() {
        guard isRecording else { return }

        audioRecorder?.stop()
        stopRecordingTimer()
        isRecording = false

        print("[SimpleSpeechInput] 停止录音，时长: \(recordingDuration)s")

        // 自动转写
        if let url = recordingURL {
            Task {
                await transcribeRecording(at: url)
            }
        }
    }

    // MARK: - 取消录音
    func cancelRecording() {
        stopRecordingTimer()
        audioRecorder?.stop()
        isRecording = false

        // 删除录音文件
        deleteRecordingFile()

        recordingURL = nil
        errorMessage = nil
        recognizedText = ""
        recordingDuration = 0

        // 重置音频会话
        try? AVAudioSession.sharedInstance().setActive(false)

        print("[SimpleSpeechInput] 取消录音")
    }

    // MARK: - 切换录音状态
    func toggleRecording() async {
        if isRecording {
            stopRecording()
        } else {
            await startRecording()
        }
    }

    // MARK: - 计时器
    private func startRecordingTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: Constants.audioLevelUpdateInterval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                guard self.isRecording else { return }

                self.recordingDuration += Constants.audioLevelUpdateInterval

                // 检查最大时长
                if self.recordingDuration >= Constants.maxRecordingDuration {
                    print("[SimpleSpeechInput] 达到最大录音时长")
                    self.stopRecording()
                }
            }
        }
        RunLoop.current.add(recordingTimer!, forMode: .common)
    }

    private func stopRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }

    // MARK: - 转写方法
    private func transcribeRecording(at url: URL) async {
        isUploading = true
        defer {
            isUploading = false
        }

        do {
            let audioData = try Data(contentsOf: url)
            let fileName = url.lastPathComponent

            print("[SimpleSpeechInput] 开始转写，文件大小: \(audioData.count / 1024)KB")

            // 调用后端转写 API (后端使用阿里云 ASR)
            let response = try await AIService.shared.transcribeAudioFile(
                audioData: audioData,
                fileName: fileName,
                language: "zh",  // 默认中文
                extractSymptoms: false
            )

            recognizedText = response.text ?? ""
            errorMessage = nil

            print("[SimpleSpeechInput] 转写完成: \(recognizedText.prefix(50))...")

        } catch {
            errorMessage = "语音识别失败: \(error.localizedDescription)"
            print("[SimpleSpeechInput] 转写失败: \(error)")
        }

        // 删除临时文件
        deleteRecordingFile(at: url)
    }

    // MARK: - 工具方法
    private func deleteRecordingFile(at url: URL? = nil) {
        let fileURL = url ?? recordingURL
        guard let fileURL = fileURL else { return }

        do {
            try FileManager.default.removeItem(at: fileURL)
            print("[SimpleSpeechInput] 临时文件已删除")
        } catch {
            print("[SimpleSpeechInput] 删除临时文件失败: \(error)")
        }

        if url == nil {
            recordingURL = nil
        }
    }

    // MARK: - 格式化的录音时长
    var formattedDuration: String {
        let minutes = Int(recordingDuration) / 60
        let seconds = Int(recordingDuration) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    // MARK: - 清理
    func cleanup() {
        transcribeTask?.cancel()
        transcribeTask = nil

        stopRecordingTimer()
        audioRecorder?.stop()
        audioRecorder = nil

        deleteRecordingFile()

        isRecording = false
        isUploading = false
        recognizedText = ""
        errorMessage = nil
        recordingDuration = 0
    }
}
