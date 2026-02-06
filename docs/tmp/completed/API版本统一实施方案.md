# API 版本统一实施方案

## 1. 执行摘要

### 1.1 项目背景

当前系统存在 V1 (`/sessions`) 和 V2 (`/v2/sessions`) 两套会话 API，造成代码冗余和维护成本增加。本方案旨在通过渐进式迁移策略，将系统统一到 V2 API，并最终清理 V1 代码。

### 1.2 核心发现

**后端现状：**
- V1 API 完整实现：6 个端点全部可用
- V2 API 部分实现：缺少 2 个关键端点（GET 列表端点）
- V2 使用更先进的 AgentRouterV2 架构

**iOS 客户端现状：**
- 当前主要使用 V1 API
- 已实现 V2 API 调用能力（UnifiedChatAPIServiceV2.swift）
- 切换工作相对简单

**前端现状：**
- 不使用 sessions API，直接使用专科 API
- 本次迁移对前端无影响

### 1.3 推荐方案

**方案：渐进式迁移到 V2 + 清理 V1**

| 阶段 | 内容 | 工期 |
|------|------|------|
| 阶段一 | 完善 V2 API（补充缺失端点） | 3-5 天 |
| 阶段二 | iOS 客户端迁移 | 5-7 天 |
| 阶段三 | 验证与监控 | 3-5 天 |
| 阶段四 | 清理 V1 API | 2-3 天 |
| 阶段五 | 文档更新 | 1 天 |
| **总计** | | **14-21 天** |

---

## 2. 实施时间表

### 2.1 总体时间表（20 个工作日）

```
┌─────────────────────────────────────────────────────────────────┐
│  W1    │  W2    │  W3    │  W4    │
│ 12345  │ 12345  │ 12345  │ 12345  │
├─────────────────────────────────────────────────────────────────┤
│ [阶段一]    │ [阶段二]           │ [阶段三]    │ [阶段四][五]  │
│ V2 完善     │ iOS 迁移           │ 验证测试    │ 清理+文档     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 详细任务分配

| 阶段 | 任务 | 预计工时 | 负责人 | 依赖 |
|------|------|----------|--------|------|
| 阶段一 | 添加 GET /v2/sessions 端点 | 0.5 天 | 后端 | 无 |
| 阶段一 | 添加 GET /v2/sessions/{id}/messages 端点 | 0.5 天 | 后端 | 无 |
| 阶段一 | V2 端点单元测试 | 1 天 | 后端 | 端点实现 |
| 阶段一 | V2 端点集成测试 | 1 天 | 后端 | 单元测试 |
| 阶段二 | iOS: 修改 APIConfig 端点配置 | 0.5 天 | iOS | 阶段一完成 |
| 阶段二 | iOS: 修改 APIService 调用逻辑 | 1 天 | iOS | 端点配置 |
| 阶段二 | iOS: 更新 ViewModel | 1 天 | iOS | APIService |
| 阶段二 | iOS: 本地功能测试 | 2 天 | iOS | ViewModel |
| 阶段三 | 后端 API 集成测试 | 1 天 | 后端 | 阶段二完成 |
| 阶段三 | iOS 端到端测试 | 2 天 | iOS | 后端测试 |
| 阶段三 | 小范围灰度测试 | 1 天 | 全员 | 端到端测试 |
| 阶段四 | 标记 V1 为 deprecated | 0.5 天 | 后端 | 阶段三完成 |
| 阶段四 | 删除 V1 路由代码 | 1 天 | 后端 | deprecation |
| 阶段四 | 删除 iOS V1 相关代码 | 1 天 | iOS | V1 删除 |
| 阶段五 | 更新 API 文档 | 0.5 天 | 后端 | 阶段四完成 |
| 阶段五 | 更新架构设计文档 | 0.5 天 | 后端 | API 文档 |

---

## 3. 阶段一：完善 V2 API（后端）

### 3.1 技术方案

#### 3.1.1 缺失端点分析

| 端点 | V1 状态 | V2 状态 | 优先级 |
|------|---------|---------|--------|
| GET /sessions | ✅ 已实现 | ❌ 缺失 | 高 |
| GET /sessions/{id}/messages | ✅ 已实现 | ❌ 缺失 | 高 |

#### 3.1.2 参考实现

V2 端点实现可参考 V1 代码，主要差异在于：
- V2 使用 `AgentRouterV2` 而非 `AgentRouter`
- V2 响应使用统一的 `AgentResponse` 格式
- V2 状态管理更简洁（`next_state` vs `agent_state`）

### 3.2 代码变更清单

#### 新增文件：无

#### 修改文件：`backend/app/routes/sessions_v2.py`

**变更 1：添加 GET /v2/sessions 端点**

```python
@router.get("", response_model=List[SessionResponse])
def get_sessions_v2(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户会话列表 (V2)

    与 V1 功能对等，返回当前用户的所有会话
    """
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(SessionModel.updated_at.desc()).all()

    result = []
    for session in sessions:
        doctor = db.query(Doctor).filter(Doctor.id == session.doctor_id).first() if session.doctor_id else None
        result.append(SessionResponse(
            session_id=session.id,
            doctor_id=session.doctor_id,
            doctor_name=doctor.name if doctor else "AI助手",
            agent_type=session.agent_type,
            last_message=session.last_message,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at
        ))
    return result
```

**变更 2：添加 GET /v2/sessions/{session_id}/messages 端点**

```python
@router.get("/{session_id}/messages", response_model=MessageListResponse)
def get_session_messages_v2(
    session_id: str,
    limit: int = 20,
    before: Optional[int] = None,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话消息列表 (V2)

    与 V1 功能对等，支持分页加载
    """
    from ..dependencies import TEST_MODE

    if TEST_MODE:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
    else:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id
        ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    query = db.query(Message).filter(Message.session_id == session_id)

    if before:
        query = query.filter(Message.id < before)

    messages = query.order_by(Message.created_at.desc()).limit(limit + 1).all()

    has_more = len(messages) > limit
    messages = messages[:limit]
    messages.reverse()

    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        has_more=has_more
    )
