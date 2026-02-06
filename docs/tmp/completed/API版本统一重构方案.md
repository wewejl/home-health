# API 版本统一重构方案

## 1. 执行摘要

通过对系统中的 V1 和 V2 两套 API 版本进行全面分析，发现以下关键情况：

1. **后端现状**：存在完整的 V1 和 V2 两套 API，V2 使用了新的多智能体架构
2. **前端使用**：主要使用 dermatology 专科 API (DERMA)，未使用 sessions API
3. **iOS 使用**：同时支持 V1 和 V2，但主要使用 V1 API
4. **未使用 API**：sessions V1 和 V2 的多个端点未被客户端使用

## 2. 现状分析

### 2.1 后端 API 现状

#### V1 API (`/sessions`) - `backend/app/routes/sessions.py`

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/sessions` | POST | 创建会话 | iOS 使用 |
| `/sessions` | GET | 获取会话列表 | iOS 使用 |
| `/sessions/{session_id}/messages` | GET | 获取消息列表 | iOS 使用 |
| `/sessions/{session_id}/messages` | POST | 发送消息 | iOS 使用 |
| `/sessions/agents` | GET | 获取智能体列表 | 未使用 |
| `/sessions/agents/{agent_type}/capabilities` | GET | 获取智能体能力 | 未使用 |

**架构特点**：
- 使用 `AgentRouter` 处理多智能体路由
- 响应格式为多字段响应
- 复杂的 `agent_state` 管理

#### V2 API (`/v2/sessions`) - `backend/app/routes/sessions_v2.py`

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/v2/sessions` | POST | 创建会话 | 已实现 |
| `/v2/sessions/{session_id}/messages` | POST | 发送消息 | 已实现 |
| `/v2/sessions/agents` | GET | 获取智能体列表 | 已实现（未使用） |
| `/v2/sessions/agents/{agent_type}/capabilities` | GET | 获取智能体能力 | 已实现（未使用） |
| `/v2/sessions` | GET | 获取会话列表 | ❌ 缺失 |
| `/v2/sessions/{session_id}/messages` | GET | 获取消息列表 | ❌ 缺失 |

**架构特点**：
- 使用 `AgentRouterV2` 处理多智能体路由
- 响应格式统一为 `AgentResponse`
- 简化的 `next_state` 管理
- 明确的阶段管理：`greeting`, `collecting`, `analyzing`, `diagnosing`, `completed`

### 2.2 V1 vs V2 对比

| 对比维度 | V1 API | V2 API |
|---------|--------|--------|
| 路由前缀 | `/sessions` | `/v2/sessions` |
| 智能体路由器 | AgentRouter | AgentRouterV2 |
| 响应格式 | 多字段响应 | AgentResponse 统一格式 |
| 状态管理 | 复杂的 agent_state | 简化的 next_state |
| 阶段管理 | 无明确定义 | greeting, collecting, analyzing, diagnosing, completed |
| 会话列表端点 | ✅ GET /sessions | ❌ 缺失 |
| 消息列表端点 | ✅ GET /sessions/{id}/messages | ❌ 缺失 |
| 智能体能力端点 | ✅ 有 | ✅ 有（均未使用） |

### 2.3 客户端使用情况

#### 前端 - `frontend/src/`

**主要 API 使用**：
- `dermaAgentApi` - 皮肤科专科 API（主要使用）
- `diseaseApi` - 疾病相关 API
- `drugApi` - 药物相关 API

**Sessions API 使用情况**：
- ❌ 完全未使用 sessions V1 API
- ❌ 完全未使用 sessions V2 API
- 前端直接使用专科 API，不经过 sessions 路由

#### iOS - `ios/xinlingyisheng/xinlingyisheng/`

**APIService.swift 分析**：

