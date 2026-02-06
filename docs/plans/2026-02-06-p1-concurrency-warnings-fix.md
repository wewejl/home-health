# P1 并发安全警告修复实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 iOS 项目中的 4 个 P1 级别的并发安全警告（MainActor/Sendable 相关）

**Architecture:** 使用 Swift 并发模型最佳实践，通过依赖注入（而非全局单）来解决 @MainActor 隔离类的初始化问题，并将非 Sendable 闭包中的属性访问移到 Task { @MainActor in } 中。

**Tech Stack:** Swift 5.9+, SwiftUI, @MainActor, Sendable, Task, AVFoundation

---

## 修复概览

| 任务 | 文件 | 问题类型 | 修复方案 |
|------|------|----------|----------|
| Task 1 | MedicalFolderViewModel.swift | init 默认参数访问 @MainActor 属性 | 移除默认参数，依赖注入 |
| Task 2 | MedicalFoldersView.swift | 更新调用点 | 注入 APIService.shared |
| Task 3 | CreateRecordSheet.swift | 更新 Preview | 注入 APIService.shared |
| Task 4 | RecordDetailView.swift | 更新 Preview | 注入 APIService.shared |
| Task 5 | VoiceTranscriptionViewModel.swift | Timer 闭包访问 MainActor 属性 | 移到 Task { @MainActor in } |
| Task 6 | VoiceTranscriptionViewModel.swift | NotificationCenter 闭包 | 移到 Task { @MainActor in } |
| Task 7 | PressAndHoldVoiceService.swift | AVAudioPCMBuffer 非 Sendable | @preconcurrency import |

---

## Task 1: 修复 MedicalFolderViewModel 初始化

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/MedicalFolderViewModel.swift:23-25`

**问题:** `main actor-isolated static property 'shared' can not be referenced from a nonisolated context`

**Step 1: 修改 init 签名**

将 `init(apiService: APIService = .shared)` 改为 `init(apiService: APIService)`，移除默认参数：

```swift
// MARK: - Initializer
init(apiService: APIService) {
    self.apiService = apiService
}
```

**修改前（第 23-25 行）：**
```swift
init(apiService: APIService = .shared) {
    self.apiService = apiService
}
```

**Step 2: 构建，验证警告位置变化**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep "MedicalFolderViewModel"`

Expected: 看到调用点（MedicalFoldersView.swift 等）出现编译错误

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/MedicalFolderViewModel.swift
git commit -m "refactor(viewModel): remove default parameter from MedicalFolderViewModel.init"
```

---

## Task 2: 更新 MedicalFoldersView 调用点

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/MedicalFoldersView.swift:7`

**Step 1: 修改 StateObject 初始化**

注入 APIService.shared：

```swift
@StateObject private var viewModel = MedicalFolderViewModel(apiService: .shared)
```

**修改前（第 7 行）：**
```swift
@StateObject private var viewModel = MedicalFolderViewModel()
```

**Step 2: 构建验证**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -A3 "MedicalFoldersView"`

Expected: MedicalFoldersView 相关警告/错误减少

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/MedicalFoldersView.swift
git commit -m "fix(view): inject APIService.shared in MedicalFoldersView"
```

---

## Task 3: 更新 CreateRecordSheet Preview

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/CreateRecordSheet.swift:566`

**Step 1: 修改 Preview 初始化**

注入 APIService.shared：

```swift
#Preview {
    CreateRecordSheet(
        viewModel: MedicalFolderViewModel(apiService: .shared),
        folders: [],
        preselectedFolder: nil
    )
}
```

**修改前（第 565-569 行）：**
```swift
#Preview {
    CreateRecordSheet(
        viewModel: MedicalFolderViewModel(),
        folders: [],
        preselectedFolder: nil
    )
}
```

**Step 2: 构建验证**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -A3 "CreateRecordSheet"`

