# 前端架构统一设计方案

**日期**: 2026-02-09
**状态**: 待确认
**优先级**: P0

---

## 一、现状分析

### 1.1 当前依赖

```json
{
  "antd": "^5.22.0",                      // Ant Design 组件库
  "@ant-design/charts": "^2.2.0",         // Ant Design 图表库
  "@ant-design/icons": "^5.5.0",           // Ant Design 图标
  "@radix-ui/react-*": "多个",             // Radix UI 无样式组件
  "lucide-react": "^0.563.0",             // Lucide 图标库
  "tailwindcss": "^3.4.19",               // Tailwind CSS
  "next-themes": "^0.4.6"                 // 主题切换
}
```

### 1.2 组件使用情况

| 页面/模块 | 组件库 | 主要组件 |
|-----------|--------|----------|
| 管理后台页面 (Dashboard, Departments, Doctors, etc.) | Ant Design | Card, Row, Col, Statistic, Spin, Table, Typography |
| 医生工作台页面 (PatientList, PatientDetail, Tabs) | shadcn/ui (Radix UI) | Button, Card, Input, Badge, Progress, Table, Tabs, Dialog |
| 布局组件 (MainLayout) | shadcn/ui | Button, DropdownMenu, Avatar |
| 图标 | 混用 | @ant-design/icons + lucide-react |

### 1.2 存在的问题

1. **主题系统割裂**：
   - CSS 变量定义了一套颜色（`--primary`, `--success` 等）
   - Ant Design 有独立的 `ConfigProvider` 主题配置
   - shadcn/ui 使用 CSS 变量
   - 三者颜色值不完全一致

2. **组件库混用**：
   - 管理后台用 Ant Design
   - 医生工作台用 shadcn/ui
   - 同一个 Button 组件在不同页面行为不一致

3. **图标系统混乱**：
   - 管理后台页面用 `@ant-design/icons`
   - 医生工作台页面用 `lucide-react`
   - 两个图标库风格不同

4. **样式重复定义**：
   - `index.css` 中定义了 `.badge-success`, `.search-bar` 等类
   - Tailwind 配置中也定义了颜色
   - Ant Design 组件有自己的样式

---

## 二、架构决策

### 2.1 组件库策略

**决策：统一使用 shadcn/ui，Ant Design 仅用于图表组件**

| 组件类型 | 使用方案 |
|----------|----------|
| 基础 UI 组件 | shadcn/ui (Button, Input, Card, Dialog, etc.) |
| 图表组件 | @ant-design/charts (保留) |
| 图标 | lucide-react (统一使用) |
| 数据表格 | shadcn/ui Table |
| 复杂业务组件 | 基于 shadcn/ui 封装 |

**决策理由**：
1. shadcn/ui 基于 Radix UI，无障碍和可访问性更好
2. shadcn/ui 直接使用 Tailwind CSS，与现有主题系统一致
3. 代码复制到项目中，可完全自定义，不被组件库版本限制
4. lucide-react 图标风格现代、统一， Tree-shaking 友好
5. Ant Design 图表功能强大，但基础组件会与主题系统冲突

### 2.2 组件迁移边界

| Ant Design 组件 | shadcn/ui 替代 | 迁移优先级 |
|-----------------|----------------|-----------|
| Button | Button | P0 |
| Card | Card | P0 |
| Input/InputNumber | Input | P0 |
| Select | Select | P0 |
| Table | Table | P0 |
| Form | 需要基于 shadcn/ui 封装 | P1 |
| DatePicker | 需要安装 shadcn/ui 的 datePicker | P1 |
| Spin | 需要创建 Loader 组件 | P1 |
| Typography | 直接使用 HTML + Tailwind | P1 |
| Row/Col (Grid) | Tailwind grid/flex | P0 |
| Statistic | 自定义 StatCard 组件 | P1 |
| @ant-design/charts | 保留不变 | N/A |

---

## 三、主题系统统一

### 3.1 统一原则

**单一数据源：CSS 变量 (`:root` 和 `.dark`)**

所有颜色、圆角、阴影都从 CSS 变量读取：
- Tailwind 通过 `tailwind.config.js` 引用
- shadcn/ui 组件直接使用 Tailwind 类
- Ant Design 图表通过配置引用 CSS 变量

### 3.2 CSS 变量定义

保留现有的 `index.css` 定义，但做以下增强：

```css
:root {
  /* === 语义化颜色 === */
  --primary: 199 89% 48%;              /* 医疗蓝 */
  --primary-hover: 200 88% 42%;
  --primary-active: 200 95% 35%;

  --success: 160 84% 39%;
  --warning: 38 92% 50%;
  --danger: 0 72% 51%;
  --info: 217 91% 60%;

  /* === 中性色 === */
  --background: 210 40% 98%;
  --surface: 0 0% 100%;
  --foreground: 222 47% 11%;

  /* === 边框和圆角 === */
  --border: 214 32% 91%;
  --radius: 6px;
}
```

### 3.3 Tailwind 配置

现有 `tailwind.config.js` 已正确配置，无需修改。

