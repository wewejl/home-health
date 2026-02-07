# 医生工作台设计方案 v2.0

> 创建日期：2026-02-07
> 状态：🔄 重新设计中
> 版本：v2.0 - 基于代码评估后的修正方案

---

## 一、设计原则修正

### 1.1 核心概念澄清

| 概念 | 对应表 | 说明 |
|------|--------|------|
| **患者** | `users` | 就医的用户 |
| **医生/管理员** | `admin_users` | 系统用户，通过 `role` 区分 |
| **AI分身** | `doctors` | AI医生配置，非真实人类 |

### 1.2 设计决策变更

| 决策点 | v1方案（已废弃） | v2方案（新） |
|--------|-----------------|-------------|
| 用户系统 | 扩展 `doctors` 表 | 复用 `admin_users` + 新增 `doctor` 角色 |
| 前端架构 | 独立 `frontend/doctor/` | 在 `frontend/src/pages/doctor/` 子目录 |
| 认证系统 | 独立医生认证 | 复用现有 admin 认证 |
| 医嘱关联 | 映射到 `doctors` | 保持指向 `admin_users` ✓ |

---

## 二、整体架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        灵犀健康系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              admin_users (统一用户表)                 │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │  role = 'admin'    → 系统管理员                        │ │
│  │  role = 'doctor'   → 医生（新增）★                    │ │
│  │  role = 'editor'   → 内容编辑                          │ │
│  │  role = 'reviewer' → 审核员                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         根据 role 显示不同的前端菜单                   │ │
│  ├──────────────────┬────────────────────────────────────┤ │
│  │   管理员菜单       │          医生菜单                 │ │
│  │ - 医生管理        │  - 我的患者                       │ │
│  │ - 科室管理        │  - 患者对话记录                   │ │
│  │ - AI分身配置      │  - 下达医嘱                       │ │
│  │ - 知识库管理      │  - 任务执行情况                   │ │
│  │ - 统计分析        │                                  │ │
│  └──────────────────┴────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据关联关系

```
admin_users (id = 1, role = 'doctor', ...)
    │
    ├─→ MedicalOrder.doctor_id = 1  ← 创建的医嘱
    │
    └─→ Session.doctor_id → doctors.id (AI分身，不是真实医生)
```

**说明**:
- `admin_users` 中的 `doctor` 角色 = 真实医生，可以登录系统
- `doctors` 表 = AI 分身配置，不可登录
- 医嘱的 `doctor_id` 指向 `admin_users`，记录是哪个医生创建的

---

## 三、后端设计

### 3.1 数据模型扩展

#### 扩展 AdminUser 模型

```python
# backend/app/models/admin_user.py

class AdminRole(str, enum.Enum):
    ADMIN = "admin"          # 系统管理员
    DOCTOR = "doctor"        # 医生（新增）
    EDITOR = "editor"        # 内容编辑
    REVIEWER = "reviewer"    # 审核员

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)

    # 角色字段（已存在，扩展枚举值）
    role = Column(String(20), default="editor")

    # 新增：医生专属属性
    doctor_attributes = Column(JSON, nullable=True)  # 医生信息
    # {
    #   "title": "主治医师",
    #   "specialty": "皮肤科",
    #   "license_no": "执业医师证号",
    #   "hospital": "医院名称"
    # }

    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 数据库迁移

```sql
-- 添加医生属性字段
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS doctor_attributes JSONB;
```

### 3.2 Schemas 扩展

```python
# backend/app/schemas/admin.py

class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str = "editor"
    permissions: Optional[Any] = None
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # 新增：医生信息（当 role='doctor' 时填充）
    doctor_info: Optional["DoctorInfo"] = None

    class Config:
        from_attributes = True


class DoctorInfo(BaseModel):
    """医生专属信息"""
    title: Optional[str] = None
    specialty: Optional[str] = None
    license_no: Optional[str] = None
    hospital: Optional[str] = None


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


# 患者相关（新增）
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


# 对话记录相关（新增）
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

### 3.3 API 路由设计

#### 复用现有认证，新增医生专用路由

