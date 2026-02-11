# 前端组件使用情况审查报告

**审查日期**: 2026-02-10
**审查范围**: `frontend/src/pages/` 和 `frontend/src/components/` 目录下的所有 .tsx 文件
**审查目标**: 查找所有非 shadcn/ui 框架的自定义实现

---

## 审查结果摘要

| 问题类型 | 文件数量 | 优先级 |
|---------|---------|--------|
| @ant-design/charts 图表组件 | 3 | P0 |
| 内联组件定义（应移至 components/） | 2 | P1 |
| 自定义样式类（不符合设计系统） | 1 | P2 |

---

## P0: 必须修复

### 1. @ant-design/charts 图表库使用

**问题描述**: 3个页面使用 `@ant-design/charts` 库渲染图表，与 shadcn/ui 设计系统不一致

| 文件 | 使用组件 | 位置 |
|------|---------|------|
| `frontend/src/pages/PatientCompliance.tsx` | Line, Column, Pie | 第30行 |
| `frontend/src/pages/Stats.tsx` | Line | 第3行 |
| `frontend/src/pages/RoundingDetail.tsx` | Line | 第17行 |

**当前代码示例**:
```tsx
// PatientCompliance.tsx:30
import { Line, Column, Pie } from '@ant-design/charts';

// Stats.tsx:3
import { Line } from '@ant-design/charts';

// RoundingDetail.tsx:17
import { Line } from '@ant-design/charts';
```

**修复建议**: 替换为以下 shadcn/ui 兼容图表库之一：
- **Recharts** (推荐) - 与 React 生态系统集成良好，支持自定义主题
- **Visx** (推荐) - D3.js 的 React 封装，高度可定制
- **Tremor** - 专为 shadcn/ui 设计的图表组件

**具体方案**:
```tsx
// 使用 Recharts 替代示例
import { LineChart, Line, ColumnChart, Column, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

// 主题颜色从 @ant-design/charts 的 getThemeColors() 迁移到 Recharts
const COLORS = {
  primary: 'hsl(var(--primary))',
  success: 'hsl(var(--success))',
  warning: 'hsl(var(--warning))',
  danger: 'hsl(var(--danger))',
};

// 折线图配置
<ResponsiveContainer width="100%" height={250}>
  <LineChart data={trendLineData}>
    <XAxis dataKey="date" />
    <YAxis domain={[0, 100]} />
    <Line type="monotone" dataKey="value" stroke={COLORS.primary} strokeWidth={2} dot={{ r: 4 }} />
    <Tooltip formatter={(value) => [`${value}%`, '完成率']} />
  </LineChart>
</ResponsiveContainer>
```

**迁移步骤**:
1. 安装 Recharts: `npm install recharts`
2. 为每个图表类型创建 `components/charts/` 组件:
   - `components/charts/line-chart.tsx`
   - `components/charts/column-chart.tsx`
   - `components/charts/pie-chart.tsx`
3. 更新所有使用 @ant-design/charts 的页面
4. 删除 `@ant-design/charts` 依赖

---

## P1: 建议修复

### 2. 内联组件定义

**问题描述**: 组件在页面文件中直接定义，应移至 `components/` 目录

| 文件 | 组件名 | 位置 |
|------|--------|------|
| `frontend/src/pages/doctor/PatientList.tsx` | `LargePatientCard` | 第101-207行 |
| `frontend/src/pages/admin/DoctorRecordAnalysis.tsx` | `FeatureCard` | 第35-47行 |

**当前代码示例**:
```tsx
// PatientList.tsx:101-207
const LargePatientCard: React.FC<{
  patient: Patient;
  onClick: () => void;
}> = ({ patient, onClick }) => {
  // ...组件实现
};
```

**修复建议**:
1. 创建 `components/patient/LargePatientCard.tsx`:
```tsx
// frontend/src/components/patient/LargePatientCard.tsx
import { Patient } from '@/types';
import { CardProps } from '@/components/ui/card';

export interface LargePatientCardProps extends CardProps {
  patient: Patient;
  onClick: () => void;
}

export const LargePatientCard: React.FC<LargePatientCardProps> = ({
  patient,
  onClick,
  className
}) => {
  // ...组件实现
};
```

2. 创建 `components/medical/FeatureCard.tsx`:
```tsx
// frontend/src/components/medical/FeatureCard.tsx
export interface FeatureCardProps {
  title: string;
  content: string;
  icon: React.ReactNode;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  content,
  icon
}) => {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="text-primary">{icon}</div>
            <p className="font-medium text-sm">{title}</p>
          </div>
          <p className="text-sm text-foreground-secondary">{content}</p>
        </div>
      </CardContent>
    </Card>
  );
};
```