关键点：
- 使用 `hsl(var(--primary))` 格式引用 CSS 变量
- `darkMode: ['class']` 支持手动切换深色模式

### 3.4 Ant Design 图表主题

修改 `App.tsx` 中的 `medicalTheme`，使用 CSS 变量：

```typescript
const medicalTheme = {
  token: {
    colorPrimary: 'hsl(var(--primary))',
    colorSuccess: 'hsl(var(--success))',
    colorWarning: 'hsl(var(--warning))',
    colorError: 'hsl(var(--danger))',
    colorInfo: 'hsl(var(--info))',
    borderRadius: 6,
  },
};
```

**注意**：Ant Design 5.x 的 ConfigProvider 不直接支持 `hsl()` 格式的 CSS 变量引用。需要在运行时获取计算后的颜色值。

### 3.5 运行时主题同步

创建 `src/lib/theme.ts` 工具：

```typescript
/**
 * 从 CSS 变量获取颜色值
 * 用于 Ant Design ConfigProvider
 */
export function getThemeColors(): Record<string, string> {
  const styles = getComputedStyle(document.documentElement);

  const getColor = (name: string): string => {
    const hsl = styles.getPropertyValue(`--${name}`).trim();
    // 将 "199 89% 48%" 转换为 hex 或 rgb
    return hslToHex(hsl);
  };

  return {
    colorPrimary: getColor('primary'),
    colorSuccess: getColor('success'),
    colorWarning: getColor('warning'),
    colorError: getColor('danger'),
    colorInfo: getColor('info'),
  };
}

function hslToHex(hsl: string): string {
  // HSL 到 Hex 转换逻辑
  // ...
}
```

---

## 四、具体实施方案

### 4.1 需要创建的文件

```
frontend/src/
├── lib/
│   ├── utils.ts              # 已存在
│   └── theme.ts              # 新增：主题工具函数
├── components/
│   ├── ui/                   # shadcn/ui 组件（已存在）
│   └── medical/              # 新增：医疗业务组件
│       ├── stat-card.tsx     # 统计卡片
│       ├── data-table.tsx    # 数据表格（带分页、筛选）
│       ├── page-header.tsx   # 页面头部
│       └── loading-skeleton.tsx  # 加载骨架屏
```

### 4.2 迁移步骤（优先级排序）

#### 阶段 1：基础设施（P0，Week 1）

| 步骤 | 任务 | 文件 | 验证方式 |
|------|------|------|----------|
| 1.1 | 创建主题工具 | `src/lib/theme.ts` | 单元测试 |
| 1.2 | 修改 Ant Design 主题配置 | `src/App.tsx` | 启动后检查颜色 |
| 1.3 | 创建 StatCard 组件 | `src/components/medical/stat-card.tsx` | 替换 Dashboard 中的 Card |
| 1.4 | 创建 Loading 组件 | `src/components/medical/loading-skeleton.tsx` | 替换 Spin |
| 1.5 | 统一图标导入 | 所有页面 | 搜索替换 |

#### 阶段 2：页面迁移（P0，Week 2）

| 页面 | 替换内容 | 工作量 |
|------|----------|--------|
| Dashboard.tsx | Card → StatCard, Row/Col → Tailwind grid | 2h |
| Departments.tsx | Table → shadcn/ui Table, Form → 自定义 | 4h |
| Doctors.tsx | Table → shadcn/ui Table | 3h |
| Diseases.tsx | Table → shadcn/ui Table | 3h |
| Drugs.tsx | Table → shadcn/ui Table | 3h |
| Knowledge.tsx | Table → shadcn/ui Table | 3h |
| Feedbacks.tsx | Table → shadcn/ui Table | 3h |
| Stats.tsx | @ant-design/charts → 保留 | 1h |
| MedicalOrders.tsx | Table → shadcn/ui Table | 3h |
| PatientCompliance.tsx | Table → shadcn/ui Table | 3h |
| Rounding.tsx | Table → shadcn/ui Table | 3h |

#### 阶段 3：深色模式完善（P1，Week 3）

| 步骤 | 任务 | 验证 |
|------|------|------|
| 3.1 | 检查所有页面深色模式 | 手动切换主题检查 |
| 3.2 | 修复 Ant Design 图表深色模式 | 检查图表颜色 |
| 3.3 | 统一加载状态样式 | 全局检查 |

#### 阶段 4：清理优化（P2，Week 4）

| 步骤 | 任务 |
|------|------|
| 4.1 | 移除不再使用的 Ant Design 组件导入 |
| 4.2 | 移除 `@ant-design/icons` 导入（保留图表需要的） |
| 4.3 | 更新 package.json，移除不必要的依赖 |

### 4.3 风险点

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Ant Design Form 功能强大 | 替换后表单验证需要重新实现 | 先使用 react-hook-form + zod |
| 深色模式切换时图表闪烁 | 用户体验下降 | 使用主题缓存，预加载颜色 |
| 大量页面修改 | 引入 bug | 分支开发，逐个页面测试 |
| Ant Design 图表不支持 CSS 变量 | 颜色不一致 | 使用运行时颜色转换 |

---

## 五、开发规范

### 5.1 组件选择规范

