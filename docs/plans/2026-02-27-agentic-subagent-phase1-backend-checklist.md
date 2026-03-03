# Agentic Subagent Phase 1 Backend 改造清单（逐文件）

## 1. 目标

本清单用于把 `home-health-backend` 接入独立 `home-health-ai` 服务，并保持以下约束：

- 问诊路径统一走远端 AI（可灰度）
- backend 保持会话与消息主存储
- backend 只做编排、鉴权、持久化、回滚
- 数据由 AI 工具层控制（backend 不再做医疗语义判断）

## 2. 实施顺序（必须按序）

1. 配置与开关
2. AI 客户端与 schema
3. `/sessions/{id}/messages` 路由接线
4. 测试与脚本
5. 发布与回滚演练

## 3. 逐文件改造

## 3.1 配置层

文件：`backend/app/config.py`

改造项：

- 新增 AI 网关配置：
  - `AI_ENGINE_MODE`（`legacy|remote_ai|hybrid_shadow`，默认 `legacy`）
  - `AI_SERVICE_URL`（默认 `http://home-health-ai:8300`）
  - `AI_SERVICE_TOKEN`（内部服务鉴权）
  - `AI_SERVICE_TIMEOUT`（建议 `20` 秒）
  - `AI_SERVICE_CONNECT_TIMEOUT`（建议 `3` 秒）
  - `AI_SERVICE_MAX_RETRIES`（建议 `1`）
  - `AI_SERVICE_RETRY_BACKOFF_MS`（建议 `200`）
- 新增配置校验：
  - `AI_ENGINE_MODE=remote_ai` 时，`AI_SERVICE_URL` 与 `AI_SERVICE_TOKEN` 必填

验收点：

- 配置缺失时启动即报错（生产模式）
- 配置齐全时服务正常启动

---

文件：`backend/.env.example`

改造项：

- 增加 Phase 1 环境变量示例：
  - `AI_ENGINE_MODE=remote_ai`
  - `AI_SERVICE_URL=http://home-health-ai:8300`
  - `AI_SERVICE_TOKEN=change-me-internal-token`
  - `AI_SERVICE_TIMEOUT=20`
  - `AI_SERVICE_CONNECT_TIMEOUT=3`
  - `AI_SERVICE_MAX_RETRIES=1`
  - `AI_SERVICE_RETRY_BACKOFF_MS=200`

验收点：

- 新成员按 `.env.example` 可完成本地启动

---

文件：`docker-compose.yml`

改造项：

- `backend` 服务注入 AI 相关环境变量透传
- 预留 `home-health-ai` 服务占位（Phase 1 可先指向外部地址，Phase 2 再本仓落地）
- `depends_on` 增加可选 AI 依赖（若同编排部署）

验收点：

- `docker inspect home-health-backend` 可看到完整 AI 配置

## 3.2 后端 AI 适配层

文件：`backend/app/schemas/ai_gateway.py`（新建）

改造项：

- 定义与 OpenAPI 对齐的 schema：
  - `ChatRespondRequest`
  - `ChatRespondResponse`
  - `ErrorObject`
  - `ToolTraceItem`
  - `RespondMetrics`
- 枚举值与 `docs/plans/2026-02-27-agentic-subagent-phase1-openapi.yaml` 一致

验收点：

- schema 单测可通过合法/非法 payload 校验

---

文件：`backend/app/services/ai_gateway/client.py`（新建）

改造项：

- 封装 `POST /v1/chat/respond`
- 统一加头：
  - `Authorization: Bearer <AI_SERVICE_TOKEN>`
  - `Content-Type: application/json`
- 支持：
  - 超时
  - 1 次可重试（`timeout/5xx/429`）
  - 错误码归一化（映射成 `AI_TIMEOUT` 等）
- 返回结构化结果，不向上抛原始上游错误文本

验收点：

- 模拟 200/400/401/429/500 响应均可稳定映射

---

文件：`backend/app/services/ai_gateway/mapper.py`（新建）

