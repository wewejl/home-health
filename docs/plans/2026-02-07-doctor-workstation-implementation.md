# 医生工作台实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **最后更新:** 2026-02-07 - 已基于现有代码审查并修正

**目标:** 为医生创建独立的工作台，包含查看患者对话、下达医嘱、查看任务完成状态功能

**架构:** 前端使用独立的 `/doctor/*` 路由，后端创建 `/api/doctor/*` API 前缀。复用现有数据模型（doctors, sessions, medical_orders），扩展 doctors 表添加登录字段。

---

## ⚠️ 重要设计说明（基于代码审查）

### 现有数据模型分析

| 表名 | 状态 | 说明 |
|------|------|------|
| `doctors` | ✅ 已存在 | **缺少** `username`, `password_hash` 登录字段，需要扩展 |
| `sessions` | ✅ 已存在 | 已有 `doctor_id` 外键指向 `doctors` 表，可直接使用 |
| `messages` | ✅ 已存在 | 已有 `sender` 枚举 (user/ai)，可直接使用 |
| `medical_orders` | ⚠️ 注意 | `doctor_id` 外键指向 `admin_users` 表，**不是** `doctors` 表 |
| `task_instances` | ✅ 已存在 | 可直接复用 |
| `completion_records` | ✅ 已存在 | 可直接复用 |

### 设计决策

**问题:** `MedicalOrder.doctor_id` 指向 `admin_users`，但医生工作台是为 `doctors` 表设计的。

**解决方案:** 采用**数据映射**方式，不修改现有外键：
- 医生工作台创建医嘱时，`doctor_id` 字段**暂时为 NULL**（因为医生在 `doctors` 表，不在 `admin_users`）
- 后续如需关联，可通过 `ai_generated` 标记区分 AI 生成的医嘱
- 或者：当医生创建医嘱时，将 `doctor_id` 设置为对应的管理员 ID（需要建立 `doctors.id` → `admin_users.id` 的映射）

### 现有文件状态

| 文件 | 状态 | 操作 |
|------|------|------|
| `backend/app/models/doctor.py` | ✅ 存在 | 需要扩展（添加登录字段） |
| `backend/app/schemas/doctor.py` | ✅ 存在 | 需要扩展（添加认证 schemas） |
| `backend/app/routes/admin_auth.py` | ✅ 存在 | 可参考其模式 |
| `backend/app/schemas/medical_order.py` | ✅ 存在 | 可复用 |

**技术栈:**
- 后端: FastAPI + SQLAlchemy + PostgreSQL
- 前端: React + TypeScript + Ant Design + React Router
- 认证: JWT Bearer Token

---

## Phase 0: 数据模型扩展

### Task 1: 扩展 Doctor 模型（添加登录字段）

**Files:**
- Modify: `backend/app/models/doctor.py`

**Step 1: 添加登录相关字段到 Doctor 模型**

在 `Doctor` 类中添加以下字段（在 `is_active` 字段之前）：

```python
# 登录认证字段
username = Column(String(50), unique=True, nullable=True, index=True)  # 允许为空以兼容现有数据
password_hash = Column(String(255), nullable=True)
last_login_at = Column(DateTime(timezone=True), nullable=True)
```

**Step 2: 更新数据库**

手动执行 SQL 或创建迁移脚本：

```sql
-- 添加登录字段（允许 NULL 以兼容现有数据）
ALTER TABLE doctors ADD COLUMN username VARCHAR(50) UNIQUE;
ALTER TABLE doctors ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE doctors ADD COLUMN last_login_at TIMESTAMP;

-- 创建索引
CREATE INDEX idx_doctors_username ON doctors(username);
```

**Step 3: 验证模型更新**

启动后端服务，确保没有报错：

```bash
cd backend
python -c "from app.models.doctor import Doctor; print('Doctor model loaded successfully')"
```

**Step 4: Commit**

```bash
git add backend/app/models/doctor.py
git commit -m "feat(doctor): add login fields to Doctor model"
```

---

### Task 2: 创建医生认证 Service

**Files:**
- Create: `backend/app/services/doctor_auth_service.py`

**Step 1: 创建认证服务文件**

```python
"""
医生认证服务

处理医生登录、JWT token 生成和验证
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..models.doctor import Doctor

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置
SECRET_KEY = "your-secret-key-here"  # 生产环境应从环境变量读取
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


class DoctorAuthService:
    """医生认证服务"""

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def authenticate_doctor(db: Session, username: str, password: str) -> Optional[Doctor]:
        """验证医生登录"""
        doctor = db.query(Doctor).filter(
            Doctor.username == username,
            Doctor.is_active == True
        ).first()

        if not doctor:
            return None

        if not doctor.password_hash:
            return None

        if not DoctorAuthService.verify_password(password, doctor.password_hash):
            return None

        # 更新最后登录时间
        doctor.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(doctor)

        return doctor

    @staticmethod
    def create_doctor_token(doctor_id: int) -> str:
        """生成 JWT token"""
        payload = {
            "sub": str(doctor_id),
            "type": "doctor",
            "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_doctor_token(token: str) -> Optional[int]:
        """验证 JWT token，返回医生 ID"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "doctor":
                return None
            return int(payload["sub"])
        except jwt.PyJWTError:
            return None

    @staticmethod
    def create_doctor_user(
        db: Session,
        username: str,
        password: str,
        name: str,
        department_id: int,
        **kwargs
    ) -> Doctor:
        """创建医生用户（带登录信息）"""
        # 检查用户名是否已存在
        existing = db.query(Doctor).filter(Doctor.username == username).first()
        if existing:
            raise ValueError(f"用户名 '{username}' 已存在")

        doctor = Doctor(
            username=username,
            password_hash=DoctorAuthService.hash_password(password),
            name=name,
            department_id=department_id,
            **kwargs
        )

        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        return doctor
```

**Step 2: Commit**

```bash
git add backend/app/services/doctor_auth_service.py
git commit -m "feat(service): create DoctorAuthService for authentication"
```

---

### Task 3: 扩展医生认证 Schemas

**Files:**
- **Modify**: `backend/app/schemas/doctor.py` ⚠️ 文件已存在，需要**扩展**而非创建

