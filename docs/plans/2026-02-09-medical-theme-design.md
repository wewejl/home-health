# 医疗工作台主题设计文档

**设计日期**: 2026-02-09
**设计者**: Claude (前端设计技能)
**状态**: ✅ 已实施

---

## 1. 设计概述

### 1.1 设计目标
为医生工作台创建一个**专业、现代、清晰**的医疗风格主题系统，解决之前 Ant Design 黑色主题与 Tailwind CSS 主题冲突导致的视觉混乱问题。

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **专业性** | 色彩传达医疗行业的可信感和专业性 |
| **可读性** | 优秀的对比度和文字层级，确保长时间使用不疲劳 |
| **一致性** | 统一的主题系统，所有组件使用相同的色彩变量 |
| **可访问性** | 支持浅色/深色模式切换，符合 WCAG 标准 |
| **响应式** | 适配各种屏幕尺寸 |

---

## 2. 色彩系统

### 2.1 主色调 - 医疗蓝

```
Primary: #0EA5E9 (Sky 500)
Hover:   #0284C7 (Sky 600)
Active:  #0369A1 (Sky 700)
```

**选择理由**：
- 蓝色是医疗行业的标准色彩，传达专业、冷静、可靠
- Sky 蓝色系比纯蓝更柔和，减少视觉疲劳
- 高对比度确保在各种背景下清晰可读

### 2.2 背景色系

| 变量 | HSL 值 | 用途 |
|------|--------|------|
| `--background` | `210 40% 98%` | 页面主背景，浅灰蓝色减少眩光 |
| `--surface` | `0 0% 100%` | 卡片表面，纯白提供清晰分隔 |
| `--surface-alt` | `210 40% 96%` | 交替表面，用于表格斑马纹 |

### 2.3 文字色系

| 变量 | HSL 值 | 用途 |
|------|--------|------|
| `--foreground` | `222 47% 11%` | 主要文字，深色确保可读性 |
| `--foreground-secondary` | `215 20% 40%` | 次要文字，用于标签和提示 |
| `--foreground-tertiary` | `215 20% 60%` | 辅助文字，用于禁用状态 |

### 2.4 状态色

| 状态 | HSL 值 | Hex | 用途 |
|------|--------|-----|------|
| **Success** | `160 84% 39%` | `#10B981` | 完成、正常、成功 |
| **Warning** | `38 92% 50%` | `#F59E0B` | 警告、待处理 |
| **Danger** | `0 72% 51%` | `#EF4444` | 错误、异常、危险 |
| **Info** | `217 91% 60%` | `#3B82F6` | 信息提示 |

### 2.5 深色模式

深色模式调整了亮度，确保在暗色背景下：
- 主色更亮 (`#38BDF8`)
- 文字反色为浅色
- 表面色使用深灰色系
- 状态色保持可识别性

---

## 3. 组件样式规范

### 3.1 按钮 (Button)

| 变体 | 样式 |
|------|------|
| `default` | 医疗蓝背景 + 白色文字 |
| `ghost` | 无背景，hover 时浅灰背景 |
| `outline` | 边框样式 |
| `destructive` | 危险操作，红色背景 |

### 3.2 标签 (Badge)

采用**浅色背景 + 深色文字**的设计：
- `success`: 浅绿背景 + 深绿文字
- `warning`: 浅橙背景 + 深橙文字
- `danger`: 浅红背景 + 深红文字
- `info`: 浅蓝背景 + 深蓝文字

### 3.3 卡片 (Card)

- 白色背景
- 细边框
- 微妙阴影
- hover 时阴影加深

### 3.4 表格 (Table)

- 斑马纹交替背景
- hover 高亮行
- 表头使用浅灰背景 + 深色文字

### 3.5 标签页 (Tabs)

- 容器使用浅灰背景
- 激活标签使用白色背景 + 阴影
- 非激活标签使用次要文字色

---

## 4. 布局与间距

### 4.1 圆角规范

| 名称 | 值 | 用途 |
|------|-----|------|
| `--radius-sm` | 4px | 小元素 |
| `--radius` | 6px | 默认圆角（按钮、输入框） |
| `--radius-lg` | 8px | 卡片、大容器 |

### 4.2 阴影规范

| 名称 | 值 | 用途 |
|------|-----|------|
| `--shadow-sm` | `0 1px 2px` | 默认阴影 |
| `--shadow` | `0 1px 3px` | 中等阴影 |
| `--shadow-md` | `0 4px 6px` | hover 阴影 |

### 4.3 间距规范

遵循 Tailwind 默认间距系统，主要使用：
- `p-6` (24px) - 卡片内边距
- `p-3` (12px) - 小元素内边距
- `gap-3` (12px) - 网格间距

---

## 5. 动画与交互

### 5.1 过渡时间

| 类型 | 时长 | 用途 |
|------|------|------|
| `duration-150` | 150ms | 快速交互（按钮 hover） |
| `duration-200` | 200ms | 标准交互（卡片 hover） |
| `duration-300` | 300ms | 缓慢动画（进度条） |

### 5.2 缓动函数

- `ease-out` - 用于 hover 效果
- `transition-all` - 统一过渡所有可动画属性

---

## 6. 已修改文件

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/index.css` | 完全重写主题系统 |
| `frontend/tailwind.config.js` | 更新色彩映射 |
| `frontend/src/App.tsx` | 修改 Ant Design 主题为医疗蓝 |
| `frontend/src/components/ui/button.tsx` | 使用新的主题变量 |
| `frontend/src/components/ui/card.tsx` | 使用 surface 色系 |
| `frontend/src/components/ui/badge.tsx` | 浅色背景设计 |
| `frontend/src/components/ui/progress.tsx` | 使用新的主题色 |
| `frontend/src/components/ui/tabs.tsx` | 更新样式 |

---

## 7. 使用示例

### 7.1 按钮使用

```tsx
<Button variant="default">主要操作</Button>
<Button variant="ghost">次要操作</Button>
<Button variant="destructive">危险操作</Button>
```

### 7.2 标签使用

```tsx
<Badge variant="success">完成</Badge>
<Badge variant="warning">警告</Badge>
<Badge variant="danger">异常</Badge>
<Badge variant="info">信息</Badge>
```

### 7.3 卡片使用

```tsx
<Card>
  <CardHeader>
    <CardTitle>标题</CardTitle>
  </CardHeader>
  <CardContent>内容</CardContent>
</Card>
```

---

## 8. 浏览器兼容性

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ 支持深色模式切换

---

## 9. 后续优化建议

1. **无障碍增强**: 添加更多 ARIA 标签
2. **动画细化**: 为页面加载添加渐进式动画
3. **主题定制**: 考虑添加主题定制选项
4. **组件扩展**: 为更多组件添加医疗风格变体