Expected: CreateRecordSheet 相关警告/错误减少

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/CreateRecordSheet.swift
git commit -m "fix(preview): inject APIService.shared in CreateRecordSheet preview"
```

---

## Task 4: 更新 RecordDetailView Preview

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/RecordDetailView.swift:338`

**Step 1: 修改 Preview 初始化**

注入 APIService.shared：

```swift
#Preview {
    RecordDetailView(
        record: MedicalRecord(
            id: UUID().uuidString,
            folderId: UUID().uuidString,
            userId: 1,
            title: "血常规检查",
            recordDate: Date(),
            description: "年度体检血常规检查结果",
            fileCount: 3
        ),
        viewModel: MedicalFolderViewModel(apiService: .shared)
    )
}
```

**修改前（第 330-339 行）：**
```swift
#Preview {
    RecordDetailView(
        record: MedicalRecord(
            id: UUID().uuidString,
            folderId: UUID().uuidString,
            userId: 1,
            title: "血常规检查",
            recordDate: Date(),
            description: "年度体检血常规检查结果",
            fileCount: 3
        ),
        viewModel: MedicalFolderViewModel()
    )
}
```

**Step 2: 构建验证**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -A3 "RecordDetailView"`

Expected: RecordDetailView 相关警告/错误减少

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/RecordDetailView.swift
git commit -m "fix(preview): inject APIService.shared in RecordDetailView preview"
```

---

