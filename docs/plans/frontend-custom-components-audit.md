# 前端自定义组件审查报告

**审查日期**: 2026-02-10
**审查范围**: `frontend/src/` 目录下所有代码
**审查目的**: 找出所有非 shadcn/ui 的自定义实现

---

## 审查概览

| 类型 | 数量 | 说明 |
|-----|------|------|
| shadcn/ui 组件 | 33 个 | `components/ui/` 目录下的标准组件 |
| 自定义组件 | 7 个 | 需要保留或重构的组件 |
| 自定义布局 | 1 个 | MainLayout |
| 页面组件 | 20+ 个 | 各功能页面 |

---

## 一、shadcn/ui 标准组件 ✅

以下是已正确使用的 shadcn/ui 组件（无需修改）：

| 组件 | 文件路径 | 状态 |
|-----|---------|------|
| Alert | `ui/alert.tsx` | ✅ |
| AlertDialog | `ui/alert-dialog.tsx` | ✅ |
| Avatar | `ui/avatar.tsx` | ✅ |
| Badge | `ui/badge.tsx` | ✅ |
| Button | `ui/button.tsx` | ✅ |
| Card | `ui/card.tsx` | ✅ |
| Checkbox | `ui/checkbox.tsx` | ✅ |
| Collapsible | `ui/collapsible.tsx` | ✅ |
| Command | `ui/command.tsx` | ✅ |
| DatePicker | `ui/date-picker.tsx` | ✅ |
| Dialog | `ui/dialog.tsx` | ✅ |
| DropdownMenu | `ui/dropdown-menu.tsx` | ✅ |
| Form | `ui/form.tsx` | ✅ |
| HoverCard | `ui/hover-card.tsx` | ✅ |
| Input | `ui/input.tsx` | ✅ |
| Label | `ui/label.tsx` | ✅ |
| NavigationMenu | `ui/navigation-menu.tsx` | ✅ |
| Popover | `ui/popover.tsx` | ✅ |
| Progress | `ui/progress.tsx` | ✅ |
| ScrollArea | `ui/scroll-area.tsx` | ✅ |
| Select | `ui/select.tsx` | ✅ |
| Separator | `ui/separator.tsx` | ✅ |
| Sheet | `ui/sheet.tsx` | ✅ |
| Skeleton | `ui/skeleton.tsx` | ✅ |
| Switch | `ui/switch.tsx` | ✅ |
| Table | `ui/table.tsx` | ✅ |
| Tabs | `ui/tabs.tsx` | ✅ |
| Textarea | `ui/textarea.tsx` | ✅ |
| Toast | `ui/toast.tsx` | ✅ |
| Tooltip | `ui/tooltip.tsx` | ✅ |

---

## 二、自定义组件（非 shadcn/ui）⚠️

### 1. MainLayout - 主布局（完全自定义）

**文件路径**: `frontend/src/layouts/MainLayout.tsx`

**问题描述**:
- 侧边栏完全手写实现，未使用 shadcn/ui 的 `Sheet` 或 `NavigationMenu`
- 菜单按钮使用纯 HTML button，而非 shadcn/ui 组件
- 折叠/展开逻辑自定义

**shadcn/ui 替代方案**:
```tsx
// 应该使用以下组件组合：
- Sheet (移动端侧边栏)
- ScrollArea (菜单滚动区域)
- Resizable (可选调整宽度)
- Collapsible (菜单分组折叠)
```

**影响范围**: 整个应用的布局结构

---

### 2. PageHeader - 页面头部（自定义）

**文件路径**: `frontend/src/components/medical/page-header.tsx`

**问题描述**:
- 自定义面包屑导航
- 自定义操作按钮容器

**shadcn/ui 替代方案**:
```tsx
// 可以使用：
- Breadcrumb (shadcn/ui 有此组件)
- Separator (用于分隔)
- Button (已有)
- DropdownMenu (已有)
```

**影响范围**: 使用此组件的页面

---

### 3. StatCard - 统计卡片（自定义）

**文件路径**: `frontend/src/components/medical/stat-card.tsx`

**问题描述**:
- 完全自定义的统计卡片组件
- 包含装饰背景、趋势标签等功能

**shadcn/ui 替代方案**:
```tsx
// 基础可用：
- Card (已有)
- Badge (已有，用于趋势)
// 但这是一个业务组件，保留自定义是合理的
```

**影响范围**: Dashboard 等统计页面

**建议**: 这是业务组件，可以保留，但可以考虑使用更统一的样式

---

### 4. DataTable - 数据表格（自定义）

**文件路径**: `frontend/src/components/medical/data-table.tsx`

**问题描述**:
- 662 行的大型自定义组件
- 实现了分页、排序、筛选等功能
- **应该使用 shadcn/ui 的 DataTable (基于 TanStack Table)**

**shadcn/ui 替代方案**:
```tsx
// shadcn/ui 官方有 DataTable 示例：
- 使用 @tanstack/react-table
- 结合 Table 组件
- 更好的类型安全
- 更强大的功能
```

**影响范围**: 多个数据展示页面

**建议**: 重构为使用 TanStack Table + shadcn/ui Table

---

### 5. Statistic - 统计数值（自定义）

**文件路径**: `frontend/src/components/ui/statistic.tsx`

**问题描述**:
- 简单的统计数值显示组件
- 放在 `ui/` 目录但不属于 shadcn/ui

**shadcn/ui 替代方案**:
```tsx
// 这是业务组件，应该移到 components/medical/
// 或者使用 Card + 自定义样式
```

**影响范围**: 少量使用

---

### 6. ThemeToggle - 主题切换（自定义）

