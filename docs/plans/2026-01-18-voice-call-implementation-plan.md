# AI 语音对话功能实现计划（简化版）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有对话界面中集成语音模式，支持文字/语音自由切换、实时识别、AI 语音播报

**Architecture:** 
- **不新建页面**，在现有 `UnifiedChatView` 中添加语音模式
- 扩展 `UnifiedChatViewModel`，添加语音相关状态和方法
- 新建 `RealtimeSpeechService`（语音识别 + VAD）和 `SpeechSynthesisService`（TTS）
- 用户在首页已选择科室，进入对话后点击麦克风切换语音模式

**Tech Stack:** SwiftUI, Combine, Speech Framework, AVFoundation, AVSpeechSynthesizer

---

## Phase 1: 语音服务层

### Task 1: 创建实时语音识别服务

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Services/RealtimeSpeechService.swift`

**Step 1: 创建语音识别服务文件**

```swift
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
        
        isRecording = true
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
        
        isRecording = false
        recognizedText = ""
        audioLevel = 0
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
```

**Step 2: 验证编译**

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/RealtimeSpeechService.swift
git commit -m "feat(voice): add RealtimeSpeechService with VAD"
```

---

### Task 2: 创建语音合成服务

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Services/SpeechSynthesisService.swift`

**Step 1: 创建 TTS 服务文件**

```swift
import Foundation
import AVFoundation
import Combine

// MARK: - 语音合成服务
class SpeechSynthesisService: NSObject, ObservableObject {
    // MARK: - Published Properties
    @Published var isSpeaking = false
    
    // MARK: - Private Properties
    private let synthesizer = AVSpeechSynthesizer()
    private var onStart: (() -> Void)?
    private var onFinish: (() -> Void)?
    
    // MARK: - Init
    override init() {
        super.init()
        synthesizer.delegate = self
    }
    
    // MARK: - Public Methods
    func speak(
        text: String,
        rate: Float = AVSpeechUtteranceDefaultSpeechRate,
        pitch: Float = 1.0,
        volume: Float = 1.0,
        onStart: (() -> Void)? = nil,
        onFinish: (() -> Void)? = nil
    ) {
        self.onStart = onStart
        self.onFinish = onFinish
        
        stop()
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "zh-CN")
        utterance.rate = rate
        utterance.pitchMultiplier = pitch
        utterance.volume = volume
        
        synthesizer.speak(utterance)
    }
    
    func stop() {
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
    }
}

// MARK: - AVSpeechSynthesizerDelegate
extension SpeechSynthesisService: AVSpeechSynthesizerDelegate {
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = true
            self.onStart?()
        }
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = false
            self.onFinish?()
        }
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
    }
}
```

**Step 2: 验证编译**

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/SpeechSynthesisService.swift
git commit -m "feat(voice): add SpeechSynthesisService for TTS"
```

---

## Phase 2: 扩展现有 ViewModel

### Task 3: 扩展 UnifiedChatViewModel 添加语音模式

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`

**Step 1: 添加语音模式属性**

在 `UnifiedChatViewModel` 类中添加以下属性：

```swift
// MARK: - 语音模式属性
@Published var isVoiceMode: Bool = false
@Published var currentRecognition: String = ""
@Published var isRecording: Bool = false
@Published var isAISpeaking: Bool = false
@Published var audioLevel: Float = 0

// MARK: - 语音服务
private let speechService = RealtimeSpeechService()
private let ttsService = SpeechSynthesisService()
private var cancellables = Set<AnyCancellable>()
```

**Step 2: 添加语音模式方法**

```swift
// MARK: - 语音模式方法

/// 切换语音模式
func toggleVoiceMode() {
    isVoiceMode.toggle()
    
    if isVoiceMode {
        startVoiceMode()
    } else {
        stopVoiceMode()
    }
}

/// 开始语音模式
private func startVoiceMode() {
    Task {
        let authorized = await speechService.requestAuthorization()
        guard authorized else {
            await MainActor.run {
                isVoiceMode = false
                // 显示权限错误
            }
            return
        }
        
        do {
            try speechService.startContinuousRecognition(
                onPartialResult: { [weak self] text in
                    self?.currentRecognition = text
                    self?.isRecording = true
                },
                onFinalResult: { [weak self] text in
                    guard let self = self, !text.isEmpty else { return }
                    self.isRecording = false
                    self.currentRecognition = ""
                    // 发送消息
                    Task {
                        await self.sendVoiceMessage(text)
                    }
                }
            )
        } catch {
            await MainActor.run {
                isVoiceMode = false
            }
        }
    }
}

/// 停止语音模式
private func stopVoiceMode() {
    speechService.stopRecognition()
    ttsService.stop()
    isRecording = false
    currentRecognition = ""
    isAISpeaking = false
}