| 函数 | 使用的 API 版本 | 状态 |
|------|----------------|------|
| `createUnifiedSession` | V1 (`/sessions`) | 主要使用 |
| `sendUnifiedMessage` | V1 (`/sessions/{id}/messages`) | 主要使用 |
| `getSessions` | V1 (`/sessions`) | 使用 |
| `getMessages` | V1 (`/sessions/{id}/messages`) | 使用 |
| `createV2Session` | V2 (`/v2/sessions`) | 已实现，未主要使用 |
| `sendV2Message` | V2 (`/v2/sessions/{id}/messages`) | 已实现，未主要使用 |

**切换机制**：
- 通过 `agentType` 参数判断使用哪个版本
- 目前默认使用 V1

## 3. 依赖关系分析

### 3.1 前端依赖

```
前端
 └── dermaAgentApi (/api/derma/)
     └── 后端专科 API (非 sessions)
```

**结论**：前端不依赖 sessions API，重构对其无影响。

### 3.2 iOS 依赖

```
iOS (APIService.swift)
 ├── V1 API (主要使用)
 │   ├── POST /sessions
 │   ├── GET /sessions
 │   ├── GET /sessions/{id}/messages
 │   └── POST /sessions/{id}/messages
 └── V2 API (已实现，未主要使用)
     ├── POST /v2/sessions
     └── POST /v2/sessions/{id}/messages
```

**涉及的 ViewModel**：
- `UnifiedChatViewModel.swift` - 使用 APIService 的会话和消息 API
- `VoiceTranscriptionViewModel.swift` - 可能涉及语音相关调用

### 3.3 依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                        后端 API                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │   V1 Sessions    │          │   V2 Sessions    │        │
│  │   /sessions      │          │   /v2/sessions   │        │
│  └────────┬─────────┘          └────────┬─────────┘        │
│           │                             │                   │
└───────────┼─────────────────────────────┼───────────────────┘
            │                             │
            │                             │
    ┌───────▼───────────┐       ┌────────▼─────────┐
    │      iOS          │       │      iOS         │
    │   (主要使用 V1)   │       │   (V2 已实现)    │
    └───────────────────┘       └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        前端                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  直接使用专科 API (/api/derma/)，不依赖 sessions             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 4. 未使用 API 清单

### 4.1 V1 未使用端点

| 端点 | 方法 | 功能 | 未使用原因 |
|------|------|------|-----------|
| `/sessions/agents` | GET | 获取智能体列表 | iOS 未调用 |
| `/sessions/agents/{agent_type}/capabilities` | GET | 获取智能体能力 | iOS 未调用 |

### 4.2 V2 未使用端点

| 端点 | 方法 | 功能 | 未使用原因 |
|------|------|------|-----------|
| `/v2/sessions` | GET | 获取会话列表 | ❌ 后端未实现 |
| `/v2/sessions/{session_id}/messages` | GET | 获取消息列表 | ❌ 后端未实现 |
| `/v2/sessions/agents` | GET | 获取智能体列表 | iOS 未调用 |
| `/v2/sessions/agents/{agent_type}/capabilities` | GET | 获取智能体能力 | iOS 未调用 |

### 4.3 清理建议

**可以删除的代码**：
1. V1 和 V2 的 `agents` 和 `capabilities` 端点（均未被使用）
2. V1 和 V2 相关的智能体列表和能力查询服务代码

## 5. 重构方案

### 5.1 方案选择

| 方案 | 描述 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|-------|
| A | 全部迁移到 V1，删除 V2 | V1 功能完整 | 架构较老 | ⭐ |
| B | 全部迁移到 V2，删除 V1 | 架构先进，响应格式统一 | 缺少部分端点 | ⭐⭐⭐⭐ |
| C | 合并 V1 和 V2，创建 V3 | 兼具两者优点 | 工作量大 | ⭐⭐ |
| D | 渐进式迁移，双版本并存 | 风险可控 | 维护成本高 | ⭐⭐⭐ |

**推荐方案：方案 B + 渐进式迁移**

