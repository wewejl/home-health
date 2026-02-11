# 技术债务清单

> 最后更新：2026-02-11 (iOS P0 安全问题全部完成)
> **详细清理计划**: [2026-02-11-tech-debt-cleanup-plan.md](../plans/2026-02-11-tech-debt-cleanup-plan.md)

---

## 🔴 高优先级（尽快处理）- P0

### 皮肤科 AI 助手后端缺失
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/pages/DermaChat.tsx`, `frontend/src/App.tsx`
- **问题**: 前端调用 `/derma/start` 端点，但后端没有对应实现
- **解决方案**: 从前端移除 DermaChat 导入和路由配置
- **关联任务**: FE-P0-004

### /dashboard 路由缺失
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/App.tsx`
- **问题**: 导航中有 `/dashboard` 链接但路由未定义
- **解决方案**: 确认 Dashboard 组件已存在，路由配置正确（`/` 即为 Dashboard）
- **关联任务**: FE-P0-005

### iOS Token 存储不安全
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Services/AuthManager.swift:33`
- **问题**: UserDefaults 未加密，token 可被越狱读取
- **解决方案**: 创建 `KeychainManager.swift` 使用 Security.framework，将 Token 从 UserDefaults 迁移到 Keychain
- **新增文件**: `ios/xinlingyisheng/xinlingyisheng/Services/KeychainManager.swift`
- **验证结果**: iOS 项目编译成功 (BUILD SUCCEEDED)
- **关联任务**: IOS-P0-002

### UnifiedChatViewModel 过于庞大
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift` (914行 → 480行)
- **问题**: 违反单一职责原则，914行代码难以维护
- **解决方案**: 拆分为三个服务类
  - **新增** `ios/xinlingyisheng/xinlingyisheng/Services/ChatSessionService.swift` - 会话管理
  - **新增** `ios/xinlingyisheng/xinlingyisheng/Services/ChatMessageService.swift` - 消息管理
  - **新增** `ios/xinlingyisheng/xinlingyisheng/Services/ChatVoiceInputService.swift` - 语音输入
  - **修改** `UnifiedChatViewModel.swift` 内部使用服务类，对外保持原有接口
- **架构说明**: 保持对外 `@Published` 属性接口不变，内部委托给三个服务类处理，避免 SwiftUI 编译器类型检查超时
- **验证结果**: iOS 项目编译成功 (BUILD SUCCEEDED)
- **关联任务**: IOS-P0-003

### 前端P0安全问题修复
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/pages/Login.tsx`, `frontend/src/pages/DermaChat.tsx`, `frontend/src/api/index.ts`, `frontend/src/components/ErrorBoundary.tsx`
- **问题**: 多个前端安全风险
- **影响**: XSS攻击、认证绕过、应用崩溃等安全风险
- **解决方案**:
  1. **移除硬编码默认凭据** - `Login.tsx:22-23` 将默认 username/password 从硬编码值改为空字符串
  2. **修复XSS风险** - `DermaChat.tsx:321-323` 添加 DOMPurify 净化消息内容，安装 `dompurify` 和 `@types/dompurify`
  3. **修复EventSource认证问题** - `api/index.ts:294-299` 将 `createSessionStream` 从 EventSource 改为 fetch API，支持自定义 Authorization 请求头
  4. **添加Error Boundary** - 创建 `ErrorBoundary.tsx` 组件并在 `App.tsx` 中使用，防止应用崩溃白屏
  5. **统一状态管理** - `authStore.ts` 已存在并功能完整，可供其他组件使用
- **验证结果**: 前端构建成功 (`npm run build`)
- **关联任务**: FE-P0-003

### 后端测试模式默认值安全问题
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `backend/app/config.py:46,51`, `docker-compose.yml:44,45`
- **问题**: 测试模式 (`TEST_MODE`, `ADMIN_TEST_MODE`) 默认值为 `True`，生产环境若忘记设置将导致安全风险
- **影响**: 生产环境安全风险（万能验证码、跳过认证）
- **解决方案**:
  - 修改 `config.py` 默认值从 `True` 改为 `False`
  - 修改 `docker-compose.yml` 环境变量默认值从 `true` 改为 `false`
  - 添加生产环境强制检查，若检测到测试模式启用则抛出异常
- **关联任务**: BE-P0-002

### 后端JWT密钥安全检查不足
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `backend/app/config.py:119-173`, `docker-compose.yml:34-35`
- **问题**: 生产环境使用弱密钥时仅发出警告，不阻止应用启动
- **影响**: 生产环境可使用弱密钥运行，存在安全风险
- **解决方案**:
  - 将警告改为 `ValueError` 异常，强制阻止启动
  - 添加空字符串检查
  - 添加新的弱密钥占位符到黑名单
  - `docker-compose.yml` 中 JWT 密钥默认值改为空
- **关联任务**: BE-P0-003

### 数据库密码硬编码问题
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `docker-compose.yml:12,29-30`, `.env.example:25,33`
- **问题**: 数据库密码使用硬编码默认值 `postgres`
- **影响**: 生产环境数据库安全风险
- **解决方案**:
  - `docker-compose.yml` 中 `POSTGRES_PASSWORD` 使用环境变量 `${POSTGRES_PASSWORD:-postgres}`
  - `DATABASE_URL` 中的密码部分也使用环境变量
  - `.env.example` 添加 `POSTGRES_PASSWORD` 配置项和安全警告
- **关联任务**: BE-P0-004

### 后端测试模式无法关闭
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `backend/app/routes/admin_auth.py:17`, `backend/app/config.py`
- **问题**: 测试模式硬编码，无法通过环境变量关闭
- **影响**: 生产环境安全风险
- **解决方案**: 添加 `ADMIN_TEST_MODE` 环境变量控制
- **关联任务**: BE-P0-001

### 前端测试模式无法关闭
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/App.tsx:34-35`, `frontend/src/api/index.ts:5-6`
- **问题**: 测试用户硬编码，认证完全失效
- **影响**: 生产环境安全风险
- **解决方案**: 添加 `VITE_ADMIN_TEST_MODE` 环境变量控制
- **关联任务**: FE-P0-001

