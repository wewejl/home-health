# 灵犀健康 iOS - 工程化优化方案

> **创建日期**: 2026-02-12
> **目标**: 项目工程化、代码规范化、提升可维护性
> **原则**: 改动可以大，但要让项目结构更清晰、更规范

---

## 一、项目工程化目标

### 1.1 当前问题

1. **目录结构不够清晰** - 文件分散，命名不一致
2. **命名不规范** - xinlingyisheng 拼写错误
3. **资源管理分散** - 图片、颜色、常量散落各处
4. **缺少统一配置** - 环境配置、API 地址硬编码
5. **缺少路由管理** - 导航跳转硬编码字符串
6. **缺少统一错误处理** - 错误处理散落各处
7. **缺少文档注释** - 复杂逻辑缺乏说明

### 1.2 工程化目标

| 目标 | 说明 |
|------|------|
| **目录结构标准化** | 按功能模块组织代码 |
| **命名规范统一** | 修正拼写，统一命名风格 |
| **资源集中管理** | 颜色、字体、图片、常量统一管理 |
| **配置文件化** | 环境配置、API 地址等集中管理 |
| **路由统一管理** | 使用 enum 管理所有路由 |
| **错误处理统一** | 统一的错误类型和处理机制 |
| **代码文档化** | 公共接口添加文档注释 |

---

## 二、目录结构重构

### 2.1 当前结构问题

```
ios/xinlingyisheng/xinlingyisheng/
├── 100+ 个 Swift 文件散落各处
├── 拼写错误: xinlingyisheng → 应为 xinlingyisheng
├── Components/ 和 Views/ 混在一起
└── 缺少明确的模块划分
```

### 2.2 目标结构

```
ios/xinlingyisheng/xinlingyisheng/
│
├── Core/                    # 核心层（不依赖业务）
│   ├── Base/
│   │   ├── BaseController.swift      # 基础控制器
│   │   ├── BaseViewModel.swift        # 基础 ViewModel
│   │   └── BaseView.swift            # 基础 View
│   ├── Config/
│   │   ├── AppConfig.swift            # 应用配置
│   │   ├── APIConfig.swift            # API 配置
│   │   └── BuildConfig.swift           # 构建配置
│   ├── Theme/
│   │   ├── AppColors.swift             # 统一颜色
│   │   ├── AppFonts.swift              # 统一字体
│   │   ├── AppSpacing.swift            # 统一间距
│   │   └── AppAssets.swift             # 图片资源
│   ├── Utils/
│   │   ├── Logger.swift                # 日志工具
│   │   ├── Extensions/                # 扩展集合
│   │   └── Constants.swift             # 常量定义
│   └── Network/
│       ├── NetworkError.swift            # 网络错误定义
│       ├── NetworkService.swift          # 网络服务基类
│       └── APIClient.swift              # API 客户端
│
├── Features/              # 功能模块（按业务划分）
│   ├── Auth/                        # 认证模块
│   │   ├── Views/
│   │   │   ├── LoginView.swift
│   │   │   └── ProfileSetupView.swift
│   │   ├── ViewModels/
│   │   │   └── LoginViewModel.swift
│   │   └── Services/
│   │       └── AuthService.swift
│   │
│   ├── Chat/                        # 聊天模块
│   │   ├── Views/
│   │   │   ├── ConsultationView.swift
│   │   │   └── SessionHistoryView.swift
│   │   ├── ViewModels/
│   │   │   └── ChatViewModel.swift
│   │   └── Services/
│   │       ├── ChatSessionService.swift
│   │       ├── ChatMessageService.swift
│   │       └── ChatVoiceService.swift
│   │
│   ├── Medical/                      # 医疗模块
│   │   ├── Dossier/                 # 病历夹
│   │   │   ├── Views/
│   │   │   ├── Orders/               # 医嘱
│   │   │   └── Models/
│   │
│   ├── Knowledge/                    # 知识库模块
│   │   ├── Disease/
│   │   │   ├── Views/
│   │   │   ├── ViewModels/
│   │   │   └── Models/
│   │   └── Drug/
│   │       ├── Views/
│   │       ├── ViewModels/
│   │       └── Models/
│   │
│   └── Profile/                     # 个人中心
│       ├── Views/
│       ├── ViewModels/
│       └── Services/
│
├── Shared/                # 共享组件（跨模块复用）
│   ├── Components/          # 通用组件
│   │   ├── Buttons/
│   │   ├── Inputs/
│   │   ├── Cards/
│   │   ├── Lists/
│   │   └── Loaders/
│   └── Resources/           # 共享资源
│
├── Resources/              # 资源文件
│   ├── Assets.xcassets      # 图片资源
│   └── Localization/       # 多语言
│       ├── en.lproj
│       └── zh-Hans.lproj
│
└── Supporting/             # 支持文件
    ├── AppDelegate.swift
    ├── SceneDelegate.swift
    ├── Info.plist
    └── Entitlements.plist
```

### 2.3 迁移清单

