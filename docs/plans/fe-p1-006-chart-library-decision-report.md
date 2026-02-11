# FE-P1-006: 图表库决策审核报告

> **任务编号**: FE-P1-006
> **审核日期**: 2026-02-11
> **审核结果**: 虚假问题 - 项目已完全使用 Recharts

---

## 问题描述

原技术债务报告中描述：
- **位置**: `Stats.tsx`, `PatientCompliance.tsx`, `RoundingDetail.tsx`
- **问题**: 使用 @ant-design/charts 而非 Recharts
- **影响**: 风格不一致
- **预估工作量**: 8 小时

---

## 审核发现

### 1. 依赖包检查

查看 `frontend/package.json`：

```json
{
  "dependencies": {
    "recharts": "^3.7.0",
    // ... 其他依赖
  }
}
```

**结论**: 项目中**没有** `@ant-design/charts` 依赖，只有 `recharts`。

### 2. 图表组件实现

项目已有完整的自定义图表组件，位于 `frontend/src/components/charts/`：

| 组件 | 文件 | 功能 |
|------|------|------|
| 折线图 | `line-chart.tsx` | 支持单/多系列、平滑曲线、Y轴范围控制 |
| 柱状图 | `column-chart.tsx` | 支持单/多柱、柱宽比例、图例位置 |
| 饼图 | `pie-chart.tsx` | 支持环形图、标签显示、图例位置 |

**导出配置** (`frontend/src/components/charts/index.ts`):
```typescript
export { default as CustomLineChart } from './line-chart';
export type { LineChartData, LineChartProps } from './line-chart';

export { default as CustomColumnChart } from './column-chart';
export type { ColumnChartData, ColumnChartProps } from './column-chart';

export { default as CustomPieChart } from './pie-chart';
export type { PieChartData, CustomPieChartProps } from './pie-chart';
```

### 3. 主题适配

图表组件已集成 shadcn/ui 主题系统 (`frontend/src/lib/theme.ts`)：

```typescript
export function getThemeColors(): Record<string, string> {
  // 从 CSS 变量获取主题颜色
  return {
    colorPrimary: getHexColor('primary'),
    colorSuccess: getHexColor('success'),
    colorWarning: getHexColor('warning'),
    colorError: getHexColor('danger'),
    colorInfo: getHexColor('info'),
  };
}
```

### 4. 使用情况

| 页面 | 使用的图表组件 | 状态 |
|------|----------------|------|
| `Stats.tsx` | `CustomLineChart` | ✅ 已使用自定义组件 |
| `PatientCompliance.tsx` | `CustomLineChart`, `CustomColumnChart`, `CustomPieChart` | ✅ 已使用自定义组件 |
| `RoundingDetail.tsx` | `CustomLineChart` | ✅ 已使用自定义组件 |

---

## 代码示例

### Stats.tsx
```typescript
import { CustomLineChart } from '@/components/charts';

<CustomLineChart
  data={chartData}
  xField="date"
  yField={['会话数', '消息数']}
  height={300}
  smooth={true}
  tooltipFormatter={tooltipFormatter}
/>
```

### PatientCompliance.tsx
```typescript
import { CustomLineChart, CustomColumnChart, CustomPieChart } from '@/components/charts';

// 折线图 - 依从性趋势
<CustomLineChart
  data={trendLineData}
  xField="date"
  yField="value"
  height={250}
  smooth={true}
  yAxisMax={100}
  yAxisMin={0}
  colors={[themeColors.colorPrimary]}
/>

// 饼图 - 任务完成分布
<CustomPieChart
  data={pieData}
  nameField="type"
  valueField="value"
  height={200}
  radius={0.8}
  innerRadius={0.6}
  colors={[themeColors.colorSuccess, themeColors.colorError, themeColors.colorWarning]}
/>

// 柱状图 - 每日任务详情
<CustomColumnChart
  data={barChartData}
  xField="date"
  yField={['总任务数', '已完成']}
  height={200}
  columnWidthRatio={0.6}
  colors={[themeColors.colorPrimary, themeColors.colorSuccess]}
/>
```

### RoundingDetail.tsx
```typescript
import { CustomLineChart } from '@/components/charts';

<CustomLineChart
  data={chartData}
  xField="date"
  yField="rate"
  height={200}
  smooth={true}
  yAxisMax={100}
  yAxisMin={0}
  colors={['#3b82f6']}
  tooltipFormatter={tooltipFormatter}
/>
```

---

## 结论

### 判定: 虚假问题

1. **无 @ant-design/charts 依赖**: package.json 中只有 recharts
2. **图表组件已统一**: 所有页面使用相同的 Custom*Chart 组件
3. **主题适配完整**: 图表颜色通过 getThemeColors() 自动适配 shadcn/ui 主题
4. **代码注释误导**: `lib/theme.ts` 中有"用于图表组件（如 @ant-design/charts）"的过时注释

### 建议

1. 更新 `frontend/src/lib/theme.ts` 中关于 @ant-design/charts 的过时注释
2. 无需其他代码修改

---

## 更新记录

| 项目 | 状态 | 说明 |
|------|------|------|
| tech-debt.md | ✅ 已更新 | 移至"已还清"区域 |
| lib/theme.ts | ⚠️ 建议更新 | 移除过时的 @ant-design/charts 注释 |
