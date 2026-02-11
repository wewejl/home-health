# 功能缺失分析

**创建日期**: 2026-02-10
**状态**: 待确认
**负责人**: 待分配

---

## 概述

本文档整理了医生工作台中三大核心功能的缺失问题：
1. 添加患者功能
2. 快速咨询功能
3. 医嘱编辑功能

---

## 一、添加患者功能

### 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 前端UI | ✅ 已有按钮 | 患者列表页面有"添加患者"按钮 |
| 按钮交互 | ❌ 无效点击 | 点击后无任何响应 |
| 后端API | ✅ 已实现 | `POST /api/doctor/patients/assign` |

### 代码位置

- **前端**: `frontend/src/pages/doctor/PatientList.tsx:130-134`
- **后端**: `backend/app/routes/doctor_workstation.py:257-318`

### 前端代码分析

```tsx
// PatientList.tsx:130-134
<Button className="px-6 py-3 bg-primary hover:bg-primary-hover rounded-xl">
  <PlusCircle className="w-4 h-4 mr-2" />
  添加患者
</Button>
```

**问题**: 按钮没有 `onClick` 事件处理函数

### 后端API能力

```python
# POST /api/doctor/patients/assign
@router.post("/patients/assign", response_model=PatientAssignResponse, status_code=201)
def assign_patient(
    request: PatientAssignRequest,  # patient_id, relationship_type, notes
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """分配患者给当前医生"""
```

### 配套API

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/doctor/patients/assignable` | GET | 获取可分配患者列表 | ✅ 已实现 |
| `/api/doctor/patients/assign` | POST | 分配患者给医生 | ✅ 已实现 |
| `/api/doctor/patients/{patient_id}/unassign` | DELETE | 解除患者关联 | ✅ 已实现 |

### 缺失实现

1. **患者选择对话框**
   - 需要创建一个对话框组件
   - 支持搜索患者
   - 显示可分配患者列表
   - 显示已分配状态

2. **患者分配流程**
   - 点击"添加患者"按钮
   - 打开患者选择对话框
   - 从 `/api/doctor/patients/assignable` 获取可分配患者
   - 选择患者后调用 `/api/doctor/patients/assign`
   - 刷新患者列表

3. **新建患者入口**
   - 当前只能分配已有患者
   - 需要考虑是否需要"创建新患者"功能
   - 或引导到用户管理页面

### 设计建议

```
┌─────────────────────────────────────────┐
│           添加患者                        │
├─────────────────────────────────────────┤
│  [搜索框: 搜索患者姓名或手机号]            │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │ 张三  男 65岁  [已分配]          │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 李四  女 42岁  [+ 添加]          │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 王五  男 58岁  [+ 添加]          │   │
│  └─────────────────────────────────┘   │
│                                          │
│           [取消]  [确认]                 │
└─────────────────────────────────────────┘
```

---

## 二、快速咨询功能

### 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 前端UI | ✅ 已有按钮 | 每个患者卡片有"快速咨询"按钮 |
| 事件处理 | ⚠️ 空实现 | 有函数但只打印日志 |
| 后端API | ❌ 未实现 | 无快速咨询专用接口 |

### 代码位置

- **患者列表**: `frontend/src/pages/doctor/PatientList.tsx:104-107`
- **卡片组件**: `frontend/src/components/patient/LargePatientCard.tsx:95-100, 183-188`

### 前端代码分析

```tsx
// PatientList.tsx:104-107
const handleQuickConsult = (patient: Patient) => {
  // TODO: 实现快速咨询功能
  console.log('快速咨询', patient.id);
};
```

```tsx
// LargePatientCard.tsx:183-188
<button
  className="flex-1 py-2.5 border border-border text-foreground rounded-xl..."
  onClick={handleQuickConsult}
>
  快速咨询
