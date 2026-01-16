# 诊断展示增强设计方案

**版本**: V1.0  
**日期**: 2026-01-16  
**状态**: 待实施

---

## 目标

让皮肤科 ReAct Agent 实现"查资料 → 推理 → 结构化诊断"的完整流程，前端可展示：
1. 中间建议（边问边给的初步建议）
2. 引用证据（检索到的医学知识）
3. 最终诊断卡（结构化诊断结果）

---

## 一、后端设计

### 1.1 状态扩展（react_state.py）

在 `DermaReActState` 中新增字段：

```python
class DermaReActState(TypedDict):
    # ... 现有字段 ...
    
    # === 新增：中间建议历史 ===
    advice_history: List[dict]  # [{id, title, content, evidence, timestamp}]
    
    # === 新增：诊断卡 ===
    diagnosis_card: Optional[dict]  # 结构化诊断结果
    
    # === 新增：推理步骤 ===
    reasoning_steps: List[str]  # ["收集症状", "检索文献", "鉴别诊断"]
```

### 1.2 Schema 扩展（schemas/derma.py）

```python
class DermaAdviceSchema(BaseModel):
    """中间建议"""
    id: str
    title: str
    content: str
    evidence: List[str] = []
    timestamp: str

class DermaKnowledgeRefSchema(BaseModel):
    """知识引用"""
    id: str
    title: str
    snippet: str
    source: Optional[str] = None
    link: Optional[str] = None

class DermaConditionSchema(BaseModel):
    """鉴别诊断条目"""
    name: str
    confidence: float
    rationale: List[str] = []

class DermaDiagnosisCardSchema(BaseModel):
    """诊断卡"""
    summary: str
    conditions: List[DermaConditionSchema]
    risk_level: Literal["low", "medium", "high", "emergency"]
    need_offline_visit: bool
    urgency: Optional[str] = None
    care_plan: List[str] = []
    references: List[DermaKnowledgeRefSchema] = []
    reasoning_steps: List[str] = []

# DermaResponse 新增字段
class DermaResponse(BaseModel):
    # ... 现有字段 ...
    advice_history: Optional[List[DermaAdviceSchema]] = None
    diagnosis_card: Optional[DermaDiagnosisCardSchema] = None
    knowledge_refs: Optional[List[DermaKnowledgeRefSchema]] = None
    reasoning_steps: Optional[List[str]] = None
```

### 1.3 检索工具（react_tools.py）

新增 `retrieve_derma_knowledge` 工具：

```python
@tool
def retrieve_derma_knowledge(
    symptoms: List[str],
    location: str,
    query: str = ""
) -> List[dict]:
    """
    检索皮肤科医学知识库
    
    Args:
        symptoms: 症状列表
        location: 皮损部位
        query: 补充查询词
    
    Returns:
        [{id, title, snippet, source, link}]
    """
    # 实现方式：
    # 1. 向量检索（如 Chroma/FAISS）
    # 2. BM25 关键词匹配
    # 3. 或调用外部 API
    pass
```

### 1.4 诊断工具升级（react_tools.py）

修改 `generate_diagnosis` 输出结构化 JSON：

```python
@tool
def generate_diagnosis(
    symptoms: List[str],
    location: str,
    duration: str,
    knowledge_refs: List[dict] = [],
    additional_info: str = ""
) -> dict:
    """生成结构化诊断"""
    # 使用 LLM 结构化输出
    llm = LLMProvider.get_llm()
    structured_llm = llm.with_structured_output(DiagnosisOutput)
    
    # 构建 prompt，包含检索到的知识
    prompt = f"""根据以下信息给出诊断：
    症状：{symptoms}
    部位：{location}
    持续时间：{duration}
    参考资料：{knowledge_refs}
    
    输出格式：
    - summary: 症状总结
    - conditions: 鉴别诊断（含置信度和依据）
    - risk_level: 风险等级
    - care_plan: 护理建议
    - reasoning_steps: 推理步骤
    """
    
    result = structured_llm.invoke(prompt)
    return result.model_dump()
```

