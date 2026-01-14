# 技术设计文档（TDD）：病历事件自动创建机制

**文档版本**: V1.0  
**创建日期**: 2026-01-14  
**负责人**: 后端技术负责人 + iOS技术负责人  
**优先级**: P0（严重问题）  
**预计工期**: 3-5 天

---

## 1. 问题描述

### 1.1 当前状态
- **PRD要求**: 用户与科室智能体对话时自动创建病历事件，同一天同科室对话归入同一事件
- **现状分析**:
  - ✅ 后端已有 `medical_events` 表和完整API（`/api/medical-events`）
  - ✅ iOS已有病历展示层（`MedicalDossierView`）
  - ❌ **缺失**: 对话结束时自动触发事件创建的逻辑
  - ❌ **缺失**: 同一天同科室对话自动聚合到同一事件的机制

### 1.2 影响范围
- **用户体验**: 核心功能缺失，用户需手动创建病历，违背"自动记录"的产品定位
- **数据完整性**: 对话数据与病历事件未关联，无法生成完整病历
- **AI摘要功能**: 无法在对话结束时自动触发AI摘要生成

### 1.3 关键集成点分析
通过代码分析，找到以下关键集成点：

**iOS端对话流程**:
1. `DermaViewModel.swift` - 皮肤科对话（行315-385）
2. `UnifiedChatViewModel.swift` - 统一对话（行237-252）
3. 对话结束标志：`stage == .completed` 或用户主动退出

**后端API**:
1. `/api/derma/start` - 开始皮肤科会话
2. `/api/derma/continue` - 继续对话
3. `/api/medical-events` - 病历事件CRUD（已存在）

---

## 2. 技术方案设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     病历事件自动创建流程                          │
└─────────────────────────────────────────────────────────────────┘

[用户开始对话]
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. 会话创建阶段                                               │
│    - iOS: startSession() / initializeSession()              │
│    - 后端: POST /api/derma/start                             │
│    - 动作: 检查当日是否有同科室事件                           │
│           - 有 → 返回 existing_event_id                      │
│           - 无 → 创建新事件，返回 event_id                    │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. 对话进行阶段                                               │
│    - iOS: sendMessage() / uploadSkinPhoto()                  │
│    - 后端: POST /api/derma/continue                          │
│    - 动作: 将对话消息、附件关联到 event_id                    │
│           - 更新 event.updated_at                            │
│           - 增量更新 event.summary                            │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. 对话结束阶段                                               │
│    - iOS: handleStreamingComplete() 检测到 stage=completed   │
│    - 后端: 对话结束时触发                                     │
│    - 动作: 自动生成AI摘要                                     │
│           - 调用 POST /api/ai/summary/generate               │
│           - 更新 event.status = 'completed'                  │
│           - 更新 event.ai_analysis                           │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
[病历事件完成，用户可在病历资料夹查看]
```

---

### 2.2 数据库设计调整

#### 2.2.1 现有表结构（已存在）
```sql
-- medical_events 表（已存在）
CREATE TABLE medical_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200),
    department VARCHAR(50),
    agent_type VARCHAR(50),
    status VARCHAR(20),
    risk_level VARCHAR(20),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    summary TEXT,
    chief_complaint TEXT,
    ai_analysis JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- event_sessions 表（需要新增）