```python
# backend/app/routes/doctor_workstation.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.admin_user import AdminUser
from ..models.user import User
from ..models.session import Session as ConsultationSession
from ..models.message import Message
from ..models.medical_order import MedicalOrder
from ..routes.admin_auth import get_current_admin
from ..schemas.admin import PatientListItem, ConsultationSession, ConsultationDetailResponse

router = APIRouter(prefix="/api/doctor", tags=["doctor-workstation"])

def get_current_doctor(
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminUser:
    """验证当前用户是否为医生"""
    if current_admin.role != "doctor":
        raise HTTPException(status_code=403, detail="需要医生权限")
    return current_admin


# ============= 患者管理 =============

@router.get("/patients", response_model=list[PatientListItem])
def get_patients(
    search: Optional[str] = None,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取医生的患者列表（有咨询记录的患者）"""
    # 获取与该医生关联的 AI 分身咨询过的患者
    patient_ids = db.query(ConsultationSession.user_id).filter(
        ConsultationSession.doctor_id.in_(
            db.query(Doctor.id)  # 获取该医生管理的所有 AI 分身
        )
    ).distinct().all()

    # ... 查询逻辑
    pass


# ============= 对话记录 =============

@router.get("/patients/{patient_id}/consultations", response_model=list[ConsultationSession])
def get_patient_consultations(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者的对话列表"""
    pass


@router.get("/consultations/{session_id}", response_model=ConsultationDetailResponse)
def get_consultation_detail(
    session_id: str,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取对话详情"""
    pass


# ============= 医嘱管理 =============

@router.post("/orders")
def create_order(
    request: MedicalOrderCreateRequest,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """创建医嘱，doctor_id 自动设置为当前医生"""
    # 注意：request 中不需要传 patient_id，需要在前端选择患者
    pass


@router.get("/patients/{patient_id}/orders")
def get_patient_orders(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者的医嘱列表"""
    pass


# ============= 任务执行情况 =============

@router.get("/patients/{patient_id}/tasks")
def get_patient_tasks(
    patient_id: int,
    task_date: str,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者的任务执行情况"""
    pass
```

### 3.4 医生与 AI 分身的关联

需要建立医生与 AI 分身的关系：

```python
# 方案 1：在 doctors 表中添加 owner_id
# backend/app/models/doctor.py

class Doctor(Base):
    # ... 现有字段

    # 新增：所属的管理员/医生
    owner_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    owner = relationship("AdminUser", back_populates="managed_ai_doctors")


# 方案 2：在 AdminUser 中添加 managed_doctor_ids
# backend/app/models/admin_user.py

class AdminUser(Base):
    # ... 现有字段

    # 新增：管理的 AI 分身列表
    managed_doctor_ids = Column(JSON, nullable=True)  # [1, 2, 3]
```

**推荐方案 2**：更简单，不需要修改外键关系。

---

## 四、前端设计

### 4.1 目录结构

```
frontend/src/
├── pages/
│   ├── admin/           # 管理员专用页面
│   │   ├── DoctorPersonaChat.tsx
│   │   └── DoctorRecordAnalysis.tsx
│   ├── doctor/          # 医生工作台（新增）★
│   │   ├── PatientList.tsx       # 患者列表
│   │   ├── PatientDetail.tsx     # 患者详情
│   │   ├── ConsultationsTab.tsx  # 对话记录 Tab
│   │   ├── OrdersTab.tsx         # 医嘱管理 Tab
│   │   └── TasksTab.tsx          # 任务情况 Tab
│   ├── Dashboard.tsx
│   ├── Doctors.tsx       # 管理员用的医生(AI分身)管理
│   ├── Departments.tsx
│   └── ...
├── layouts/
│   └── MainLayout.tsx    # 根据 role 显示不同菜单
└── App.tsx
```

### 4.2 路由设计

