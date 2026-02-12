# 医生工作台激活 API 统一设计文档

> **创建日期**: 2026-02-12
> **状态**: 设计中
> **优先级**: P1 (中)

---

## 1. 问题分析

### 1.1 现状问题

根据 tech-debt.md 记录：

**问题**: 医生工作台激活 API 路由不一致

**现状**:
- `doctors.py`: `PUT /doctors/{id}/activate` 激活/停用医生
- `doctor_workstation.py`: 激活状态端点命名和实现不统一

### 1.2 影响范围

| 模块 | 端点 | 问题 |
|------|--------|------|
| 后端 doctors | `/admin/doctors/{id}/activate` | 仅管理员可调用 |
| 后端 workstation | `/api/doctor/me/activate` | 医生自己的激活端点 |
| 前端调用 | `doctorApi.activateDoctor()` | 可能调用错误的端点 |

---

## 2. 解决方案

### 2.1 统一规范

#### 原则

1. **管理员激活医生**: 使用 `/admin/doctors/{id}/activate`
2. **医生自我激活**: 使用 `/api/doctor/me/activate`（自己激活自己）
3. **激活状态同步**: 医生表的 `is_active` 字段作为唯一真相来源

### 2.2 API 路由规范

| 操作 | 路由 | 调用者 | 说明 |
|------|------|--------|------|
| 管理员激活医生 | `PUT /admin/doctors/{id}/activate?is_active=true` | 管理员 | 直接修改数据库 |
| 医生激活自己 | `PUT /api/doctor/me/activate` | 医生 | 验证后修改 |
| 医生激活同科室医生 | `PUT /api/doctor/activate` | 管理员 | 旧端点兼容 |
| 获取激活状态 | `GET /api/doctor/me/activate` | 医生 | 返回当前状态 |

### 2.3 数据库字段

```sql
-- doctors 表
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS last_activation_at TIMESTAMP;
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS last_deactivation_at TIMESTAMP;
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS activation_note TEXT;

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_doctors_active_status
ON doctors(is_active, last_activation_at DESC);
```

---

## 3. 后端实现

### 3.1 管理员激活端点（已存在）

```python
# backend/app/routes/admin_doctors.py

@router.put("/{doctor_id}/activate")
async def activate_doctor(
    doctor_id: int,
    is_active: bool = Query(...),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    管理员激活/停用医生

    激活时：
    - 设置 is_active = True
    - 更新 last_activation_at
    - 设置 verification_note
    - 发送通知给医生

    停用时：
    - 设置 is_active = False
    - 更新 last_deactivation_at
    - 记录停用原因
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "医生不存在")

    doctor.is_active = is_active

    if is_active:
        doctor.last_activation_at = datetime.utcnow()
        doctor.verified_by = current_admin.id
        doctor.verified_at = datetime.utcnow()
        # 清除停用记录
        doctor.last_deactivation_at = None
        doctor.deactivation_reason = None
    else:
        doctor.last_deactivation_at = datetime.utcnow()
        # 可选：记录停用原因
        # doctor.deactivation_reason = request_data.get('reason')

    db.commit()
    return {
        "id": doctor.id,
        "is_active": doctor.is_active,
        "message": f"医生已{'激活' if is_active else '停用'}"
    }
```

### 3.2 医生自我激活端点

```python
# backend/app/routes/doctor_workstation.py

from pydantic import BaseModel

class SelfActivationRequest(BaseModel):
    is_active: bool
    device_info: Optional[str] = None  # 设备信息

@router.put("/me/activate")
async def self_activate(
    request: SelfActivationRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    医生激活/停用自己

    限制条件：
    - 仅能修改自己的状态
    - 需要验证当前状态（不能重复激活）
    """
    me = current_doctor

    # 验证状态变化
    if me.is_active == request.is_active:
        raise HTTPException(400, f"当前已是{'激活' if me.is_active else '停用'}状态")

    me.is_active = request.is_active

    if request.is_active:
        me.last_activation_at = datetime.utcnow()
        if request.device_info:
            me.activation_note = f"通过设备激活: {request.device_info}"
    else:
        me.last_deactivation_at = datetime.utcnow()
        me.deactivation_reason = "自我停用"

    db.commit()
    return {
        "id": me.id,
        "is_active": me.is_active,
        "message": f"已{'激活' if request.is_active else '停用'}"
    }
```

### 3.3 获取激活状态

```python
@router.get("/me/activate")
async def get_activation_status(
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取当前激活状态
    """
    return {
        "id": current_doctor.id,
        "is_active": current_doctor.is_active,
        "last_activation_at": current_doctor.last_activation_at,
        "last_deactivation_at": current_doctor.last_deactivation_at,
        "activation_note": current_doctor.activation_note
    }
```

### 3.4 激活同科室医生（管理员功能）

