# 中间建议工具化设计方案

**日期**: 2026-01-16  
**版本**: V1.0  
**状态**: 设计完成，待实施

---

## 问题背景

### 当前实现的缺陷

在 2026-01-16 完成的诊断展示功能缺陷修复中，中间建议（`advice_history`）的提取采用了**关键词匹配**方式：

```python
# backend/app/services/dermatology/react_agent.py:112
if any(keyword in content for keyword in ["建议", "可以", "应该", "注意", "避免", "推荐"]):
    # 自动提取为建议...
```

**存在的问题**:

1. **违背智能体设计原则**  
   - Agent 通过工具调用驱动状态更新（如 `retrieve_derma_knowledge`、`generate_structured_diagnosis`）
   - 中间建议却由框架层用规则"猜测"，Agent 自身不知道记录了什么
   - 不符合 ReAct 架构的"工具-状态-响应"模式

2. **语义理解脆弱**  
   - "可以告诉我..."（问句）可能被误判为建议
   - "从图片可以看到..."（描述）也可能误触发
   - 无法处理复杂语境和否定句

3. **可维护性差**  
   - 关键词列表需要持续调优
   - 无法扩展结构化字段（如严重程度、引用证据）
   - 后续优化只能继续堆规则

4. **测试覆盖不足**  
   - 单元测试只验证"关键词命中 → state 有建议"
   - 未覆盖 Agent 真实决策流程

---

## 设计目标

1. **符合智能体架构**: 所有状态更新通过工具调用驱动
2. **Agent 自主决策**: 由 Agent 判断何时记录建议，而非框架猜测
3. **数据流清晰**: 工具调用 → tool_node 处理 → state 更新 → API 响应
4. **易于扩展**: 支持结构化字段，便于后续增强
5. **不增加成本**: 无需额外 LLM 调用

---

## 解决方案

### 核心思路

**将中间建议提取从"框架层关键词匹配"改为"Agent 主动工具调用"**

- 新增 `record_intermediate_advice` 工具
- 在 System Prompt 中明确告知 Agent 何时调用该工具
- 在 `tool_node` 中处理工具返回值，更新 `state["advice_history"]`
- 移除 `call_model` 中的关键词匹配逻辑

---

## 架构设计

### 数据流

```
用户消息 
  ↓
agent 节点 (call_model)
  ↓
LLM 推理：需要记录建议？
  ↓ 是
调用 record_intermediate_advice 工具
  ↓
tool_node 处理
  ↓
更新 state["advice_history"]
  ↓
build_response() 构建 API 响应
  ↓
前端展示建议卡片
```

### 组件关系

```
┌─────────────────────────────────────────┐
│  DERMA_REACT_PROMPT                     │
│  - 指导 Agent 何时调用工具               │
│  - 示例：给出护理建议时调用              │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  record_intermediate_advice (工具)       │
│  - 入参: title, content, evidence       │
│  - 返回: {id, title, content, ...}      │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  tool_node (处理器)                      │
│  - 识别工具名                            │
│  - 追加到 state["advice_history"]       │
│  - 同步 reasoning_steps                 │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  DermaReActState                        │
│  - advice_history: List[dict]           │
└─────────────────────────────────────────┘
```

---

## 详细设计

### 1. 工具定义

**文件**: `backend/app/services/dermatology/react_tools.py`

```python
@tool
def record_intermediate_advice(
    title: str,
    content: str,
    evidence: List[str] = []
) -> dict:
    """
    记录中间护理建议
    
    在问诊过程中，当你给出护理建议或风险提示时调用此工具。
    例如：建议保持清洁、避免抓挠等初步护理措施。
    
    Args:
        title: 建议标题，如"初步护理建议"、"风险提示"
        content: 建议内容，清晰具体的护理指导
        evidence: 依据列表（可选），如 ["湿疹护理指南"]
    
    Returns:
        结构化建议对象，包含 id、timestamp 等字段
    """
    import uuid
    from datetime import datetime
    
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "evidence": evidence,
        "timestamp": datetime.utcnow().isoformat()
    }
```

