# 中间建议工具化实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将中间建议提取从关键词匹配改为 Agent 主动工具调用，符合 ReAct 智能体架构

**Architecture:** 新增 `record_intermediate_advice` 工具供 Agent 调用，在 `tool_node` 中处理返回值写入 state，更新 Prompt 指导 Agent 使用，移除 `call_model` 中的关键词匹配逻辑

**Tech Stack:** Python, LangChain, LangGraph, Pydantic, pytest

---

## Task 1: 新增 record_intermediate_advice 工具

**Files:**
- Modify: `backend/app/services/dermatology/react_tools.py:303-306`

**Step 1: 添加工具定义**

在 `react_tools.py` 文件末尾，`get_derma_tools()` 函数之前添加：

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

**Step 2: 更新工具列表**

修改 `get_derma_tools()` 函数：

```python
def get_derma_tools():
    """获取皮肤科工具列表"""
    return [
        analyze_skin_image, 
        generate_diagnosis, 
        retrieve_derma_knowledge, 
        generate_structured_diagnosis,
        record_intermediate_advice
    ]
```

**Step 3: 验证导入**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_tools import record_intermediate_advice; print('Import OK')"`

Expected: `Import OK`

**Step 4: Commit**

```bash
git add backend/app/services/dermatology/react_tools.py
git commit -m "feat(backend): 新增 record_intermediate_advice 工具

- 添加工具定义，接收 title/content/evidence 参数
- 返回带 id 和 timestamp 的结构化建议对象
- 更新 get_derma_tools() 列表"
```

---

## Task 2: 更新 System Prompt

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:17-79`

**Step 1: 在 Prompt 中添加新工具说明**

在 `DERMA_REACT_PROMPT` 的 `## 可用工具及使用时机` 章节，`### 4. generate_diagnosis` 之后添加：

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

**Step 2: 验证 Prompt 格式**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import DERMA_REACT_PROMPT; print('Prompt length:', len(DERMA_REACT_PROMPT))"`

Expected: 输出 Prompt 长度（应大于原来的值）

**Step 3: Commit**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "feat(backend): 更新 System Prompt 添加 record_intermediate_advice 说明

- 在可用工具章节新增工具 5 说明
- 明确使用时机和示例场景
- 强调必须调用以记录建议"
```

---

## Task 3: 扩展 tool_node 处理逻辑

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:126-182`

**Step 1: 添加工具处理分支**

在 `tool_node` 函数中，`elif tool_name == "analyze_skin_image":` 分支之后添加：

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

**Step 2: 验证语法**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import _build_derma_react_graph; print('Syntax OK')"`

Expected: `Syntax OK`

**Step 3: Commit**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "feat(backend): tool_node 支持 record_intermediate_advice

- 添加工具处理分支
- 更新 advice_history 和 reasoning_steps
- 保持与其他工具处理逻辑一致"
```

---

## Task 4: 移除关键词匹配逻辑

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:95-124`

**Step 1: 简化 call_model 函数**

将 `call_model` 函数简化为：

```python
def call_model(state: DermaReActState) -> Dict[str, Any]:
    """Agent 节点：调用 LLM"""
    system_message = SystemMessage(content=DERMA_REACT_PROMPT)
    
    # 构建消息列表
    messages = [system_message] + list(state["messages"])
    
    # 调用 LLM
    response = model_with_tools.invoke(messages)
    
    return {"messages": [response]}
```

**Step 2: 验证语法**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import _build_derma_react_graph; print('Syntax OK')"`

Expected: `Syntax OK`

**Step 3: Commit**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "refactor(backend): 移除 call_model 中的关键词匹配逻辑

- 删除自动建议提取代码
- 简化为纯消息传递
- 建议提取完全由工具调用驱动"
```

---

## Task 5: 编写单元测试

**Files:**
- Modify: `backend/test/test_tool_node_state_update.py:95-161`

**Step 1: 添加新测试用例**

在 `TestAdviceExtraction` 类之前添加新测试类：

```python
class TestRecordIntermediateAdviceTool:
    """测试 record_intermediate_advice 工具"""
    
    def test_record_advice_updates_state(self):
        """测试工具调用更新 advice_history"""
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

**Step 2: 删除旧测试**

删除或注释掉以下测试方法：
- `test_advice_extracted_from_response`
- `test_no_advice_extraction_for_questions`

