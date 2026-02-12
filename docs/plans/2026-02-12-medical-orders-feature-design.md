# 医嘱创建功能设计文档

> **创建日期**: 2026-02-12
> **状态**: ✅ 已完成 (Phase 1 + E2E 测试)
> **优先级**: P0 (高)

---

## 1. 功能概述

### 1.1 业务背景

医生需要为患者创建医嘱，包括：
- **处方**：开具药品处方
- **用药指导**：用药频率、用量、注意事项
- **检查项目**：需要进行的检查（验血、X光等）
- **医嘱说明**：给患者的综合建议

### 1.2 用户角色

| 角色 | 操作权限 |
|------|----------|
| **医生** | 创建、编辑、删除自己的医嘱 |
| **患者** | 查看自己的医嘱 |
| **管理员** | 查看所有医嘱（仅统计） |

---

## 2. 现有状态分析

### 2.1 后端现状

**文件**: `backend/app/routes/medical_orders.py`

**现有功能**:
- ✅ 基础 CRUD API 已存在
- ✅ 与患者关联已实现
- ✅ 与医生关联已实现

**需要补充**:
- ❌ 多步骤医嘱创建流程
- ❌ 药品库关联
- ❌ 检查项目关联
- ❌ 医嘱模板功能

### 2.2 前端现状

**文件**: `frontend/src/pages/doctor/orders/`

**现有组件**:
- ✅ `CreateOrderDialog.tsx` - 医嘱创建对话框
- ✅ `OrdersTab.tsx` - 医嘱列表
- ✅ 医嘱列表展示

**需要优化**:
- ❌ 多步骤创建流程（基础信息 → 药品 → 检查 → 确认）
- ❌ 药品搜索和选择
- ❌ 检查项目选择

---

## 3. 功能需求

### 3.1 核心功能

#### F1. 多步骤医嘱创建

```
步骤1: 基础信息
├── 患者选择
├── 医嘱类型（处方/检查/综合）
├── 开始日期
└── 预计结束日期

步骤2: 药品信息（如选择处方）
├── 药品搜索
├── 药品选择（支持多药）
├── 用法用量
├── 用药频率
└── 用药时长

步骤3: 检查项目（如需要）
├── 检查类型选择
├── 检查项目备注
└── 检查机构（可选）

步骤4: 确认和提交
├── 医嘱预览
├── 备注说明
└── 提交保存
```

#### F2. 医嘱模板

- 常用处方模板（高血压、糖尿病等）
- 快速复制历史医嘱

#### F3. 医嘱复制

- 从历史医嘱快速复制
- 批量创建相似医嘱

### 3.2 API 需求

| 端点 | 方法 | 描述 |
|--------|------|------|
| `/api/doctor/orders` | POST | 创建医嘱 |
| `/api/doctor/orders/{id}` | GET | 获取医嘱详情 |
| `/api/doctor/orders/{id}` | PUT | 更新医嘱 |
| `/api/doctor/orders/{id}` | DELETE | 删除医嘱 |
| `/api/doctor/orders` | GET | 获取医嘱列表 |
| `/api/doctor/orders/templates` | GET | 获取医嘱模板 |
| `/api/doctor/orders/{id}/copy` | POST | 复制医嘱 |
| `/api/doctor/drugs/search` | GET | 搜索药品 |

### 3.3 数据模型

```python
# MedicalOrder (医嘱主表)
class MedicalOrder(Base):
    id: UUID (PK)
    patient_id: UUID (FK → users.id)
    doctor_id: UUID (FK → doctors.id)
    order_type: Enum  # prescription, examination, comprehensive
    title: String
    description: Text (可选)
    start_date: DateTime
    end_date: DateTime (可选)
    status: Enum  # draft, active, completed, cancelled
    created_at: DateTime
    updated_at: DateTime

# OrderItem (医嘱项目 - 药品/检查)
class OrderItem(Base):
    id: UUID (PK)
    order_id: UUID (FK → medical_orders.id)
    item_type: Enum  # drug, examination
    drug_id: UUID (FK → drugs.id, 可选)
    name: String  # 药品/检查名称
    dosage: String  # 用法用量
    frequency: String  # 用药频率
    duration: String  # 用药时长
    notes: Text  # 备注
    sort_order: Integer  # 排序
```

---

## 4. 技术设计

### 4.1 后端实现

#### 4.1.1 API 路由

