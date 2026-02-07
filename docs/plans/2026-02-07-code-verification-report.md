# 医生工作站 v2.0 设计方案代码验证报告

> 验证日期：2026-02-07
> 验证方法：全面代码审查
> 验证范围：后端模型、认证系统、前端架构、API 接口

---

## 一、核心发现汇总

### 1.1 数据模型验证

| 表名 | v2 方案假设 | 实际情况 | 状态 |
|------|------------|----------|------|
| `AdminUser` | 已有 `department_id` | ❌ **没有此字段** | 🔴 需添加 |
| `Doctor` | AI 分身配置 | ✅ 确认是 AI 分身 | ✅ 正确 |
| `Session.doctor_id` | → `doctors.id` | ✅ 确认 | ✅ 正确 |
| `MedicalOrder.doctor_id` | → `admin_users.id` | ✅ 确认 | ✅ 正确 |

### 1.2 认证系统验证

| 功能 | v2 方案假设 | 实际情况 | 状态 |
|------|------------|----------|------|
| admin_auth.py 存在 | ✅ | ✅ 存在 | ✅ 正确 |
| get_current_admin 可用 | ✅ | ✅ 可用 | ✅ 正确 |
| TEST_MODE 支持 | ✅ | ✅ 支持 | ✅ 正确 |
| JWT token 验证 | ✅ | ✅ 实现 | ✅ 正确 |

### 1.3 前端架构验证

| 方面 | v2 方案假设 | 实际情况 | 状态 |
|------|------------|----------|------|
| MainLayout.tsx 可扩展 | ✅ | ✅ 可扩展 | ✅ 正确 |
| 菜单可配置 | ✅ | ✅ 可配置 | ✅ 正确 |
| src/pages/ 目录存在 | ✅ | ✅ 存在 | ✅ 正确 |
| **无角色区分逻辑** | ❌ 需添加 | 当前无 | 🔴 需实现 |

### 1.4 医嘱 API 验证

| 功能 | v2 方案假设 | 实际情况 | 状态 |
|------|------------|----------|------|
| `/medical-orders` 存在 | ✅ | ✅ 存在 | ✅ 正确 |
| **只允许患者为自己创建** | ❌ 需扩展 | 当前限制 | 🔴 需修改 |
| doctor_id 字段存在 | ✅ | ✅ 存在但未使用 | ⚠️ 需启用 |

---

## 二、需要修正的设计内容

### 2.1 AdminUser 模型缺少 department_id

**v2 方案假设**：
```python
# backend/app/models/admin_user.py
department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
```

**实际情况**：
```python
# backend/app/models/admin_user.py
# ❌ 没有 department_id 字段
```

**修正方案**：需要添加此字段

### 2.2 医生与 AI 分身关联方案需要调整

**v2 方案**：通过 `department_id` 关联 AI 分身

**问题**：AdminUser 没有 department_id

**修正方案**：
- 选项 A：添加 `department_id` 到 AdminUser（推荐）
- 选项 B：使用 `managed_doctor_ids` JSON 字段
- 选项 C：先不实现关联，医生可看所有患者（MVP）

### 2.3 医嘱创建权限限制

**现状**：
```python
# backend/app/routes/medical_orders.py 第 61 行
order_data["patient_id"] = current_user.id  # 只允许为自己创建
```

**v2 方案**：医生可以为患者创建医嘱

**修正方案**：创建新的 `/api/doctor/orders` 端点

---

## 三、实施方案调整

### 修正后的 Task 1：扩展 AdminUser 模型

```python
# backend/app/models/admin_user.py

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class AdminUser(Base):
    __tablename__ = "admin_users"

    # ... 现有字段保持不变 ...

    # ========== 新增字段 ==========

    # 科室关联（医生角色用于关联 AI 分身）
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="admin_users")

    # 医生专属属性
    doctor_attributes = Column(JSON, nullable=True)
```

**同时修改 Department 模型**：

```python
# backend/app/models/department.py

class Department(Base):
    # ... 现有字段 ...

    doctors = relationship("Doctor", back_populates="department")
    diseases = relationship("Disease", back_populates="department")

    # ========== 新增反向关系 ==========
    admin_users = relationship("AdminUser", back_populates="department")
```

### 数据库迁移脚本

