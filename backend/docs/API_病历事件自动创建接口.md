# API接口设计文档：病历事件自动创建

**文档版本**: V1.0  
**创建日期**: 2026-01-14  
**负责人**: 后端开发团队  
**关联文档**: TDD_病历事件自动创建机制.md

---

## 1. 接口概览

### 1.1 修改的现有接口
- `POST /api/derma/start` - 开始皮肤科会话（新增event_id响应）
- `POST /api/derma/continue` - 继续皮肤科对话（新增event_id响应）
- `POST /api/sessions/unified/create` - 创建统一会话（新增event_id响应）
- `POST /api/sessions/unified/message` - 发送统一消息（新增event_id响应）

### 1.2 新增接口
- `POST /api/medical-events/smart-aggregate` - 智能聚合病历事件
- `POST /api/medical-events/{event_id}/complete` - 完成病历事件
- `GET /api/medical-events/by-session/{session_id}` - 根据会话ID查询事件

---

## 2. 接口详细设计

### 2.1 修改现有接口

#### POST /api/derma/start

**功能**: 开始皮肤科会话，自动创建或关联病历事件

**请求头**:
```http
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "chief_complaint": "手臂出现红疹，伴有瘙痒"
}
```

**响应体**（修改后）:
```json
{
  "session_id": "derma_20260114_103045_a1b2c3d4",
  "message": "您好，我是皮肤科AI医生。我看到您提到手臂出现红疹并伴有瘙痒，我会帮您详细了解情况。\n\n首先，请问：\n1. 红疹出现多久了？\n2. 红疹的形状和大小是怎样的？",
  "stage": "inquiry",
  "progress": 10,
  "quick_options": [
    {
      "label": "1-3天",
      "value": "红疹出现1-3天了"
    },
    {
      "label": "一周以上",
      "value": "红疹出现一周以上了"
    }
  ],
  
  // ===== 新增字段 =====
  "event_id": 123,
  "is_new_event": true,
  "event_title": "手臂出现红疹"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| event_id | integer | 是 | 关联的病历事件ID |
| is_new_event | boolean | 是 | 是否是新创建的事件（true=新建，false=复用） |
| event_title | string | 是 | 事件标题 |

**状态码**:
- `200 OK` - 成功
- `401 Unauthorized` - 未授权
- `500 Internal Server Error` - 服务器错误

**错误响应**:
```json
{
  "detail": "创建病历事件失败: {error_message}"
}
```

---

#### POST /api/derma/continue

**功能**: 继续皮肤科对话，更新关联的病历事件

**请求体**:
```json
{
  "session_id": "derma_20260114_103045_a1b2c3d4",
  "history": [
    {
      "role": "user",
      "message": "红疹出现3天了",
      "timestamp": "2026-01-14T10:30:45Z"
    }
  ],
  "current_message": "红疹主要在手臂内侧",
  "task_type": null
}
```

**响应体**（修改后）:
```json
{
  "session_id": "derma_20260114_103045_a1b2c3d4",
  "message": "了解了，手臂内侧的红疹。请问红疹是否有以下特征：\n- 边界清晰还是模糊？\n- 是否有脱屑？\n- 按压后是否褪色？",
  "stage": "analysis",
  "progress": 60,
  "quick_options": [...],
  "skin_analysis": null,
  
  // ===== 新增字段 =====
  "event_id": 123,
  "event_updated": true,
  "should_generate_summary": false
}
```

**当对话结束时**:
```json
{
  "session_id": "derma_20260114_103045_a1b2c3d4",
  "message": "根据您的描述和照片分析，初步判断可能是接触性皮炎...",
  "stage": "completed",  // 关键：对话结束标志
  "progress": 100,
  "skin_analysis": {
    "condition": "接触性皮炎",
    "confidence": 0.82,
    "severity": "轻度",
    "recommendations": [...]
  },
  
  // ===== 新增字段 =====
  "event_id": 123,
  "event_updated": true,
  "should_generate_summary": true  // 提示iOS端生成摘要
}
```

---

### 2.2 新增接口

#### POST /api/medical-events/smart-aggregate

**功能**: 智能聚合病历事件（内部服务调用，也可供前端直接调用）

**请求头**:
```http
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "session_id": "derma_20260114_103045_a1b2c3d4",
  "session_type": "dermatology",
  "department": "dermatology",
  "chief_complaint": "手臂红疹",
  "timestamp": "2026-01-14T10:30:45Z"
}
```

**响应体**:
```json
{
  "action": "create_new",
  "event_id": 123,
  "is_new_event": true,
  "event_title": "手臂红疹",
  "reason": "当日无同科室进行中事件，创建新事件",
  "created_at": "2026-01-14T10:30:45Z"
}
```

**action枚举值**:
- `create_new` - 创建新事件
- `append_existing` - 追加到现有事件

**聚合规则**:
1. 查找用户当日（00:00-23:59）同科室的 `in_progress` 状态事件
2. 如果存在 → 返回 `append_existing`
3. 如果不存在 → 创建新事件，返回 `create_new`
4. 不同科室的对话始终创建新事件

**状态码**:
- `200 OK` - 成功
- `400 Bad Request` - 参数错误
- `401 Unauthorized` - 未授权

---

#### POST /api/medical-events/{event_id}/complete

**功能**: 标记病历事件为已完成

**请求头**:
```http
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "final_summary": "患者主诉手臂红疹3天，经AI分析判断为接触性皮炎，建议避免接触过敏原并使用炉甘石洗剂。",
  "ai_analysis": {
    "symptoms": ["红疹", "瘙痒", "局部肿胀"],
    "possible_diagnosis": ["接触性皮炎", "湿疹"],
    "recommendations": ["避免搔抓", "保持清洁", "使用炉甘石洗剂"],
    "risk_level": "low"
  }
}
```

**响应体**:
```json
{
  "success": true,
  "event_id": 123,
  "status": "completed",
  "end_time": "2026-01-14T11:15:30Z",
  "message": "病历事件已完成"
}
```

**状态码**:
- `200 OK` - 成功
- `404 Not Found` - 事件不存在
- `403 Forbidden` - 无权限操作此事件

---

#### GET /api/medical-events/by-session/{session_id}

**功能**: 根据会话ID查询关联的病历事件

**请求头**:
```http
Authorization: Bearer {token}
```

**路径参数**:
- `session_id` (string, required) - 会话ID

**响应体**:
```json
{
  "event_id": 123,
  "title": "手臂红疹",
  "department": "dermatology",
  "status": "in_progress",
  "created_at": "2026-01-14T10:30:45Z",
  "updated_at": "2026-01-14T11:00:00Z"
}
```

**状态码**:
- `200 OK` - 成功
- `404 Not Found` - 未找到关联事件
- `401 Unauthorized` - 未授权

---

## 3. 数据库操作

### 3.1 event_sessions 表操作

**插入会话关联**:
```sql
INSERT INTO event_sessions (event_id, session_id, session_type, timestamp)
VALUES (123, 'derma_20260114_103045_a1b2c3d4', 'dermatology', NOW())
ON CONFLICT (session_id) DO NOTHING;
```

**查询会话关联的事件**:
```sql
SELECT event_id FROM event_sessions
WHERE session_id = 'derma_20260114_103045_a1b2c3d4';
```

### 3.2 medical_events 表操作

**查找当日同科室进行中事件**:
```sql
SELECT * FROM medical_events
WHERE user_id = 1
  AND agent_type = 'dermatology'
  AND status = 'in_progress'
  AND start_time >= CURRENT_DATE
  AND start_time < CURRENT_DATE + INTERVAL '1 day'