```

**变更 3：添加状态转换层（新增，处理旧会话兼容性）**

在文件顶部添加状态转换函数：

```python
# 在 sessions_v2.py 文件顶部添加

def migrate_v1_state_to_v2(v1_state: Optional[Dict]) -> Dict:
    """
    将 V1 状态转换为 V2 格式

    V1 字段 -> V2 字段映射：
    - questions_asked -> 删除（V2 不需要）
    - session_id -> 删除（V2 从 session 对象获取）
    - user_id -> 删除（V2 从 session 对象获取）
    - stage -> 保留（V2 也使用）
    - chief_complaint -> 保留（V2 也使用）
    - symptoms -> 保留
    - skin_location -> 保留
    - diagnosis_card -> 保留
    - advice_history -> 保留
    """
    if not v1_state:
        return {}

    # 处理 JSON 字符串情况（V1 可能存成字符串）
    if isinstance(v1_state, str):
        try:
            import json
            v1_state = json.loads(v1_state)
        except:
            return {}

    # V2 需要保留的状态字段
    v2_fields = {
        "stage", "chief_complaint", "symptoms",
        "skin_location", "diagnosis_card", "advice_history",
        "knowledge_refs", "reasoning_steps", "latest_analysis",
        "latest_interpretation"
    }

    return {k: v for k, v in v1_state.items() if k in v2_fields}
```

然后在 `send_message_v2` 函数中使用状态转换：

```python
# 修改 send_message_v2 中的状态恢复代码
# 原代码（约第 148 行）：
state = session.agent_state

# 修改为：
state = migrate_v1_state_to_v2(session.agent_state)
```

### 3.3 测试用例

| 用例 ID | 描述 | 前置条件 | 步骤 | 预期结果 |
|---------|------|----------|------|----------|
| V2-001 | 获取空会话列表 | 用户已登录，无会话 | GET /v2/sessions | 返回空数组 |
| V2-002 | 获取会话列表 | 用户有 3 个会话 | GET /v2/sessions | 返回 3 个会话，按更新时间倒序 |
| V2-003 | 获取消息列表 | 会话有 30 条消息 | GET /v2/sessions/{id}/messages?limit=20 | 返回 20 条，has_more=true |
| V2-004 | 分页加载 | 已加载前 20 条 | GET ...?limit=20&before={min_id} | 返回后续 10 条，has_more=false |
| V2-005 | 权限验证 | 用户 A 尝试获取用户 B 的会话 | GET /v2/sessions/{B的session_id}/messages | 返回 404 |
| **V2-M01** | **V1 会话用 V2 API** | **V1 创建的会话** | **POST /v2/sessions/{id}/messages** | **状态正确转换，正常响应** |
| **V2-M02** | **V1 空 agent_state** | **agent_state 为 None** | **POST /v2/sessions/{id}/messages** | **正常处理，返回响应** |
| **V2-M03** | **V1 JSON 字符串状态** | **agent_state 是 JSON 字符串** | **POST /v2/sessions/{id}/messages** | **正确解析，正常响应** |

### 3.4 验收标准

- [ ] GET /v2/sessions 返回格式与 V1 一致
- [ ] GET /v2/sessions/{id}/messages 返回格式与 V1 一致
- [ ] 单元测试覆盖率 > 80%
- [ ] 所有测试用例通过（包括 V2-M01 ~ V2-M03 兼容性测试）

---

## 4. 阶段二：iOS 客户端迁移

### 4.1 技术方案

#### 4.1.1 iOS API 使用现状

| 文件 | 当前使用 | 迁移目标 |
|------|----------|----------|
| APIConfig.swift | V1 端点 (/sessions) | V2 端点 (/v2/sessions) |
| APIService.swift | V1 调用 | 使用现有 V2 扩展 |
| UnifiedChatViewModel.swift | createUnifiedSession | createSessionV2 |

#### 4.1.2 V2 能力现状

iOS 已完成 V2 API 实现：
- `UnifiedChatAPIServiceV2.swift` - V2 端点完整实现
- `createSessionV2()` - 创建会话
- `sendMessageStreamingV2()` - 流式发送消息
- `getAgentCapabilitiesV2()` - 获取智能体能力

**结论：iOS 端代码已准备就绪，只需切换调用。**

### 4.2 代码变更清单

#### 修改文件 1：`APIConfig.swift`

```swift
// 修改前
static let sessions = "/sessions"
static func messages(sessionId: String) -> String {
    return "/sessions/\(sessionId)/messages"
}