/// 发送语音消息
private func sendVoiceMessage(_ text: String) async {
    // 复用现有的 sendUnifiedMessageStreaming 方法
    inputText = text
    await sendUnifiedMessageStreaming()
}

/// 打断 AI 播报
func interruptAISpeech() {
    if isAISpeaking {
        ttsService.stop()
        isAISpeaking = false
    }
}

/// 播报 AI 回复（在收到 AI 消息后调用）
func speakAIResponse(_ text: String) {
    guard isVoiceMode else { return }
    
    ttsService.speak(
        text: text,
        rate: 0.5,
        onStart: { [weak self] in
            self?.isAISpeaking = true
        },
        onFinish: { [weak self] in
            self?.isAISpeaking = false
        }
    )
}
```

**Step 3: 绑定语音服务状态**

在 `init()` 中添加：

```swift
// 绑定语音服务状态
speechService.$audioLevel
    .receive(on: DispatchQueue.main)
    .assign(to: &$audioLevel)

ttsService.$isSpeaking
    .receive(on: DispatchQueue.main)
    .assign(to: &$isAISpeaking)
```

**Step 4: 验证编译**

**Step 5: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift
git commit -m "feat(voice): extend UnifiedChatViewModel with voice mode"
```

---

## Phase 3: UI 组件

### Task 4: 创建语音控制栏组件

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Components/VoiceControlBar.swift`

**Step 1: 创建语音控制栏**

```swift
import SwiftUI

// MARK: - 语音控制栏
struct VoiceControlBar: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    
    var body: some View {
        VStack(spacing: 12) {
            // 提示文字
            if viewModel.isAISpeaking {
                Text("点击或说话打断")
                    .font(.system(size: 14))
                    .foregroundColor(.gray)
            }
            
            // 控制按钮
            HStack(spacing: 32) {
                // 麦克风按钮
                VoiceButton(
                    icon: "mic.fill",
                    label: "麦克风",
                    isActive: viewModel.isRecording,
                    action: {}
                )
                
                // AI 功能按钮
                VoiceButton(
                    icon: "sparkles",
                    label: "AI生成",
                    isActive: false,
                    action: {}
                )
                
                // 图片按钮
                VoiceButton(
                    icon: "photo",
                    label: "图片",
                    isActive: false,
                    action: {}
                )
                
                // 关闭按钮
                VoiceButton(
                    icon: "xmark",
                    label: "关闭",
                    isActive: false,
                    isDestructive: true,
                    action: {
                        viewModel.toggleVoiceMode()
                    }
                )
            }
            
            // 底部提示
            Text("内容由 AI 生成")
                .font(.system(size: 12))
                .foregroundColor(.gray.opacity(0.6))
        }
        .padding(.vertical, 16)
        .padding(.horizontal, 20)
        .background(Color(hex: "#E8F5E9"))
    }
}

// MARK: - 语音按钮
struct VoiceButton: View {
    let icon: String
    let label: String
    var isActive: Bool = false
    var isDestructive: Bool = false
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                ZStack {
                    Circle()
                        .fill(backgroundColor)
                        .frame(width: 48, height: 48)
                    
                    Image(systemName: icon)
                        .font(.system(size: 20))
                        .foregroundColor(iconColor)
                }
                
                Text(label)
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
            }
        }
    }
    
    private var backgroundColor: Color {
        if isDestructive { return Color.red.opacity(0.1) }
        if isActive { return Color.green.opacity(0.2) }
        return Color.white
    }
    
    private var iconColor: Color {
        if isDestructive { return .red }
        if isActive { return .green }
        return .gray
    }
}
```

**Step 2: 验证编译**

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Components/VoiceControlBar.swift
git commit -m "feat(voice): add VoiceControlBar component"
```

---

### Task 5: 创建录音指示器组件

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Components/RecordingIndicator.swift`

**Step 1: 创建录音指示器**

```swift
import SwiftUI

// MARK: - 录音指示器
struct RecordingIndicator: View {
    @State private var isAnimating = false
    
    var body: some View {
        Circle()
            .fill(Color.red)
            .frame(width: 10, height: 10)
            .scaleEffect(isAnimating ? 1.0 : 0.8)
            .animation(
                .easeInOut(duration: 0.75)
                .repeatForever(autoreverses: true),
                value: isAnimating
            )
            .onAppear {
                isAnimating = true
            }
    }
}

// MARK: - 播报指示器
struct SpeakingIndicator: View {
    var body: some View {
        Image(systemName: "speaker.wave.2.fill")
            .font(.system(size: 14))
            .foregroundColor(.blue)
    }
}
```

**Step 2: 验证编译**

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Components/RecordingIndicator.swift
git commit -m "feat(voice): add RecordingIndicator component"
```

---