ORDER BY start_time DESC
LIMIT 1;
```

**创建新事件**:
```sql
INSERT INTO medical_events (
    user_id, title, department, agent_type, status, risk_level,
    start_time, summary, chief_complaint, created_at, updated_at
) VALUES (
    1, '手臂红疹', 'dermatology', 'dermatology', 'in_progress', 'low',
    NOW(), '手臂出现红疹，伴有瘙痒', '手臂出现红疹', NOW(), NOW()
)
RETURNING id;
```

**更新事件时间戳**:
```sql
UPDATE medical_events
SET updated_at = NOW()
WHERE id = 123;
```

**完成事件**:
```sql
UPDATE medical_events
SET status = 'completed',
    end_time = NOW(),
    updated_at = NOW(),
    summary = '患者主诉手臂红疹3天...'
WHERE id = 123;
```

---

## 4. 错误处理

### 4.1 错误码定义

| 错误码 | HTTP状态 | 说明 | 处理方式 |
|--------|----------|------|----------|
| EVENT_CREATE_FAILED | 500 | 事件创建失败 | 记录日志，返回通用错误 |
| EVENT_NOT_FOUND | 404 | 事件不存在 | 提示用户事件不存在 |
| SESSION_NOT_LINKED | 400 | 会话未关联事件 | 尝试重新聚合 |
| DB_CONNECTION_ERROR | 500 | 数据库连接失败 | 重试3次，失败则降级 |

### 4.2 降级策略

如果病历事件创建失败：
1. **不阻塞对话流程** - 对话继续进行
2. **记录错误日志** - 便于后续排查
3. **返回 event_id=null** - iOS端优雅处理
4. **异步重试** - 后台任务队列重试创建

```python
try:
    event, is_new = EventAggregator.find_or_create_event(...)
    event_id = event.id