**说明:** 现有 `schemas/doctor.py` 包含 `DoctorResponse`, `DoctorCreate`, `DoctorUpdate` 等，但**缺少**登录认证相关的 schemas。

**Step 1: 在现有文件中添加认证相关 schemas**

在 `backend/app/schemas/doctor.py` 文件**末尾添加**以下内容：

```python
# ============= 登录认证相关（新增）=============

from pydantic import BaseModel
from typing import Optional, List


class DoctorLoginRequest(BaseModel):
    """医生登录请求"""
    username: str
    password: str


class DoctorLoginResponse(BaseModel):
    """医生登录响应"""
    access_token: str
    token_type: str = "bearer"
    doctor: "DoctorResponse"  # 引用现有的 DoctorResponse


# ============= 患者相关（新增）=============

class PatientListItem(BaseModel):
    """患者列表项"""
    id: int
    nickname: Optional[str] = None
    phone: str
    gender: Optional[str] = None
    age: Optional[int] = None
    last_consultation_at: Optional[datetime] = None
    active_orders_count: int = 0
    completion_rate: float = 0.0

    class Config:
        from_attributes = True


class PatientDetailResponse(PatientListItem):
    """患者详情"""
    avatar_url: Optional[str] = None
    is_profile_completed: bool = False
    created_at: Optional[datetime] = None


# ============= 对话记录相关（新增）=============

class ConsultationMessage(BaseModel):
    """对话消息"""
    id: int
    sender: str  # "user" or "ai"
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConsultationSession(BaseModel):
    """对话会话"""
    id: str
    doctor_id: Optional[int] = None
    agent_type: str
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ConsultationDetailResponse(BaseModel):
    """对话详情（含消息列表）"""
    session: ConsultationSession
    messages: List[ConsultationMessage]
```

**注意:**
- `DoctorResponse` 已存在，无需重复定义
- 需要在文件顶部添加 `from datetime import datetime` 和 `from typing import List`（如果不存在）

**Step 2: 更新现有的 DoctorResponse**

现有的 `DoctorResponse` 类需要添加 `username` 字段。找到 `DoctorResponse` 类定义，添加：

```python
username: Optional[str] = None  # 登录用户名
```

**Step 3: Commit**

```bash
git add backend/app/schemas/doctor.py
git commit -m "feat(schemas): add authentication and patient schemas to doctor.py"
```

---

## Phase 1: 后端 API 开发

### Task 4: 创建医生认证路由

**Files:**
- Create: `backend/app/routes/doctor_auth.py`
- Modify: `backend/app/routes/__init__.py`

**Step 1: 创建医生认证路由**

```python
"""
医生认证 API 路由

处理医生登录、登出、获取当前医生信息
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.doctor import Doctor
from ..services.doctor_auth_service import DoctorAuthService
from ..schemas.doctor import DoctorLoginRequest, DoctorLoginResponse, DoctorResponse

router = APIRouter(prefix="/api/doctor/auth", tags=["doctor-auth"])
security = HTTPBearer(auto_error=False)

# 测试模式开关
TEST_MODE = True


def get_current_doctor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Doctor:
    """获取当前登录的医生"""
    # 测试模式：返回测试医生
    if TEST_MODE:
        test_doctor = db.query(Doctor).filter(Doctor.username == "test_doctor").first()
        if not test_doctor:
            # 创建测试医生
            from ..models.department import Department
            dept = db.query(Department).first()
            if not dept:
                # 如果没有科室，创建一个默认科室
                dept = Department(id=1, name="皮肤科", icon="🏥", sort_order=1)
                db.add(dept)
                db.commit()

            test_doctor = Doctor(
                username="test_doctor",
                password_hash=DoctorAuthService.hash_password("test123"),
                name="测试医生",
                title="主治医师",
                department_id=dept.id,
                hospital="灵犀健康",
                is_active=True
            )
            db.add(test_doctor)
            db.commit()
            db.refresh(test_doctor)
        return test_doctor

    # 生产模式：验证 token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    doctor_id = DoctorAuthService.verify_doctor_token(token)

    if doctor_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.is_active == True
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="医生不存在或已禁用"
        )

    return doctor


@router.post("/login", response_model=DoctorLoginResponse)
def doctor_login(
    request: DoctorLoginRequest,
    db: Session = Depends(get_db)
):
    """医生登录"""
    doctor = DoctorAuthService.authenticate_doctor(db, request.username, request.password)

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    token = DoctorAuthService.create_doctor_token(doctor.id)

    return DoctorLoginResponse(
        access_token=token,
        doctor=DoctorResponse.model_validate(doctor)
    )


@router.get("/me", response_model=DoctorResponse)
def get_current_doctor_info(doctor: Doctor = Depends(get_current_doctor)):
    """获取当前医生信息"""
    return DoctorResponse.model_validate(doctor)


@router.post("/logout")
def doctor_logout():
    """医生登出（客户端删除 token 即可）"""
    return {"message": "已登出"}
```

**Step 2: 在 __init__.py 中注册路由**

在 `backend/app/routes/__init__.py` 中添加：

```python
from .doctor_auth import router as doctor_auth_router
# ... 其他导入

__all__ = [
    # ... 现有路由
    "doctor_auth_router",  # 添加这一行
]
```

**Step 3: 在 main.py 中注册路由**

确保在 `backend/app/main.py` 中添加：

```python
from app.routes import doctor_auth_router

app.include_router(doctor_auth_router)
```

**Step 4: 测试登录 API**

```bash
# 启动服务后测试
curl -X POST "http://localhost:8000/api/doctor/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_doctor", "password": "test123"}'
```

**Step 5: Commit**

```bash
git add backend/app/routes/doctor_auth.py backend/app/routes/__init__.py
git commit -m "feat(api): add doctor authentication routes"
```

---

### Task 5: 创建患者管理路由

**Files:**
- Create: `backend/app/routes/doctor_patients.py`

**Step 1: 创建患者管理路由**

