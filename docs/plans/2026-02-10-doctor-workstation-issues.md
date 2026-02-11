# 医生工作台问题清单

**文档日期**: 2026-02-10
**文档版本**: 1.0
**整理人**: Claude (Team Lead)

---

## 问题概述

医生工作台是灵犀健康项目的核心功能模块，为医生角色提供患者管理、医嘱管理、任务跟踪等功能。经过多轮测试和代码审查，发现的问题主要分为以下几类：

1. **功能未完成** (TODO 标记的功能)
2. **用户体验问题** (设计、交互、响应式)
3. **代码质量问题** (可维护性、一致性)
4. **API 接口问题** (缺失、不规范)

本文档将所有问题按优先级 (P0/P1/P2) 进行分类，并提供详细的修复建议和预估工作量。

---

## P0 级问题（高优先级 - 阻塞或严重影响用户体验）

### P0-001: 快速咨询功能未实现

**描述**: 患者列表卡片中的"快速咨询"按钮点击后仅打印日志，未实现实际功能。

**位置**: `frontend/src/pages/doctor/PatientList.tsx:104-107`

```typescript
const handleQuickConsult = (patient: Patient) => {
  // TODO: 实现快速咨询功能
  console.log('快速咨询', patient.id);
};
```

**影响**:
- 用户无法使用快速咨询功能
- 按钮点击无反馈，体验差

**修复建议**:
1. 快速咨询应直接跳转到患者详情页的 AI 对话记录 Tab
2. 或打开一个新的对话框，发起与该患者的对话

**预估工作量**: 0.5 天

---

### P0-002: 今日新增患者数据未获取

**描述**: 统计卡片中的"今日新增"数据硬编码为 0，未从后端 API 获取。

**位置**: `frontend/src/pages/doctor/PatientList.tsx:77`

```typescript
setStats({
  total,
  active,
  new_today: 0, // TODO: 从 API 获取今日新增数据
  low_compliance: lowCompliance,
});
```

**影响**:
- 统计数据不准确
- 医生无法了解今日新增患者情况

**修复建议**:
1. 后端 API 增加今日新增患者统计接口
2. 前端调用新接口获取数据

**预估工作量**: 0.5 天 (后端) + 0.25 天 (前端)

---

### P0-003: API 调用方式不统一

**描述**: 医生工作台页面中部分使用 `doctorApi` 封装，部分直接使用 `fetch`，导致代码不一致。

**位置**:
- `frontend/src/pages/doctor/ConsultationsTab.tsx:44-45` - 直接使用 fetch
- `frontend/src/pages/doctor/OrdersTab.tsx:55` - 直接使用 fetch
- `frontend/src/pages/doctor/TasksTab.tsx:50` - 直接使用 fetch

**影响**:
- 错误处理不一致
- Token 处理可能遗漏
- 代码可维护性差

**修复建议**:
1. 将所有直接 `fetch` 调用改为使用 `doctorApi` 封装
2. 统一错误处理和 Token 管理

**预估工作量**: 1 天

---

### P0-004: 测试用户角色硬编码

**描述**: 前端测试用户角色硬编码在 `App.tsx` 中，不便于切换测试不同角色。

**位置**: `frontend/src/App.tsx:41-46`

```typescript
const testUser: AdminUser = {
  id: 1,
  username: "test_doctor",
  role: "doctor",
  is_active: true
};
```

**影响**:
- 测试不同角色需要修改代码
- 可能导致生产环境遗留测试代码

**修复建议**:
1. 使用 URL 参数或 localStorage 控制测试角色
2. 添加环境变量判断，确保生产环境不使用测试用户

**预估工作量**: 0.5 天

---

## P1 级问题（中优先级 - 影响使用体验但不阻塞）

### P1-001: 患者头像使用通用图标

**描述**: 患者详情页头像区域使用通用 `User` 图标，未使用患者姓名首字母或真实头像。

**位置**: `frontend/src/pages/doctor/PatientDetail.tsx:101-104`

```typescript
<div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mb-3">
  <User className="h-10 w-10 text-muted-foreground" />
</div>
```

**影响**:
- 视觉单调，缺乏个性化
- 用户识别度低

