# 医生工作台设计方案 v2.2

> 创建日期：2026-02-07
> 状态：✅ 已评估并修正，可以实施
> 版本：v2.2 - 修正代码示例和边界情况处理

---

## 📋 代码验证结论

| 验证项 | 状态 | 说明 |
|--------|------|------|
| 概念设计 | ✅ 正确 | AI分身 vs 真实医生区分正确 |
| 架构设计 | ✅ 正确 | 复用现有系统，整体合理 |
| AdminUser 模型 | ⚠️ 需扩展 | 缺少 `department_id` 字段 |
| 认证系统 | ✅ 可用 | admin_auth.py 可直接复用 |
| 前端架构 | ✅ 正确 | MainLayout 和 App.tsx 需小幅修改 |
| 医嘱 API | ⚠️ 需扩展 | 需新增医生专用端点 |

**总体评分：8.0/10** - 方案基本正确，需先完成 Phase 0 数据模型准备。

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

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base  # 注意：根据实际导入路径调整

# 角色常量（用于代码提示和验证）
class AdminRole:
    ADMIN = "admin"          # 系统管理员
    DOCTOR = "doctor"        # 医生（新增）
    EDITOR = "editor"        # 内容编辑
    REVIEWER = "reviewer"    # 审核员


class AdminUser(Base):
    __tablename__ = "admin_users"

    # ========== 现有字段保持不变 ==========
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)

    # 角色字段（已存在，扩展枚举值）
    # 可选值: admin, doctor, editor, reviewer
    role = Column(String(20), default="editor")

    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ========== 新增字段（Phase 0 实施） ==========

    # 科室关联（医生角色用于关联 AI 分身）
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="admin_users")

    # 医生专属属性
    doctor_attributes = Column(JSON, nullable=True)
    # {
    #   "title": "主治医师",
    #   "specialty": "皮肤科",
    #   "license_no": "执业医师证号",
    #   "hospital": "医院名称"
    # }
```

#### 同步修改 Department 模型

```python
# backend/app/models/department.py

class Department(Base):
    __tablename__ = "departments"

    # ... 现有字段 ...

    # 现有关系
    doctors = relationship("Doctor", back_populates="department")
    diseases = relationship("Disease", back_populates="department")

    # ========== 新增反向关系 ==========
    admin_users = relationship("AdminUser", back_populates="department")
```

#### 数据库迁移脚本

```sql
-- ========== Phase 0: AdminUser 模型扩展 ==========

-- 1. 添加 doctor_attributes 字段
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS doctor_attributes JSONB;

-- 2. 添加 department_id 字段
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS department_id INTEGER;

-- 3. 添加外键约束
ALTER TABLE admin_users ADD CONSTRAINT fk_admin_users_department
    FOREIGN KEY (department_id) REFERENCES departments(id)
    ON DELETE SET NULL ON UPDATE CASCADE;

-- 4. 创建索引（提升查询性能）
CREATE INDEX idx_admin_users_department_id ON admin_users(department_id);
CREATE INDEX idx_admin_users_role ON admin_users(role);
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
from typing import Optional

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.doctor import Doctor  # 新增：AI 分身模型
from app.models.session import Session as ConsultationSession
from app.models.message import Message
from app.models.medical_order import MedicalOrder
from app.routes.admin_auth import get_current_admin
from app.schemas.admin import PatientListItem, ConsultationSession, ConsultationDetailResponse

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
    """
    获取医生的患者列表（本科室 AI 分身咨询过的患者）
    """
    # 边界情况处理：医生未分配科室
    if not doctor.department_id:
        return []

    # 获取医生所在科室的 AI 分身列表
    ai_doctors = db.query(Doctor).filter(
        Doctor.department_id == doctor.department_id
    ).all()

    # 边界情况处理：科室无 AI 分身
    if not ai_doctors:
        return []

    ai_doctor_ids = [d.id for d in ai_doctors]

    # 获取与这些 AI 分身咨询过的患者
    patient_ids = db.query(ConsultationSession.user_id).filter(
        ConsultationSession.doctor_id.in_(ai_doctor_ids)
    ).distinct().all()

    # ... 后续查询逻辑
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

#### 关联逻辑

医生（`admin_users.role='doctor'`）通过 **科室** 关联 AI 分身（`doctors` 表）：

```
admin_users (真实医生)
    ↓ department_id
departments.id
    ↑ department_id
doctors (AI 分身)
```

#### 查询逻辑实现

```python
# backend/app/routes/doctor_workstation.py

from ..models.doctor import Doctor
from ..models.session import Session as ConsultationSession

@router.get("/patients", response_model=list[PatientListItem])
def get_patients(
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取医生的患者列表（本科室 AI 分身咨询过的患者）"""

    # 1. 获取医生所在科室的 AI 分身列表
    ai_doctors = db.query(Doctor).filter(
        Doctor.department_id == doctor.department_id  # ← Phase 0 添加的字段
    ).all()
    ai_doctor_ids = [d.id for d in ai_doctors]

    # 2. 获取这些 AI 分身接待过的患者
    patient_ids = db.query(ConsultationSession.user_id).filter(
        ConsultationSession.doctor_id.in_(ai_doctor_ids)
    ).distinct().all()

    # 3. 查询患者详细信息
    patients = db.query(User).filter(
        User.id.in_([p[0] for p in patient_ids])
    ).all()

    # 4. 组装返回数据
    return [format_patient_info(p) for p in patients]
```

#### 为什么选择科室关联？

