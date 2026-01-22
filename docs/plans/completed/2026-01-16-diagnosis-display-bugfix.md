# 诊断展示功能缺陷修复方案

**日期**: 2026-01-16
**版本**: V1.0
**状态**: ✅ 已完成

---

## 问题概述

在完成诊断展示增强功能后，发现两个关键问题：

### 问题 1：快捷回答交互不符合预期
**现象**：点击快捷回答后直接发送消息  
**预期**：点击后填入输入框，支持多选，发送后消失

### 问题 2：诊断卡片未显示
**现象**：对话过程中，中间建议卡片和诊断卡片始终不显示  
**预期**：Agent 应在适当时机生成并展示这些卡片

---

## 根因分析

### 问题 1 根因

**当前实现** (`ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift:608-614`):
```swift
Button(action: {
    // 发送快捷选项作为用户消息
    NotificationCenter.default.post(
        name: NSNotification.Name("SendQuickOption"),
        object: nil,
        userInfo: ["text": option.text]
    )
})
```

**问题**：
- 点击后通过 `NotificationCenter` 立即触发 `sendMessage`
- 无法多选，点击即发送
- 快捷选项绑定在消息对象上，不会自动消失

---

### 问题 2 根因

经过全面代码审查，确认了三个关键缺陷：

#### 缺陷 1：System Prompt 缺少新工具说明

**文件**: `backend/app/services/dermatology/react_agent.py:16-41`

**当前 Prompt**:
```python
DERMA_REACT_PROMPT = """你是一位经验丰富的皮肤科专家医生...

## 可用工具
- analyze_skin_image: 分析皮肤图片
- generate_diagnosis: 生成诊断建议
"""
```

**问题**：
- 只提到了旧的两个工具
- **没有提到** `retrieve_derma_knowledge` 和 `generate_structured_diagnosis`
- Agent 不知道何时调用新工具

---

#### 缺陷 2：工具执行后未更新 state（致命）

**文件**: `backend/app/services/dermatology/react_agent.py:67-88`

**当前实现**:
```python
def tool_node(state: DermaReActState) -> Dict[str, Any]:
    """工具节点：执行工具调用"""
    outputs = []
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 执行工具
            if tool_name in tools_by_name:
                result = tools_by_name[tool_name].invoke(tool_args)
                outputs.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
                        name=tool_name,
                        tool_call_id=tool_call["id"]
                    )
                )
    
    return {"messages": outputs}  # ❌ 只返回了 messages！
```

**问题**：
- 工具执行结果只作为 `ToolMessage` 返回给 LLM
- **没有将结果写入 `state["diagnosis_card"]` 等字段**
- `build_response` 函数永远拿不到这些数据
- 即使 Agent 调用了工具，前端也看不到结果

---

#### 缺陷 3：缺少中间建议生成机制

**当前状态**:
- `advice_history` 字段已定义但从未被使用
- 没有任何代码生成中间建议并写入该字段

---

## 修复方案

### 方案 1：快捷回答交互优化

#### 目标
- 点击快捷回答 → 填入输入框（支持多选）
- 用户手动点击发送按钮
- 发送后快捷选项消失

#### 实施步骤

**步骤 1.1：修改点击行为**

**文件**: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`

**位置**: `quickOptionsView` 的 Button action (约 608 行)

**修改**:
```swift
// 原代码：
Button(action: {
    NotificationCenter.default.post(
        name: NSNotification.Name("SendQuickOption"),
        object: nil,
        userInfo: ["text": option.text]
    )
})

// 改为：
Button(action: {
    // 追加到输入框，支持多选
    if !messageText.isEmpty {
        messageText += " "  // 用空格分隔
    }
    messageText += option.text
})
```

**步骤 1.2：添加已选中状态（可选增强）**

如果需要视觉反馈，可以添加：
```swift
@State private var selectedOptions: Set<String> = []

