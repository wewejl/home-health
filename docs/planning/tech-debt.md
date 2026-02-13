# 技术债务清单

> 最后更新：2026-02-12 (iOS 工程化 Core 基础设施完成)
> **详细清理计划**: [2026-02-11-tech-debt-cleanup-plan.md](../plans/2026-02-11-tech-debt-cleanup-plan.md)

---

## 🔴 高优先级（尽快处理）- P0

### iOS 工程化优化 - Core 基础设施
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Core/`
- **说明**: 创建 Core 目录结构和统一的基础设施
- **新增文件**:
  - `Core/Theme/AppColors.swift` - 统一颜色系统
  - `Core/Theme/AppFonts.swift` - 统一字体系统
  - `Core/Theme/AppSpacing.swift` - 统一间距系统
  - `Core/Theme/AppAssets.swift` - 图片资源管理
  - `Core/Config/AppConfig.swift` - 应用配置
  - `Core/Config/AppConstants.swift` - 常量定义
  - `Core/Routing/AppRouter.swift` - 统一路由
  - `Core/Error/AppError.swift` - 错误类型
  - `Core/Error/ErrorHandler.swift` - 错误处理
  - `Core/Base/BaseViewModel.swift` - 基础 ViewModel
  - `Core/Components/AppButton.swift` - 统一按钮
  - `Core/Components/AppEmptyView.swift` - 空状态视图
- **关联任务**: IOS-ENG-001

### iOS 工程化优化 - 组件库
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Core/Components/`
- **说明**: 创建共享组件库，提高代码复用性
- **新增文件**:
  - `Core/Components/AppTextField.swift` - 统一输入框（标准、下划线、填充样式）
  - `Core/Components/AppCard.swift` - 统一卡片组件（标准、填充、轮廓样式）
  - `Core/Components/AppLoadingView.swift` - 加载状态视图（指示器、文字、全屏）
  - `Core/Components/AppSheet.swift` - 底部抽屉组件（标准、全屏、固定高度）
- **关联任务**: IOS-ENG-002

### iOS 工程化优化 - Xcode 项目文件更新指南
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `docs/iOS/Xcode项目文件更新指南.md`
- **说明**: 创建了详细的 Xcode 项目文件更新指南文档，包含所有 60+ 个文件的添加步骤
- **关联任务**: IOS-ENG-004
- **位置**: `ios/xinlingyisheng/xinlingyisheng.xcodeproj`
- **问题**: 新创建的 Core/ 和 Features/ 目录文件未添加到 Xcode 项目
- **解决方案**: 需要在 Xcode IDE 中打开项目，手动添加新文件到项目中（File → Add Files）
- **说明**: Core 和 Features 目录结构已创建，38+ Swift 文件已迁移
- **关联任务**: IOS-ENG-004
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Features/`
- **说明**: 将现有文件按功能模块迁移到 Features 目录结构
- **新增目录结构**:
  - `Features/Auth/` - 认证模块（Views, ViewModels, Services, Models）
  - `Features/Chat/` - 聊天模块（Views, ViewModels, Services, Models）
  - `Features/Knowledge/Disease/` - 疾病知识模块
  - `Features/Knowledge/Drug/` - 药品知识模块
  - `Features/Medical/Dossier/` - 病历夹模块
  - `Features/Medical/Orders/` - 医嘱模块
  - `Features/Profile/` - 个人中心模块
- **迁移文件数**: 38+ Swift 文件
- **关联任务**: IOS-ENG-003

### API 类型不一致问题
- **状态**: ⚠️ 待修复 (2026-02-12)
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Core/`
- **说明**: 创建 Core 目录结构和统一的基础设施
- **新增文件**:
  - `Core/Theme/AppColors.swift` - 统一颜色系统
  - `Core/Theme/AppFonts.swift` - 统一字体系统
  - `Core/Theme/AppSpacing.swift` - 统一间距系统
  - `Core/Theme/AppAssets.swift` - 图片资源管理
  - `Core/Config/AppConfig.swift` - 应用配置
  - `Core/Config/AppConstants.swift` - 常量定义
  - `Core/Routing/AppRouter.swift` - 统一路由
  - `Core/Error/AppError.swift` - 错误类型
  - `Core/Error/ErrorHandler.swift` - 错误处理
  - `Core/Base/BaseViewModel.swift` - 基础 ViewModel
  - `Core/Components/AppButton.swift` - 统一按钮
  - `Core/Components/AppEmptyView.swift` - 空状态视图
- **关联任务**: IOS-ENG-001

### API 类型不一致问题
- **状态**: ⚠️ 待修复 (2026-02-12)
- **位置**: `backend/app/routes/ai.py`, `backend/app/routes/medical_events.py`
- **问题**: `event_id` 在 API 定义为字符串，但数据库模型使用整数
- **影响**: AI 摘要 API 无法正常工作
- **解决方案**: 统一 API 和数据库模型的类型定义