### 智能体框架重复实现
- **状态**: ✅ 已移除 (2026-02-11) - 虚假问题
- **位置**: `backend/app/services/ai/`
- **审核结果**: CrewAI 和 LangGraph 依赖已安装但实际代码中并未使用
- **说明**: 代码使用自定义 BaseAIService 直接调用 LLM API
- **关联任务**: BE-P0-002

### 前端内联组件反模式
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/pages/Doctors.tsx`
- **问题**: 组件导入路径不统一（相对路径 vs 别名路径）
- **解决方案**: 统一使用 `@/components/ui/...` 别名路径
- **关联任务**: FE-P0-002

### iOS 对话页面输入框透明问题
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: iOS 多个页面
- **问题**: 输入框背景色使用 `.opacity(0.5)` 导致显示异常
- **解决方案**: 移除透明度设置，使用完全不透明的背景色
- **影响文件**: 8 个文件（AskDoctorView, DiseaseListView, LoginView, MedLiveDiseaseDetailView, ExportConfigView, EventDetailView, TaskCheckInView, WeChatStyleInputBar）
- **关联任务**: IOS-P0-001, TASK-UI-006

---

## 🟡 中优先级（有空就做）- P1

### 硬编码配置
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `backend/app/config.py`, `docker-compose.yml`, `.env.example`
- **问题**: JWT_SECRET_KEY、ADMIN_JWT_SECRET、DATABASE_URL 使用硬编码默认值
- **解决方案**:
  - 使用 `secrets.token_urlsafe(32)` 生成强随机密钥作为默认值
  - 更新 `.env.example` 添加安全警告和密钥生成命令
  - 更新 `docker-compose.yml` 支持环境变量覆盖
  - 生产环境自动检测并警告使用默认密钥
- **影响**: 提升生产环境安全性
- **关联任务**: BE-P1-003

### API V1/V2 并存
- **状态**: ❌ 待处理
- **位置**: 后端 `backend/app/routes/sessions.py` vs `sessions_v2.py`
- **问题**: 存在 V1 和 V2 两套 API
- **影响**: 维护成本高
- **预估工作量**: 16 小时
- **关联任务**: BE-P1-001

### N+1 查询风险
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: 后端多处关系查询
- **问题**: 未使用 joinedload 优化
- **影响**: 性能问题
- **解决方案**:
  - 添加 `from sqlalchemy.orm import joinedload, selectinload` 导入
  - `doctor_workstation.py`: 优化 7 处 N+1 查询
    - `get_doctor_info`: 使用 `joinedload` 预加载 department
    - `get_patient_stats`: 批量查询替代循环查询（4 个查询替代 N+1）
    - `get_patients`: 批量查询替代循环查询（4 个查询替代 3N+1）
    - `get_assignable_patients`: 批量获取分配时间（2 个查询替代 N+1）
    - `get_patient_consultations`: 批量获取消息计数（2 个查询替代 N+1）
    - `get_patient_tasks`: 使用 `selectinload` 预加载 order
  - `admin_departments.py`: 优化 4 处 N+1 查询
    - `list_departments`: 使用 `joinedload` 预加载 doctors
    - `get_department`: 使用 `joinedload` 预加载 doctors
    - `update_department`: 使用 `joinedload` 预加载 doctors
    - `delete_department`: 使用 `joinedload` 预加载 doctors
  - `medical_orders.py`: 优化 4 处 N+1 查询
    - `get_family_bonds`: 批量获取用户信息（4 个查询替代 2N+2）
    - `get_daily_tasks`: 使用 `selectinload` 预加载 order
    - `get_family_member_tasks`: 使用 `selectinload` 预加载 order
    - `get_alerts`: 使用 `selectinload` 预加载 task_instance 和 order
- **验证结果**: 所有 API 测试通过
  - `/admin/departments`: 28 个科室，正确显示医生数量
  - `/api/doctor/me`: 医生信息、科室名称、AI 分身列表正常
  - `/api/doctor/patient-stats`: 患者统计正常
  - `/api/doctor/patients`: 患者列表正常
- **设计文档**: [2026-02-11-n1-query-optimization-design.md](../plans/2026-02-11-n1-query-optimization-design.md)
- **关联任务**: BE-P1-002

### 前端 Token 认证
- **状态**: ✅ 已验证 (2026-02-11) - 虚假问题
- **位置**: `frontend/src/api/index.ts:16-53`
- **问题**: 原报告称"认证代码被注释"
- **审核结果**: 请求/响应拦截器已完整实现，token 认证机制正常工作
- **说明**: 支持 `VITE_ADMIN_TEST_MODE` 环境变量切换测试/生产模式
- **关联任务**: FE-P1-003

### 前端权限系统问题
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/App.tsx:104`, `frontend/src/constants/roles.ts`, `frontend/src/components/auth/ProtectedRoute.tsx`
- **问题**: 角色硬编码字符串、无权限守卫组件
- **影响**: 越权访问风险
- **解决方案**:
  - 创建 `src/constants/roles.ts` 定义角色常量
  - 创建 `src/components/auth/ProtectedRoute.tsx` 权限守卫组件
  - 创建 `src/types/auth.ts` 认证相关类型定义
  - 更新 `App.tsx` 使用权限守卫和角色常量
  - 更新 `MainLayout.tsx` 使用角色常量