```python
@router.put("/activate-by-department")
async def activate_doctors_by_department(
    department_id: int,
    is_active: bool,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    按科室批量激活/停用医生

    用于快速切换整个科室的医生状态
    """
    doctors = db.query(Doctor).filter(
        Doctor.department_id == department_id
    ).all()

    for doctor in doctors:
        doctor.is_active = is_active
        if is_active:
            doctor.last_activation_at = datetime.utcnow()
            doctor.verified_by = current_admin.id
            doctor.verified_at = datetime.utcnow()
        else:
            doctor.last_deactivation_at = datetime.utcnow()

    db.commit()

    return {
        "count": len(doctors),
        "message": f"已{'激活' if is_active else '停用'} {len(doctors)} 位医生"
    }
```

---

## 4. 前端实现

### 4.1 API 服务封装

```typescript
// frontend/src/api/doctor.ts

// 医生激活相关 API
export const doctorActivationApi = {
  // 管理员激活医生
  activateDoctor: (doctorId: number, isActive: boolean) =>
    apiRequest(`/admin/doctors/${doctorId}/activate?is_active=${isActive}`, {
      method: 'PUT'
    }),

  // 医生自我激活
  selfActivate: (isActive: boolean, deviceInfo?: string) =>
    apiRequest('/api/doctor/me/activate', {
      method: 'PUT',
      data: { is_active: isActive, device_info: deviceInfo }
    }),

  // 获取激活状态
  getActivationStatus: () =>
    apiRequest('/api/doctor/me/activate', {
      method: 'GET'
    }),

  // 批量激活科室医生
  activateByDepartment: (departmentId: number, isActive: boolean) =>
    apiRequest(`/api/doctor/activate-by-department?department_id=${departmentId}&is_active=${isActive}`, {
      method: 'PUT'
    })
};

export const doctorApi = {
  ...doctorApi,
  // ... 其他现有 API
};
```

### 4.2 状态管理

```typescript
// frontend/src/store/doctorActivationStore.ts

import { create } from 'zustand';

interface DoctorActivationState {
  activationStatus: 'idle' | 'activating' | 'success' | 'error';
  currentDoctor: Doctor | null;
  error: string | null;
}

export const useDoctorActivationStore = create<DoctorActivationState>((set) => ({
  activationStatus: 'idle',
  currentDoctor: null,
  error: null,

  activateDoctor: async (doctorId: number, isActive: boolean) => {
    set({ activationStatus: 'activating' });
    try {
      const result = await doctorApi.activateDoctor(doctorId, isActive);
      set({
        activationStatus: 'success',
        currentDoctor: result.data
      });
    } catch (error) {
      set({
        activationStatus: 'error',
        error: error.message
      });
    }
  },

  selfActivate: async (isActive: boolean) => {
    set({ activationStatus: 'activating' });
    try {
      const result = await doctorApi.selfActivate(isActive);
      set({
        activationStatus: 'success',
        currentDoctor: result.data
      });
    } catch (error) {
      set({
        activationStatus: 'error',
        error: error.message
      });
    }
  }
}));
```

### 4.3 UI 组件

```typescript
// frontend/src/components/doctor/ActivationButton.tsx

import { useDoctorActivationStore } from '@/store/doctorActivationStore';

interface ActivationButtonProps {
  doctor: Doctor;
  onActivationChange?: () => void;
}

export function ActivationButton({ doctor, onActivationChange }: ActivationButtonProps) {
  const { activationStatus, activateDoctor, selfActivate } = useDoctorActivationStore();

  const isActivating = activationStatus === 'activating';
  const isActive = doctor.is_active;

  const handleToggle = () => {
    if (isActive) {
      // 停用确认
      Modal.confirm({
        title: '确认停用',
        content: '停用后将无法接诊，确认停用？',
        onOk: () => selfActivate(false)
      });
    } else {
      // 激活
      selfActivate(true);
    }
  };

  return (
    <Tooltip title={isActive ? '点击停用' : '点击激活'}>
      <Button
        type={isActive ? 'default' : 'primary'}
        danger={isActive}
        loading={isActivating}
        onClick={handleToggle}
        icon={isActive ? <StopOutlined /> : <CheckOutlined />}
      >
        {isActive ? '已激活' : '已停用'}
      </Button>
    </Tooltip>
  );
}
```

### 4.4 激活历史组件

```typescript
// frontend/src/components/doctor/ActivationHistory.tsx

interface ActivationHistoryProps {
  doctor: Doctor;
}

export function ActivationHistory({ doctor }: ActivationHistoryProps) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // 加载激活历史（从审计日志或新增字段）
    loadActivationHistory(doctor.id).then(setHistory);
  }, [doctor.id]);

  return (
    <div className="activation-history">
      <h4>激活历史</h4>
      <Timeline>
        {history.map((record, index) => (
          <Timeline.Item key={index}>
            <span>{record.action}</span>
            <span>{record.timestamp}</span>
            {record.operator && <span>操作人: {record.operator}</span>}
            {record.note && <span>备注: {record.note}</span>}
          </Timeline.Item>
        ))}
      </Timeline>
    </div>
  );
}
```

