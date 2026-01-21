# 语音模式功能完善提示词

## 背景说明

我们已经完成了语音模式的UI界面一比一还原（参考竞品小荷AI医生），创建了 `FullScreenVoiceModeView.swift` 全屏语音模式页面。现在需要将真实的语音识别、语音合成、VAD（语音活动检测）功能集成进来。

## 当前状态

### 已完成
1. ✅ 全屏语音模式UI界面（`FullScreenVoiceModeView.swift`）
2. ✅ 三种状态的视觉呈现（待机、识别中、AI播报）
3. ✅ 4个圆形按钮（麦克风、AI生成、图片、关闭）
4. ✅ 挂断确认弹窗
5. ✅ 与 `ModernConsultationView` 的集成（使用 `.fullScreenCover`）

### 待完善
1. ❌ 真实的语音识别功能（iOS Speech Framework）
2. ❌ 真实的语音合成功能（AVSpeechSynthesizer）
3. ❌ VAD 语音活动检测（自动判断用户说话/静默）
4. ❌ 与现有 `UnifiedChatViewModel` 的深度集成
5. ❌ 错误处理和权限请求
6. ❌ 状态同步和数据流

## 任务目标

将 `FullScreenVoiceModeView` 从演示界面升级为完整功能的语音对话系统，实现：
- 用户说话 → 实时语音识别 → 显示文字气泡
- 静默2秒 → 自动发送消息到后端
- AI回复 → 显示文字气泡 + TTS语音播报
- 用户可随时打断AI播报

## 实现步骤

### 第1步：阅读现有代码架构

**必读文件**：
```
1. ios/xinlingyisheng/xinlingyisheng/Views/FullScreenVoiceModeView.swift
   - 当前的UI实现
   - 需要集成真实功能的地方

2. ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift
   - 现有的语音服务集成
   - speechService 和 ttsService 的使用方式
   - 查看 startVoiceMode()、stopVoiceMode() 方法

3. ios/xinlingyisheng/xinlingyisheng/Services/RealtimeSpeechService.swift
   - 语音识别服务实现
   - VAD 参数配置
   - 持续识别模式

4. ios/xinlingyisheng/xinlingyisheng/Services/SpeechSynthesisService.swift
   - 语音合成服务实现
   - TTS 播报控制

5. docs/plans/2026-01-18-voice-call-agent-design.md
   - 完整的设计文档
   - 交互流程和状态机
```

**关键理解点**：
- `UnifiedChatViewModel` 已经有 `speechService` 和 `ttsService` 实例
- 已经有 `isVoiceMode`、`currentRecognition`、`isRecording`、`isAISpeaking` 等状态
- 需要将这些状态和服务与 `FullScreenVoiceModeView` 连接起来

### 第2步：重构 FullScreenVoiceModeView

**目标**：将 `FullScreenVoiceModeView` 改为使用 `@ObservedObject var viewModel: UnifiedChatViewModel`

**修改内容**：
```swift
struct FullScreenVoiceModeView: View {
    // 改为使用传入的 viewModel，而不是内部状态
    @ObservedObject var viewModel: UnifiedChatViewModel
    
    // 回调保持不变
    var onDismiss: () -> Void = {}
    var onSubtitleTap: () -> Void = {}
    var onImageTap: () -> Void = {}
    
    // 删除内部的 @State 变量：
    // - voiceState（改用 viewModel 的状态推导）
    // - recognizedText（改用 viewModel.currentRecognition）
    // - aiResponseText（改用 viewModel.messages.last）
    // - showExitConfirmation（可保留）
    
    // 根据 viewModel 的状态计算当前显示状态
    private var currentState: VoiceModeState {
        if viewModel.isAISpeaking {
            return .aiSpeaking
        } else if viewModel.isRecording {
            return .listening
        } else {
            return .idle
        }
    }
}
```

### 第3步：修改 ModernConsultationView 传递 viewModel

**修改位置**：`ModernConsultationView.swift` 第 97-109 行

```swift
.fullScreenCover(isPresented: $viewModel.isVoiceMode) {
    FullScreenVoiceModeView(
        viewModel: viewModel,  // 传递 viewModel
        onDismiss: {
            viewModel.toggleVoiceMode()
        },
        onSubtitleTap: {
            viewModel.toggleVoiceMode()
        },
        onImageTap: {
            showImageSourcePicker = true
        }
    )
}
```

### 第4步：实现麦克风按钮的真实功能

**当前问题**：麦克风按钮只是切换演示状态

**修改方案**：
```swift
// 在 FullScreenVoiceModeView 的麦克风按钮中
VoiceModeCircleButton(
    icon: "mic.fill",
    label: "麦克风",
    isHighlighted: viewModel.isRecording,
    highlightColor: recordingGreen
) {
    // 如果 AI 正在播报，点击打断
    if viewModel.isAISpeaking {
        viewModel.interruptAISpeech()
    }
    // 否则不需要手动操作，VAD 会自动检测
}
```

**关键点**：
- 语音识别在进入语音模式时自动开启（`startVoiceMode()` 中已实现）
- VAD 会自动检测用户说话，无需手动点击
- 麦克风按钮主要用于打断 AI 播报

### 第5步：实现中央内容区域的数据绑定

**待机状态**：保持不变，显示"请说话"引导

**识别中状态**：
```swift
private var listeningStateContent: some View {
    VStack(spacing: 32) {
        Spacer()
        
        // 显示实时识别文字（从 viewModel 获取）
        if !viewModel.currentRecognition.isEmpty {
            Text(viewModel.currentRecognition)
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(textDarkGray)
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: Color.black.opacity(0.06), radius: 8, y: 4)
        }
        
        Spacer()
        
        // 状态指示
        HStack(spacing: 8) {
            Image(systemName: "mic.fill")
                .font(.system(size: 16))
                .foregroundColor(recordingGreen)
            
            Text("正在聆听...")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(recordingGreen)
        }
    }
}
```