| 原路径 | 目标路径 | 文件数量 |
|---------|----------|----------|
| Views/ → Features/ | ~30 个文件 |
| ViewModels/ → Features/ | ~8 个文件 |
| Services/ → Features/ | ~20 个文件 |
| Models/ → Features/ | ~15 个文件 |
| Components/ → Shared/Components | ~25 个文件 |
| Theme/ → Core/Theme | ~5 个文件 |

---

## 三、命名规范统一

### 3.1 修正项目名称拼写

```bash
# 项目重命名
xinlingyisheng → xinlingyisheng  # 修正拼写
```

### 3.2 文件命名规范

| 规则 | 示例 |
|------|------|
| View 文件以 `View` 结尾 | `LoginView.swift` ✅ |
| ViewModel 文件以 `ViewModel` 结尾 | `LoginViewModel.swift` ✅ |
| Service 文件以 `Service` 或 `Manager` 结尾 | `AuthService.swift` ✅ |
| Model 文件以 `Model` 或 `Entity` 结尾 | `UserModel.swift` ✅ |
| Extension 文件以 `+` 结尾 | `String+Extensions.swift` ✅ |
| 协议文件以 `Protocol` 结尾 | `AuthServiceProtocol.swift` ✅ |

### 3.3 代码命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| **类名** | 大驼峰，描述性命名 | `UserProfileService.swift` |
| **函数** | 小驼峰，动词开头 | `fetchUserProfile()` |
| **变量** | 小驼峰 | `userName`, `sessionId` |
| **常量** | 全大写，下划线分隔 | `MAX_RETRY_COUNT` |
| **协议** | 以 `Protocol` 结尾 | `UserServiceProtocol.swift` |
| **枚举** | 大驼峰，单数形式 | `APIError`, `HTTPMethod` |

---

## 四、资源管理统一

### 4.1 颜色系统统一

```swift
// Core/Theme/AppColors.swift

import SwiftUI

/// 应用颜色系统
///
/// 使用语义化命名，而非具体颜色值
/// 便于后续主题切换（如暗黑模式）
///
enum AppColors {

    // MARK: - Primary Colors
    static let primary = Color(hex: "#517A6B")
    static let primaryLight = Color(hex: "#739E89")
    static let primaryDark = Color(hex: "#2D4A35")

    // MARK: - Semantic Colors
    static let background = Color(hex: "#F7F2E8")
    static let cardBackground = Color.white
    static let textPrimary = Color(hex: "#383833")
    static let textSecondary = Color(hex: "#6B6B66")
    static let textTertiary = Color(hex: "#9E9E99")

    // MARK: - Status Colors
    static let success = Color(hex: "#4DB885")
    static let warning = Color(hex: "#F5A623")
    static let error = Color(hex: "#D95959")
    static let info = Color(hex: "#517A6B")

    // MARK: - Functional Colors
    static let link = Color(hex: "#517A6B")
    static let border = Color(hex: "#E0E0E0")
    static let divider = Color(hex: "#F0F0F0")

    // MARK: - Overlay Colors
    static let overlay = Color.black.opacity(0.5)
    static let modalBackground = Color.white
    static let sheetBackground = Color(hex: "#F5F5F7")
}

extension Color {
    init(hex: String) {
        let hex = hex.replacingOccurrences(of: "#", with: "")
        var rgb: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&rgb)
        self.init(
            red: Double((rgb & 0xFF0000) >> 16) / 255.0,
            green: Double((rgb & 0x00FF00) >> 8) / 255.0,
            blue: Double(rgb & 0x0000FF) / 255.0
        )
    }
}
```

### 4.2 字体系统统一

```swift
// Core/Theme/AppFonts.swift

import SwiftUI

/// 应用字体系统
///
/// 统一管理字体大小和样式
/// 支持动态字体大小调整
///
enum AppFonts {

    // MARK: - Font Sizes (相对单位，支持缩放)
    static let large: CGFloat = 20
    static let title1: CGFloat = 18
    static let title2: CGFloat = 16
    static let title3: CGFloat = 14
    static let body: CGFloat = 14
    static let callout: CGFloat = 13
    static let subheadline: CGFloat = 12
    static let footnote: CGFloat = 11
    static let caption1: CGFloat = 10
    static let caption2: CGFloat = 9

    // MARK: - Font Weights
    static let bold: Font.Weight = .bold
    static let semibold: Font.Weight = .semibold
    static let medium: Font.Weight = .medium
    static let regular: Font.Weight = .regular

    // MARK: - Font Families
    static let system = "SF Pro Text"
    static let mono = "SF Mono"

    // MARK: - Combined Font API
    static func font(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        Font.system(size: size, weight: weight)
    }
}

// 使用示例
Text("Hello")
    .font(AppFonts.font(.body, weight: .medium))
    .foregroundColor(AppColors.textPrimary)
```

### 4.3 间距系统统一

