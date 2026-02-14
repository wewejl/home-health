# iOS 架构设计文档

> **项目名称**: 鑫琳医生（灵犀健康）
> **平台**: iOS 17.0+
> **语言**: Swift
> **UI 框架**: SwiftUI
> **架构模式**: MVVM + Coordinator
> **更新日期**: 2026-02-14

> **⚠️ 重要说明**: 当前项目处于架构迁移阶段，新架构（Core/Features/Shared）与旧架构（Components/ViewModels/Models/等）并存。**编译时存在文件重复错误**，需要清理旧架构文件后才能正常编译。详见 [迁移状态](#迁移状态) 章节。

---

## 目录

1. [架构概览](#架构概览)
2. [Core 核心层](#core-核心层)
3. [Features 功能层](#features-功能层)
4. [Shared 共享层](#shared-共享层)
5. [设计原则](#设计原则)
6. [模块依赖关系](#模块依赖关系)

---

## 架构概览

### 整体结构

```
ios/xinlingyisheng/
├── Core/                    # 核心基础层
│   ├── Base/               # 基础组件
│   ├── Components/         # 共享 UI 组件
│   ├── Config/             # 配置管理
│   ├── Error/              # 错误处理
│   ├── Routing/            # 路由管理
│   └── Theme/              # 主题系统
│
├── Features/               # 功能模块层
│   ├── Auth/               # 认证功能
│   ├── Consultation/       # 咨询功能
│   ├── Knowledge/          # 知识库
│   ├── Medical/            # 医疗功能
│   └── Profile/            # 个人中心
│
└── Shared/                 # 共享资源层
    └── Resources/          # 共享资源
```

### 架构分层

```
┌─────────────────────────────────────────────────────┐
│                   Features Layer                     │
│  (业务功能模块：Auth、Consultation、Medical...)       │
└─────────────────────────────────────────────────────┘
                         ↓ 依赖
┌─────────────────────────────────────────────────────┐
│                    Core Layer                        │
│  (基础组件、UI 组件、配置、路由、主题、错误处理)       │
└─────────────────────────────────────────────────────┘
                         ↓ 依赖
┌─────────────────────────────────────────────────────┐
│                   Shared Layer                       │
│              (共享资源、通用工具)                     │
└─────────────────────────────────────────────────────┘
```

---

## Core 核心层

### Base/ - 基础组件

#### BaseView.swift

所有 View 的基础协议，提供统一的视图能力。

```swift
protocol BaseView: View {
    associatedtype EmptyViewContent: View

    func emptyView() -> EmptyViewContent
}

// 扩展方法
- hideKeyboard()          // 隐藏键盘
- ifShow(_ condition: Bool)    // 条件显示
- ifHide(_ condition: Bool)    // 条件隐藏
```

#### BaseViewModel.swift

所有 ViewModel 的基类，提供统一的状态管理。

```swift
class BaseViewModel: ObservableObject {
    // 核心状态
    @Published var isLoading: Bool = false
    @Published var isRefreshing: Bool = false
    @Published var error: AppError?

    // 加载管理
    func startLoading()
    func stopLoading()
    func setError(_ error: AppError)
    func clearError()
}
```

---

### Components/ - 共享 UI 组件

#### AppButton.swift

统一按钮组件，支持多种样式和尺寸。

**按钮类型**:
| 类型 | 用途 |
|------|------|
| `primary` | 主要操作按钮 |
| `secondary` | 次要操作按钮 |
| `tertiary` | 第三级按钮 |
| `danger` | 危险操作（删除等） |
| `success` | 成功操作 |

**按钮尺寸**:
| 尺寸 | 高度 |
|------|------|
| `small` | 32pt |
| `medium` | 40pt |
| `large` | 48pt |

**使用示例**:
```swift
AppButton("登录", style: .primary, size: .large) {
    viewModel.login()
}
```

#### 其他组件

| 组件 | 作用 |
|------|------|
| `AppLoadingView` | 统一加载视图 |
| `AppCard` | 卡片容器 |
| `AppTextField` | 文本输入框 |
| `AppSheet` | 抽屉弹窗 |

---

### Config/ - 配置管理

#### AppConfig.swift

集中式配置管理，单例模式。

```swift
struct AppConfig {
    // API 配置
    static let apiBaseURL = "http://localhost:8100"
    static let apiTimeout: TimeInterval = 30
    static let apiMaxRetries = 3

    // 应用设置
    static let appName = "灵犀健康"
    static let appVersion = "1.0.0"

    // 功能开关
    static let isDebug: Bool = { /* 编译时判断 */ }()
    static let isTestMode: Bool = false
    static let isLoggingEnabled: Bool = true

    // 存储键
    static let keyAccessToken = "app_access_token"
}
```

---

### Error/ - 错误处理

#### AppError.swift

统一错误类型定义。

```swift
enum AppError: LocalizedError {
    // 网络错误
    case networkRequestFailed(String)
    case networkTimeout
    case noNetworkConnection
    case serverError(statusCode: Int, message: String?)

    // 认证错误
    case notAuthenticated
    case tokenExpire
    case loginFailed(String)

    // 数据错误
    case dataParsingFailed
    case emptyData
    case noDataFound

    // 用户输入错误
    case invalidInput(String)
    case invalidPhoneFormat
    case invalidVerificationCode

    // 存储错误
    case storageFailed(String)
    case readFailed(String)
}
```

#### ErrorHandler.swift

单例错误处理器，统一错误显示管理。

```swift
class ErrorHandler: ObservableObject {
    static let shared = ErrorHandler()

    @Published var currentError: AppError?
    private var hideTask: Task<Void, Never>?

    func show(_ error: AppError) {
        // 显示错误，3秒后自动隐藏
    }
}
```

View 扩展：
```swift
extension View {
    func onError() -> some View {
        // 绑定错误处理器
    }
}
```

---

### Routing/ - 路由管理

#### AppRouter.swift

类型安全的路由系统。

```swift
enum AppRouter: Identifiable {
    case home
    case askDoctor
    case consultations
    case medicalDossier
    case knowledge
    case profile
    case settings
}

// 导航方法
func navigate(to route: AppRouter)
func navigationPath(to route: AppRouter) -> NavigationPath
func presentSheet<Content: View>(route: AppRouter, content: Content)
func showAlert(title: String, message: String)
```

---

### Theme/ - 主题系统

#### AppColors.swift

治愈系配色方案，温暖自然的设计语言。

```swift
struct AppColors {
    // 主品牌色 - 鼠尾草绿
    static let primary = Color(red: 0xB5/255, green: 0xD1/255, blue: 0xC2/255)

    // 语义化颜色
    static let success = Color(red: 0x4D/255, green: 0xB8/255, blue: 0x85/255)
    static let warning = Color(red: 0xF5/255, green: 0xA6/255, blue: 0x23/255)
    static let error = Color(red: 0xD9/255, green: 0x59/255, blue: 0x59/255)

    // 中性色
    static let background = Color(red: 0xF7/255, green: 0xF2/255, blue: 0xE8/255)
    static let cardBackground = Color.white
    static let textPrimary = Color(red: 0x1C/255, green: 0x1C/255, blue: 0x1E/255)
    static let textSecondary = Color(red: 0x6B/255, green: 0x72/255, blue: 0x80/255)
}
```

#### AppSpacing.swift

基于 4pt 的间距系统。

```swift
struct AppSpacing {
    static let micro: CGFloat = 2    // 0.5x
    static let tiny: CGFloat = 4      // 1x
    static let small: CGFloat = 6     // 1.5x
    static let compact: CGFloat = 8   // 2x
    static let medium: CGFloat = 12   // 3x
    static let standard: CGFloat = 16 // 4x
    static let large: CGFloat = 24    // 6x
    static let xLarge: CGFloat = 32    // 8x
}
```

---

## Features 功能层

### Auth/ - 认证功能

#### 目录结构

```
Auth/
├── ViewModels/
│   └── LoginViewModel.swift      # 登录逻辑
├── Views/
│   ├── SplashView.swift          # 启动页
│   ├── LoginView.swift           # 登录页
│   └── ProfileSetupView.swift    # 资料设置
└── Services/
    └── KeychainManager.swift     # 安全存储
```

#### LoginViewModel

**状态管理**:
```swift
enum LoginStep {
    case phoneInput     // 手机号输入
    case codeInput      // 验证码输入
}

enum LoginUIState: Equatable {
    case idle
    case sendingCode
    case codeSent
    case loggingIn
    case success
    case error(LoginErrorState)
}
```

**核心方法**:
- `sendVerificationCode()` - 发送验证码
- `verifyAndLogin()` - 验证并登录
- `autoLogin()` - 自动登录

---

### Consultation/ - 咨询功能

#### 目录结构

```
Consultation/
├── ViewModels/
│   ├── UnifiedChatViewModel.swift      # 统一聊天 VM
│   ├── VoiceInputViewModel.swift       # 语音输入
│   └── VoiceTranscriptionViewModel.swift # 语音转写
├── Views/
│   ├── ModernConsultationView.swift    # 现代咨询页
│   ├── AskDoctorView.swift            # 问医生页
│   ├── SessionHistoryView.swift        # 会话历史
│   └── MyQuestionsView.swift           # 我的问题
└── Services/
    ├── UnifiedChatAPIService.swift      # 统一 API
    ├── ChatSessionService.swift         # 会话服务
    ├── ChatMessageService.swift         # 消息服务
    └── SessionStateManager.swift        # 状态管理
```

#### UnifiedChatViewModel 架构

**服务分离**:
```swift
private let sessionService: ChatSessionService      // 会话管理
private let messageService: ChatMessageService      // 消息管理
private let voiceService: ChatVoiceInputService     // 语音处理
```

**流式输出支持**:
```swift
@Published var streamingContent = ""        // 流式内容
@Published var isStreaming = false          // 流式状态
```

---

### Knowledge/ - 知识库功能

#### 目录结构

```
Knowledge/
├── Disease/
│   └── Views/
│       ├── DiseaseListView.swift       # 疾病列表
│       ├── DiseaseDetailView.swift     # 疾病详情
│       └── DepartmentDetailView.swift  # 科室详情
└── Drug/
    └── Views/
        ├── DrugListView.swift          # 药品列表
        └── DrugDetailView.swift        # 药品详情
```

---

### Medical/ - 医疗功能

#### 目录结构

```
Medical/
├── Dossier/
│   ├── ViewModels/
│   │   ├── MedicalDossierViewModel.swift
│   │   └── MedicalFolderViewModel.swift
│   ├── Services/
│   │   ├── MedicalEventAPIService.swift
│   │   └── PDFGenerator.swift
│   └── Views/
└── Orders/
    └── ViewModels/
        └── MedicalOrderViewModel.swift
```

#### MedicalEventAPIService

**DTO 设计**:
```swift
struct MedicalEventDTO: Decodable, Identifiable {
    let id: Int
    let title: String
    let department: String
    let date: String
    // ...
}
```

---

### Profile/ - 个人中心

#### 目录结构

```
Profile/
├── Views/
│   └── ProfileView.swift
└── Services/
    └── ProfileService.swift
```

---

## Shared 共享层

### Resources/ - 共享资源

```
Shared/Resources/
└── Assets/
    └── (预留位置，用于放置跨模块共享的资源)
```

**未来可扩展**:
- 通用工具类
- 共享的数据模型
- 跨模块的常量定义

---

## 设计原则

### 1. 模块化设计

每个功能模块独立封装，清晰的职责边界。

### 2. 依赖注入

通过构造函数注入依赖，便于测试和解耦。

```swift
init(sessionService: ChatSessionService,
     messageService: ChatMessageService) {
    self.sessionService = sessionService
    self.messageService = messageService
}
```

### 3. 服务层抽象

业务逻辑封装在 Service 层，ViewModel 只负责状态管理。

### 4. 响应式编程

使用 Combine 框架实现数据流管理。

```swift
@Published var messages: [UnifiedChatMessage] = []
```

### 5. 类型安全

使用枚举定义路由和错误类型，避免字符串硬编码。

### 6. 主线程安全

使用 `@MainActor` 确保 UI 更新在主线程。

```swift
@MainActor
class LoginViewModel: ObservableObject {
    // UI 相关代码
}
```

---

## 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                         Features                              │
│  ┌──────┐  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌────────┐ │
│  │ Auth │  │Consultation│ │ Knowledge│ │Medical│ │ Profile │ │
│  └───┬──┘  └─────┬────┘  └─────┬────┘  └───┬──┘  └────┬───┘ │
│      │          │             │           │           │     │
└──────┼──────────┼─────────────┼───────────┼───────────┼─────┘
       ↓          ↓             ↓           ↓           ↓
┌─────────────────────────────────────────────────────────────┐
│                          Core                                 │
│  ┌──────┐ ┌──────────┐ ┌───────┐ ┌────┐ ┌────┐ ┌─────────┐  │
│  │ Base │ │Components│ │ Config│ │Error│ │Route│ │  Theme  │  │
│  └──────┘ └──────────┘ └───────┘ └────┘ └────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                         Shared                                │
│                     ┌─────────────┐                          │
│                     │  Resources  │                          │
│                     └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 特色亮点

### 治愈系设计语言

- **配色**: 温暖的鼠尾草绿为主色调
- **间距**: 统一的 4pt 栅格系统
- **动画**: 流畅的过渡效果

### 智能化功能

- **语音识别**: 按住说话，实时转写
- **图片分析**: 皮肤、报告、心电图智能分析
- **流式输出**: 实时显示 AI 回复

### 安全性设计

- **Keychain 存储**: 敏感信息安全保存
- **自动降级**: Keychain 失败时降级到 UserDefaults
- **会话管理**: 完整的会话生命周期管理

### 性能优化

- **懒加载**: 按需加载资源
- **异步处理**: 避免阻塞主线程
- **内存管理**: 及时清理资源

---

## 迁移状态

### 当前问题

项目处于 **架构迁移阶段**，新旧架构并存：

| 状态 | 目录 | 说明 |
|------|------|------|
| ✅ 新架构 | `Core/`, `Features/`, `Shared/` | 已创建并填充代码 |
| ⚠️ 旧架构 | `Components/`, `ViewModels/`, `Models/`, `Services/`, `Views/` | 仍存在且在 Xcode 项目中 |

### 编译错误

**当前无法编译**，原因：
- 同一个 Swift 文件在 Xcode 项目中被添加了两次（旧路径 + 新路径）
- 例如：`LoginViewModel.swift` 同时存在于 `xinlingyisheng/ViewModels/` 和 `xinlingyisheng/Features/Auth/ViewModels/`

### 解决方案

需要从 Xcode 项目中移除旧架构文件的引用，或删除旧目录：

```bash
# 方案 1: 删除旧目录（谨慎操作，先备份）
# rm -rf xinlingyisheng/Components
# rm -rf xinlingyisheng/ViewModels
# rm -rf xinlingyisheng/Models
# rm -rf xinlingyisheng/Services
# rm -rf xinlingyisheng/Views
# rm -rf xinlingyisheng/Utils
# rm -rf xinlingyisheng/Theme

# 方案 2: 使用 Xcode 移除引用（推荐）
# 在 Xcode 中选中旧文件 → Move to Trash
```

### 迁移清单

| 模块 | 新路径 | 旧路径 | 状态 |
|------|--------|--------|------|
| 基础组件 | `Core/Base/` | - | ✅ 完成 |
| UI 组件 | `Core/Components/` | `Components/` | ⚠️ 重复 |
| 配置 | `Core/Config/` | - | ✅ 完成 |
| 错误处理 | `Core/Error/` | - | ✅ 完成 |
| 路由 | `Core/Routing/` | - | ✅ 完成 |
| 主题 | `Core/Theme/` | `Theme/` | ⚠️ 重复 |
| 认证 | `Features/Auth/` | `Views/LoginView.swift` 等 | ⚠️ 重复 |
| 咨询 | `Features/Consultation/` | `Views/` 中相关文件 | ⚠️ 重复 |
| 知识库 | `Features/Knowledge/` | `Views/` 中相关文件 | ⚠️ 重复 |
| 医疗 | `Features/Medical/` | `Views/MedicalDossier/` 等 | ⚠️ 重复 |
| 个人中心 | `Features/Profile/` | `Views/ProfileView.swift` 等 | ⚠️ 重复 |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-02-14 | 新架构重构完成（但存在旧架构残留） |

---

## 参考资料

- [SwiftUI 官方文档](https://developer.apple.com/documentation/swiftui)
- [Combine 框架](https://developer.apple.com/documentation/combine)
- [iOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