**修复建议**:
1. 优先显示患者真实头像 (avatar_url)
2. 无头像时显示姓名首字母
3. 使用渐变背景增强视觉效果

**预估工作量**: 0.5 天

---

### P1-002: 对话界面移动端体验不佳

**描述**: ConsultationsTab 中会话列表使用固定宽度 `md:w-80`，在小屏幕上体验不佳。

**位置**: `frontend/src/pages/doctor/ConsultationsTab.tsx:86`

```typescript
<Card className="w-full md:w-80 flex-shrink-0 overflow-hidden flex flex-col">
```

**影响**:
- 移动端布局不合理
- 小屏幕设备使用困难

**修复建议**:
1. 移动端使用上下布局替代左右布局
2. 添加会话列表折叠/展开功能

**预估工作量**: 1 天

---

### P1-003: 消息气泡设计传统

**描述**: AI 对话消息气泡使用简单的边框+背景色，缺乏现代聊天应用的圆角和阴影效果。

**位置**: `frontend/src/pages/doctor/ConsultationsTab.tsx:190-195`

```typescript
className={`p-3 rounded-lg border-l-4 ${
  message.sender === 'user'
    ? 'border-success bg-success-light/30'
    : 'border-info bg-info-light/30'
}`}
```

**影响**:
- 视觉效果平淡
- 与现代聊天应用体验差距较大

**修复建议**:
1. 使用 `rounded-2xl` 增加圆角
2. 添加渐变背景和阴影
3. 区分用户和 AI 消息样式

**预估工作量**: 0.5 天

---

### P1-004: 任务列表使用固定高度

**描述**: TasksTab 中任务列表使用固定高度 `calc(100vh-400px)`，在不同屏幕上体验不一致。

**位置**: `frontend/src/pages/doctor/TasksTab.tsx:103`

```typescript
<Card className="h-[calc(100vh-400px)] overflow-hidden flex flex-col">
```

**影响**:
- 屏幕高度不足时内容被截断
- 屏幕高度过大时留白过多

**修复建议**:
1. 使用 flex 布局自动计算高度
2. 或使用 min-height 替代固定高度

**预估工作量**: 0.25 天

---

### P1-005: 星期选择器使用 Checkbox

**描述**: OrdersTab 中医嘱调度配置的星期选择使用 Checkbox，交互体验不如按钮组。

**位置**: `frontend/src/pages/doctor/orders/ScheduleStep.tsx` (推测)

**影响**:
- 点击区域小，操作不便
- 视觉效果不直观

**修复建议**:
1. 改用圆形按钮组设计
2. 选中状态使用主色背景

**预估工作量**: 0.5 天

---

### P1-006: 管理分身按钮功能未实现

**描述**: 患者列表页面中"管理分身"按钮仅有样式，无实际功能。

**位置**: `frontend/src/pages/doctor/PatientList.tsx:171-173`

```typescript
<button className="px-4 py-2 text-primary text-sm font-medium hover:bg-primary/10 rounded-lg transition-colors">
  管理分身 →
</button>
```

**影响**:
- 医生无法管理 AI 分身
- 功能入口形同虚设

**修复建议**:
1. 跳转到分身管理页面
2. 或打开分身管理对话框

**预估工作量**: 1 天 (需配合后端 API)

---

### P1-007: 医生信息卡片职称硬编码

**描述**: 医生信息卡片中"主任医师"职称硬编码，未从后端获取。

**位置**: `frontend/src/pages/doctor/PatientList.tsx:149-150`

```typescript
<p className="text-foreground-secondary text-sm">
  {doctorInfo.department_name || '内科'} · 主任医师
</p>
```

**影响**:
- 显示信息不准确
- 不同职称医生显示错误

**修复建议**:
1. 后端 API 返回医生职称字段
2. 前端动态显示职称

**预估工作量**: 0.25 天 (后端) + 0.25 天 (前端)

---

### P1-008: 医嘱编辑功能不完整

**描述**: 医嘱编辑时只能编辑部分字段 (title, description, end_date)，无法编辑医嘱类型、调度配置等核心字段。

**位置**:
- `backend/app/routes/doctor_workstation.py:673-697` - PUT `/orders/{order_id}` 仅支持 3 个字段
- `frontend/src/pages/doctor/orders/CreateOrderDialog.tsx` - 编辑时缺少完整表单

