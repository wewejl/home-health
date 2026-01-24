# 达摩院语音方案集成设计

**版本**: V1.0
**设计日期**: 2026-01-24
**状态**: 设计中

---

## 一、方案概述

### 1.1 混合方案架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         iOS 语音服务架构                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│  │    VAD       │   │    ASR       │   │    TTS       │                   │
│  │  (本地 ONNX)  │   │ (系统框架)   │   │ (云端 SDK)   │                   │
│  │              │   │             │   │              │                   │
│  │  FSMN-VAD    │   │  SFSpeech    │   │ CosyVoice   │                   │
│  │  0.5 MB      │   │ Recognizer │   │ iOS SDK     │                   │
│  └──────┬────────┘   └──────┬──────┘   └──────┬──────┘                   │
│         │                    │                   │                     │
│         ▼                    ▼                   ▼                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               统一语音服务 (FunASRVoiceService)               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│  │  │VAD      │  │ASR      │  │TTS      │  │播放器    │               │  │
│  │  │Service  │  │Service  │  │Service  │  │          │               │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              UnifiedChatViewModel (现有)                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、组件详细设计

### 2.1 VAD 服务 - FSMNVADService

#### 模型信息
- **模型**: FSMN-VAD ONNX
- **大小**: ~500KB
- **输入**: [1, dynamic, 400] - Fbank 特征
- **输出**: [1, dynamic, 248] - VAD logits

#### 接口设计
```swift
@MainActor
class FSMNVADService: ObservableObject {
    // MARK: - Published State
    @Published var isDetecting = false
    @Published var speechProbability: Float = 0.0
    @Published var isSpeech: Bool = false

    // MARK: - Callbacks
    var onSpeechStarted: (() -> Void)?
    var onSpeechEnded: (() -> Void)?

    // MARK: - Methods
    func start() async throws
    func stop()
    func processAudioBuffer(_ buffer: AVAudioPCMBuffer) async
}
```

#### 依赖
- ONNX Runtime Swift (需要 Pod)
- 音频特征提取器 (Fbank)

---

### 2.2 ASR 服务 - AppleSpeechService

保持现有实现，无需修改：
- `SFSpeechRecognizer`
- 系统自带，零体积增加
- 支持中文实时识别

---

### 2.3 TTS 服务 - CosyVoiceTTSService