```
┌─────────────────────────────────────────────────────────┐
│                    组件选择决策树                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  需要组件？                                              │
│     │                                                   │
│     ├── 图表？ ──→ @ant-design/charts                   │
│     │                                                   │
│     ├── 基础 UI (Button, Input, etc.)？ ──→ shadcn/ui   │
│     │                                                   │
│     ├── 复杂业务组件？ ──→ 基于shadcn/ui 自定义         │
│     │                                                   │
│     └── 图标？ ──→ lucide-react                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 样式规范

| 场景 | 使用方式 |
|------|----------|
| 布局 | Tailwind 类：`flex`, `grid`, `p-4`, `gap-4` |
| 颜色 | 语义化变量：`text-primary`, `bg-success` |
| 边框 | Tailwind 类：`border`, `border-border` |
| 圆角 | Tailwind 类：`rounded-lg` (引用 CSS 变量) |
| 深色模式 | Tailwind 类：`dark:bg-background` |
| 复杂组件 | shadcn/ui 组件 |

### 5.3 图标规范

```typescript
// ✅ 正确：使用 lucide-react
import { Search, User, Stethoscope } from 'lucide-react';

// ❌ 错误：使用 @ant-design/icons
import { SearchOutlined } from '@ant-design/icons';
```

### 5.4 代码审查检查点

每次 PR 必须检查：

- [ ] 没有使用 `antd` 的基础组件（Button, Input, Card, Table, Form）
- [ ] 没有使用 `@ant-design/icons`（图表页面除外）
- [ ] 颜色使用语义化变量（`bg-primary`, `text-success`）
- [ ] 深色模式正常工作
- [ ] 新组件放在正确的目录
  - 通用 UI 组件：`src/components/ui/`
  - 医疗业务组件：`src/components/medical/`

---

## 六、目录结构规范

```
frontend/src/
├── components/
│   ├── ui/                     # shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── ...
│   ├── medical/                # 医疗业务组件
│   │   ├── stat-card.tsx       # 统计卡片
│   │   ├── data-table.tsx      # 数据表格
│   │   ├── patient-card.tsx    # 患者卡片
│   │   ├── order-badge.tsx     # 医嘱徽章
│   │   └── loading-skeleton.tsx
│   └── theme-provider.tsx      # 主题提供者
├── lib/
│   ├── utils.ts                # cn() 工具函数
│   └── theme.ts                # 主题相关工具
├── layouts/
│   └── MainLayout.tsx
├── pages/
│   ├── admin/                  # 管理员页面
│   ├── doctor/                 # 医生工作台页面
│   └── ...
├── api/
│   └── ...
└── index.css                   # CSS 变量定义
```

---

## 七、实施检查清单

### 基础设施阶段
- [ ] 创建 `src/lib/theme.ts`
- [ ] 创建 `src/components/medical/` 目录
- [ ] 创建 StatCard 组件
- [ ] 创建 LoadingSkeleton 组件
- [ ] 创建 DataTable 组件
- [ ] 更新 App.tsx 的主题配置

### 迁移阶段
- [ ] Dashboard.tsx
- [ ] Departments.tsx
- [ ] Doctors.tsx
- [ ] Diseases.tsx
- [ ] Drugs.tsx
- [ ] Knowledge.tsx
- [ ] Feedbacks.tsx
- [ ] Stats.tsx
- [ ] MedicalOrders.tsx
- [ ] PatientCompliance.tsx
- [ ] Rounding.tsx
- [ ] RoundingDetail.tsx

### 清理阶段
- [ ] 移除未使用的 Ant Design 导入
- [ ] 移除未使用的图标导入
- [ ] 更新 package.json
- [ ] 更新文档

---

## 八、验证标准

### 功能验证
- [ ] 所有页面功能正常
- [ ] 深色模式切换正常
- [ ] 颜色在所有模式下一致

### 性能验证
- [ ] 首屏加载时间不增加
- [ ] 图标正确 Tree-shaking
- [ ] 没有重复的样式规则

### 代码质量
- [ ] ESLint 无错误
- [ ] TypeScript 无类型错误
- [ ] 没有使用被禁止的组件

---

## 九、附录：shadcn/ui 安装命令

```bash
# 基础组件
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add label
npx shadcn@latest add select
npx shadcn@latest add checkbox
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add separator
npx shadcn@latest add tabs
npx shadcn@latest add table
npx shadcn@latest add badge
npx shadcn@latest add progress
npx shadcn@latest add avatar

# 表单相关
npx shadcn@latest add form
npx shadcn@latest add textarea
npx shadcn@latest add radio-group
```

---

## 十、总结

| 决策 | 理由 |
|------|------|
| 统一使用 shadcn/ui | 与 Tailwind 深度集成，主题一致性好 |
| 保留 @ant-design/charts | 图表功能强大，无替代方案 |
| 统一使用 lucide-react | 现代、轻量、Tree-shaking |
| CSS 变量为单一数据源 | 确保深色模式下颜色一致 |

迁移完成后，将实现：
1. 统一的组件库
2. 一致的主题系统
3. 清晰的目录结构
4. 可维护的代码库
