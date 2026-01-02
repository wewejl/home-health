# iOS AI诊室改造完成说明

> **状态更新 (2025-12-30)**: 以下改造已在 iOS 项目中实施完成。

## 改造概览

本次改造使 iOS 客户端适配后端新的"单一请求体 + AI 驱动评估"接口，主要涉及以下文件：

| 文件 | 改动内容 |
|------|----------|
| `Models/DiagnosisModels.swift` | 新增 AI 评估字段和统一请求体模型 |
| `Services/APIService.swift` | 添加统一问诊接口方法 |
| `ViewModels/DiagnosisViewModel.swift` | 适配新字段、构建历史消息 |
| `Views/AIDiagnosisView.swift` | 新增 AI 评估信息卡片组件 |

---

## 1. 数据模型改动 (`DiagnosisModels.swift`)

### 1.1 响应模型新增字段

```swift
// AI评估字段（新增）
let should_diagnose: Bool?   // AI 判断是否应进入诊断
let confidence: Int?         // 诊断置信度 (0-100)
let missing_info: [String]?  // 缺失的关键信息列表

var shouldDiagnose: Bool { should_diagnose ?? false }
```

### 1.2 统一请求体模型

```swift
struct UnifiedDiagnosisRequest: Encodable {
    let consultation_id: String
    let force_conclude: Bool
    let history: [HistoryMessage]
    let current_input: CurrentInput
    
    struct HistoryMessage: Encodable {
        let role: String  // "user" or "assistant"
        let message: String
        let timestamp: String  // ISO8601 格式
    }
    
    struct CurrentInput: Encodable {
        let message: String
    }
}
```

---

## 2. 网络层改动 (`APIService.swift`)

### 2.1 新增统一问诊接口

```swift
/// 统一问诊接口（新版，携带完整历史）
func sendDiagnosisWithHistory(
    consultationId: String,
    history: [UnifiedDiagnosisRequest.HistoryMessage],
    currentMessage: String,
    forceConclude: Bool = false
) async throws -> DiagnosisResponseModel
```

- 每次发送消息都携带最近 10 条对话历史
- 后端可根据历史重建状态
- 旧版 `continueDiagnosis` 接口保留兼容

---

## 3. ViewModel 改动 (`DiagnosisViewModel.swift`)

### 3.1 新增 AI 评估状态

```swift
// AI评估字段（新增）
@Published var shouldDiagnose: Bool = false
@Published var confidence: Int = 0
@Published var missingInfo: [String] = []

// 计算属性
var confidenceText: String { "置信度 \(confidence)%" }
var hasMissingInfo: Bool { !missingInfo.isEmpty }
```

### 3.2 构建历史消息方法

```swift
private func buildHistoryMessages() -> [UnifiedDiagnosisRequest.HistoryMessage] {
    let recentMessages = messages.suffix(10)  // 取最近 10 条
    return recentMessages.map { msg in
        UnifiedDiagnosisRequest.HistoryMessage(
            role: msg.isFromUser ? "user" : "assistant",
            message: msg.content,
            timestamp: ISO8601DateFormatter().string(from: msg.timestamp)
        )
    }
}
```

### 3.3 发送消息改用新接口

`sendMessage()` 方法现在使用 `sendDiagnosisWithHistory()` 携带完整历史。

---

## 4. UI 改动 (`AIDiagnosisView.swift`)

### 4.1 新增 AIEvaluationCard 组件

在问诊过程中展示：
- **进度** (progress): 问诊完成度百分比
- **置信度** (confidence): AI 诊断置信度，根据数值变色
- **缺失信息** (missingInfo): 可展开查看 AI 还需了解的信息

```swift
struct AIEvaluationCard: View {
    let progress: Int
    let confidence: Int
    let missingInfo: [String]
    
    @State private var isExpanded = false
    // ...
}
```

### 4.2 视图集成位置

在流程指示器下方、风险警告上方显示，仅在问诊未完成时展示。

---

## 5. 功能对照

| 后端新功能 | iOS 对应实现 |
|-----------|-------------|
| 统一请求体 | `UnifiedDiagnosisRequest` + `sendDiagnosisWithHistory()` |
| AI 评估 progress | `viewModel.progress` + `AIEvaluationCard` |
| AI 评估 should_diagnose | `viewModel.shouldDiagnose` |
| AI 评估 confidence | `viewModel.confidence` + 颜色变化展示 |
| AI 评估 missing_info | `viewModel.missingInfo` + 可展开列表 |
| 首轮动态选项 | 已支持（`quick_options` 由后端动态返回） |
| force_conclude | 已支持（`concludeDiagnosis()` 方法） |

---

## 6. 测试建议

1. **多轮问诊**：验证历史消息正确携带，进度和置信度实时更新
2. **force_conclude**：点击"直接出结论"按钮，确认立即生成诊断
3. **首轮选项**：多次进入问诊，验证快捷选项随主诉动态变化
4. **缺失信息展示**：验证 AI 评估卡片展开/收起功能正常
5. **网络异常**：验证 fallback 和错误提示正常

---

## 7. 兼容性说明

- 旧版 `continueDiagnosis()` 接口保留，确保向后兼容
- 后端字段采用可选类型解码，兼容旧版响应
- UI 组件仅在有数据时显示，不影响旧版流程

如有问题，可参考后端 `README.md` 中的接口说明。
