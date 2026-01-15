# Medical Events API 修复文档

## 问题描述

### 1. 422 错误 - `/medical-events/aggregate`
iOS 客户端调用聚合接口时传递了后端不支持的 `session_type` 值，导致请求验证失败。

**原因：**
- 后端 Schema 只接受 `Literal["derma", "diagnosis"]`
- iOS 端传递的是 `agentType.rawValue`，可能包含其他科室类型（cardio, general, ortho 等）

### 2. 500 错误 - `GET /medical-events`
查询病历列表时，数据库中存在无效的枚举值，导致数据转换失败。

**原因：**
- 数据库中某些记录的 `agent_type`、`status`、`risk_level` 字段包含无效值
- 缺少错误处理，导致抛出 500 异常而非优雅降级

## 修复方案

### 1. 扩展 session_type 支持所有科室类型

**文件：** `backend/app/schemas/medical_event.py`

```python
class AggregateSessionRequest(BaseModel):
    """聚合会话请求"""
    session_id: str
    session_type: Literal["cardio", "derma", "ortho", "neuro", "general", "endo", "gastro", "respiratory", "diagnosis"]
```

### 2. 添加科室类型映射逻辑

**文件：** `backend/app/routes/medical_events.py`

在 `aggregate_session` 函数中添加了科室映射：

```python
DEPARTMENT_MAPPING = {
    "cardio": {"name": "心血管科", "agent_type": AgentType.CARDIO},
    "derma": {"name": "皮肤科", "agent_type": AgentType.DERMA},
    "ortho": {"name": "骨科", "agent_type": AgentType.ORTHO},
    "neuro": {"name": "神经科", "agent_type": AgentType.NEURO},
    "general": {"name": "全科", "agent_type": AgentType.GENERAL},
    "endo": {"name": "内分泌科", "agent_type": AgentType.ENDO},
    "gastro": {"name": "消化科", "agent_type": AgentType.GASTRO},
    "respiratory": {"name": "呼吸科", "agent_type": AgentType.RESPIRATORY},
    "diagnosis": {"name": "全科", "agent_type": AgentType.GENERAL},
}
```

对于没有专门会话表的科室，创建通用会话数据：

```python
else:
    # 对于其他科室类型，创建通用会话数据
    session_data = {
        "session_id": request.session_id,
        "session_type": request.session_type,
        "timestamp": datetime.utcnow().isoformat(),
        "summary": f"{department}问诊",
        "risk_level": "low",
        "stage": "completed"
    }
```

### 3. 添加错误处理防止 500 错误

**文件：** `backend/app/routes/medical_events.py`

#### 在 `_build_event_summary` 中添加安全处理：

```python
def _build_event_summary(event: MedicalEvent) -> MedicalEventSummarySchema:
    """构建事件摘要"""
    # 安全获取枚举值，防止无效数据导致500错误
    try:
        agent_type_value = event.agent_type.value if event.agent_type else "general"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid agent_type for event {event.id}: {event.agent_type}")
        agent_type_value = "general"
    
    # ... 类似处理 status 和 risk_level
    
    return MedicalEventSummarySchema(
        id=event.id,
        title=event.title or f"病历事件 {event.id}",  # 防止空值
        department=event.department or "全科",
        agent_type=agent_type_value,
        # ...
    )
```

#### 在 `_build_event_detail` 中添加安全处理：

- 安全解析 AI 分析数据
- 安全解析会话记录
- 安全解析附件和备注
- 安全获取枚举值
- 为所有可能为空的字段提供默认值

### 4. 数据库完整性检查工具

创建了三个工具来检查和修复数据库问题：

#### Python 脚本（需要 SQLAlchemy）
`backend/scripts/check_medical_events_integrity.py`

```bash
cd backend
python -m scripts.check_medical_events_integrity
```

#### SQL 检查脚本
`backend/scripts/check_medical_events.sql`

```bash
psql -d your_database -f backend/scripts/check_medical_events.sql
```

#### SQL 修复脚本
`backend/scripts/fix_medical_events.sql`