---

## 5. UI 设计

### 5.1 管理员医生列表

```
┌─────────────────────────────────────────────────────────┐
│  医生管理                              [+ 新增医生]    │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  搜索: [____________]  科室: [全部 ▼]         │
│                                                 │
│  ┌─────────────────────────────────────────────┐   │
│  │ 姓名         科室       状态    操作  │   │
│  ├─────────────────────────────────────────────┤   │
│  │ 张三  内科   ● 活跃  [详情] │   │
│  │            ├─[切换状态]                      │   │
│  │            └─[编辑] [删除]                 │   │
│  │ 李四  外科   ○ 停用  [详情] │   │
│  │            ├─[切换状态]                      │   │
│  │            └─[编辑] [删除]                 │   │
│  │ 王五  心内科 ● 活跃  [详情] │   │
│  │            ├─[切换状态]                      │   │
│  │            └─[编辑] [删除]                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                 │
│  [显示更多 20]                                  │
└─────────────────────────────────────────────────────────┘
```

### 5.2 医生工作台激活入口

```
┌─────────────────────────────────────────────────────────┐
│  医生工作台                    [设置] [退出]    │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  当前状态: ● 在线  ○ 离线               │
│                                                 │
│  ┌─────────────────────────────────────────────┐   │
│  │                                         │   │
│  │  🟢 服务正常运行中                    │   │
│  │                                         │   │
│  │  激活时间: 2024-02-10 09:30:15     │   │
│  │                                         │   │
│  │  设备: iPhone 15 Pro                   │   │
│  │                                         │   │
│  │                                    [切换状态]   │
│  └─────────────────────────────────────────────┘   │
│                                                 │
│  最近登录记录:                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ 📅 今天 09:30  iPhone 15 Pro    │   │
│  │ 📅 昨天 14:20  iPad Pro         │   │
│  │ 📅 2月9日 08:45  Web               │   │
│  └─────────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 6. 测试计划

### 6.1 单元测试

```python
# backend/test/test_doctor_activation_api.py

class TestAdminActivateDoctor:
    def test_activate_doctor_success(self): ...
    def test_deactivate_doctor_success(self): ...
    def test_activate_nonexistent_doctor(self): ...

class TestSelfActivation:
    def test_self_activate_success(self): ...
    def test_self_activate_already_active(self): ...
    def test_self_deactivate_success(self): ...

class TestActivationHistory:
    def test_get_activation_history(self): ...
    def test_department_batch_activation(self): ...
```

### 6.2 集成测试

1. 管理员激活医生 → 验证医生状态更新
2. 医生自我激活 → 验证状态更新
3. 批量激活科室 → 验证所有相关医生状态
4. 停用医生 → 验证无法接诊

---

## 7. 实施计划

### Phase 1: 数据库更新 (1h)
- [ ] 添加 doctors 表新字段（last_activation_at 等）
- [ ] 创建数据库迁移脚本
- [ ] 添加索引

### Phase 2: 后端实现 (2h)
- [ ] 扩展 `admin_doctors.py` 激活端点
- [ ] 新增 `doctor_workstation.py` 自我激活端点
- [ ] 添加激活历史查询端点
- [ ] 编写 API 测试

### Phase 3: 前端实现 (2h)
- [ ] 创建 `doctorActivationStore` 状态管理
- [ ] 创建 `ActivationButton` 组件
- [ ] 创建 `ActivationHistory` 组件
- [ ] 更新医生列表页面
- [ ] 更新工作台激活入口

### Phase 4: 测试验证 (1h)
- [ ] 运行单元测试
- [ ] 端到端测试激活流程
- [ ] 验证状态同步正确性

---

## 8. 验收标准

- [ ] 管理员可以激活/停用医生
- [ ] 医生可以自我激活/停用
- [ ] 激活状态在医生列表正确显示
- [ ] 工作台显示当前激活状态
- [ ] 激活历史可查询
- [ ] 所有 API 有测试覆盖
- [ ] 前端组件通过 ESLint
- [ ] 功能文档更新

---

## 9. 风险和注意事项

| 风险 | 缓解措施 |
|------|----------|
| 并发激活冲突 | 数据库行级锁 |
| 状态不一致 | 以数据库为准，定时同步 |
| 恶意停用 | 添加停用原因记录和审计 |
| 通知未送达 | 使用 WebSocket 推送 |

---

*文档版本*: v1.0
*最后更新*: 2026-02-12