理由：
1. V2 使用了更先进的架构（AgentRouterV2）
2. 响应格式更标准化（AgentResponse）
3. 阶段管理更清晰（greeting, collecting, analyzing, diagnosing, completed）
4. 代码更简洁，易于维护
5. iOS 已经实现了 V2 API 的调用

### 5.2 迁移计划

#### 阶段一：完善 V2 API（1-2 周）

**任务清单**：
- [ ] 在 `sessions_v2.py` 中添加 `GET /v2/sessions` 端点
- [ ] 在 `sessions_v2.py` 中添加 `GET /v2/sessions/{session_id}/messages` 端点
- [ ] 确保 V2 功能与 V1 对等
- [ ] 编写单元测试

**代码变更**：
```python
# backend/app/routes/sessions_v2.py

@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取会话消息列表"""
    # 实现逻辑

@router.get("")
async def list_sessions(
    current_user: User = Depends(get_current_user)
):
    """获取用户会话列表"""
    # 实现逻辑
```

#### 阶段二：iOS 客户端迁移（2-3 周）

**任务清单**：
- [ ] 修改 `APIService.swift` 默认使用 V2 API
- [ ] 更新 `UnifiedChatViewModel.swift` 适配 V2 响应格式
- [ ] 更新 `VoiceTranscriptionViewModel.swift`（如需要）
- [ ] 进行集成测试

**代码变更**：
```swift
// APIService.swift
// 修改默认使用 V2
static func createSession(...) -> URLSessionTask {
    return createV2Session(...)  // 改为使用 V2
}
```

#### 阶段三：清理 V1 API（1 周）

**任务清单**：
- [ ] 验证所有功能已迁移到 V2
- [ ] 删除 `sessions.py` 文件
- [ ] 删除 V1 相关的服务代码
- [ ] 更新 `main.py` 移除 V1 路由注册
- [ ] 清理测试文件中的 V1 引用

#### 阶段四：前端适配（可选）

前端目前不使用 sessions API，暂无需迁移。如未来需要，直接使用 V2 API。

### 5.3 清理清单

#### 后端可删除的文件

- [ ] `backend/app/routes/sessions.py`（V1 路由）
- [ ] `backend/app/services/agent_router.py`（V1 智能体路由器，如无其他引用）
- [ ] 相关测试文件中的 V1 引用

#### 后端可删除的代码

- [ ] `main.py` 中的 V1 路由注册
- [ ] V1 和 V2 均未使用的 `agents` 和 `capabilities` 端点

#### iOS 可删除的代码

- [ ] `APIService.swift` 中的 V1 专用函数（迁移完成后）
- [ ] `createUnifiedSession`（替换为 V2 版本）
- [ ] `sendUnifiedMessage`（替换为 V2 版本）

## 6. 风险评估

| 风险类型 | 风险描述 | 概率 | 影响 | 缓解措施 |
|---------|---------|------|------|---------|
| 技术风险 | V2 可能缺少某些 V1 的隐式功能 | 中 | 高 | 完整功能对比测试 |
| 兼容性风险 | 现有 iOS 用户可能受影响 | 低 | 中 | API 向后兼容 |
| 业务风险 | 迁移期间服务中断 | 低 | 高 | 灰度发布 |
| 测试风险 | 测试覆盖不全导致 bug | 中 | 中 | 完善测试计划 |

## 7. 测试计划

### 7.1 单元测试

```bash
# 测试 V2 所有端点
cd backend
pytest tests/routes/test_sessions_v2.py -v
```

**测试项**：
- [ ] POST /v2/sessions - 创建会话
- [ ] GET /v2/sessions - 获取会话列表
- [ ] GET /v2/sessions/{id}/messages - 获取消息列表
- [ ] POST /v2/sessions/{id}/messages - 发送消息

### 7.2 集成测试

**iOS 集成测试**：
- [ ] 使用 V2 API 创建会话
- [ ] 使用 V2 API 发送消息
- [ ] 使用 V2 API 获取消息列表
- [ ] 使用 V2 API 获取会话列表
- [ ] 验证 UI 显示正确

