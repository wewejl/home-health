# 前端代码评审报告 - shadcn/ui 规范

**评审日期**: 2026-02-09
**评审范围**: 前端页面组件
**评审标准**: shadcn/ui 规范、项目开发规范、代码质量

---

## 1. 评审结果总览

| 文件 | 评分 | 等级 | 主要问题 |
|------|------|------|----------|
| `Login.tsx` | 85/100 | 良好 | 使用了自定义样式而非 shadcn/ui 组件 |
| `Dashboard.tsx` | 90/100 | 优秀 | 组件使用规范，代码结构清晰 |
| `PatientList.tsx` | 75/100 | 中等 | 直接使用 fetch API，缺少统一封装 |
| `PatientDetail.tsx` | 82/100 | 良好 | 部分样式硬编码 |
| `MedicalOrders.tsx` | 78/100 | 良好 | 复杂表单处理可优化 |
| `DoctorPersonaChat.tsx` | 88/100 | 优秀 | 组件使用规范，用户体验良好 |

**总体评分**: 83/100 (良好)

---

## 2. 详细评审

### 2.1 Login.tsx - 85/100

**优点**:
- 正确使用 lucide-react 图标 (`User`, `Lock`, `Eye`, `EyeOff`)
- 使用 shadcn/ui 组件 (`Card`, `Input`, `Button`, `Label`)
- 支持深色模式 (使用 `dark:` 前缀)
- 表单验证逻辑清晰
- TypeScript 类型定义完整 (`FormErrors`, `LoginProps`)
- 无内联样式，全部使用 Tailwind 类

**问题**:
1. 自定义样式类未从组件库导入:
   - `animate-fade-in` - 应使用 shadcn/ui 的动画组件
   - `text-foreground-secondary` - 需确认是否在主题中定义
   - `bg-success-light`, `text-success` - 需确认颜色变量

2. 硬编码加载动画:
   ```tsx
   <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
   ```
   建议使用 `Loader2` 图标组件

3. 默认值硬编码:
   ```tsx
   const [username, setUsername] = useState('admin');
   const [password, setPassword] = useState('admin123');
   ```
   生产环境应移除

**改进建议**:
- 使用 `@/components/ui/textarea` 替代原生 textarea (如有)
- 抽取登录表单为独立组件，提高复用性
- 添加 forgot password 功能入口

---

### 2.2 Dashboard.tsx - 90/100

**优点**:
- 正确使用 lucide-react 图标
- 正确使用 shadcn/ui 组件
- 使用自定义 `StatCardGrid` 和 `PageHeader` 组件
- 代码结构清晰，逻辑分离
- TypeScript 类型定义完整 (`OverviewStats`)
- 加载状态使用 `LoadingSkeleton` 组件
- 列表渲染使用稳定的 key

**问题**:
1. 使用 `Array.from({ length: 8 })` 生成骨架屏:
   ```tsx
   {Array.from({ length: 8 }).map((_, i) => (
     <LoadingSkeleton key={i} variant="card" />
   ))}
   ```
   建议使用有意义的 key 或简化为固定数量的骨架屏

2. 数据获取缺少错误处理 UI:
   ```tsx
   } catch (error) {
     console.error('Failed to fetch stats:', error);
   }
   ```
   用户看不到错误提示

**改进建议**:
- 添加错误提示组件或 toast 通知
- 考虑添加数据刷新功能
- 添加空状态提示

---

### 2.3 PatientList.tsx - 75/100

**优点**:
- 正确使用 shadcn/ui 组件 (`Button`, `Card`, `Input`, `Badge`, `Progress`, `Table`)
- 使用 lucide-react 图标 (`Search`, `User`, `Stethoscope`, `Loader2`)
- 支持深色模式
- 列表渲染使用稳定的 `patient.id` 作为 key
- 响应式布局 (`md:grid-cols-2`)