// 修改后
static let sessions = "/v2/sessions"
static func messages(sessionId: String) -> String {
    return "/v2/sessions/\(sessionId)/messages"
}
```

#### 修改文件 2：`APIService.swift`

**方法 1：getSessions()**

```swift
// 修改前：使用 V1
func getSessions() async throws -> [SessionModel] {
    return try await makeRequest(endpoint: APIConfig.Endpoints.sessions, requiresAuth: true)
}

// 修改后：使用 V2（无需修改，因为 APIConfig.Endpoints.sessions 已更新）
func getSessions() async throws -> [SessionModel] {
    return try await makeRequest(endpoint: APIConfig.Endpoints.sessions, requiresAuth: true)
}
```

**方法 2：getMessages()**

```swift
// 同样，由于 APIConfig 更新，自动切换到 V2
```

#### 修改文件 3：`UnifiedChatViewModel.swift`

**方案选择 A：最小修改**

只需修改 `createUnifiedSession` 调用为 `createSessionV2`：

```swift
// 修改前
let session = try await apiService.createUnifiedSession(
    doctorId: doctorId,
    agentType: inferredAgentType
)

// 修改后
let session = try await apiService.createSessionV2(
    doctorId: doctorId,
    agentType: inferredAgentType
)
```

**方案选择 B：统一入口（推荐）**

在 `APIService.swift` 中添加统一方法，内部调用 V2：

```swift
func createUnifiedSession(doctorId: Int? = nil, agentType: AgentType? = nil) async throws -> UnifiedSessionResponse {
    // 现在内部调用 V2
    return try await createSessionV2(doctorId: doctorId, agentType: agentType)
}

func sendUnifiedMessageStreaming(
    sessionId: String,
    content: String,
    attachments: [MessageAttachment] = [],
    action: AgentAction = .conversation,
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (UnifiedMessageResponse) -> Void,
    onError: @escaping (Error) -> Void,
    isRetry: Bool = false
) async {
    // 现在内部调用 V2
    await sendMessageStreamingV2(
        sessionId: sessionId,
        content: content,
        attachments: attachments,
        action: action,
        onChunk: onChunk,
        onComplete: { v2Response in
            // 转换 V2 响应为统一格式
            onComplete(convertV2ToUnified(v2Response))
        },
        onError: onError,
        isRetry: isRetry
    )
}
```

### 4.3 测试用例

| 用例 ID | 描述 | 前置条件 | 步骤 | 预期结果 |
|---------|------|----------|------|----------|
| iOS-001 | 创建会话 | 用户已登录 | 选择医生，开始咨询 | 成功创建会话 |
| iOS-002 | 发送文本消息 | 会话已创建 | 输入文本，发送 | AI 正常回复 |
| iOS-003 | 流式响应显示 | 发送消息中 | 观察 AI 响应 | 文本逐字显示 |
| iOS-004 | 图片上传 | 选择皮肤分析 | 上传皮肤照片 | 成功分析 |
| iOS-005 | 会话列表加载 | 有历史会话 | 打开会话历史 | 显示所有会话 |
| iOS-006 | 消息历史加载 | 打开旧会话 | 加载消息 | 显示历史消息 |
| iOS-007 | 错误处理 | 网络断开 | 尝试发送消息 | 显示错误提示 |

### 4.4 验收标准

- [ ] 所有核心功能正常（创建会话、发送消息、接收回复）
- [ ] 流式响应正常显示
- [ ] 图片上传功能正常
- [ ] 会话列表和消息历史正常加载
- [ ] 错误处理正常工作

---

## 5. 阶段三：验证与监控

### 5.1 集成测试

#### 5.1.1 后端集成测试

```bash
# 运行 V2 API 集成测试
cd backend
pytest tests/routes/test_sessions_v2.py -v --cov=app/routes/sessions_v2
```

#### 5.1.2 前后端联调测试

| 测试项 | 测试命令/方式 | 预期结果 |
|--------|--------------|----------|
| 创建会话 | POST /v2/sessions | 返回 session_id |
| 发送消息 | POST /v2/sessions/{id}/messages | 返回 AI 响应 |
| 获取会话列表 | GET /v2/sessions | 返回会话数组 |
| 获取消息历史 | GET /v2/sessions/{id}/messages | 返回消息数组 |
| 流式响应 | Accept: text/event-stream | SSE 流正常 |

#### 5.1.3 iOS 端到端测试

**测试设备：**
- iPhone 模拟器（iOS 17+）
- 真机（如可用）

**测试流程：**
1. 用户登录
2. 选择科室/医生
3. 创建会话
4. 发送文本消息
5. 观察流式响应
6. 上传图片分析
7. 返回会话列表
8. 重新进入旧会话
9. 验证消息历史

### 5.2 灰度发布

#### 5.2.1 灰度策略

| 阶段 | 用户范围 | 持续时间 | 放宽条件 |
|------|----------|----------|----------|
| 灰度 1 | 内部测试人员（2-3人） | 2 天 | 无错误 |
| 灰度 2 | 10% 用户 | 3 天 | 错误率 < 0.1% |
| 灰度 3 | 50% 用户 | 3 天 | 错误率 < 0.1% |
| 全量 | 100% 用户 | - | 持续监控 |

#### 5.2.2 监控指标

| 指标 | 目标值 | 告警阈值 |
|------|--------|----------|
| API 成功率 | > 99.5% | < 99% |
| API 平均响应时间 | < 2s | > 3s |
| API 错误率 | < 0.5% | > 1% |
| 客户端崩溃率 | < 0.1% | > 0.2% |

### 5.3 回滚触发条件

**立即回滚：**
- API 错误率 > 5%
- 客户端崩溃率 > 1%
- 核心功能不可用

**评估后回滚：**
- API 错误率持续 > 1%
- 用户投诉激增

---

## 6. 阶段四：清理 V1 API

### 6.1 清理时机

**前置条件：**
- [ ] V2 API 已全量发布
- [ ] 监控指标稳定 2 周
- [ ] 无用户投诉或异常

### 6.2 后端清理

#### 6.2.1 代码删除清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/routes/sessions.py` | 删除 | V1 路由文件 |
| `backend/app/main.py` | 修改 | 移除 V1 路由注册 |
| `backend/app/services/agent_router.py` | 评估 | 如无其他引用则删除 |