```python
"""
医生患者管理 API 路由

医生查看自己的患者列表、患者详情
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import datetime, timedelta

from ..database import get_db
from ..models.doctor import Doctor
from ..models.user import User
from ..models.session import Session as ConsultationSession
from ..models.message import Message
from ..models.medical_order import MedicalOrder, TaskInstance, TaskStatus, OrderStatus
from ..routes.doctor_auth import get_current_doctor
from ..schemas.doctor import PatientListItem, PatientDetailResponse

router = APIRouter(prefix="/api/doctor/patients", tags=["doctor-patients"])


@router.get("", response_model=list[PatientListItem])
def get_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取患者列表

    返回与该医生有过咨询的患者
    """
    # 获取与该医生有过咨询的患者 ID
    consultation_patient_ids = db.query(ConsultationSession.user_id).filter(
        ConsultationSession.doctor_id == doctor.id
    ).distinct().all()

    patient_ids = [p[0] for p in consultation_patient_ids]

    if not patient_ids:
        return []

    # 构建查询
    query = db.query(User).filter(User.id.in_(patient_ids))

    # 搜索过滤
    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )

    patients = query.order_by(desc(User.created_at)).all()

    # 为每个患者计算统计数据
    result = []
    for patient in patients:
        # 最后咨询时间
        last_session = db.query(ConsultationSession).filter(
            ConsultationSession.user_id == patient.id,
            ConsultationSession.doctor_id == doctor.id
        ).order_by(desc(ConsultationSession.updated_at)).first()

        # 进行中的医嘱数
        active_orders = db.query(MedicalOrder).filter(
            MedicalOrder.patient_id == patient.id,
            MedicalOrder.status == OrderStatus.ACTIVE
        ).count()

        # 最近7天完成率
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_tasks = db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient.id,
            TaskInstance.scheduled_date >= week_ago.date()
        ).all()

        completed_count = sum(1 for t in week_tasks if t.status == TaskStatus.COMPLETED)
        completion_rate = completed_count / len(week_tasks) if week_tasks else 0.0

        result.append(PatientListItem(
            id=patient.id,
            nickname=patient.nickname,
            phone=patient.phone,
            gender=patient.gender,
            age=patient.age,
            last_consultation_at=last_session.updated_at if last_session else None,
            active_orders_count=active_orders,
            completion_rate=round(completion_rate, 2)
        ))

    return result


@router.get("/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(
    patient_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者详情"""
    patient = db.query(User).filter(User.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 验证该患者是否与医生有过咨询
    has_consultation = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id,
        ConsultationSession.doctor_id == doctor.id
    ).first()

    if not has_consultation:
        raise HTTPException(status_code=403, detail="无权查看此患者信息")

    # 最后咨询时间
    last_session = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id,
        ConsultationSession.doctor_id == doctor.id
    ).order_by(desc(ConsultationSession.updated_at)).first()

    # 进行中的医嘱数
    active_orders = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient_id,
        MedicalOrder.status == OrderStatus.ACTIVE
    ).count()

    # 最近7天完成率
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    completed_count = sum(1 for t in week_tasks if t.status == TaskStatus.COMPLETED)
    completion_rate = completed_count / len(week_tasks) if week_tasks else 0.0

    return PatientDetailResponse(
        id=patient.id,
        nickname=patient.nickname,
        phone=patient.phone,
        gender=patient.gender,
        age=patient.age,
        avatar_url=patient.avatar_url,
        is_profile_completed=patient.is_profile_completed,
        last_consultation_at=last_session.updated_at if last_session else None,
        active_orders_count=active_orders,
        completion_rate=round(completion_rate, 2),
        created_at=patient.created_at
    )
```

**Step 2: 在 __init__.py 中注册路由**

```python
from .doctor_patients import router as doctor_patients_router

__all__ = [
    # ...
    "doctor_patients_router",
]
```

**Step 3: 在 main.py 中注册路由**

```python
from app.routes import doctor_patients_router

app.include_router(doctor_patients_router)
```

**Step 4: 测试患者列表 API**

```bash
# 测试获取患者列表
curl -X GET "http://localhost:8000/api/doctor/patients"
```

**Step 5: Commit**

```bash
git add backend/app/routes/doctor_patients.py
git commit -m "feat(api): add doctor patients management routes"
```

---

### Task 6: 创建对话记录路由

**Files:**
- Create: `backend/app/routes/doctor_consultations.py`

**Step 1: 创建对话记录路由**

```python
"""
医生对话记录 API 路由

医生查看患者的咨询对话记录
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.doctor import Doctor
from ..models.user import User
from ..models.session import Session as ConsultationSession
from ..models.message import Message, SenderType
from ..routes.doctor_auth import get_current_doctor
from ..schemas.doctor import ConsultationSession, ConsultationMessage, ConsultationDetailResponse

router = APIRouter(prefix="/api/doctor/patients", tags=["doctor-consultations"])


@router.get("/{patient_id}/consultations", response_model=list[ConsultationSession])
def get_patient_consultations(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取患者的对话列表

    返回该患者与当前医生的对话会话
    """
    # 验证患者存在
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取对话会话
    sessions = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id,
        ConsultationSession.doctor_id == doctor.id
    ).order_by(ConsultationSession.updated_at.desc()).limit(limit).all()

    # 为每个会话计算消息数量
    result = []
    for session in sessions:
        message_count = db.query(Message).filter(
            Message.session_id == session.id
        ).count()

        session_data = ConsultationSession.model_validate(session).model_dump()
        session_data["message_count"] = message_count
        result.append(ConsultationSession(**session_data))

    return result


@router.get("/consultations/{session_id}", response_model=ConsultationDetailResponse)
def get_consultation_detail(
    session_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取对话详情（含消息列表）

    返回指定会话的所有消息
    """
    # 获取会话
    session = db.query(ConsultationSession).filter(
        ConsultationSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 验证权限（该会话必须属于当前医生）
    if session.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="无权查看此对话")

    # 获取消息
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()

    return ConsultationDetailResponse(
        session=ConsultationSession.model_validate(session),
        messages=[
            ConsultationMessage(
                id=msg.id,
                sender=msg.sender.value,
                content=msg.content,
                created_at=msg.created_at
            )
            for msg in messages
        ]
    )
```

**Step 2: 注册路由（同上）**