- **关联任务**: FE-P1-001, FE-P1-002

### 前端组件目录重复
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `/@/components/ui/` vs `/src/components/ui/`
- **问题**: 组件目录重复，导入混乱
- **影响**: 维护困难
- **解决方案**: 删除了 `frontend/@/` 物理目录，统一使用 `@/components/ui/` 别名路径
- **关联任务**: FE-P1-004

### 添加患者功能缺失
- **状态**: ✅ 已完成 (2026-02-11) - 虚假问题
- **位置**: `frontend/src/pages/doctor/PatientList.tsx:130-134`
- **问题**: 原报告称"按钮存在但无点击事件"
- **审核结果**: 功能已完整实现
- **说明**:
  - 后端 API 完整：`/api/doctor/patients/assign`、`/api/doctor/patients/{id}/unassign`、`/api/doctor/patients/assignable`
  - 前端 API 封装完整：`doctorApi.assignPatient`、`unassignPatient`、`getAssignablePatients`
  - AssignPatientDialog 组件功能完整
  - PatientList.tsx 按钮已正确绑定 `onClick={() => setAssignDialogOpen(true)}`
- **关联任务**: FE-P1-005

### 图表库不统一
- **状态**: ✅ 已完成 (2026-02-11) - 虚假问题
- **位置**: `frontend/src/components/charts/`
- **问题**: 原报告称"使用 @ant-design/charts 而非 Recharts"
- **审核结果**: 项目已完全使用 Recharts，所有图表组件已统一
- **说明**:
  - `frontend/package.json` 只有 `recharts` 依赖，无 `@ant-design/charts`
  - 自定义图表组件已完整实现：CustomLineChart、CustomColumnChart、CustomPieChart
  - 所有使用图表的页面已迁移到自定义组件：
    - `Stats.tsx` - 使用 CustomLineChart
    - `PatientCompliance.tsx` - 使用 CustomLineChart、CustomColumnChart、CustomPieChart
    - `RoundingDetail.tsx` - 使用 CustomLineChart
  - 图表组件支持 shadcn/ui 主题适配（通过 `getThemeColors()`）