---

## P2: 可选优化

### 3. 自定义样式类

**问题描述**: 使用不符合 shadcn/ui 设计系统的自定义样式类

| 文件 | 问题 | 说明 |
|------|------|------|
| `frontend/src/pages/doctor/PatientList.tsx` | 硬编码 Tailwind 类 | 使用了大量自定义颜色类，如 `bg-sky-500`, `text-sky-600` 等 |

**修复建议**: 使用 shadcn/ui 的 CSS 变量系统:
```tsx
// 不推荐
className="bg-sky-500 text-white"

// 推荐
className="bg-primary text-primary-foreground"
```

---

## 已正确使用 shadcn/ui 的页面

以下页面已完全使用 shadcn/ui 组件，无需修改：

| 页面 | 使用的 shadcn/ui 组件 |
|------|----------------------|
| `Dashboard.tsx` | StatCardGrid, PageHeader, LoadingSkeleton |
| `Login.tsx` | Card, Input, Button, Label |
| `Departments.tsx` | Table, Dialog, Input, Textarea, Label, Badge, Checkbox, Button, Select |
| `Doctors.tsx` | Table, Dialog, Sheet, AlertDialog, Input, Label, Switch, Select, Tabs, Card, Button, InputNumber |
| `Diseases.tsx` | Table, Dialog, AlertDialog, Input, Select, Switch, Badge, Tabs, Label, PageHeader, LoadingSkeleton |
| `Drugs.tsx` | Table, Dialog, AlertDialog, Input, Select, Switch, Badge, Tabs, Label, PageHeader, LoadingSkeleton |
| `Knowledge.tsx` | Table, Dialog, AlertDialog, Input, Select, Badge, Tabs, Label, Card, PageHeader, LoadingSkeleton |
| `DermaChat.tsx` | Button, Card, Badge, Avatar, Textarea |
| `Feedbacks.tsx` | Table, Dialog, Input, Select, Badge, Card, Label, Textarea, Button |
| `MedicalOrders.tsx` | Card, Button, Badge, Tabs, Dialog, Input, Select, DatePicker, Tooltip, Textarea, StatCardGrid, PageHeader, Progress, Table |
| `Rounding.tsx` | Card, Input, Select, Avatar, Badge, Progress, Button |
| `DoctorPersonaChat.tsx` | Button, Card, Badge, Textarea, AlertDialog |
| `DoctorRecordAnalysis.tsx` | Button, Card, Badge, Progress |
| `PatientDetail.tsx` | Button, Card, Badge, Tabs, Separator |
| `ConsultationsTab.tsx` | Card, Badge, Separator |
| `OrdersTab.tsx` | Button, useToast, OrdersList, CreateOrderDialog, ConfirmDialog |
| `TasksTab.tsx` | Card, Badge, Input |

---

## 总结

### 必须执行的修改
1. **替换 @ant-design/charts** (3个文件) - 使用 Recharts 或 Tremor

### 建议执行的修改
1. **提取内联组件** (2个文件) - 移至 `components/` 目录

### 可选优化
1. **统一样式类** (1个文件) - 使用 CSS 变量替代硬编码颜色

### 整体评估
- **shadcn/ui 采用率**: 约 90%
- **主要问题**: 图表库依赖和少量内联组件
- **修复工作量**: 中等（约 2-3 小时）

---

## 附录：shadcn/ui 组件清单

当前项目中已有的 shadcn/ui 组件（位于 `frontend/src/components/ui/`）：

- alert.tsx
- alert-dialog.tsx
- avatar.tsx
- badge.tsx
- button.tsx
- card.tsx
- checkbox.tsx
- collapsible.tsx
- command.tsx
- date-picker.tsx
- dialog.tsx
- dropdown-menu.tsx
- form.tsx
- hover-card.tsx
- input-number.tsx
- input.tsx
- label.tsx
- navigation-menu.tsx
- popover.tsx
- progress.tsx
- scroll-area.tsx
- select.tsx
- separator.tsx
- sheet.tsx
- skeleton.tsx
- statistic.tsx
- switch.tsx
- table.tsx
- tabs.tsx
- textarea.tsx
- toast.tsx
- tooltip.tsx

---

*报告生成时间: 2026-02-10*