改造项：

- 输入：`session + state + recent messages + request`
- 输出：`ChatRespondRequest`
- 负责字段映射：
  - `request_id`（无则生成）
  - `turn_index`（按会话消息计算或状态维护）
  - `history`（限制最近 N 条，建议 20）
- 输出裁剪与脱敏（去除不必要内部字段）

验收点：

- 相同输入稳定产出相同请求体（除 request_id）

## 3.3 路由接线

文件：`backend/app/routes/sessions.py`

改造项：

- 在 `send_message` 中增加引擎模式分支：
  - `legacy`：保持现状
  - `remote_ai`：调用 `AIGatewayClient`
  - `hybrid_shadow`：主回 legacy，同时旁路 remote_ai 仅记录对比
- `remote_ai` 模式下的行为：
  - 先保存用户消息（保持主存一致）
  - 调用 AI 服务
  - 把返回的 `assistant_message/risk_level/quick_options/...` 映射为现有 `AgentResponse`
  - 保存 AI 消息与 `session.agent_state`（写入 `memory_patch/tool_trace/metrics`）
- 错误兜底：
  - 绝不把 `[ERROR]`/`timed out` 返回用户
  - 使用自然语言安全兜底回复
- 幂等：
  - 以 `session_id + turn_index + request_id` 做去重（Phase 1 先存 `session.agent_state.idempotency_cache`）
- SSE（`text/event-stream`）兼容：
  - Phase 1 若 `remote_ai` 且无流式，返回单次 chunk + complete 事件

验收点：

- `remote_ai` 下 `/sessions/{id}/messages` 仍返回当前前端可消费格式
- 同幂等键重复请求不重复生成回复

## 3.4 数据模型（Phase 1 采用无迁移方案）

文件：`backend/app/models/message.py`、`backend/app/models/session.py`

改造项：

- Phase 1 不改表结构
- 新增数据落在：
  - `messages.structured_data`（保存 tool_trace/metrics/citations）
  - `sessions.agent_state`（保存 turn_index、idempotency_cache、memory_patch 摘要）

验收点：

- 不执行数据库迁移也可跑通完整链路

备注：

- Phase 2 再评估是否引入显式字段（如 `request_id`, `turn_index`）与索引优化

## 3.5 测试与验证

文件：`backend/test/test_sessions_api.py`

改造项：

- 新增 `remote_ai` 模式用例：
  - 成功路径：200 回包映射正确
  - 失败路径：上游 timeout/500 时返回自然语言兜底
  - 幂等路径：重复 request_id 返回同结果
  - 鉴权失败路径：映射 `AI_UNAUTHORIZED`

验收点：

- `sessions` 关键回归测试通过

---

文件：`backend/scripts/agentic_gray_eval.py`

改造项：

- 保持现有脚本入口不变
- 增加 `--engine-mode remote_ai|legacy` 参数
- 报告增加字段：
  - `engine_mode`
  - `timeouts`
  - `fallback_count`
  - `p95_latency_ms`

验收点：

- 能对比 legacy 与 remote_ai 两条路径的质量与稳定性

## 4. 开关与回滚策略

配置开关：

- `AI_ENGINE_MODE=legacy|remote_ai|hybrid_shadow`

回滚策略：

- 任何异常直接改回 `legacy` 并重启 backend
- `hybrid_shadow` 用于线上对比，不影响用户主回包

回滚触发阈值（建议）：

- 15 分钟窗口内 `AI_TIMEOUT` > 5%
- 用户可见兜底回复比例 > 10%
- `/sessions/messages` P95 > 25 秒

## 5. Definition of Done（Backend 侧）

全部满足才可进入 Phase 2：

- OpenAPI 契约字段在 backend 实现中 1:1 对齐
- `remote_ai` 模式在本地与 docker 环境可跑通
- sessions 回归测试通过
- 跑批脚本可生成 remote_ai 对标报告
- 可在 5 分钟内通过配置开关回滚至 legacy

