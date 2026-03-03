# Agentic Subagent Phase 1 契约文档

## 1. 目标与范围

本阶段目标是定义 `home-health-backend` 与 `home-health-ai` 的统一交互契约，并定义 AI 内部工具层契约，确保：

- 问诊由主智能体主导（非固定工作流）
- 数据通过工具读写（不直连业务存储）
- 支持 subagent 模式（先落地 retrieval subagent）
- 支持历史记忆、幂等、可观测、可回退

本阶段不包含业务逻辑实现代码，仅定义接口和运行语义。

## 2. 服务边界

- `home-health-backend`
  - 会话与消息主存储（唯一真源）
  - 鉴权、用户权限、灰度路由
  - 调用 `home-health-ai` 获取回复
- `home-health-ai`
  - 主智能体决策、subagent 调度、工具调用
  - 不直接写业务数据库
  - 返回自然语言回复与最小内部元数据
- `medical-knowledge-service`
  - 向量检索服务，仅作为 AI 工具依赖

## 3. Northbound API（backend -> ai）

### 3.1 Endpoint

- `POST /v1/chat/respond`
- `Content-Type: application/json`
- 鉴权：`Authorization: Bearer <internal_service_token>`

### 3.2 请求体（Request）

```json
{
  "request_id": "req_20260227_xxx",
  "session_id": "uuid",
  "turn_index": 6,
  "user_id": "u_12345",
  "agent_type": "general",
  "locale": "zh-CN",
  "stream": false,
  "user_message": "我喉咙很疼，晚上卧室更严重",
  "history": [
    {"role": "user", "content": "..." },
    {"role": "assistant", "content": "..."}
  ],
  "attachments": [],
  "client_context": {
    "timezone": "America/Los_Angeles",
    "channel": "web"
  },
  "debug": false
}
```

字段约束：

- `request_id`：必填，幂等键（同 `session_id + turn_index + request_id` 不可重复执行）
- `turn_index`：必填，严格递增
- `history`：建议最近 12-20 条消息；超长由 backend 截断
- `user_message`：必填，当前用户输入
- `stream`：Phase 1 固定 `false`（流式在后续阶段）

### 3.3 响应体（Response）

```json
{
  "request_id": "req_20260227_xxx",
  "session_id": "uuid",
  "turn_index": 6,
  "assistant_message": "自然语言回复",
  "risk_level": "low",
  "quick_options": ["有发热", "无发热", "不确定"],
  "memory_patch": {
    "facts": ["喉咙痛3天", "夜间卧室加重"],
    "summary_delta": "症状以咽痛为主，需继续确认发热和吞咽困难",
    "profile_delta": {}
  },
  "citations": [
    {"id": "E1", "source": "kb", "snippet": "..." }
  ],
  "tool_trace": [
    {"name": "memory.read", "status": "ok", "latency_ms": 8},
    {"name": "subagent.retrieval", "status": "ok", "latency_ms": 230}
  ],
  "metrics": {
    "total_ms": 13840,
    "llm_ms": 12600,
    "tools_ms": 248,
    "model_calls": 1
  },
  "error": null
}
```

响应约束：

- `assistant_message` 必须可直接面向用户展示（禁止错误栈）
- `memory_patch` 是建议写入，不是 AI 直接落库
- `tool_trace` 与 `metrics` 仅内部可见，前端默认不展示

## 4. Southbound Tool 契约（ai -> tools）

## 4.1 memory.read

用途：读取会话记忆层（近期消息、滚动摘要、长期画像）

输入：

```json
{
  "session_id": "uuid",
  "user_id": "u_12345",
  "max_recent_messages": 20,
  "include_summary": true,
  "include_profile": true
}
```

输出：

```json
{
  "recent_messages": [{"role":"user","content":"..."}],
  "rolling_summary": "最近问诊摘要",
  "profile_memory": {"allergy": [], "chronic_history": []},
  "version": 12
}
```

## 4.2 memory.write

用途：写入主智能体返回的记忆增量（由 backend 执行持久化）

输入：