#### 6.2.2 具体操作

**步骤 1：标记为 deprecated**

```python
# backend/app/routes/sessions.py

import warnings

@router.post("", response_model=SessionResponse, deprecated=True)
async def create_session(...):
    warnings.warn("V1 API is deprecated. Please use /v2/sessions instead.", DeprecationWarning)
    ...
```

**步骤 2：观察期（2 周）**

- 监控 V1 API 调用量
- 确认无异常调用

**步骤 3：删除代码**

```bash
# 删除 V1 路由文件
rm backend/app/routes/sessions.py

# 更新 main.py，移除 V1 路由注册
# from app.routes.sessions import router as sessions_router  # 删除这行
# app.include_router(sessions_router)  # 删除这行
```

### 6.3 iOS 清理

#### 6.3.1 代码删除清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `APIService.swift` | 修改 | 移除 V1 专用方法（如果存在） |
| `APIConfig.swift` | 清理 | 移除 V1 端点注释 |

#### 6.3.2 具体操作

**删除方法（如有）：**
- `createSessionV1()` - 如存在则删除
- `sendMessageV1()` - 如存在则删除

---

## 7. 阶段五：文档更新

### 7.1 更新文件清单

| 文档 | 更新内容 |
|------|----------|
| `docs/API文档.md` | 移除 V1 端点，更新为 V2 |
| `docs/架构设计.md` | 更新 API 架构说明 |
| `docs/配置指南.md` | 无需变更 |
| `docs/启动指南.md` | 无需变更 |

### 7.2 API 文档更新内容

#### 7.2.1 会话管理 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/v2/sessions` | POST | 创建会话 |
| `/v2/sessions` | GET | 获取会话列表 |
| `/v2/sessions/{id}/messages` | GET | 获取消息列表 |
| `/v2/sessions/{id}/messages` | POST | 发送消息 |
| `/v2/sessions/agents` | GET | 获取智能体列表 |
| `/v2/sessions/agents/{type}/capabilities` | GET | 获取智能体能力 |

#### 7.2.2 移除内容

- ~~`/sessions`~~ - 已废弃，请使用 `/v2/sessions`

---

## 8. 测试计划

### 8.1 单元测试

#### 8.1.1 后端单元测试

```bash
# 运行所有测试
cd backend
pytest tests/ -v

# 运行 V2 相关测试
pytest tests/routes/test_sessions_v2.py -v

# 覆盖率测试
pytest tests/routes/test_sessions_v2.py --cov=app/routes/sessions_v2 --cov-report=html
```

#### 8.1.2 iOS 单元测试

```bash
# 运行 iOS 测试
cd ios/xinlingyisheng
xcodebuild test -scheme xinlingyisheng -destination 'platform=iOS Simulator,name=iPhone 15'
```

### 8.2 集成测试

#### 8.2.1 API 集成测试脚本

```bash
#!/bin/bash
# api_integration_test.sh

BASE_URL="http://127.0.0.1:8100"
TOKEN="test_token"

# 1. 创建会话
echo "1. 创建会话..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/v2/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"doctor_id": 1}')
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo "会话ID: $SESSION_ID"

# 2. 发送消息
echo "2. 发送消息..."
curl -s -X POST "$BASE_URL/v2/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "你好"}'

# 3. 获取会话列表
echo "3. 获取会话列表..."
curl -s -X GET "$BASE_URL/v2/sessions" \
  -H "Authorization: Bearer $TOKEN"

# 4. 获取消息列表
echo "4. 获取消息列表..."
curl -s -X GET "$BASE_URL/v2/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN"
```

### 8.3 性能测试

```bash
# 使用 ab 进行压力测试
ab -n 1000 -c 10 -H "Authorization: Bearer test_token" \
   http://127.0.0.1:8100/v2/sessions

# 使用 wrk 进行测试
wrk -t4 -c100 -d30s --latency \
    -H "Authorization: Bearer test_token" \
    http://127.0.0.1:8100/v2/sessions
```

---

## 9. 回滚方案

### 9.1 回滚触发条件

| 条件 | 阈值 | 动作 |
|------|------|------|
| API 错误率 | > 5% | 立即回滚 |
| 客户端崩溃率 | > 1% | 立即回滚 |
| 核心功能不可用 | 任何 | 立即回滚 |
| API 响应时间 | > 5s 持续 10 分钟 | 评估回滚 |

### 9.2 回滚步骤

#### 9.2.1 iOS 回滚（最快，5 分钟内）

```swift
// APIService.swift
// 回滚：恢复使用 V1

func createUnifiedSession(...) async throws -> UnifiedSessionResponse {
    // 临时：恢复使用 V1
    return try await createSessionV1(doctorId: doctorId, agentType: agentType)
}
```