### 7.3 性能测试

```bash
# API 响应时间测试
curl -X POST http://localhost:8000/v2/sessions -w "@curl-format.txt"

# 并发测试
ab -n 1000 -c 10 http://localhost:8000/v2/sessions
```

## 8. 回滚方案

如果迁移出现问题，按以下步骤回滚：

1. **iOS 回滚**：
   ```swift
   // APIService.swift
   // 恢复使用 V1
   static func createSession(...) -> URLSessionTask {
       return createV1Session(...)  // 回退到 V1
   }
   ```

2. **后端回滚**：
   - 保留 V1 API 代码直到迁移完全成功
   - 使用 Git 回滚到迁移前版本

3. **数据库回滚**：
   - V1 和 V2 使用相同的数据模型，无需迁移数据

## 9. 附录

### 9.1 完整 API 端点列表

#### V1 Sessions API

| 端点 | 方法 | 描述 | iOS 使用 | 前端使用 |
|------|------|------|---------|---------|
| `/sessions` | POST | 创建会话 | ✅ | ❌ |
| `/sessions` | GET | 获取会话列表 | ✅ | ❌ |
| `/sessions/{id}/messages` | GET | 获取消息列表 | ✅ | ❌ |
| `/sessions/{id}/messages` | POST | 发送消息 | ✅ | ❌ |
| `/sessions/agents` | GET | 获取智能体列表 | ❌ | ❌ |
| `/sessions/agents/{type}/capabilities` | GET | 获取智能体能力 | ❌ | ❌ |

#### V2 Sessions API

| 端点 | 方法 | 描述 | iOS 使用 | 前端使用 | 状态 |
|------|------|------|---------|---------|------|
| `/v2/sessions` | POST | 创建会话 | ✅ | ❌ | 已实现 |
| `/v2/sessions` | GET | 获取会话列表 | ❌ | ❌ | 待实现 |
| `/v2/sessions/{id}/messages` | GET | 获取消息列表 | ❌ | ❌ | 待实现 |
| `/v2/sessions/{id}/messages` | POST | 发送消息 | ✅ | ❌ | 已实现 |
| `/v2/sessions/agents` | GET | 获取智能体列表 | ❌ | ❌ | 已实现 |
| `/v2/sessions/agents/{type}/capabilities` | GET | 获取智能体能力 | ❌ | ❌ | 已实现 |

### 9.2 代码变更清单

#### 后端变更

```
新增：
- backend/app/routes/sessions_v2.py: GET /v2/sessions
- backend/app/routes/sessions_v2.py: GET /v2/sessions/{id}/messages

修改：
- backend/app/main.py: 移除 V1 路由注册（迁移完成后）

删除：
- backend/app/routes/sessions.py（迁移完成后）
- backend/app/services/agent_router.py（如无其他引用）
```

#### iOS 变更

```
修改：
- ios/.../Services/APIService.swift: 默认使用 V2
- ios/.../ViewModels/UnifiedChatViewModel.swift: 适配 V2 响应格式

删除（迁移完成后）：
- ios/.../Services/APIService.swift 中的 V1 专用函数
```

### 9.3 时间表

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 阶段一 | 完善 V2 API | 1-2 周 |
| 阶段二 | iOS 客户端迁移 | 2-3 周 |
| 阶段三 | 清理 V1 API | 1 周 |
| **总计** | | **4-6 周** |

## 10. 结论

当前系统存在明显的 API 版本冗余问题。建议采用渐进式迁移策略，逐步将系统统一到 V2 API。

**关键发现**：
1. 前端不使用 sessions API，不受影响
2. iOS 主要使用 V1，但已实现 V2 调用
3. V2 架构更先进，但缺少部分端点

**预期收益**：
1. 统一架构，简化维护
2. 提升代码质量
3. 为未来功能扩展奠定基础
4. 删除冗余代码，减少维护成本

---

**报告生成时间**：2026-02-03
**分析人员**：Claude AI Agent