**影响**:
- 医生无法修改医嘱的关键配置
- 必须删除后重新创建，效率低
- 历史记录丢失

**修复建议**:
1. 后端 PUT 接口支持所有可编辑字段
2. 前端编辑对话框复用创建对话框的完整表单
3. 明确哪些字段不可编辑 (如创建时间、医生 ID)

**预估工作量**: 1 天 (后端) + 1 天 (前端)

---

### P1-009: 后端 N+1 查询问题

**描述**: 获取患者列表时，为每个患者单独查询统计数据（最后咨询时间、医嘱数、完成率），存在 N+1 查询问题。

**位置**: `backend/app/routes/doctor_workstation.py:217-249`

```python
for patient in patients:
    # 每个患者单独查询
    last_session = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient.id
    ).order_by(desc(ConsultationSession.updated_at)).first()

    active_orders = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient.id,
        MedicalOrder.status == OrderStatus.ACTIVE
    ).count()

    week_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient.id,
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()
```

**影响**:
- 患者数量多时接口响应慢
- 数据库压力大
- 用户体验差

**修复建议**:
1. 使用 JOIN 一次查询获取所有数据
2. 或使用子查询聚合统计数据
3. 考虑添加 Redis 缓存统计数据

**预估工作量**: 1 天

---

### P1-010: 缺少分页支持

**描述**: 患者列表、对话记录、任务列表均未实现分页，数据量大时性能问题严重。

**位置**:
- `GET /api/doctor/patients` - 无 limit/offset 参数
- `GET /api/doctor/patients/{patient_id}/consultations` - 仅 limit，无 offset
- `GET /api/doctor/patients/{patient_id}/orders` - 无分页

**影响**:
- 数据量大时页面加载慢
- 内存占用高
- 浏览器渲染卡顿

**修复建议**:
1. 所有列表接口添加 page/page_size 或 limit/offset 参数
2. 返回总数用于分页控件
3. 前端添加分页组件

**预估工作量**: 1 天 (后端) + 1 天 (前端)

---

## P2 级问题（低优先级 - 优化改进）

### P2-001: 页面无入场动画

**描述**: 医生工作台各页面切换时无入场动画，用户体验平淡。

**位置**: 所有页面组件

**影响**:
- 页面切换生硬
- 缺乏流畅感

**修复建议**:
1. 引入 Framer Motion 或 CSS 动画
2. 添加 fade-in + slide-up 入场效果

**预估工作量**: 1 天

---

### P2-002: 搜索栏无玻璃态效果

**描述**: 患者列表搜索栏使用普通背景，无现代应用的玻璃态效果。

**位置**: `frontend/src/pages/doctor/PatientList.tsx:122-128`

**影响**:
- 视觉效果一般
- 与现代设计趋势不符

**修复建议**:
1. 添加 backdrop-blur 效果
2. 使用半透明背景

**预估工作量**: 0.25 天

---

### P2-003: 统计卡片背景单一

**描述**: 各页面统计卡片使用统一背景色，未使用渐变区分不同类型数据。

**位置**: PatientList.tsx, PatientDetail.tsx, TasksTab.tsx

**影响**:
- 视觉区分度低
- 色彩运用保守

**修复建议**:
1. 为不同类型统计卡片使用不同渐变背景
2. 统一视觉风格

**预估工作量**: 0.5 天

---

### P2-004: 悬停效果简单

**描述**: 各组件悬停效果仅使用简单的背景色变化或阴影变化。

**位置**: 所有交互组件

**影响**:
- 交互反馈弱
- 缺乏精致感

**修复建议**:
1. 增加悬停时的 transform 效果
2. 添加更丰富的过渡动画

**预估工作量**: 0.5 天

---

### P2-005: 字体层级不够丰富

**描述**: 页面字体层级仅使用 text-xl, text-lg, text-sm，层级不够丰富。

**位置**: 所有页面

**影响**:
- 视觉层次弱
- 重点不突出

**修复建议**:
1. 增加更多字体大小层级
2. 使用字重区分重要性

**预估工作量**: 0.5 天

---

### P2-006: 空状态提示可优化