```swift
// Core/Theme/AppSpacing.swift

import SwiftUI

/// 应用间距系统
///
/// 统一管理内边距、外边距、组件间距
///
enum AppSpacing {

    // MARK: - Base Spacing Unit (支持屏幕缩放)
    static let base: CGFloat = 4

    // MARK: - Micro Spacing (2px)
    static let micro: CGFloat = base * 0.5      // 2pt
    static let tiny: CGFloat = base            // 4pt

    // MARK: - Small Spacing (4-8px)
    static let small: CGFloat = base * 1.5     // 6pt
    static let compact: CGFloat = base * 2       // 8pt

    // MARK: - Medium Spacing (12-16px)
    static let medium: CGFloat = base * 3       // 12pt
    static let standard: CGFloat = base * 4     // 16pt

    // MARK: - Large Spacing (20-32px)
    static let large: CGFloat = base * 6        // 24pt
    static let xLarge: CGFloat = base * 8       // 32pt

    // MARK: - Specific Spacing
    static let buttonHorizontal: CGFloat = base * 3   // 12pt
    static let buttonVertical: CGFloat = base * 1.5    // 6pt
    static let cardPadding: CGFloat = base * 4         // 16pt
    static let sectionSpacing: CGFloat = base * 6       // 24pt
}

// 使用示例
VStack(spacing: AppSpacing.standard) {
    Text("Title")
        .padding(.horizontal, AppSpacing.standard)
}
```

### 4.4 图片资源管理

```swift
// Core/Theme/AppAssets.swift

import SwiftUI

/// 应用图片资源管理
///
/// 集中管理所有图片名称和加载逻辑
///
enum AppAssets {

    // MARK: - Icons
    enum Icons {
        static let tabHome = "house.fill"
        static let tabChat = "message.badge.fill"
        static let tabOrders = "checkmark.seal.fill"
        static let tabFiles = "folder.fill"
        static let tabProfile = "person.circle.fill"

        static let camera = "camera.fill"
        static let photoLibrary = "photo.fill"
        static let microphone = "mic.fill"
        static let send = "arrow.up.circle.fill"
        static let add = "plus.circle.fill"
        static let close = "xmark.circle.fill"
        static let more = "ellipsis"
        static let checkmark = "checkmark"
        static let chevronRight = "chevron.right"
        static let chevronLeft = "chevron.left"
        static let search = "magnifyingglass"
        static let bell = "bell"
        static let settings = "gearshape"
        static let trash = "trash"
        static let edit = "pencil"
        static let share = "square.and.arrow.up"
    }

    // MARK: - Images
    enum Images {
        static let logo = "app_logo"
        static let placeholder = "placeholder"
        static let defaultAvatar = "default_avatar"
        static let background = "app_background"
    }

    // MARK: - SF Symbol Resolver
    static func symbol(_ name: String) -> Image {
        Image(systemName: name)
    }

    static func icon(_ icon: String) -> Image {
        symbol(icon)
    }
}
```

---

## 五、配置管理统一

### 5.1 应用配置

```swift
// Core/Config/AppConfig.swift

import Foundation

/// 应用配置
///
/// 集中管理所有配置项
/// 支持不同环境（开发/测试/生产）
///
enum AppConfig {

    // MARK: - Environment
    static var environment: Environment {
        #if DEBUG
        return .development
        #else
        return .production
        #endif
    }

    enum Environment: String {
        case development
        case staging
        case production

        var displayName: String {
            switch self {
            case .development: return "开发环境"
            case .staging: return "测试环境"
            case .production: return "生产环境"
            }
        }
    }

    // MARK: - API Configuration
    enum API {
        static let baseURL: String = {
            switch AppConfig.environment {
            case .development: return "http://localhost:8100"
            case .staging: return "https://staging-api.example.com"
            case .production: return "https://api.example.com"
            }
        }()

        static let timeout: TimeInterval = 30
        static let maxRetries: Int = 3
    }

    // MARK: - App Info
    enum App {
        static let name = "灵犀健康"
        static let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
        static let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"

        static let displayName = "灵犀健康"
        static let bundleIdentifier = "com.example.xinlingyisheng"
    }

    // MARK: - Cache Configuration
    enum Cache {
        static let maxMemoryCount: Int = 100
        static let maxDiskSize: Int = 50 * 1024 * 1024  // 50 MB
        static let defaultCacheTime: TimeInterval = 15 * 60  // 15 分钟
    }

    // MARK: - Feature Flags
    enum Feature {
        static let isDebugEnabled: Bool = {
            #if DEBUG
            return true
            #else
            return false
            #endif
        }()

        static let isCrashReportingEnabled: Bool = true
        static let isAnalyticsEnabled: Bool = true
    }
}
```

### 5.2 常量管理