**Step 3: Commit**

```bash
git add backend/app/routes/doctor_consultations.py
git commit -m "feat(api): add doctor consultation history routes"
```

---

### Task 7: 创建医嘱管理路由（医生专用）

**Files:**
- Create: `backend/app/routes/doctor_orders.py`

**Step 1: 创建医嘱管理路由**

```python
"""
医生医嘱管理 API 路由

医生为患者创建、管理医嘱
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List

from ..database import get_db
from ..models.doctor import Doctor
from ..models.user import User
from ..models.medical_order import (
    MedicalOrder, TaskInstance, OrderStatus, OrderType,
    ScheduleType, TaskStatus
)
from ..routes.doctor_auth import get_current_doctor
from ..schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderResponse,
    TaskInstanceResponse, TaskListResponse
)
from ..services.medical_order_service import MedicalOrderService

router = APIRouter(prefix="/api/doctor", tags=["doctor-orders"])


@router.post("/orders", response_model=MedicalOrderResponse, status_code=201)
def create_order(
    request: MedicalOrderCreateRequest,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    为患者创建医嘱

    doctor_id 自动设置为当前医生
    """
    # 验证患者存在
    patient = db.query(User).filter(User.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    service = MedicalOrderService(db)

    order_data = request.model_dump()
    order_data["doctor_id"] = doctor.id  # 设置为当前医生

    order = service.create_draft_order(order_data)

    return MedicalOrderResponse.model_validate(order)


@router.get("/patients/{patient_id}/orders", response_model=list[MedicalOrderResponse])
def get_patient_orders(
    patient_id: int,
    status_filter: str = None,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者的医嘱列表"""
    query = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient_id
    )

    if status_filter:
        try:
            status = OrderStatus(status_filter)
            query = query.filter(MedicalOrder.status == status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值")

    orders = query.order_by(MedicalOrder.created_at.desc()).all()

    return [MedicalOrderResponse.model_validate(o) for o in orders]


@router.get("/patients/{patient_id}/tasks", response_model=TaskListResponse)
def get_patient_tasks(
    patient_id: int,
    task_date: date,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者指定日期的任务列表"""
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
        return TaskInstanceResponse(**data)

    total = len(tasks)
    completed_count = len(completed)

    from ..schemas.medical_order import ComplianceResponse

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

**Step 2: 注册路由**

**Step 3: Commit**

```bash
git add backend/app/routes/doctor_orders.py
git commit -m "feat(api): add doctor medical orders management routes"
```

---

## Phase 2: 前端基础架构

### Task 8: 创建医生工作台前端目录结构

**Files:**
- Create: `frontend/doctor/` 目录结构

**Step 1: 创建目录结构**

```bash
cd frontend
mkdir -p doctor/src/{api,pages,layouts,components,store,types,utils}
mkdir -p doctor/public
```

**Step 2: 创建 package.json**

```json
{
  "name": "doctor-workstation",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.6",
    "axios": "^1.6.2",
    "zustand": "^4.4.7",
    "dayjs": "^1.11.10"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8"
  }
}
```

**Step 3: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

**Step 4: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Step 5: Commit**

```bash
git add frontend/doctor/
git commit -m "feat(frontend): initialize doctor workstation project structure"
```

---

### Task 9: 创建 API 客户端

**Files:**
- Create: `frontend/doctor/src/api/index.ts`
- Create: `frontend/doctor/src/api/doctor.ts`

**Step 1: 创建 axios 实例配置**

`frontend/doctor/src/api/index.ts`:

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('doctor_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('doctor_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

**Step 2: 创建医生认证 API**

`frontend/doctor/src/api/doctor.ts`:

```typescript
import api from './index'

export interface DoctorLoginRequest {
  username: string
  password: string
}

export interface Doctor {
  id: number
  name: string
  title?: string
  department_id: number
  hospital?: string
  specialty?: string
  avatar_url?: string
  is_active: boolean
  username?: string
}

export interface Patient {
  id: number
  nickname?: string
  phone: string
  gender?: string
  age?: number
  last_consultation_at?: string
  active_orders_count: number
  completion_rate: number
}

export const doctorApi = {
  // 认证
  login: (data: DoctorLoginRequest) =>
    api.post('/doctor/auth/login', data),

  getCurrentDoctor: () =>
    api.get('/doctor/auth/me'),

  logout: () =>
    api.post('/doctor/auth/logout'),

  // 患者
  getPatients: (params?: { search?: string }) =>
    api.get('/doctor/patients', { params }),

  getPatientDetail: (patientId: number) =>
    api.get(`/doctor/patients/${patientId}`),

  // 对话记录
  getConsultations: (patientId: number, params?: { limit?: number }) =>
    api.get(`/doctor/patients/${patientId}/consultations`, { params }),

  getConsultationDetail: (sessionId: string) =>
    api.get(`/doctor/consultations/${sessionId}`),

  // 医嘱
  createOrder: (data: any) =>
    api.post('/doctor/orders', data),

  getPatientOrders: (patientId: number, params?: { status?: string }) =>
    api.get(`/doctor/patients/${patientId}/orders`, { params }),

  getPatientTasks: (patientId: number, taskDate: string) =>
    api.get(`/doctor/patients/${patientId}/tasks`, { params: { task_date: taskDate } })
}
```

**Step 3: Commit**

```bash
git add frontend/doctor/src/api/
git commit -m "feat(frontend): add API client for doctor workstation"
```

---

### Task 10: 创建状态管理（Zustand）

**Files:**
- Create: `frontend/doctor/src/store/authStore.ts`

**Step 1: 创建认证状态管理**

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { doctorApi, Doctor } from '../api/doctor'

interface AuthState {
  doctor: Doctor | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (doctor: Doctor, token: string) => void
  logout: () => void
  loadFromStorage: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      doctor: null,
      token: null,
      isAuthenticated: false,

      setAuth: (doctor, token) => {
        localStorage.setItem('doctor_token', token)
        set({ doctor, token, isAuthenticated: true })
      },

      logout: () => {
        localStorage.removeItem('doctor_token')
        set({ doctor: null, token: null, isAuthenticated: false })
      },

      loadFromStorage: () => {
        const token = localStorage.getItem('doctor_token')
        if (token) {
          set({ token, isAuthenticated: true })
          // 获取医生信息
          doctorApi.getCurrentDoctor()
            .then((res: any) => {
              set({ doctor: res.doctor })
            })
            .catch(() => {
              localStorage.removeItem('doctor_token')
              set({ doctor: null, token: null, isAuthenticated: false })
            })
        }
      }
    }),
    {
      name: 'doctor-auth-storage',
      partialize: (state) => ({
        token: state.token,
        doctor: state.doctor,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/store/
git commit -m "feat(frontend): add auth state management with Zustand"
```