```python
# backend/app/routes/medical_orders.py

@router.post("/orders", response_model=MedicalOrderResponse)
async def create_order(
    order: MedicalOrderCreate,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """创建医嘱"""
    # 1. 验证患者分配
    # 2. 创建医嘱主记录
    # 3. 创建医嘱项目（药品/检查）
    # 4. 返回完整医嘱数据
    pass

@router.get("/orders/{order_id}", response_model=MedicalOrderDetail)
async def get_order(order_id: UUID, ...):
    """获取医嘱详情（包含项目）"""
    pass

@router.put("/orders/{order_id}")
async def update_order(order_id: UUID, ...):
    """更新医嘱"""
    pass
```

#### 4.1.2 服务层

```python
# backend/app/services/order_service.py

class OrderService:
    @staticmethod
    def create_order(db: Session, doctor_id: UUID, order_data: dict) -> MedicalOrder:
        """创建医嘱业务逻辑"""
        # 1. 验证患者分配
        patient = get_patient_relationship(db, doctor_id, order_data['patient_id'])
        if not patient:
            raise HTTPException(403, "未分配该患者")

        # 2. 创建医嘱
        order = MedicalOrder(**order_data)
        db.add(order)
        db.flush()

        # 3. 创建项目
        for item in order_data.get('items', []):
            order_item = OrderItem(
                order_id=order.id,
                **item
            )
            db.add(order_item)

        db.commit()
        return order
```

### 4.2 前端实现

#### 4.2.1 页面结构

```
frontend/src/pages/doctor/orders/
├── CreateOrderWizard.tsx      # 多步骤创建向导
│   ├── Step1_BasicInfo.tsx
│   ├── Step2_Medications.tsx
│   ├── Step2_Examinations.tsx
│   └── Step4_Confirm.tsx
├── OrderTemplates.tsx           # 医嘱模板选择
├── OrderDetail.tsx              # 医嘱详情页
└── OrdersList.tsx              # 医嘱列表（已存在）
```

#### 4.2.2 状态管理

```typescript
// frontend/src/store/orderStore.ts

interface OrderState {
  currentOrder: MedicalOrder | null;
  orderItems: OrderItem[];
  templates: OrderTemplate[];
  selectedTemplate: string | null;
}

export const useOrderStore = create<OrderState>((set) => ({
  currentOrder: null,
  orderItems: [],
  templates: [],
  selectedTemplate: null,
  // actions...
}));
```

### 4.3 组件设计

```typescript
// CreateOrderWizard.tsx - 核心创建组件

function CreateOrderWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [orderData, setOrderData] = useState({
    patient_id: '',
    order_type: 'prescription',
    title: '',
    items: []
  });

  const steps = [
    { id: 1, title: '基础信息', component: Step1_BasicInfo },
    { id: 2, title: '用药信息', component: Step2_Medications },
    { id: 3, title: '检查项目', component: Step2_Examinations },
    { id: 4, title: '确认提交', component: Step4_Confirm }
  ];

  return (
    <Dialog>
      <Stepper activeStep={currentStep} steps={steps} />
      <form onSubmit={handleSubmit}>
        {currentStep === 1 && <Step1_BasicInfo />}
        {currentStep === 2 && <Step2_Medications />}
        {currentStep === 3 && <Step2_Examinations />}
        {currentStep === 4 && <Step4_Confirm />}
      </form>
    </Dialog>
  );
}
```

---

## 5. UI 设计

### 5.1 创建流程界面

```
┌─────────────────────────────────────────────────────────┐
│  创建医嘱                              [X]            │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  步骤：  ━━━━━●━━━━━━━━━━━━━━━━  ━           │
│                                                 │
│  ┌───────────────────────────────────────┐         │
│  │ 步骤 1: 基础信息         [下一步] │         │
│  ├─────────────────────────────────────┤         │
│  │ 患者 *: [选择患者 ▼]              │         │
│  │ 医嘱类型: ○ 处方 ○ 检查 ● 综合  │         │
│  │ 标题: [_________________________]    │         │
│  │ 开始日期: [2024-02-12]              │         │
│  │ 结束日期: [________________] (可选)     │         │
│  └─────────────────────────────────────┘         │
│                                                 │
│  [上一步]           [取消]                    │         │
└─────────────────────────────────────────────────┘
```

### 5.2 用药步骤界面