```swift
// Core/Utils/Constants.swift

import Foundation

/// 应用常量
///
/// 集中管理所有硬编码常量
///
enum AppConstants {

    // MARK: - User Defaults Keys
    enum UserDefaults {
        static let keyHasOnboarded = "hasOnboarded"
        static let keyUserID = "userID"
        static let keyUserToken = "userToken"
        static let keyRefreshToken = "refreshToken"
        static let keyLastSyncDate = "lastSyncDate"
    }

    // MARK: - Keychain Keys
    enum Keychain {
        static let keyAccessToken = "com.xinlingyisheng.accessToken"
        static let keyRefreshToken = "com.xinlingyisheng.refreshToken"
        static let keyBiometricEnabled = "com.xinlingyisheng.biometricEnabled"
    }

    // MARK: - Pagination
    enum Pagination {
        static let defaultPageSize: Int = 20
        static let messagePageSize: Int = 50
        static let maxPageSize: Int = 100
    }

    // MARK: - File Size Limits
    enum FileSize {
        static let maxImageUploadSize: Int = 10 * 1024 * 1024  // 10 MB
        static let maxVideoDuration: TimeInterval = 60  // 60 秒
        static let thumbnailSize: CGFloat = 1024
    }

    // MARK: - Time Intervals
    enum Time {
        static let debounceDelay: TimeInterval = 0.3
        static let animationDuration: Double = 0.3
        static let alertAutoDismiss: TimeInterval = 3.0
        static let requestTimeout: TimeInterval = 30.0
    }

    // MARK: - Validation
    enum Validation {
        static let minPhoneLength: Int = 11
        static let maxPhoneLength: Int = 11
        static let verificationCodeLength: Int = 6
        static let maxRetries: Int = 3
    }
}
```

---

## 六、路由管理统一

### 6.1 路由定义

```swift
// Core/Routing/AppRouter.swift

import SwiftUI

/// 应用路由
///
/// 统一管理所有页面路由
/// 避免硬编码字符串
/// 支持深度链接和类型安全
///
enum AppRouter: Hashable {

    // MARK: - Authentication
    case login
    case profileSetup
    case forgotPassword

    // MARK: - Main Tabs
    case home
    case chat(doctorId: Int?, department: String?)
    case orders
    case medicalDossier
    case profile

    // MARK: - Chat
    case chatSession(sessionId: String)
    case sessionHistory
    case newChat(doctorId: Int?)

    // MARK: - Medical
    case diseaseList(departmentId: Int?)
    case diseaseDetail(diseaseId: Int)
    case drugList(categoryId: Int?)
    case drugDetail(drugId: Int)

    // MARK: - Orders
    case orderList
    case orderDetail(orderId: Int)
    case taskCheckIn(orderId: Int, taskId: Int)

    // MARK: - Medical Dossier
    case dossierFolders
    case dossierEvents(folderId: Int?)
    case eventDetail(eventId: String)
    case createEvent

    // MARK: - Settings
    case settings
    case about
    case privacyPolicy
    case termsOfService

    // MARK: - Computed Properties
    var title: String {
        switch self {
        case .login: return "登录"
        case .profileSetup: return "完善资料"
        case .home: return "首页"
        case .chat: return "问医生"
        case .orders: return "医嘱"
        case .medicalDossier: return "病历"
        case .profile: return "我的"
        case .settings: return "设置"
        case .about: return "关于"
        default: return "灵犀健康"
        }
    }
}

// MARK: - Navigation Path Extension

extension NavigationPath {
    mutating func route(to router: AppRouter) {
        append(router)
    }
}
```

### 6.2 路由使用示例

```swift
// 使用前（硬编码）
NavigationLink(value: "doctor_profile") { ... }
NavigationLink(value: "session_detail_\(sessionId)") { ... }

// 使用后（类型安全）
NavigationLink(value: AppRouter.doctorProfile(userId: userId)) { ... }
NavigationLink(value: AppRouter.chatSession(sessionId: sessionId)) { ... }

// 在 View 中处理
.navigationDestination(item: $selectedRoute) { route in
    switch route {
    case .login:
        LoginView()
    case .chat(let doctorId, let department):
        ConsultationView(doctorId: doctorId, department: department)
    case .chatSession(let sessionId):
        ChatSessionView(sessionId: sessionId)
    // ...
    default:
        EmptyView()
    }
}
```

---

## 七、错误处理统一

### 7.1 错误类型定义

