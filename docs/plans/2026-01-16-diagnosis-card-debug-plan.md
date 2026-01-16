# 诊断卡片显示问题调试方案

**日期**: 2026-01-16  
**版本**: V1.0  
**状态**: 待实施

---

## 问题描述

用户反馈：
1. **中间建议不显示** - 建议和普通消息混在一起
2. **诊断卡片不显示** - 没有看到最终诊断的展示

经过代码审查发现：
- 中间建议：后端数据正常，但 iOS 缺少 UI 组件显示
- 诊断卡片：数据流完整，但需要验证 Agent 是否真的调用了工具

---

## 调试目标

**验证诊断卡片数据流的每个环节**：

1. Agent 是否调用 `generate_structured_diagnosis` 工具
2. `tool_node` 是否正确更新 `state["diagnosis_card"]`
3. `build_response` 是否正确序列化数据
4. API 响应是否包含 `diagnosis_card` 字段
5. iOS 前端是否正确解析和存储数据
6. UI 条件判断是否正确触发显示

---

## 调试方案

### 阶段 1: 后端日志验证

#### 1.1 验证 Agent 工具调用

**文件**: `backend/app/services/dermatology/react_agent.py`

**位置**: `tool_node` 函数开始处 (约 118 行)

**添加日志**:
```python
def tool_node(state: DermaReActState) -> Dict[str, Any]:
    """工具节点：执行工具调用并更新状态"""
    outputs = []
    updates = {}
    last_message = state["messages"][-1]
    
    # === 新增调试日志 ===
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[DEBUG] tool_node 收到工具调用: {len(last_message.tool_calls)} 个")
        for tool_call in last_message.tool_calls:
            print(f"[DEBUG] 工具名称: {tool_call['name']}")
            print(f"[DEBUG] 工具参数: {tool_call['args']}")
    # === 日志结束 ===
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 执行工具
            if tool_name in tools_by_name:
                result = tools_by_name[tool_name].invoke(tool_args)
                
                # === 新增调试日志 ===
                if tool_name == "generate_structured_diagnosis":
                    print(f"[DEBUG] generate_structured_diagnosis 返回结果:")
                    print(f"[DEBUG] - summary: {result.get('summary', 'N/A')}")
                    print(f"[DEBUG] - conditions: {len(result.get('conditions', []))} 个")
                    print(f"[DEBUG] - risk_level: {result.get('risk_level', 'N/A')}")
                # === 日志结束 ===
                
                # 根据工具类型更新 state
                if tool_name == "retrieve_derma_knowledge":
                    ...
```

#### 1.2 验证 state 更新

**位置**: `tool_node` 函数 `generate_structured_diagnosis` 分支 (约 144 行)

**添加日志**:
```python
elif tool_name == "generate_structured_diagnosis":
    # 更新诊断卡
    if isinstance(result, dict):
        updates["diagnosis_card"] = result
        
        # === 新增调试日志 ===
        print(f"[DEBUG] 更新 state['diagnosis_card']:")
        print(f"[DEBUG] - 字段数量: {len(result.keys())}")
        print(f"[DEBUG] - 包含字段: {list(result.keys())}")
        # === 日志结束 ===
        
        # 更新推理步骤
        if "reasoning_steps" in result:
            ...
```

#### 1.3 验证 API 响应

**文件**: `backend/app/routes/derma.py`

**位置**: `build_response` 函数诊断卡片处理部分 (约 223 行)

**添加日志**:
```python
# 添加诊断卡
if state.get("diagnosis_card"):
    card = state["diagnosis_card"]
    
    # === 新增调试日志 ===
    print(f"[DEBUG] build_response 处理 diagnosis_card:")
    print(f"[DEBUG] - summary: {card.get('summary', 'N/A')}")
    print(f"[DEBUG] - conditions 数量: {len(card.get('conditions', []))}")
    # === 日志结束 ===
    
    response_data["diagnosis_card"] = DermaDiagnosisCardSchema(
        summary=card.get("summary", ""),
        ...
    )
else:
    # === 新增调试日志 ===
    print(f"[DEBUG] build_response: state 中没有 diagnosis_card")
    print(f"[DEBUG] state 包含的字段: {list(state.keys())}")
    # === 日志结束 ===
```

