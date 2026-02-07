# 医生工作台实施计划 v2.0

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **最后更新:** 2026-02-07 - v2.0 基于代码评估重新设计

**核心变更:**
- 复用 `admin_users` 表，新增 `doctor` 角色
- 前端在 `frontend/src/pages/doctor/` 子目录
- 复用现有 admin 认证系统
- 保持 `MedicalOrder.doctor_id` → `admin_users.id` 不变

---

## 实施步骤总览

| Phase | 任务 | 预计时间 |
|-------|------|----------|
| Phase 1 | 后端基础扩展 | 1-2天 |
| Phase 2 | 后端 API 开发 | 2-3天 |
| Phase 3 | 前端基础 | 1天 |
| Phase 4 | 前端页面开发 | 2-3天 |
| Phase 5 | 测试验证 | 1天 |

---

## Phase 1: 后端基础扩展

### Task 1: 扩展 AdminUser 模型

**Files:**
- Modify: `backend/app/models/admin_user.py`

**Step 1: 添加医生属性字段**

```python
# backend/app/models/admin_user.py

# 需要添加的导入
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

# 在 AdminUser 类中添加（last_login_at 字段之后）：

# 医生专属属性（当 role='doctor' 时使用）
doctor_attributes = Column(JSON, nullable=True)
# 示例数据：
# {
#   "title": "主治医师",
#   "specialty": "皮肤科",
#   "license_no": "执业医师证号",
#   "hospital": "医院名称"
# }

# 科室关联（用于关联 AI 分身）
department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
department = relationship("Department", back_populates="admin_users")
```

**注意**：同时需要在 `Department` 模型中添加反向关系：

```python
# backend/app/models/department.py

class Department(Base):
    # ... 现有字段

    # 新增：反向关系
    admin_users = relationship("AdminUser", back_populates="department")
```

**Step 2: 数据库迁移**

```bash
# 连接到数据库
psql -h localhost -U your_user -d xinlin

# 执行迁移
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS doctor_attributes JSONB;
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS department_id INTEGER;

# 添加外键约束（可选）
ALTER TABLE admin_users ADD CONSTRAINT fk_admin_users_department
  FOREIGN KEY (department_id) REFERENCES departments(id);
```

**Step 3: 验证**

```bash
cd backend
python -c "from app.models.admin_user import AdminUser; print('AdminUser model OK')"
```

**Step 4: Commit**

```bash
git add backend/app/models/admin_user.py
git commit -m "feat(model): add doctor_attributes to AdminUser for doctor role"
```

---

### Task 2: 扩展 Admin Schemas

**Files:**
- Modify: `backend/app/schemas/admin.py`

**Step 1: 添加医生相关 schemas**

在文件末尾添加：

```python
# ============= 医生相关 Schemas =============

class DoctorInfo(BaseModel):
    """医生专属信息"""
    title: Optional[str] = None      # 职称
    specialty: Optional[str] = None   # 专科
    license_no: Optional[str] = None  # 执业医师证号
    hospital: Optional[str] = None    # 医院


class DoctorCreateRequest(BaseModel):
    """创建医生请求"""
    username: str
    password: str
    email: Optional[str] = None
    role: str = "doctor"

    # 医生专属信息
    title: Optional[str] = None
    specialty: Optional[str] = None
    license_no: Optional[str] = None
    hospital: Optional[str] = None


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

**Step 2: 更新 AdminUserResponse**

在现有的 `AdminUserResponse` 类中添加：

```python
# 在 AdminUserResponse 类中添加：
doctor_info: Optional[DoctorInfo] = None
```

**Step 3: 添加必要的导入**

```python
# 文件顶部确保有：
from typing import List, Optional, Any
from datetime import datetime
```

**Step 4: Commit**

```bash
git add backend/app/schemas/admin.py
git commit -m "feat(schemas): add doctor-related schemas for doctor workstation"
```

---

### Task 3: 更新认证服务支持医生角色

**Files:**
- Modify: `backend/app/routes/admin_auth.py`

**Step 1: 添加医生角色验证函数**

在 `get_current_admin` 函数后添加：

```python
def get_current_doctor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """获取当前登录的医生（role 必须为 'doctor'）"""
    admin = get_current_admin(credentials, db)

    # 验证角色
    if admin.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要医生权限"
        )

    return admin