```swift
// Core/Network/AppError.swift

import Foundation

/// 应用错误类型
///
/// 统一定义所有可能的错误
/// 支持本地化和用户友好提示
///
enum AppError: Error, LocalizedError {

    // MARK: - Network Errors
    case networkUnavailable
    case networkTimeout
    case noInternetConnection
    case serverError(code: Int, message: String?)
    case tooManyRequests

    // MARK: - Authentication Errors
    case unauthorized
    case tokenExpired
    case invalidCredentials
    case accountLocked
    case accountDisabled
    case notLoggedIn
    case sessionExpired

    // MARK: - Validation Errors
    case invalidInput(field: String, reason: String)
    case missingRequiredField(String)
    case invalidFormat(field: String, expected: String)
    case valueOutOfRange(field: String, min: String?, max: String?)

    // MARK: - Business Logic Errors
    case resourceNotFound(type: String, id: String?)
    case operationFailed(reason: String)
    case insufficientPermissions
    case featureNotAvailable
    case quotaExceeded

    // MARK: - System Errors
    case databaseError(underlying: Error)
    case fileSystemError(underlying: Error)
    case encodingError(underlying: Error)
    case decodingError(underlying: Error)
    case unknownError(underlying: Error?)

    // MARK: - LocalizedError
    var errorDescription: String? {
        switch self {
            // Network
        case .networkUnavailable:
            return "网络连接不可用，请检查网络设置"
        case .networkTimeout:
            return "请求超时，请稍后重试"
        case .noInternetConnection:
            return "无网络连接"
        case .serverError(let code, let message):
            return message ?? "服务器错误 (\(code))"
        case .tooManyRequests:
            return "请求过于频繁，请稍后再试"

            // Auth
        case .unauthorized:
            return "登录已过期，请重新登录"
        case .tokenExpired:
            return "登录已过期，请重新登录"
        case .invalidCredentials:
            return "用户名或密码错误"
        case .accountLocked:
            return "账户已被锁定，请稍后重试"
        case .accountDisabled:
            return "账户已被禁用"
        case .notLoggedIn:
            return "请先登录"
        case .sessionExpired:
            return "会话已过期"

            // Validation
        case .invalidInput(let field, let reason):
            return "\(field)格式错误：\(reason)"
        case .missingRequiredField(let field):
            return "请输入\(field)"
        case .invalidFormat(let field, let expected):
            return "\(field)格式应为\(expected)"
        case .valueOutOfRange(let field, let min, let max):
            if let min = min, let max = max {
                return "\(field)应在\(min)到\(max)之间"
            } else if let min = min {
                return "\(field)应大于或等于\(min)"
            } else if let max = max {
                return "\(field)应小于或等于\(max)"
            } else {
                return "\(field)值无效"
            }

            // Business
        case .resourceNotFound(let type, let id):
            return "\(type)(ID: \(id ?? "未知"))不存在"
        case .operationFailed(let reason):
            return reason
        case .insufficientPermissions:
            return "权限不足"
        case .featureNotAvailable:
            return "此功能暂时不可用"
        case .quotaExceeded:
            return "已超出配额限制"

            // System
        case .databaseError(let error):
            return "数据错误：\(error.localizedDescription)"
        case .fileSystemError(let error):
            return "文件错误：\(error.localizedDescription)"
        case .encodingError:
            return "数据编码错误"
        case .decodingError:
            return "数据解析错误"
        case .unknownError(let error):
            return error?.localizedDescription ?? "未知错误"
        }
    }

    /// 用户友好的错误标题
    var title: String {
        switch self {
        case .networkUnavailable, .networkTimeout, .noInternetConnection:
            return "网络问题"
        case .unauthorized, .tokenExpired, .sessionExpired:
            return "需要登录"
        case .invalidInput, .missingRequiredField:
            return "输入错误"
        case .serverError:
            return "服务器错误"
        default:
            return "操作失败"
        }
    }

    /// 错误级别
    var level: ErrorLevel {
        switch self {
        case .networkUnavailable, .noInternetConnection:
            return .error
        case .unauthorized, .tokenExpired, .accountLocked:
            return .warning
        case .invalidInput, .missingRequiredField:
            return .info
        default:
            return .error
        }
    }
}

enum ErrorLevel {
    case info
    case warning
    case error
}
```

### 7.2 错误处理服务

```swift
// Core/Error/ErrorHandler.swift

import SwiftUI

/// 错误处理服务
///
/// 统一处理和显示错误
/// 支持 Toast、Alert、Sheet 等多种展示方式
///
@MainActor
class ErrorHandler: ObservableObject {
    static let shared = ErrorHandler()

    // MARK: - Published Properties
    @Published var currentError: AppError?
    @Published var isErrorShown: Bool = false

    // MARK: - Display Methods
    /// 显示 Toast 轻提示
    func showToast(_ error: AppError, duration: TimeInterval = 2.0) {
        currentError = error
        isErrorShown = true

        Task {
            try await Task.sleep(nanoseconds: UInt64(duration * 1_000_000_000))
            isErrorShown = false
            currentError = nil
        }
    }

    /// 显示 Alert 对话框
    func showAlert(_ error: AppError) {
        currentError = error
        isErrorShown = true
    }

    /// 隐藏错误提示
    func hide() {
        isErrorShown = false
        currentError = nil
    }

    /// 包装异步操作并自动处理错误
    func handle<T>(
        _ operation: () async throws -> T,
        onError: ((AppError) -> Void)? = nil
    ) async -> T? {
        do {
            return try await operation()
        } catch let error as AppError {
            if let onError = onError {
                onError(error)
            } else {
                showAlert(error)
            }
            return nil
        } catch {
            let appError = AppError.unknownError(error)
            showAlert(appError)
            return nil
        }
    }

    /// 包装 API 请求
    func handleAPIRequest<T>(
        _ request: () async throws -> T
    ) async -> T? {
        return await handle(request)
    }
}

// 使用示例
struct SomeView: View {
    @StateObject private var errorHandler = ErrorHandler.shared

    var body: some View {
        VStack {
            Button("执行操作") {
                Task {
                    await errorHandler.handle {
                        try await performRiskyOperation()
                    }
                }
            }
        }
        .alert("错误", isPresented: $errorHandler.isErrorShown) {
            Button("确定") { errorHandler.hide() }
        } message: {
            Text(errorHandler.currentError?.errorDescription ?? "未知错误")
        }
    }
}
```