**发布热更新：**
1. 修改代码
2. 构建 TestFlight 版本
3. 提交审核（说明为紧急修复）

#### 9.2.2 后端回滚（需要重启服务）

```bash
# 方案 A：Git 回滚
git revert <commit_hash>
git push
# 服务器部署

# 方案 B：配置开关（推荐）
# backend/app/config.py
ENABLE_V2_API = False  # 切换回 V1
```

**推荐：预置配置开关**

```python
# backend/app/config.py
class Settings:
    # API 版本控制
    api_version: str = os.getenv("API_VERSION", "v2")  # v1 或 v2

# backend/app/routes/sessions.py
@router.post("", response_model=SessionResponse)
async def create_session(...):
    if settings.api_version == "v1":
        return await create_session_v1(...)
    else:
        return await create_session_v2(...)
```

### 9.3 回滚验证

| 验证项 | 验证方式 | 成功标准 |
|--------|----------|----------|
| API 可用性 | curl 测试 | 200 响应 |
| 错误率 | 监控指标 | < 0.5% |
| 用户反馈 | 客服渠道 | 无负面反馈 |

---

## 10. 风险评估

### 10.1 风险矩阵

| 风险 | 可能性 | 影响 | 风险等级 | 缓解措施 |
|------|--------|------|----------|----------|
| V2 API 隐式功能缺失 | 中 | 高 | **高** | 完整功能对比测试 |
| 旧会话状态不兼容 | 中 | 高 | **高** | 状态转换层（见 13.2.3） |
| iOS 响应格式不兼容 | 低 | 高 | 中 | iOS 已有完整 V2 实现 |
| 迁移期间服务中断 | 低 | 高 | 中 | 灰度发布 + 配置开关 |
| 用户数据丢失 | 极低 | 极高 | 中 | V1/V2 共享数据库 |
| 测试覆盖不全 | 中 | 中 | 中 | 代码审查 + 自动化测试 |
| 性能下降 | 低 | 中 | 低 | 性能基准测试 |

### 10.2 详细风险分析

#### 风险 1：V2 API 隐式功能缺失

**描述：** V2 可能缺少 V1 的某些隐式功能或边界情况处理。

**缓解措施：**
- 逐行对比 V1/V2 代码
- 使用相同测试用例验证两端
- 在灰度期密切关注用户反馈

#### 风险 2：旧会话状态不兼容（新增）

**描述：** V1 和 V2 的 `agent_state` 结构不同：
- V1 使用 `create_initial_state()` 创建包含 `session_id`、`user_id`、`questions_asked` 等字段的复杂状态
- V2 使用空字典 `{}` 作为初始状态
- 旧会话切换到 V2 API 时可能无法正确识别 V1 特有字段

**缓解措施：**
- 实现状态转换层 `migrate_v1_state_to_v2()`（见 13.2.3）
- 在 V2 端点中检测并转换旧状态格式
- 进行 T1-T5 兼容性测试（见 13.3.1）

#### 风险 3：iOS 响应格式不兼容

**描述：** V2 的 AgentResponse 格式可能与现有 iOS 解析逻辑不兼容。

**实际状况：**
- ✅ iOS 已有完整的 `AgentResponseV2.swift` 实现
- ✅ 与后端 `AgentResponse` schema 完全对应
- ✅ 已在 `UnifiedChatAPIServiceV2.swift` 中使用

**缓解措施：**
- 充分的单元测试
- 灰度测试期间验证
- 无需额外代码修改

#### 风险 4：迁移期间服务中断

**描述：** 切换过程中可能导致短暂的服务不可用。

**缓解措施：**
- 使用配置开关，无需重启服务
- V1/V2 并存期间逐步切换
- 准备快速回滚方案

---

## 11. 验收标准

### 11.1 方案完整性

- [ ] 时间表明确，每个阶段有明确的时间节点
- [ ] 代码变更清单完整，可执行
- [ ] 测试用例覆盖所有变更
- [ ] 回滚方案可行
- [ ] 风险已识别并有缓解措施

### 11.2 技术验收

#### 阶段一验收
- [ ] GET /v2/sessions 实现并测试通过
- [ ] GET /v2/sessions/{id}/messages 实现并测试通过
- [ ] 单元测试覆盖率 > 80%
- [ ] 与 V1 功能对等

#### 阶段二验收
- [ ] iOS 成功切换到 V2 API
- [ ] 所有核心功能正常
- [ ] 流式响应正常
- [ ] 本地测试通过

#### 阶段三验收
- [ ] 集成测试通过
- [ ] 灰度测试无异常
- [ ] 监控指标达标

#### 阶段四验收
- [ ] V1 代码已删除
- [ ] 无遗留引用
- [ ] 文档已更新

### 11.3 业务验收

- [ ] 用户无感知迁移
- [ ] 无功能降级
- [ ] 性能无下降
- [ ] 无新增 bug

---

## 12. 附录

### 附录 A：代码变更详细清单

#### A.1 后端变更

```
修改:
├── backend/app/routes/sessions_v2.py
│   ├── 新增: GET /v2/sessions 端点
│   └── 新增: GET /v2/sessions/{id}/messages 端点
│
修改（阶段四）:
├── backend/app/main.py
│   └── 删除: V1 路由注册
│
删除（阶段四）:
├── backend/app/routes/sessions.py
```

#### A.2 iOS 变更