```bash
psql -d your_database -f backend/scripts/fix_medical_events.sql
```

## 使用说明

### 1. 立即修复数据库问题

如果你有 PostgreSQL 访问权限，运行修复脚本：

```bash
# 先检查问题
psql -d your_database -f backend/scripts/check_medical_events.sql

# 确认后修复
psql -d your_database -f backend/scripts/fix_medical_events.sql
```

或者手动执行 SQL：

```sql
-- 修复无效的枚举值
UPDATE medical_events SET agent_type = 'general' 
WHERE agent_type NOT IN ('cardio', 'derma', 'ortho', 'neuro', 'general', 'endo', 'gastro', 'respiratory');

UPDATE medical_events SET status = 'active' 
WHERE status NOT IN ('active', 'completed', 'exported', 'archived');

UPDATE medical_events SET risk_level = 'low' 
WHERE risk_level NOT IN ('low', 'medium', 'high', 'emergency');

-- 修复空字段
UPDATE medical_events SET title = '病历事件 ' || id WHERE title IS NULL OR title = '';
UPDATE medical_events SET department = '全科' WHERE department IS NULL OR department = '';
UPDATE medical_events SET sessions = '[]'::json WHERE sessions IS NULL;
UPDATE medical_events SET ai_analysis = '{}'::json WHERE ai_analysis IS NULL;
UPDATE medical_events SET session_count = 0 WHERE session_count IS NULL;
UPDATE medical_events SET attachment_count = 0 WHERE attachment_count IS NULL;
UPDATE medical_events SET export_count = 0 WHERE export_count IS NULL;
```

### 2. 重启后端服务

修复代码后，重启后端服务以应用更改：

```bash
cd backend
# 如果使用 Docker
docker-compose restart backend

# 如果直接运行
# 停止当前进程，然后重新启动
uvicorn app.main:app --reload
```

### 3. 测试修复结果

#### 测试聚合接口（所有科室类型）

```bash
# 测试心血管科
curl -X POST http://localhost:8000/medical-events/aggregate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session_1", "session_type": "cardio"}'

# 测试皮肤科
curl -X POST http://localhost:8000/medical-events/aggregate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session_2", "session_type": "derma"}'

# 测试其他科室
curl -X POST http://localhost:8000/medical-events/aggregate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session_3", "session_type": "ortho"}'
```

#### 测试列表接口

```bash
curl -X GET "http://localhost:8000/medical-events?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

应该返回 200 状态码，不再出现 500 错误。

## 支持的科室类型

现在 `/medical-events/aggregate` 接口支持以下所有科室类型：

| session_type | 科室名称 | AgentType |
|--------------|---------|-----------|
| cardio | 心血管科 | CARDIO |
| derma | 皮肤科 | DERMA |
| ortho | 骨科 | ORTHO |
| neuro | 神经科 | NEURO |
| general | 全科 | GENERAL |
| endo | 内分泌科 | ENDO |
| gastro | 消化科 | GASTRO |
| respiratory | 呼吸科 | RESPIRATORY |
| diagnosis | 全科 | GENERAL |

## 注意事项

1. **向后兼容**：修改完全向后兼容，现有的 `derma` 和 `diagnosis` 类型继续正常工作

2. **错误处理**：即使数据库中有脏数据，API 也会优雅降级，返回默认值而不是 500 错误

3. **日志记录**：所有数据问题都会记录警告日志，便于后续排查

4. **通用会话**：对于没有专门会话表的科室（如 cardio、ortho 等），系统会创建通用会话数据

5. **数据完整性**：建议定期运行检查脚本，确保数据库数据质量

## 后续建议

1. **添加数据验证**：在创建/更新病历事件时，添加更严格的数据验证

2. **创建专门的会话表**：为其他科室创建专门的会话表（如 `cardio_sessions`、`ortho_sessions` 等）

3. **定期清理**：设置定时任务定期检查和修复数据完整性问题

4. **监控告警**：添加监控，当出现无效数据时发送告警

5. **单元测试**：为聚合接口添加单元测试，覆盖所有科室类型