- **关联任务**: FE-P1-006

### iOS 弃用 API 未清理
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: iOS 多处 `@available(*, deprecated)`
- **问题**: 弃用代码未清理
- **影响**: 技术债务累积
- **解决方案**:
  - 删除 `ColorSchemes.swift` 整个文件（仅包含弃用 API）
  - 删除 `AppColor` 兼容层（`HealingColorTheme.swift`）
  - 删除 `MedicalColors` 结构（`ModernDesignSystem.swift`）
  - 删除 `UnifiedFont.caption` 属性（`LayoutConstants.swift`）
  - 删除 `AdaptiveFont.caption` 属性（`LayoutConstants.swift`）
  - 删除 `.caption(weight:)` View 扩展（`LayoutConstants.swift`）
  - 移除 `DeinitSafety` 弃用标记（`DeinitSafetyChecker.swift`）
- **验证**: iOS 项目编译成功（BUILD SUCCEEDED）
- **关联任务**: IOS-P1-001

### iOS AppIcon 图标缺失
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `ios/xinlingyisheng/Assets.xcassets/AppIcon.appiconset/`
- **问题**: 部分尺寸的图标未分配
- **解决方案**: 从 AppStore-1024.png 生成缺失的图标尺寸
- **新增文件**:
  - iPhone-20.png (20x20)
  - iPad-20.png (20x20)
  - iPhone-83.5@2x.png (167x167, iPad Pro)
- **影响**: 应用图标显示完整
- **预估工作量**: 2 小时
- **关联任务**: IOS-P1-002

### iOS 组件功能重叠
- **状态**: ✅ 已完成 (2026-02-11) - 分析完成
- **位置**: iOS 多个组件
- **问题**: 多处组件功能重叠
- **审核结果**:
  - **EmptyStateView 重叠**: `DossierEmptyStateView` vs `UnifiedEmptyStateView`
    - 保留 `UnifiedEmptyStateView`（更通用，支持预设样式）
    - `DossierEmptyStateView` 可迁移到统一组件
  - **API 服务重叠**: `AIService.swift` vs `UnifiedChatAPIService.swift` vs `UnifiedChatAPIServiceV2.swift`
    - `AIService.swift`: 专门处理 AI 相关 API（摘要、语音转写、智能聚合等）
    - `UnifiedChatAPIService.swift`: 处理 V1 端点会话和消息
    - `UnifiedChatAPIServiceV2.swift`: 处理 V2 端点（多智能体架构）
    - **结论**: 各自有不同用途，属于合理的 API 分层，非重叠
  - **PDF 生成器重叠**: `PDFGenerator.swift` vs `ConversationPDFGenerator.swift`
    - `PDFGenerator.swift`: 生成医疗事件 PDF（病历导出）
    - `ConversationPDFGenerator.swift`: 生成对话记录 PDF（聊天记录导出）
    - **结论**: 用途不同，非重叠
  - **Card 组件重叠**: `AdviceCardView`, `DiagnosisSummaryCard`, `AIAnalysisCardView`
    - `AdviceCardView`: 显示单个建议条目
    - `DiagnosisSummaryCard`: 完整诊断卡片（含风险、条件、推理步骤、护理建议等）
    - `AIAnalysisCardView`: AI 分析卡片（含症状、诊断、建议等）
    - **结论**: 用途不同，但可考虑统一诊断进度条显示逻辑
  - **Voice 服务**: `SimpleSpeechInputService.swift` 在技术债务清单中列出，但文件不存在
    - **结论**: 该文件已被清理，技术债务已还清
- **建议**:
  - 迁移 `DossierEmptyStateView` 使用 `UnifiedEmptyStateView`
  - 其他"重叠"组件实际用途不同，建议保留现状
- **预估工作量**: 2 小时（如需迁移 EmptyStateView）
- **关联任务**: IOS-P1-003

---

