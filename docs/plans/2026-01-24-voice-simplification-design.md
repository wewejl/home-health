# 语音通话架构简化设计

**日期**: 2026-01-24
**状态**: 设计完成，待实施

## 1. 问题背景

当前语音通话架构过于复杂：
- iOS 端有 5 个独立服务类（`HybridVoiceService`、`BackendVoiceASRService`、`BackendVoiceTTSService`、`AudioEnergyVADService` 等）
- 后端通过 WebSocket 代理转发到阿里云
- 多层代理导致延迟和复杂性

## 2. 核心设计原则

**极简原则**：ASR 持续监听 + TTS 流式播放 + 有结果就停

```
┌─────────────────────────────────────────────────────────┐
│  iOS 端                                                  │
│  ┌──────────┐    ┌────────────┐    ┌───────────────┐   │
│  │ ASR服务   │───▶│ 持续录音    │    │  TTS播放器    │   │
│  │ (WebSocket)  │  │ (16kHz PCM)  │  │ (收到就播放)   │   │
│  └──────────┘    └────────────┘    └───────────────┘   │
│       │                                    ▲            │
│       │  收到任何识别结果                   │            │
│       └────────────────────────────────────┴──── stop   │
└─────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌──────────────────┐              ┌──────────────────┐
│ 后端 /ws/voice/asr│              │ 后端 /ws/voice/tts│
│   (转发 FunASR)   │              │ (转发 Qwen TTS)  │
└──────────────────┘              └──────────────────┘
```

## 3. 后端设计

### 3.1 ASR 端点

**保持现有 `/ws/voice/asr`，确保低延迟配置**：

```python
"parameters": {
    "format": "pcm",
    "sample_rate": 16000,
    "semantic_punctuation_enabled": False,  # VAD 断句，低延迟
    "max_sentence_silence": 1300
}
```

**返回事件**：
```json
{"event": "asr_partial", "text": "你好"}      // 中间结果 - 立即发送
{"event": "asr_final", "text": "你好医生"}    // 最终结果
```

### 3.2 TTS 端点

**保持现有 `/ws/voice/tts` 长连接模式**

### 3.3 后端改动

- 确认 `semantic_punctuation_enabled: False`
- 确保 `asr_partial` 事件立即转发，不等待 `asr_final`

## 4. iOS 端设计

### 4.1 删除文件

```
ios/xinlingyisheng/xinlingyisheng/Services/Voice/
├── HybridVoiceService.swift          [删除]
├── BackendVoiceASRService.swift      [删除]
├── BackendVoiceTTSService.swift      [删除]
├── AudioEnergyVADService.swift       [删除]
├── BackendVoiceConfig.swift          [删除]
├── BackendVoiceASRConfig.swift       [删除]
├── BackendVoiceTTSConfig.swift       [删除]
└── AudioEnergyVADConfig.swift        [删除]
```

### 4.2 新增文件

**`ios/xinlingyisheng/xinlingyisheng/Services/Voice/SimpleVoiceService.swift`**

```swift
class SimpleVoiceService: NSObject, ObservableObject {
    // 状态
    @Published var isPlayingTTS = false
    @Published private(set) var asrText = ""

    // ASR
    private var asrWebSocket: URLSessionWebSocketTask?
    private let audioEngine = AVAudioEngine()

    // TTS
    private var ttsWebSocket: URLSessionWebSocketTask?
    private var audioPlayer: AVAudioPlayerNode?
    private let audioFormat = AVAudioFormat(
        commonFormat: .pcmFormatInt16,
        sampleRate: 24000,
        channels: 1,
        interleaved: false
    )!

    // 核心逻辑：收到 ASR 结果就停止 TTS
    func onASRResult(_ text: String) {
        stopTTS()
        asrText = text
    }

    func stopTTS() {
        audioPlayer?.stop()
        isPlayingTTS = false
    }
}
```

## 5. 数据流与时序

```
时间线 →

用户端                    后端                    阿里云
  │                       │                        │
  ├─ 1. 连接 ASR WebSocket ─▶│                        │
  │                       ├─ 连接 FunASR ───────────▶│
  │                       │◀─ task-started ─────────┤
  │◀─ asr_ready ──────────┤                        │
  │                       │                        │
  ├─ 2. 连接 TTS WebSocket ─▶│                        │
  │                       ├─ 连接 Qwen TTS ─────────▶│
  │◀─ tts_ready ───────────┤                        │
  │                       │                        │
  ├─ 3. 发送 "我头痛" ─────▶│                        │
  │                       ├─ 发送给 AI ────────────▶│
  │                       │◀─ AI 回复 "具体哪痛？" ─┤
  │◀──────────────────── TTS 音频流 ────────────────┤
  │  (开始播放)             │                        │
  │                       │                        │
  ├─ 4. 同时持续发送录音 ──▶│◀───────────────────────┤
  │                       │                        │
  │◀─ asr_partial: "左边" ─┤  (用户开始说话)        │
  │  【立即停止 TTS 播放】  │                        │
  │                       │                        │
```

**关键时序保证**：
1. ASR 和 TTS 并行工作，不互相阻塞
2. ASR 持续发送音频流，不管 TTS 是否在播放
3. 收到 `asr_partial` 就停止 TTS，不等 `asr_final`

## 6. 状态管理

```swift
enum VoiceState {
    case idle           // 空闲
    case listening      // 正在听（ASR 持续工作）
    case speaking       // 正在说（TTS 播放中）
    case interrupted    // 被打断（用户说话）
}
```

## 7. 错误处理

| 情况 | 处理方式 |
|------|----------|
| ASR 连接失败 | 提示用户，允许重连 |
| TTS 连接失败 | 仅显示文字回复，不播放语音 |
| ASR 断线 | 自动重连，重连期间暂停对话 |
| TTS 断线 | 仅显示文字 |
| TTS 播放时用户说话 | 立即停止 TTS，ASR 结果继续处理 |
| 静音/噪音 | ASR 返回空 text 不触发停止 |

## 8. 实施检查清单

### 后端（改动很小）
- [ ] 确认 `semantic_punctuation_enabled: False`
- [ ] 确认 `asr_partial` 事件立即转发

### iOS（需要重构）
- [ ] 删除旧的语音服务类（4-5个文件）
- [ ] 创建 `SimpleVoiceService.swift`
- [ ] ASR WebSocket 持续连接，发送录音
- [ ] TTS WebSocket 长连接，接收音频流
- [ ] 收到 ASR 结果 → `stopTTS()`
- [ ] 更新 `ModernConsultationView` 使用新服务

### 测试
- [ ] 正常对话流程
- [ ] 打断 TTS 播放
- [ ] 网络断线重连
- [ ] 静音场景