```

**Step 2: 导出新函数**

确保导出：

```python
from .admin_auth import get_current_admin, get_current_doctor
```

**Step 3: Commit**

```bash
git add backend/app/routes/admin_auth.py
git commit -m "feat(auth): add get_current_doctor dependency for doctor role"
```

---

### Task 4: 更新 AdminUserService 支持创建医生

**Files:**
- Modify: `backend/app/services/admin_auth_service.py`

**Step 1: 扩展创建方法**

```python
@staticmethod
def create_admin_user(
    db: Session,
    username: str,
    password: str,
    email: str = None,
    role: str = "editor",
    doctor_attributes: dict = None  # 新增参数
) -> AdminUser:
    admin = AdminUser(
        username=username,
        password_hash=AdminAuthService.hash_password(password),
        email=email,
        role=role,
        doctor_attributes=doctor_attributes  # 新增
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
```

**Step 5: Commit**

```bash
git add backend/app/services/admin_auth_service.py
git commit -m "feat(service): support doctor_attributes in AdminAuthService"
```

---

## Phase 2: 后端 API 开发

### Task 5: 创建医生工作台路由

**Files:**
- Create: `backend/app/routes/doctor_workstation.py`

**Step 1: 创建路由文件**

```python
"""
医生工作台 API 路由

医生角色专用功能：
- 查看患者列表
- 查看患者对话记录
- 创建和管理医嘱
- 查看患者任务执行情况
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta, date

from ..database import get_db
from ..models.admin_user import AdminUser
from ..models.user import User
from ..models.session import Session as ConsultationSession
from ..models.message import Message, SenderType
from ..models.medical_order import (
    MedicalOrder, TaskInstance, OrderStatus, OrderType,
    ScheduleType, TaskStatus
)
from ..routes.admin_auth import get_current_doctor
from ..schemas.admin import (
    PatientListItem, PatientDetailResponse,
    ConsultationSession, ConsultationMessage, ConsultationDetailResponse
)
from ..schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderResponse,
    TaskInstanceResponse, TaskListResponse
)
from ..services.medical_order_service import MedicalOrderService

router = APIRouter(prefix="/api/doctor", tags=["doctor-workstation"])


# ============= 患者管理 =============

@router.get("/patients", response_model=List[PatientListItem])
def get_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取医生的患者列表

    返回与该医生管理的 AI 分身有过咨询的患者
    """
    # TODO: 关联医生与 AI 分身后，这里需要过滤
    # 当前返回所有有咨询记录的患者

    # 获取所有有咨询记录的患者 ID
    patient_ids = db.query(ConsultationSession.user_id).distinct().all()
    patient_ids = [p[0] for p in patient_ids]

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
            ConsultationSession.user_id == patient.id
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


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者详情"""
    patient = db.query(User).filter(User.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 最后咨询时间
    last_session = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
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


# ============= 对话记录 =============

@router.get("/patients/{patient_id}/consultations", response_model=List[ConsultationSession])
def get_patient_consultations(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取患者的对话列表

    返回该患者的所有对话会话
    """
    # 验证患者存在
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取对话会话
    sessions = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
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
    doctor: AdminUser = Depends(get_current_doctor),
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


# ============= 医嘱管理 =============

@router.post("/orders", response_model=MedicalOrderResponse, status_code=201)
def create_order(
    request: MedicalOrderCreateRequest,
    doctor: AdminUser = Depends(get_current_doctor),
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


@router.get("/patients/{patient_id}/orders", response_model=List[MedicalOrderResponse])
def get_patient_orders(
    patient_id: int,
    status_filter: Optional[str] = None,
    doctor: AdminUser = Depends(get_current_doctor),
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


@router.put("/orders/{order_id}", response_model=MedicalOrderResponse)
def update_order(
    order_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    end_date: Optional[date] = None,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """更新医嘱"""
    order = db.query(MedicalOrder).filter(MedicalOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    if title is not None:
        order.title = title
    if description is not None:
        order.description = description
    if end_date is not None:
        order.end_date = end_date

    db.commit()
    db.refresh(order)

    return MedicalOrderResponse.model_validate(order)


@router.delete("/orders/{order_id}")
def delete_order(
    order_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """停用医嘱"""
    order = db.query(MedicalOrder).filter(MedicalOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    order.status = OrderStatus.STOPPED
    db.commit()

    return {"message": "医嘱已停用"}


# ============= 任务执行情况 =============

@router.get("/patients/{patient_id}/tasks", response_model=TaskListResponse)
def get_patient_tasks(
    patient_id: int,
    task_date: date,
    doctor: AdminUser = Depends(get_current_doctor),
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

**Step 2: 在 main.py 中注册路由**

```python
# backend/app/main.py

from app.routes import doctor_workstation_router

app.include_router(doctor_workstation_router)
```

**Step 3: 在 routes/__init__.py 中导出**

```python
# backend/app/routes/__init__.py

from .doctor_workstation import router as doctor_workstation_router

__all__ = [
    # ... 其他路由
    "doctor_workstation_router",
]
```

**Step 4: Commit**

```bash
git add backend/app/routes/doctor_workstation.py
git add backend/app/main.py
git add backend/app/routes/__init__.py
git commit -m "feat(api): add doctor workstation routes"
```

---

## Phase 3: 前端基础

### Task 6: 修改 MainLayout 支持角色菜单

**Files:**
- Modify: `frontend/src/layouts/MainLayout.tsx`

**Step 1: 添加医生菜单**

```tsx
// frontend/src/layouts/MainLayout.tsx

// 引入新的图标
import {
  // ... 现有图标
  UserSwitchOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons';

// 医生专用菜单
const doctorMenuItems = [
  {
    key: '/patients',
    icon: <UserSwitchOutlined />,
    label: '我的患者',
  },
];

// 管理员菜单保持不变
const adminMenuItems = [
  // ... 现有菜单
];

// 根据角色选择菜单
const menuItems = user?.role === 'doctor' ? doctorMenuItems : adminMenuItems;
```

**Step 2: 更新页脚信息显示

医生用户显示不同的登录标识：

```tsx
<span>{user?.username} ({user?.role === 'doctor' ? '医生' : '管理员'})</span>
```

**Step 3: Commit**

```bash
git add frontend/src/layouts/MainLayout.tsx
git commit -m "feat(frontend): add role-based menu in MainLayout"
```

---

### Task 7: 修改 App.tsx 添加医生路由

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: 添加医生路由导入**

```tsx
// 新增医生页面组件（后续创建）
import PatientList from './pages/doctor/PatientList';
import PatientDetail from './pages/doctor/PatientDetail';
```

**Step 2: 添加医生路由**

```tsx
<Route
  path="/"
  element={
    isAuthenticated ? (
      <MainLayout user={user} onLogout={handleLogout} />
    ) : (
      <Navigate to="/login" replace />
    )
  }
>
  {/* 医生路由 */}
  {user?.role === 'doctor' && (
    <>
      <Route path="patients" element={<PatientList />} />
      <Route path="patients/:id" element={<PatientDetail />} />
    </>
  )}

  {/* 管理员路由（保持不变） */}
  {user?.role !== 'doctor' && (
    <>
      <Route index element={<Dashboard />} />
      {/* ... 其他路由 */}
    </>
  )}
</Route>
```

**Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): add doctor routes to App.tsx"
```

---

### Task 8: 创建医生页面目录和组件

**Files:**
- Create: `frontend/src/pages/doctor/PatientList.tsx`
- Create: `frontend/src/pages/doctor/PatientDetail.tsx`
- Create: `frontend/src/pages/doctor/ConsultationsTab.tsx`
- Create: `frontend/src/pages/doctor/OrdersTab.tsx`
- Create: `frontend/src/pages/doctor/TasksTab.tsx`

**Step 1: 创建患者列表页**

```tsx
// frontend/src/pages/doctor/PatientList.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Input, Card, Tag, Space, Progress, Typography } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  last_consultation_at?: string;
  active_orders_count: number;
  completion_rate: number;
}

const PatientList = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    fetchPatients();
  }, [searchText]);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const url = searchText
        ? `/api/doctor/patients?search=${encodeURIComponent(searchText)}`
        : '/api/doctor/patients';

      const response = await fetch(url);
      const data = await response.json();
      setPatients(data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<Patient> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
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
      ),
    },
    {
      title: '年龄',
      dataIndex: 'age',
      width: 80,
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      width: 130,
    },
    {
      title: '进行中医嘱',
      dataIndex: 'active_orders_count',
      width: 100,
      render: (count: number) => (
        <Tag color={count > 0 ? 'blue' : 'default'}>{count}</Tag>
      ),
    },
    {
      title: '完成率',
      dataIndex: 'completion_rate',
      width: 150,
      render: (rate: number) => {
        const percent = Math.round(rate * 100);
        const color = percent >= 80 ? 'success' : percent >= 50 ? 'normal' : 'exception';
        return <Progress percent={percent} status={color} size="small" />;
      },
    },
    {
      title: '最后咨询',
      dataIndex: 'last_consultation_at',
      width: 120,
      render: (date: string) => (date ? new Date(date).toLocaleDateString() : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Patient) => (
        <a onClick={() => navigate(`/patients/${record.id}`)}>查看</a>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>我的患者</Typography>
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
      />
    </div>
  );
};

export default PatientList;
```

**Step 2: 创建患者详情页（框架）**

```tsx
// frontend/src/pages/doctor/PatientDetail.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Tabs, Card, Row, Col, Statistic, Tag, Typography, Button, Space } from 'antd';
import {
  UserOutlined,
  ArrowLeftOutlined,
  MessageOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import ConsultationsTab from './ConsultationsTab';
import OrdersTab from './OrdersTab';
import TasksTab from './TasksTab';

const { Title, Text } = Typography;

interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  avatar_url?: string;
  active_orders_count: number;
  completion_rate: number;
}

const PatientDetail = () => {
  const navigate = useNavigate();
  const { patientId } = useParams<{ patientId: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (patientId) {
      fetchPatientDetail();
    }
  }, [patientId]);

  const fetchPatientDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/doctor/patients/${patientId}`);
      const data = await response.json();
      setPatient(data);
    } catch (error) {
      console.error('Failed to fetch patient:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !patient) {
    return <div>加载中...</div>;
  }

  const percent = Math.round(patient.completion_rate * 100);

  const tabItems = [
    {
      key: 'consultations',
      label: 'AI对话记录',
      icon: <MessageOutlined />,
      children: <ConsultationsTab patientId={Number(patientId)} />,
    },
    {
      key: 'orders',
      label: '医嘱管理',
      icon: <FileTextOutlined />,
      children: <OrdersTab patientId={Number(patientId)} refresh={fetchPatientDetail} />,
    },
    {
      key: 'tasks',
      label: '任务完成情况',
      icon: <CheckCircleOutlined />,
      children: <TasksTab patientId={Number(patientId)} />,
    },
  ];

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/patients')}
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
                justifyContent: 'center',
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
                valueStyle={{
                  color: percent >= 80 ? '#52c41a' : percent >= 50 ? '#faad14' : '#f5222d',
                }}
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
  );
};

export default PatientDetail;
```

**Step 3: 创建对话记录 Tab**

```tsx
// frontend/src/pages/doctor/ConsultationsTab.tsx

import React, { useState, useEffect } from 'react';
import { List, Tag, Avatar, Empty, Typography, Divider } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';

interface Props {
  patientId: number;
}

interface Message {
  id: number;
  sender: string;
  content: string;
  created_at: string;
}

interface Session {
  id: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

interface ConsultationDetail {
  session: Session;
  messages: Message[];
}

const ConsultationsTab = ({ patientId }: Props) => {
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<ConsultationDetail | null>(null);

  useEffect(() => {
    fetchSessions();
  }, [patientId]);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/doctor/patients/${patientId}/consultations`);
      const data = await response.json();
      setSessions(data);
      if (data.length > 0) {
        fetchSessionDetail(data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch consultations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetail = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/doctor/consultations/${sessionId}`);
      const data = await response.json();
      setSelectedSession(data);
    } catch (error) {
      console.error('Failed to fetch session detail:', error);
    }
  };

  if (loading) {
    return <div>加载中...</div>;
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
                background:
                  selectedSession?.session.id === session.id ? '#f0f0f0' : 'transparent',
                borderRadius: 8,
              }}
            >
              <div style={{ width: '100%' }}>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {new Date(session.created_at).toLocaleString()}
                </Typography.Text>
                <div style={{ marginTop: 4 }}>{session.message_count || 0} 条消息</div>
              </div>
            </List.Item>
          )}
        />
      </div>

      {/* 右侧：对话详情 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          background: '#f9f9f9',
          borderRadius: 8,
          padding: 16,
        }}
      >
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
                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <Avatar size={20} icon={<UserOutlined />} />
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          患者
                        </Typography.Text>
                      </div>
                      <Typography.Text>{msg.content}</Typography.Text>
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
                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <Avatar size={20} icon={<RobotOutlined />} style={{ background: '#1890ff' }} />
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          AI医生
                        </Typography.Text>
                      </div>
                      <Typography.Text>{msg.content}</Typography.Text>
                    </div>
                  </div>
                )}
                <div style={{ textAlign: 'center', margin: '8px 0' }}>
                  <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </Typography.Text>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty description="选择一个对话查看详情" />
        )}
      </div>
    </div>
  );
};

export default ConsultationsTab;
```

**Step 4: 创建医嘱管理 Tab**

```tsx
// frontend/src/pages/doctor/OrdersTab.tsx

import React, { useState, useEffect } from 'react';
import { List, Tag, Button, Modal, Form, Input, Select, DatePicker, message, Empty } from 'antd';
import { PlusOutlined, EditOutlined, StopOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface Props {
  patientId: number;
  refresh: () => void;
}

interface Order {
  id: number;
  title: string;
  order_type: string;
  status: string;
  schedule_type: string;
  start_date: string;
  end_date?: string;
  reminder_times: string[];
}

const ORDER_TYPE_MAP = {
  medication: { label: '用药', color: 'blue' },
  monitoring: { label: '监测', color: 'green' },
  behavior: { label: '行为', color: 'orange' },
  followup: { label: '复诊', color: 'purple' },
};

const STATUS_MAP = {
  draft: { label: '草稿', color: 'default' },
  active: { label: '进行中', color: 'blue' },
  completed: { label: '已完成', color: 'success' },
  stopped: { label: '已停用', color: 'error' },
};

const OrdersTab = ({ patientId, refresh }: Props) => {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState<Order[]>([]);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchOrders();
  }, [patientId]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/doctor/patients/${patientId}/orders`);
      const data = await response.json();
      setOrders(data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        patient_id: patientId,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
        reminder_times: values.reminder_times || [],
      };

      const response = await fetch('/api/doctor/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        message.success('医嘱创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        fetchOrders();
        refresh();
      }
    } catch (error) {
      console.error('Create order failed:', error);
    }
  };

  const handleStop = async (orderId: number) => {
    try {
      const response = await fetch(`/api/doctor/orders/${orderId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('医嘱已停用');
        fetchOrders();
        refresh();
      }
    } catch (error) {
      console.error('Stop order failed:', error);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 16, textAlign: 'right' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
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
                marginBottom: 8,
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
              {order.status === 'active' && (
                <Button
                  size="small"
                  danger
                  icon={<StopOutlined />}
                  onClick={() => handleStop(order.id)}
                >
                  停用
                </Button>
              )}
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
          setCreateModalVisible(false);
          form.resetFields();
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
  );
};

export default OrdersTab;
```

**Step 5: 创建任务情况 Tab**

```tsx
// frontend/src/pages/doctor/TasksTab.tsx

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, List, Empty, DatePicker } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, StopOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface Props {
  patientId: number;
}

interface Task {
  id: number;
  order_title?: string;
  order_type?: string;
  scheduled_time: string;
  status: string;
  completed_at?: string;
}

interface TaskSummary {
  date: string;
  total: number;
  completed: number;
  overdue: number;
  pending: number;
  rate: number;
}

interface TaskData {
  date: string;
  pending: Task[];
  completed: Task[];
  overdue: Task[];
  summary: TaskSummary;
}

const TASK_STATUS_MAP = {
  pending: { label: '待完成', color: 'default', icon: <ClockCircleOutlined /> },
  completed: { label: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
  overdue: { label: '已超时', color: 'error', icon: <StopOutlined /> },
};

const TasksTab = ({ patientId }: Props) => {
  const [loading, setLoading] = useState(true);
  const [taskData, setTaskData] = useState<TaskData | null>(null);
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'));

  useEffect(() => {
    fetchTasks(selectedDate);
  }, [patientId, selectedDate]);

  const fetchTasks = async (date: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/doctor/patients/${patientId}/tasks?task_date=${date}`
      );
      const data = await response.json();
      setTaskData(data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !taskData) {
    return <div>加载中...</div>;
  }

  const { summary, pending, completed, overdue } = taskData;
  const percent = Math.round(summary.rate * 100);
  const color = percent >= 80 ? 'success' : percent >= 50 ? 'normal' : 'exception';

  const renderTaskCard = (title: string, tasks: Task[]) => (
    <Card
      type="inner"
      title={
        <Tag color={tasks[0] ? TASK_STATUS_MAP[tasks[0].status]?.color : 'default'}>
          {title} ({tasks.length})
        </Tag>
      }
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
  );

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <DatePicker
          value={dayjs(selectedDate)}
          onChange={(date) => setSelectedDate(date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'))}
          allowClear={false}
        />
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总任务" value={summary.total} />
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
  );
};

export default TasksTab;
```

**Step 6: Commit**

```bash
git add frontend/src/pages/doctor/
git commit -m "feat(frontend): add doctor workstation pages"
```

---

## Phase 4: 测试验证

### Task 9: 端到端测试

**Step 1: 创建测试医生账号**

```bash
# 方法1：通过 Python 脚本
cd backend
python -c "
from app.database import SessionLocal
from app.services.admin_auth_service import AdminAuthService

db = SessionLocal()
doctor = AdminAuthService.create_admin_user(
    db=db,
    username='doctor_test',
    password='test123',
    email='doctor@test.com',
    role='doctor',
    doctor_attributes={'title': '主治医师', 'specialty': '皮肤科'}
)
print(f'医生账号创建成功: {doctor.username}')
"
```

**Step 2: 启动服务**

```bash
# 后端
cd backend
python -m uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
```

**Step 3: 测试流程**

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| 医生登录 | 使用 doctor_test/test123 登录 | 成功进入，菜单显示"我的患者" |
| 患者列表 | 查看患者列表 | 显示有咨询记录的患者 |
| 患者搜索 | 输入姓名/手机号搜索 | 过滤结果正确 |
| 患者详情 | 点击患者进入详情 | 显示患者信息和三个Tab |
| 对话记录 | 查看对话记录 | 显示历史对话 |
| 创建医嘱 | 创建新医嘱 | 医嘱创建成功 |
| 任务情况 | 查看任务执行情况 | 显示任务列表和统计 |

**Step 4: Commit**

```bash
git commit -m "test(e2e): complete doctor workstation testing"
```

---

## 完成检查清单

- [ ] Phase 1: 后端基础扩展完成
- [ ] Phase 2: 后端 API 开发完成
- [ ] Phase 3: 前端基础完成
- [ ] Phase 4: 前端页面开发完成
- [ ] Phase 5: 测试验证通过

---

## 参考文件

| 类型 | 文件 |
|------|------|
| 设计文档 | `docs/plans/2026-02-07-doctor-workstation-design-v2.md` |
| 评估报告 | `docs/plans/2026-02-07-doctor-workstation-evaluation.md` |
| 后端模型 | `backend/app/models/admin_user.py` |
| 后端路由 | `backend/app/routes/admin_auth.py` |
| 前端布局 | `frontend/src/layouts/MainLayout.tsx` |