**描述**: 部分空状态提示较为简单，可添加插画或更友好的提示。

**位置**: 各页面空状态

**影响**:
- 空状态体验一般
- 缺乏情感化设计

**修复建议**:
1. 添加空状态插画
2. 优化提示文案

**预估工作量**: 0.5 天

---

### P2-007: 加载状态可优化

**描述**: 骨架屏已添加，但可进一步优化动画效果和布局。

**位置**: 各页面加载状态

**影响**:
- 加载体验一般
- 可进一步提升

**修复建议**:
1. 优化骨架屏动画
2. 调整骨架屏布局更接近真实内容

**预估工作量**: 0.5 天

---

## API 接口问题

### API-001: 今日新增患者统计接口缺失

**接口需求**: `GET /api/doctor/patients/stats`

**返回数据**:
```json
{
  "total": 156,
  "active": 89,
  "new_today": 3,
  "low_compliance": 12
}
```

**优先级**: P0

**预估工作量**: 0.5 天

---

### API-002: 医生职称字段缺失

**接口**: `GET /api/doctor/me`

**当前响应**: 缺少职称字段

**需要添加**:
```json
{
  "id": 1,
  "username": "test_doctor",
  "title": "主任医师",  // 新增
  ...
}
```

**优先级**: P1

**预估工作量**: 0.25 天

---

### API-003: 分身管理接口

**接口需求**:
- `GET /api/doctor/managed-doctors` - 获取管理的 AI 分身列表
- `PUT /api/doctor/managed-doctors` - 更新管理的 AI 分身

**优先级**: P1

**预估工作量**: 1 天

---

## 代码质量问题

### CODE-001: 工具函数在组件内定义

**问题**: `getDoctorInitial`, `getAiDoctorInitial`, `getAgentTypeLabel` 等工具函数在组件内定义。

**位置**:
- `PatientList.tsx:87-93`
- `ConsultationsTab.tsx:68-80`
- `TasksTab.tsx:60-94`

**影响**:
- 每次组件重新渲染时重新创建函数
- 无法复用

**修复建议**: 提取到 `utils/` 目录

**预估工作量**: 0.5 天

---

### CODE-002: 类型定义重复

**问题**: Patient, ConsultationSession 等类型在多个文件中重复定义。

**影响**:
- 维护成本高
- 类型不一致风险

**修复建议**: 统一提取到 `types/` 目录

**预估工作量**: 0.5 天

---

## 测试相关问题

### TEST-001: 测试数据不足

**问题**: 测试环境中患者数据较少，部分场景无法充分测试。

**影响**:
- 边界情况测试不足
- 分页等功能无法验证

**修复建议**: 添加更多测试数据

**预估工作量**: 0.25 天

---

### TEST-002: 测试用户切换不便

**问题**: 测试不同角色用户需要修改代码。

**影响**:
- 测试效率低
- 可能导致代码提交错误

**修复建议**: 参见 P0-004

**预估工作量**: 0.5 天

---

## 问题汇总表