**AI播报状态**：
```swift
private var aiSpeakingStateContent: some View {
    VStack(spacing: 32) {
        Spacer()
        
        // 显示最新的 AI 回复（从 viewModel.messages 获取）
        if let lastMessage = viewModel.messages.last,
           lastMessage.role == .assistant {
            HStack(alignment: .top, spacing: 12) {
                Text(lastMessage.content)
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(textDarkGray)
                    .lineSpacing(4)
                
                // 播报图标
                Image(systemName: "speaker.wave.2.fill")
                    .font(.system(size: 16))
                    .foregroundColor(MedicalColors.primaryBlue)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.white)
            .cornerRadius(16)
            .shadow(color: Color.black.opacity(0.06), radius: 8, y: 4)
        }
        
        Spacer()
        
        // 打断提示
        Text("点击或说话打断")
            .font(.system(size: 16, weight: .regular))
            .foregroundColor(textGray)
    }
}
```

### 第6步：处理状态切换逻辑

**关键点**：
- 进入语音模式时，`UnifiedChatViewModel.startVoiceMode()` 会自动启动语音识别
- VAD 检测到说话 → `isRecording = true` → 显示识别中状态
- 静默2秒 → 自动发送消息 → `currentRecognition` 清空
- AI 回复到达 → TTS 自动播报 → `isAISpeaking = true` → 显示 AI 播报状态
- AI 播报完成 → `isAISpeaking = false` → 恢复待机状态

**无需额外代码**：这些逻辑已在 `UnifiedChatViewModel` 中实现，只需正确绑定状态即可。

### 第7步：测试和调试

**测试清单**：
```
1. 权限请求
   - 首次点击麦克风，是否弹出麦克风权限请求？
   - 首次点击麦克风，是否弹出语音识别权限请求？
   - 权限被拒绝时，是否显示错误提示？

2. 语音识别
   - 说话时，是否实时显示识别文字？
   - 识别文字是否准确？
   - 静默2秒后，是否自动发送消息？

3. AI 回复
   - AI 回复是否正确显示在气泡中？
   - TTS 是否自动播报？
   - 播报时是否显示 🔊 图标？

4. 打断功能
   - AI 播报时说话，是否立即停止播报？
   - 打断后是否立即开始识别新输入？

5. 退出流程
   - 点击「字幕」按钮，是否直接退出？
   - 点击「关闭」按钮，是否弹出确认框？
   - 确认退出后，是否正确停止语音服务？
```

**调试技巧**：
```swift
// 在关键位置添加日志
print("🎤 [Voice] 当前状态: \(currentState)")
print("🎤 [Voice] isRecording: \(viewModel.isRecording)")
print("🎤 [Voice] isAISpeaking: \(viewModel.isAISpeaking)")
print("🎤 [Voice] currentRecognition: \(viewModel.currentRecognition)")
```

### 第8步：优化和完善

**性能优化**：
- 确保语音识别在后台线程运行
- 避免频繁的 UI 更新导致卡顿

**用户体验优化**：
- 添加触觉反馈（`UIImpactFeedbackGenerator`）
- 优化动画过渡效果
- 添加加载状态指示

**错误处理**：
- 网络断开时的提示
- 语音识别失败时的重试
- TTS 播放失败时的降级处理

## 编码规范

**必须遵守**：
1. 阅读 `ios/xinlingyisheng/IOS_CODING_RULES.md` 中的强制性代码规范
2. 使用项目既有的设计系统（`MedicalColors`、`MedicalTypography` 等）
3. 所有新增的结构体/类/枚举，必须先用 `grep_search` 查阅真实定义
4. Preview 中的数据模型必须与真实结构完全一致
5. 每次修改后必须立即编译（⌘+B），确保无错误和警告

## 验收标准

完成后，语音模式应该：
1. ✅ 点击麦克风进入全屏浅绿色语音模式
2. ✅ 自动开始监听，检测到说话时实时显示识别文字
3. ✅ 静默2秒后自动发送消息到后端
4. ✅ AI 回复自动显示并播报
5. ✅ 用户可随时打断 AI 播报
6. ✅ 点击「字幕」或「关闭」可退出语音模式
7. ✅ 退出时正确清理资源和停止服务

## 参考文档

- 设计文档：`docs/plans/2026-01-18-voice-call-agent-design.md`
- 开发规范：`ios/xinlingyisheng/IOS_CODING_RULES.md`
- API 契约：`docs/API_CONTRACT.md`
- 全局开发规范：`docs/DEVELOPMENT_GUIDELINES.md`

## 注意事项

1. **不要重复造轮子**：`UnifiedChatViewModel` 已经实现了大部分语音功能，只需正确集成
2. **状态驱动UI**：UI 应该完全由 `viewModel` 的状态驱动，不要在 View 中维护业务逻辑
3. **测试驱动开发**：每完成一个功能点，立即测试验证
4. **增量开发**：先让基础功能跑通，再逐步优化体验

## 预期工作量

- 重构 `FullScreenVoiceModeView`：30分钟
- 数据绑定和状态同步：20分钟
- 测试和调试：30分钟
- 优化和完善：20分钟

**总计**：约 1.5-2 小时

---

**开始实施前，请先**：
1. 完整阅读上述所有参考文件
2. 理解现有的语音服务架构
3. 在 Xcode 中运行当前版本，体验现有功能
4. 制定详细的实施计划

祝编码顺利！🚀