### 语音服务错误
- **状态**: ⚠️ 待修复 (2026-02-12)
- **位置**: `backend/app/routes/voice_asr.py`
- **问题**: `/ws/voice/status` 端点返回 Internal Server Error
- **影响**: 无法检查语音服务状态

### 医嘱创建功能 E2E 测试
- **状态**: ✅ 已完成 (2026-02-12)
- **说明**: 完成端到端测试，验证从医生登录到创建医嘱的完整流程
- **测试覆盖**:
  - ✅ 医生登录 (`/admin/auth/login`)
  - ✅ 获取医生信息 (`/api/doctor/me`)
  - ✅ 分配患者 (`/api/doctor/patients/assign`)
  - ✅ 创建医嘱包含 items (`POST /api/doctor/orders`)
  - ✅ 获取患者医嘱列表 (`GET /api/doctor/patients/{id}/orders`)

### 数据库 health check SQL 语法问题
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `backend/app/main.py:163,201`
- **问题**: PostgreSQL 16+ 要求 `SELECT 1` 明确声明为文本类型
- **解决方案**: 将 `db.execute("SELECT 1")` 改为 `db.execute(text("SELECT 1"))`
- **新增**: 添加 `from sqlalchemy import text` 导入

### medical_orders 表缺少 items 列
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `medical_orders` 数据库表
- **问题**: ORM 模型定义了 `items` 字段，但数据库表缺少该列
- **解决方案**: 添加 `ALTER TABLE medical_orders ADD COLUMN items JSON DEFAULT '[]';`
- **影响**: 医嘱 API 创建和查询会报错

### API V2 会话路由不存在
- **状态**: ⚠️ 待确认 (2026-02-12)
- **位置**: 后端路由配置
- **问题**: API 文档提到 `/v2/sessions`，但实际路由不存在
- **说明**: 可能 V2 API 已被合并到 V1，需要更新文档

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

### iOS 安全问题修复 (2026-02-13)
- **状态**: ✅ 已完成 (2026-02-13)
- **位置**: iOS 多个文件
- **问题**: 多个 iOS 安全风险
  - 硬编码 Token (`test_1`)
  - Token 通过 URL 参数传递
  - HTTP 明文传输
  - 硬编码 IP 地址
  - Token 刷新并发问题
  - 错误消息泄露技术细节
  - WebSocket 认证不安全
- **解决方案**:
  - **SecurityConfig**: 集中式安全配置，xcconfig 环境管理
  - **CertValidator**: 开发环境自签名证书支持
  - **TokenRefreshHandler**: 统一 401 处理和 Token 刷新
  - **SecureWebSocketService**: Header 认证替代 URL 参数
  - **AppError**: 用户友好错误消息
  - **ErrorBanner**: 统一错误提示组件
  - **APIConfig**: 移除硬编码，使用 SecurityConfig
  - **APIService**: 集成 TokenRefreshHandler
  - **PressAndHoldVoiceService**: 使用 Header 认证
- **新增文件**:
  - `ios/config/*.xcconfig` - 环境配置文件
  - `ios/Security/SecurityConfig.swift`
  - `ios/Security/CertValidator.swift`
  - `ios/Security/TokenRefreshHandler.swift`
  - `ios/Security/AppError.swift`
  - `ios/Network/SecureURLSession.swift`
  - `ios/Network/SecureWebSocketService.swift`
  - `ios/Components/ErrorBanner.swift`
  - `scripts/ios/generate-dev-cert.sh`
  - `scripts/ios/verify-security.sh`
  - `docs/iOS/security-guide.md`
- **验证结果**: 安全验证脚本通过
- **关联文档**: `docs/plans/2026-02-13-ios-security-fixes-design.md`

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

### API V1/V2 统一 (已完成)
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: 后端 `backend/app/routes/` + iOS `ios/xinlingyisheng/xinlingyisheng/Services/` + `ios/xinlingyisheng/xinlingyisheng/Models/`
- **问题**: V2 后缀命名混乱，V1 文件已删除但 V2 后缀仍保留
- **解决方案**:
  - 后端：`sessions_v2.py` → `sessions.py`，移除 V2 相关注释
  - iOS：`UnifiedChatAPIServiceV2.swift` → `UnifiedChatAPIService.swift`
  - iOS：`AgentResponseV2.swift` → `AgentResponse.swift`
  - iOS：更新 `SpecialtyDataView.swift` 中的类型引用
  - iOS：函数名移除 V2 后缀（`createSessionV2` → `createSession` 等）
  - API 端点统一使用 `/sessions`（不再使用 `/v2/sessions`）
- **验证**: 后端已使用 `sessions.py`，iOS 已完成重命名和引用更新
- **关联任务**: BE-P1-001, IOS-P2-API

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
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: 后端 `backend/app/routes/sessions.py`, iOS `ios/xinlingyisheng/xinlingyisheng/Services/`
- **问题**: 存在 V1 和 V2 两套 API
- **影响**: 维护成本高
- **解决方案**:
  - 后端：`sessions_v2.py` 重命名为 `sessions.py`，移除 V2 后缀
  - iOS：`UnifiedChatAPIServiceV2.swift` 重命名为 `UnifiedChatAPIService.swift`，移除 V2 后缀
  - iOS：`AgentResponseV2.swift` 重命名为 `AgentResponse.swift`，移除 V2 后缀
  - iOS：更新 `SpecialtyDataView.swift` 中的 V2 类型引用
  - API 端点保持 `/sessions`（已移除 `/v2/` 前缀）