// 在 Button 中：
Button(action: {
    if selectedOptions.contains(option.text) {
        // 取消选中：从输入框移除
        messageText = messageText.replacingOccurrences(of: option.text, with: "")
            .trimmingCharacters(in: .whitespaces)
        selectedOptions.remove(option.text)
    } else {
        // 选中：追加到输入框
        if !messageText.isEmpty { messageText += " " }
        messageText += option.text
        selectedOptions.insert(option.text)
    }
}) {
    Text(option.text)
        .foregroundColor(
            selectedOptions.contains(option.text) 
                ? .white 
                : MedicalColors.primaryBlue
        )
        .background(
            selectedOptions.contains(option.text)
                ? MedicalColors.primaryBlue
                : MedicalColors.primaryBlue.opacity(0.1)
        )
}
```

**步骤 1.3：发送后清空选中状态**

在 `sendMessage()` 函数中添加：
```swift
private func sendMessage() {
    let text = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !text.isEmpty else { return }
    
    messageText = ""
    selectedOptions.removeAll()  // 清空选中状态
    
    Task {
        await viewModel.sendMessage(content: text)
    }
}
```

---

### 方案 2：诊断卡片显示修复

#### 目标
- Agent 在收集完症状后自动调用新工具
- 工具结果正确写入 state
- 前端能够接收并展示诊断卡片

#### 实施步骤

**步骤 2.1：更新 System Prompt**

**文件**: `backend/app/services/dermatology/react_agent.py`

**位置**: `DERMA_REACT_PROMPT` (约 16-41 行)

**修改**:
```python
DERMA_REACT_PROMPT = """你是一位经验丰富的皮肤科专家医生，正在与患者进行问诊对话。

## 角色定位
- 专业但亲和，用通俗易懂的语言
- 像真人医生一样自然对话

## 对话原则
1. 直接响应用户问题，不使用固定模板
2. 渐进式诊断：边问诊边给初步建议
3. 每次回复后追问 1-2 个关键问题
4. 需要时主动调用工具

## 信息收集要点
- 主诉：什么问题
- 部位：身体哪个位置
- 症状：红肿、瘙痒、疼痛、脱皮等
- 持续时间

## 可用工具及使用时机

### 1. analyze_skin_image
- **用途**: 分析皮肤图片
- **时机**: 用户上传皮肤照片时

### 2. retrieve_derma_knowledge
- **用途**: 检索皮肤科医学知识库
- **时机**: 收集到症状后，生成诊断前
- **参数**: symptoms（症状列表）, location（部位）, query（补充查询词）
- **返回**: 相关医学知识引用列表

### 3. generate_structured_diagnosis
- **用途**: 生成结构化诊断卡
- **时机**: 收集完主要信息（主诉、部位、症状、持续时间）后
- **参数**: symptoms, location, duration, knowledge_refs（来自步骤2）, additional_info
- **返回**: 包含鉴别诊断、风险等级、护理建议的结构化诊断卡

### 4. generate_diagnosis (旧工具，保留兼容)
- **用途**: 生成文本诊断建议
- **时机**: 快速给出初步建议时使用

## 诊断工作流（重要）

当收集完以下信息后，按顺序调用工具：
1. 主诉（chief_complaint）
2. 部位（skin_location）
3. 症状列表（symptoms，至少2个）
4. 持续时间（duration）

**标准流程**:
```
步骤1: 调用 retrieve_derma_knowledge(symptoms=症状列表, location=部位)
步骤2: 调用 generate_structured_diagnosis(
    symptoms=症状列表,
    location=部位,
    duration=持续时间,
    knowledge_refs=步骤1的结果
)
```

## 输出要求
- 回复简洁自然（2-4句话）
- 识别危急情况立即建议就医
- 调用工具后，基于结果给出专业建议"""
```

---

**步骤 2.2：修改工具节点，更新 state**

**文件**: `backend/app/services/dermatology/react_agent.py`

**位置**: `tool_node` 函数 (约 67-88 行)

**修改**:
```python
def tool_node(state: DermaReActState) -> Dict[str, Any]:
    """工具节点：执行工具调用并更新状态"""
    outputs = []
    updates = {}  # 用于收集 state 更新
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 执行工具
            if tool_name in tools_by_name:
                result = tools_by_name[tool_name].invoke(tool_args)
                
                # 根据工具类型更新 state
                if tool_name == "retrieve_derma_knowledge":
                    # 更新知识引用
                    if isinstance(result, list):
                        updates["knowledge_refs"] = result
                        # 同时添加到推理步骤
                        current_steps = state.get("reasoning_steps", [])
                        updates["reasoning_steps"] = current_steps + [
                            f"检索到 {len(result)} 条相关医学知识"
                        ]
                
                elif tool_name == "generate_structured_diagnosis":
                    # 更新诊断卡
                    if isinstance(result, dict):
                        updates["diagnosis_card"] = result
                        # 更新推理步骤
                        if "reasoning_steps" in result:
                            current_steps = state.get("reasoning_steps", [])
                            updates["reasoning_steps"] = current_steps + result["reasoning_steps"]
                        # 更新风险等级和就诊建议
                        if "risk_level" in result:
                            updates["risk_level"] = result["risk_level"]
                        if "need_offline_visit" in result:
                            updates["need_offline_visit"] = result["need_offline_visit"]
                
                elif tool_name == "analyze_skin_image":
                    # 保持原有逻辑
                    if isinstance(result, dict) and "analysis" in result:
                        skin_analyses = state.get("skin_analyses", [])
                        updates["skin_analyses"] = skin_analyses + [result]
                
                # 添加工具消息
                outputs.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
                        name=tool_name,
                        tool_call_id=tool_call["id"]
                    )
                )
    
    # 返回消息和状态更新
    return {"messages": outputs, **updates}