CREATE TABLE event_sessions (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES medical_events(id) ON DELETE CASCADE,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    session_type VARCHAR(50),
    timestamp TIMESTAMP,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- event_attachments 表（已存在）
CREATE TABLE event_attachments (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES medical_events(id) ON DELETE CASCADE,
    type VARCHAR(20),
    url TEXT,
    thumbnail_url TEXT,
    filename VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    description TEXT,
    is_important BOOLEAN DEFAULT FALSE,
    upload_time TIMESTAMP DEFAULT NOW()
);
```

#### 2.2.2 需要新增的表
```sql
-- 会话消息表（用于存储完整对话记录）
CREATE TABLE session_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    is_important BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- 存储附件引用、分析结果等
    FOREIGN KEY (session_id) REFERENCES event_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_session_messages_session_id ON session_messages(session_id);
CREATE INDEX idx_session_messages_timestamp ON session_messages(timestamp);
```

---

### 2.3 后端API设计

#### 2.3.1 修改现有对话API响应

**POST /api/derma/start**
```python
# 请求体（保持不变）
{
    "chief_complaint": "手臂出现红疹"
}

# 响应体（新增字段）
{
    "session_id": "derma_20260114_abc123",
    "message": "您好，我是皮肤科AI医生...",
    "stage": "inquiry",
    "progress": 10,
    "quick_options": [...],
    
    # 新增字段
    "event_id": 123,  # 关联的病历事件ID
    "is_new_event": true  # 是否是新创建的事件
}
```

**POST /api/derma/continue**
```python
# 响应体（新增字段）
{
    "session_id": "derma_20260114_abc123",
    "message": "根据您的描述...",
    "stage": "completed",  # 对话结束标志
    "progress": 100,
    
    # 新增字段
    "event_id": 123,
    "event_updated": true,  # 事件是否已更新
    "should_generate_summary": true  # 是否应该生成摘要
}
```

#### 2.3.2 新增智能聚合API

**POST /api/medical-events/smart-aggregate**
```python
# 请求体
{
    "user_id": 1,
    "session_id": "derma_20260114_abc123",
    "session_type": "dermatology",
    "department": "dermatology",
    "chief_complaint": "手臂红疹",
    "timestamp": "2026-01-14T10:30:00Z"
}

# 响应体
{
    "action": "create_new" | "append_existing",
    "event_id": 123,
    "reason": "当日无同科室事件，创建新事件",
    "event_title": "[皮肤科] 2026-01-14"
}
```

**逻辑规则**:
1. 查找用户当日（00:00-23:59）同科室的 `in_progress` 事件
2. 如果存在 → 返回 `append_existing`
3. 如果不存在 → 创建新事件，返回 `create_new`
4. 事件标题格式：`[科室名] YYYY-MM-DD` 或 `[科室名] 主诉摘要`

---

### 2.4 iOS端集成方案

#### 2.4.1 修改 DermaViewModel.swift

```swift
// 在 DermaViewModel 中新增属性
@Published var currentEventId: Int?
@Published var isNewEvent: Bool = false

// 修改 handleResponse 方法
private func handleResponse(_ response: DermaResponse) {
    sessionId = response.session_id
    stage = response.stageValue
    progress = response.progressValue
    
    // 新增：保存事件ID
    if let eventId = response.event_id {
        currentEventId = eventId
        isNewEvent = response.is_new_event ?? false
        
        print("[Derma] 关联病历事件: \(eventId), 新事件: \(isNewEvent)")
    }
    
    // 检测对话结束，触发摘要生成
    if stage == .completed, let eventId = currentEventId {
        Task {
            await triggerAISummaryGeneration(eventId: eventId)
        }
    }
    
    // ... 其他逻辑保持不变
}

// 新增：触发AI摘要生成
private func triggerAISummaryGeneration(eventId: Int) async {
    do {
        print("[Derma] 对话结束，自动生成AI摘要...")
        let summary = try await AIService.shared.generateSummary(
            eventId: String(eventId),
            forceRegenerate: true
        )
        print("[Derma] AI摘要生成成功")
        
        // 可选：显示提示"病历已保存"
        // showSuccessMessage("病历已自动保存到资料夹")
    } catch {
        print("[Derma] AI摘要生成失败: \(error)")
    }
}
```

#### 2.4.2 修改 UnifiedChatViewModel.swift

```swift
// 新增属性
@Published var currentEventId: Int?

// 修改 handleComplete 方法
private func handleComplete(_ response: UnifiedMessageResponse) {
    streamingMessageId = nil
    streamingContent = ""
    isSending = false
    
    // 新增：保存事件ID
    if let eventId = response.event_id {
        currentEventId = eventId
    }
    
    // 检测对话结束
    if response.is_conversation_ended == true, let eventId = currentEventId {
        Task {
            await triggerAISummaryGeneration(eventId: eventId)
        }
    }
    
    // ... 其他逻辑
}
```

#### 2.4.3 新增 DermaResponse 字段

```swift
// 在 DermaModels.swift 中修改
struct DermaResponse: Decodable {
    let session_id: String
    let message: String
    let stage: String
    let progress: Int
    let quick_options: [DermaQuickOption]?
    let skin_analysis: SkinAnalysisResult?
    let report_interpretation: ReportInterpretation?
    
    // 新增字段
    let event_id: Int?
    let is_new_event: Bool?
    let should_generate_summary: Bool?
}
```

---

### 2.5 后端实现细节

#### 2.5.1 创建 EventAggregator 服务

```python
# backend/app/services/event_aggregator.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import MedicalEvent, EventSession
from typing import Optional, Tuple

class EventAggregator:
    """病历事件智能聚合服务"""
    
    @staticmethod
    def find_or_create_event(
        db: Session,
        user_id: int,
        session_id: str,
        session_type: str,
        department: str,
        chief_complaint: Optional[str] = None
    ) -> Tuple[MedicalEvent, bool]:
        """
        查找或创建病历事件
        
        Returns:
            (event, is_new): 事件对象和是否为新创建
        """
        # 1. 查找当日同科室的进行中事件
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        existing_event = db.query(MedicalEvent).filter(
            MedicalEvent.user_id == user_id,
            MedicalEvent.agent_type == session_type,
            MedicalEvent.status == 'in_progress',
            MedicalEvent.start_time >= today_start,
            MedicalEvent.start_time < today_end
        ).first()
        
        if existing_event:
            # 2. 找到现有事件，关联会话
            EventAggregator._link_session_to_event(
                db, existing_event.id, session_id, session_type
            )
            return existing_event, False
        
        # 3. 创建新事件
        new_event = MedicalEvent(
            user_id=user_id,
            title=EventAggregator._generate_title(department, chief_complaint),
            department=department,
            agent_type=session_type,
            status='in_progress',
            risk_level='low',
            start_time=datetime.now(),
            summary=chief_complaint or "",
            chief_complaint=chief_complaint,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(new_event)
        db.flush()  # 获取ID但不提交
        
        # 4. 关联会话
        EventAggregator._link_session_to_event(
            db, new_event.id, session_id, session_type
        )
        
        db.commit()
        return new_event, True
    
    @staticmethod
    def _generate_title(department: str, chief_complaint: Optional[str]) -> str:
        """生成事件标题"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        dept_name = {
            'dermatology': '皮肤科',
            'cardiology': '心内科',
            'general': '全科'
        }.get(department, department)
        
        if chief_complaint and len(chief_complaint) <= 10:
            return f"{chief_complaint}"
        else:
            return f"[{dept_name}] {date_str}"
    
    @staticmethod
    def _link_session_to_event(
        db: Session,
        event_id: int,
        session_id: str,
        session_type: str
    ):
        """将会话关联到事件"""
        # 检查是否已关联
        existing = db.query(EventSession).filter(
            EventSession.session_id == session_id
        ).first()
        
        if not existing:
            event_session = EventSession(
                event_id=event_id,
                session_id=session_id,
                session_type=session_type,
                timestamp=datetime.now()
            )
            db.add(event_session)
            db.commit()
    
    @staticmethod
    def update_event_on_message(
        db: Session,
        event_id: int,
        message_role: str,
        message_content: str,
        attachment_url: Optional[str] = None
    ):
        """对话时更新事件"""
        event = db.query(MedicalEvent).filter(
            MedicalEvent.id == event_id
        ).first()
        
        if event:
            event.updated_at = datetime.now()
            
            # 如果有附件，记录到 event_attachments
            if attachment_url:
                from app.models import EventAttachment
                attachment = EventAttachment(
                    event_id=event_id,
                    type='image',
                    url=attachment_url,
                    upload_time=datetime.now()
                )
                db.add(attachment)
            
            db.commit()
    
    @staticmethod
    def complete_event(
        db: Session,
        event_id: int,
        final_summary: Optional[str] = None
    ):
        """完成事件"""
        event = db.query(MedicalEvent).filter(
            MedicalEvent.id == event_id
        ).first()
        
        if event:
            event.status = 'completed'
            event.end_time = datetime.now()
            event.updated_at = datetime.now()
            
            if final_summary:
                event.summary = final_summary
            
            db.commit()
```

#### 2.5.2 修改 derma.py 路由

```python
# backend/app/routes/derma.py

from app.services.event_aggregator import EventAggregator

@router.post("/start")
async def start_derma_session(
    request: DermaStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开始皮肤科会话（修改版）"""
    
    # 1. 创建会话ID
    session_id = f"derma_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 2. 智能聚合：查找或创建病历事件
    event, is_new = EventAggregator.find_or_create_event(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        session_type='dermatology',
        department='dermatology',
        chief_complaint=request.chief_complaint
    )
    
    # 3. 调用AI生成欢迎消息（保持原有逻辑）
    # ... AI调用代码 ...
    
    # 4. 返回响应（新增event_id字段）
    return {
        "session_id": session_id,
        "message": ai_response,
        "stage": "inquiry",
        "progress": 10,
        "quick_options": [...],
        "event_id": event.id,  # 新增
        "is_new_event": is_new  # 新增
    }

@router.post("/continue")
async def continue_derma_session(
    request: DermaContinueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """继续皮肤科对话（修改版）"""
    
    # 1. 获取会话关联的事件
    event_session = db.query(EventSession).filter(
        EventSession.session_id == request.session_id
    ).first()
    
    event_id = event_session.event_id if event_session else None
    
    # 2. 调用AI处理消息（保持原有逻辑）
    # ... AI调用代码 ...
    
    # 3. 更新事件
    if event_id:
        EventAggregator.update_event_on_message(
            db=db,
            event_id=event_id,
            message_role='user',
            message_content=request.current_message
        )
    
    # 4. 检测对话是否结束
    is_completed = ai_response.get('stage') == 'completed'
    should_generate_summary = is_completed
    
    # 5. 如果对话结束，标记事件完成
    if is_completed and event_id:
        EventAggregator.complete_event(db=db, event_id=event_id)
    
    # 6. 返回响应
    return {
        "session_id": request.session_id,
        "message": ai_response['message'],
        "stage": ai_response['stage'],
        "progress": ai_response['progress'],
        "event_id": event_id,
        "should_generate_summary": should_generate_summary
    }
```

---

## 3. 实施计划

### 3.1 开发任务分解

| 任务 | 负责人 | 工作量 | 依赖 |
|------|--------|--------|------|
| 1. 数据库迁移脚本 | 后端 | 0.5天 | - |
| 2. EventAggregator服务开发 | 后端 | 1天 | 任务1 |
| 3. 修改derma.py路由 | 后端 | 0.5天 | 任务2 |
| 4. 修改sessions.py路由（统一对话） | 后端 | 0.5天 | 任务2 |
| 5. iOS DermaViewModel集成 | iOS | 0.5天 | 任务3 |
| 6. iOS UnifiedChatViewModel集成 | iOS | 0.5天 | 任务4 |
| 7. 联调测试 | 全栈 | 1天 | 任务5,6 |
| 8. 回归测试 | 测试 | 0.5天 | 任务7 |

**总工期**: 3-5天

### 3.2 里程碑

- **Day 1**: 完成后端EventAggregator服务和数据库迁移
- **Day 2**: 完成后端API修改和iOS集成
- **Day 3**: 联调测试和bug修复
- **Day 4-5**: 回归测试和灰度发布

---

## 4. 测试方案

### 4.1 单元测试

**后端测试用例**:
```python
# test_event_aggregator.py

def test_create_new_event_first_time():
    """首次对话应创建新事件"""
    event, is_new = EventAggregator.find_or_create_event(
        db, user_id=1, session_id="test_001",
        session_type="dermatology", department="dermatology"
    )
    assert is_new == True
    assert event.status == "in_progress"

def test_append_to_existing_event_same_day():
    """同一天同科室第二次对话应复用事件"""
    # 第一次对话
    event1, is_new1 = EventAggregator.find_or_create_event(...)
    
    # 第二次对话（同一天）
    event2, is_new2 = EventAggregator.find_or_create_event(...)
    
    assert is_new2 == False
    assert event1.id == event2.id

def test_create_new_event_different_department():
    """不同科室应创建新事件"""
    event1, _ = EventAggregator.find_or_create_event(
        ..., session_type="dermatology"
    )
    event2, is_new = EventAggregator.find_or_create_event(
        ..., session_type="cardiology"
    )
    assert is_new == True
    assert event1.id != event2.id
```

### 4.2 集成测试

**测试场景**:
1. ✅ 用户首次与皮肤科AI对话 → 创建新事件
2. ✅ 用户同一天再次与皮肤科AI对话 → 复用事件
3. ✅ 用户同一天与心内科AI对话 → 创建新事件
4. ✅ 对话结束时自动生成AI摘要
5. ✅ 病历资料夹能正确显示事件

### 4.3 端到端测试

**测试流程**:
1. 用户登录 → 进入皮肤科AI
2. 开始对话，上传照片
3. 完成对话
4. 进入病历资料夹，验证事件已创建
5. 验证AI摘要已生成
6. 验证附件已关联

---

## 5. 风险评估与应对

### 5.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 数据库迁移失败 | 低 | 高 | 先在测试环境验证，准备回滚脚本 |
| 现有对话流程被破坏 | 中 | 高 | 充分的回归测试，灰度发布 |
| AI摘要生成超时 | 中 | 中 | 异步生成，不阻塞主流程 |
| 同一天多次对话误聚合 | 低 | 中 | 提供手动拆分功能（后续迭代） |

### 5.2 回滚方案

如果上线后出现严重问题：
1. 后端：回滚到上一版本代码
2. 数据库：保留新表，但不影响旧功能
3. iOS：降级处理，忽略 `event_id` 字段

---

## 6. 监控指标

### 6.1 关键指标

- **事件创建率**: 对话会话 → 病历事件的转化率（目标 >95%）
- **聚合准确率**: 同一天同科室对话正确聚合的比例（目标 >90%）
- **AI摘要生成成功率**: 对话结束后摘要生成成功率（目标 >98%）
- **响应时间**: 事件创建/更新的API响应时间（目标 <200ms）

### 6.2 日志埋点

```python
# 关键操作日志
logger.info(f"[EventAggregator] 用户{user_id}开始对话，事件ID:{event_id}，是否新建:{is_new}")
logger.info(f"[EventAggregator] 对话结束，触发AI摘要生成，事件ID:{event_id}")
logger.error(f"[EventAggregator] AI摘要生成失败，事件ID:{event_id}，错误:{error}")
```

---

## 7. 后续优化方向

### 7.1 V1.1 增强功能
- 智能拆分：用户可手动将误聚合的对话拆分为独立事件
- 智能合并：AI建议将相关事件合并
- 事件标题优化：使用AI生成更语义化的标题

### 7.2 V2.0 高级功能
- 跨天事件追踪：慢性病随访自动关联多天对话
- 家庭成员事件隔离：避免家庭账户事件混淆
- 事件模板：常见病症预设事件结构

---

## 8. 附录

### 8.1 相关文档
- PRD: `/PRD_多模态病历资料夹.md`
- 数据库设计: `/backend/migrations/add_medical_events_tables.py`
- API文档: `/backend/docs/AI_API_DOCUMENTATION.md`

### 8.2 代码位置
- iOS对话ViewModel: `/ios/xinlingyisheng/xinlingyisheng/ViewModels/DermaViewModel.swift`
- 后端对话路由: `/backend/app/routes/derma.py`
- 病历事件API: `/backend/app/routes/medical_events.py`

---

**审核状态**: 待审核  
**审核人**: 技术负责人 + 产品经理  
**预计上线时间**: 2026-01-17（本周五）