---

### Task 11: 创建登录页面

**Files:**
- Create: `frontend/doctor/src/pages/Login.tsx`

**Step 1: 创建登录页面组件**

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { doctorApi } from '../api/doctor'
import { useAuthStore } from '../store/authStore'

const { Title, Text } = Typography

const Login = () => {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res: any = await doctorApi.login(values)
      setAuth(res.doctor, res.access_token)
      message.success('登录成功')
      navigate('/')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card
        style={{ width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={3} style={{ color: '#667eea', marginBottom: 8 }}>
            灵犀健康
          </Title>
          <Text type="secondary">医生工作台</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ background: '#667eea', borderColor: '#667eea' }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            测试账号: test_doctor / test123
          </Text>
        </div>
      </Card>
    </div>
  )
}

export default Login
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/pages/Login.tsx
git commit -m "feat(frontend): add doctor login page"
```

---

### Task 12: 创建主布局组件

**Files:**
- Create: `frontend/doctor/src/layouts/DoctorLayout.tsx`

**Step 1: 创建主布局**

```typescript
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Button, theme } from 'antd'
import {
  TeamOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons'
import { useState } from 'react'
import { useAuthStore } from '../store/authStore'

const { Header, Sider, Content } = Layout

const DoctorLayout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()
  const doctor = useAuthStore((state) => state.doctor)
  const logout = useAuthStore((state) => state.logout)

  const menuItems = [
    {
      key: '/',
      icon: <TeamOutlined />,
      label: '患者列表'
    }
  ]

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true
    }
  ]

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout()
      navigate('/login')
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{ background: token.colorBgContainer }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `1px solid ${token.colorBorderSecondary}`
          }}
        >
          <h2 style={{ color: token.colorPrimary, margin: 0, fontSize: collapsed ? 16 : 18 }}>
            {collapsed ? '灵犀' : '灵犀健康'}
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorderSecondary}`
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />

          <Dropdown
            menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
            placement="bottomRight"
          >
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{doctor?.name || '医生'}</span>
            </div>
          </Dropdown>
        </Header>

        <Content
          style={{
            margin: 24,
            padding: 24,
            background: token.colorBgContainer,
            borderRadius: token.borderRadiusLG,
            overflow: 'auto'
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default DoctorLayout
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/layouts/DoctorLayout.tsx
git commit -m "feat(frontend): add doctor main layout component"
```

---

### Task 13: 创建患者列表页面

**Files:**
- Create: `frontend/doctor/src/pages/Patients.tsx`

**Step 1: 创建患者列表页面**

```typescript
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Input, Card, Tag, Space, Progress, Typography } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { doctorApi, Patient } from '../api/doctor'

const { Title } = Typography

const Patients = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [patients, setPatients] = useState<Patient[]>([])
  const [searchText, setSearchText] = useState('')

  useEffect(() => {
    fetchPatients()
  }, [searchText])

  const fetchPatients = async () => {
    setLoading(true)
    try {
      const res: any = await doctorApi.getPatients(
        searchText ? { search: searchText } : undefined
      )
      setPatients(res)
    } catch (error) {
      console.error('Failed to fetch patients:', error)
    } finally {
      setLoading(false)
    }
  }

  const columns: ColumnsType<Patient> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60
    },
    {
      title: '姓名',
      dataIndex: 'nickname',
      render: (name: string, record: Patient) => (
        <Space>
          <span>{name || '未设置'}</span>
          {record.gender && (
            <Tag color={record.gender === '男' ? 'blue' : 'pink'}>
              {record.gender}
            </Tag>
          )}
        </Space>
      )
    },
    {
      title: '年龄',
      dataIndex: 'age',
      width: 80
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      width: 130
    },
    {
      title: '进行中医嘱',
      dataIndex: 'active_orders_count',
      width: 100,
      render: (count: number) => (
        <Tag color={count > 0 ? 'blue' : 'default'}>{count}</Tag>
      )
    },
    {
      title: '完成率',
      dataIndex: 'completion_rate',
      width: 150,
      render: (rate: number) => {
        const percent = Math.round(rate * 100)
        const color = percent >= 80 ? 'success' : percent >= 50 ? 'normal' : 'exception'
        return <Progress percent={percent} status={color} size="small" />
      }
    },
    {
      title: '最后咨询',
      dataIndex: 'last_consultation_at',
      width: 120,
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-'
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>我的患者</Title>
        <Input
          placeholder="搜索患者姓名或手机号"
          prefix={<SearchOutlined />}
          style={{ width: 250 }}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />
      </div>

      <Table
        columns={columns}
        dataSource={patients}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        onRow={(record) => ({
          onClick: () => navigate(`/patients/${record.id}`),
          style: { cursor: 'pointer' }
        })}
      />
    </div>
  )
}

export default Patients
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/pages/Patients.tsx
git commit -m "feat(frontend): add patients list page"
```

---

### Task 14: 创建患者详情页面

**Files:**
- Create: `frontend/doctor/src/pages/PatientDetail.tsx`

**Step 1: 创建患者详情页面（框架）**

