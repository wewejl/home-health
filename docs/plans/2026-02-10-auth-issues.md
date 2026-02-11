# 登录和权限问题分析文档

**创建时间**: 2026-02-10
**状态**: 分析完成

---

## 概述

本文档详细分析了前端登录和权限控制系统中存在的问题，重点关注角色硬编码、登录流程和路由权限控制三个方面。

---

## 一、角色硬编码问题

### 1.1 问题描述

在 `frontend/src/App.tsx:44` 中，存在测试模式下角色硬编码的问题：

```typescript
// 第 39-46 行
// 测试模式：使用虚拟用户
// 修改 role 为 'doctor' 测试医生工作台，'admin' 测试管理员页面
const testUser: AdminUser = {
  id: 1,
  username: "test_doctor",
  role: "doctor",  // 硬编码为 'doctor'
  is_active: true
};
```

### 1.2 影响

| 影响范围 | 描述 |
|---------|------|
| 开发效率 | 每次需要测试不同角色时，必须手动修改代码并重新构建 |
| 测试覆盖 | 无法同时测试多角色场景 |
| 生产风险 | 测试代码可能意外部署到生产环境 |

### 1.3 后端对应问题

在 `backend/app/routes/admin_auth.py:17` 中也定义了测试模式：

```python
# 测试模式：禁用所有认证检查
TEST_MODE = True
```

这导致：
- 所有 API 请求不再验证 Token
- 无法区分真实用户和测试用户
- 生产环境安全风险

---

## 二、登录流程分析

### 2.1 当前登录流程

```
┌─────────────────────────────────────────────────────────┐
│                    前端登录流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 用户访问 /login                                     │
│     ↓                                                  │
│  2. 输入用户名和密码                                    │
│     ↓                                                  │
│  3. 调用 authApi.login(username, password)             │
│     ↓                                                  │
│  4. 后端验证并返回 access_token + admin 对象            │
│     ↓                                                  │
│  5. 调用 onLogin(token, admin)                         │
│     - localStorage.setItem('admin_token', token)       │
│     - localStorage.setItem('admin_user', JSON.stringify(admin)) │
│     - setUser(admin)                                   │
│     - setIsAuthenticated(true)                         │
│     ↓                                                  │
│  6. 跳转到首页 (/)                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 测试模式下的登录流程

在当前测试模式下，登录流程被完全绕过：

```typescript
// App.tsx 第 48-53 行
useEffect(() => {
  // 测试模式：自动设置测试用户，跳过登录
  setUser(testUser);
  setIsAuthenticated(true);
  setLoading(false);
}, []);
```

**结果**：
- 用户永远无法看到登录页面
- `isAuthenticated` 始终为 `true`
- `user` 始终为硬编码的 `testUser`

### 2.3 API 请求中的认证

在 `frontend/src/api/index.ts:13-15` 中：

```typescript
// 测试模式：移除所有认证检查
// 不再添加 Authorization header
// 不再处理 401 跳转登录
```

**问题**：
- 所有 API 请求都不带 Token
- 无法处理 401 未授权响应
- 与后端测试模式配合，完全绕过认证

---

## 三、路由权限控制

### 3.1 当前路由结构

```typescript
// App.tsx 第 83-131 行
<Route path="/login" element={...} />
<Route path="/" element={...}>
  {/* 根据用户角色渲染不同的路由 */}
  {user?.role === 'doctor' ? (
    // 医生路由
    <Route index element={<Navigate to="/patients" replace />} />
    <Route path="patients" element={<PatientList />} />
    <Route path="patients/:patientId" element={<PatientDetail />} />
  ) : (
    // 管理员路由
    <Route index element={<Dashboard />} />
    <Route path="departments" element={<Departments />} />
    // ... 更多管理员路由
  )}
</Route>
```

### 3.2 权限控制问题

| 问题 | 描述 | 风险等级 |
|------|------|---------|
| 硬编码角色判断 | `user?.role === 'doctor'` 字符串比较 | 中 |
| 无权限守卫组件 | 没有统一的权限检查组件 | 高 |
| 无路由级权限 | 没有基于路由配置的权限声明 | 中 |
| 无细粒度权限 | 只支持角色判断，不支持功能权限 | 高 |

### 3.3 后端权限控制

后端定义了权限相关的依赖函数：

```python
# admin_auth.py

