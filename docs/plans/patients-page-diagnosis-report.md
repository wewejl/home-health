# /patients 页面诊断报告

**诊断日期**: 2026-02-10
**诊断目标**: http://localhost:8150/patients 页面无法展示内容

---

## 问题描述

用户访问 http://localhost:8150/patients 时：
- 页面显示空白
- 控制台报错：`No routes matched location "/patients"`
- 页面只有导航栏，主内容区为空

---

## 根本原因

### 用户角色与路由配置不匹配

**文件**: `frontend/src/App.tsx`

#### 问题代码 (第 41-46 行)

```typescript
const testUser: AdminUser = {
  id: 1,
  username: "test_admin",
  role: "admin",  // <-- 当前是 admin 角色
  is_active: true
};
```

#### 路由配置 (第 104-130 行)

```typescript
{user?.role === 'doctor' ? (
  <>
    {/* 医生路由 */}
    <Route index element={<Navigate to="/patients" replace />} />
    <Route path="patients" element={<PatientList />} />
    <Route path="patients/:patientId" element={<PatientDetail />} />
  </>
) : (
  <>
    {/* 管理员路由 - 没有 /patients */}
    <Route index element={<Dashboard />} />
    <Route path="departments" element={<Departments />} />
    // ... 其他管理员路由
  </>
)}
```

### 结论

- 测试用户角色设置为 `"admin"`
- `/patients` 路由只在 `role === 'doctor'` 时定义
- 因此 `admin` 角色访问 `/patients` 时，React Router 找不到匹配的路由

---

## 修复方案

### 方案一：修改测试用户角色（推荐 - 用于测试医生工作台）

修改 `frontend/src/App.tsx` 第 44 行：

```typescript
// 修改前
role: "admin",

// 修改后
role: "doctor",
```

### 方案二：添加管理员可访问 /patients（如果需求需要）

如果管理员也需要访问患者列表，需要修改路由配置：

```typescript
{user?.role === 'doctor' ? (
  <>
    <Route index element={<Navigate to="/patients" replace />} />
    <Route path="patients" element={<PatientList />} />
    <Route path="patients/:patientId" element={<PatientDetail />} />
  </>
) : user?.role === 'admin' ? (
  <>
    <Route index element={<Dashboard />} />
    <Route path="departments" element={<Departments />} />
    {/* 添加患者路由给管理员 */}
    <Route path="patients" element={<PatientList />} />
    <Route path="patients/:patientId" element={<PatientDetail />} />
    {/* ... 其他管理员路由 */}
  </>
) : null}
```

---

## 验证步骤

1. 修改测试用户角色为 `"doctor"`
2. 刷新页面 http://localhost:8150/patients
3. 确认患者列表正常显示
4. 确认控制台无路由错误

---

## 控制台错误截图

保存位置: `.tasks/screenshots/patients-page-issue.png`

---

## 相关文件

- `/Users/zhuxinye/Desktop/project/home-health/frontend/src/App.tsx` - 路由配置
- `/Users/zhuxinye/Desktop/project/home-health/frontend/src/pages/doctor/PatientList.tsx` - 患者列表组件

---

## 诊断完成时间

2026-02-10