**文件路径**: `frontend/src/components/theme-toggle.tsx`

**问题描述**:
- 使用 next-themes 的主题切换
- 自定义按钮实现

**shadcn/ui 替代方案**:
```tsx
// 实际上 shadcn/ui 有官方主题切换示例：
- 使用 DropdownMenu
- 或使用 Button + Switch
```

**影响范围**: 全局主题切换

**建议**: 这个实现合理，可保留

---

### 7. Avatar（增强版）

**文件路径**: `frontend/src/components/ui/avatar.tsx`

**问题描述**:
- 虽然基于 shadcn/ui，但增加了 fallback 功能
- 与 shadcn/ui 标准版有差异

**shadcn/ui 替代方案**:
```tsx
// 标准的 shadcn/ui Avatar 包含：
- Avatar
- AvatarImage
- AvatarFallback
// 当前实现与标准类似，可保留
```

**影响范围**: 全局头像显示

**建议**: 当前实现合理

---

### 8. LoadingSkeleton - 加载骨架屏（自定义）

**文件路径**: `frontend/src/components/medical/loading-skeleton.tsx`

**问题描述**:
- 自定义骨架屏组件
- 包含多种变体

**shadcn/ui 替代方案**:
```tsx
// shadcn/ui 有 Skeleton 组件
// 当前组件基于 Skeleton 扩展，是合理的业务组件
```

**影响范围**: 加载状态显示

**建议**: 这是业务组件，可以保留

---

### 9. PatientCard - 患者卡片（自定义）

**文件路径**: `frontend/src/components/patient/PatientCard.tsx`

**问题描述**:
- 完全自定义的患者卡片组件
- 包含渐变头像、完成率等功能

**shadcn/ui 替代方案**:
```tsx
// 这是业务组件，应该保留
// 基于 Card 组件构建是正确的
```

**影响范围**: 患者列表页面

**建议**: 保留，这是业务组件

---

## 三、页面组件（20+ 个）

**所有页面组件**:
- `Login.tsx`
- `Dashboard.tsx`
- `Doctors.tsx`
- `Departments.tsx`
- `Diseases.tsx`
- `Drugs.tsx`
- `Knowledge.tsx`
- `Feedbacks.tsx`
- `Stats.tsx`
- `DermaChat.tsx`
- `MedicalOrders.tsx`
- `PatientCompliance.tsx`
- `Rounding.tsx`
- `RoundingDetail.tsx`
- `DoctorPersonaChat.tsx`
- `DoctorRecordAnalysis.tsx`
- `PatientList.tsx` (医生工作台)
- `PatientDetail.tsx` (医生工作台)
- `TasksTab.tsx` (医生工作台)
- `ConsultationsTab.tsx` (医生工作台)
- `OrdersTab.tsx` (医生工作台)

**说明**: 页面组件都是业务代码，不需要使用 shadcn/ui 替代。

---

## 四、CSS 自定义样式类

**文件路径**: `frontend/src/index.css`

**自定义样式类**:
```css
/* 页面容器 */
.page-container

/* 统计卡片 */
.stat-card

/* 状态标签 */
.badge, .badge-success, .badge-warning, .badge-danger, .badge-info, .badge-neutral

/* 搜索栏 */
.search-bar

/* 表格样式 */
.table-header, .table-zebra, .table-row-hover

/* 卡片样式 */
.card-elevated

/* 分隔线 */
.divider, .divider-vertical

/* 信息网格 */
.info-grid, .info-item, .info-label, .info-value

/* 标签页列表 */
.tabs-list

/* 按钮增强 */
.btn-primary, .btn-ghost

/* 进度条容器 */
.progress-container, .progress-bar

/* 加载状态 */
.loading-skeleton

/* 空状态 */
.empty-state, .empty-state-icon

/* 患者卡片 */
.patient-card

/* 卡片悬停效果 */
.card-hover
```

**说明**: 这些是辅助类，增强了 shadcn/ui 的功能，可以保留。

---

## 五、总结与建议

### 需要重构的组件

| 组件 | 优先级 | 建议 |
|-----|-------|------|
| **MainLayout** | P0 | 使用 Sheet + ScrollArea 重构侧边栏 |
| **DataTable** | P1 | 使用 TanStack Table + shadcn/ui Table |
| **PageHeader** | P2 | 使用 shadcn/ui Breadcrumb 组件 |

### 可以保留的组件

| 组件 | 理由 |
|-----|------|
| StatCard | 业务组件，基于 Card 构建 |
| ThemeToggle | 实现合理，可保留 |
| LoadingSkeleton | 基于 Skeleton 的业务组件 |
| PatientCard | 业务组件，基于 Card 构建 |
| Statistic | 简单展示组件 |

### 优先级说明

- **P0 (高)**: MainLayout 影响整个应用的布局结构和用户体验
- **P1 (中)**: DataTable 是核心数据展示组件
- **P2 (低)**: PageHeader 是辅助组件，当前实现可用

---

## 六、下一步行动

1. **重构 MainLayout** (P0)
   - 使用 `Sheet` 组件替代自定义侧边栏
   - 使用 `ScrollArea` 实现菜单滚动
   - 使用 `Collapsible` 实现菜单分组

2. **重构 DataTable** (P1)
   - 引入 `@tanstack/react-table`
   - 使用 shadcn/ui Table 作为基础
   - 保持现有 API 兼容性

3. **优化 PageHeader** (P2)
   - 添加 shadcn/ui Breadcrumb 组件
   - 或使用现有 Breadcrumb 组件重构

---

**报告完成时间**: 2026-02-10
**审查人**: Claude (Team Lead)