**Step 3: 运行测试**

Run: `cd backend && source venv/bin/activate && python -m pytest test/test_tool_node_state_update.py::TestRecordIntermediateAdviceTool -v`

Expected: PASS (1 test passed)

**Step 4: Commit**

```bash
git add backend/test/test_tool_node_state_update.py
git commit -m "test(backend): 更新单元测试覆盖工具调用路径

- 新增 TestRecordIntermediateAdviceTool 测试类
- 验证工具调用更新 advice_history 和 reasoning_steps
- 移除关键词提取相关测试"
```

---

## Task 6: 运行完整测试套件

**Files:**
- Test: `backend/test/test_tool_node_state_update.py`
- Test: `backend/test/test_react_state.py`
- Test: `backend/test/test_build_response.py`

**Step 1: 运行所有相关测试**

Run: `cd backend && source venv/bin/activate && python -m pytest test/test_tool_node_state_update.py test/test_react_state.py test/test_build_response.py -v`

Expected: 所有测试通过

**Step 2: 验证后端代码导入**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import get_derma_react_graph; print('Import OK')"`

Expected: `Import OK`

**Step 3: 检查代码覆盖**

Run: `cd backend && source venv/bin/activate && python -m pytest test/test_tool_node_state_update.py --cov=app.services.dermatology.react_agent --cov-report=term-missing`

Expected: 覆盖率报告显示新增代码被测试覆盖

---

## Task 7: 更新文档

**Files:**
- Modify: `docs/plans/2026-01-16-diagnosis-display-bugfix.md`

**Step 1: 在文档末尾添加更新记录**

在 `## 实施记录` 章节添加：

```markdown
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
详见 [中间建议工具化设计方案](./2026-01-16-intermediate-advice-tooling-design.md)
```

**Step 2: Commit**

```bash
git add docs/plans/2026-01-16-diagnosis-display-bugfix.md
git commit -m "docs: 更新实施记录 - 中间建议工具化重构

- 记录重构背景和改动
- 说明优势和参考文档"
```

---

## Task 8: 最终验证

**Files:**
- Verify: 所有修改的文件

**Step 1: 完整编译检查**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import get_derma_react_graph; from app.services.dermatology.react_tools import get_derma_tools; print('Tools:', len(get_derma_tools())); print('All OK')"`

Expected: 
```
Tools: 5
All OK
```

**Step 2: 运行完整测试套件**

Run: `cd backend && source venv/bin/activate && python -m pytest test/ -v -k "derma or react" --tb=short`

Expected: 所有测试通过，无失败

**Step 3: 检查 git 状态**

Run: `git status`

Expected: 工作目录干净，所有改动已提交

**Step 4: 查看提交历史**

Run: `git log --oneline -8`

Expected: 看到 8 个新提交（包括之前的 import 修复和设计文档）

---

## 验收清单

### 功能验收
- [ ] `record_intermediate_advice` 工具已定义并加入工具列表
- [ ] System Prompt 包含新工具说明和使用场景
- [ ] `tool_node` 正确处理工具返回值
- [ ] `call_model` 不再包含关键词匹配逻辑
- [ ] 单元测试覆盖工具调用路径
- [ ] 所有测试通过

### 代码质量
- [ ] 代码符合 PEP8 规范
- [ ] 函数有清晰的 docstring
- [ ] 无硬编码值
- [ ] 错误处理适当
- [ ] 日志记录完整

### 文档完整性
- [ ] 设计文档已创建
- [ ] 实施记录已更新
- [ ] 提交信息清晰
- [ ] 代码注释充分

---

## 回滚方案

如果实施后发现问题，可以回滚到之前的版本：

```bash
# 查看提交历史
git log --oneline -10

# 回滚到指定提交（实施前的最后一个提交）
git reset --hard <commit-hash>

# 或者创建 revert 提交
git revert HEAD~7..HEAD
```

---

## 后续工作

1. **监控 Agent 行为**: 观察 Agent 是否正确调用 `record_intermediate_advice`
2. **调优 Prompt**: 根据实际表现优化工具说明
3. **扩展工具参数**: 添加 `severity`、`category` 等字段
4. **前端增强**: 根据建议类型显示不同样式

---

**计划创建时间**: 2026-01-16  
**预计完成时间**: 1-2 小时  
**风险等级**: 低
