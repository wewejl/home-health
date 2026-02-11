# 前端代码与 UI 风格统一规范

**创建日期**: 2026-02-10
**风格定位**: 极简医疗蓝
**适用范围**: frontend/ 全部代码

---

## 一、视觉设计规范

### 1.1 色彩系统

#### 主色调
| 用途 | 颜色值 | CSS 变量 | Tailwind 类 |
|------|--------|----------|-------------|
| 主色 | `#0284c7` | `--primary` | `bg-primary` |
| 主色悬停 | `#0369a1` | `--primary-hover` | `hover:bg-primary-hover` |
| 主色激活 | `#075985` | `--primary-active` | `active:bg-primary-active` |

#### 语义色
| 用途 | 颜色值 | CSS 变量 | Tailwind 类 |
|------|--------|----------|-------------|
| 成功 | `#10b981` | `--success` | `text-success`, `bg-success` |
| 警告 | `#f59e0b` | `--warning` | `text-warning`, `bg-warning` |
| 危险 | `#ef4444` | `--danger` | `text-danger`, `bg-danger` |
| 信息 | `#3b82f6` | `--info` | `text-info`, `bg-info` |

#### 中性色
| 用途 | 颜色值 | CSS 变量 | Tailwind 类 |
|------|--------|----------|-------------|
| 背景 | `#ffffff` | `--background` | `bg-background` |
| 次要背景 | `#f8fafc` | `--surface` | `bg-surface` |
| 前景 | `#0f172a` | `--foreground` | `text-foreground` |
| 次要前景 | `#64748b` | `--foreground-secondary` | `text-foreground-secondary` |
| 边框 | `#e2e8f0` | `--border` | `border-border` |

### 1.2 圆角规范

| 元素类型 | 圆角值 | Tailwind 类 |
|---------|--------|-------------|
| 小元素（按钮、输入框） | `6px` | `rounded` |
| 卡片 | `8px` | `rounded-lg` |
| 大卡片 | `12px` | `rounded-xl` |
| 圆形元素（头像） | `50%` | `rounded-full` |

**禁止使用**: `rounded-sm`, `rounded-2xl`, `rounded-3xl`

### 1.3 间距规范

| 用途 | 间距值 | Tailwind 类 |
|------|--------|-------------|
| 紧密间距 | `8px` | `gap-2`, `p-2` |
| 标准间距 | `16px` | `gap-4`, `p-4` |
| 宽松间距 | `24px` | `gap-6`, `p-6` |
| 页面边距 | `32px` | `p-8` |

**标准**: 统一使用 `gap-4` 作为默认间距

### 1.4 阴影规范

| 用途 | 阴影值 | Tailwind 类 |
|------|--------|-------------|
| 轻微阴影 | `0 1px 2px rgba(0,0,0,0.05)` | `shadow-sm` |
| 标准阴影 | `0 2px 8px rgba(0,0,0,0.08)` | `shadow` |
| 悬浮阴影 | `0 8px 16px rgba(0,0,0,0.12)` | `shadow-lg` |

**极简风格原则**: 默认使用 `shadow-sm`，重要悬浮才用 `shadow`

### 1.5 字体规范

| 用途 | 字号 | 字重 | Tailwind 类 |
|------|------|------|-------------|
| 页面标题 | `24px` | 600 | `text-2xl font-semibold` |
| 卡片标题 | `18px` | 600 | `text-lg font-semibold` |
| 正文 | `14px` | 400 | `text-sm` |
| 辅助文字 | `12px` | 400 | `text-xs` |
| 统计数字 | `32px` | 700 | `text-4xl font-bold` |

---

## 二、代码风格规范

### 2.1 格式化配置

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "printWidth": 100,
  "arrowParens": "avoid"
}
```

### 2.2 组件定义规范

**统一使用命名导出 + 函数声明**

```typescript
// ✅ 正确
interface ComponentProps {
  title: string
  onClick: () => void
}

export function ComponentName({ title, onClick }: ComponentProps) {
  // hooks
  // handlers
  // render
}
```

```typescript
// ❌ 错误
const Component: React.FC<Props> = ({ prop }) => {
  // ...
}