```
修改:
├── APIConfig.swift
│   ├── sessions: /sessions → /v2/sessions
│   └── messages(sessionId): /sessions/{id}/messages → /v2/sessions/{id}/messages
│
修改（可选）:
├── APIService.swift
│   ├── createUnifiedSession: 内部调用 createSessionV2
│   └── sendUnifiedMessageStreaming: 内部调用 sendMessageStreamingV2
│
删除（阶段四）:
├── 任何 V1 专用方法（如存在）
```

### 附录 B：测试用例详细清单

#### B.1 后端测试用例

| 用例 ID | API | 方法 | 参数 | 预期 HTTP | 预期响应 |
|---------|-----|------|------|-----------|----------|
| V2-B-001 | /v2/sessions | POST | {"doctor_id": 1} | 201 | SessionResponse |
| V2-B-002 | /v2/sessions | GET | - | 200 | SessionResponse[] |
| V2-B-003 | /v2/sessions/{id}/messages | GET | limit=20 | 200 | MessageListResponse |
| V2-B-004 | /v2/sessions/{id}/messages | GET | limit=20&before=100 | 200 | MessageListResponse |
| V2-B-005 | /v2/sessions/{id}/messages | POST | {"content": "test"} | 200 | AgentResponse |

#### B.2 iOS 测试用例

| 用例 ID | 场景 | 操作 | 预期 |
|---------|------|------|------|
| V2-I-001 | 新用户首次使用 | 选择医生 → 创建会话 → 发送消息 | AI 正常回复 |
| V2-I-002 | 老用户查看历史 | 打开会话列表 → 选择会话 | 显示历史消息 |
| V2-I-003 | 皮肤分析 | 点击皮肤分析 → 上传照片 | 返回分析结果 |
| V2-I-004 | 网络异常 | 断网后发送消息 | 显示错误提示 |
| V2-I-005 | Token 过期 | Token 过期后操作 | 自动刷新并重试 |

### 附录 C：监控指标

#### C.1 API 监控

| 指标 | 采集方式 | 告警阈值 |
|------|----------|----------|
| QPS | 日志统计 | - |
| 响应时间 (P50) | 日志统计 | < 1s |
| 响应时间 (P99) | 日志统计 | < 3s |
| 错误率 | 日志统计 | < 0.5% |
| 超时率 | 日志统计 | < 0.1% |

#### C.2 客户端监控

| 指标 | 采集方式 | 告警阈值 |
|------|----------|----------|
| API 调用成功率 | 客户端上报 | > 99% |
| 崩溃率 | Crashlytics | < 0.1% |
| ANR 率 | 客户端上报 | < 0.5% |

### 附录 D：V1 vs V2 API 对照表

| 功能 | V1 端点 | V2 端点 | 变化 |
|------|---------|---------|------|
| 创建会话 | POST /sessions | POST /v2/sessions | 响应格式统一 |
| 获取会话列表 | GET /sessions | GET /v2/sessions | 无变化 |
| 获取消息 | GET /sessions/{id}/messages | GET /v2/sessions/{id}/messages | 无变化 |
| 发送消息 | POST /sessions/{id}/messages | POST /v2/sessions/{id}/messages | 响应格式统一 |
| 智能体列表 | GET /sessions/agents | GET /v2/sessions/agents | 无变化 |
| 智能体能力 | GET /sessions/agents/{type}/capabilities | GET /v2/sessions/agents/{type}/capabilities | 无变化 |

---

## 13. V1 与 V2 关键差异分析（新增）

### 13.1 响应格式差异

#### 13.1.1 非流式响应差异

| 对比项 | V1 响应格式 | V2 响应格式 |
|--------|------------|------------|
| 结构 | `{"user_message": {...}, "ai_message": {...}}` | `AgentResponse` 统一格式 |
| AI 内容路径 | `ai_message.content` | `message` (直接) |
| 结构化数据 | `structured_data` 字段 | `specialty_data` 字段 |
| 状态管理 | 返回完整的 `agent_state` | `next_state` 字段 |
| 阶段信息 | 无 | `stage` 字段 |
| 进度信息 | 无 | `progress` 字段 |

**V1 响应示例：**
```json
{
  "user_message": {
    "id": 123,
    "content": "我手上有红疹",
    "sender": "user"
  },
  "ai_message": {
    "id": 124,
    "content": "请问红疹持续多久了？",
    "sender": "ai",
    "structured_data": {
      "type": "skin_analysis",
      "data": {...}
    }
  }
}
```

**V2 响应示例：**
```json
{
  "message": "请问红疹持续多久了？",
  "stage": "collecting",
  "progress": 20,
  "quick_options": ["3天以内", "一周左右", "超过两周"],
  "specialty_data": {
    "diagnosis_card": {...}
  },
  "next_state": {...}
}
```

#### 13.1.2 流式响应差异

| 事件类型 | V1 | V2 |
|----------|-----|-----|
| meta | ✅ 相同 | ✅ 相同 |
| chunk | ✅ 相同 | ✅ 相同 |
| complete | 自定义格式 | `AgentResponse` 格式 |
| error | ✅ 相同 | ✅ 相同 |

**V1 complete 事件：**
```json
{
  "message": "回答内容",
  "structured_data": {...},
  "advice_history": [...],
  "diagnosis_card": {...}
}
```