## Task 5: 修复 VoiceTranscriptionViewModel Timer 闭包

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/VoiceTranscriptionViewModel.swift:203-228`

**问题:** `main actor-isolated property 'isRecording'/'audioRecorder' can not be referenced from a Sendable closure`

**Step 1: 修改 startMonitoring 方法**

将所有 MainActor 属性访问移到 Task { @MainActor in } 内：

```swift
/// 启动计时和音量监测（合并为一个 Timer）
private func startMonitoring() {
    recordingTimer = Timer.scheduledTimer(withTimeInterval: Constants.audioLevelUpdateInterval, repeats: true) { [weak self] _ in
        // 所有 MainActor 操作都在 Task 内完成
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
```

**修改前（第 201-232 行）：**
```swift
private func startMonitoring() {
    // 使用 CADisplayLink 或 Timer 都可以，这里用 Timer 兼容性好
    recordingTimer = Timer.scheduledTimer(withTimeInterval: Constants.audioLevelUpdateInterval, repeats: true) { [weak self] _ in
        guard let self = self, self.isRecording else { return }

        // 更新计时
        Task { @MainActor [weak self] in
            guard let self = self else { return }
            self.recordingDuration += Constants.audioLevelUpdateInterval

            // 检查最大时长
            if self.recordingDuration >= TranscriptionConfig.maxRecordingDuration {
                print("[Voice] ⏱️ Max recording duration reached")
                self.stopRecording()
                return
            }
        }

        // 更新音量级别
        self.audioRecorder?.updateMeters()
        let level = self.audioRecorder?.averagePower(forChannel: 0) ?? Constants.minAudioLevel
        let normalizedLevel = max(0, (level - Constants.minAudioLevel) / abs(Constants.minAudioLevel))

        Task { @MainActor [weak self] in
            guard let self = self else { return }
            self.audioLevel = normalizedLevel
        }
    }

    // 确保 Timer 在 RunLoop 中运行
    RunLoop.current.add(recordingTimer!, forMode: .common)
}
```

**Step 2: 构建验证**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep "VoiceTranscriptionViewModel" | grep "warning:"`

Expected: 减少 3-4 个 MainActor 相关警告

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/VoiceTranscriptionViewModel.swift
git commit -m "fix(concurrency): move Timer closure MainActor access to Task"
```

---

## Task 6: 修复 VoiceTranscriptionViewModel NotificationCenter 闭包

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/VoiceTranscriptionViewModel.swift:242-248`

**问题:** `call to main actor-isolated instance method in a synchronous nonisolated context`

**Step 1: 修改 setupAudioSessionInterruptionObserver 方法**

将方法调用包装在 Task 中：

```swift
/// 设置音频会话中断监听
private func setupAudioSessionInterruptionObserver() {
    audioSessionObserver = NotificationCenter.default.addObserver(
        forName: AVAudioSession.interruptionNotification,
        object: nil,
        queue: .main
    ) { [weak self] _ in
        Task { @MainActor in
            self?.handleAudioSessionInterruption()
        }
    }
}
```

**修改前（第 241-248 行）：**
```swift
private func setupAudioSessionInterruptionObserver() {
    audioSessionObserver = NotificationCenter.default.addObserver(
        forName: AVAudioSession.interruptionNotification,
        object: nil,
        queue: .main
    ) { [weak self] _ in
        self?.handleAudioSessionInterruption()
    }
}
```

**Step 2: 构建验证**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep "VoiceTranscriptionViewModel" | grep "warning:"`

Expected: 减少 NotificationCenter 相关警告

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/VoiceTranscriptionViewModel.swift
git commit -m "fix(concurrency): wrap NotificationCenter handler in Task"
```

---

## Task 7: 修复 PressAndHoldVoiceService AVAudioPCMBuffer Sendable

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift:14`

**问题:** `capture of 'buffer' with non-Sendable type 'AVAudioPCMBuffer' in a '@Sendable' closure`

**Step 1: 添加 @preconcurrency import**

修改 AVFoundation 的导入：

```swift
@preconcurrency import AVFoundation
```

**修改前（第 15 行）：**
```swift
import AVFoundation
```

**Step 2: 构建验证**

Run: `cd ios/xinlingyisheng && xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep "PressAndHoldVoiceService" | grep "warning:"`

Expected: AVAudioPCMBuffer Sendable 警告消失

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift
git commit -m "fix(concurrency): add @preconcurrency import AVFoundation"
```

---

## 验证步骤

**所有任务完成后执行：**

**Step 1: 完整构建**

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator clean build 2>&1 | tee build.log
```

**Step 2: 检查 P1 警告数量**

```bash
grep "MainActor\|Sendable" build.log | grep "warning:" | wc -l
```

Expected: P1 并发安全警告从 4 个减少到 0 个

**Step 3: 检查具体警告**

```bash
grep -E "MedicalFolderViewModel|VoiceTranscriptionViewModel|PressAndHoldVoiceService" build.log | grep "warning:"
```

Expected: 无 MainActor/Sendable 相关警告

**Step 4: 运行应用测试**

1. 在模拟器中启动应用
2. 导航到病历夹页面，验证功能正常
3. 测试语音录音功能，验证音量显示和计时正常
4. 测试按住说话功能，验证语音识别正常

---

## 最终提交

```bash
git commit --amend -m "fix(ios): resolve P1 concurrency warnings with dependency injection

- Remove default parameter from MedicalFolderViewModel.init
- Inject APIService.shared at all call sites
- Move Timer closure MainActor access to Task context
- Wrap NotificationCenter handler in Task
- Add @preconcurrency import AVFoundation

Resolves 4 P1-level concurrency warnings related to MainActor isolation
and Sendable closure requirements."
```

---

## 文档更新

修改 `docs/plans/2026-02-06-ios-build-warnings-fix.md`：

```markdown
## P1: 并发安全警告 ✅ 已修复

| 文件 | 行号 | 警告内容 | 状态 |
|------|------|----------|------|
| `MedicalFolderViewModel.swift` | 23 | APIService.shared 访问问题 | ✅ 已修复（依赖注入）|
| `VoiceTranscriptionViewModel.swift` | 204, 220-221 | Timer 闭包 | ✅ 已修复 |
| `VoiceTranscriptionViewModel.swift` | 247 | NotificationCenter | ✅ 已修复 |
| `PressAndHoldVoiceService.swift` | 659 | AVAudioPCMBuffer | ✅ 已修复 |
```