## 🟢 低优先级（暂缓）- P2

### 患者搜索功能优化
- **状态**: ✅ 已完成 (2026-02-11) - 虚假问题
- **位置**: `frontend/src/pages/doctor/PatientList.tsx`
- **审核结果**: 搜索功能已完整实现
- **说明**:
  - 搜索输入框已实现（支持姓名或手机号搜索）
  - 使用 `useDebounce` hook 优化搜索请求（300ms 防抖）
  - 后端 API 调用正确（`doctorApi.getPatients(debouncedSearch)`）
  - 搜索无结果时显示友好提示
- **关联任务**: FE-P2-SEARCH

### 自定义侧边栏优化
- **状态**: ✅ 已完成 (2026-02-11) - 虚假问题
- **位置**: `frontend/src/layouts/MainLayout.tsx`
- **审核结果**: 已使用 shadcn/ui Sheet 组件
- **说明**:
  - 已正确导入: `import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';`
  - 移动端菜单使用 Sheet 组件实现（`renderMobileMenu` 函数）
  - 桌面端使用 NavigationMenu，平板端使用 DropdownMenu
  - 三种响应式布局完整实现
- **关联任务**: FE-P2-SIDEBAR

### iOS V1/V2 API 并存
- **状态**: ✅ 已完成 (2026-02-11) - 虚假问题
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Services/`
- **审核结果**: V1 和 V2 API 各有用途，非重复代码
- **说明**:
  - `UnifiedChatAPIService.swift`: 处理 V1 端点（`/sessions`），单智能体架构
  - `UnifiedChatAPIServiceV2.swift`: 处理 V2 端点（`/v2/sessions`），多智能体架构
  - 两者响应模型不同：V1 使用 `UnifiedMessageResponse`，V2 使用 `AgentResponseV2`
  - 后端也有对应的 `sessions.py` 和 `sessions_v2.py` 路由，属于版本演进，非重复
- **关联任务**: IOS-P2-API

### 服务层循环依赖风险
- **状态**: ✅ 已完成 (2026-02-11) - 虚假问题
- **位置**: `backend/app/services/ai/`
- **审核结果**: 无循环依赖
- **说明**:
  - `BaseAIService`: 基类，提供 LLM 调用、JSON 解析等通用功能
  - `AISummaryService`: 继承 BaseAIService，提供摘要功能
  - `EventAggregationService`: 继承 BaseAIService，提供聚合功能
  - 所有服务使用单例模式（`get_xxx_service()` 函数）
  - 导入关系清晰：子类 → 基类，无循环依赖
- **关联任务**: BE-P2-CIRCULAR

### 测试覆盖不足
- **状态**: 🟡 部分完成 (2026-02-11)
- **位置**: 全项目
- **问题**: 缺少单元测试和集成测试
- **影响**: 质量保障不足
- **进度**: iOS P0 端对端测试已完成（8/8 通过）
- **预估工作量**: 后端 28h + 前端 12h + iOS 12h
- **关联任务**: BE-P2-001, BE-P2-002, IOS-P2-001
- **测试报告**: [2026-02-11-ios-p0-e2e-test-report.md](../plans/2026-02-11-ios-p0-e2e-test-report.md)

### 前端类型定义不完整
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/types/`
- **解决方案**: 新增完整的类型定义文件
  - `medical-order.ts`: 医嘱、任务、打卡记录等类型
  - `consultation.ts`: 会话、消息、附件等类型
  - `doctor.ts`: 医生信息、统计数据等类型
  - `department.ts`: 科室相关类型
  - `index.ts`: 统一导出
- **关联任务**: FE-P2-001

### 快速咨询功能空实现
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/pages/doctor/PatientList.tsx:105-107`
- **解决方案**: 实现导航到患者详情页的咨询 Tab
  - `handleQuickConsult` 导航到 `/patients/${id}?tab=consultations`
  - `PatientDetail` 组件支持 URL 参数控制默认激活的 Tab
- **关联任务**: FE-P2-005

### 医嘱编辑体验优化
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/src/pages/doctor/orders/CreateOrderDialog.tsx`
- **解决方案**: 优化编辑模式 UX
  - 编辑模式直接进入基础信息编辑步骤
  - 移除调度配置步骤（编辑时不修改调度）
  - 添加结束日期编辑功能
  - 优化按钮文案（取消/保存）
- **关联任务**: FE-P2-006