```typescript
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Tabs, Card, Row, Col, Statistic, Tag, Typography, Button, Space } from 'antd'
import {
  UserOutlined,
  ArrowLeftOutlined,
  MessageOutlined,
  FileTextOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { doctorApi, Patient } from '../api/doctor'
import ConsultationsTab from '../components/PatientDetail/ConsultationsTab'
import OrdersTab from '../components/PatientDetail/OrdersTab'
import TasksTab from '../components/PatientDetail/TasksTab'

const { Title, Text } = Typography

const PatientDetail = () => {
  const navigate = useNavigate()
  const { patientId } = useParams<{ patientId: string }>()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (patientId) {
      fetchPatientDetail()
    }
  }, [patientId])

  const fetchPatientDetail = async () => {
    setLoading(true)
    try {
      const res: any = await doctorApi.getPatientDetail(Number(patientId))
      setPatient(res)
    } catch (error) {
      console.error('Failed to fetch patient:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !patient) {
    return <div>加载中...</div>
  }

  const percent = Math.round(patient.completion_rate * 100)

  const tabItems = [
    {
      key: 'consultations',
      label: 'AI对话记录',
      icon: <MessageOutlined />,
      children: <ConsultationsTab patientId={Number(patientId)} />
    },
    {
      key: 'orders',
      label: '医嘱管理',
      icon: <FileTextOutlined />,
      children: <OrdersTab patientId={Number(patientId)} refresh={fetchPatientDetail} />
    },
    {
      key: 'tasks',
      label: '任务完成情况',
      icon: <CheckCircleOutlined />,
      children: <TasksTab patientId={Number(patientId)} />
    }
  ]

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/')}
        style={{ marginBottom: 16 }}
      >
        返回患者列表
      </Button>

      {/* 患者基本信息卡片 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={24} align="middle">
          <Col>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: '#f0f0f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <UserOutlined style={{ fontSize: 32, color: '#999' }} />
            </div>
          </Col>
          <Col flex={1}>
            <Space size="large" align="center">
              <Title level={4} style={{ margin: 0 }}>
                {patient.nickname || '未设置姓名'}
              </Title>
              {patient.gender && (
                <Tag color={patient.gender === '男' ? 'blue' : 'pink'}>
                  {patient.gender}
                </Tag>
              )}
              <Text type="secondary">{patient.age}岁</Text>
              <Text type="secondary">{patient.phone}</Text>
            </Space>
          </Col>
          <Col>
            <Space size="large">
              <Statistic title="进行中医嘱" value={patient.active_orders_count} />
              <Statistic
                title="完成率"
                value={percent}
                suffix="%"
                valueStyle={{ color: percent >= 80 ? '#52c41a' : percent >= 50 ? '#faad14' : '#f5222d' }}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Tab 内容区 */}
      <Card>
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}

export default PatientDetail
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/pages/PatientDetail.tsx
git commit -m "feat(frontend): add patient detail page framework"
```

---

### Task 15: 创建对话记录 Tab 组件

**Files:**
- Create: `frontend/doctor/src/components/PatientDetail/ConsultationsTab.tsx`

**Step 1: 创建对话记录组件**

```typescript
import { useState, useEffect } from 'react'
import { List, Tag, Avatar, Empty, Typography, Divider } from 'antd'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'
import { doctorApi } from '../../api/doctor'

const { Text } = Typography

interface ConsultationsTabProps {
  patientId: number
}

interface Message {
  id: number
  sender: string
  content: string
  created_at: string
}

interface Session {
  id: string
  created_at: string
  updated_at: string
  message_count?: number
}

interface ConsultationDetail {
  session: Session
  messages: Message[]
}

const ConsultationsTab = ({ patientId }: ConsultationsTabProps) => {
  const [loading, setLoading] = useState(true)
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSession, setSelectedSession] = useState<ConsultationDetail | null>(null)

  useEffect(() => {
    fetchSessions()
  }, [patientId])

  const fetchSessions = async () => {
    setLoading(true)
    try {
      const res: any = await doctorApi.getConsultations(patientId, { limit: 20 })
      setSessions(res)
      if (res.length > 0) {
        fetchSessionDetail(res[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch consultations:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSessionDetail = async (sessionId: string) => {
    try {
      const res: any = await doctorApi.getConsultationDetail(sessionId)
      setSelectedSession(res)
    } catch (error) {
      console.error('Failed to fetch session detail:', error)
    }
  }

  if (loading) {
    return <div>加载中...</div>
  }

  return (
    <div style={{ display: 'flex', gap: 16, height: 500 }}>
      {/* 左侧：会话列表 */}
      <div style={{ width: 280, overflowY: 'auto' }}>
        <List
          dataSource={sessions}
          renderItem={(session: Session) => (
            <List.Item
              key={session.id}
              onClick={() => fetchSessionDetail(session.id)}
              style={{
                cursor: 'pointer',
                padding: 12,
                background: selectedSession?.session.id === session.id ? '#f0f0f0' : 'transparent',
                borderRadius: 8
              }}
            >
              <div style={{ width: '100%' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {new Date(session.created_at).toLocaleString()}
                </Text>
                <div style={{ marginTop: 4 }}>
                  {session.message_count || 0} 条消息
                </div>
              </div>
            </List.Item>
          )}
        />
      </div>

      {/* 右侧：对话详情 */}
      <div style={{ flex: 1, overflowY: 'auto', background: '#f9f9f9', borderRadius: 8, padding: 16 }}>
        {selectedSession ? (
          <div>
            {selectedSession.messages.map((msg: Message) => (
              <div key={msg.id} style={{ marginBottom: 16 }}>
                {msg.sender === 'user' ? (
                  <div style={{ textAlign: 'right' }}>
                    <div
                      style={{
                        display: 'inline-block',
                        maxWidth: '70%',
                        padding: '8px 12px',
                        background: 'white',
                        borderRadius: 12,
                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <Avatar size={20} icon={<UserOutlined />} />
                        <Text type="secondary" style={{ fontSize: 12 }}>患者</Text>
                      </div>
                      <Text>{msg.content}</Text>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'left' }}>
                    <div
                      style={{
                        display: 'inline-block',
                        maxWidth: '70%',
                        padding: '8px 12px',
                        background: '#e6f7ff',
                        borderRadius: 12,
                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <Avatar size={20} icon={<RobotOutlined />} style={{ background: '#1890ff' }} />
                        <Text type="secondary" style={{ fontSize: 12 }}>AI医生</Text>
                      </div>
                      <Text>{msg.content}</Text>
                    </div>
                  </div>
                )}
                <div style={{ textAlign: 'center', margin: '8px 0' }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </Text>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty description="选择一个对话查看详情" />
        )}
      </div>
    </div>
  )
}

export default ConsultationsTab
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/components/PatientDetail/ConsultationsTab.tsx
git commit -m "feat(frontend): add consultations tab component"
```