**更新工具列表**:

```python
def get_derma_tools():
    """获取皮肤科工具列表"""
    return [
        analyze_skin_image, 
        generate_diagnosis, 
        retrieve_derma_knowledge, 
        generate_structured_diagnosis,
        record_intermediate_advice  # 新增
    ]
```

---

### 2. Prompt 更新

**文件**: `backend/app/services/dermatology/react_agent.py`

在 `DERMA_REACT_PROMPT` 的"可用工具及使用时机"章节后新增：

```python
### 5. record_intermediate_advice
- **用途**: 记录中间护理建议或风险提示
- **时机**: 在对话过程中给出护理建议时主动调用
- **参数**: title（建议标题）, content（建议内容）, evidence（依据列表，可选）
- **示例场景**:
  - 用户描述症状后，给出初步护理建议："建议保持皮肤清洁干燥"
  - 识别到风险征象时："发现感染迹象，建议尽快就医"
  - 提供日常护理指导："避免使用刺激性化妆品"

**重要**: 每次给出护理建议或风险提示时，必须调用此工具记录，以便前端展示。
```

---

### 3. tool_node 扩展

**文件**: `backend/app/services/dermatology/react_agent.py`

在 `tool_node` 函数的工具处理分支中新增：

```python
elif tool_name == "record_intermediate_advice":
    # 记录中间建议
    if isinstance(result, dict):
        advice_history = state.get("advice_history", [])
        updates["advice_history"] = advice_history + [result]
        # 同步推理步骤
        current_steps = state.get("reasoning_steps", [])
        updates["reasoning_steps"] = current_steps + [
            f"记录护理建议: {result.get('title', '未命名')}"
        ]
```

---

### 4. 移除关键词逻辑

**文件**: `backend/app/services/dermatology/react_agent.py`

在 `call_model` 函数中删除以下代码：

```python
# 删除这段代码（约 108-122 行）
if isinstance(response, AIMessage) and not response.tool_calls:
    content = response.content
    if any(keyword in content for keyword in ["建议", "可以", "应该", "注意", "避免", "推荐"]):
        advice_entry = {
            "id": str(uuid.uuid4()),
            "title": "护理建议",
            "content": content,
            "evidence": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        advice_history = state.get("advice_history", [])
        updates["advice_history"] = advice_history + [advice_entry]
```

简化为：

```python
def call_model(state: DermaReActState) -> Dict[str, Any]:
    """Agent 节点：调用 LLM"""
    system_message = SystemMessage(content=DERMA_REACT_PROMPT)
    messages = [system_message] + list(state["messages"])
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}
```

---

### 5. 测试调整

**文件**: `backend/test/test_tool_node_state_update.py`

**新增测试用例**:

```python
def test_record_intermediate_advice_updates_state(self):
    """测试 record_intermediate_advice 更新 advice_history"""
    from app.services.dermatology.react_agent import _build_derma_react_graph, reset_derma_react_graph
    
    reset_derma_react_graph()
    
    with patch('app.services.llm_provider.LLMProvider.get_llm') as mock_llm:
        # 模拟 Agent 调用 record_intermediate_advice 工具
        mock_tool_call = {
            "name": "record_intermediate_advice",
            "args": {
                "title": "初步护理建议",
                "content": "建议保持皮肤清洁干燥，避免抓挠",
                "evidence": ["湿疹护理指南"]
            },
            "id": "call-789"
        }
        mock_ai_response = AIMessage(content="", tool_calls=[mock_tool_call])
        mock_final_response = AIMessage(content="请问症状持续多久了？")
        
        mock_model = MagicMock()
        mock_model.bind_tools.return_value.invoke.side_effect = [
            mock_ai_response,
            mock_final_response
        ]
        mock_llm.return_value = mock_model
        
        graph = _build_derma_react_graph()
        state = create_react_initial_state("test-session", 1)
        state["messages"] = [HumanMessage(content="我手臂有红疹")]
        
        result = graph.invoke(state)
        
        # 验证 advice_history 被更新
        assert "advice_history" in result
        assert len(result["advice_history"]) > 0
        assert result["advice_history"][0]["title"] == "初步护理建议"
        assert "建议" in result["advice_history"][0]["content"]
        
        # 验证 reasoning_steps 同步
        assert "reasoning_steps" in result
        assert any("记录护理建议" in step for step in result["reasoning_steps"])
```