**问题**:
1. 直接使用 fetch API，未使用项目统一的 API 封装:
   ```tsx
   const response = await fetch('/api/doctor/me');
   const data = await response.json();
   ```
   应使用:
   ```tsx
   import { doctorApi } from '@/api';
   const data = await doctorApi.getMe();
   ```

2. 搜索触发时机问题:
   ```tsx
   useEffect(() => {
     fetchDoctorInfo();
     fetchPatients();
   }, [searchText]);
   ```
   每次输入都触发请求，应添加防抖

3. 缺少错误处理 UI

4. 自定义 CSS 类:
   - `page-container`
   - `search-bar`
   - `table-row-hover`
   需确认是否在全局样式中定义

**改进建议**:
- 使用统一的 API 封装
- 添加搜索防抖 (useDebounce)
- 添加错误处理和空状态
- 将自定义类移至 Tailwind 配置或组件库

---

### 2.4 PatientDetail.tsx - 82/100

**优点**:
- 正确使用 shadcn/ui 组件 (`Button`, `Card`, `Badge`, `Tabs`, `Separator`)
- 使用 lucide-react 图标
- 使用 Tabs 组件组织内容
- TypeScript 类型定义完整
- 列表渲染使用稳定的 `patientId`

**问题**:
1. 自定义样式类未从组件库导入:
   - `page-container`
   - `stat-card`
   - `bg-medical-success`

2. 硬编码颜色类:
   ```tsx
   className={patient.is_profile_completed ? 'bg-medical-success' : ''}
   ```
   应使用 Badge 的 variant 属性

3. 直接使用 fetch API:
   ```tsx
   const response = await fetch(`/api/doctor/patients/${patientId}`);
   ```
   应使用统一的 API 封装

4. 重复的日期格式化逻辑:
   ```tsx
   new Date(patient.created_at).toLocaleDateString()
   ```
   应使用 dayjs 或 date-fns

**改进建议**:
- 使用统一的 API 封装
- 使用日期工具库 (dayjs)
- 抽取统计卡片为独立组件
- 将自定义类移至组件库

---

### 2.5 MedicalOrders.tsx - 78/100

**优点**:
- 正确使用 shadcn/ui 组件 (`Button`, `Card`, `Badge`, `Tabs`, `Dialog`, `Input`, `Select`, `DatePicker`, `Tooltip`, `Table`)
- 使用 lucide-react 图标
- 使用 dayjs 进行日期处理
- TypeScript 类型定义完整 (多个 interface)
- 配置对象化 (`ORDER_TYPE_CONFIG`, `STATUS_CONFIG`)
- 列表渲染使用稳定的 `order.id` 和 `task.id`

**问题**:
1. 使用原生 textarea 而非 shadcn/ui Textarea:
   ```tsx
   <textarea
     className="flex min-h-[80px] w-full rounded-sm border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-foreground-secondary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
   />
   ```
   应使用:
   ```tsx
   import { Textarea } from '@/components/ui/textarea';
   <Textarea ... />
   ```

2. 复杂的类型断言:
   ```tsx
   const data: any = {};
   ```
   应定义具体的类型

3. 自定义 toast 实现:
   ```tsx
   const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
   ```
   应使用 shadcn/ui 的 toast 组件

4. 移除未使用变量的方式不规范:
   ```tsx
   void TASK_STATUS_CONFIG;
   void tasksLoading;
   ```

**改进建议**:
- 使用 `@/components/ui/textarea`
- 使用 shadcn/ui 的 `useToast()` hook
- 移除 `any` 类型，使用具体类型
- 简化表单处理逻辑，考虑使用 react-hook-form
- 将配置对象移至独立文件

---

### 2.6 DoctorPersonaChat.tsx - 88/100

**优点**:
- 正确使用 shadcn/ui 组件 (`Button`, `Card`, `Badge`, `AlertDialog`)
- 使用 lucide-react 图标
- 使用 `cn()` 工具函数
- 使用 `useToast()` hook
- TypeScript 类型定义完整
- 良好的用户体验 (防刷新丢失进度、键盘快捷键)
- 自动滚动到底部
- 自适应高度的输入框