| 方案 | 优势 | 劣势 |
|------|------|------|
| **科室关联** ✅ | 符合实际业务逻辑；利用现有字段 | 医生只能看本科室 |
| 无关联 | 简单 | 无权限隔离 |
| 直接管理表 | 灵活 | 需要新建关联表 |

**实际业务场景**：皮肤科医生查看皮肤科 AI 分身接待的患者，符合医院科室分工模式。

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

### Phase 0: 数据模型准备（🔴 必须首先完成）

**此阶段是代码验证后发现必须先执行的步骤。**

1. **扩展 AdminUser 模型** - `backend/app/models/admin_user.py`
   - 添加 `department_id` 字段（外键 → departments.id）
   - 添加 `department` 关系
   - 添加 `doctor_attributes` JSON 字段

2. **扩展 Department 模型** - `backend/app/models/department.py`
   - 添加 `admin_users` 反向关系

3. **执行数据库迁移**
   ```bash
   # 连接数据库
   psql -h localhost -U xinlingyisheng -d xinlingyisheng

   # 执行迁移脚本（见上方 SQL）
   \i migrations/phase_0_admin_user_extension.sql
   ```

4. **验证迁移**
   ```sql
   -- 验证字段已添加
   \d admin_users

   -- 验证索引已创建
   \d admin_users_department_id_idx

   -- 验证外键约束
   SELECT
       constraint_name,
       constraint_type
   FROM information_schema.table_constraints
   WHERE table_name = 'admin_users';
   ```

### Phase 1: 后端基础（1-2天）

**依赖**: Phase 0 完成

1. 扩展 `schemas/admin.py`，添加医生相关 schemas
2. 更新 `admin_auth.py`，支持 `doctor` 角色登录
3. 添加 `get_current_doctor` 依赖函数
4. 创建 `routes/doctor_workstation.py`
5. 在 `main.py` 中注册新路由

### Phase 2: 后端 API（2-3天）

**依赖**: Phase 1 完成

6. 实现患者列表 API（含科室关联逻辑）
7. 实现对话记录 API
8. 实现医嘱管理 API（复用现有医嘱逻辑）
9. 实现任务执行情况 API

### Phase 3: 前端基础（1天）

**依赖**: Phase 1 完成

10. 修改 `MainLayout.tsx`，根据角色显示不同菜单
11. 修改 `App.tsx`，添加医生路由
12. 创建 `pages/doctor/` 目录和基础组件

### Phase 4: 前端页面（2-3天）

**依赖**: Phase 2-3 完成

13. 实现患者列表页
14. 实现患者详情页框架
15. 实现对话记录 Tab
16. 实现医嘱管理 Tab
17. 实现任务执行情况 Tab

### Phase 5: 测试（1天）

**依赖**: Phase 1-4 完成

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

## 九、与现有系统的整合点

### 9.1 现有医嘱 API 需要调整

**现状**：`/medical-orders` 路由的创建医嘱接口

```python
# backend/app/routes/medical_orders.py (第 41-65 行)

@router.post("", response_model=MedicalOrderResponse, status_code=status.HTTP_201_CREATED)
def create_medical_order(
    request: MedicalOrderCreateRequest,
    current_user: User = Depends(get_current_user),  # ← 当前是患者
    db: Session = Depends(get_db)
):
    order_data["patient_id"] = current_user.id  # 暂时只允许为自己创建
```

**问题**：当前只允许患者为自己创建医嘱，医生无法为患者创建。

**调整方案**：

```python
# 选项 1：修改现有路由支持医生
@router.post("", response_model=MedicalOrderResponse)
def create_medical_order(
    request: MedicalOrderCreateRequest,
    current_user: User = Depends(get_current_user),  # 患者
    current_admin: Optional[AdminUser] = Depends(get_current_admin_optional),  # 医生
    db: Session = Depends(get_db)
):
    # 如果是医生，为指定患者创建
    if current_admin and current_admin.role == "doctor":
        patient_id = request.patient_id
    else:
        # 如果是患者，只能为自己创建
        patient_id = current_user.id

    order_data = request.model_dump()
    order_data["doctor_id"] = current_admin.id if current_admin else None
    order_data["patient_id"] = patient_id

# 选项 2：保持现有路由，新增医生专用路由
# backend/app/routes/doctor_workstation.py
@router.post("/orders")
def create_order(
    request: MedicalOrderCreateRequest,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    # 医生专用创建逻辑
    order_data = request.model_dump()
    order_data["doctor_id"] = doctor.id
    ...
```

**推荐**：选项 2，保持现有 `/medical-orders` 路由不变，新增 `/api/doctor/orders` 医生专用路由。

### 9.2 测试模式处理

现有代码使用 `TEST_MODE` 全局变量处理测试：

```python
# backend/app/dependencies.py
TEST_MODE = True

def get_current_user(...):
    if TEST_MODE:
        return test_user  # 返回测试用户
```

医生工作台需要保持一致的模式：

```python
# backend/app/routes/admin_auth.py
TEST_MODE = True  # 已存在

def get_current_admin(...):
    if TEST_MODE:
        return test_admin  # 已实现
```

### 9.3 路由前缀确认

| 路由 | 前缀 | 说明 |
|------|------|------|
| 患者医嘱 | `/medical-orders` | 现有，患者为自己创建 |
| 医生医嘱 | `/api/doctor/orders` | 新增，医生为患者创建 |
| 管理员医嘱 | `/admin/orders` | 可选，管理员管理所有 |

---

## 十、待确认问题

1. 医生是否需要管理多个 AI 分身？
2. 医生是否有权限编辑 AI 分身的提示词？
3. 是否需要医生之间的患者转诊功能？
