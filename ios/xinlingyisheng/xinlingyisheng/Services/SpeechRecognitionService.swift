import Foundation
import AVFoundation
import Combine

// MARK: - 语音识别服务
@MainActor
class SpeechRecognitionService: ObservableObject {
    
    // MARK: - Published 属性
    @Published var isRecording = false
    @Published var isUploading = false
    @Published var recognizedText = ""
    @Published var errorMessage: String?
    
    // MARK: - 私有属性
    private var audioRecorder: AVAudioRecorder?
    private var recordingURL: URL?
    private let transcriptionService = TranscriptionAPIService.shared
    
    // MARK: - 单例
    static let shared = SpeechRecognitionService()
    
    // MARK: - 初始化
    private init() {}
    
    // MARK: - 请求麦克风权限
    func requestAuthorization() async -> Bool {
        let granted: Bool
        if #available(iOS 17.0, *) {
            granted = await AVAudioApplication.requestRecordPermission()
        } else {
            granted = await withCheckedContinuation { continuation in
                AVAudioSession.sharedInstance().requestRecordPermission { granted in
                    continuation.resume(returning: granted)
                }
            }
        }
        
        if !granted {
            errorMessage = "麦克风权限被拒绝，请在设置中开启"
        }
        
        return granted
    }
    
    // MARK: - 开始录音识别
    func startRecording() async {
        if isRecording {
            stopRecording()
            return
        }
        
        // 检查权限
        guard await requestAuthorization() else { return }
        
        // 重置状态
        recognizedText = ""
        errorMessage = nil
        
        do {
            // 配置音频会话
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers])
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
            
            let fileURL = makeRecordingURL()
            recordingURL = fileURL
            if FileManager.default.fileExists(atPath: fileURL.path) {
                try FileManager.default.removeItem(at: fileURL)
            }
            
            let settings: [String: Any] = [
                AVFormatIDKey: kAudioFormatMPEG4AAC,
                AVSampleRateKey: 16000,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]
            
            audioRecorder = try AVAudioRecorder(url: fileURL, settings: settings)
            audioRecorder?.prepareToRecord()
            audioRecorder?.record()
            
            isRecording = true
        } catch {
            errorMessage = "录音启动失败: \(error.localizedDescription)"
            stopRecording(cleanupOnly: true)
        }
    }
    
    // MARK: - 停止录音识别
    func stopRecording() {
        stopRecording(cleanupOnly: false)
    }
    
    private func stopRecording(cleanupOnly: Bool) {
        if isRecording {
            audioRecorder?.stop()
            audioRecorder = nil
            isRecording = false
        }
        
        do {
            try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        } catch {
            print("重置音频会话失败: \(error)")
        }
        
        guard !cleanupOnly, let fileURL = recordingURL else {
            cleanupRecordingFile()
            return
        }
        
        Task {
            await transcribeRecording(at: fileURL)
        }
    }
    
    private func transcribeRecording(at url: URL) async {
        isUploading = true
        defer {
            isUploading = false
            cleanupRecordingFile()
        }
        
        do {
            let response = try await transcriptionService.transcribeAudioFile(at: url)
            recognizedText = response.text
            errorMessage = nil
        } catch {
            errorMessage = "语音识别失败: \(error.localizedDescription)"
        }
    }
    
    private func makeRecordingURL() -> URL {
        let tempDir = FileManager.default.temporaryDirectory
        return tempDir.appendingPathComponent("voice-input.m4a")
    }
    
    private func cleanupRecordingFile() {
        if let url = recordingURL {
            try? FileManager.default.removeItem(at: url)
        }
        recordingURL = nil
    }
    
    // MARK: - 切换录音状态
    func toggleRecording() async {
        if isRecording {
            stopRecording()
        } else {
            await startRecording()
        }
    }
}
