# PRD - 会话架构重构方案

**文档版本**: v1.0  
**创建日期**: 2026-01-15  
**负责人**: 产品团队  
**优先级**: P0 (最高优先级)

---

## 📋 目录

1. [背景与问题](#1-背景与问题)
2. [目标与价值](#2-目标与价值)
3. [现状分析](#3-现状分析)
4. [解决方案](#4-解决方案)
5. [技术架构设计](#5-技术架构设计)
6. [数据模型设计](#6-数据模型设计)
7. [API接口设计](#7-api接口设计)
8. [数据迁移方案](#8-数据迁移方案)
9. [实施路线图](#9-实施路线图)
10. [风险评估](#10-风险评估)
11. [成功指标](#11-成功指标)

---

## 1. 背景与问题

### 1.1 问题描述

当前系统在用户与智能体对话后点击"生成病历"按钮时，生成的病历资料存在**数据缺失和虚假数据**问题，严重影响用户体验和产品价值。

### 1.2 核心问题

#### 问题1: 会话数据模型不统一
- 系统存在3个独立的会话表：`sessions`、`derma_sessions`、`diagnosis_sessions`
- iOS客户端使用统一聊天接口创建 `sessions` 表记录
- 后端病历聚合逻辑却查询 `derma_sessions` 和 `diagnosis_sessions` 表
- **结果**: 表不匹配导致永远查询不到真实数据

#### 问题2: 假数据生成机制
- 当查询不到会话数据时，系统创建通用假数据
- 假数据只包含：科室名称、默认风险等级、完成状态
- **缺失**: 真实对话历史、用户主诉、症状详情、AI分析结果、上传图片

#### 问题3: 数据流断裂
```
iOS创建Session → 用户对话存入Message表 → 点击生成病历 
→ 后端查询DermaSession (❌查不到) → 创建假数据 → 病历内容空洞
```

### 1.3 影响范围

- **用户影响**: 100%的病历生成功能不可用
- **科室影响**: 所有科室（皮肤科、心血管科、骨科、全科等）
- **数据影响**: 已生成的病历资料均为假数据，无法用于AI摘要生成

---

## 2. 目标与价值

### 2.1 产品目标

1. **统一会话架构**: 所有科室使用同一套会话数据模型
2. **消除假数据**: 病历资料100%基于真实对话数据生成
3. **完整数据链路**: 从对话到病历的数据流完整可追溯
4. **可扩展性**: 支持未来新增科室无需修改核心架构

### 2.2 用户价值

- 获得真实、完整的病历资料
- AI摘要基于真实对话，提供有价值的健康建议
- 病历可用于后续就医参考

### 2.3 技术价值

- 简化系统架构，降低维护成本
- 提高代码可读性和可维护性
- 减少数据冗余，提升查询性能

---

## 3. 现状分析

### 3.1 当前数据模型

#### 表1: sessions (通用会话表)
```sql
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    doctor_id INTEGER,
    agent_type VARCHAR(50) DEFAULT 'general',
    agent_state JSON,  -- 存储智能体状态
    last_message TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 表2: derma_sessions (皮肤科专用)
```sql
CREATE TABLE derma_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stage VARCHAR(20),
    chief_complaint TEXT,
    symptoms JSON,
    symptom_details JSON,
    skin_analyses JSON,
    possible_conditions JSON,
    risk_level VARCHAR(20),
    -- ... 20+ 个字段
);
```

#### 表3: diagnosis_sessions (全科专用)
```sql
CREATE TABLE diagnosis_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stage VARCHAR(20),
    chief_complaint TEXT,
    symptoms JSON,
    possible_diseases JSON,
    risk_level VARCHAR(20),
    -- ... 15+ 个字段
);
```

### 3.2 当前API接口

#### iOS使用的接口 (新)
- `POST /api/sessions` - 创建统一会话 → 写入 `sessions` 表
- `POST /api/sessions/{id}/messages` - 发送消息 → 写入 `messages` 表

#### 后端病历聚合接口 (旧)
- `POST /api/medical-events/aggregate` - 聚合会话到病历
  - 查询 `derma_sessions` 或 `diagnosis_sessions` 表 ❌
  - 查不到就创建假数据 ❌

#### 废弃但仍存在的接口
- `POST /api/derma/start` - 创建皮肤科会话 (iOS不再使用)
- `POST /api/diagnosis/start` - 创建全科会话 (iOS不再使用)

### 3.3 问题代码定位

**核心Bug位置**: `backend/app/routes/medical_events.py:433-458`

```python
# ❌ 错误逻辑
if request.session_type in ("derma", "dermatology"):
    session = db.query(DermaSession).filter(
        DermaSession.id == request.session_id,  # iOS传的是Session.id
        DermaSession.user_id == current_user.id
    ).first()
    
    if not session:  # 永远为True，因为表不匹配
        # 创建假数据
        session_data = {
            "session_id": request.session_id,
            "summary": f"{department}问诊",  # 通用描述
            "risk_level": "low",  # 默认值
            "stage": "completed"  # 默认值
        }
```

---

## 4. 解决方案

### 4.1 方案概述

**核心思路**: 统一会话数据模型，使用 `sessions` 表 + `agent_state` JSON字段存储所有科室的特定状态。

### 4.2 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案A: 统一Session表** | 架构简洁、易维护、扩展性强 | 需要数据迁移 | ⭐⭐⭐⭐⭐ |
| 方案B: 保留多表+桥接 | 改动小 | 架构复杂、维护成本高 | ⭐⭐ |
| 方案C: 仅修复Bug | 快速 | 治标不治本 | ⭐ |

**选择方案A**: 统一Session表架构

---

## 5. 技术架构设计

### 5.1 新架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      iOS 客户端                          │
│  UnifiedChatViewModel → APIService                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                    后端 API 层                           │
│  /api/sessions/* (统一会话接口)                         │
│  /api/medical-events/aggregate (重构后的聚合接口)       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                   数据持久层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   sessions   │  │   messages   │  │medical_events│ │
│  │ (统一会话表) │  │  (消息表)    │  │  (病历表)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 5.2 agent_state 结构设计

使用JSON字段存储不同科室的特定状态，保持灵活性：

```json
{
  "stage": "collecting",
  "progress": 60,
  "chief_complaint": "皮肤瘙痒红肿",
  "symptoms": ["瘙痒", "红肿", "脱皮"],
  "symptom_details": {
    "瘙痒": {
      "duration": "3天",
      "severity": "中度",
      "location": "手臂"
    }
  },
  "risk_level": "medium",
  "questions_asked": 5,
  "can_conclude": false,
  
  // 皮肤科特有字段
  "skin_analyses": [
    {
      "timestamp": "2026-01-15T10:30:00Z",
      "image_url": "https://...",
      "conditions": ["湿疹", "过敏性皮炎"],
      "confidence": 0.85
    }
  ],
  
  // 心血管科特有字段
  "ecg_interpretations": [
    {
      "timestamp": "2026-01-15T11:00:00Z",
      "report_url": "https://...",
      "findings": ["心律不齐"],
      "risk_level": "medium"
    }
  ],
  
  // 全科特有字段
  "possible_diseases": [
    {"name": "感冒", "probability": 0.7},
    {"name": "流感", "probability": 0.3}
  ],
  
  "recommendations": {
    "department": "内科",
    "urgency": "建议3天内就诊",
    "lifestyle": ["多喝水", "注意休息"]
  }
}
```

---

## 6. 数据模型设计

### 6.1 统一会话表 (sessions)

```python
class Session(Base):
    """统一会话表 - 支持所有科室"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    
    # 智能体信息
    agent_type = Column(String(50), default="general", nullable=False, index=True)
    agent_state = Column(JSON, nullable=True, default=dict)  # 核心：存储所有科室特定状态
    
    # 会话元信息
    last_message = Column(Text, nullable=True)
    status = Column(String(20), default="active", index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User")
    doctor = relationship("Doctor")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
```

### 6.2 消息表 (messages) - 保持不变

```python
class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    sender = Column(SQLEnum(SenderType), nullable=False)  # user/assistant
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text/image/structured
    attachments = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="messages")
```

### 6.3 病历事件表 (medical_events) - 保持不变

```python
class MedicalEvent(Base):
    """病历事件表"""
    __tablename__ = "medical_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    department = Column(String(50), nullable=False)
    agent_type = Column(SQLEnum(AgentType), default=AgentType.general)
    status = Column(SQLEnum(EventStatus), default=EventStatus.active)
    
    chief_complaint = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.low)
    
    ai_analysis = Column(JSON, nullable=True, default=dict)
    sessions = Column(JSON, nullable=True, default=list)  # 存储关联的会话摘要
    
    session_count = Column(Integer, default=0)
    attachment_count = Column(Integer, default=0)
    
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 6.4 废弃的表

以下表将被标记为废弃，数据迁移后删除：

- ❌ `derma_sessions`
- ❌ `diagnosis_sessions`

---

## 7. API接口设计

### 7.1 会话管理接口 (保持不变)

#### 创建会话
```http
POST /api/sessions
Content-Type: application/json

{
  "doctor_id": 1,
  "agent_type": "dermatology"
}

Response:
{
  "session_id": "abc-123-def",
  "agent_type": "dermatology",
  "status": "active",
  "created_at": "2026-01-15T10:00:00Z"
}
```

#### 发送消息
```http
POST /api/sessions/{session_id}/messages
Content-Type: application/json

{
  "content": "我的手臂有红疹",
  "attachments": [
    {
      "type": "image",
      "data": "base64_encoded_image"
    }
  ],
  "action": "conversation"  // 或 "analyze_skin", "interpret_report"
}

Response: (流式响应)
data: {"type": "chunk", "content": "根据您的描述"}
data: {"type": "chunk", "content": "，这可能是"}
data: {"type": "complete", "message": "...", "quick_options": [...]}
```

### 7.2 病历聚合接口 (重构)

#### 聚合会话到病历
```http
POST /api/medical-events/aggregate
Content-Type: application/json

{
  "session_id": "abc-123-def",
  "session_type": "dermatology"  // 用于确定科室，但不再用于查表
}

Response:
{
  "event_id": 42,
  "message": "会话已聚合到病历事件",
  "is_new_event": true,
  "session_summary": {
    "chief_complaint": "皮肤瘙痒红肿",
    "symptoms": ["瘙痒", "红肿", "脱皮"],
    "risk_level": "medium",
    "message_count": 15,
    "has_images": true
  }
}
```

**新的实现逻辑**:

```python
@router.post("/aggregate", response_model=AggregateResponse)
def aggregate_session(
    request: AggregateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    聚合会话到病历事件 (重构版本)
    
    核心改动：
    1. 从 sessions 表查询会话数据
    2. 从 messages 表获取完整对话历史
    3. 从 agent_state 提取症状、主诉等信息
    4. 不再创建假数据
    """
    # 1. 查询统一会话表
    session = db.query(Session).filter(
        Session.id == request.session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {request.session_id}"
        )
    
    # 2. 获取消息历史
    messages = db.query(Message).filter(
        Message.session_id == request.session_id
    ).order_by(Message.created_at).all()
    
    # 3. 从 agent_state 提取信息
    state = session.agent_state or {}
    chief_complaint = state.get("chief_complaint", "")
    symptoms = state.get("symptoms", [])
    risk_level = state.get("risk_level", "low")
    stage = state.get("stage", "completed")
    
    # 4. 构建完整的会话数据
    session_data = {
        "session_id": session.id,
        "session_type": session.agent_type,
        "timestamp": session.created_at.isoformat(),
        "summary": f"{get_department_name(session.agent_type)}问诊 - {chief_complaint}",
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "risk_level": risk_level,
        "stage": stage,
        "message_count": len(messages),
        "messages": [
            {
                "role": msg.sender.value,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "type": msg.message_type
            }
            for msg in messages[:50]  # 限制消息数量，避免JSON过大
        ],
        # 科室特定数据
        "skin_analyses": state.get("skin_analyses", []),
        "ecg_interpretations": state.get("ecg_interpretations", []),
        "possible_diseases": state.get("possible_diseases", []),
        "recommendations": state.get("recommendations", {})
    }
    
    # 5. 查找或创建病历事件
    department = get_department_name(session.agent_type)
    agent_type_enum = get_agent_type_enum(session.agent_type)
    
    today = datetime.utcnow().date()
    existing_event = db.query(MedicalEvent).filter(
        MedicalEvent.user_id == current_user.id,
        MedicalEvent.agent_type == agent_type_enum,
        MedicalEvent.status == EventStatus.active,
        MedicalEvent.start_time >= datetime.combine(today, datetime.min.time())
    ).first()
    
    is_new_event = False
    
    if existing_event:
        # 添加到现有事件
        sessions_list = existing_event.sessions or []
        if not any(s.get("session_id") == request.session_id for s in sessions_list):
            sessions_list.append(session_data)
            existing_event.sessions = sessions_list
            existing_event.session_count = len(sessions_list)
            # 更新主诉（如果当前会话有主诉）
            if chief_complaint and not existing_event.chief_complaint:
                existing_event.chief_complaint = chief_complaint
        event = existing_event
    else:
        # 创建新事件
        event = MedicalEvent(
            user_id=current_user.id,
            title=f"{department} {today.strftime('%Y-%m-%d')}",
            department=department,
            agent_type=agent_type_enum,
            chief_complaint=chief_complaint,
            risk_level=RiskLevel(risk_level),
            status=EventStatus.active,
            sessions=[session_data],
            session_count=1
        )
        db.add(event)
        is_new_event = True
    
    db.commit()
    db.refresh(event)
    
    logger.info(f"Successfully aggregated session {request.session_id} to event {event.id}")
    
    return AggregateResponse(
        event_id=str(event.id),
        message="会话已聚合到病历事件",
        is_new_event=is_new_event,
        session_summary={
            "chief_complaint": chief_complaint,
            "symptoms": symptoms,
            "risk_level": risk_level,
            "message_count": len(messages),
            "has_images": any(msg.message_type == "image" for msg in messages)
        }
    )
```

### 7.3 辅助函数

```python
def get_department_name(agent_type: str) -> str:
    """获取科室中文名称"""
    mapping = {
        "dermatology": "皮肤科",
        "cardiology": "心血管科",
        "orthopedics": "骨科",
        "general": "全科",
        "neurology": "神经科",
        "endocrinology": "内分泌科",
        "gastroenterology": "消化科",
        "respiratory": "呼吸科"
    }
    return mapping.get(agent_type, "全科")

def get_agent_type_enum(agent_type: str) -> AgentType:
    """将字符串转换为AgentType枚举"""
    mapping = {
        "dermatology": AgentType.derma,
        "cardiology": AgentType.cardio,
        "orthopedics": AgentType.ortho,
        "general": AgentType.general,
        "neurology": AgentType.neuro,
        "endocrinology": AgentType.endo,
        "gastroenterology": AgentType.gastro,
        "respiratory": AgentType.respiratory
    }
    return mapping.get(agent_type, AgentType.general)
```

### 7.4 废弃的接口

以下接口将被标记为废弃，但保留兼容性：

- `POST /api/derma/start` → 重定向到 `POST /api/sessions`
- `POST /api/derma/continue` → 重定向到 `POST /api/sessions/{id}/messages`
- `POST /api/diagnosis/start` → 重定向到 `POST /api/sessions`
- `POST /api/diagnosis/continue` → 重定向到 `POST /api/sessions/{id}/messages`

---

## 8. 数据迁移方案

### 8.1 迁移策略

采用**分阶段迁移**策略，确保零停机时间：

1. **Phase 1**: 新旧系统并行运行
2. **Phase 2**: 迁移历史数据
3. **Phase 3**: 切换流量到新系统
4. **Phase 4**: 废弃旧表

### 8.2 迁移脚本

#### 脚本1: 迁移 derma_sessions 到 sessions

```python
# backend/migrations/migrate_derma_sessions.py

from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.derma_session import DermaSession
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def migrate_derma_sessions():
    """
    将 derma_sessions 表的数据迁移到 sessions 表
    """
    db = SessionLocal()
    
    try:
        # 获取所有皮肤科会话
        derma_sessions = db.query(DermaSession).all()
        
        migrated_count = 0
        skipped_count = 0
        
        for derma in derma_sessions:
            # 检查是否已迁移
            existing = db.query(SessionModel).filter(
                SessionModel.id == derma.id
            ).first()
            
            if existing:
                logger.info(f"Session {derma.id} already exists, skipping")
                skipped_count += 1
                continue
            
            # 构建 agent_state
            agent_state = {
                "stage": derma.stage,
                "progress": derma.progress,
                "questions_asked": derma.questions_asked,
                "chief_complaint": derma.chief_complaint,
                "symptoms": derma.symptoms or [],
                "symptom_details": derma.symptom_details or {},
                "skin_location": derma.skin_location,
                "duration": derma.duration,
                "skin_analyses": derma.skin_analyses or [],
                "latest_analysis": derma.latest_analysis,
                "report_interpretations": derma.report_interpretations or [],
                "latest_interpretation": derma.latest_interpretation,
                "possible_conditions": derma.possible_conditions or [],
                "risk_level": derma.risk_level,
                "care_advice": derma.care_advice,
                "need_offline_visit": derma.need_offline_visit,
                "current_task": derma.current_task,
                "awaiting_image": derma.awaiting_image
            }
            
            # 创建新的 Session 记录
            new_session = SessionModel(
                id=derma.id,
                user_id=derma.user_id,
                doctor_id=None,  # derma_sessions 没有 doctor_id
                agent_type="dermatology",
                agent_state=agent_state,
                last_message=derma.current_response,
                status="active" if derma.stage != "completed" else "completed",
                created_at=derma.created_at,
                updated_at=derma.updated_at
            )
            
            db.add(new_session)
            migrated_count += 1
            
            if migrated_count % 100 == 0:
                db.commit()
                logger.info(f"Migrated {migrated_count} derma sessions")
        
        db.commit()
        
        logger.info(f"Migration complete: {migrated_count} migrated, {skipped_count} skipped")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_derma_sessions()
```

#### 脚本2: 迁移 diagnosis_sessions 到 sessions

```python
# backend/migrations/migrate_diagnosis_sessions.py

from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.diagnosis_session import DiagnosisSession
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def migrate_diagnosis_sessions():
    """
    将 diagnosis_sessions 表的数据迁移到 sessions 表
    """
    db = SessionLocal()
    
    try:
        diagnosis_sessions = db.query(DiagnosisSession).all()
        
        migrated_count = 0
        skipped_count = 0
        
        for diagnosis in diagnosis_sessions:
            existing = db.query(SessionModel).filter(
                SessionModel.id == diagnosis.id
            ).first()
            
            if existing:
                logger.info(f"Session {diagnosis.id} already exists, skipping")
                skipped_count += 1
                continue
            
            # 构建 agent_state
            agent_state = {
                "stage": diagnosis.stage,
                "progress": diagnosis.progress,
                "questions_asked": diagnosis.questions_asked,
                "chief_complaint": diagnosis.chief_complaint,
                "symptoms": diagnosis.symptoms or [],
                "symptom_details": diagnosis.symptom_details or {},
                "possible_diseases": diagnosis.possible_diseases or [],
                "risk_level": diagnosis.risk_level,
                "recommendations": diagnosis.recommendations or {},
                "can_conclude": diagnosis.can_conclude,
                "reasoning": diagnosis.reasoning
            }
            
            new_session = SessionModel(
                id=diagnosis.id,
                user_id=diagnosis.user_id,
                doctor_id=None,
                agent_type="general",
                agent_state=agent_state,
                last_message=diagnosis.current_question,
                status="active" if diagnosis.stage != "completed" else "completed",
                created_at=diagnosis.created_at,
                updated_at=diagnosis.updated_at
            )
            
            db.add(new_session)
            migrated_count += 1
            
            if migrated_count % 100 == 0:
                db.commit()
                logger.info(f"Migrated {migrated_count} diagnosis sessions")
        
        db.commit()
        
        logger.info(f"Migration complete: {migrated_count} migrated, {skipped_count} skipped")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_diagnosis_sessions()
```

#### 脚本3: 迁移消息历史

```python
# backend/migrations/migrate_messages.py

from sqlalchemy.orm import Session
from app.models.message import Message
from app.models.derma_session import DermaSession
from app.models.diagnosis_session import DiagnosisSession
from app.database import SessionLocal
import logging
import json

logger = logging.getLogger(__name__)

def migrate_derma_messages():
    """
    将 derma_sessions.messages (JSON) 迁移到 messages 表
    """
    db = SessionLocal()
    
    try:
        derma_sessions = db.query(DermaSession).all()
        
        migrated_count = 0
        
        for derma in derma_sessions:
            if not derma.messages:
                continue
            
            for msg_data in derma.messages:
                # 检查是否已存在
                existing = db.query(Message).filter(
                    Message.session_id == derma.id,
                    Message.content == msg_data.get("content"),
                    Message.created_at == msg_data.get("timestamp")
                ).first()
                
                if existing:
                    continue
                
                # 创建消息记录
                message = Message(
                    session_id=derma.id,
                    sender=msg_data.get("role", "user"),
                    content=msg_data.get("content", ""),
                    message_type=msg_data.get("task_type", "text"),
                    created_at=msg_data.get("timestamp")
                )
                
                db.add(message)
                migrated_count += 1
            
            if migrated_count % 500 == 0:
                db.commit()
                logger.info(f"Migrated {migrated_count} messages")
        
        db.commit()
        logger.info(f"Derma messages migration complete: {migrated_count} messages")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def migrate_diagnosis_messages():
    """
    将 diagnosis_sessions.messages (JSON) 迁移到 messages 表
    """
    db = SessionLocal()
    
    try:
        diagnosis_sessions = db.query(DiagnosisSession).all()
        
        migrated_count = 0
        
        for diagnosis in diagnosis_sessions:
            if not diagnosis.messages:
                continue
            
            for msg_data in diagnosis.messages:
                existing = db.query(Message).filter(
                    Message.session_id == diagnosis.id,
                    Message.content == msg_data.get("content"),
                    Message.created_at == msg_data.get("timestamp")
                ).first()
                
                if existing:
                    continue
                
                message = Message(
                    session_id=diagnosis.id,
                    sender=msg_data.get("role", "user"),
                    content=msg_data.get("content", ""),
                    message_type="text",
                    created_at=msg_data.get("timestamp")
                )
                
                db.add(message)
                migrated_count += 1
            
            if migrated_count % 500 == 0:
                db.commit()
                logger.info(f"Migrated {migrated_count} messages")
        
        db.commit()
        logger.info(f"Diagnosis messages migration complete: {migrated_count} messages")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_derma_messages()
    migrate_diagnosis_messages()
```

### 8.3 迁移执行计划

```bash
# 1. 备份数据库
pg_dump -U postgres home_health > backup_before_migration.sql

# 2. 执行迁移脚本
python backend/migrations/migrate_derma_sessions.py
python backend/migrations/migrate_diagnosis_sessions.py
python backend/migrations/migrate_messages.py

# 3. 验证数据完整性
python backend/migrations/verify_migration.py

# 4. 部署新代码
git pull origin main
docker-compose restart backend

# 5. 监控错误日志
tail -f logs/backend.log

# 6. 如果一切正常，7天后删除旧表
# ALTER TABLE derma_sessions RENAME TO derma_sessions_deprecated;
# ALTER TABLE diagnosis_sessions RENAME TO diagnosis_sessions_deprecated;
```

---

## 9. 实施路线图

### 9.1 总体时间线

**总工期**: 3周

```
Week 1: 准备与开发
Week 2: 测试与迁移
Week 3: 上线与监控
```

### 9.2 详细计划

#### Phase 1: 准备阶段 (Day 1-2)

**目标**: 完成技术方案评审和环境准备

| 任务 | 负责人 | 工时 | 交付物 |
|------|--------|------|--------|
| PRD评审会议 | 产品+技术 | 2h | 评审纪要 |
| 技术方案评审 | 后端团队 | 3h | 技术方案文档 |
| 数据库备份 | 运维 | 1h | 备份文件 |
| 创建测试环境 | 运维 | 2h | 测试环境URL |

#### Phase 2: 后端开发 (Day 3-7)

**目标**: 完成核心代码重构

| 任务 | 负责人 | 工时 | 交付物 |
|------|--------|------|--------|
| 修改 Session 模型 | 后端 | 4h | models/session.py |
| 重构 aggregate_session 接口 | 后端 | 8h | routes/medical_events.py |
| 编写迁移脚本 | 后端 | 6h | migrations/*.py |
| 添加单元测试 | 后端 | 8h | tests/*.py |
| 代码审查 | 技术负责人 | 2h | 审查报告 |

#### Phase 3: 数据迁移 (Day 8-10)

**目标**: 完成历史数据迁移

| 任务 | 负责人 | 工时 | 交付物 |
|------|--------|------|--------|
| 在测试环境执行迁移 | 后端 | 4h | 迁移日志 |
| 验证数据完整性 | 后端+QA | 6h | 验证报告 |
| 修复迁移问题 | 后端 | 4h | 修复记录 |
| 生产环境迁移演练 | 后端+运维 | 3h | 演练报告 |

#### Phase 4: 测试阶段 (Day 11-14)

**目标**: 完成全面测试

| 任务 | 负责人 | 工时 | 交付物 |
|------|--------|------|--------|
| 功能测试 | QA | 16h | 测试用例+报告 |
| 接口测试 | QA | 8h | 接口测试报告 |
| 性能测试 | QA | 6h | 性能测试报告 |
| iOS集成测试 | iOS+后端 | 8h | 集成测试报告 |
| Bug修复 | 后端 | 12h | Bug列表 |

#### Phase 5: 上线阶段 (Day 15-17)

**目标**: 灰度发布和全量上线

| 任务 | 负责人 | 工时 | 交付物 |
|------|--------|------|--------|
| 生产环境数据迁移 | 后端+运维 | 4h | 迁移日志 |
| 灰度发布 (10%流量) | 运维 | 2h | 灰度配置 |
| 监控指标 | 后端+运维 | 4h | 监控报告 |
| 扩大灰度 (50%流量) | 运维 | 1h | 灰度配置 |
| 全量发布 | 运维 | 1h | 发布记录 |
| 7x24小时值班 | 全员 | - | 值班表 |

#### Phase 6: 清理阶段 (Day 18-21)

**目标**: 废弃旧代码和旧表

| 任务 | 负责人 | 工时 | 交付物 |
|------|--------|------|--------|
| 监控7天无问题 | 运维 | - | 监控报告 |
| 标记旧接口为废弃 | 后端 | 2h | API文档 |
| 重命名旧表 | 运维 | 1h | SQL脚本 |
| 更新文档 | 产品+技术 | 4h | 技术文档 |
| 项目复盘会议 | 全员 | 2h | 复盘报告 |

### 9.3 里程碑

| 里程碑 | 日期 | 标准 |
|--------|------|------|
| M1: 开发完成 | Day 7 | 代码审查通过 |
| M2: 测试完成 | Day 14 | 所有测试用例通过 |
| M3: 灰度上线 | Day 15 | 10%流量无异常 |
| M4: 全量上线 | Day 17 | 100%流量无异常 |
| M5: 项目结项 | Day 21 | 旧表废弃，文档更新 |

---

## 10. 风险评估

### 10.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| **数据迁移失败** | 中 | 高 | 1. 提前在测试环境演练<br>2. 准备回滚脚本<br>3. 保留完整备份 |
| **性能下降** | 低 | 中 | 1. JSON字段添加索引<br>2. 查询优化<br>3. 缓存热点数据 |
| **数据不一致** | 中 | 高 | 1. 编写验证脚本<br>2. 双写验证<br>3. 数据对账 |
| **旧接口兼容性** | 低 | 低 | 1. 保留旧接口重定向<br>2. 逐步废弃 |

### 10.2 业务风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| **用户体验中断** | 低 | 高 | 1. 灰度发布<br>2. 快速回滚机制<br>3. 7x24值班 |
| **历史数据丢失** | 低 | 高 | 1. 多重备份<br>2. 迁移前后数据对比<br>3. 保留旧表30天 |
| **新Bug引入** | 中 | 中 | 1. 充分测试<br>2. 代码审查<br>3. 监控告警 |

### 10.3 回滚方案

#### 场景1: 迁移失败
```bash
# 1. 停止迁移脚本
kill -9 <migration_pid>

# 2. 恢复数据库
psql -U postgres home_health < backup_before_migration.sql

# 3. 回滚代码
git revert <commit_hash>
docker-compose restart backend
```

#### 场景2: 上线后发现严重Bug
```bash
# 1. 立即回滚代码到上一个稳定版本
git checkout <previous_stable_tag>
docker-compose restart backend

# 2. 切换流量到旧接口
# 修改 Nginx 配置，将 /api/medical-events/aggregate 路由到旧逻辑

# 3. 通知团队，紧急修复
```

---

## 11. 成功指标

### 11.1 功能指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| **病历生成成功率** | 100% | 监控 API 成功率 |
| **真实数据占比** | 100% | 抽样检查病历内容 |
| **数据完整性** | 100% | 验证脚本检查 |
| **API响应时间** | <500ms | APM监控 |

### 11.2 质量指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| **单元测试覆盖率** | >80% | pytest-cov |
| **接口测试通过率** | 100% | Postman测试集 |
| **代码审查通过** | 100% | Code Review |
| **零生产事故** | 0 | 事故统计 |

### 11.3 用户指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| **用户投诉率** | <1% | 客服反馈 |
| **病历查看率** | >50% | 埋点统计 |
| **病历分享率** | >20% | 埋点统计 |
| **用户满意度** | >4.5/5 | 用户调研 |

### 11.4 技术指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| **数据库查询优化** | <100ms | Slow query log |
| **内存使用** | <2GB | 服务器监控 |
| **CPU使用** | <50% | 服务器监控 |
| **错误率** | <0.1% | Sentry监控 |

---

## 12. 附录

### 12.1 相关文档

- [API文档](./API_DOCUMENTATION.md)
- [数据库设计文档](./DATABASE_DESIGN.md)
- [测试计划](./TEST_PLAN.md)
- [运维手册](./OPS_MANUAL.md)

### 12.2 团队分工

| 角色 | 姓名 | 职责 |
|------|------|------|
| 产品经理 | - | PRD编写、需求评审、验收 |
| 技术负责人 | - | 技术方案、架构设计、代码审查 |
| 后端工程师 | - | 代码开发、迁移脚本、Bug修复 |
| iOS工程师 | - | 客户端适配、集成测试 |
| QA工程师 | - | 测试用例、功能测试、回归测试 |
| 运维工程师 | - | 环境准备、数据迁移、监控告警 |

### 12.3 会议安排

| 会议 | 时间 | 参与人 | 议题 |
|------|------|--------|------|
| 需求评审会 | Day 1 | 全员 | PRD讲解、需求确认 |
| 技术方案评审 | Day 2 | 技术团队 | 技术方案讨论 |
| 每日站会 | 每天10:00 | 全员 | 进度同步、问题讨论 |
| 测试评审会 | Day 11 | 后端+QA | 测试计划评审 |
| 上线评审会 | Day 14 | 全员 | 上线准备检查 |
| 项目复盘会 | Day 21 | 全员 | 项目总结、经验分享 |

### 12.4 联系方式

- **紧急联系**: [技术负责人电话]
- **项目群**: [企业微信群]
- **监控告警**: [告警邮箱]
- **值班表**: [值班表链接]

---

## 13. 变更记录

| 版本 | 日期 | 修改人 | 修改内容 |
|------|------|--------|----------|
| v1.0 | 2026-01-15 | 产品团队 | 初始版本 |

---

**文档状态**: ✅ 已完成  
**下一步行动**: 需求评审会议