export default Component
```

### 2.3 组件内部结构

```typescript
export function ComponentName({ prop1, prop2 }: ComponentProps) {
  // 1. Hooks
  const [state, setState] = useState()
  useEffect(() => {}, [])

  // 2. 派生状态
  const derived = useMemo(() => {}, [])

  // 3. 事件处理函数
  const handleClick = () => {}
  const handleSubmit = () => {}

  // 4. 渲染函数（可选）
  const renderItem = () => {}

  // 5. 返回 JSX
  return (
    <div>...</div>
  )
}
```

### 2.4 Props 接口规范

```typescript
// ✅ 正确：接口与组件同文件，导出接口
export interface PatientCardProps {
  patient: Patient
  onClick: () => void
}

export function PatientCard({ patient, onClick }: PatientCardProps) {
  // ...
}
```

### 2.5 导入顺序

```typescript
// 1. 第三方库
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

// 2. 组件库
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

// 3. 自定义组件
import { PatientCard } from '@/components/patient'

// 4. API
import { doctorApi } from '@/api'

// 5. 工具函数/Hooks
import { useDebounce } from '@/hooks/useDebounce'

// 6. 类型
import type { Patient } from '@/types'
```

---

## 三、UI 组件使用规范

### 3.1 颜色使用规则

**禁止硬编码颜色，统一使用 CSS 变量类**

| ❌ 禁止 | ✅ 使用 |
|--------|---------|
| `text-gray-900` | `text-foreground` |
| `text-gray-500` | `text-foreground-secondary` |
| `bg-sky-500` | `bg-primary` |
| `text-rose-600` | `text-danger` |
| `bg-emerald-500` | `bg-success` |
| `text-amber-600` | `text-warning` |
| `border-gray-200` | `border-border` |

### 3.2 渐变使用规范

**极简风格原则**: 限制渐变使用，仅在关键位置使用

```typescript
// 允许的渐变位置
// 1. 登录页背景
from-sky-500 via-blue-500 to-indigo-600

// 2. 头像/图标点缀
from-sky-400 to-sky-600
from-emerald-400 to-emerald-600
```

### 3.3 组件使用规则

| 用途 | 使用组件 | 禁止 |
|------|---------|------|
| 按钮 | `Button` 组件 | 原生 `<button>` + 自定义样式 |
| 输入框 | `Input` 组件 | 原生 `<input>` + 自定义样式 |
| 卡片 | `Card` 组件 | `<div>` + border 样式 |
| 徽章 | `Badge` 组件 | `<span>` + bg + text 样式 |
| 对话框 | `Dialog` 组件 | 自定义 modal |

---

## 四、页面布局规范

### 4.1 标准页面结构

```typescript
export function PageName() {
  return (
    <div className="page-container min-h-screen bg-background p-6">
      {/* 页面标题 */}
      <PageHeader
        title="页面标题"
        description="页面描述"
      />

      {/* 内容区域 */}
      <div className="space-y-6">
        {/* 内容 */}
      </div>
    </div>
  )
}
```

### 4.2 页面容器

| 页面类型 | 容器类 |
|---------|--------|
| 标准页面 | `page-container min-h-screen bg-background p-6` |
| 全屏页面 | `min-h-screen bg-background` |
| 嵌套内容 | `space-y-6` 或 `space-y-4` |

---

## 五、修复优先级

### P0 - 立即修复
- [ ] 替换所有硬编码颜色为 CSS 变量类
- [ ] 统一圆角使用（移除 `rounded-sm`, `rounded-2xl`）
- [ ] 配置 Prettier 自动格式化

### P1 - 本周修复
- [ ] 统一组件定义方式
- [ ] 统一间距使用
- [ ] 统一阴影使用

### P2 - 下周修复
- [ ] 统一导出方式
- [ ] 统一 Props 接口定义
- [ ] 统一页面容器结构

---

## 六、验收标准

修复完成后应满足：

1. ✅ 所有页面使用 CSS 变量类（无 `text-gray-*`, `bg-*` 硬编码）
2. ✅ 圆角统一为 `rounded`, `rounded-lg`, `rounded-xl`
3. ✅ 间距统一为 `gap-2`, `gap-4`, `gap-6`
4. ✅ 组件统一使用命名导出函数
5. ✅ Prettier 格式化无报错
6. ✅ 暗色模式正常工作