#### SDK 集成
- **SDK**: `nuisdk.framework` (阿里云提供)
- **连接**: WebSocket (wss://dashscope.aliyuncs.com/api-ws/v1/inference)
- **API Key**: 阿里云百炼平台获取

#### 接口设计
```swift
@MainActor
class CosyVoiceTTSService: NSObject, ObservableObject {
    // MARK: - Published State
    @Published var isPlaying = false
    @Published var isConnecting = false

    // MARK: - Methods
    func initialize(apiKey: String) async throws
    func synthesize(
        text: String,
        model: CosyVoiceModel = .v2,
        voice: CosyVoiceVoice = .longxiaochun,
        completion: @escaping (Data?) -> Void
    )
    func stop()

    // MARK: - Callbacks
    var onAudioData: ((Data) -> Void)?
    var onSynthesisComplete: (() -> Void)?
    var onError: ((Error) -> Void)?
}

enum CosyVoiceModel: String {
    case v1 = "cosyvoice-v1"
    case v2 = "cosyvoice-v2"
    case v3Flash = "cosyvoice-v3-flash"
    case v3Plus = "cosyvoice-v3-plus"
}

enum CosyVoiceVoice: String {
    case longxiaochun = "longxiaochun_v2"
    case zhichu = "zhichu_v2"
    case aijia = "aijia_v2"
    // 更多音色...
}
```

---

### 2.4 音频特征提取器 - AudioFeatureExtractor

#### 功能
提取 Fbank/Mel 频谱特征，用于 VAD 和 ASR

```swift
class AudioFeatureExtractor {
    // 配置
    let sampleRate: Double = 16000
    let nMels: Int = 80
    let frameLength: Int = 25  // ms
    let frameShift: Int = 10   // ms

    func extractFbank(from buffer: AVAudioPCMBuffer) -> [Float]
}
```

---

### 2.5 统一语音服务 - FunASRVoiceService

协调所有语音组件的主服务

```swift
@MainActor
class FunASRVoiceService: NSObject, ObservableObject {
    // MARK: - Published State
    @Published var voiceState: FunASRVoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var audioLevel: Float = 0

    // MARK: - Services
    private let vadService: FSMNVADService
    private let asrService: AppleSpeechService  // 复用现有
    private let ttsService: CosyVoiceTTSService

    // MARK: - Callbacks
    var onPartialResult: ((String) -> Void)?
    var onFinalResult: ((String) -> Void)?
    var onVoiceInterruption: (() -> Void)?
    var onAudioData: ((Data) -> Void)?

    // MARK: - Methods
    func start(apiKey: String) async throws
    func stop()
    func toggleMute()
    func interruptAISpeaking()
}

enum FunASRVoiceState {
    case idle
    case listening
    case processing
    case aiSpeaking
}
```

---

## 三、集成步骤

### 3.1 添加依赖

```ruby
# Podfile
pod 'ONNXRuntimeSwift', '~0.2.0'
# 下载 nuiskdk.framework 后手动集成
```

### 3.2 下载 CosyVoice iOS SDK

1. 访问阿里云百炼平台
2. 创建语音合成应用
3. 获取 API Key
4. 下载 iOS SDK (nuisdk.framework)

### 3.3 文件结构

```
ios/xinlingyisheng/xinlingyisheng/Services/FunASR/
├── FunASRVoiceService.swift          # 主服务
├── VAD/
│   ├── FSMNVADService.swift            # FSMN-VAD ONNX 推理
│   └── AudioFeatureExtractor.swift      # Fbank 特征提取
├── TTS/
│   ├── CosyVoiceTTSService.swift       # CosyVoice 云端 TTS
│   └── nuisdk.framework/               # 阿里云 SDK
└── Models/
    ├── FSMNVAD.mlmodel                 # FSMN-VAD Core ML
    └── speech_fsmn_vad_*.onnx        # 原始 ONNX
```

---

## 四、API 密钥配置

### 4.1 阿里云百炼平台

1. 开通阿里云百炼服务
2. 创建语音合成应用
3. 获取 API Key

### 4.2 iOS 配置

```swift
// APIConfig.swift
struct AliyunConfig {
    static let apiKey = "your-api-key-here"  // 从环境变量或配置文件读取
    static let ttsEndpoint = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
}
```

---

## 五、性能优化

### 5.1 体积优化

| 组件 | 大小 |
|------|------|
| FSMN-VAD ONNX | ~500KB |
| nuisdk.framework | ~5MB |
| 总增加 | <10MB |

### 5.2 内存优化

- VAD 模型按需加载
- 音频缓冲区复用
- 流式处理减少内存占用

### 5.3 网络优化

- TTS 使用流式回调
- 音频数据边收边播
- 网络断线缓存策略

---

## 六、错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| API Key 无效 | 弹窗引导重新配置 |
| 网络断开 | 自动重连 + 降级到本地 TTS |
| VAD 模型加载失败 | 降级到能量法 VAD |
| TTS 服务超时 | 重试 3 次 |

---

## 七、测试计划

### 7.1 单元测试

- [ ] FSMNVADService 推理测试
- [ ] AudioFeatureExtractor 特征提取测试
- [ ] CosyVoiceTTSService API 调用测试

### 7.2 集成测试

- [ ] 完整语音通话流程测试
- [ ] 打断场景测试
- [ ] 网络异常场景测试

### 7.3 性能测试

- [ ] VAD 延迟测试
- [ ] ASR 实时性测试
- [ ] TTS 首字延迟测试

---

## 八、后续优化

- [ ] 支持离线 ASR (如用户需求)
- [ ] 自定义音色复刻
- [ ] 多语言支持
- [ ] 情感语音合成

---

**文档维护者**: 项目团队
**最后更新**: 2026-01-24