---

### 阶段 2: 前端日志验证

#### 2.1 验证 API 响应接收

**文件**: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`

**位置**: `handleComplete` 函数 (约 482 行)

**添加日志**:
```swift
// 更新诊断展示增强字段
if let history = response.adviceHistory {
    adviceHistory = history
    print("[DEBUG] 收到 adviceHistory: \(history.count) 条")
}
if let card = response.diagnosisCard {
    diagnosisCard = card
    print("[DEBUG] 收到 diagnosisCard:")
    print("[DEBUG] - summary: \(card.summary)")
    print("[DEBUG] - conditions: \(card.conditions.count) 个")
    print("[DEBUG] - risk_level: \(card.riskLevel)")
} else {
    print("[DEBUG] API 响应中没有 diagnosisCard")
}
if let refs = response.knowledgeRefs {
    knowledgeRefs = refs
    print("[DEBUG] 收到 knowledgeRefs: \(refs.count) 条")
}
if let steps = response.reasoningSteps {
    reasoningSteps = steps
    print("[DEBUG] 收到 reasoningSteps: \(steps.count) 步")
}
```

#### 2.2 验证 UI 渲染条件

**文件**: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`

**位置**: 诊断卡片显示部分 (约 179 行)

**添加日志**:
```swift
// 诊断卡片
if let diagnosisCard = viewModel.diagnosisCard {
    DiagnosisSummaryCard(
        card: diagnosisCard,
        onViewDossier: { viewDossier() }
    )
    .padding(.horizontal, MedicalSpacing.lg)
    .transition(.move(edge: .bottom).combined(with: .opacity))
    .onAppear {
        print("[DEBUG] DiagnosisSummaryCard 已渲染")
        print("[DEBUG] - summary: \(diagnosisCard.summary)")
    }
} else {
    // === 新增调试日志 ===
    Text("诊断卡片未显示 (diagnosisCard = nil)")
        .font(.caption)
        .foregroundColor(.red)
        .padding()
        .onAppear {
            print("[DEBUG] diagnosisCard 为 nil，未渲染卡片")
            print("[DEBUG] viewModel.messages.count: \(viewModel.messages.count)")
        }
    // === 日志结束 ===
}
```

---

### 阶段 3: 测试验证

#### 3.1 测试场景

**完整对话流程**:
1. 启动 iOS 应用，进入皮肤科问诊
2. 用户: "我手臂上有红疹"
3. AI: 询问症状
4. 用户: "很痒，还有点脱皮"
5. AI: 询问持续时间
6. 用户: "大概三天了"
7. **观察**: Agent 是否调用 `generate_structured_diagnosis`

#### 3.2 预期日志输出

**后端日志** (按顺序):
```
[DEBUG] tool_node 收到工具调用: 1 个
[DEBUG] 工具名称: retrieve_derma_knowledge
[DEBUG] 工具参数: {'symptoms': ['红疹', '瘙痒', '脱皮'], 'location': '手臂'}

[DEBUG] tool_node 收到工具调用: 1 个
[DEBUG] 工具名称: generate_structured_diagnosis
[DEBUG] 工具参数: {'symptoms': ['红疹', '瘙痒', '脱皮'], 'location': '手臂', 'duration': '三天'}
[DEBUG] generate_structured_diagnosis 返回结果:
[DEBUG] - summary: 手臂红疹伴瘙痒脱皮
[DEBUG] - conditions: 2 个
[DEBUG] - risk_level: low

[DEBUG] 更新 state['diagnosis_card']:
[DEBUG] - 字段数量: 8
[DEBUG] - 包含字段: ['summary', 'conditions', 'risk_level', ...]

[DEBUG] build_response 处理 diagnosis_card:
[DEBUG] - summary: 手臂红疹伴瘙痒脱皮
[DEBUG] - conditions 数量: 2
```