```sql
-- 添加 doctor_attributes
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS doctor_attributes JSONB;

-- 添加 department_id
ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS department_id INTEGER;

-- 添加外键
ALTER TABLE admin_users ADD CONSTRAINT fk_admin_users_department
    FOREIGN KEY (department_id) REFERENCES departments(id)
    ON DELETE SET NULL ON UPDATE CASCADE;

-- 创建索引
CREATE INDEX idx_admin_users_department_id ON admin_users(department_id);
```

---

## 四、前端实施调整

### 修正后的 MainLayout.tsx

```tsx
// frontend/src/layouts/MainLayout.tsx

// 根据角色配置菜单
const getMenuItems = (user: { role?: string }) => {
  if (user?.role === 'doctor') {
    // 医生菜单
    return [
      {
        key: '/patients',
        icon: <UserSwitchOutlined />,
        label: '我的患者',
      },
    ];
  }

  // 管理员菜单（保持现有）
  return [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/derma-chat', icon: <RobotOutlined />, label: '皮肤科AI对话' },
    // ... 其他菜单项
  ];
};

const MainLayout: React.FC<MainLayoutProps> = ({ user, onLogout }) => {
  const menuItems = getMenuItems(user || {});
  // ...
};
```

### 修正后的 App.tsx 路由

```tsx
// frontend/src/App.tsx

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
  {/* 管理员路由 */}
  {user?.role !== 'doctor' && (
    <>
      <Route index element={<Dashboard />} />
      <Route path="departments" element={<Departments />} />
      {/* ... 其他管理员路由 */}
    </>
  )}

  {/* 医生路由 */}
  {user?.role === 'doctor' && (
    <>
      <Route path="patients" element={<PatientList />} />
      <Route path="patients/:id" element={<PatientDetail />} />
    </>
  )}
</Route>
```

---

## 五、验证结论

### 5.1 v2.0 方案整体评估

| 方面 | 评分 | 说明 |
|------|------|------|
| 概念设计 | 9/10 | AI分身 vs 真实医生区分正确 |
| 架构设计 | 8/10 | 整体合理，但需补充细节 |
| 实施步骤 | 7/10 | 大部分正确，少数需要调整 |
| 与现有代码兼容 | 8/10 | 兼容性好，冲突少 |

**总体评分：8.0/10** ✅

### 5.2 必须修正的问题

| 优先级 | 问题 | 修正方案 |
|--------|------|----------|
| 🔴 P0 | AdminUser 缺少 department_id | 添加字段和外键 |
| 🔴 P0 | 前端无角色区分 | 添加角色判断逻辑 |
| 🟡 P1 | 医嘱创建权限限制 | 新增医生专用端点 |
| 🟡 P1 | AI 分身关联未实现 | 添加科室关联逻辑 |

### 5.3 可以直接使用的部分

| 组件 | 状态 | 说明 |
|------|------|------|
| admin_auth.py | ✅ | 可直接复用 |
| admin_auth_service.py | ✅ | 可直接复用 |
| schemas/admin.py | ✅ | 需扩展但基础存在 |
| MainLayout.tsx | ✅ | 需修改但结构完整 |
| 前端目录结构 | ✅ | 符合设计 |

---

## 六、修正后的实施计划

### Phase 0（新增）：数据模型准备

1. 添加 `AdminUser.department_id` 字段
2. 添加 `Department.admin_users` 反向关系
3. 执行数据库迁移
4. 更新相关 schemas

### Phase 1：后端基础（调整后）

- Task 1：扩展 AdminUser 模型（已修正）
- Task 2-4：保持原计划

### Phase 2：后端 API（调整后）

- Task 5：创建医生工作台路由（添加科室关联逻辑）
- Task 6-9：保持原计划

### Phase 3：前端基础（调整后）

- Task 10：修改 MainLayout.tsx 添加角色菜单（已修正）
- Task 11：修改 App.tsx 添加医生路由（已修正）
- Task 12：创建医生页面组件

### Phase 4-5：保持原计划

---

## 七、最终建议

### ✅ 批准 v2.0 方案进入实施

**条件**：先完成 Phase 0（数据模型准备），然后按修正后的计划执行。

### 下一步行动

1. **立即执行**：添加 AdminUser.department_id 字段
2. **同步更新**：修正 v2.0 设计和实施文档
3. **开始实施**：按修正后的计划执行

---

**验证完成日期**：2026-02-07
**验证结论**：✅ 方案基本正确，需要少量调整后实施