### 1.5 API 响应构建（routes/derma.py）

`build_response()` 透传新字段：

```python
def build_response(state: dict) -> DermaResponse:
    response_data = {
        # ... 现有字段 ...
        "advice_history": state.get("advice_history"),
        "diagnosis_card": state.get("diagnosis_card"),
        "knowledge_refs": state.get("knowledge_refs"),
        "reasoning_steps": state.get("reasoning_steps"),
    }
    return DermaResponse(**response_data)
```

---

## 二、iOS 设计

### 2.1 模型扩展（UnifiedChatModels.swift）

```swift
// 中间建议
struct AdviceEntry: Codable, Identifiable {
    let id: String
    let title: String
    let content: String
    let evidence: [String]
    let timestamp: String
}

// 知识引用
struct KnowledgeRef: Codable, Identifiable {
    let id: String
    let title: String
    let snippet: String
    let source: String?
    let link: String?
}

// 鉴别诊断条目
struct DiagnosisCondition: Codable {
    let name: String
    let confidence: Double
    let rationale: [String]
}

// 诊断卡
struct DiagnosisCard: Codable {
    let summary: String
    let conditions: [DiagnosisCondition]
    let riskLevel: String
    let needOfflineVisit: Bool
    let urgency: String?
    let carePlan: [String]
    let references: [KnowledgeRef]
    let reasoningSteps: [String]
}

// 扩展 UnifiedMessageResponse
struct UnifiedMessageResponse: Codable {
    // ... 现有字段 ...
    let adviceHistory: [AdviceEntry]?
    let diagnosisCard: DiagnosisCard?
    let knowledgeRefs: [KnowledgeRef]?
    let reasoningSteps: [String]?
}
```

### 2.2 UI 组件

#### AdviceCardView（中间建议卡）

```swift
struct AdviceCardView: View {
    let advice: AdviceEntry
    let onAccept: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // 标题 + 标签
            HStack {
                Text("💡 \(advice.title)")
                    .font(.system(size: 14, weight: .semibold))
                Spacer()
                Text("初步建议")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(4)
            }
            
            // 内容
            Text(advice.content)
                .font(.system(size: 14))
            
            // 依据标签
            if !advice.evidence.isEmpty {
                FlowLayout(spacing: 4) {
                    ForEach(advice.evidence, id: \.self) { e in
                        Text(e)
                            .font(.caption)
                            .padding(4)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }
            
            // 采纳按钮
            Button("好的，知道了") { onAccept() }
        }
        .padding()
        .background(Color.blue.opacity(0.05))
        .cornerRadius(12)
    }
}
```

#### EvidenceListView（证据列表）

```swift
struct EvidenceListView: View {
    let refs: [KnowledgeRef]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("📚 参考资料")
                .font(.system(size: 14, weight: .semibold))
            
            ForEach(refs) { ref in
                VStack(alignment: .leading, spacing: 4) {
                    Text(ref.title)
                        .font(.system(size: 13, weight: .medium))
                    Text(ref.snippet)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                    if let source = ref.source {
                        Text("来源: \(source)")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
                .padding(8)
                .background(Color.gray.opacity(0.05))
                .cornerRadius(8)
            }
        }
    }
}
```

#### DiagnosisSummaryCard（诊断卡）