```
┌─────────────────────────────────────────────────────────┐
│  步骤 2: 用药信息                        [上一步] │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  药品列表:                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ [+ 添加药品]    [搜索药品...]        │   │
│  ├─────────────────────────────────────────────┤   │
│  │ │ 药品名称     │ 用法    │ 频率   │   │
│  │ │ 阿司匹林    │ 1片     │ 3次/日 │   │
│  │ │ 阿莫西林    │ 2片     │ 2次/日 │  │  │
│  │ │ [删除]       │         │         │   │
│  │ │ 阿莫西林    │ 1片     │ 1次    │   │
│  │ │ [删除]       │         │         │   │
│  └─────────────────────────────────────────────┘   │
│  │                                    [继续添加]   │
│  └─────────────────────────────────────────────────┘   │
│                                                 │
│  备注:                                          │
│  [_________________________________________]    │
│                                                 │
│  [上一步]           [取消]                    │
└─────────────────────────────────────────────────┘
```

---

## 6. 权限和安全

### 6.1 权限控制

| 操作 | 医生 | 患者 | 管理员 |
|------|------|------|----------|
| 创建医嘱 | ✅ | ❌ | ❌ |
| 查看医嘱 | ✅ 自己的 | ❌ | ✅ |
| 编辑医嘱 | ✅ 自己的 | ❌ | ❌ |
| 删除医嘱 | ✅ 自己的 | ❌ | ❌ |

### 6.2 数据验证

```python
# 医嘱数据验证
def validate_order_data(order_data: dict) -> list[str]:
    errors = []

    # 患者验证
    if not order_data.get('patient_id'):
        errors.append('必须选择患者')

    # 药品验证
    if order_data.get('order_type') == 'prescription':
        if not order_data.get('items'):
            errors.append('处方必须包含药品')

    # 日期验证
    start_date = order_data.get('start_date')
    end_date = order_data.get('end_date')
    if end_date and start_date > end_date:
        errors.append('结束日期不能早于开始日期')

    return errors
```

---

## 7. 测试计划

### 7.1 单元测试

```python
# backend/test/test_medical_orders_api.py

class TestCreateOrderAPI:
    def test_create_order_success(self): ...
    def test_create_order_unassigned_patient(self): ...
    def test_create_order_empty_items(self): ...

class TestOrderTemplates:
    def test_get_templates_success(self): ...
    def test_apply_template_success(self): ...
```

### 7.2 集成测试

1. 创建患者 → 创建医嘱 → 验证医嘱在患者列表显示
2. 编辑医嘱 → 更新患者列表 → 验证变更正确
3. 删除医嘱 → 验证患者列表不再显示

---

## 8. 实施计划

### Phase 1: 后端 API (2h)
- [x] 扩展 `medical_orders.py` API
- [x] 添加医嘱模板接口
- [x] 添加药品搜索接口
- [x] 编写 API 测试

### Phase 2: 前端组件 (4h)
- [x] 创建 `CreateOrderWizard.tsx` 多步骤组件 (复用现有 CreateOrderDialog)
- [x] 创建 `Step1_BasicInfo.tsx` 基础信息组件 (已存在)
- [x] 创建 `Step2_Medications.tsx` 用药组件 (新增 MedicationsStep.tsx)
- [x] 创建 `Step4_Confirm.tsx` 确认组件 (已存在)
- [x] 创建 `OrderTemplates.tsx` 模板选择组件

### Phase 3: 联调测试 (2h)
- [x] 端到端测试创建流程 (容器内测试通过)
- [x] 验证数据正确保存
- [ ] 测试权限控制 (需要前端配合)

---

## 9. 验收标准

- [x] 医生可以通过多步骤流程创建医嘱 (复用现有 CreateOrderDialog)
- [ ] 患者可以在移动端查看医嘱 (需移动端验证)
- [x] 医嘱支持药品和检查项目 (已添加 MedicationsStep)
- [x] 支持医嘱模板快速创建 (已添加 OrderTemplates)
- [ ] 所有 API 有对应测试覆盖
- [ ] 前端组件通过 ESLint 检查
- [x] 功能文档完整更新

---

## 10. 风险和依赖

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 患者未分配 | API 403 错误 | 前端显示分配患者入口 |
| 药品数据缺失 | 无法选择药品 | 提供默认药品库 |
| 多步骤状态丢失 | 用户体验差 | 状态持久化到 localStorage |
| 并发编辑 | 数据冲突 | 乐观锁机制 |

---

*文档版本*: v1.0
*最后更新*: 2026-02-12
