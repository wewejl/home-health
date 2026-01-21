# 流式响应技术设计文档

**文档版本**: 1.0
**创建日期**: 2026-01-20
**状态**: 待实施
**优先级**: 中

---

## 一、背景

### 1.1 问题概述

当前智能体系统虽然支持 SSE (Server-Sent Events) 连接，但 AI 响应是**一次性返回**的，没有实现真正的流式输出。用户需要等待 4-8 秒才能看到完整的 AI 回复，体验不佳。

### 1.2 当前 SSE 输出示例

```
event: meta
data: {"session_id": "...", "agent_type": "general"}

event: complete
data: {"message": "您好，我是您的AI医生助手..."}
```

**问题**: 缺少 `event: chunk`，无法实现打字机效果。

### 1.3 期望 SSE 输出

```
event: meta
data: {"session_id": "...", "agent_type": "general"}

event: chunk
data: {"text": "您好"}

event: chunk
data: {"text": "，我是"}

event: chunk
data: {"text": "您的"}

event: chunk
data: {"text": "AI医生"}

...

event: complete
data: {"message": "...", "stage": "...", ...}
```

---

## 二、架构分析

### 2.1 当前调用链

```
┌─────────────────────────────────────────────────────────────┐
│                     sessions.py (路由层)                      │
│  stream_agent_response()                                     │
│     ↓                                                        │
│     chunk_queue = asyncio.Queue()                           │
│     on_chunk = lambda c: chunk_queue.put(("chunk", c))      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   ReActAgent (智能体层)                       │
│  run(state, user_input, on_chunk, ...)                      │
│     ↓                                                        │
│  graph.ainvoke(state)  ← 非流式！                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     LangGraph (图执行引擎)                    │
│  _reasoning_node()          ← 使用 chat_with_tools()        │
│     ↓                                                        │
│  _tool_executor_node()      ← 执行工具                       │
│     ↓                                                        │
│  _response_generator_node() ← 使用 chat_with_tools()        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     QwenService (LLM 层)                     │
│  ✓ chat_with_tools()         - 非流式                        │
│  ✓ chat_with_tools_stream() - 流式 (已存在但未使用!)         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 问题根源

| 层级 | 问题 | 说明 |
|------|------|------|
| 智能体层 | `run()` 使用 `ainvoke()` | LangGraph 的 `ainvoke` 是非流式的 |
| 节点层 | `_reasoning_node` 使用非流式 LLM | 调用 `chat_with_tools()` 而非 `chat_with_tools_stream()` |
| 节点层 | `_response_generator_node` 使用非流式 LLM | 同上 |
| 回调层 | `on_chunk` 从未被调用 | 虽然传递了但内部没使用 |

### 2.3 现有可用资源

```python
# qwen_service.py - 已存在但未使用!
async def chat_with_tools_stream(
    messages, tools, tool_choice, model, temperature, max_tokens
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Yields:
        {"type": "content", "delta": "文本片段"}
        {"type": "tool_call", "tool_call": {...}}
        {"type": "done", "finish_reason": "..."}
    """
```

---

## 三、设计方案

### 3.1 修改策略

采用 **全流程流式** 方案，让用户看到 AI 的完整思考过程：

1. **推理阶段**: 流式输出 AI 的思考过程（可选，通过配置控制）
2. **工具执行**: 显示"正在分析..."等状态
3. **响应生成**: 流式输出最终回复

### 3.2 新的调用链

```
stream_agent_response()
    ↓
ReActAgent.run_stream()  ← 新方法
    ↓
graph.astream()  ← 流式图遍历
    ↓
    ├─ reasoning_node_stream()  ← 流式推理
    ├─ tool_executor_node()
    └─ response_generator_node_stream()  ← 流式生成
    ↓
on_chunk("...")  ← 逐字输出
```

### 3.3 新增事件类型

```python
# 当前事件类型
event: chunk      # 文本片段
event: complete  # 完成

# 新增事件类型
event: thinking   # AI 思考中
event: tool_call  # 调用工具
event: tool_result # 工具结果
```

---

## 四、具体改动

### 4.1 修改 `react_base.py`

#### 4.1.1 新增 `run_stream()` 方法

**位置**: `ReActAgent` 类中，与 `run()` 并列

```python
async def run_stream(
    self,
    state: Dict[str, Any],
    user_input: str = None,
    attachments: list = None,
    action: str = "conversation",
    on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
    show_thinking: bool = False,  # 是否显示思考过程
    **kwargs
) -> AgentResponse:
    """
    流式运行 ReAct Agent

    Args:
        state: 当前会话状态
        user_input: 用户输入
        attachments: 附件列表
        action: 动作类型
        on_chunk: 流式输出回调
        show_thinking: 是否显示 AI 思考过程

    Returns:
        AgentResponse
    """
    # 重置状态
    state["iteration_count"] = 0
    state["tool_results"] = []
    state["pending_tool_calls"] = []

    # 添加用户消息
    if user_input:
        state["messages"].append({"role": "user", "content": user_input})

    if attachments:
        state["attachments"] = attachments

    try:
        # 使用 astream 而不是 ainvoke
        async for event in self.graph.astream(state):
            node_name = event.get("node", "")
            node_state = event

            # 处理不同节点
            if node_name == "reasoning":
                await self._handle_reasoning_stream(
                    node_state, on_chunk, show_thinking
                )
            elif node_name == "response_generator":
                await self._handle_response_stream(
                    node_state, on_chunk
                )

        # 获取最终状态
        final_state = state
        serialized_state = self._serialize_state_for_db(final_state)

        return AgentResponse(
            message=final_state.get("current_response", ""),
            stage=final_state.get("stage", "collecting"),
            progress=final_state.get("progress", 0),
            quick_options=final_state.get("quick_options", []),
            risk_level=final_state.get("risk_level"),
            specialty_data=final_state.get("specialty_data"),
            next_state=serialized_state
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return AgentResponse(
            message=f"抱歉，处理您的请求时出现了问题: {str(e)}",
            stage=state.get("stage", "collecting"),
            progress=state.get("progress", 0),
            quick_options=[],
            next_state=state
        )
```

#### 4.1.2 新增 `_handle_reasoning_stream()` 方法

```python
async def _handle_reasoning_stream(
    self,
    state: Dict[str, Any],
    on_chunk: Optional[Callable[[str], Awaitable[None]]],
    show_thinking: bool
):
    """处理推理节点的流式输出"""
    messages = self._build_reasoning_messages(state)
    decision_instruction = self._get_decision_instruction(state)
    messages.append({"role": "user", "content": decision_instruction})

    # 发送思考状态
    if show_thinking and on_chunk:
        await on_chunk("🤔 正在分析...\n")

    # 使用流式 LLM
    full_response = ""
    async for chunk in QwenService.chat_with_tools_stream(
        messages=messages,
        tools=self._tool_schemas,
        tool_choice="auto",
        max_tokens=2000
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "content":
            delta = chunk.get("delta", "")
            full_response += delta
            # 如果显示思考过程，发送给前端
            if show_thinking and on_chunk:
                await on_chunk(delta)

        elif chunk_type == "tool_call":
            # AI 决定调用工具
            tool_call = chunk.get("tool_call", {})
            state["pending_tool_calls"] = [tool_call]
            state["agent_decision"] = {
                "action": "use_tool",
                "tool_calls": [tool_call],
                "thought": full_response
            }
            return

        elif chunk_type == "done":
            # AI 决定直接回复
            decision = self._parse_decision(full_response)
            state["agent_decision"] = decision
            return
```

#### 4.1.3 新增 `_handle_response_stream()` 方法

```python
async def _handle_response_stream(
    self,
    state: Dict[str, Any],
    on_chunk: Optional[Callable[[str], Awaitable[None]]]
):
    """处理响应生成节点的流式输出"""
    decision = state.get("agent_decision", {})
    response = decision.get("response", "")

    if not response:
        action = decision.get("action", "respond")
        if action == "diagnose":
            # 流式生成诊断
            response = await self._generate_diagnosis_stream(state, on_chunk)
        else:
            response = "请问还有什么需要了解的吗？"

    # 流式输出响应
    if on_chunk:
        for char in response:
            await on_chunk(char)

    state["current_response"] = response
    state["quick_options"] = decision.get("quick_options", [])

    if decision.get("stage"):
        state["stage"] = decision["stage"]
    if decision.get("progress"):
        state["progress"] = decision["progress"]
```

#### 4.1.4 新增 `_generate_diagnosis_stream()` 方法

```python
async def _generate_diagnosis_stream(
    self,
    state: Dict[str, Any],
    on_chunk: Optional[Callable[[str], Awaitable[None]]]
) -> str:
    """流式生成诊断"""
    ctx = state.get("medical_context", {})
    specialty_data = state.get("specialty_data", {})

    diagnosis_prompt = f"""基于以下收集的信息，请给出专业的初步诊断意见：

- {self._format_medical_context(ctx)}

图像分析结果：{specialty_data.get('skin_analysis', {}).get('findings', '无')}
风险评估：{specialty_data.get('risk_assessment', {}).get('risk_level', '未评估')}

请包含：
1. 可能的诊断（按可能性排序）
2. 诊断依据
3. 建议的处理方式
4. 是否需要线下就医
5. 日常护理建议
6. 注意事项和警示信号

请用专业但通俗易懂的语言回复。"""

    messages = [
        {"role": "system", "content": self.get_system_prompt()},
        {"role": "user", "content": diagnosis_prompt}
    ]

    full_response = ""
    async for chunk in QwenService.chat_with_tools_stream(
        messages=messages,
        tools=[],
        max_tokens=2000
    ):
        if chunk.get("type") == "content":
            delta = chunk.get("delta", "")
            full_response += delta
            if on_chunk:
                await on_chunk(delta)
        elif chunk.get("type") == "done":
            break

    return full_response
```

### 4.2 修改 `sessions.py` 路由

#### 4.2.1 修改 `stream_agent_response()` 函数

**位置**: `sessions.py`, 约 327 行

**当前代码**:
```python
final_state = await agent.run(
    state=state,
    user_input=user_input,
    attachments=attachments,
    action=action,
    on_chunk=on_chunk,
    **extra_kwargs
)
```

**修改为**:
```python
# 检查是否支持流式
if hasattr(agent, 'run_stream'):
    final_state = await agent.run_stream(
        state=state,
        user_input=user_input,
        attachments=attachments,
        action=action,
        on_chunk=on_chunk,
        show_thinking=False,  # 可配置
        **extra_kwargs
    )
else:
    # 降级到非流式
    final_state = await agent.run(
        state=state,
        user_input=user_input,
        attachments=attachments,
        action=action,
        on_chunk=on_chunk,
        **extra_kwargs
    )
```

### 4.3 新增配置项

在 `config.py` 中添加:

```python
# 流式响应配置
ENABLE_STREAMING: bool = Field(default=True)
SHOW_THINKING_PROCESS: bool = Field(default=False)  # 是否显示 AI 思考过程
STREAMING_CHUNK_SIZE: int = Field(default=10)  # 每次发送的字符数
```

---

## 五、前端对接

### 5.1 当前前端 SSE 处理

```typescript
// 需要支持新的事件类型
const eventHandlers = {
  meta: (data) => { /* ... */ },
  chunk: (data) => {
    // 当前: data.text
    // 需要处理: 思考、工具调用等
  },
  complete: (data) => { /* ... */ },
  // 新增
  thinking: (data) => { /* 显示思考动画 */ },
  tool_call: (data) => { /* 显示工具调用状态 */ },
  tool_result: (data) => { /* 显示工具结果 */ },
};
```

### 5.2 建议的 UI 改进

```
┌────────────────────────────────────────┐
│ 👤 用户: 我头痛，请问我该怎么办？      │
├────────────────────────────────────────┤
│ 🤔 AI 正在分析...                      │  ← 新增思考状态
│                                         │
│ [✓ 查询医学知识]                       │  ← 新增工具调用状态
│                                         │
│ 根据您的描述，头痛可能由多种原因        │  ← 流式输出
│ 引起。请问您的头痛是最近才开始的吗      │
│ ？具体在哪个部位？                      │
│                                         │
│ [感冒发热] [消化不适] [其他症状]       │
└────────────────────────────────────────┘
```

---

## 六、测试计划

### 6.1 单元测试

```python
# test_streaming_agent.py

async def test_run_stream_basic():
    """测试基础流式输出"""
    agent = GeneralReActAgent()
    state = create_initial_state("test-session", 1, "general")

    chunks = []
    async def on_chunk(chunk):
        chunks.append(chunk)

    response = await agent.run_stream(
        state=state,
        user_input="你好",
        on_chunk=on_chunk
    )

    assert len(chunks) > 0
    assert response.message is not None

async def test_run_stream_with_tools():
    """测试工具调用的流式输出"""
    # ...

async def test_run_stream_with_thinking():
    """测试显示思考过程"""
    # ...
```

### 6.2 集成测试

```bash
# 1. 启动后端
curl -s 'http://localhost:8100/health'

# 2. 创建会话并测试流式
curl -N -X POST 'http://localhost:8100/sessions/{id}/messages' \
  -H 'Accept: text/event-stream' \
  -d '{"content": "你好"}'

# 预期: 看到 event: chunk 事件
```

### 6.3 验收标准

- [ ] SSE 响应包含 `event: chunk` 事件
- [ ] chunk 事件包含非空 `text` 字段
- [ ] 前端能正确显示逐字输出效果
- [ ] 工具调用时显示对应状态
- [ ] 完成后包含完整响应
- [ ] 错误情况能正确处理

---

## 七、实施步骤

### 阶段 1: 基础流式 (1-2 天)

1. 在 `react_base.py` 新增 `run_stream()` 方法
2. 修改 `_response_generator_node` 支持流式
3. 修改 `sessions.py` 调用新方法
4. 测试验证基础流式输出

### 阶段 2: 完整流式 (2-3 天)

1. 实现 `_handle_reasoning_stream()`
2. 实现 `_generate_diagnosis_stream()`
3. 添加工具调用状态输出
4. 完整测试

### 阶段 3: 前端对接 (2-3 天)

1. 更新 SSE 事件处理
2. 添加思考状态 UI
3. 添加工具调用状态 UI
4. 联调测试

### 阶段 4: 优化 (1 天)

1. 性能优化
2. 错误处理完善
3. 配置项调整
4. 文档更新

**预计总工时**: 6-9 天

---

## 八、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LangGraph astream 兼容性 | 中 | 先做技术验证，确保 astream 行为符合预期 |
| 流式与状态同步 | 高 | 确保流式输出后状态正确更新 |
| 性能问题 | 中 | 添加缓存，控制流式频率 |
| 前端兼容性 | 低 | 保留非流式降级方案 |

---

## 九、实施状态

### ✅ 已完成

#### 阶段 1: 基础流式
- [x] 在 `react_base.py` 新增 `run_stream()` 方法
- [x] 修改 `_response_generator_node` 支持流式
- [x] 修改 `sessions.py` 调用新方法
- [x] 测试验证基础流式输出

#### 阶段 2: 完整流式
- [x] 实现 `_handle_reasoning_stream()`
- [x] 实现 `_generate_diagnosis_stream()`
- [x] 添加工具调用状态输出
- [x] 完整测试

#### 阶段 3: 前端对接
- [x] iOS: 更新 SSE 事件处理 (`APITypes.swift`, `UnifiedChatAPIService.swift`)
- [x] iOS: 添加 `@Published` 状态属性 (`UnifiedChatViewModel.swift`)
- [x] iOS: 添加 `StreamingStatusView` 组件
- [x] React: 更新 SSE 事件处理 (`api/index.ts`)
- [x] React: 添加 `StreamingStatusView` 组件 (`DermaChat.tsx`)

#### 阶段 4: 优化
- [x] 性能优化: 分块缓冲 (`_stream_chunked`)
- [x] 错误处理: 超时处理 (`asyncio.wait_for`)
- [x] 配置项: 添加 `STREAMING_TIMEOUT`, `STREAMING_QUEUE_SIZE`
- [x] 文档更新

### 关键实现文件

| 文件 | 修改内容 |
|------|---------|
| `backend/app/services/agents/react_base.py` | 添加 `run_stream()`, `_handle_reasoning_stream()`, `_generate_diagnosis_stream()`, `_stream_chunked()` |
| `backend/app/routes/sessions.py` | 添加超时处理、队列大小限制、错误恢复 |
| `backend/app/config.py` | 添加流式配置项 |
| `ios/.../Components/StreamingStatusView.swift` | 新增流式状态 UI 组件 |
| `ios/.../ViewModels/UnifiedChatViewModel.swift` | 添加 `isThinking`, `activeToolCalls`, `completedTools` 状态 |
| `frontend/src/pages/DermaChat.tsx` | 添加 `StreamingStatusView` 组件和事件处理 |

---

## 十、参考资料

- LangGraph 流式执行: https://langchain-ai.github.io/langgraph/concepts/low_level/#streaming
- Server-Sent Events: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- 通义千问流式 API: https://help.aliyun.com/zh/dashscope/developer-reference/api-details

---

**文档维护**: 本文档应在实施过程中持续更新，记录实际遇到的问题和解决方案。