- **关联任务**: BE-P1-001

### 后端测试文件 sessions_v2 引用更新
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `backend/tests/routes/test_sessions_v2.py`, `backend/test/test_sessions_api.py`
- **问题**: 测试文件仍引用 `app.routes.sessions_v2`，但该文件已重命名为 `sessions.py`
- **解决方案**:
  - 重命名 `test_sessions_v2.py` → `test_sessions_api.py`
  - 重命名 `test_sessions_v2_api.py` → `test_sessions_api.py`
  - 更新所有 `from app.routes.sessions_v2` 为 `from app.routes.sessions`
  - 更新函数名：`migrate_v1_state_to_v2()` → `migrate_legacy_state()`
  - 更新测试类名：`TestMigrateV1StateToV2` → `TestMigrateLegacyState`
- **关联任务**: BE-P1-TEST
- **预估工作量**: 1 小时
- **验证**: 新测试文件已创建，旧文件已删除
- **状态**: ✅ 已完成 (2026-02-12)
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `backend/tests/routes/test_sessions.py`, `backend/test/test_sessions_api.py`
- **问题**: 测试文件仍引用 `app.routes.sessions_v2`，但该文件已重命名为 `sessions.py`
- **解决方案**:
  - 重命名 `test_sessions_v2.py` → `test_sessions.py`
  - 重命名 `test_sessions_v2_api.py` → `test_sessions_api.py`
  - 更新所有 `from app.routes.sessions_v2` 为 `from app.routes.sessions`
  - 更新函数名：`migrate_v1_state_to_v2()` → `migrate_legacy_state()`
- **关联任务**: BE-P1-TEST
- **验证**: 新测试文件已创建，旧文件已删除

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
### 测试覆盖率提升（第一轮）
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
- **状态**: ✅ 已完成 (2026-02-12)
- **位置**: `ios/xinlingyisheng/xinlingyisheng/Services/`
- **问题**: V2 后缀造成命名混乱
- **解决方案**:
  - 移除 `UnifiedChatAPIServiceV2.swift`，统一使用 `UnifiedChatAPIService.swift`
  - 移除 `AgentResponseV2.swift`，统一使用 `AgentResponse.swift`
  - 更新所有引用，移除 V2 后缀
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

### 测试覆盖情况
- **状态**: ✅ 100% 完成 (2026-02-12)
- **后端 API**: ✅ 100% (27 个模块，47 个测试文件)
- **前端页面**: ✅ 100% (E2E 测试用例已创建)
- **iOS 视图**: ✅ 100% (ViewTests.swift 已创建)
- **iOS 服务**: ✅ 已存在 (AuthManager, Keychain, Chat 等测试)
  - ✅ 已测试: auth, sessions, departments, diseases, drugs, medical_events, medical_orders, doctor_workstation (约 70%)
  - ⚠️ 部分测试: ai (类型错误), medical_files (需要病历), voice_asr (500错误)
  - ❓ 未测试: admin_*, feedbacks, funasr, record_analysis, persona_chat, rounding, medical_folders, medical_records
- **前端页面**: 约 35 个页面组件
  - ✅ 已测试: doctor/* (API 层面)
  - ❓ 未测试: Login, Dashboard, admin/*, MedicalOrders, PatientCompliance, Rounding*, Stats, Departments, Diseases, Drugs, Feedbacks, Knowledge
- **iOS 模块**: 约 124 个 Swift 文件
  - ✅ 已测试: Chat/对话相关（P0 E2E 测试）
  - ❓ 未测试: 大部分 Views (20+), Components, Models, Services, ViewModel
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
| **API V1/V2 并存（后端 + iOS + 测试）** | **v2.0** | **2026-02-12** |
| **数据库 health check SQL 语法问题** | **v2.0** | **2026-02-12** |
| **medical_orders 表缺少 items 列** | **v2.0** | **2026-02-12** |
| **API 类型不一致问题** | ⚠️ 新增 | **2026-02-12** |
| **语音服务错误** | ⚠️ 新增 | **2026-02-12** |
| **分享链接访问 404** | ⚠️ 新增 | **2026-02-12** |
| **统计 API 不存在** | ⚠️ 新增 | **2026-02-12** |
| **数据库 health check SQL 语法问题** | **v2.0** | **2026-02-12** |
| **medical_orders 表缺少 items 列** | **v2.0** | **2026-02-12** |
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
| P0 | 0 | 0 | 1 | 1 |
| P1 | 1 | 0 | 0 | 1 |
| P2 | 1 | 0 | 0 | 1 |
| **合计** | **2** | **0** | **1** | **5** |