except Exception as e:
    logger.error(f"[EventAggregator] 创建事件失败: {e}")
    event_id = None  # 降级处理
    # 加入重试队列
    retry_queue.add_task('create_event', {...})
```

---

## 5. 性能优化

### 5.1 数据库索引

```sql
-- event_sessions 表索引
CREATE INDEX idx_event_sessions_session_id ON event_sessions(session_id);
CREATE INDEX idx_event_sessions_event_id ON event_sessions(event_id);

-- medical_events 表索引
CREATE INDEX idx_medical_events_user_status ON medical_events(user_id, status);
CREATE INDEX idx_medical_events_user_date ON medical_events(user_id, start_time);
CREATE INDEX idx_medical_events_agent_type ON medical_events(agent_type);
```

### 5.2 查询优化

**优化前**（N+1查询）:
```python
for session in sessions:
    event = db.query(MedicalEvent).filter(
        MedicalEvent.id == session.event_id
    ).first()
```

**优化后**（批量查询）:
```python
event_ids = [s.event_id for s in sessions]
events = db.query(MedicalEvent).filter(
    MedicalEvent.id.in_(event_ids)
).all()
event_map = {e.id: e for e in events}
```

### 5.3 缓存策略

**Redis缓存当日事件**:
```python
cache_key = f"user:{user_id}:today_events:{department}"
cached_event = redis.get(cache_key)

if cached_event:
    return json.loads(cached_event)
else:
    event = db.query(...).first()
    redis.setex(cache_key, 3600, json.dumps(event))  # 缓存1小时
    return event
```

---

## 6. 安全性

### 6.1 权限验证

```python
def verify_event_ownership(event_id: int, user_id: int, db: Session):
    """验证用户是否拥有该事件"""
    event = db.query(MedicalEvent).filter(
        MedicalEvent.id == event_id,
        MedicalEvent.user_id == user_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=403, detail="无权限访问此事件")
    
    return event
```

### 6.2 输入验证

```python
from pydantic import BaseModel, validator

class SmartAggregateRequest(BaseModel):
    session_id: str
    session_type: str
    department: str
    chief_complaint: Optional[str] = None
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('session_id无效')
        return v
    
    @validator('session_type')
    def validate_session_type(cls, v):
        allowed = ['dermatology', 'cardiology', 'general']
        if v not in allowed:
            raise ValueError(f'session_type必须是{allowed}之一')
        return v
```

---

## 7. 监控与日志

### 7.1 关键日志

```python
# 事件创建日志
logger.info(
    f"[EventAggregator] 用户{user_id}创建病历事件",
    extra={
        "user_id": user_id,
        "event_id": event.id,
        "session_id": session_id,
        "department": department,
        "is_new": is_new
    }
)

# 事件聚合日志
logger.info(
    f"[EventAggregator] 会话聚合到现有事件",
    extra={
        "user_id": user_id,
        "event_id": event.id,
        "session_id": session_id,
        "reason": "当日已有同科室事件"
    }
)

# 错误日志
logger.error(
    f"[EventAggregator] 事件创建失败",
    extra={
        "user_id": user_id,
        "session_id": session_id,
        "error": str(e)
    },
    exc_info=True
)
```

### 7.2 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        # 记录慢查询
        if duration > 0.5:
            logger.warning(
                f"[Performance] {func.__name__} 耗时 {duration:.2f}s",
                extra={"function": func.__name__, "duration": duration}
            )
        
        return result
    return wrapper

@monitor_performance
async def find_or_create_event(...):
    ...
```

---

## 8. 测试用例