**V2 complete 事件：**
```json
{
  "message": "回答内容",
  "stage": "completed",
  "progress": 100,
  "specialty_data": {...},
  "next_state": {...}
}
```

#### 13.1.3 iOS 端兼容性处理

iOS 已有完整的 V2 响应解析实现：

```swift
// AgentResponseV2.swift - 与后端 AgentResponse schema 完全对应
struct AgentResponseV2: Codable {
    let message: String          // 对应后端 message
    let stage: String            // 对应后端 stage
    let progress: Int            // 对应后端 progress
    let quickOptions: [String]   // 对应后端 quick_options
    let specialtyData: SpecialtyDataV2?  // 对应后端 specialty_data
    let nextState: [String: AnyCodable]  // 对应后端 next_state
}
```

**结论：** iOS 端已准备就绪，无需额外解析逻辑修改。

### 13.2 状态初始化差异

#### 13.2.1 创建会话时的状态初始化

| 对比项 | V1 | V2 |
|--------|-----|-----|
| 初始状态 | `create_initial_state()` 创建复杂状态 | `{}` 空字典 |
| session_id | 包含在状态中 | 不包含在状态中 |
| user_id | 包含在状态中 | 不包含在状态中 |
| questions_asked | 初始化为 0 | 不存在 |

**V1 代码：**
```python
# sessions.py:70-77
initial_state = create_initial_state(
    session_id=session_id,
    user_id=current_user.id,
    agent_type=agent_type
)
session.agent_state = initial_state
```

**V2 代码：**
```python
# sessions_v2.py:59-66
session = SessionModel(
    id=session_id,
    user_id=current_user.id,
    doctor_id=request.doctor_id,
    agent_type=agent_type,
    agent_state={}  # V2: 初始状态为空字典
)
```

#### 13.2.2 智能体调用时的状态恢复

| 对比项 | V1 | V2 |
|--------|-----|-----|
| 状态检查 | 打印详细调试信息 | 无调试信息 |
| 状态为空时 | 调用 `agent.create_initial_state()` | 直接使用空字典 `{}` |
| JSON 处理 | 处理字符串类型的状态 | 无需处理（V2 始终是 dict） |

**影响分析：**
- ✅ **好消息**：V2 的 `AgentRouterV2.get_agent()` 内部会自动处理空状态
- ⚠️ **风险**：从 V1 迁移的旧会话，其 `agent_state` 可能包含 V1 特有的字段（如 `questions_asked`），V2 智能体可能不识别

#### 13.2.3 旧会话兼容性方案

**方案 A：状态转换层（推荐）**

在 V2 端点中添加状态转换逻辑：

```python
def migrate_v1_state_to_v2(v1_state: Dict) -> Dict:
    """
    将 V1 状态转换为 V2 格式

    V1 字段 -> V2 字段映射：
    - questions_asked -> 删除（V2 不需要）
    - stage -> 保留（V2 也使用）
    - chief_complaint -> 保留（V2 也使用）
    """
    if not v1_state:
        return {}

    # V2 只需要的状态字段
    v2_fields = [
        "stage", "chief_complaint", "symptoms",
        "skin_location", "diagnosis_card", "advice_history"
    ]

    return {k: v for k, v in v1_state.items() if k in v2_fields}
```

**方案 B：标记迁移（简单）**

在会话表中增加 `api_version` 字段：

```python
# 创建新会话时标记版本
session = SessionModel(
    ...
    api_version="v2"  # 新字段
)

# 读取时检查版本
if session.api_version == "v1":
    state = migrate_v1_state_to_v2(session.agent_state)
else:
    state = session.agent_state or {}
```

### 13.3 旧会话兼容性测试

#### 13.3.1 测试场景

| 场景 | 描述 | 预期结果 |
|------|------|----------|
| T1: V1 会话继续使用 V1 | 创建 V1 会话，用 V1 发送消息 | 正常工作 |
| T2: V1 会话迁移到 V2 | 创建 V1 会话，用 V2 发送消息 | 状态正确转换 |
| T3: V2 会话回退到 V1 | 创建 V2 会话，用 V1 发送消息 | 状态兼容或报错 |
| T4: 空 agent_state | agent_state 为 None 的会话 | V2 正常处理 |
| T5: JSON 字符串状态 | agent_state 是 JSON 字符串 | V2 正确解析 |

#### 13.3.2 测试脚本

```python
# test_migration.py
import pytest
import requests

BASE_URL = "http://127.0.0.1:8100"
TOKEN = "test_token"

def test_v1_session_with_v2_api():
    """用 V2 API 访问 V1 创建的会话"""

    # 1. 用 V1 创建会话
    response = requests.post(
        f"{BASE_URL}/sessions",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"doctor_id": 1}
    )
    session_id = response.json()["session_id"]
    print(f"V1 会话创建: {session_id}")

    # 2. 用 V2 发送消息
    response = requests.post(
        f"{BASE_URL}/v2/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"content": "你好"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    print("V2 API 响应正常")

def test_v2_session_with_v1_api():
    """用 V1 API 访问 V2 创建的会话"""

    # 1. 用 V2 创建会话
    response = requests.post(
        f"{BASE_URL}/v2/sessions",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"doctor_id": 1}
    )
    session_id = response.json()["session_id"]
    print(f"V2 会话创建: {session_id}")

    # 2. 用 V1 发送消息
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"content": "你好"}
    )
    # 预期：V1 应该能处理 V2 的空状态
    assert response.status_code == 200
    print("V1 API 响应正常")

def test_empty_agent_state():
    """测试空 agent_state 的处理"""

    # 直接操作数据库，创建空状态的会话
    # ...（数据库操作代码）

    # 用 V2 发送消息
    # ...（API 调用代码）

    # 验证响应
    assert "message" in response.json()
```

