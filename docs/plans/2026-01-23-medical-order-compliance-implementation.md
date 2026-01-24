# 医嘱执行监督系统实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一套完整的医嘱执行监督系统，包括AI医嘱生成、患者打卡、家属关怀、依从性分析、异常预警等核心功能。

**Architecture:** 基于现有 home-health 架构，复用用户系统、通知服务、语音服务。后端使用 FastAPI + SQLAlchemy，前端使用 SwiftUI (iOS) + React (Web医生端)，AI使用 LangChain + 通义千问。

**Tech Stack:** FastAPI, SQLAlchemy, LangChain, 通义千问 API, APScheduler, SwiftUI, React, Ant Design

---

## 目录

1. [Phase P0: 数据模型层](#phase-p0-数据模型层)
2. [Phase P0: 后端核心服务](#phase-p0-后端核心服务)
3. [Phase P0: API路由层](#phase-p0-api路由层)
4. [Phase P0: iOS患者端](#phase-p0-ios患者端)
5. [Phase P1: AI数值抽取](#phase-p1-ai数值抽取)
6. [Phase P1: 依从性分析](#phase-p1-依从性分析)
7. [Phase P1: 家属关怀](#phase-p1-家属关怀)
8. [Phase P1: 异常预警](#phase-p1-异常预警)
9. [Phase P2: Web医生端](#phase-p2-web医生端)

---

## Phase P0: 数据模型层

### Task 1: 创建医嘱类型枚举

**Files:**
- Create: `backend/app/models/medical_order.py`

**Step 1: Write the failing test**

Create test file: `tests/test_medical_order_models.py`

```python
import pytest
from backend.app.models.medical_order import OrderType, ScheduleType, OrderStatus, TaskStatus

def test_order_type_enum():
    assert OrderType.MEDICATION == "medication"
    assert OrderType.MONITORING == "monitoring"
    assert OrderType.BEHAVIOR == "behavior"
    assert OrderType.FOLLOWUP == "followup"

def test_schedule_type_enum():
    assert ScheduleType.ONCE == "once"
    assert ScheduleType.DAILY == "daily"
    assert ScheduleType.WEEKLY == "weekly"
    assert ScheduleType.CUSTOM == "custom"

def test_order_status_enum():
    assert OrderStatus.DRAFT == "draft"
    assert OrderStatus.ACTIVE == "active"
    assert OrderStatus.COMPLETED == "completed"
    assert OrderStatus.STOPPED == "stopped"

def test_task_status_enum():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.OVERDUE == "overdue"
    assert TaskStatus.SKIPPED == "skipped"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'backend.app.models.medical_order'"

**Step 3: Write minimal implementation**

Create: `backend/app/models/medical_order.py`

```python
"""
医嘱执行监督系统数据模型

包含：
- MedicalOrder: 医嘱主表
- TaskInstance: 任务实例表
- CompletionRecord: 打卡记录表
- FamilyBond: 患者家属关系表
"""
import enum
from datetime import date, datetime, time
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Text, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class OrderType(str, enum.Enum):
    """医嘱类型"""
    MEDICATION = "medication"    # 用药任务
    MONITORING = "monitoring"    # 监测任务
    BEHAVIOR = "behavior"        # 行为任务
    FOLLOWUP = "followup"        # 复诊任务


class ScheduleType(str, enum.Enum):
    """调度类型"""
    ONCE = "once"               # 一次性
    DAILY = "daily"             # 每日
    WEEKLY = "weekly"           # 每周
    CUSTOM = "custom"           # 自定义


class OrderStatus(str, enum.Enum):
    """医嘱状态"""
    DRAFT = "draft"             # 草稿
    ACTIVE = "active"           # 进行中
    COMPLETED = "completed"     # 已完成
    STOPPED = "stopped"         # 已停用


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"         # 待完成
    COMPLETED = "completed"     # 已完成
    OVERDUE = "overdue"         # 已超时
    SKIPPED = "skipped"         # 已跳过


class NotificationLevel(str, enum.Enum):
    """通知级别"""
    ALL = "all"                 # 全部通知
    ABNORMAL = "abnormal"       # 仅异常
    SUMMARY = "summary"         # 仅摘要
    NONE = "none"               # 不通知
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/medical_order.py tests/test_medical_order_models.py
git commit -m "feat(medical-order): add enums for order types and statuses"
```

---

### Task 2: 创建 MedicalOrder 模型

**Files:**
- Modify: `backend/app/models/medical_order.py`
- Modify: `tests/test_medical_order_models.py`

**Step 1: Write the failing test**

Add to `tests/test_medical_order_models.py`:

```python
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.medical_order import MedicalOrder, OrderType, ScheduleType, OrderStatus
from backend.app.models.user import User

def test_create_medical_order(db_session):
    # 创建测试用户
    user = User(phone="13800000001", nickname="测试患者")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 创建医嘱
    order = MedicalOrder(
        patient_id=user.id,
        doctor_id=None,  # AI生成时为空
        order_type=OrderType.MEDICATION,
        title="胰岛素注射",
        description="每日三餐前注射，每次4单位",
        schedule_type=ScheduleType.DAILY,
        start_date=date.today(),
        end_date=date.today().replace(month=date.today().month + 1),
        frequency="每日3次",
        reminder_times=["08:00", "12:00", "18:00"],
        ai_generated=True,
        status=OrderStatus.DRAFT
    )

    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    assert order.id is not None
    assert order.title == "胰岛素注射"
    assert order.ai_generated is True
    assert order.status == OrderStatus.DRAFT

@pytest.fixture
def db_session():
    """测试数据库会话"""
    from backend.app.database import engine, Base
    Base.metadata.create_all(bind=engine)
    session = Session(autoflush=False, autocommit=False, bind=engine)
    yield session
    session.rollback()
    session.close()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_models.py::test_create_medical_order -v`
Expected: FAIL with "MedicalOrder not defined" or similar

**Step 3: Write minimal implementation**

Add to `backend/app/models/medical_order.py` (after enums):

```python
class MedicalOrder(Base):
    """医嘱主表 - 医生审核后生效"""
    __tablename__ = "medical_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True, index=True)

    # 医嘱基本信息
    order_type = Column(SQLEnum(OrderType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 调度信息
    schedule_type = Column(SQLEnum(ScheduleType), nullable=False, default=ScheduleType.DAILY)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    frequency = Column(String(50), nullable=True)
    reminder_times = Column(JSON, nullable=True, default=list)  # ["08:00", "12:00", "18:00"]

    # AI 生成标记
    ai_generated = Column(Boolean, default=False)
    ai_session_id = Column(String(100), nullable=True, index=True)  # 关联的问诊会话

    # 状态
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.DRAFT, index=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    task_instances = relationship("TaskInstance", back_populates="order", cascade="all, delete-orphan")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("AdminUser", foreign_keys=[doctor_id])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_models.py::test_create_medical_order -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/medical_order.py tests/test_medical_order_models.py
git commit -m "feat(medical-order): add MedicalOrder model"
```

---

### Task 3: 创建 TaskInstance 模型

**Files:**
- Modify: `backend/app/models/medical_order.py`
- Modify: `tests/test_medical_order_models.py`

**Step 1: Write the failing test**

Add to `tests/test_medical_order_models.py`:

```python
def test_create_task_instance(db_session):
    from backend.app.models.medical_order import TaskInstance, TaskStatus

    # 创建测试用户和医嘱
    user = User(phone="13800000002", nickname="测试患者2")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    order = MedicalOrder(
        patient_id=user.id,
        order_type=OrderType.MEDICATION,
        title="早餐前胰岛素",
        schedule_type=ScheduleType.DAILY,
        start_date=date.today(),
        status=OrderStatus.ACTIVE
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    # 创建任务实例
    task = TaskInstance(
        order_id=order.id,
        patient_id=user.id,
        scheduled_date=date.today(),
        scheduled_time=time(8, 0),
        status=TaskStatus.PENDING
    )

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.status == TaskStatus.PENDING
    assert task.scheduled_time.hour == 8
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_models.py::test_create_task_instance -v`
Expected: FAIL with "TaskInstance not defined"

**Step 3: Write minimal implementation**

Add to `backend/app/models/medical_order.py`:

```python
class TaskInstance(Base):
    """任务实例表 - 系统根据医嘱自动生成的每日任务"""
    __tablename__ = "task_instances"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("medical_orders.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 调度信息
    scheduled_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(Time, nullable=False)

    # 状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)

    # 完成信息
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    order = relationship("MedicalOrder", back_populates="task_instances")
    completion_records = relationship("CompletionRecord", back_populates="task_instance", cascade="all, delete-orphan")
    patient_rel = relationship("User", foreign_keys=[patient_id])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_models.py::test_create_task_instance -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/medical_order.py tests/test_medical_order_models.py
git commit -m "feat(medical-order): add TaskInstance model"
```

---

### Task 4: 创建 CompletionRecord 模型

**Files:**
- Modify: `backend/app/models/medical_order.py`
- Modify: `tests/test_medical_order_models.py`

**Step 1: Write the failing test**

Add to `tests/test_medical_order_models.py`:

```python
def test_create_completion_record(db_session):
    from backend.app.models.medical_order import CompletionRecord, CompletionType

    # 创建测试数据
    user = User(phone="13800000003", nickname="测试患者3")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    order = MedicalOrder(
        patient_id=user.id,
        order_type=OrderType.MONITORING,
        title="早餐后血糖",
        schedule_type=ScheduleType.DAILY,
        start_date=date.today(),
        status=OrderStatus.ACTIVE
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    task = TaskInstance(
        order_id=order.id,
        patient_id=user.id,
        scheduled_date=date.today(),
        scheduled_time=time(9, 0),
        status=TaskStatus.PENDING
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # 创建打卡记录（血糖监测值）
    record = CompletionRecord(
        task_instance_id=task.id,
        completed_by=user.id,
        completion_type=CompletionType.VALUE,
        value={"value": 7.8, "unit": "mmol/L"},
        notes="早餐后血糖正常"
    )

    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    assert record.id is not None
    assert record.value["value"] == 7.8
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_models.py::test_create_completion_record -v`
Expected: FAIL with "CompletionRecord/CompletionType not defined"

**Step 3: Write minimal implementation**

Add to `backend/app/models/medical_order.py` (add CompletionType enum before class):

```python
class CompletionType(str, enum.Enum):
    """打卡类型"""
    CHECK = "check"              # 打卡确认
    PHOTO = "photo"              # 照片证明
    VALUE = "value"              # 数值录入
    MEDICATION = "medication"    # 用药记录


class CompletionRecord(Base):
    """打卡记录表 - 执行时的详细数据记录"""
    __tablename__ = "completion_records"

    id = Column(Integer, primary_key=True, index=True)
    task_instance_id = Column(Integer, ForeignKey("task_instances.id"), nullable=False, index=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 打卡类型和数据
    completion_type = Column(SQLEnum(CompletionType), nullable=False)
    value = Column(JSON, nullable=True, default=dict)  # 监测值，如 {"value": 7.8, "unit": "mmol/L"}
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task_instance = relationship("TaskInstance", back_populates="completion_records")
    completed_by_user = relationship("User", foreign_keys=[completed_by])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_models.py::test_create_completion_record -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/medical_order.py tests/test_medical_order_models.py
git commit -m "feat(medical-order): add CompletionRecord model"
```

---

### Task 5: 创建 FamilyBond 模型

**Files:**
- Modify: `backend/app/models/medical_order.py`
- Modify: `tests/test_medical_order_models.py`

**Step 1: Write the failing test**

Add to `tests/test_medical_order_models.py`:

```python
def test_create_family_bond(db_session):
    from backend.app.models.medical_order import FamilyBond, NotificationLevel

    # 创建患者和家属用户
    patient = User(phone="13800000004", nickname="患者")
    family = User(phone="13800000005", nickname="家属")
    db_session.add_all([patient, family])
    db_session.commit()
    db_session.refresh(patient)
    db_session.refresh(family)

    # 创建家属关系
    bond = FamilyBond(
        patient_id=patient.id,
        family_member_id=family.id,
        relationship="子女",
        notification_level=NotificationLevel.ALL
    )

    db_session.add(bond)
    db_session.commit()
    db_session.refresh(bond)

    assert bond.id is not None
    assert bond.relationship == "子女"
    assert bond.notification_level == NotificationLevel.ALL
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_models.py::test_create_family_bond -v`
Expected: FAIL with "FamilyBond not defined"

**Step 3: Write minimal implementation**

Add to `backend/app/models/medical_order.py`:

```python
class FamilyBond(Base):
    """患者家属关系表"""
    __tablename__ = "family_bonds"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    family_member_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    relationship = Column(String(50), nullable=False)  # 父母/子女/配偶等
    notification_level = Column(SQLEnum(NotificationLevel), default=NotificationLevel.ALL)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    patient = relationship("User", foreign_keys=[patient_id])
    family_member = relationship("User", foreign_keys=[family_member_id])

    # 唯一约束：同一患者和家属只能有一条关系
    __table_args__ = (
        # 使用 Index 创建唯一约束
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_models.py::test_create_family_bond -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/medical_order.py tests/test_medical_order_models.py
git commit -m "feat(medical-order): add FamilyBond model"
```

---

### Task 6: 更新 models/__init__.py 导出

**Files:**
- Modify: `backend/app/models/__init__.py`

**Step 1: Add imports**

```python
# ... existing imports ...
from .medical_order import (
    MedicalOrder, TaskInstance, CompletionRecord, FamilyBond,
    OrderType, ScheduleType, OrderStatus, TaskStatus,
    CompletionType, NotificationLevel
)

__all__ = [
    # ... existing exports ...
    "MedicalOrder", "TaskInstance", "CompletionRecord", "FamilyBond",
    "OrderType", "ScheduleType", "OrderStatus", "TaskStatus",
    "CompletionType", "NotificationLevel"
]
```

**Step 2: Run tests to verify**

Run: `pytest tests/test_medical_order_models.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add backend/app/models/__init__.py
git commit -m "feat(medical-order): export medical order models"
```

---

## Phase P0: 后端核心服务

### Task 7: 创建医嘱管理服务

**Files:**
- Create: `backend/app/services/medical_order_service.py`
- Create: `tests/test_medical_order_service.py`

**Step 1: Write the failing test**

```python
# tests/test_medical_order_service.py
import pytest
from datetime import date, time
from backend.app.services.medical_order_service import MedicalOrderService
from backend.app.models.medical_order import OrderType, ScheduleType, OrderStatus

def test_create_draft_order(db_session, test_user):
    """测试创建草稿医嘱"""
    service = MedicalOrderService(db_session)

    order_data = {
        "patient_id": test_user.id,
        "order_type": OrderType.MEDICATION,
        "title": "胰岛素注射",
        "description": "每日三餐前注射，每次4单位",
        "schedule_type": ScheduleType.DAILY,
        "start_date": date.today(),
        "end_date": date.today().replace(month=date.today().month + 1),
        "frequency": "每日3次",
        "reminder_times": ["08:00", "12:00", "18:00"],
        "ai_generated": True
    }

    order = service.create_draft_order(order_data)

    assert order.id is not None
    assert order.title == "胰岛素注射"
    assert order.status == OrderStatus.DRAFT
    assert order.ai_generated is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backend/app/services/medical_order_service.py
"""
医嘱管理服务

包含：
- 医嘱 CRUD 操作
- 医嘱激活（生成任务实例）
- 任务生成逻辑
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.medical_order import (
    MedicalOrder, TaskInstance, OrderType, ScheduleType,
    OrderStatus, TaskStatus, CompletionRecord
)
from ..models.user import User


class MedicalOrderService:
    """医嘱管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_draft_order(self, data: Dict[str, Any]) -> MedicalOrder:
        """
        创建草稿医嘱

        通常由 AI 从问诊对话中自动生成，或由医生手动创建
        """
        # 处理 reminder_times 格式
        reminder_times = data.get("reminder_times", [])
        if isinstance(reminder_times[0], str) if reminder_times else False:
            # 将 "08:00" 转换为 time 对象（如果需要）
            pass  # 暂时保持字符串存储

        order = MedicalOrder(
            patient_id=data["patient_id"],
            doctor_id=data.get("doctor_id"),
            order_type=data["order_type"],
            title=data["title"],
            description=data.get("description"),
            schedule_type=data["schedule_type"],
            start_date=data["start_date"],
            end_date=data.get("end_date"),
            frequency=data.get("frequency"),
            reminder_times=reminder_times,
            ai_generated=data.get("ai_generated", False),
            ai_session_id=data.get("ai_session_id"),
            status=OrderStatus.DRAFT
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def activate_order(self, order_id: int) -> MedicalOrder:
        """
        激活医嘱（医生审核通过）

        激活后开始生成每日任务实例
        """
        order = self.db.query(MedicalOrder).filter(
            MedicalOrder.id == order_id
        ).first()

        if not order:
            raise ValueError(f"医嘱不存在: {order_id}")

        if order.status != OrderStatus.DRAFT:
            raise ValueError(f"只有草稿状态的医嘱可以激活")

        order.status = OrderStatus.ACTIVE

        # 生成初始任务实例
        self._generate_task_instances(order)

        self.db.commit()
        self.db.refresh(order)

        return order

    def _generate_task_instances(self, order: MedicalOrder) -> List[TaskInstance]:
        """
        为医嘱生成任务实例

        根据调度类型和提醒时间生成任务
        """
        instances = []

        if order.schedule_type == ScheduleType.ONCE:
            # 一次性任务
            instance = TaskInstance(
                order_id=order.id,
                patient_id=order.patient_id,
                scheduled_date=order.start_date,
                scheduled_time=self._parse_time(order.reminder_times[0]) if order.reminder_times else time(9, 0),
                status=TaskStatus.PENDING
            )
            instances.append(instance)

        elif order.schedule_type == ScheduleType.DAILY:
            # 每日任务 - 生成未来7天的任务
            for days_ahead in range(7):
                task_date = order.start_date + timedelta(days=days_ahead)

                # 如果有结束日期，不超过结束日期
                if order.end_date and task_date > order.end_date:
                    break

                # 为每个提醒时间创建任务
                for reminder in order.reminder_times:
                    instance = TaskInstance(
                        order_id=order.id,
                        patient_id=order.patient_id,
                        scheduled_date=task_date,
                        scheduled_time=self._parse_time(reminder),
                        status=TaskStatus.PENDING
                    )
                    instances.append(instance)

        # 批量添加
        self.db.add_all(instances)
        self.db.commit()

        return instances

    def _parse_time(self, time_str: str) -> time:
        """解析时间字符串 HH:MM"""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except (ValueError, AttributeError):
            return time(9, 0)  # 默认9点

    def get_patient_orders(
        self,
        patient_id: int,
        status: Optional[OrderStatus] = None,
        active_date: Optional[date] = None
    ) -> List[MedicalOrder]:
        """
        获取患者的医嘱列表

        active_date: 如果指定，只返回该日期有效的医嘱
        """
        query = self.db.query(MedicalOrder).filter(
            MedicalOrder.patient_id == patient_id
        )

        if status:
            query = query.filter(MedicalOrder.status == status)

        # 筛选指定日期有效的医嘱
        if active_date:
            query = query.filter(
                and_(
                    MedicalOrder.start_date <= active_date,
                    MedicalOrder.end_date >= active_date if MedicalOrder.end_date is not None else True
                )
            )

        return query.order_by(MedicalOrder.created_at.desc()).all()

    def get_patient_tasks(
        self,
        patient_id: int,
        task_date: date,
        status: Optional[TaskStatus] = None
    ) -> List[TaskInstance]:
        """
        获取患者指定日期的任务列表
        """
        query = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == task_date
        )

        if status:
            query = query.filter(TaskInstance.status == status)

        return query.order_by(TaskInstance.scheduled_time).all()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/medical_order_service.py tests/test_medical_order_service.py
git commit -m "feat(medical-order): add MedicalOrderService"
```

---

### Task 8: 创建任务调度器

**Files:**
- Create: `backend/app/services/task_scheduler.py`
- Create: `tests/test_task_scheduler.py`

**Step 1: Write the failing test**

```python
# tests/test_task_scheduler.py
import pytest
from datetime import date, time, timedelta
from backend.app.services.task_scheduler import TaskScheduler

def test_generate_daily_tasks(db_session, test_user, medical_order):
    """测试生成每日任务"""
    scheduler = TaskScheduler(db_session)

    # 生成明天的任务
    tomorrow = date.today() + timedelta(days=1)
    tasks = scheduler.generate_daily_tasks(medical_order.id, tomorrow)

    assert len(tasks) > 0
    assert all(t.scheduled_date == tomorrow for t in tasks)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_task_scheduler.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backend/app/services/task_scheduler.py
"""
任务调度服务

负责：
- 每日定时生成任务实例
- 检测超时任务
- 标记过期待完成的任务
"""
from typing import List
from datetime import date, datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.medical_order import MedicalOrder, TaskInstance, OrderStatus, TaskStatus


class TaskScheduler:
    """任务调度器"""

    def __init__(self, db: Session):
        self.db = db

    def generate_daily_tasks(self, order_id: int, target_date: date) -> List[TaskInstance]:
        """
        为指定医嘱生成指定日期的任务实例

        通常由定时任务每晚调用，生成第二天的任务
        """
        order = self.db.query(MedicalOrder).filter(
            MedicalOrder.id == order_id
        ).first()

        if not order:
            raise ValueError(f"医嘱不存在: {order_id}")

        if order.status != OrderStatus.ACTIVE:
            return []

        # 检查是否在有效期内
        if target_date < order.start_date:
            return []
        if order.end_date and target_date > order.end_date:
            return []

        # 检查是否已生成
        existing = self.db.query(TaskInstance).filter(
            TaskInstance.order_id == order_id,
            TaskInstance.scheduled_date == target_date
        ).first()

        if existing:
            return []  # 已生成

        instances = []
        reminder_times = order.reminder_times or ["09:00"]

        for reminder in reminder_times:
            instance = TaskInstance(
                order_id=order.id,
                patient_id=order.patient_id,
                scheduled_date=target_date,
                scheduled_time=self._parse_time(reminder),
                status=TaskStatus.PENDING
            )
            instances.append(instance)

        self.db.add_all(instances)
        self.db.commit()

        return instances

    def mark_overdue_tasks(self) -> int:
        """
        标记超时未完成的任务

        应该每分钟或每小时运行一次
        """
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()

        # 查找所有应该已完成但未完成的任务
        overdue_tasks = self.db.query(TaskInstance).filter(
            TaskInstance.status == TaskStatus.PENDING,
            TaskInstance.scheduled_date < current_date
        ).all()

        # 加上当天的超时任务
        today_overdue = self.db.query(TaskInstance).filter(
            TaskInstance.status == TaskStatus.PENDING,
            TaskInstance.scheduled_date == current_date,
            TaskInstance.scheduled_time < current_time
        ).all()

        all_overdue = overdue_tasks + today_overdue

        for task in all_overdue:
            task.status = TaskStatus.OVERDUE

        self.db.commit()

        return len(all_overdue)

    def generate_all_active_orders_tasks(self, target_date: date) -> int:
        """
        为所有活跃医嘱生成指定日期的任务

        由定时任务调用
        """
        active_orders = self.db.query(MedicalOrder).filter(
            MedicalOrder.status == OrderStatus.ACTIVE
        ).all()

        total_instances = 0
        for order in active_orders:
            instances = self.generate_daily_tasks(order.id, target_date)
            total_instances += len(instances)

        return total_instances

    def _parse_time(self, time_str: str) -> time:
        """解析时间字符串"""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except (ValueError, AttributeError):
            return time(9, 0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_task_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/task_scheduler.py tests/test_task_scheduler.py
git commit -m "feat(medical-order): add TaskScheduler service"
```

---

### Task 9: 创建依从性计算服务

**Files:**
- Create: `backend/app/services/compliance_service.py`
- Create: `tests/test_compliance_service.py`

**Step 1: Write the failing test**

```python
# tests/test_compliance_service.py
import pytest
from datetime import date, timedelta
from backend.app.services.compliance_service import ComplianceService

def test_calculate_daily_compliance(db_session, test_user):
    """测试计算日依从性"""
    service = ComplianceService(db_session)

    compliance = service.calculate_daily_compliance(test_user.id, date.today())

    assert "total" in compliance
    assert "completed" in compliance
    assert "rate" in compliance
    assert 0 <= compliance["rate"] <= 1

def test_calculate_weekly_compliance(db_session, test_user):
    """测试计算周依从性"""
    service = ComplianceService(db_session)

    weekly = service.calculate_weekly_compliance(test_user.id)

    assert "daily_rates" in weekly
    assert "average_rate" in weekly
    assert len(weekly["daily_rates"]) <= 7
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_compliance_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backend/app/services/compliance_service.py
"""
依从性计算服务

负责：
- 计算患者日/周/医嘱周期依从性
- 生成依从性报告数据
"""
from typing import Dict, List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.medical_order import TaskInstance, TaskStatus


class ComplianceService:
    """依从性计算服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_daily_compliance(self, patient_id: int, target_date: date) -> Dict:
        """
        计算指定日期的依从性

        返回:
        {
            "total": 总任务数,
            "completed": 完成数,
            "overdue": 超时数,
            "pending": 待完成数,
            "rate": 依从率 (0-1)
        }
        """
        # 查询当日所有任务
        tasks = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == target_date
        ).all()

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        overdue = sum(1 for t in tasks if t.status == TaskStatus.OVERDUE)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

        rate = completed / total if total > 0 else 0

        return {
            "date": target_date.isoformat(),
            "total": total,
            "completed": completed,
            "overdue": overdue,
            "pending": pending,
            "rate": round(rate, 2)
        }

    def calculate_weekly_compliance(self, patient_id: int) -> Dict:
        """
        计算近7天的依从性趋势

        返回:
        {
            "daily_rates": [日依从率列表],
            "average_rate": 平均依从率,
            "dates": [日期列表]
        }
        """
        today = date.today()
        daily_rates = []
        dates = []

        for i in range(6, -1, -1):  # 从6天前到今天
            target_date = today - timedelta(days=i)
            compliance = self.calculate_daily_compliance(patient_id, target_date)
            daily_rates.append(compliance["rate"])
            dates.append(target_date.isoformat())

        average_rate = sum(daily_rates) / len(daily_rates) if daily_rates else 0

        return {
            "daily_rates": daily_rates,
            "average_rate": round(average_rate, 2),
            "dates": dates
        }

    def calculate_order_compliance(self, order_id: int) -> Dict:
        """
        计算整个医嘱周期的依从性

        返回:
        {
            "order_id": 医嘱ID,
            "total": 总任务数,
            "completed": 完成数,
            "rate": 依从率,
            "start_date": 开始日期,
            "end_date": 结束日期
        }
        """
        tasks = self.db.query(TaskInstance).filter(
            TaskInstance.order_id == order_id
        ).all()

        if not tasks:
            return {
                "order_id": order_id,
                "total": 0,
                "completed": 0,
                "rate": 0,
                "start_date": None,
                "end_date": None
            }

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        rate = completed / total if total > 0 else 0

        # 获取日期范围
        dates = [t.scheduled_date for t in tasks]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None

        return {
            "order_id": order_id,
            "total": total,
            "completed": completed,
            "rate": round(rate, 2),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }

    def get_abnormal_records(
        self,
        patient_id: int,
        days: int = 30
    ) -> List[Dict]:
        """
        获取异常记录（超时未完成的任务）

        返回最近N天的异常记录
        """
        since_date = date.today() - timedelta(days=days)

        tasks = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date >= since_date,
            TaskInstance.status == TaskStatus.OVERDUE
        ).order_by(TaskInstance.scheduled_date.desc()).all()

        return [
            {
                "task_id": t.id,
                "date": t.scheduled_date.isoformat(),
                "time": t.scheduled_time.strftime("%H:%M"),
                "order_title": t.order.title if t.order else "未知医嘱"
            }
            for t in tasks
        ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_compliance_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/compliance_service.py tests/test_compliance_service.py
git commit -m "feat(medical-order): add ComplianceService"
```

---

## Phase P0: API路由层

### Task 10: 创建医嘱 Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/medical_order.py`
- Create: `tests/test_medical_order_schemas.py`

**Step 1: Write the failing test**

```python
# tests/test_medical_order_schemas.py
import pytest
from datetime import date, time
from backend.app.schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderResponse,
    TaskInstanceResponse, CompletionRecordRequest
)

def test_medical_order_create_schema():
    """测试医嘱创建请求 schema"""
    data = {
        "order_type": "medication",
        "title": "胰岛素注射",
        "description": "每日三餐前注射",
        "schedule_type": "daily",
        "start_date": "2024-01-23",
        "end_date": "2024-02-23",
        "frequency": "每日3次",
        "reminder_times": ["08:00", "12:00", "18:00"]
    }

    schema = MedicalOrderCreateRequest(**data)

    assert schema.order_type == "medication"
    assert schema.title == "胰岛素注射"
    assert len(schema.reminder_times) == 3

def test_completion_record_value_schema():
    """测试打卡记录数值 schema"""
    data = {
        "task_instance_id": 1,
        "completion_type": "value",
        "value": {"value": 7.8, "unit": "mmol/L"},
        "notes": "早餐后血糖正常"
    }

    schema = CompletionRecordRequest(**data)

    assert schema.completion_type == "value"
    assert schema.value["value"] == 7.8
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_order_schemas.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backend/app/schemas/medical_order.py
"""
医嘱执行监督系统 Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime


# ========== 请求 Schemas ==========

class MedicalOrderCreateRequest(BaseModel):
    """创建医嘱请求"""
    order_type: str = Field(..., description="医嘱类型")
    title: str = Field(..., max_length=200, description="医嘱标题")
    description: Optional[str] = Field(None, description="详细说明")
    schedule_type: str = Field(..., description="调度类型")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    frequency: Optional[str] = Field(None, max_length=50, description="频次")
    reminder_times: Optional[List[str]] = Field(default_factory=list, description="提醒时间")
    ai_generated: bool = Field(False, description="是否AI生成")
    ai_session_id: Optional[str] = Field(None, description="关联的问诊会话ID")


class MedicalOrderUpdateRequest(BaseModel):
    """更新医嘱请求"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    end_date: Optional[date] = None
    frequency: Optional[str] = None
    reminder_times: Optional[List[str]] = None


class ActivateOrderRequest(BaseModel):
    """激活医嘱请求"""
    confirm: bool = Field(..., description="确认激活")


class CompletionRecordRequest(BaseModel):
    """打卡记录请求"""
    task_instance_id: int = Field(..., description="任务实例ID")
    completion_type: str = Field(..., description="打卡类型")
    value: Optional[Dict[str, Any]] = Field(None, description="监测值")
    photo_url: Optional[str] = Field(None, max_length=500, description="照片URL")
    notes: Optional[str] = Field(None, description="备注")


# ========== 响应 Schemas ==========

class MedicalOrderResponse(BaseModel):
    """医嘱响应"""
    id: int
    patient_id: int
    doctor_id: Optional[int]
    order_type: str
    title: str
    description: Optional[str]
    schedule_type: str
    start_date: date
    end_date: Optional[date]
    frequency: Optional[str]
    reminder_times: List[str]
    ai_generated: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskInstanceResponse(BaseModel):
    """任务实例响应"""
    id: int
    order_id: int
    patient_id: int
    scheduled_date: date
    scheduled_time: time
    status: str
    completed_at: Optional[datetime]
    completion_notes: Optional[str]

    # 关联医嘱信息
    order_title: Optional[str] = None
    order_type: Optional[str] = None

    class Config:
        from_attributes = True


class CompletionRecordResponse(BaseModel):
    """打卡记录响应"""
    id: int
    task_instance_id: int
    completed_by: int
    completion_type: str
    value: Optional[Dict[str, Any]]
    photo_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceResponse(BaseModel):
    """依从性响应"""
    date: Optional[str]
    total: int
    completed: int
    overdue: int
    pending: int
    rate: float


class WeeklyComplianceResponse(BaseModel):
    """周依从性响应"""
    daily_rates: List[float]
    average_rate: float
    dates: List[str]


class TaskListResponse(BaseModel):
    """任务列表响应"""
    date: str
    pending: List[TaskInstanceResponse]
    completed: List[TaskInstanceResponse]
    overdue: List[TaskInstanceResponse]
    summary: ComplianceResponse


class FamilyBondCreateRequest(BaseModel):
    """创建家属关系请求"""
    patient_id: int
    family_member_phone: str = Field(..., description="家属手机号")
    relationship: str = Field(..., max_length=50, description="关系")
    notification_level: str = Field("all", description="通知级别")


class FamilyBondResponse(BaseModel):
    """家属关系响应"""
    id: int
    patient_id: int
    family_member_id: int
    relationship: str
    notification_level: str
    family_member_name: Optional[str] = None
    family_member_phone: Optional[str] = None

    class Config:
        from_attributes = True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_medical_order_schemas.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/medical_order.py tests/test_medical_order_schemas.py
git commit -m "feat(medical-order): add Pydantic schemas"
```

---

### Task 11: 创建医嘱 API 路由

**Files:**
- Create: `backend/app/routes/medical_orders.py`
- Create: `tests/test_medical_orders_routes.py`

**Step 1: Write the failing test**

```python
# tests/test_medical_orders_routes.py
import pytest
from fastapi.testclient import TestClient

def test_create_order(client, auth_headers, test_user):
    """测试创建医嘱"""
    data = {
        "order_type": "medication",
        "title": "胰岛素注射",
        "schedule_type": "daily",
        "start_date": "2024-01-23",
        "reminder_times": ["08:00", "12:00", "18:00"]
    }

    response = client.post("/medical-orders", json=data, headers=auth_headers)

    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "胰岛素注射"
    assert result["status"] == "draft"

def test_get_patient_orders(client, auth_headers, test_user):
    """测试获取患者医嘱列表"""
    response = client.get("/medical-orders", headers=auth_headers)

    assert response.status_code == 200
    result = response.json()
    assert "orders" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_medical_orders_routes.py -v`
Expected: FAIL with "404 Not Found" (route not registered)

**Step 3: Write minimal implementation**

```python
# backend/app/routes/medical_orders.py
"""
医嘱执行监督 API 路由

包含：
- 医嘱 CRUD
- 任务查询
- 打卡操作
- 依从性查询
"""
import logging
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_order import (
    MedicalOrder, TaskInstance, CompletionRecord, OrderStatus, TaskStatus
)
from ..schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderUpdateRequest, MedicalOrderResponse,
    ActivateOrderRequest, TaskInstanceResponse, TaskListResponse,
    CompletionRecordRequest, CompletionRecordResponse,
    ComplianceResponse, WeeklyComplianceResponse
)
from ..services.medical_order_service import MedicalOrderService
from ..services.compliance_service import ComplianceService

router = APIRouter(prefix="/medical-orders", tags=["medical-orders"])
logger = logging.getLogger(__name__)


# ============= 医嘱 CRUD =============

@router.post("", response_model=MedicalOrderResponse, status_code=status.HTTP_201_CREATED)
def create_medical_order(
    request: MedicalOrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建医嘱（草稿状态）

    通常由 AI 从问诊对话自动生成，或由医生手动创建
    """
    service = MedicalOrderService(db)

    # 验证患者是当前用户或医生为患者创建
    # TODO: 添加医生权限检查

    order_data = request.model_dump()
    order_data["patient_id"] = current_user.id  # 暂时只允许为自己创建

    order = service.create_draft_order(order_data)

    return MedicalOrderResponse.model_validate(order)


@router.get("", response_model=List[MedicalOrderResponse])
def get_medical_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的医嘱列表"""
    query = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == current_user.id
    )

    if status_filter:
        query = query.filter(MedicalOrder.status == OrderStatus(status_filter))

    orders = query.order_by(MedicalOrder.created_at.desc()).all()

    return [MedicalOrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=MedicalOrderResponse)
def get_medical_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取医嘱详情"""
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id,
        MedicalOrder.patient_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    return MedicalOrderResponse.model_validate(order)


@router.put("/{order_id}", response_model=MedicalOrderResponse)
def update_medical_order(
    order_id: int,
    request: MedicalOrderUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新医嘱（仅草稿状态可编辑）"""
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id,
        MedicalOrder.patient_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    if order.status != OrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的医嘱可以编辑")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    db.commit()
    db.refresh(order)

    return MedicalOrderResponse.model_validate(order)


@router.post("/{order_id}/activate", response_model=MedicalOrderResponse)
def activate_medical_order(
    order_id: int,
    request: ActivateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """激活医嘱（生成任务实例）"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="需要确认激活")

    service = MedicalOrderService(db)

    # 验证权限
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    if order.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此医嘱")

    activated = service.activate_order(order_id)

    return MedicalOrderResponse.model_validate(activated)


# ============= 任务查询 =============

@router.get("/tasks/{task_date}", response_model=TaskListResponse)
def get_daily_tasks(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定日期的任务列表

    返回按状态分组的任务
    """
    tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == current_user.id,
        TaskInstance.scheduled_date == task_date
    ).all()

    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]

    # 构建响应
    def build_response(task):
        data = TaskInstanceResponse.model_validate(task).model_dump()
        if task.order:
            data["order_title"] = task.order.title
            data["order_type"] = task.order.order_type.value
        return data

    # 计算依从性
    total = len(tasks)
    completed_count = len(completed)
    overdue_count = len(overdue)
    pending_count = len(pending)
    rate = completed_count / total if total > 0 else 0

    summary = ComplianceResponse(
        date=task_date.isoformat(),
        total=total,
        completed=completed_count,
        overdue=overdue_count,
        pending=pending_count,
        rate=round(rate, 2)
    )

    return TaskListResponse(
        date=task_date.isoformat(),
        pending=[build_response(t) for t in pending],
        completed=[build_response(t) for t in completed],
        overdue=[build_response(t) for t in overdue],
        summary=summary
    )


@router.get("/tasks/{task_date}/pending", response_model=List[TaskInstanceResponse])
def get_pending_tasks(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取待完成任务"""
    tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == current_user.id,
        TaskInstance.scheduled_date == task_date,
        TaskInstance.status == TaskStatus.PENDING
    ).order_by(TaskInstance.scheduled_time).all()

    return [TaskInstanceResponse.model_validate(t) for t in tasks]


# ============= 打卡操作 =============

@router.post("/tasks/{task_id}/complete", response_model=CompletionRecordResponse)
def complete_task(
    task_id: int,
    request: CompletionRecordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    完成任务打卡

    支持多种打卡类型：
    - check: 简单打卡确认
    - photo: 照片证明
    - value: 数值录入（如血糖）
    - medication: 用药记录
    """
    task = db.query(TaskInstance).filter(
        TaskInstance.id == task_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务已完成")

    # 覆盖 request 中的 task_instance_id
    request.task_instance_id = task_id

    # 创建打卡记录
    record = CompletionRecord(
        task_instance_id=task_id,
        completed_by=current_user.id,
        completion_type=request.completion_type,
        value=request.value,
        photo_url=request.photo_url,
        notes=request.notes
    )

    # 更新任务状态
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.completion_notes = request.notes

    db.add(record)
    db.commit()
    db.refresh(record)

    return CompletionRecordResponse.model_validate(record)


# ============= 依从性查询 =============

@router.get("/compliance/daily", response_model=ComplianceResponse)
def get_daily_compliance(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定日期的依从性"""
    service = ComplianceService(db)
    compliance = service.calculate_daily_compliance(current_user.id, task_date)
    return ComplianceResponse(**compliance)


@router.get("/compliance/weekly", response_model=WeeklyComplianceResponse)
def get_weekly_compliance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取近7天依从性趋势"""
    service = ComplianceService(db)
    weekly = service.calculate_weekly_compliance(current_user.id)
    return WeeklyComplianceResponse(**weekly)
```

**Step 4: Register route in main app**

Modify `backend/app/routes/__init__.py`:

```python
from .medical_orders import router as medical_orders_router
```

Modify `backend/app/main.py`:

```python
from app.routes.medical_orders import router as medical_orders_router
app.include_router(medical_orders_router)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_medical_orders_routes.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/routes/medical_orders.py backend/app/main.py tests/test_medical_orders_routes.py
git commit -m "feat(medical-order): add medical orders API routes"
```

---

## Phase P0: iOS患者端

### Task 12-20: iOS 页面和 ViewModel

由于 iOS 代码较复杂，以下为核心任务概要：

**Task 12: 创建 MedicalOrder API Models**
- 文件: `ios/xinlingyisheng/xinlingyisheng/Models/MedicalOrderModels.swift`
- 定义与后端对应的 Swift 结构体

**Task 13: 创建 MedicalOrderViewModel**
- 文件: `ios/xinlingyisheng/xinlingyisheng/ViewModels/MedicalOrderViewModel.swift`
- 实现医嘱列表查询、任务获取、打卡操作

**Task 14: 创建医嘱列表页**
- 文件: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalOrderListView.swift`
- 显示每日任务，按状态分组

**Task 15: 创建打卡弹窗**
- 文件: `ios/xinlingyisheng/xinlingyisheng/Views/TaskCheckInView.swift`
- 支持语音/照片/数值输入

**Task 16: 添加任务提醒通知**
- 文件: `ios/xinlingyisheng/xinlingyisheng/Services/NotificationService.swift`
- 定时推送任务提醒

**Task 17: 创建依从性图表**
- 文件: `ios/xinlingyisheng/xinlingyisheng/Views/ComplianceChartView.swift`
- 显示周依从性柱状图

**Task 18: 创建家属关怀页**
- 文件: `ios/xinlingyisheng/xinlingyisheng/Views/FamilyCareView.swift`
- 显示关联患者的任务状态

**Task 19: 添加 Tab 导航入口**
- 修改: `ios/xinlingyisheng/xinlingyisheng/Views/MainTabView.swift`
- 添加"医嘱"Tab

**Task 20: 编译验证**

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme 灵犀医生 \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

---

## Phase P1: AI数值抽取

### Task 21: 创建数值抽取 Agent

**Files:**
- Create: `backend/app/services/agents/value_extraction.py`
- Create: `tests/test_value_extraction.py`

**Step 1: Write test**

```python
# tests/test_value_extraction.py
import pytest
from backend.app.services.agents.value_extraction import ValueExtractionAgent

@pytest.mark.asyncio
async def test_extract_blood_glucose():
    """测试血糖值抽取"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_glucose("血糖8点5")
    assert result["value"] == 8.5
    assert result["unit"] == "mmol/L"

    result = await agent.extract_blood_glucose("餐后血糖七点八")
    assert result["value"] == 7.8

@pytest.mark.asyncio
async def test_extract_blood_pressure():
    """测试血压值抽取"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_pressure("血压135到85")
    assert result["systolic"] == 135
    assert result["diastolic"] == 85

    result = await agent.extract_blood_pressure("高压120低压80")
    assert result["systolic"] == 120
    assert result["diastolic"] == 80
```

**Step 2: Write implementation**

```python
# backend/app/services/agents/value_extraction.py
"""
数值抽取 Agent

从语音识别文本中抽取医嘱相关数值：
- 血糖值
- 血压值（收缩压/舒张压）
- 体温
- 体重等
"""
import re
import json
from typing import Dict, Optional, Any
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..ai.llm_service import get_llm


class BloodGlucoseResult(BaseModel):
    """血糖抽取结果"""
    value: float = Field(description="血糖数值")
    unit: str = Field(description="单位，默认mmol/L")
    is_low: bool = Field(description="是否低血糖")
    is_high: bool = Field(description="是否高血糖")


class BloodPressureResult(BaseModel):
    """血压抽取结果"""
    systolic: int = Field(description="收缩压（高压）")
    diastolic: int = Field(description="舒张压（低压）")
    level: str = Field(description="血压等级：normal/elevated/high_1/high_2")


class ValueExtractionAgent:
    """数值抽取 Agent"""

    def __init__(self):
        self.llm = get_llm()

        # 中文数字映射
        self.cn_numbers = {
            "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
            "十": 10, "两": 2
        }

    async def extract_blood_glucose(self, text: str) -> Dict[str, Any]:
        """
        从语音文本中抽取血糖值

        支持多种表达：
        - "血糖8点5"
        - "血糖八"
        - "餐后血糖7.8"
        - "低血糖3.2"
        """
        # 先尝试正则抽取
        result = self._extract_glucose_regex(text)
        if result:
            return await self._normalize_glucose(result)

        # LLM 抽取
        parser = PydanticOutputParser(pydantic_object=BloodGlucoseResult)

        prompt = ChatPromptTemplate.from_template("""
从以下语音识别文本中抽取血糖值：

"{text}"

{format_instructions}

注意：
1. 单位默认为 mmol/L
2. 血糖 < 3.9 为低血糖
3. 空腹血糖 > 7.0 或餐后2h > 11.1 为高血糖
""")

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke({
                "text": text,
                "format_instructions": parser.get_format_instructions()
            })
            return result.model_dump()
        except Exception as e:
            # 降级到正则匹配
            return self._extract_glucose_fallback(text)

    def _extract_glucose_regex(self, text: str) -> Optional[Dict]:
        """正则抽取血糖"""
        # 匹配 "8.5" 或 "8点5" 或 "八"
        patterns = [
            r'血糖?\s*(\d+(?:\.\d+)?)',  # "血糖8.5"
            r'(\d+)\s*点\s*(\d+)',  # "8点5"
            r'血糖?\s*([一二三四五六七八九十零百]+)',  # "血糖八"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if pattern == patterns[1]:  # "X点Y"
                    value = float(f"{match.group(1)}.{match.group(2)}")
                elif pattern == patterns[2]:  # 中文数字
                    value = self._cn_number_to_arabic(match.group(1))
                else:
                    value = float(match.group(1))
                return {"value": value, "unit": "mmol/L"}
        return None

    def _cn_number_to_arabic(self, cn: str) -> int:
        """中文数字转阿拉伯数字"""
        if cn in self.cn_numbers:
            return self.cn_numbers[cn]
        # 处理"十"开头的数字
        if cn.startswith("十"):
            if len(cn) == 1:
                return 10
            return 10 + self.cn_numbers.get(cn[1], 0)
        return 0

    async def _normalize_glucose(self, result: Dict) -> Dict:
        """标准化血糖结果"""
        value = result.get("value", 0)
        return {
            "value": value,
            "unit": "mmol/L",
            "is_low": value < 3.9,
            "is_high": value > 11.1
        }

    def _extract_glucose_fallback(self, text: str) -> Dict:
        """降级抽取"""
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            value = float(numbers[0])
            return {
                "value": value,
                "unit": "mmol/L",
                "is_low": value < 3.9,
                "is_high": value > 11.1
            }
        return {"value": 0, "unit": "mmol/L", "is_low": False, "is_high": False}

    async def extract_blood_pressure(self, text: str) -> Dict[str, Any]:
        """
        从语音文本中抽取血压值

        支持多种表达：
        - "血压135到85"
        - "血压135 85"
        - "高压150低压95"
        """
        # 先尝试正则抽取
        result = self._extract_pressure_regex(text)
        if result:
            return await self._normalize_pressure(result)

        # LLM 抽取
        parser = PydanticOutputParser(pydantic_object=BloodPressureResult)

        prompt = ChatPromptTemplate.from_template("""
从以下语音识别文本中抽取血压值：

"{text}"

{format_instructions}

血压等级标准：
- 正常：< 120/80
- 高值：120-129/< 80
- 高血压1期：130-139/80-89
- 高血压2期：≥ 140/90
""")

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke({
                "text": text,
                "format_instructions": parser.get_format_instructions()
            })
            return result.model_dump()
        except Exception as e:
            return self._extract_pressure_fallback(text)

    def _extract_pressure_regex(self, text: str) -> Optional[Dict]:
        """正则抽取血压"""
        # 匹配 "135/85" 或 "135到85" 或 "135 85"
        patterns = [
            r'(\d{2,3})\s*/\s*(\d{2,3})',  # "135/85"
            r'(\d{2,3})\s*[到至]\s*(\d{2,3})',  # "135到85"
            r'高压\s*(\d{2,3})\s*(?:低压|低压是)\s*(\d{2,3})',  # "高压135低压85"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return {
                    "systolic": int(match.group(1)),
                    "diastolic": int(match.group(2))
                }
        return None

    async def _normalize_pressure(self, result: Dict) -> Dict:
        """标准化血压结果"""
        systolic = result.get("systolic", 0)
        diastolic = result.get("diastolic", 0)

        # 判断等级
        if systolic < 120 and diastolic < 80:
            level = "normal"
        elif systolic < 130 and diastolic < 80:
            level = "elevated"
        elif systolic < 140 or diastolic < 90:
            level = "high_1"
        else:
            level = "high_2"

        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "level": level
        }

    def _extract_pressure_fallback(self, text: str) -> Dict:
        """降级抽取"""
        numbers = re.findall(r'\d{2,3}', text)
        if len(numbers) >= 2:
            return {
                "systolic": int(numbers[0]),
                "diastolic": int(numbers[1]),
                "level": "unknown"
            }
        return {"systolic": 0, "diastolic": 0, "level": "unknown"}
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_value_extraction.py -v
git add backend/app/services/agents/value_extraction.py tests/test_value_extraction.py
git commit -m "feat(medical-order): add ValueExtractionAgent for voice input"
```

---

## Phase P1: 依从性分析

### Task 22: 添加依从性分析 API**

**Files:**
- Modify: `backend/app/routes/medical_orders.py`

**Implementation** (add to existing routes):

```python
@router.get("/compliance/order/{order_id}", response_model=Dict)
def get_order_compliance(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取医嘱依从性详情"""
    # 验证权限
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id,
        MedicalOrder.patient_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    service = ComplianceService(db)
    return service.calculate_order_compliance(order_id)


@router.get("/compliance/abnormal", response_model=List[Dict])
def get_abnormal_records(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取异常记录"""
    service = ComplianceService(db)
    return service.get_abnormal_records(current_user.id, days)
```

---

## Phase P1: 家属关怀

### Task 23: 家属关系管理 API

**Files:**
- Modify: `backend/app/routes/medical_orders.py`

**Implementation**:

```python
@router.post("/family-bonds", response_model=FamilyBondResponse, status_code=201)
def create_family_bond(
    request: FamilyBondCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建家属关系"""
    # 查找家属用户
    family_member = db.query(User).filter(
        User.phone == request.family_member_phone
    ).first()

    if not family_member:
        raise HTTPException(status_code=404, detail="家属用户不存在")

    # 检查是否已存在关系
    existing = db.query(FamilyBond).filter(
        FamilyBond.patient_id == request.patient_id,
        FamilyBond.family_member_id == family_member.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="关系已存在")

    # 验证患者权限（只能为自己或未成年子女创建）
    if request.patient_id != current_user.id:
        # TODO: 添加家属关系验证逻辑
        pass

    bond = FamilyBond(
        patient_id=request.patient_id,
        family_member_id=family_member.id,
        relationship=request.relationship,
        notification_level=request.notification_level
    )

    db.add(bond)
    db.commit()
    db.refresh(bond)

    return FamilyBondResponse(
        id=bond.id,
        patient_id=bond.patient_id,
        family_member_id=bond.family_member_id,
        relationship=bond.relationship,
        notification_level=bond.notification_level.value,
        family_member_name=family_member.nickname,
        family_member_phone=family_member.phone
    )


@router.get("/family-bonds", response_model=List[FamilyBondResponse])
def get_family_bonds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我的家属关系（我作为患者或作为家属）"""
    from ..models.medical_order import FamilyBond

    # 查找我是家属的关系
    as_family = db.query(FamilyBond).filter(
        FamilyBond.family_member_id == current_user.id
    ).all()

    results = []
    for bond in as_family:
        patient = db.query(User).filter(User.id == bond.patient_id).first()
        results.append(FamilyBondResponse(
            id=bond.id,
            patient_id=bond.patient_id,
            family_member_id=bond.family_member_id,
            relationship=bond.relationship,
            notification_level=bond.notification_level.value,
            family_member_name=patient.nickname if patient else "未知",
            family_member_phone=patient.phone if patient else None
        ))

    return results


@router.get("/family-bonds/{patient_id}/tasks", response_model=TaskListResponse)
def get_family_member_tasks(
    patient_id: int,
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取家属的任务列表"""
    from ..models.medical_order import FamilyBond

    # 验证有权查看
    bond = db.query(FamilyBond).filter(
        FamilyBond.patient_id == patient_id,
        FamilyBond.family_member_id == current_user.id
    ).first()

    if not bond:
        raise HTTPException(status_code=403, detail="无权查看此患者信息")

    # 获取任务
    tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date == task_date
    ).all()

    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]

    def build_response(task):
        data = TaskInstanceResponse.model_validate(task).model_dump()
        if task.order:
            data["order_title"] = task.order.title
            data["order_type"] = task.order.order_type.value
        return data

    total = len(tasks)
    completed_count = len(completed)

    summary = ComplianceResponse(
        date=task_date.isoformat(),
        total=total,
        completed=completed_count,
        overdue=len(overdue),
        pending=len(pending),
        rate=round(completed_count / total, 2) if total > 0 else 0
    )

    return TaskListResponse(
        date=task_date.isoformat(),
        pending=[build_response(t) for t in pending],
        completed=[build_response(t) for t in completed],
        overdue=[build_response(t) for t in overdue],
        summary=summary
    )
```

---

## Phase P1: 异常预警

### Task 24: 异常检测和预警服务

**Files:**
- Create: `backend/app/services/alert_service.py`
- Modify: `backend/app/routes/medical_orders.py`

**Implementation**:

```python
# backend/app/services/alert_service.py
"""
异常预警服务

负责：
- 检测监测值异常
- 多级预警（黄/橙/红）
- 推送通知给患者、家属、医生
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.medical_order import CompletionRecord, TaskInstance, MedicalOrder, OrderType
from ..models.user import User
from ..models.family_bond import FamilyBond


class AlertLevel:
    YELLOW = "yellow"  # 轻微异常
    ORANGE = "orange"  # 中度异常
    RED = "red"       # 重度异常


class AlertService:
    """异常预警服务"""

    # 预警阈值配置
    THRESHOLDS = {
        "blood_glucose": {
            "low_red": 2.8,      # 严重低血糖
            "low_orange": 3.9,   # 低血糖
            "high_orange": 11.1, # 高血糖
            "high_red": 16.7,    # 严重高血糖
        },
        "blood_pressure": {
            "high_red_sys": 180,     # 重度高血压
            "high_red_dia": 120,
            "high_orange_sys": 140,  # 高血压
            "high_orange_dia": 90,
        }
    }

    def __init__(self, db: Session):
        self.db = db

    async def check_completion_value(
        self,
        record: CompletionRecord
    ) -> Optional[Dict]:
        """
        检查打卡记录中的数值是否异常

        返回预警信息或 None
        """
        if not record.value:
            return None

        task = self.db.query(TaskInstance).filter(
            TaskInstance.id == record.task_instance_id
        ).first()

        if not task or not task.order:
            return None

        order = task.order

        # 根据医嘱类型检测
        if order.order_type == OrderType.MONITORING:
            # 血糖监测
            if "血糖" in order.title or "glucose" in order.title.lower():
                return self._check_blood_glucose(record.value.get("value", 0))

            # 血压监测
            if "血压" in order.title or "pressure" in order.title.lower():
                systolic = record.value.get("systolic", 0)
                diastolic = record.value.get("diastolic", 0)
                return self._check_blood_pressure(systolic, diastolic)

        return None

    def _check_blood_glucose(self, value: float) -> Optional[Dict]:
        """检测血糖异常"""
        thresholds = self.THRESHOLDS["blood_glucose"]

        if value < thresholds["low_red"]:
            return {
                "level": AlertLevel.RED,
                "type": "low_blood_glucose",
                "message": f"严重低血糖！当前值 {value} mmol/L，请立即进食或就医",
                "value": value,
                "threshold": thresholds["low_red"]
            }

        if value < thresholds["low_orange"]:
            return {
                "level": AlertLevel.ORANGE,
                "type": "low_blood_glucose",
                "message": f"低血糖预警：当前值 {value} mmol/L，建议补充糖分",
                "value": value,
                "threshold": thresholds["low_orange"]
            }

        if value > thresholds["high_red"]:
            return {
                "level": AlertLevel.RED,
                "type": "high_blood_glucose",
                "message": f"严重高血糖！当前值 {value} mmol/L，请立即就医",
                "value": value,
                "threshold": thresholds["high_red"]
            }

        if value > thresholds["high_orange"]:
            return {
                "level": AlertLevel.ORANGE,
                "type": "high_blood_glucose",
                "message": f"高血糖预警：当前值 {value} mmol/L，请注意饮食",
                "value": value,
                "threshold": thresholds["high_orange"]
            }

        return None

    def _check_blood_pressure(
        self,
        systolic: int,
        diastolic: int
    ) -> Optional[Dict]:
        """检测血压异常"""
        thresholds = self.THRESHOLDS["blood_pressure"]

        if systolic >= thresholds["high_red_sys"] or diastolic >= thresholds["high_red_dia"]:
            return {
                "level": AlertLevel.RED,
                "type": "high_blood_pressure",
                "message": f"严重高血压！{systolic}/{diastolic} mmHg，请立即就医",
                "value": {"systolic": systolic, "diastolic": diastolic}
            }

        if systolic >= thresholds["high_orange_sys"] or diastolic >= thresholds["high_orange_dia"]:
            return {
                "level": AlertLevel.ORANGE,
                "type": "high_blood_pressure",
                "message": f"高血压预警：{systolic}/{diastolic} mmHg，建议测量并咨询医生",
                "value": {"systolic": systolic, "diastolic": diastolic}
            }

        return None

    async def send_alert(
        self,
        patient_id: int,
        alert: Dict
    ) -> List[str]:
        """
        发送预警通知

        返回发送成功的通知列表
        """
        # TODO: 实现通知发送逻辑
        # 1. 推送给患者
        # 2. 根据家属设置推送
        # 3. 红色预警推送给医生
        return []
```

---

## Phase P2: Web医生端

### Task 25-30: React 前端页面

**任务列表**（简略）：

1. 创建医嘱管理页面 (`frontend/src/pages/doctor/MedicalOrders.tsx`)
2. 创建患者依从性详情页 (`frontend/src/pages/doctor/PatientCompliance.tsx`)
3. 创建依从性图表组件 (`frontend/src/components/ComplianceChart.tsx`)
4. 添加路由配置 (`frontend/src/router/index.tsx`)
5. 集成 API 调用 (`frontend/src/api/medicalOrders.ts`)

---

## 执行顺序总结

1. **P0 数据模型** (Task 1-6): 核心数据库结构
2. **P0 后端服务** (Task 7-9): CRUD 和调度逻辑
3. **P0 API 路由** (Task 10-11): REST 接口
4. **P0 iOS 基础** (Task 12-20): 患者端核心功能
5. **P1 AI 抽取** (Task 21): 语音数值抽取
6. **P1 依从性** (Task 22): 详细分析
7. **P1 家属** (Task 23): 关系和监控
8. **P1 预警** (Task 24): 异常检测
9. **P2 医生端** (Task 25-30): Web 管理界面

---

**计划完成。** 该计划遵循 TDD 原则，每个任务包含测试、实现、验证、提交四个步骤。
