# iOS 架构设计文档

> **项目名称**: 鑫琳医生（灵犀健康）
> **平台**: iOS 17.0+
> **语言**: Swift
> **UI 框架**: SwiftUI
> **架构模式**: MVVM + Coordinator
> **更新日期**: 2026-02-14

---

## 目录

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
├── Features/               # 功能模块层
│   ├── Auth/               # 认证功能
│   ├── Consultation/       # 咨询功能
│   ├── Knowledge/          # 知识库
│   ├── Medical/            # 医疗功能
│   └── Profile/           # 个人中心
└── Shared/                 # 共享资源层
    └── Resources/          # 共享资源
```

---

## 架构概览

### 整体结构
```
┌─────────────────────────────────────────────────────────┐
│                    Features Layer                     │
│  ┌───────────────────────────────────────────┐   │
│  │            Auth  │ Consultation │ Knowledge │ Medical │ Profile │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                    ↓ 依赖
┌─────────────────────────────────────────────────────────┐
│                   Core Layer                      │
│  ┌───────────────────────────────────────────────┐ │
│  │ Base │ Components │ Config │ Error │ Routing │ Theme │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                    ↓ 依赖
┌─────────────────────────────────────────────────────────┐
│                 Shared Layer                        │
│  ┌───────────────────────────────────────────────┐ │
│  │            Resources                          │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Core 核心层

### Base/ - 基础组件

#### BaseView.swift

所有 View 的基础协议，提供统一的视图能力。

```swift
protocol BaseView: View {
    var emptyStateView: some View {
        EmptyStateView(icon: "doc.text.magnifyingglass", title: "暂无数据")
    }
}
```

扩展方法：
- `hideKeyboard()` - 隐藏键盘
- `ifShow(_:)` - 条件显示
- `ifHide(_:)` - 条件隐藏

---

### Components/ - 共享UI组件

#### AppButton.swift

统一按钮组件，支持多种样式和尺寸。

```swift
// 按钮类型
enum AppButtonType {
    case primary
    case secondary
    case tertiary
    case danger
    case success
}
```

#### AppTextField.swift

统一文本输入框组件，支持多种输入类型和状态。

#### AppCard.swift

卡片容器组件，提供统一的卡片样式。

#### AppLoadingView.swift

统一加载视图组件。

#### AppSheet.swift

抽屉弹窗组件。

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

#### ErrorHandler.swift

单例错误处理器，统一错误显示管理。

```swift
class ErrorHandler: ObservableObject {
    static let shared = ErrorHandler()

    @Published var currentError: AppError?

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
```

导航方法：
- `navigate(to:)` - 直接导航
- `navigationPath(to:)` - 支持返回的导航
- `presentSheet()` - 抽屉展示
- `showAlert()` - 警告提示

---

## Features 功能层

### Auth/ - 认证功能

#### 目录结构
```
Auth/
├── ViewModels/
│   ├── LoginViewModel.swift      # 登录逻辑
│   └── ProfileSetupViewModel.swift
├── Views/
│   ├── SplashView.swift          # 启动页
│   ├── LoginView.swift           # 登录页
│   └── ProfileSetupView.swift    # 资料设置
└── Services/
    └── KeychainManager.swift     # 安全存储
```

---

### Consultation/ - 咨询功能

#### 目录结构
```
Consultation/
├── ViewModels/
│   ├── UnifiedChatViewModel.swift
│   ├── ChatMessageViewModel.swift
│   ├── ChatSessionViewModel.swift
│   ├── VoiceInputViewModel.swift
│   └── VoiceTranscriptionViewModel.swift
├── Views/
│   ├── ModernConsultationView.swift
│   ├── AskDoctorView.swift
│   ├── SessionHistoryView.swift
│   └── MyQuestionsView.swift
└── Services/
    ├── UnifiedChatAPIService.swift
    ├── ChatSessionService.swift
    ├── ChatMessageService.swift
    └── SessionStateManager.swift
```

#### UnifiedChatViewModel 架构

服务分离模式：
```swift
private let sessionService: ChatSessionService      // 会话管理
private let messageService: ChatMessageService      // 消息管理
private let voiceService: ChatVoiceInputService     // 语音处理
```

---

### Knowledge/ - 知识库功能

#### 目录结构
```
Knowledge/
├── Disease/
│   └── Views/
│       ├── DiseaseListView.swift
│       ├── DiseaseDetailView.swift
│       └── DepartmentDetailView.swift
└── Drug/
    └── Views/
        ├── DrugListView.swift
        └── DrugDetailView.swift
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
│       ├── MedicalDossierView.swift
│       ├── MedicalFoldersView.swift
│       ├── EventDetailView.swift
│       ├── CreateRecordSheet.swift
│       └── RecordDetailView.swift
└── Orders/
    └── ViewModels/
        └── MedicalOrderViewModel.swift
```

#### MedicalEventAPIService

使用 DTO 设计模式：
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

预留位置，用于放置跨模块共享的资源。

---

## 设计原则

### 1. 模块化设计

每个功能模块独立封装，清晰的职责边界。

### 2. 依赖注入

通过构造函数注入依赖，便于测试和解耦。

### 3. 服务层抽象

业务逻辑封装在 Service 层，ViewModel 只负责状态管理。

### 4. 类型安全

使用枚举定义路由和错误类型，避免字符串硬编码。

### 5. 主线程安全

使用 `@MainActor` 确保 UI 更新在主线程。

---

## 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                   Features Layer                     │
│  ┌───────────────────────────────────────────────┐   │
│  │            Auth │ Consultation │ Knowledge │ Medical │ Profile │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                    ↓ 依赖
┌─────────────────────────────────────────────────────────┐
│                    Core Layer                      │
│  ┌───────────────────────────────────────────────┐ │
│  │ Base │ Components │ Config │ Error │ Routing │ Theme │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                    ↓ 依赖
┌─────────────────────────────────────────────────────────┐
│                 Shared Layer                        │
│  ┌───────────────────────────────────────────────┐ │
│  │            Resources                          │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 特色亮点

### 治愈系设计语言

- **配色方案**: 使用温暖、自然的颜色
- **动画效果**: 流畅的过渡动画
- **视觉层次**: 清晰的信息架构

### 智能化功能

- **语音识别**: 按住说话，实时转写
- **图片分析**: 皮肤、报告、心电图分析
- **流式输出**: 实时显示 AI 回复

### 安全性设计

- **Keychain 存储**: 敏感信息安全保存
- **自动降级**: Keychain 失败时降级到 UserDefaults
- **会话管理**: 完整的会话生命周期管理

### 性能优化

- **懒加载**: 按需加载资源
- **内存管理**: 及时清理资源
- **异步处理**: 避免阻塞主线程
---

## 编译错误列表

| 文件 | 行号 | 错误描述 | 状态 |
|------|------|----------|------|
| `Core/Base/BaseView.swift` | 18:9 | expected get or set in a protocol property | ✅ 已修复 |
| `Core/Base/BaseView.swift` | 47:1 | extraneous '}' at top level | ✅ 已修复 |
| `Core/Components/AppTextField.swift` | 44:59 | Expected ',' separator | ⏳ 待修复 |
| `Core/Theme/AppColors.swift` | 113:9 | Expected declaration | ⏳ 待修复 |

### 错误原因

这些错误是新架构代码本身的问题，与旧架构清理无关。需要在后续迭代中修复。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-02-14 | 新架构重构完成（但存在旧架构残留） |