| 问题ID | 标题 | 优先级 | 类别 | 预估工作量 | 状态 |
|--------|------|--------|------|-----------|------|
| P0-001 | 快速咨询功能未实现 | P0 | 功能 | 0.5天 | 待修复 |
| P0-002 | 今日新增数据未获取 | P0 | 功能 | 0.75天 | 待修复 |
| P0-003 | API 调用方式不统一 | P0 | 代码 | 1天 | 待修复 |
| P0-004 | 测试用户角色硬编码 | P0 | 测试 | 0.5天 | 待修复 |
| P1-001 | 患者头像使用通用图标 | P1 | 体验 | 0.5天 | 待修复 |
| P1-002 | 对话界面移动端体验不佳 | P1 | 体验 | 1天 | 待修复 |
| P1-003 | 消息气泡设计传统 | P1 | 体验 | 0.5天 | 待修复 |
| P1-004 | 任务列表固定高度 | P1 | 体验 | 0.25天 | 待修复 |
| P1-005 | 星期选择器体验差 | P1 | 体验 | 0.5天 | 待修复 |
| P1-006 | 管理分身按钮未实现 | P1 | 功能 | 1天 | 待修复 |
| P1-007 | 医生职称硬编码 | P1 | 数据 | 0.5天 | 待修复 |
| P1-008 | 医嘱编辑功能不完整 | P1 | 功能 | 2天 | 待修复 |
| P1-009 | 后端 N+1 查询问题 | P1 | 性能 | 1天 | 待修复 |
| P1-010 | 缺少分页支持 | P1 | 性能 | 2天 | 待修复 |
| P2-001 | 页面无入场动画 | P2 | 体验 | 1天 | 待修复 |
| P2-002 | 搜索栏无玻璃态 | P2 | 体验 | 0.25天 | 待修复 |
| P2-003 | 统计卡片背景单一 | P2 | 体验 | 0.5天 | 待修复 |
| P2-004 | 悬停效果简单 | P2 | 体验 | 0.5天 | 待修复 |
| P2-005 | 字体层级不够丰富 | P2 | 设计 | 0.5天 | 待修复 |
| P2-006 | 空状态提示可优化 | P2 | 体验 | 0.5天 | 待修复 |
| P2-007 | 加载状态可优化 | P2 | 体验 | 0.5天 | 待修复 |
| API-001 | 今日新增统计接口 | P0 | API | 0.5天 | 待开发 |
| API-002 | 医生职称字段 | P1 | API | 0.25天 | 待开发 |
| API-003 | 分身管理接口 | P1 | API | 1天 | 待开发 |
| CODE-001 | 工具函数提取 | P2 | 代码 | 0.5天 | 待修复 |
| CODE-002 | 类型定义统一 | P2 | 代码 | 0.5天 | 待修复 |
| TEST-001 | 测试数据不足 | P2 | 测试 | 0.25天 | 待处理 |
| TEST-002 | 测试用户切换 | P0 | 测试 | 0.5天 | 待修复 |

---

## 总预估工作量

| 优先级 | 工作量 |
|--------|--------|
| P0 | 3.5 天 |
| P1 | 10.25 天 (新增 5 天) |
| P2 | 5 天 |
| **总计** | **18.75 天** |

---

## 修复建议顺序

### 第一周 (P0 问题)
1. P0-004: 测试用户角色硬编码 - 0.5天
2. P0-003: API 调用方式统一 - 1天
3. P0-002: 今日新增数据 - 0.75天
4. P0-001: 快速咨询功能 - 0.5天
5. API-001: 今日新增统计接口 - 0.5天

### 第二周 (P1 性能问题)
1. P1-009: 后端 N+1 查询优化 - 1天
2. P1-010: 添加分页支持 - 2天
3. API-002, API-003: 接口开发 - 1.25天

### 第三周 (P1 体验问题)
1. P1-008: 医嘱编辑功能完善 - 2天
2. P1-006: 管理分身按钮 - 1天
3. P1-002: 对话界面移动端 - 1天
4. P1-001, P1-003, P1-005, P1-007: 其他 P1 问题 - 1.25天

### 第四周 (P2 问题)
根据优先级和实际需求灵活安排。

---

## 相关文档

- `docs/plans/doctor-workstation-code-review.md` - 代码审核报告
- `docs/plans/doctor-workstation-refactor-e2e-report.md` - 端到端测试报告
- `docs/plans/patients-page-diagnosis-report.md` - 患者页面诊断报告
- `docs/plans/patients-page-fix-verification-report.md` - 修复验证报告
- `docs/plans/patient-list-redesign-verification.md` - 患者列表重构验证

---

## 附录：文件清单

### 前端文件
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/pages/doctor/PatientList.tsx` - 患者列表
- `frontend/src/pages/doctor/PatientDetail.tsx` - 患者详情
- `frontend/src/pages/doctor/ConsultationsTab.tsx` - AI对话记录
- `frontend/src/pages/doctor/OrdersTab.tsx` - 医嘱管理
- `frontend/src/pages/doctor/TasksTab.tsx` - 任务完成情况

### 后端文件
- `backend/app/routes/doctor_workstation.py` - 医生工作台 API

### 组件文件
- `frontend/src/components/patient/` - 患者相关组件
- `frontend/src/components/medical/loading-skeleton.tsx` - 骨架屏组件
- `frontend/src/pages/doctor/orders/` - 医嘱相关子组件

---

**文档结束**