```tsx
// frontend/src/App.tsx

const isDoctor = user?.role === 'doctor';

<Route path="/" element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" />}>
  {/* 共同页面 */}
  <Route index element={<Dashboard />} />

  {isDoctor ? (
    // 医生菜单
    <>
      <Route path="patients" element={<PatientList />} />
      <Route path="patients/:id" element={<PatientDetail />} />
    </>
  ) : (
    // 管理员菜单
    <>
      <Route path="departments" element={<Departments />} />
      <Route path="doctors" element={<Doctors />} />
      <Route path="diseases" element={<Diseases />} />
      <Route path="drugs" element={<Drugs />} />
      <Route path="knowledge" element={<Knowledge />} />
      <Route path="feedbacks" element={<Feedbacks />} />
      <Route path="stats" element={<Stats />} />
      <Route path="medical-orders" element={<MedicalOrders />} />
      <Route path="patient-compliance" element={<PatientCompliance />} />
      <Route path="rounding" element={<Rounding />} />
    </>
  )}
</Route>
```

### 4.3 菜单设计

```tsx
// frontend/src/layouts/MainLayout.tsx

const menuItems = user?.role === 'doctor' ? [
  {
    key: '/patients',
    icon: <UserOutlined />,
    label: '我的患者',
  },
] : [
  // ... 现有管理员菜单
];
```

---

## 五、页面设计

### 5.1 患者列表页

```
┌─────────────────────────────────────────┐
│  医生工作台              张医生  退出    │
├─────────────────────────────────────────┤
│  🔍 搜索患者姓名/手机号...              │
├─────────────────────────────────────────┤
│  姓名     性别   年龄    最近咨询    操作│
│  ─────────────────────────────────────  │
│  张三      男     65     2小时前    [查看]│
│  李四      女     42     昨天      [查看]│
│  王五      男     38     3天前     [查看]│
└─────────────────────────────────────────┘
```

### 5.2 患者详情页

```
┌─────────────────────────────────────────┐
│  ← 返回        张三 (男, 65岁)           │
├─────────────────────────────────────────┤
│  [AI对话记录] [医嘱管理] [任务执行]     │
├─────────────────────────────────────────┤
│                                         │
│   当前 Tab 内容...                       │
│                                         │
└─────────────────────────────────────────┘
```

---

## 六、实施步骤

### Phase 1: 后端基础（1-2天）

1. 扩展 `AdminUser` 模型，添加 `doctor_attributes` 字段
2. 扩展 `schemas/admin.py`，添加医生相关 schemas
3. 更新 `admin_auth.py`，支持 `doctor` 角色登录
4. 创建 `routes/doctor_workstation.py`
5. 在 `main.py` 中注册新路由

### Phase 2: 后端 API（2-3天）

6. 实现患者列表 API
7. 实现对话记录 API
8. 实现医嘱管理 API（复用现有医嘱逻辑）
9. 实现任务执行情况 API

### Phase 3: 前端基础（1天）

10. 修改 `MainLayout.tsx`，根据角色显示不同菜单
11. 修改 `App.tsx`，添加医生路由
12. 创建 `pages/doctor/` 目录和基础组件

### Phase 4: 前端页面（2-3天）

13. 实现患者列表页
14. 实现患者详情页框架
15. 实现对话记录 Tab
16. 实现医嘱管理 Tab
17. 实现任务执行情况 Tab

### Phase 5: 测试（1天）

18. 端到端测试
19. 修复 bug

---

## 七、对比 v1 方案的优势

| 方面 | v1 方案 | v2 方案 | 优势 |
|------|---------|---------|------|
| 数据模型 | 扩展 `doctors` 表 | 复用 `admin_users` | 概念清晰 |
| 前端架构 | 独立 `frontend/doctor/` | `pages/doctor/` 子目录 | 复用代码 |
| 认证系统 | 独立医生认证 | 复用 admin 认证 | 减少重复 |
| 外键关系 | 需要映射 | 保持一致 | 无技术债 |
| 实施周期 | 7-10天 | 5-7天 | 更快 |

---

## 八、风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| `admin_users` 角色变更影响现有功能 | 低 | 添加新角色，不修改现有角色 |
| 医生与管理员权限混乱 | 中 | 清晰的权限检查函数 |
| AI 分身关联逻辑复杂 | 中 | 使用 `managed_doctor_ids` 简化 |

---

## 九、待确认问题

1. 医生是否需要管理多个 AI 分身？
2. 医生是否有权限编辑 AI 分身的提示词？
3. 是否需要医生之间的患者转诊功能？