---

### Task 16: 创建医嘱管理 Tab 组件

**Files:**
- Create: `frontend/doctor/src/components/PatientDetail/OrdersTab.tsx`

**Step 1: 创建医嘱管理组件**

```typescript
import { useState, useEffect } from 'react'
import { List, Tag, Button, Modal, Form, Input, Select, DatePicker, message, Empty } from 'antd'
import { PlusOutlined, EditOutlined, StopOutlined } from '@ant-design/icons'
import { doctorApi } from '../../api/doctor'
import dayjs from 'dayjs'

interface OrdersTabProps {
  patientId: number
  refresh: () => void
}

interface Order {
  id: number
  title: string
  order_type: string
  status: string
  schedule_type: string
  start_date: string
  end_date?: string
  reminder_times: string[]
}

const ORDER_TYPE_MAP = {
  medication: { label: '用药', color: 'blue' },
  monitoring: { label: '监测', color: 'green' },
  behavior: { label: '行为', color: 'orange' },
  followup: { label: '复诊', color: 'purple' }
}

const STATUS_MAP = {
  draft: { label: '草稿', color: 'default' },
  active: { label: '进行中', color: 'blue' },
  completed: { label: '已完成', color: 'success' },
  stopped: { label: '已停用', color: 'error' }
}

const OrdersTab = ({ patientId, refresh }: OrdersTabProps) => {
  const [loading, setLoading] = useState(true)
  const [orders, setOrders] = useState<Order[]>([])
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchOrders()
  }, [patientId])

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const res: any = await doctorApi.getPatientOrders(patientId)
      setOrders(res)
    } catch (error) {
      console.error('Failed to fetch orders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      const data = {
        ...values,
        patient_id: patientId,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
        reminder_times: values.reminder_times || []
      }

      await doctorApi.createOrder(data)
      message.success('医嘱创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchOrders()
      refresh()
    } catch (error) {
      console.error('Create order failed:', error)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, textAlign: 'right' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          下达新医嘱
        </Button>
      </div>

      {orders.length === 0 ? (
        <Empty description="暂无医嘱" />
      ) : (
        <List
          loading={loading}
          dataSource={orders}
          renderItem={(order: Order) => (
            <List.Item
              style={{
                padding: 16,
                background: '#fafafa',
                borderRadius: 8,
                marginBottom: 8
              }}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Tag color={ORDER_TYPE_MAP[order.order_type]?.color}>
                      {ORDER_TYPE_MAP[order.order_type]?.label}
                    </Tag>
                    {order.title}
                  </Space>
                }
                description={
                  <Space split={<span>|</span>}>
                    <span>{order.schedule_type}</span>
                    <span>{order.reminder_times?.join(', ') || '-'}</span>
                    <span>{order.start_date} 起</span>
                  </Space>
                }
              />
              <Tag color={STATUS_MAP[order.status]?.color}>
                {STATUS_MAP[order.status]?.label}
              </Tag>
            </List.Item>
          )}
        />
      )}

      {/* 创建医嘱弹窗 */}
      <Modal
        title="下达新医嘱"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="order_type"
            label="医嘱类型"
            rules={[{ required: true, message: '请选择医嘱类型' }]}
          >
            <Select placeholder="选择类型">
              <Select.Option value="medication">用药</Select.Option>
              <Select.Option value="monitoring">监测</Select.Option>
              <Select.Option value="behavior">行为</Select.Option>
              <Select.Option value="followup">复诊</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="title"
            label="医嘱标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="例如：早餐前注射胰岛素" />
          </Form.Item>

          <Form.Item name="description" label="详细说明">
            <Input.TextArea rows={3} placeholder="医嘱的详细说明..." />
          </Form.Item>

          <Form.Item
            name="schedule_type"
            label="调度类型"
            rules={[{ required: true, message: '请选择调度类型' }]}
          >
            <Select placeholder="选择调度">
              <Select.Option value="once">一次性</Select.Option>
              <Select.Option value="daily">每日</Select.Option>
              <Select.Option value="weekly">每周</Select.Option>
              <Select.Option value="custom">自定义</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="start_date"
            label="开始日期"
            rules={[{ required: true, message: '请选择开始日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="end_date" label="结束日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="reminder_times" label="提醒时间">
            <Select
              mode="tags"
              placeholder="输入提醒时间，如 08:00"
              style={{ width: '100%' }}
            >
              <Select.Option value="08:00">08:00</Select.Option>
              <Select.Option value="12:00">12:00</Select.Option>
              <Select.Option value="18:00">18:00</Select.Option>
              <Select.Option value="21:00">21:00</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="frequency" label="频次">
            <Input placeholder="例如：每日3次" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default OrdersTab
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/components/PatientDetail/OrdersTab.tsx
git commit -m "feat(frontend): add orders management tab component"
```

---

### Task 17: 创建任务完成情况 Tab 组件

**Files:**
- Create: `frontend/doctor/src/components/PatientDetail/TasksTab.tsx`

**Step 1: 创建任务完成情况组件**