---

## 八、基础组件重构

### 8.1 基础 ViewModel

```swift
// Core/Base/BaseViewModel.swift

import Foundation
import Combine

/// 基础 ViewModel
///
/// 提供所有 ViewModel 的公共功能
/// 减少重复代码
///
@MainActor
class BaseViewModel: ObservableObject {

    // MARK: - Published Properties
    @Published var isLoading: Bool = false
    @Published var isRefreshing: Bool = false
    @Published var error: AppError?
    @Published var hasError: Bool = false

    // MARK: - Cancellables
    var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization
    init() {
        setupErrorHandling()
    }

    // MARK: - Setup
    private func setupErrorHandling() {
        // 监听全局错误处理器
        ErrorHandler.shared.$currentError
            .receive(on: DispatchQueue.main)
            .sink { [weak self] error in
                self?.error = error
                self?.hasError = (error != nil)
            }
            .store(in: &cancellables)
    }

    // MARK: - Public Methods
    /// 加载数据
    func load<T>(_ operation: () async throws -> T) async {
        isLoading = true
        error = nil
        hasError = false

        defer { isLoading = false }

        do {
            let result = try await operation()
            return result
        } catch {
            self.error = error as? AppError ?? .unknownError(error)
            self.hasError = true
            return nil
        }
    }

    /// 刷新数据
    func refresh<T>(_ operation: () async throws -> T) async {
        isRefreshing = true
        error = nil
        hasError = false

        defer { isRefreshing = false }

        do {
            let result = try await operation()
            return result
        } catch {
            self.error = error as? AppError ?? .unknownError(error)
            self.hasError = true
            return nil
        }
    }

    /// 清除错误
    func clearError() {
        self.error = nil
        self.hasError = false
    }

    /// 清理资源
    func cleanup() {
        cancellables.forEach { $0.cancel() }
        cancellables.removeAll()
    }
}
```

### 8.2 通用按钮组件

```swift
// Shared/Components/Buttons/AppButton.swift

import SwiftUI

/// 应用统一按钮样式
///
/// 提供多种样式变体
/// 统一按钮行为和外观
///
struct AppButton: View {

    // MARK: - Types
    enum Style {
        case primary      // 主要按钮
        case secondary    // 次要按钮
        case outline     // 轮廓按钮
        case text        // 文本按钮
        case danger      // 危险操作按钮
        case iconOnly    // 仅图标按钮
    }

    enum Size {
        case large
        case medium
        case small
        case compact
    }

    // MARK: - Properties
    private let title: String?
    let action: () -> Void
    let style: Style
    let size: Size
    let isLoading: Bool
    let isDisabled: Bool
    let icon: String?

    // MARK: - Initialization
    init(
        _ title: String,
        action: @escaping () -> Void,
        style: Style = .primary,
        size: Size = .medium,
        isLoading: Bool = false,
        isDisabled: Bool = false,
        icon: String? = nil
    ) {
        self.title = title
        self.action = action
        self.style = style
        self.size = size
        self.isLoading = isLoading
        self.isDisabled = isDisabled
        self.icon = icon
    }

    // MARK: - Icon Only Convenience
    init(icon: String, action: @escaping () -> Void, size: Size = .medium) {
        self.title = nil
        self.action = action
        self.style = .iconOnly
        self.size = size
        self.isLoading = false
        self.isDisabled = false
        self.icon = icon
    }

    // MARK: - Body
    var body: some View {
        buttonContent
            .disabled(isDisabled || isLoading)
            .buttonStyle(buttonStyle)
            .onTapGesture {
                if !isLoading {
                    action()
                }
            }
    }

    // MARK: - Private Views
    @ViewBuilder
    private var buttonContent: some View {
        Group {
            if isLoading {
                loadingView
            } else {
                labelContent
            }
        }
    }

    private var labelContent: some View {
        HStack(spacing: 8) {
            if let icon = icon {
                Image(systemName: icon)
                    .font(.system(size: fontSize, weight: .regular))
            }

            if let title = title {
                Text(title)
                    .font(.system(size: fontSize, weight: fontWeight))
            }
        }
        .padding(.horizontal, horizontalPadding)
        .padding(.vertical, verticalPadding)
    }

    private var loadingView: some View {
        ProgressView()
            .tint(foregroundColor)
    }

    // MARK: - Style Configuration
    private var foregroundColor: Color {
        switch style {
        case .primary: return AppColors.primary
        case .secondary: return AppColors.textPrimary
        case .outline: return AppColors.primary
        case .text: return AppColors.textPrimary
        case .danger: return AppColors.error
        case .iconOnly: return AppColors.primary
        }
    }

    private var backgroundColor: Color {
        switch style {
        case .primary: return AppColors.primary
        case .secondary: return AppColors.background
        case .outline: return Color.clear
        case .text: return Color.clear
        case .danger: return AppColors.error
        case .iconOnly: return Color.clear
        }
    }

    private var buttonStyle: some ButtonStyle {
        switch style {
        case .primary:
            return .borderedProminent
        case .secondary:
            return .bordered
        case .outline:
            return .bordered
        case .text:
            return .borderless
        case .danger:
            return .borderedProminent
        case .iconOnly:
            return .borderless
        }
    }

    // MARK: - Size Configuration
    private var fontSize: CGFloat {
        switch size {
        case .large: return 18
        case .medium: return 16
        case .small: return 14
        case .compact: return 12
        }
    }

    private var fontWeight: Font.Weight {
        switch size {
        case .large: return .semibold
        case .medium: return .medium
        case .small: return .medium
        case .compact: return .semibold
        }
    }

    private var horizontalPadding: CGFloat {
        switch size {
        case .large: return 32
        case .medium: return 24
        case .small: return 20
        case .compact: return 16
        }
    }

    private var verticalPadding: CGFloat {
        switch size {
        case .large: return 16
        case .medium: return 12
        case .small: return 10
        case .compact: return 8
        }
    }
}
```