### Task 6: 修改 UnifiedChatView 添加语音模式

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/UnifiedChatView.swift`

**Step 1: 添加语音模式切换按钮**

在底部输入栏中添加麦克风按钮：

```swift
// 在输入框旁边添加麦克风按钮
Button(action: {
    viewModel.toggleVoiceMode()
}) {
    Image(systemName: viewModel.isVoiceMode ? "keyboard" : "mic.fill")
        .font(.system(size: 22))
        .foregroundColor(viewModel.isVoiceMode ? .blue : .gray)
}
```

**Step 2: 添加语音模式视图切换**

```swift
// 底部区域根据模式切换
if viewModel.isVoiceMode {
    // 语音模式：显示语音控制栏
    VStack(spacing: 0) {
        // 实时识别显示
        if !viewModel.currentRecognition.isEmpty {
            HStack {
                Image(systemName: "mic.fill")
                    .foregroundColor(.green)
                Text(viewModel.currentRecognition)
                    .foregroundColor(.primary)
                Spacer()
                RecordingIndicator()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color(.systemGray6))
        }
        
        VoiceControlBar(viewModel: viewModel)
    }
    .background(Color(hex: "#E8F5E9"))
} else {
    // 文字模式：显示原有输入栏
    // ... 现有的输入栏代码
}
```

**Step 3: 添加右上角「字幕」按钮**

```swift
// 在导航栏添加
.toolbar {
    ToolbarItem(placement: .navigationBarTrailing) {
        if viewModel.isVoiceMode {
            Button("字幕") {
                viewModel.toggleVoiceMode()
            }
        }
    }
}
```

**Step 4: 修改消息气泡显示播报状态**

在消息气泡中添加播报指示器：

```swift
// 在 AI 消息气泡右侧
if viewModel.isAISpeaking && message.id == viewModel.messages.last?.id {
    SpeakingIndicator()
}
```

**Step 5: 验证编译**

**Step 6: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/UnifiedChatView.swift
git commit -m "feat(voice): add voice mode to UnifiedChatView"
```

---

## Phase 4: 权限配置与测试

### Task 7: 添加 Info.plist 权限说明

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Info.plist`

**Step 1: 添加权限说明**

确保 Info.plist 包含以下权限：

```xml
<key>NSMicrophoneUsageDescription</key>
<string>需要使用麦克风进行语音问诊</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>需要语音识别功能将您的语音转换为文字</string>
```

**Step 2: 验证编译**

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Info.plist
git commit -m "feat(voice): add microphone and speech recognition permissions"
```

---

### Task 8: 端到端测试

**测试用例:**

1. **权限测试**
   - 首次点击麦克风，应弹出麦克风权限请求
   - 首次点击麦克风，应弹出语音识别权限请求

2. **模式切换测试**
   - 点击麦克风按钮进入语音模式
   - 背景变为浅绿色
   - 底部显示语音控制栏
   - 点击「字幕」或「关闭」退出语音模式

3. **语音识别测试**
   - 语音模式下说话，实时显示识别文字
   - 停顿 2 秒后自动发送消息

4. **AI 播报测试**
   - AI 回复后自动语音播报
   - 消息气泡显示播报图标
   - 说话可打断 AI 播报

---

## 文件清单

### 新增文件

| 路径 | 说明 |
|------|------|
| `Services/RealtimeSpeechService.swift` | 实时语音识别 + VAD |
| `Services/SpeechSynthesisService.swift` | TTS 语音合成 |
| `Components/VoiceControlBar.swift` | 语音控制栏 |
| `Components/RecordingIndicator.swift` | 录音/播报指示器 |

### 修改文件

| 路径 | 说明 |
|------|------|
| `ViewModels/UnifiedChatViewModel.swift` | 添加语音模式状态和方法 |
| `Views/UnifiedChatView.swift` | 添加语音模式 UI |
| `Info.plist` | 添加权限说明 |

---

## 依赖关系

```
UnifiedChatView
    └── UnifiedChatViewModel（扩展）
          ├── RealtimeSpeechService（语音识别 + VAD）
          ├── SpeechSynthesisService（TTS）
          └── APIService.shared（复用）
    └── VoiceControlBar
    └── RecordingIndicator / SpeakingIndicator
```

---

## 开发里程碑

### Phase 1: 语音服务层（0.5天）
- [x] RealtimeSpeechService
- [x] SpeechSynthesisService

### Phase 2: ViewModel 扩展（0.5天）
- [ ] 扩展 UnifiedChatViewModel

### Phase 3: UI 组件（1天）
- [ ] VoiceControlBar
- [ ] RecordingIndicator
- [ ] 修改 UnifiedChatView

### Phase 4: 测试与优化（0.5天）
- [ ] 权限配置
- [ ] 端到端测试

**总计: 2.5 天**