```

---

**步骤 2.3：实现中间建议生成机制**

有两种实现方式：

#### 方式 A：自动提取（推荐，简单）

在 `call_model` 函数中，当 Agent 给出建议时自动提取：

**文件**: `backend/app/services/dermatology/react_agent.py`

**位置**: `call_model` 函数 (约 55-65 行)

**修改**:
```python
def call_model(state: DermaReActState) -> Dict[str, Any]:
    """Agent 节点：调用 LLM"""
    system_message = SystemMessage(content=DERMA_REACT_PROMPT)
    
    # 构建消息列表
    messages = [system_message] + list(state["messages"])
    
    # 调用 LLM
    response = model_with_tools.invoke(messages)
    
    updates = {"messages": [response]}
    
    # 如果 Agent 给出了建议（没有调用工具），提取为中间建议
    if isinstance(response, AIMessage) and not response.tool_calls:
        content = response.content
        # 简单判断：如果回复包含建议关键词
        if any(keyword in content for keyword in ["建议", "可以", "应该", "注意", "避免"]):
            import uuid
            from datetime import datetime
            
            advice_entry = {
                "id": str(uuid.uuid4()),
                "title": "护理建议",
                "content": content,
                "evidence": [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            advice_history = state.get("advice_history", [])
            updates["advice_history"] = advice_history + [advice_entry]
    
    return updates
```

#### 方式 B：创建专门工具（更灵活，但复杂）

创建 `generate_advice` 工具，让 Agent 主动调用。

**推荐使用方式 A**，因为：
- 实现简单，不增加 Agent 负担
- 自动捕获所有建议
- 不需要修改 prompt 和工具列表

---

**步骤 2.4：验证数据流**

确认 `build_response` 函数已正确处理新字段：

**文件**: `backend/app/routes/derma.py`

**位置**: `build_response` 函数 (约 198-249 行)

**检查点**:
```python
# 添加中间建议历史
if state.get("advice_history"):
    response_data["advice_history"] = [
        DermaAdviceSchema(
            id=adv.get("id", ""),
            title=adv.get("title", ""),
            content=adv.get("content", ""),
            evidence=adv.get("evidence", []),
            timestamp=adv.get("timestamp", "")
        ) for adv in state["advice_history"]
    ]

# 添加诊断卡
if state.get("diagnosis_card"):
    card = state["diagnosis_card"]
    response_data["diagnosis_card"] = DermaDiagnosisCardSchema(
        summary=card.get("summary", ""),
        conditions=[...],
        risk_level=card.get("risk_level", "low"),
        ...
    )

# 添加知识引用
if state.get("knowledge_refs"):
    response_data["knowledge_refs"] = [...]

# 添加推理步骤
if state.get("reasoning_steps"):
    response_data["reasoning_steps"] = state["reasoning_steps"]
```

✅ **已验证**：这部分代码已在之前的实现中完成。

---

## 测试计划

### 测试 1：快捷回答交互
1. 启动 iOS 应用，进入问诊界面
2. 发送消息，等待 AI 回复带快捷选项
3. **点击第一个快捷选项** → 验证文本填入输入框
4. **点击第二个快捷选项** → 验证追加到输入框（空格分隔）
5. **点击发送** → 验证消息发送，快捷选项消失

### 测试 2：诊断卡片显示
1. 启动后端服务
2. 创建新会话，开始问诊
3. 按顺序提供信息：
   - "我手臂上有红疹"（主诉 + 部位）
   - "很痒，还有点脱皮"（症状）
   - "大概三天了"（持续时间）
4. **验证点**：
   - 后端日志显示调用 `retrieve_derma_knowledge`
   - 后端日志显示调用 `generate_structured_diagnosis`
   - API 响应包含 `diagnosis_card` 字段
   - iOS 界面显示诊断卡片
5. **检查诊断卡片内容**：
   - 症状总结
   - 鉴别诊断列表（带置信度）
   - 风险等级标签
   - 护理建议
   - 知识引用（可展开）
   - 推理步骤时间线

### 测试 3：中间建议
1. 在对话过程中，AI 给出建议
2. **验证**：建议被提取为 `advice_history` 条目
3. **验证**：iOS 界面显示中间建议卡片（如果实现了该组件）

---

## 实施检查清单

### 快捷回答优化
- [ ] 修改 `ModernConsultationView.swift` 的 Button action
- [ ] （可选）添加已选中状态管理
- [ ] 在 `sendMessage()` 中清空选中状态
- [ ] iOS 编译通过
- [ ] 功能测试通过

### 诊断卡片修复
- [ ] 更新 `DERMA_REACT_PROMPT`，添加新工具说明
- [ ] 修改 `tool_node` 函数，更新 state
- [ ] 实现中间建议提取（方式 A 或 B）
- [ ] 验证 `build_response` 处理逻辑
- [ ] 后端单元测试通过
- [ ] 端到端测试通过

---

## 风险评估

### 低风险
- 快捷回答交互优化：纯前端修改，不影响后端
- System Prompt 更新：只是添加说明，不改变现有逻辑

### 中风险
- `tool_node` 修改：涉及核心数据流，需要仔细测试
- 中间建议提取：需要验证不会误提取

### 缓解措施
1. 保留原有代码注释，便于回滚
2. 先在测试环境验证
3. 添加详细日志，便于调试
4. 单元测试覆盖新逻辑

---

## 预期效果

### 快捷回答
- ✅ 用户体验更流畅
- ✅ 支持多选组合
- ✅ 界面更整洁

### 诊断卡片
- ✅ Agent 自动调用新工具
- ✅ 诊断卡片正确显示
- ✅ 知识引用可追溯
- ✅ 推理过程透明化

---

## 后续优化建议

1. **中间建议卡片 UI**：如果采用方式 A，需要实现 `AdviceCardView` 的显示逻辑
2. **工具调用监控**：添加 metrics，跟踪工具调用频率和成功率
3. **知识库扩充**：丰富本地知识库内容
4. **诊断质量评估**：收集用户反馈，优化诊断准确性

---

**文档维护者**: 项目团队  
**最后更新**: 2026-01-16  
**下次审查**: 实施完成后

---

## 实施记录

### 2026-01-16 实施完成

#### 修改文件
- `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`
  - 修改 `ModernMessageBubbleAdapter` 添加 `@Binding var messageText: String`
  - 修改快捷选项点击行为：从 NotificationCenter 发送改为填入输入框
  - 删除 NotificationCenter 监听代码
- `backend/app/services/dermatology/react_agent.py`
  - 更新 `DERMA_REACT_PROMPT` 添加新工具使用说明和诊断工作流
  - 修改 `tool_node` 函数在工具执行后更新 state 字段
  - 修改 `call_model` 函数实现中间建议自动提取机制
- `backend/test/test_tool_node_state_update.py` (新增)
  - 测试工具节点状态更新
  - 测试中间建议提取逻辑

#### 测试结果
- ✅ iOS 编译通过 (BUILD SUCCEEDED)
- ✅ 后端代码导入验证通过
- ✅ 快捷回答交互优化完成
- ✅ System Prompt 更新完成
- ✅ tool_node 状态更新实现完成
- ✅ 中间建议提取机制实现完成

#### 实施检查清单更新

##### 快捷回答优化
- [x] 修改 `ModernConsultationView.swift` 的 Button action
- [x] 删除 NotificationCenter 监听
- [x] iOS 编译通过

##### 诊断卡片修复
- [x] 更新 `DERMA_REACT_PROMPT`，添加新工具说明
- [x] 修改 `tool_node` 函数，更新 state
- [x] 实现中间建议提取（方式 A: 自动提取）
- [x] 添加单元测试文件

#### 遗留问题
- iOS submodule 提交需要手动处理

#### 后续优化
- 考虑添加快捷选项已选中的视觉反馈
- 优化中间建议提取的关键词匹配逻辑
- 扩充本地知识库内容

### 2026-01-16 中间建议工具化重构

#### 背景
原实现使用关键词匹配自动提取建议，不符合智能体架构原则。

#### 改动
- 新增 `record_intermediate_advice` 工具
- 更新 System Prompt 指导 Agent 使用
- 扩展 `tool_node` 处理工具返回值
- 移除 `call_model` 中的关键词匹配逻辑
- 更新单元测试覆盖工具调用路径

#### 优势
- 符合 ReAct 架构，所有状态更新通过工具驱动
- Agent 自主决策何时记录建议
- 数据流清晰可追踪
- 易于扩展结构化字段

#### 参考
详见 [中间建议工具化实施计划](./2026-01-16-intermediate-advice-tooling-implementation.md)