### 8.3 通用输入框组件

```swift
// Shared/Components/Inputs/AppTextField.swift

import SwiftUI

/// 应用统一输入框样式
///
/// 支持多种状态和样式
/// 统一输入验证和错误提示
///
struct AppTextField: View {

    // MARK: - Types
    enum Style {
        case standard
        case underline
        case filled
    }

    enum ValidationState {
        case valid
        case invalid(String)
        case loading
    }

    // MARK: - Properties
    @Binding private var text: String
    let placeholder: String
    let style: Style
    var validationState: ValidationState = .valid
    let isSecure: Bool
    let keyboardType: UIKeyboardType
    let onSubmit: (() -> Void)?

    // MARK: - Initialization
    init(
        _ text: Binding<String>,
        placeholder: String,
        style: Style = .standard,
        validationState: ValidationState = .valid,
        isSecure: Bool = false,
        keyboardType: UIKeyboardType = .default,
        onSubmit: (() -> Void)? = nil
    ) {
        self._text = text
        self.placeholder = placeholder
        self.style = style
        self.validationState = validationState
        self.isSecure = isSecure
        self.keyboardType = keyboardType
        self.onSubmit = onSubmit
    }

    // MARK: - Body
    var body: some View {
        HStack(spacing: 0) {
            switch style {
                case .standard:
                    standardField
                case .underline:
                    underlineField
                case .filled:
                    filledField
            }

            if case .invalid(let message) = validationState {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(AppColors.textTertiary)
                }
                .transition(.scale.combined(with: .opacity))
            }
        }
        .padding(.vertical, 8)
    }

    // MARK: - Private Views
    private var standardField: some View {
        TextField(placeholder, text: $text)
            .textFieldStyle(.plain)
            .keyboardType(keyboardType)
            .disabled(isLoading)
            .onSubmit(onSubmit ?? {})
            .foregroundColor(AppColors.textPrimary)
            .font(AppFonts.font(.body))
            .padding(.horizontal, 16)
            .background(AppColors.cardBackground)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(validationBorderColor, lineWidth: 1)
            )
    }

    private var underlineField: some View {
        TextField(placeholder, text: $text)
            .textFieldStyle(.plain)
            .keyboardType(keyboardType)
            .disabled(isLoading)
            .foregroundColor(AppColors.textPrimary)
            .font(AppFonts.font(.body))
            .padding(.horizontal, 0)
            .overlay(
                Rectangle()
                    .fill(validationBorderColor)
                    .frame(height: 1)
                    .padding(.bottom, 8)
            )
    }

    private var filledField: some View {
        ZStack(alignment: .leading) {
            if isSecure {
                SecureField(placeholder, text: $text)
            } else {
                TextField(placeholder, text: $text)
            }
            .textFieldStyle(.plain)
            .keyboardType(keyboardType)
            .disabled(isLoading)
            .foregroundColor(AppColors.textPrimary)
            .font(AppFonts.font(.body))
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(AppColors.background)
            .cornerRadius(12)
        }
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(validationBorderColor, lineWidth: 1)
        )
    }

    // MARK: - Computed Properties
    private var isLoading: Bool {
        if case .loading = validationState {
            return true
        }
        return false
    }

    private var validationBorderColor: Color {
        switch validationState {
        case .valid: return AppColors.border
        case .invalid: return AppColors.error
        case .loading: return AppColors.textTertiary
        }
    }
}
```