```swift
struct DiagnosisSummaryCard: View {
    let card: DiagnosisCard
    let onViewDossier: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 顶部：风险徽章
            HStack {
                RiskBadge(level: card.riskLevel)
                Spacer()
                if card.needOfflineVisit {
                    Text("⚠️ 建议线下就诊")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }
            
            // 症状总结
            Text(card.summary)
                .font(.system(size: 15))
            
            // 鉴别诊断
            VStack(alignment: .leading, spacing: 8) {
                Text("🔍 可能的诊断")
                    .font(.system(size: 14, weight: .semibold))
                
                ForEach(card.conditions, id: \.name) { condition in
                    ConditionRow(condition: condition)
                }
            }
            
            // 推理步骤
            if !card.reasoningSteps.isEmpty {
                ReasoningTimeline(steps: card.reasoningSteps)
            }
            
            // 护理建议
            if !card.carePlan.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("💊 护理建议")
                        .font(.system(size: 14, weight: .semibold))
                    ForEach(card.carePlan, id: \.self) { tip in
                        Text("• \(tip)")
                            .font(.system(size: 13))
                    }
                }
            }
            
            // 引用证据（可折叠）
            if !card.references.isEmpty {
                DisclosureGroup("📚 引用证据 (\(card.references.count))") {
                    EvidenceListView(refs: card.references)
                }
            }
            
            // CTA
            Button(action: onViewDossier) {
                Text("查看/生成病历")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(16)
        .shadow(radius: 4)
    }
}
```

### 2.3 ViewModel 扩展

```swift
@MainActor
class UnifiedChatViewModel: ObservableObject {
    // ... 现有属性 ...
    
    @Published var adviceHistory: [AdviceEntry] = []
    @Published var diagnosisCard: DiagnosisCard?
    @Published var knowledgeRefs: [KnowledgeRef] = []
    
    func handleResponse(_ response: UnifiedMessageResponse) {
        // 更新中间建议
        if let history = response.adviceHistory {
            adviceHistory = history
        }
        
        // 更新诊断卡
        if let card = response.diagnosisCard {
            diagnosisCard = card
        }
        
        // 更新知识引用
        if let refs = response.knowledgeRefs {
            knowledgeRefs = refs
        }
    }
}
```

### 2.4 聊天界面集成

在 `ModernConsultationView` 中：

```swift
// 消息列表后添加诊断卡
if let card = viewModel.diagnosisCard {
    DiagnosisSummaryCard(
        card: card,
        onViewDossier: { viewDossier() }
    )
    .padding(.horizontal)
}

// 在 AI 消息后插入中间建议
ForEach(viewModel.adviceHistory) { advice in
    AdviceCardView(
        advice: advice,
        onAccept: { /* 发送确认 */ }
    )
}
```

---

## 三、交互流程

```
用户输入症状
    ↓
Agent 问诊 + 给出初步建议 → advice_history 追加
    ↓
用户继续描述
    ↓
Agent 判断信息足够 → 调用 retrieve_derma_knowledge
    ↓
前端收到 knowledge_refs → 显示"正在查阅资料..."
    ↓
Agent 调用 generate_diagnosis（含检索结果）
    ↓
返回 diagnosis_card → 前端渲染诊断卡
```

---

## 四、实施步骤

1. **后端 Phase 1**（2天）
   - 扩展 `DermaReActState` 状态字段
   - 扩展 `DermaResponse` Schema
   - 修改 `build_response()` 透传新字段

2. **后端 Phase 2**（3天）
   - 实现 `retrieve_derma_knowledge` 检索工具
   - 升级 `generate_diagnosis` 输出结构化 JSON
   - 添加单元测试

3. **iOS Phase 1**（2天）
   - 扩展 `UnifiedMessageResponse` 模型
   - 实现 `AdviceCardView`、`EvidenceListView`

4. **iOS Phase 2**（2天）
   - 实现 `DiagnosisSummaryCard`
   - 集成到 `ModernConsultationView`
   - ViewModel 状态管理

5. **联调测试**（2天）
   - 端到端测试
   - UI 调优
   - 更新 API 文档

---

## 五、风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 知识库数据不足 | 初期用 LLM 自身知识 + mock 引用 |
| LLM 结构化输出不稳定 | 添加 fallback 默认值 |
| iOS 解析失败 | 所有新字段设为 Optional |

---

## 六、文档更新

- [ ] 更新 `docs/API_CONTRACT.md`
- [ ] 更新 `docs/IOS_DEVELOPMENT_GUIDE.md`
- [ ] 更新 `CHANGELOG.md`
