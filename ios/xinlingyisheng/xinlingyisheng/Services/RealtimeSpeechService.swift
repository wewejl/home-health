import Foundation
import Speech
import AVFoundation
import Combine

// MARK: - 实时语音识别服务
class RealtimeSpeechService: ObservableObject {
    // MARK: - Published Properties
    @Published var isRecording = false
    @Published var recognizedText = ""
    @Published var audioLevel: Float = 0
    @Published var error: Error?
    
    // MARK: - Private Properties
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    // VAD 参数
    private let silenceThreshold: TimeInterval = 2.0
    private let volumeThreshold: Float = 0.15
    private var silenceTimer: Timer?
    private var lastSpeechTime: Date?
    
    // 回调
    private var onPartialResult: ((String) -> Void)?
    private var onFinalResult: ((String) -> Void)?
    
    // MARK: - Authorization
    func requestAuthorization() async -> Bool {
        let micStatus = await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
        guard micStatus else { return false }
        
        let speechStatus = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
        return speechStatus
    }
    
    // MARK: - Start Continuous Recognition
    func startContinuousRecognition(
        onPartialResult: @escaping (String) -> Void,
        onFinalResult: @escaping (String) -> Void
    ) throws {
        self.onPartialResult = onPartialResult
        self.onFinalResult = onFinalResult
        
        stopRecognition()
        
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetooth])
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw NSError(domain: "SpeechService", code: -1, userInfo: [NSLocalizedDescriptionKey: "无法创建识别请求"])
        }
        recognitionRequest.shouldReportPartialResults = true
        
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
            self?.processAudioLevel(buffer: buffer)
        }
        
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }
            
            if let result = result {
                let text = result.bestTranscription.formattedString
                DispatchQueue.main.async {
                    self.recognizedText = text
                    self.lastSpeechTime = Date()
                    self.onPartialResult?(text)
                }
                
                if result.isFinal {
                    DispatchQueue.main.async {
                        self.onFinalResult?(text)
                    }
                }
            }
            
            if let error = error {
                DispatchQueue.main.async {
                    self.error = error
                }
            }
        }
        
        audioEngine.prepare()
        try audioEngine.start()
        
        DispatchQueue.main.async {
            self.isRecording = true
        }
        lastSpeechTime = Date()
        startSilenceDetection()
    }
    
    // MARK: - Stop Recognition
    func stopRecognition() {
        silenceTimer?.invalidate()
        silenceTimer = nil
        
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        
        recognitionTask?.cancel()
        recognitionTask = nil
        
        DispatchQueue.main.async {
            self.isRecording = false
            self.recognizedText = ""
            self.audioLevel = 0
        }
    }
    
    // MARK: - Private Methods
    private func processAudioLevel(buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        let frames = buffer.frameLength
        
        var sum: Float = 0
        for i in 0..<Int(frames) {
            sum += abs(channelData[i])
        }
        let average = sum / Float(frames)
        
        DispatchQueue.main.async {
            self.audioLevel = min(average * 10, 1.0)
        }
    }
    
    private func startSilenceDetection() {
        silenceTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            guard let self = self,
                  let lastSpeech = self.lastSpeechTime else { return }
            
            let silenceDuration = Date().timeIntervalSince(lastSpeech)
            
            if silenceDuration >= self.silenceThreshold && !self.recognizedText.isEmpty {
                let finalText = self.recognizedText
                DispatchQueue.main.async {
                    self.onFinalResult?(finalText)
                    self.recognizedText = ""
                    self.lastSpeechTime = Date()
                }
            }
        }
    }
}