---

## 九、实施计划

### 9.1 第一阶段：基础设施（1-2周）

| 顺序 | 任务 | 优先级 | 预计时间 |
|------|------|--------|----------|
| 1 | 创建 Core 目录结构 | 🔴 P0 | 0.5天 |
| 2 | 实现 AppColors.swift | 🔴 P0 | 0.5天 |
| 3 | 实现 AppFonts.swift | 🔴 P0 | 0.5天 |
| 4 | 实现 AppSpacing.swift | 🔴 P0 | 0.5天 |
| 5 | 实现 AppAssets.swift | 🔴 P0 | 0.5天 |
| 6 | 实现 AppConfig.swift | 🔴 P0 | 1天 |
| 7 | 实现 AppConstants.swift | 🔴 P0 | 0.5天 |
| 8 | 实现 AppRouter.swift | 🔴 P0 | 1天 |
| 9 | 实现 AppError.swift | 🔴 P0 | 1天 |
| 10 | 实现 ErrorHandler.swift | 🔴 P0 | 1天 |
| 11 | 实现 BaseViewModel.swift | 🟡 P1 | 1天 |

### 9.2 第二阶段：组件库（2-3周）

| 顺序 | 任务 | 优先级 | 预计时间 |
|------|------|--------|----------|
| 1 | 创建 Shared/Components 目录 | 🟡 P1 | 0.5天 |
| 2 | 实现 AppButton.swift | 🟡 P1 | 1天 |
| 3 | 实现 AppTextField.swift | 🟡 P1 | 1天 |
| 4 | 实现 AppCard.swift | 🟡 P1 | 1天 |
| 5 | 实现 AppLoadingView.swift | 🟡 P1 | 0.5天 |
| 6 | 实现 AppEmptyView.swift | 🟡 P1 | 0.5天 |
| 7 | 实现 AppSheet.swift | 🟢 P2 | 1天 |

### 9.3 第三阶段：目录迁移（3-4周）

| 顺序 | 任务 | 优先级 | 预计时间 |
|------|------|--------|----------|
| 1 | 迁移 Views/ → Features/Auth/Views/ | 🟡 P1 | 2天 |
| 2 | 迁移 Views/ → Features/Chat/Views/ | 🟡 P1 | 3天 |
| 3 | 迁移 ViewModels/ → Features/ | 🟡 P1 | 3天 |
| 4 | 迁移 Services/ → Features/ | 🟡 P1 | 2天 |
| 5 | 迁移 Models/ → Features/ | 🟢 P2 | 2天 |
| 6 | 更新所有 import 路径 | 🟡 P1 | 2天 |
| 7 | 删除旧目录 | 🟢 P2 | 0.5天 |

### 9.4 第四阶段：测试验证（1周）

| 顺序 | 任务 | 优先级 | 预计时间 |
|------|------|--------|----------|
| 1 | 编译测试所有新增文件 | 🔴 P0 | 1天 |
| 2 | 运行应用验证基础功能 | 🔴 P0 | 1天 |
| 3 | 手动测试所有页面 | 🔴 P0 | 2天 |
| 4 | 修复发现的问题 | 🔴 P0 | 2天 |

---

## 十、预期收益

### 10.1 代码质量提升

| 指标 | 当前 | 目标 |
|--------|--------|------|
| 目录规范性 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 命名规范性 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 资源管理 | ⭐⭐ | ⭐⭐⭐⭐ |
| 代码复用性 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 可维护性 | ⭐⭐⭐ | ⭐⭐⭐ |

### 10.2 开发效率提升

| 改进点 | 效率提升 |
|---------|----------|
| 统一路由 | 减少 50% 导航相关 bug |
| 统一错误处理 | 减少 30% 错误处理时间 |
| 统一组件库 | 减少 40% UI 开发时间 |
| 集中配置管理 | 减少 60% 配置相关时间 |
| 规范命名 | 减少 20% 理解代码时间 |

---

## 十一、迁移指南

### 11.1 新旧代码共存策略

```
第一阶段：创建新结构
├── 保持旧代码不变
├── 创建新的 Core/ 和 Features/ 目录
└── 新功能使用新结构

第二阶段：逐步迁移
├── 逐模块迁移到新结构
├── 每个模块迁移后测试验证
└── 保持应用可运行状态

第三阶段：清理
├── 删除旧的目录结构
├── 统一 import 路径
└── 提交完成标记
```

### 11.2 Import 路径更新

```swift
// 旧导入
import struct SomeView // 从根目录导入

// 新导入
import Features.Chat.Views.SomeView // 从模块导入
import Core.Theme.AppColors // 使用资源前缀
import Shared.Components.AppButton // 使用共享组件
```

---

*方案版本: v3.0 (工程化版)*
*生成日期: 2026-02-12*
*核心原则: 改动可以大，但方向要正确，让项目更工程化、更规范*