**iOS 日志**:
```
[DEBUG] 收到 diagnosisCard:
[DEBUG] - summary: 手臂红疹伴瘙痒脱皮
[DEBUG] - conditions: 2 个
[DEBUG] - risk_level: low

[DEBUG] DiagnosisSummaryCard 已渲染
[DEBUG] - summary: 手臂红疹伴瘙痒脱皮
```

#### 3.3 问题定位

**如果后端没有日志**:
- Agent 没有调用工具
- 检查 System Prompt 是否清晰
- 检查信息收集是否完整

**如果后端有日志，但 state 没更新**:
- `tool_node` 逻辑问题
- 检查 `isinstance(result, dict)` 条件

**如果 state 更新了，但 API 响应没有**:
- `build_response` 序列化问题
- 检查 Schema 定义

**如果 API 有响应，但 iOS 没收到**:
- 网络问题或解析问题
- 检查 `UnifiedMessageResponse` 解码

**如果 iOS 收到了，但 UI 没显示**:
- `diagnosisCard` 赋值问题
- UI 条件判断问题

---

## 实施步骤

### Step 1: 添加后端日志
- [ ] 修改 `react_agent.py` 添加 `tool_node` 日志
- [ ] 修改 `derma.py` 添加 `build_response` 日志
- [ ] 重启后端服务

### Step 2: 添加前端日志
- [ ] 修改 `UnifiedChatViewModel.swift` 添加接收日志
- [ ] 修改 `ModernConsultationView.swift` 添加渲染日志
- [ ] 重新编译 iOS 应用

### Step 3: 执行测试
- [ ] 启动后端，观察控制台
- [ ] 启动 iOS，观察 Xcode 控制台
- [ ] 执行完整对话流程
- [ ] 记录所有日志输出

### Step 4: 分析结果
- [ ] 对比预期日志和实际日志
- [ ] 定位数据流断点
- [ ] 确定修复方向

---

## 可能的修复方案

### 场景 1: Agent 不调用工具

**原因**: System Prompt 不够清晰或触发条件不明确

**修复**:
```python
# 在 DERMA_REACT_PROMPT 中强化说明
## 诊断工作流（重要）

**必须执行**: 当收集完以下信息后，立即按顺序调用工具：
1. 主诉（chief_complaint）
2. 部位（skin_location）
3. 症状列表（symptoms，至少2个）
4. 持续时间（duration）

**标准流程**:
步骤1: 调用 retrieve_derma_knowledge(symptoms=症状列表, location=部位)
步骤2: 调用 generate_structured_diagnosis(
    symptoms=症状列表,
    location=部位,
    duration=持续时间,
    knowledge_refs=步骤1的结果
)

**示例**:
用户: "我手臂有红疹，很痒，三天了"
→ 收集到: 部位=手臂, 症状=[红疹,瘙痒], 持续时间=三天
→ 立即调用 retrieve_derma_knowledge
→ 立即调用 generate_structured_diagnosis
```

### 场景 2: 数据流断裂

**原因**: 某个环节的数据转换失败

**修复**: 根据日志定位具体断点，修复对应代码

### 场景 3: UI 条件判断问题

**原因**: `diagnosisCard` 为 `nil` 但数据已到达

**修复**: 检查 `handleComplete` 中的赋值逻辑

---

## 预期成果

完成调试后，应该能够：
1. 明确知道 Agent 是否调用了诊断工具
2. 定位数据流的断点位置
3. 确定具体的修复方案
4. 为后续实施提供清晰的方向

---

## 后续工作

根据调试结果：
- 如果 Agent 不调用工具 → 优化 System Prompt
- 如果数据流断裂 → 修复对应环节
- 如果 UI 不显示 → 修复前端逻辑
- 同时实施中间建议卡片的 UI 组件开发

---

**文档维护者**: 项目团队  
**最后更新**: 2026-01-16  
**下次审查**: 调试完成后