def get_current_admin() -> AdminUser:
    """获取当前登录的管理员"""

def require_admin_role(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    """要求管理员权限"""

def get_current_doctor() -> AdminUser:
    """获取当前登录的医生（role 必须为 'doctor'）"""
```

但在测试模式下，这些函数都返回测试用户，不进行真实权限验证。

---

## 四、数据模型分析

### 4.1 AdminUser 模型

```python
# backend/app/models/admin_user.py

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(255))
    email = Column(String(100))
    role = Column(String(20), default="admin")  # admin/doctor
    permissions = Column(JSON, nullable=True)   # 权限 JSON
    is_active = Column(Boolean, default=True)

    # Phase 0 新增字段
    department_id = Column(Integer, ForeignKey("departments.id"))
    managed_doctor_ids = Column(JSON, default=list)
    doctor_attributes = Column(JSON, nullable=True)
```

### 4.2 角色常量

```python
class AdminRole:
    ADMIN = "admin"    # 系统管理员
    DOCTOR = "doctor"  # 医生
```

**注意**：前端未使用这些常量，直接使用字符串比较。

---

## 五、问题汇总

### 5.1 高优先级问题

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| AUTH-001 | 测试模式无法关闭 | App.tsx:35, admin_auth.py:17 | 生产环境安全风险 |
| AUTH-002 | 无权限守卫组件 | 前端全局 | 用户可越权访问 |
| AUTH-003 | Token 未使用 | api/index.ts:13-15 | 认证完全失效 |

### 5.2 中优先级问题

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| AUTH-004 | 角色硬编码字符串 | App.tsx:104 | 维护困难 |
| AUTH-005 | 无细粒度权限控制 | 全局 | 无法实现功能级权限 |
| AUTH-006 | 测试用户数据污染 | admin_auth.py:27-38 | 数据库存在测试数据 |

### 5.3 低优先级问题

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| AUTH-007 | 无权限类型定义 | 前端 | 缺少类型安全 |
| AUTH-008 | 登录页默认值 | Login.tsx:21-22 | 用户体验 |

---

## 六、建议改进方案

### 6.1 短期方案（快速修复）

1. **环境变量控制测试模式**
   ```typescript
   const TEST_MODE = import.meta.env.VITE_TEST_MODE === 'true';
   ```

2. **添加权限守卫组件**
   ```typescript
   <ProtectedRoute role="doctor">
     <PatientList />
   </ProtectedRoute>
   ```

3. **统一角色常量**
   ```typescript
   export const ROLES = {
     ADMIN: 'admin',
     DOCTOR: 'doctor',
   } as const;
   ```

### 6.2 长期方案（完整重构）

1. **基于 RBAC 的权限系统**
   - 角色-权限矩阵
   - 功能级权限控制
   - 动态路由生成

2. **统一的认证状态管理**
   - Zustand store 完整实现
   - Token 刷新机制
   - 会话超时处理

3. **后端权限增强**
   - 移除测试模式硬编码
   - 实现完整的权限验证中间件
   - 添加操作审计日志

---

## 七、相关文件清单

| 文件 | 说明 |
|------|------|
| frontend/src/App.tsx | 前端路由和权限控制入口 |
| frontend/src/pages/Login.tsx | 登录页面组件 |
| frontend/src/api/index.ts | API 请求封装 |
| backend/app/routes/admin_auth.py | 后端认证路由 |
| backend/app/models/admin_user.py | 用户数据模型 |
| backend/app/services/admin_auth_service.py | 认证服务 |

---

## 八、测试检查清单

在修复完成后，请验证以下场景：

- [ ] 测试模式关闭后，未登录用户被重定向到登录页
- [ ] 登录后，管理员只能访问管理员路由
- [ ] 登录后，医生只能访问医生工作台路由
- [ ] Token 过期后，自动跳转到登录页
- [ ] API 请求正确携带 Authorization header
- [ ] 后端正确验证 Token 并拒绝无效请求
- [ ] 刷新页面后，用户状态保持正确