### 13.4 配置开关实现（完善）

#### 13.4.1 后端配置开关

**文件：`backend/app/config.py`**

```python
class Settings(BaseSettings):
    # ... 现有配置 ...

    # ========== API 版本控制 ==========
    api_version: str = os.getenv("API_VERSION", "v2")  # "v1" 或 "v2"
    enable_v2_only_mode: bool = os.getenv("ENABLE_V2_ONLY", "false").lower() == "true"

    @property
    def use_v2_api(self) -> bool:
        """是否使用 V2 API（兼容性属性）"""
        return self.api_version == "v2"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**文件：`.env`（可选配置）**

```bash
# API 版本控制（不设置则默认 v2）
# API_VERSION=v1

# 强制启用 V2（禁用 V1）
# ENABLE_V2_ONLY=true
```

#### 13.4.2 动态路由切换

**文件：`backend/app/main.py`**

```python
from app.config import settings
from app.routes.sessions import router as sessions_v1_router
from app.routes.sessions_v2 import router as sessions_v2_router

# ========== API 版本路由注册 ==========

# 方案 A：基于环境变量（推荐用于灰度）
if settings.enable_v2_only_mode:
    # 仅启用 V2
    app.include_router(sessions_v2_router)
    logging.info("✅ API 模式: V2 ONLY（V1 已禁用）")
else:
    # V1 和 V2 同时启用
    app.include_router(sessions_v1_router)
    app.include_router(sessions_v2_router)
    logging.info("✅ API 模式: V1 + V2 并存")

# 方案 B：基于请求头（推荐用于 A/B 测试）
from fastapi import Header

@app.api_route("/sessions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def sessions_proxy(
    path: str,
    request: Request,
    x_api_version: str = Header(None)
):
    """根据请求头动态路由"""

    # 优先使用请求头指定的版本
    version = x_api_version or settings.api_version

    if version == "v2":
        # 转发到 V2 路由
        return await sessions_v2_router.handle_request(request, path)
    else:
        # 转发到 V1 路由
        return await sessions_v1_router.handle_request(request, path)
```

#### 13.4.3 iOS 端配置开关

**文件：`ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`**

```swift
struct APIConfig {
    // ========== API 版本控制 ==========
    #if DEBUG
    /// 调试模式：可通过环境变量或 Remote Config 切换
    static var apiVersion: String {
        // 优先使用远程配置（支持热切换）
        return RemoteConfig.shared.getString(key: "api_version") ?? "v2"
    }
    #else
    /// 生产模式：编译时确定
    static let apiVersion = "v2"
    #endif

    // ========== 端点配置（动态） ==========
    struct Endpoints {
        static var sessions: String {
            return "/\(apiVersion)/sessions"
        }

        static func messages(sessionId: String) -> String {
            return "/\(apiVersion)/sessions/\(sessionId)/messages"
        }

        static var agents: String {
            return "/\(apiVersion)/sessions/agents"
        }

        static func agentCapabilities(agentType: String) -> String {
            return "/\(apiVersion)/sessions/agents/\(agentType)/capabilities"
        }
    }
}
```

#### 13.4.4 Firebase Remote Config（可选）

如果项目已集成 Firebase，可使用远程配置实现无发布切换：

```swift
// RemoteConfigManager.swift
import FirebaseRemoteConfig

class RemoteConfigManager {
    static let shared = RemoteConfigManager()

    private let remoteConfig = RemoteConfig.remoteConfig()

    func fetchAndActivate() {
        let settings = RemoteConfigSettings()
        settings.minimumFetchInterval = 300  // 5 分钟
        remoteConfig.configSettings = settings

        remoteConfig.fetchAndActivate { status, error in
            if let error = error {
                print("RemoteConfig fetch error: \(error)")
                return
            }
            print("RemoteConfig activated: api_version = \(self.apiVersion)")
        }
    }

    var apiVersion: String {
        return remoteConfig.configValue(forKey: "api_version").stringValue ?? "v2"
    }

    var useV2API: Bool {
        return apiVersion == "v2"
    }
}
```

---

## 14. 结论

本实施方案通过渐进式迁移策略，在 14-21 个工作日内完成 API 版本统一。方案设计充分考虑了风险控制和回滚能力，确保迁移过程平滑、可控。

**关键成功因素：**
1. V2 缺失端点的快速实现
2. iOS 端已有的 V2 实现基础
3. 完善的测试覆盖（包括旧会话兼容性）
4. 灰度发布策略
5. 配置开关实现快速回滚

**预期收益：**
- 统一架构，简化维护
- 代码质量提升
- 删除冗余代码
- 为未来功能扩展奠定基础

**风险缓解：**
- 响应格式差异：iOS 已有完整的 `AgentResponseV2` 解析实现
- 状态初始化差异：添加状态转换层处理旧会话
- 兼容性风险：通过灰度测试及早发现问题
- 回滚能力：配置开关支持 5 分钟内快速切换

---

**文档版本：** 1.1
**创建日期：** 2026-02-03
**更新日期：** 2026-02-03
**作者：** Claude AI Agent
**审批状态：** 待审批