```typescript
import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Tag, List, Empty } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined, StopOutlined } from '@ant-design/icons'
import { doctorApi } from '../../api/doctor'
import dayjs from 'dayjs'

interface TasksTabProps {
  patientId: number
}

interface Task {
  id: number
  order_title?: string
  order_type?: string
  scheduled_time: string
  status: string
  completed_at?: string
}

interface TaskSummary {
  date: string
  total: number
  completed: number
  overdue: number
  pending: number
  rate: number
}

interface TaskListResponse {
  date: string
  pending: Task[]
  completed: Task[]
  overdue: Task[]
  summary: TaskSummary
}

const TASK_STATUS_MAP = {
  pending: { label: '待完成', color: 'default', icon: <ClockCircleOutlined /> },
  completed: { label: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
  overdue: { label: '已超时', color: 'error', icon: <StopOutlined /> }
}

const TasksTab = ({ patientId }: TasksTabProps) => {
  const [loading, setLoading] = useState(true)
  const [taskData, setTaskData] = useState<TaskListResponse | null>(null)
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'))

  useEffect(() => {
    fetchTasks(selectedDate)
  }, [patientId, selectedDate])

  const fetchTasks = async (date: string) => {
    setLoading(true)
    try {
      const res: any = await doctorApi.getPatientTasks(patientId, date)
      setTaskData(res)
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !taskData) {
    return <div>加载中...</div>
  }

  const { summary, pending, completed, overdue } = taskData
  const percent = Math.round(summary.rate * 100)
  const color = percent >= 80 ? 'success' : percent >= 50 ? 'normal' : 'exception'

  // 渲染任务卡片
  const renderTaskCard = (title: string, tasks: Task[]) => (
    <Card
      type="inner"
      title={<Tag color={tasks[0] ? TASK_STATUS_MAP[tasks[0].status]?.color : 'default'}>{title} ({tasks.length})</Tag>}
      size="small"
    >
      {tasks.length === 0 ? (
        <Empty description="无" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={tasks}
          renderItem={(task: Task) => (
            <List.Item>
              <List.Item.Meta
                title={task.order_title || '未命名任务'}
                description={
                  <span>
                    <Tag color="blue">{task.order_type}</Tag>
                    {task.scheduled_time}
                  </span>
                }
              />
              {task.completed_at && (
                <Tag color="success">{dayjs(task.completed_at).format('HH:mm')}</Tag>
              )}
            </List.Item>
          )}
        />
      )}
    </Card>
  )

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务"
              value={summary.total}
              suffix={`/ ${summary.completed + summary.overdue}`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="完成率"
              value={percent}
              suffix="%"
              valueStyle={{ color: percent >= 80 ? '#52c41a' : percent >= 50 ? '#faad14' : '#f5222d' }}
            />
            <Progress percent={percent} status={color} size="small" showInfo={false} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待完成"
              value={summary.pending}
              valueStyle={{ color: summary.pending > 0 ? '#1890ff' : undefined }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已超时"
              value={summary.overdue}
              valueStyle={{ color: summary.overdue > 0 ? '#f5222d' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 任务列表 */}
      <Row gutter={16}>
        <Col span={8}>{renderTaskCard('待完成', pending)}</Col>
        <Col span={8}>{renderTaskCard('已完成', completed)}</Col>
        <Col span={8}>{renderTaskCard('已超时', overdue)}</Col>
      </Row>
    </div>
  )
}

export default TasksTab
```

**Step 2: Commit**

```bash
git add frontend/doctor/src/components/PatientDetail/TasksTab.tsx
git commit -m "feat(frontend): add tasks completion tab component"
```

---

### Task 18: 创建 App 入口和路由配置

**Files:**
- Create: `frontend/doctor/src/App.tsx`
- Create: `frontend/doctor/src/main.tsx`

**Step 1: 创建 App.tsx**

```typescript
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Login from './pages/Login'
import DoctorLayout from './layouts/DoctorLayout'
import Patients from './pages/Patients'
import PatientDetail from './pages/PatientDetail'
import { useAuthStore } from './store/authStore'

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const loadFromStorage = useAuthStore((state) => state.loadFromStorage)

  useEffect(() => {
    loadFromStorage()
  }, [])

  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login />
              )
            }
          />
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <DoctorLayout />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          >
            <Route index element={<Patients />} />
            <Route path="patients/:patientId" element={<PatientDetail />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
```

**Step 2: 创建 main.tsx**

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

**Step 3: 创建 index.css**

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: 'Courier New', monospace;
}
```

**Step 4: 创建 index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>灵犀健康 - 医生工作台</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 5: Commit**

```bash
git add frontend/doctor/src/App.tsx frontend/doctor/src/main.tsx frontend/doctor/src/index.css frontend/doctor/index.html
git commit -m "feat(frontend): add App entry and routing configuration"
```

---

## Phase 3: 测试和验证

### Task 19: 端到端测试

**Step 1: 启动后端服务**

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Step 2: 启动前端服务**

```bash
cd frontend/doctor
npm install
npm run dev
```

**Step 3: 测试功能清单**

- [ ] 医生登录功能
- [ ] 患者列表展示
- [ ] 患者搜索功能
- [ ] 患者详情页查看
- [ ] AI对话记录查看
- [ ] 医嘱创建功能
- [ ] 任务完成情况查看

**Step 4: Commit**

```bash
git commit -m "test(e2e): complete end-to-end testing verification"
```

---

## 完成检查清单

- [ ] 所有代码已提交
- [ ] 后端 API 测试通过
- [ ] 前端页面无报错
- [ ] 登录功能正常
- [ ] 患者列表正常显示
- [ ] 对话记录正常显示
- [ ] 医嘱创建功能正常
- [ ] 任务完成情况正常显示

---

## 参考文件

### 现有代码文件（审查确认）
| 类型 | 文件 | 说明 |
|------|------|------|
| 模型 | `backend/app/models/doctor.py` | ✅ 已存在，需扩展登录字段 |
| 模型 | `backend/app/models/medical_order.py` | ✅ 已存在 |
| 模型 | `backend/app/models/session.py` | ✅ 已存在，doctor_id 指向 doctors |
| 模型 | `backend/app/models/message.py` | ✅ 已存在 |
| 模型 | `backend/app/models/user.py` | ✅ 已存在 |
| Schemas | `backend/app/schemas/doctor.py` | ✅ 已存在，需扩展认证 schemas |
| Schemas | `backend/app/schemas/medical_order.py` | ✅ 已存在 |
| 路由 | `backend/app/routes/admin_auth.py` | ✅ 可参考模式 |

### 设计文档
- 设计文档: `docs/plans/2026-02-07-doctor-workstation-design.md`
- 前端参考: `frontend/src/pages/MedicalOrders.tsx`

### ⚠️ 数据模型约束
- `MedicalOrder.doctor_id` 外键 → `admin_users.id` (不是 `doctors.id`)
- `Session.doctor_id` 外键 → `doctors.id` ✓