**移除/更新旧测试**:

- `test_advice_extracted_from_response` - 删除（不再使用关键词提取）
- `test_no_advice_extraction_for_questions` - 删除（不再需要）

---

## 实施步骤

### Step 1: 新增工具定义
- 在 `react_tools.py` 中添加 `record_intermediate_advice` 函数
- 更新 `get_derma_tools()` 返回列表

### Step 2: 更新 Prompt
- 在 `DERMA_REACT_PROMPT` 中添加工具说明和使用场景

### Step 3: 扩展 tool_node
- 在 `tool_node` 中添加 `record_intermediate_advice` 处理分支

### Step 4: 简化 call_model
- 删除关键词匹配逻辑
- 保持简洁的消息传递

### Step 5: 调整测试
- 新增工具调用测试用例
- 移除关键词提取相关测试

### Step 6: 验证
- 运行单元测试
- 手动测试 Agent 是否正确调用工具

---

## 验收标准

### 功能验收

- [ ] Agent 在给出护理建议时主动调用 `record_intermediate_advice`
- [ ] 工具返回值正确写入 `state["advice_history"]`
- [ ] `reasoning_steps` 同步更新
- [ ] API 响应包含 `advice_history` 字段
- [ ] 前端正确展示建议卡片

### 代码质量

- [ ] 工具定义清晰，参数类型明确
- [ ] Prompt 说明详细，示例充分
- [ ] tool_node 逻辑正确，无遗漏
- [ ] 单元测试覆盖核心路径
- [ ] 无关键词匹配残留代码

### 架构一致性

- [ ] 所有状态更新通过工具调用
- [ ] 数据流清晰可追踪
- [ ] 符合 ReAct 模式
- [ ] 与现有工具（retrieve_derma_knowledge、generate_structured_diagnosis）保持一致

---

## 风险评估

### 低风险

- 工具定义简单，不涉及外部调用
- tool_node 扩展逻辑清晰
- 不影响现有工具

### 中风险

- **Agent 可能不调用工具**: 如果 Prompt 说明不够清晰，Agent 可能忽略该工具
  - **缓解**: 在 Prompt 中强调"必须调用"，并提供多个示例场景
  
- **调用时机不准确**: Agent 可能在不合适的时候调用
  - **缓解**: 通过测试和实际使用调优 Prompt

### 缓解措施

1. 详细的 Prompt 说明和示例
2. 完整的单元测试覆盖
3. 手动测试验证 Agent 行为
4. 保留日志便于调试

---

## 后续优化

### 短期（1-2 周）

1. **监控工具调用频率**: 确认 Agent 是否正确使用工具
2. **收集用户反馈**: 建议卡片是否有价值
3. **调优 Prompt**: 根据实际表现优化说明

### 中期（1-2 月）

1. **扩展工具参数**: 添加 `severity`（严重程度）、`category`（建议类型）等字段
2. **前端增强**: 根据 severity 显示不同样式
3. **建议去重**: 避免重复记录相似建议

### 长期（3+ 月）

1. **建议质量评估**: 收集用户对建议的反馈
2. **个性化建议**: 根据用户历史调整建议内容
3. **多语言支持**: 支持英文等其他语言

---

## 相关文档

- [诊断展示功能缺陷修复实施计划](./2026-01-16-diagnosis-display-bugfix-implementation.md)
- [API 契约文档](../API_CONTRACT.md)
- [开发规范](../DEVELOPMENT_GUIDELINES.md)

---

**设计者**: AI 开发团队  
**审核者**: 技术负责人  
**最后更新**: 2026-01-16