```json
{
  "session_id": "uuid",
  "user_id": "u_12345",
  "turn_index": 6,
  "request_id": "req_20260227_xxx",
  "memory_patch": {
    "facts": ["..."],
    "summary_delta": "...",
    "profile_delta": {}
  }
}
```

输出：

```json
{
  "applied": true,
  "new_version": 13
}
```

## 4.3 kb.search

用途：知识检索工具（retrieval subagent 可调用）

输入：

```json
{
  "query": "咽痛 夜间加重 不通风",
  "specialty": "general",
  "top_k": 5,
  "score_threshold": 0.0
}
```

输出：

```json
{
  "count": 3,
  "results": [
    {"content":"...", "score":0.73, "metadata":{"source":"..."}}
  ]
}
```

## 4.4 audit.log

用途：记录关键调用链路与异常，支持回放和审计

输入：

```json
{
  "request_id": "req_20260227_xxx",
  "session_id": "uuid",
  "turn_index": 6,
  "event": "tool_call",
  "payload": {"tool":"kb.search","status":"ok","latency_ms":230}
}
```

输出：

```json
{"ok": true}
```

## 5. Subagent 契约

Phase 1 只保留一个子智能体：`retrieval_subagent`

输入：

```json
{
  "question": "我喉咙疼是否和空气有关",
  "context": "最近对话摘要与关键症状",
  "specialty": "general",
  "top_k": 5
}
```

输出：

```json
{
  "evidence_bundle": {
    "summary": "可能与刺激性环境和上呼吸道炎症相关",
    "confidence": 0.71,
    "items": [
      {"id":"E1","snippet":"...","source":"kb","score":0.78}
    ],
    "conflicts": []
  }
}
```

约束：

- subagent 不直接面向用户输出
- subagent 不写会话数据
- 主智能体决定是否采纳证据

## 6. 错误码规范

统一错误对象：

```json
{
  "code": "AI_TIMEOUT",
  "message": "upstream model timeout",
  "retryable": true
}
```

错误码清单：

- `AI_BAD_REQUEST`：请求参数非法（4xx，不重试）
- `AI_UNAUTHORIZED`：内部鉴权失败（401/403，不重试）
- `AI_TIMEOUT`：模型或工具超时（可重试 1 次）
- `AI_UPSTREAM_5XX`：上游服务异常（可重试 1 次）
- `AI_OVERLOADED`：限流触发（429，可退避重试）
- `AI_INTERNAL_ERROR`：未知错误（可重试 1 次）

## 7. 超时、重试、熔断语义

- 总预算：`20s`
- 主模型调用预算：`14s`
- 工具总预算：`4s`
- 单次检索工具预算：`2.5s`
- 内部重试：仅针对 `timeout/5xx/429`，最多 `1` 次，指数退避 `200-500ms`
- 熔断：连续失败 `5` 次后，`60s` 内跳过非关键工具调用

## 8. 降级与兜底语义

当工具或模型失败时：

- 不允许返回 `[ERROR]`、`timed out` 给用户
- 返回自然语言安全兜底回复（继续问关键问题或给保守建议）
- 在 `error` 字段记录机器可读错误码
- `tool_trace` 必须记录降级事实（`status=degraded`）

## 9. 幂等与并发控制

- 幂等键：`session_id + turn_index + request_id`
- 同一幂等键重复请求，返回首次成功结果（不重复执行模型调用）
- 若并发写同一 `turn_index`，后到请求返回 `AI_BAD_REQUEST`

## 10. 可观测字段

每轮至少记录：

- `request_id/session_id/turn_index`
- `model_name/model_calls/llm_ms`
- `tool_calls/tools_ms`
- `total_ms`
- `degraded`（是否降级）
- `error_code`（若失败）

## 11. Phase 1 完成判定

满足以下条件才算完成：

- backend 与 ai 的 `respond` 契约已联调通过
- 4 个工具契约可用（memory.read/write, kb.search, audit.log）
- 幂等、超时、降级语义已按文档实现
- 日志可完整回放一次请求调用链