**问题**:
1. 使用原生 textarea 而非 shadcn/ui Textarea

2. 自定义样式类:
   ```tsx
   className="flex-1 resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-h-[38px] max-h-[120px] h-auto"
   ```
   这些样式与 Textarea 组件重复

3. Badge variant 类型不匹配:
   ```tsx
   <Badge variant="info">进度: {currentStageIndex + 1}/{STAGES.length}</Badge>
   <Badge variant="success" className="gap-1">
   ```
   需确认 Badge 是否支持这些 variant

**改进建议**:
- 使用 `@/components/ui/textarea`
- 确认 Badge variant 类型定义
- 考虑添加消息重发功能
- 添加复制生成的 prompt 功能

---

## 3. 共性问题总结

### 3.1 组件使用问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 使用原生 textarea 而非 Textarea 组件 | 中 | 样式不一致 |
| 自定义样式类未在组件库中定义 | 中 | 维护困难 |
| Badge variant 类型不一致 | 低 | 类型警告 |

### 3.2 API 调用问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 直接使用 fetch API | 高 | 不符合项目规范 |
| 缺少统一错误处理 | 中 | 用户体验差 |
| 缺少请求防抖 | 低 | 性能问题 |

### 3.3 代码质量问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 使用 `any` 类型 | 中 | 类型安全降低 |
| 硬编码默认值 | 低 | 安全风险 |
| 重复的日期格式化逻辑 | 低 | 代码冗余 |
| 自定义 toast 实现 | 中 | 不一致的用户体验 |

---

## 4. 改进建议优先级

### P0 - 必须修复

1. **统一 API 调用方式**
   - 所有页面应使用 `@/api` 中封装的 API 方法
   - 统一错误处理逻辑

2. **使用 shadcn/ui Textarea 组件**
   - 替换所有原生 textarea
   - 确保样式一致性

### P1 - 建议修复

1. **使用 shadcn/ui Toast**
   - 替换自定义 toast 实现
   - 使用 `useToast()` hook

2. **移除 `any` 类型**
   - 定义具体的数据类型
   - 提高类型安全性

3. **添加搜索防抖**
   - 使用 useDebounce hook
   - 优化性能

### P2 - 可选优化

1. **抽取可复用组件**
   - 统计卡片
   - 表单对话框
   - 空状态提示

2. **添加更多错误处理 UI**
   - 错误边界
   - 网络错误提示
   - 重试功能

3. **统一日期处理**
   - 使用 dayjs 或 date-fns
   - 抽取常用格式化函数

---

## 5. 代码规范检查清单

| 检查项 | 通过 | 说明 |
|--------|------|------|
| 使用 shadcn/ui 组件 | 部分 | 需替换原生 textarea |
| 使用 lucide-react 图标 | 是 | 全部符合 |
| 不使用 antd 基础组件 | 是 | 未发现 antd 使用 |
| 使用 Tailwind 类布局 | 是 | 全部符合 |
| 使用语义化颜色变量 | 部分 | 需确认自定义类 |
| 无内联样式 | 是 | 全部符合 |
| 支持深色模式 | 是 | 主要页面支持 |
| TypeScript 类型完整 | 部分 | 存在 any 类型 |
| 列表渲染稳定 key | 是 | 全部符合 |
| 避免不必要重渲染 | 是 | 未发现问题 |

---

## 6. 结论

总体而言，前端代码质量良好，大部分页面正确使用了 shadcn/ui 组件和 Tailwind CSS。主要问题集中在：

1. **API 调用不统一** - 部分页面直接使用 fetch
2. **组件使用不完整** - 未使用 shadcn/ui 的 Textarea 和 Toast
3. **类型安全** - 存在 `any` 类型使用

建议按照优先级逐步改进，重点关注 API 调用统一和组件使用完整性。

---

**评审人**: Claude Code (Team Lead)
**下次评审**: 修复完成后进行复评
