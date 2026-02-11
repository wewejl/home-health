# shadcn/ui 组件补充优化设计方案

## 状态
- [x] 草案中
- [ ] 待确认
- [ ] 已批准
- [ ] 实现中
- [ ] 已完成

## 创建时间
2026-02-09

## 1. 项目背景

### 1.1 当前状态分析

基于 `frontend/src/components/ui/` 目录的真实代码分析，项目已具备以下基础：

| 项目 | 状态 | 说明 |
|------|------|------|
| **UI 组件数量** | ✅ 22个 | 已实现核心组件 |
| **Radix UI 依赖** | ✅ 部分安装 | 需补充 avatar、sheet、switch、toast、tooltip |
| **Tailwind CSS** | ✅ 已配置 | 完整的医疗主题色彩系统 |
| **主题系统** | ✅ 已配置 | next-themes + 深色模式 |
| **components.json** | ✅ 已配置 | shadcn/ui 规范配置 |

### 1.2 现有组件清单

```
frontend/src/components/ui/
├── alert.tsx              ✅ 警告提示
├── alert-dialog.tsx       ✅ 警告对话框
├── avatar.tsx             ✅ 头像
├── badge.tsx              ✅ 徽章
├── button.tsx             ✅ 按钮
├── card.tsx               ✅ 卡片
├── checkbox.tsx           ✅ 复选框
├── date-picker.tsx        ✅ 日期选择器（自定义）
├── dialog.tsx             ✅ 对话框
├── dropdown-menu.tsx      ✅ 下拉菜单
├── input.tsx              ✅ 输入框
├── label.tsx              ✅ 标签
├── progress.tsx           ✅ 进度条
├── select.tsx             ✅ 选择器
├── separator.tsx          ✅ 分隔符
├── sheet.tsx              ✅ 侧边抽屉
├── statistic.tsx          ✅ 统计数值（医疗专用）
├── switch.tsx             ✅ 开关
├── table.tsx              ✅ 表格
├── tabs.tsx               ✅ 标签页
├── toast.tsx              ✅ 提示消息
└── tooltip.tsx            ✅ 工具提示
```

## 2. 优化目标

**主要目标**：补充缺失的 shadcn/ui 组件，覆盖全站页面使用

**优化原则**：
1. ✅ 遵循现有代码风格和 shadcn/ui 规范
2. ✅ 复用现有设计系统（CSS 变量、Tailwind 配置）
3. ✅ 保持医疗主题一致性
4. ✅ 组件优先级根据实际需求排序

## 3. 需要补充的组件

### 3.1 高优先级组件（P0）

| 组件 | 用途 | 应用场景 | Radix 依赖 |
|------|------|----------|------------|
| **textarea** | 多行文本输入 | 医生备注、病情描述、知识库内容 | - |
| **form** | 表单验证集成 | 登录、患者信息录入、医嘱创建 | react-hook-form |
| **popover** | 气泡弹出层 | 操作菜单、信息展示 | @radix-ui/react-popover |

### 3.2 中优先级组件（P1）

| 组件 | 用途 | 应用场景 | Radix 依赖 |
|------|------|----------|------------|
| **scroll-area** | 自定义滚动区域 | 长列表、聊天记录 | @radix-ui/react-scroll-area |
| **command** | 命令面板 | 全局搜索、快速操作 | cmdk |
| **collapsible** | 可折叠内容 | FAQ、详细信息展开 | @radix-ui/react-collapsible |

### 3.3 低优先级组件（P2）

| 组件 | 用途 | 应用场景 | Radix 依赖 |
|------|------|----------|------------|
| **skeleton** | 骨架屏 | 内容加载占位 | - |
| **hover-card** | 悬停卡片 | 用户信息预览 | @radix-ui/react-hover-card |
| **navigation-menu** | 导航菜单 | 多级导航 | @radix-ui/react-navigation-menu |

## 4. 技术实现

### 4.1 依赖补充

需要安装的 npm 包：

```bash
# 高优先级
npm install @radix-ui/react-popover
npm install react-hook-form @hookform/resolvers zod

# 中优先级
npm install @radix-ui/react-scroll-area
npm install cmdk
npm install @radix-ui/react-collapsible

# 低优先级
npm install @radix-ui/react-hover-card
npm install @radix-ui/react-navigation-menu
```

### 4.2 组件实现规范

所有组件遵循以下规范：

1. **使用 `cn` 工具函数**（已存在于 `lib/utils.ts`）
2. **使用 CVA (class-variance-authority)** 管理样式变体
3. **导出 TypeScript 类型**
4. **支持深色模式**（通过 CSS 变量）
5. **遵循 Radix UI 组合模式**

### 4.3 组件模板示例

```tsx
// src/components/ui/textarea.tsx
import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input",
          "bg-background px-3 py-2 text-sm ring-offset-background",
          "placeholder:text-muted-foreground",
          "focus-visible:outline-none focus-visible:ring-2",
          "focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
```

## 5. 实施计划

### 阶段一：高优先级组件（P0）

1. **textarea** - 多行文本输入
2. **popover** - 气泡弹出层
3. **form** - 表单验证集成

### 阶段二：中优先级组件（P1）

1. **scroll-area** - 自定义滚动区域
2. **command** - 命令面板
3. **collapsible** - 可折叠内容

### 阶段三：低优先级组件（P2）

1. **skeleton** - 骨架屏
2. **hover-card** - 悬停卡片
3. **navigation-menu** - 导航菜单

## 6. 页面应用映射

| 页面 | 需要补充的组件 |
|------|----------------|
| **登录页** (Login.tsx) | textarea, form |
| **疾病百科** (Diseases.tsx) | textarea, popover |
| **药品百科** (Drugs.tsx) | textarea, popover |
| **知识库** (Knowledge.tsx) | textarea, form, scroll-area |
| **医嘱监督** (MedicalOrders.tsx) | form, popover |
| **医生工作台** (doctor/*) | form, textarea, scroll-area |
| **统计页面** (Stats.tsx) | scroll-area |

## 7. 验收标准

- [ ] 所有新增组件符合 shadcn/ui 规范
- [ ] 组件支持深色模式
- [ ] TypeScript 类型定义完整
- [ ] 通过 ESLint 检查
- [ ] 在对应页面中验证功能正常
- [ ] 文档更新（API文档.md 或组件使用文档）

## 8. 注意事项

1. **不破坏现有组件**：已有组件保持不变
2. **保持一致性**：新组件风格与现有组件一致
3. **按需添加**：优先实现 P0 组件，P1/P2 根据实际需求
4. **测试验证**：每个组件实现后在实际页面中测试

## 9. 参考资料

- [shadcn/ui 官方文档](https://ui.shadcn.com/)
- [Radix UI 文档](https://www.radix-ui.com/)
- 现有组件实现：`frontend/src/components/ui/`
- 设计系统：`frontend/src/index.css`
- Tailwind 配置：`frontend/tailwind.config.js`