### 8.1 API测试用例

**测试1: 首次对话创建新事件**
```bash
curl -X POST http://localhost:8000/api/derma/start \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "chief_complaint": "手臂红疹"
  }'

# 预期响应
{
  "event_id": 123,
  "is_new_event": true,
  ...
}
```

**测试2: 同一天第二次对话复用事件**
```bash
# 第一次对话（上午10点）
curl -X POST .../derma/start -d '{"chief_complaint": "手臂红疹"}'
# 返回: event_id=123, is_new_event=true

# 第二次对话（下午3点，同一天）
curl -X POST .../derma/start -d '{"chief_complaint": "红疹加重了"}'
# 预期: event_id=123, is_new_event=false
```

**测试3: 不同科室创建新事件**
```bash
# 皮肤科对话
curl -X POST .../derma/start -d '{"chief_complaint": "皮肤问题"}'
# 返回: event_id=123

# 心内科对话（同一天）
curl -X POST .../sessions/unified/create -d '{"agent_type": "cardiology"}'
# 预期: event_id=124 (新事件)
```

### 8.2 集成测试

```python
import pytest
from fastapi.testclient import TestClient

def test_event_auto_creation(client: TestClient, auth_headers):
    """测试事件自动创建"""
    # 1. 开始对话
    response = client.post(
        "/api/derma/start",
        json={"chief_complaint": "手臂红疹"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert data["is_new_event"] == True
    
    event_id = data["event_id"]
    
    # 2. 验证事件已创建
    event_response = client.get(
        f"/api/medical-events/{event_id}",
        headers=auth_headers
    )
    assert event_response.status_code == 200
    event = event_response.json()
    assert event["status"] == "in_progress"

def test_event_aggregation_same_day(client: TestClient, auth_headers):
    """测试同一天事件聚合"""
    # 第一次对话
    resp1 = client.post("/api/derma/start", ...)
    event_id_1 = resp1.json()["event_id"]
    
    # 第二次对话（同一天）
    resp2 = client.post("/api/derma/start", ...)
    event_id_2 = resp2.json()["event_id"]
    
    # 应该是同一个事件
    assert event_id_1 == event_id_2
    assert resp2.json()["is_new_event"] == False
```

---

## 9. 版本兼容性

### 9.1 向后兼容

**旧版iOS客户端**（不支持event_id）:
- 后端正常返回 `event_id` 字段
- 旧版客户端忽略该字段
- 不影响现有功能

**新版iOS客户端**（支持event_id）:
- 读取 `event_id` 字段
- 实现自动关联功能
- 提升用户体验

### 9.2 API版本控制

```python
# 可选：使用API版本号
@router.post("/v2/derma/start")  # 新版本
async def start_derma_session_v2(...):
    # 包含event_id逻辑
    ...

@router.post("/v1/derma/start")  # 旧版本（兼容）
async def start_derma_session_v1(...):
    # 不包含event_id逻辑
    ...
```

---

## 10. 附录

### 10.1 完整请求示例

**完整对话流程**:

```bash
# 1. 开始对话
curl -X POST http://localhost:8000/api/derma/start \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "chief_complaint": "手臂出现红疹，伴有瘙痒"
  }'

# 响应
{
  "session_id": "derma_20260114_103045_a1b2c3d4",
  "message": "您好，我是皮肤科AI医生...",
  "stage": "inquiry",
  "progress": 10,
  "event_id": 123,
  "is_new_event": true
}

# 2. 继续对话
curl -X POST http://localhost:8000/api/derma/continue \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "session_id": "derma_20260114_103045_a1b2c3d4",
    "current_message": "红疹出现3天了",
    "history": [...]
  }'

# 3. 上传照片
curl -X POST http://localhost:8000/api/derma/upload-image \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "session_id=derma_20260114_103045_a1b2c3d4" \
  -F "image=@skin_photo.jpg"

# 4. 对话结束
# 后端自动标记事件为completed，触发AI摘要生成
```

### 10.2 相关文档链接

- 技术设计文档: `TDD_病历事件自动创建机制.md`
- 数据库迁移脚本: `/backend/migrations/add_event_sessions_table.py`
- iOS集成方案: `iOS_病历事件自动创建集成方案.md`

---

**文档状态**: 待审核  
**审核人**: 后端技术负责人  
**更新日期**: 2026-01-14