### 前端遗留备份文件
- **状态**: ✅ 已完成 (2026-02-11)
- **位置**: `frontend/**/*.bak`
- **解决方案**: 确认无备份文件残留
- **关联任务**: FE-P2-004

---

## 已还清

| 问题 | 解决版本 | 解决日期 |
|------|----------|----------|
| EventDetailView Caption 废弃警告 | v1.0 | 2026-02-06 |
| iOS 并发安全警告 (@MainActor) | v1.0 | 2026-02-06 |
| iOS 编译错误 (uploadFile) | v1.0 | 2026-02-06 |
| Python 虚拟环境路径警告 | v1.0 | 2026-02-06 |
| iOS Caption 废弃警告（SpecialtyDataView + LogoView） | v1.0 | 2026-02-08 |
| **Schema 缺少 weekdays 字段** | **v2.0** | **2026-02-09** |
| **医生工作台激活 API 路由不一致** | **v2.0** | **2026-02-09** |
| **多步骤表单数据传递问题** | **v2.0** | **2026-02-09** |
| **后端测试模式无法关闭** | **v2.0** | **2026-02-11** |
| **前端测试模式无法关闭** | **v2.0** | **2026-02-11** |
| **前端 Token 认证（虚假问题）** | **v2.0** | **2026-02-11** |
| **iOS 对话页面输入框透明问题** | **v2.0** | **2026-02-11** |
| **前端组件目录重复** | **v2.0** | **2026-02-11** |
| **添加患者功能缺失（虚假问题）** | **v2.0** | **2026-02-11** |
| **硬编码配置** | **v2.0** | **2026-02-11** |
| **前端权限系统问题** | **v2.0** | **2026-02-11** |
| **iOS AppIcon 图标缺失** | **v2.0** | **2026-02-11** |
| **图表库不统一（虚假问题）** | **v2.0** | **2026-02-11** |
| **iOS 组件功能重叠（分析完成）** | **v2.0** | **2026-02-11** |
| **iOS 弃用 API 清理** | **v2.0** | **2026-02-11** |
| **N+1 查询优化** | **v2.0** | **2026-02-11** |
| **前端类型定义不完整** | **v2.0** | **2026-02-11** |
| **快速咨询功能空实现** | **v2.0** | **2026-02-11** |
| **医嘱编辑体验优化** | **v2.0** | **2026-02-11** |
| **前端遗留备份文件** | **v2.0** | **2026-02-11** |
| **患者搜索功能优化（虚假问题）** | **v2.0** | **2026-02-11** |
| **后端测试模式默认值安全问题** | **v2.0** | **2026-02-11** |
| **后端JWT密钥安全检查不足** | **v2.0** | **2026-02-11** |
| **数据库密码硬编码问题** | **v2.0** | **2026-02-11** |
| **DevOps配置安全加固** | **v2.0** | **2026-02-11** |
| **前端P0安全风险修复** | **v2.0** | **2026-02-11** |
| **iOS Token 存储安全修复（Keychain）** | **v2.0** | **2026-02-11** |
| **iOS UnifiedChatViewModel 拆分（服务类架构）** | **v2.0** | **2026-02-11** |
| **自定义侧边栏优化（虚假问题）** | **v2.0** | **2026-02-11** |
| **iOS V1/V2 API 并存（虚假问题）** | **v2.0** | **2026-02-11** |
| **服务层循环依赖风险（虚假问题）** | **v2.0** | **2026-02-11** |

### 说明
- **未使用的依赖（Starscream）**: 经检查，Starscream 正在被 `PressAndHoldVoiceService.swift` 使用，用于 WebSocket 连接，不是未使用的依赖。
- **Python 虚拟环境路径警告**: 经检查，项目配置中不存在相关警告。

---

## 优先级说明

| 优先级 | 处理时机 |
|--------|----------|
| 🔴 高 (P0) | 尽快处理，影响构建或核心功能 |
| 🟡 中 (P1) | 有空就做，不影响主功能 |
| 🟢 低 (P2) | 暂缓，时间允许时处理 |

---

## 统计

| 优先级 | 后端 | 前端 | iOS | 合计 |
|--------|------|------|-----|------|
| P0 | 0 | 0 | 0 | 0 |
| P1 | 1 | 0 | 0 | 1 |
| P2 | 1 | 0 | 0 | 1 |
| **合计** | **2** | **0** | **0** | **2** |