</button>
```

### 功能需求分析

**快速咨询**是指医生主动向患者发起咨询，预期行为：

1. **导航到咨询页面**
   - 跳转到聊天对话界面
   - 预选患者和AI分身类型

2. **创建新会话**
   - 可能需要创建新的咨询会话
   - 或打开最近的一次会话

3. **消息通知**
   - 发送通知给患者
   - 告知医生发起了咨询

### 实现选项

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A. 导航到聊天页面 | 跳转到 `/chat?patient_id=xxx` | 实现简单 | 需要确认聊天页面路径 |
| B. 创建医生会话 | 创建医生-患者专用会话 | 医生专属记录 | 需要新数据模型 |
| C. 打开最近会话 | 查找最近会话并打开 | 保持对话连续性 | 可能无最近会话 |

### 推荐实现方案

```tsx
const handleQuickConsult = (patient: Patient) => {
  // 方案1: 导航到聊天页面
  navigate(`/chat?patient_id=${patient.id}`);

  // 方案2: 导航到患者详情并切换到咨询标签
  navigate(`/patients/${patient.id}`, { state: { tab: 'consultations' } });
};
```

### 需要确认的问题

1. **聊天页面路径**: 系统中是否有独立的聊天/咨询页面？
2. **会话创建逻辑**: 是否需要后端API创建新会话？
3. **AI分身选择**: 快速咨询时使用哪个AI分身？

---

## 三、医嘱编辑功能

### 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 前端UI | ✅ 已实现 | 有完整的编辑对话框 |
| 编辑流程 | ⚠️ 部分受限 | 编辑时只能修改部分字段 |
| 后端API | ⚠️ 功能受限 | 只允许修改 title, description, end_date |

### 代码位置

- **对话框组件**: `frontend/src/pages/doctor/orders/CreateOrderDialog.tsx`
- **更新API**: `backend/app/routes/doctor_workstation.py:673-697`

### 前端实现分析

```tsx
// CreateOrderDialog.tsx:73-93 - 编辑时准备数据
const handleEdit = (order: MedicalOrder) => {
  setEditingOrder(order);

  const basicInfo: BasicInfoData = {
    order_type: order.order_type,
    title: order.title,
    description: order.description,
  };
  const schedule: ScheduleData = {
    schedule_type: (order.schedule_type as ScheduleType) || 'once',
    start_date: order.start_date,
    end_date: order.end_date || undefined,
    reminder_times: order.reminder_times || [],
    frequency: order.frequency,
  };

  setInitialBasicInfo(basicInfo);
  setInitialSchedule(schedule);
  setInitialScheduleType((order.schedule_type as ScheduleType) || 'once');
  setModalVisible(true);
};
```

```tsx
// CreateOrderDialog.tsx:86-102 - 提交时只发送部分字段
if (editingOrder) {
  const response = await fetch(`/api/doctor/orders/${editingOrder.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      end_date: payload.end_date,
    }),
  });
}
```

### 后端API限制

```python
# doctor_workstation.py:673-697
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
    # 只允许修改这三个字段
    if title is not None:
        order.title = title
    if description is not None:
        order.description = description
    if end_date is not None:
        order.end_date = end_date
    ...
```

### 功能限制对比

| 字段 | 创建时可设置 | 编辑时可修改 | 限制原因 |
|------|-------------|-------------|----------|
| title | ✅ | ✅ | - |
| description | ✅ | ✅ | - |
| end_date | ✅ | ✅ | - |
| order_type | ✅ | ❌ | 类型不应改变 |
| schedule_type | ✅ | ❌ | 可能影响任务生成 |
| start_date | ✅ | ❌ | 开始日期不应改变 |
| reminder_times | ✅ | ❌ | 可能影响任务生成 |
| frequency | ✅ | ❌ | 可能影响任务生成 |
| weekdays | ✅ | ❌ | 可能影响任务生成 |

### 潜在问题

1. **用户体验不一致**
   - 编辑对话框显示完整表单
   - 但提交时忽略大部分字段
   - 用户可能误以为修改生效

2. **缺少输入限制**
   - 表单没有禁用不可编辑字段
   - 用户可以修改但实际不生效

3. **缺少提示**
   - 没有告知用户哪些字段可编辑
   - 应该添加说明或视觉提示

### 改进建议

**选项A: 编辑时禁用不可修改字段**

```tsx
<BasicInfoStep
  data={basicInfoData}
  onChange={setBasicInfoData}
  errors={formErrors}
  readonlyFields={['order_type']}  // 编辑时禁用
/>
```

**选项B: 简化编辑对话框**

```tsx
// 编辑时使用简化对话框，只显示可编辑字段
{editingOrder ? (
  <EditOrderDialog order={editingOrder} />
) : (
  <CreateOrderDialog />
)}
```

**选项C: 扩展后端API**

```python
# 如果需要完整编辑功能，后端需要：
# 1. 验证医嘱状态（只有draft可编辑全部字段）
# 2. 重新生成任务实例（如果调度信息变更）
# 3. 处理历史记录
```

---

## 优先级建议

| 功能 | 优先级 | 工作量 | 依赖 |
|------|--------|--------|------|
| 添加患者 | P1 | 中 | 无 |
| 快速咨询 | P2 | 小 | 需确认聊天页面路径 |
| 医嘱编辑体验优化 | P2 | 小 | 无 |

---

## 实施计划

### 阶段一：添加患者功能

1. 创建 `AssignPatientDialog` 组件
2. 实现患者搜索和选择
3. 调用分配API
4. 刷新列表

### 阶段二：快速咨询功能

1. 确认目标页面路径
2. 实现 `handleQuickConsult` 函数
3. 添加导航逻辑
4. 处理无会话情况

### 阶段三：医嘱编辑优化

1. 添加字段禁用逻辑
2. 或创建独立编辑对话框
3. 添加用户提示
4. 统一前后端能力

---

## 相关文档

- [API文档](/docs/API文档.md)
- [医生工作台设计](/docs/plans/doctor-workstation-code-review.md)
- [前端开发规范](/docs/前端开发规范.md)
