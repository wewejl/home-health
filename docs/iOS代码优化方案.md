# iOS 代码优化方案

> **创建日期**: 2026-02-12
> **项目**: 灵犀健康 iOS 应用
> **目标**: 提升代码质量、可维护性和性能

---

## 目录

1. [日志系统统一](#一日志系统统一)
2. [错误处理机制](#二错误处理机制)
3. [常量管理](#三常量管理)
4. [服务层重构](#四服务层重构)
5. [ViewModel 拆分](#五viewmodel-拆分)
6. [性能优化](#六性能优化)
7. [代码规范改进](#七代码规范改进)

---

## 一、日志系统统一

### 1.1 当前问题

代码中同时使用两种日志方式：
- `print()` - 直接输出到控制台
- `AppLogger` - 结构化日志系统

### 1.2 优化方案

#### 步骤 1: 创建统一的日志协议

```swift
// Services/Logging/AppLogger.swift

import Foundation
import os.log

/// 统一的日志协议
protocol AppLoggerProtocol {
    func debug(_ message: String, file: String = #file, function: String = #function, line: Int = #line)
    func info(_ message: String, file: String = #file, function: String = #function, line: Int = #line)
    func warning(_ message: String, file: String = #file, function: String = #function, line: Int = #line)
    func error(_ message: String, error: Error?, file: String = #file, function: String = #function, line: Int = #line)
}

/// 结构化日志实现
struct StructuredLogger: AppLoggerProtocol {
    private let subsystem = "com.lingxiyisheng"
    private let category = "AppLogging"

    private let logger = OSLog(subsystem: subsystem, category: category)

    func debug(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        logger.debug("\(file):\(line) - \(message)")
    }

    func info(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        logger.info("\(file):\(line) - \(message)")
    }

    func warning(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        logger_fault("\(file):\(line) - \(message)")
    }

    func error(_ message: String, error: Error?, file: String = #file, function: String = #function, line: Int = #line) {
        if let error = error {
            logger_fault("\(file):\(line) - \(message): \(error.localizedDescription)")
        } else {
            logger_fault("\(file):\(line) - \(message)")
        }
    }
}

/// 全局日志实例
let AppLogger = StructuredLogger()
```

#### 步骤 2: 替换所有 print() 调用

```swift
// 替换前
print("[Auth] Token 从 Keychain 加载成功")

// 替换后
AppLogger.debug("Token 从 Keychain 加载成功", file: "AuthManager.swift", function: "loadStoredAuth")

// 带上下文的日志
AppLogger.error("从 Keychain 加载 Token 失败", error: error)
```

#### 步骤 3: 批量替换列表

需要替换的文件：
1. `AuthManager.swift` - 10+ 处
2. `APIService.swift` - 20+ 处
3. `SessionStateManager.swift` - 5+ 处
4. `UnifiedChatViewModel.swift` - 15+ 处
5. `MedicalDossierViewModel.swift` - 10+ 处

---

## 二、错误处理机制

### 2.1 当前问题

错误处理依赖 `print()` 输出，没有统一的错误类型和用户提示。

### 2.2 优化方案

#### 步骤 1: 定义统一错误类型

```swift
// Models/AppError.swift

import Foundation

/// 应用统一错误类型
enum AppError: LocalizedError, CustomDebugStringConvertible {
    // 网络错误
    case networkUnavailable
    case networkTimeout
    case invalidURL
    case serverError(String)

    // 认证错误
    case unauthorized
    case tokenExpired
    case loginFailed(String)

    // 数据错误
    case decodingFailed
    case encodingFailed

    // 业务错误
    case sessionNotFound
    case patientNotFound
    case invalidInput(String)

    var errorDescription: String? {
        switch self {
        case .networkUnavailable: return "网络连接不可用"
        case .networkTimeout: return "请求超时，请检查网络"
        case .unauthorized: return "登录已过期，请重新登录"
        case .tokenExpired: return "登录已过期，请重新登录"
        case .sessionNotFound: return "会话不存在"
        case .invalidInput(let msg): return msg
        case .serverError(let msg): return msg
        default: return "未知错误"
        }
    }

    var debugDescription: String {
        switch self {
        case .networkUnavailable: return "网络不可用"
        case .decodingFailed: return "JSON 解析失败"
        default: return "\(self)"
        }
    }
}
```

#### 步骤 2: 统一错误处理

```swift
// Utils/ErrorHandler.swift

import Foundation
import SwiftUI

/// 错误处理器
@MainActor
class ErrorHandler: ObservableObject {
    @Published var currentError: AppError?
    @Published var showError: Bool = false

    static let shared = ErrorHandler()

    /// 处理错误并显示提示
    func handle(_ error: Error) {
        if let appError = error as? AppError {
            currentError = appError
            showError = true
        } else {
            currentError = AppError.networkError(error.localizedDescription)
            showError = true
        }

        // 自动消失
        Task {
            try await Task.sleep(nanoseconds: 3_000_000_000) // 3秒
            showError = false
        }
    }

    /// 处理 API 错误响应
    func handleAPIResponse<T>(_ response: HTTPURLResponse?, data: Data?, decodeType: T.Type) async throws -> T {
        guard let httpResponse = response else {
            throw AppError.networkUnavailable
        }

        switch httpResponse.statusCode {
        case 200...299:
            break // 成功
        case 401:
            throw AppError.unauthorized
        case 404:
            throw AppError.sessionNotFound
        case 500...599:
            if let data = data,
               let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw AppError.serverError(errorResponse.detail ?? "服务器错误")
            }
            throw AppError.serverError("服务器错误")
        default:
            throw AppError.networkError("HTTP \(httpResponse.statusCode)")
        }

        guard let data = data else {
            throw AppError.decodingFailed
        }

        do {
            return try JSONDecoder().decode(decodeType, from: data)
        } catch {
            throw AppError.decodingFailed
        }
    }

    /// 清除错误
    func clear() {
        currentError = nil
        showError = false
    }
}

// 使用示例
// 在 View 中
.alert("错误", isPresented: $errorHandler.showError) {
    Button("确定") { errorHandler.clear() }
} message: {
    Text(errorHandler.currentError?.errorDescription ?? "未知错误")
}
```

---

## 三、常量管理

### 3.1 当前问题

代码中存在大量硬编码的魔法数字：
- `maxMessageCount = 200`
- `maxImageMessagesInMemory = 10`
- 超时时间散落在各处

### 3.2 优化方案

```swift
// Config/AppConfiguration.swift

import Foundation

/// 应用配置常量
enum AppConfiguration {
    // 网络配置
    enum Network {
        static let timeoutInterval: TimeInterval = 30.0
        static let resourceTimeout: TimeInterval = 60.0
        static let maxConnectionsPerHost = 5
    }

    // 缓存配置
    enum Cache {
        static let maxMessageCount = 200
        static let maxImageMessagesInMemory = 10
        static let memoryCapacity = 20 * 1024 * 1024 // 20 MB
        static let diskCapacity = 100 * 1024 * 1024 // 100 MB
    }

    // 分页配置
    enum Pagination {
        static let defaultPageSize = 20
        static let messagePageSize = 50
    }

    // 图片配置
    enum Image {
        static let maxDimension: CGFloat = 1024
        static let compressionQuality: CGFloat = 0.8
    }

    // 超时配置
    enum Timeout {
        static let alertDismiss: TimeInterval = 3.0
        static let debounceDelay: TimeInterval = 0.3
    }
}
```

---

## 四、服务层重构

### 4.1 当前问题

`APIService.swift` 文件超过 500 行，包含所有 API 方法，难以维护。

### 4.2 优化方案

#### 步骤 1: 按功能模块拆分服务

```swift
// Services/Auth/AuthAPIService.swift

import Foundation

/// 认证相关 API 服务
struct AuthAPIService {
    private let baseURL = APIConfig.baseURL
    private let session = URLSession.shared

    func sendVerificationCode(phone: String) async throws -> SendCodeResponse {
        try await performRequest(
            endpoint: APIConfig.Endpoints.sendCode,
            method: "POST",
            body: SendCodeRequest(phone: phone)
        )
    }

    func login(phone: String, code: String) async throws -> LoginResponse {
        try await performRequest(
            endpoint: APIConfig.Endpoints.login,
            method: "POST",
            body: LoginRequest(phone: phone, code: code)
        )
    }

    func refreshToken(refreshToken: String) async throws -> RefreshTokenResponse {
        try await performRequest(
            endpoint: APIConfig.Endpoints.refresh,
            method: "POST",
            body: RefreshTokenRequest(refresh_token: refreshToken)
        )
    }

    private func performRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: (some Encodable)? = nil,
        requiresAuth: Bool = false
    ) async throws -> T {
        // 统一的请求实现
        // ...
    }
}
```

```swift
// Services/Medical/MedicalOrderAPIService.swift

/// 医嘱相关 API 服务
struct MedicalOrderAPIService {
    func getMedicalOrders(status: String?) async throws -> [MedicalOrder] {
        // 实现细节
    }

    func createMedicalOrder(_ request: MedicalOrderCreateRequest) async throws -> MedicalOrder {
        // 实现细节
    }

    func completeTask(_ request: CompletionRecordRequest) async throws -> CompletionRecord {
        // 实现细节
    }
}
```

#### 步骤 2: 使用协议抽象

```swift
// Services/Protocols/APIServiceProtocol.swift

/// API 服务协议
protocol APIServiceProtocol {
    func request<T: Decodable>(
        endpoint: String,
        method: HTTPMethod = .get,
        body: Data? = nil,
        requiresAuth: Bool = false
    ) async throws -> T
}

/// 扩展协议支持不同认证方式
protocol AuthenticatedAPIService: APIServiceProtocol {
    var authToken: String? { get }
    func requestWithAuth<T: Decodable>(
        endpoint: String,
        method: HTTPMethod = .get,
        body: Data? = nil
    ) async throws -> T
}

extension AuthenticatedAPIService {
    func requestWithAuth<T: Decodable>(
        endpoint: String,
        method: HTTPMethod = .get,
        body: Data? = nil
    ) async throws -> T {
        var request = URLRequest(url: URL(string: "\(baseURL)\(endpoint)")!)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = body
        }

        // 执行请求...
    }
}
```

---

## 五、ViewModel 拆分

### 5.1 当前问题

`UnifiedChatViewModel.swift` 包含过多职责：
- 会话管理
- 消息管理
- 语音输入
- 图片处理
- 病历生成

超过 450 行代码。

### 5.2 优化方案

#### 步骤 1: 按职责拆分

```swift
// ViewModels/Chat/SessionViewModel.swift

/// 会话管理 ViewModel
@MainActor
class SessionViewModel: ObservableObject {
    @Published var sessionId: String?
    @Published var agentType: AgentType?
    @Published var capabilities: AgentCapabilities?
    @Published var currentDoctorId: Int?
    @Published var currentDepartment: String?
    @Published var isLoading: Bool = false
    @Published var isConversationCompleted: Bool = false
    @Published var eventId: String?
    @Published var isNewEvent: Bool = false
    @Published var shouldShowDossierPrompt: Bool = false
    @Published var showGenerateConfirmation: Bool = false
    @Published var generateConfirmationMessage: String = ""
    @Published var errorMessage: String?
    @Published var showError: Bool = false

    private let sessionService: ChatSessionService
    private let apiService: APIServiceProtocol

    init(sessionService: ChatSessionService = .shared, apiService: APIServiceProtocol = APIService.shared) {
        self.sessionService = sessionService
        self.apiService = apiService
        setupBindings()
    }

    func initializeSession(doctorId: Int?, department: String?) async {
        isLoading = true
        defer { isLoading = false }

        do {
            let session = try await sessionService.createNewSession(
                doctorId: doctorId,
                department: department
            )
            sessionId = session.id
            agentType = session.agentType
            AppLogger.debug("会话初始化成功: \(session.id)")
        } catch {
            errorMessage = "无法创建会话"
            showError = true
        }
    }
}
```

```swift
// ViewModels/Chat/MessageViewModel.swift

/// 消息管理 ViewModel
@MainActor
class MessageViewModel: ObservableObject {
    @Published var messages: [UnifiedChatMessage] = []
    @Published var isSending: Bool = false
    @Published var isUploadingImage: Bool = false
    @Published var isAnalyzing: Bool = false
    @Published var streamingContent: String = ""
    @Published var streamingMessageId: UUID?
    @Published var currentActionMode: AgentAction?
    @Published var adviceHistory: [AdviceEntry] = []
    @Published var diagnosisCard: AgentDiagnosisCard?
    @Published var knowledgeRefs: [KnowledgeRef] = []
    @Published var reasoningSteps: [String] = []

    private let messageService: ChatMessageService

    init(messageService: ChatMessageService = .shared) {
        self.messageService = messageService
        setupBindings()
    }

    func sendMessage(content: String, attachments: [MessageAttachment] = []) async {
        isSending = true
        defer { isSending = false }

        do {
            await messageService.sendMessage(
                sessionId: sessionId,
                content: content,
                attachments: attachments
            )
        } catch {
            AppLogger.error("发送消息失败", error: error)
        }
    }
}
```

```swift
// ViewModels/Chat/VoiceInputViewModel.swift

/// 语音输入 ViewModel
@MainActor
class VoiceInputViewModel: ObservableObject {
    @Published var voiceState: VoiceState = .idle
    @Published var recognizedText: String = ""
    @Published var aiResponseText: String = ""
    @Published var audioLevel: Float = 0
    @Published var isMicrophoneMuted: Bool = false
    @Published var showExitConfirmation: Bool = false

    private let voiceService: ChatVoiceInputService

    init(voiceService: ChatVoiceInputService = .shared) {
        self.voiceService = voiceService
        setupBindings()
    }

    func startPressAndHoldRecording() async {
        await voiceService.startPressAndHoldRecording()
    }

    func stopPressAndHoldRecording() async {
        if let text = await voiceService.stopPressAndHoldRecording() {
            recognizedText = text
        }
    }

    func toggleMute(_ muted: Bool) {
        voiceService.toggleMute(muted)
    }
}
```

#### 步骤 2: 组合 ViewModel

```swift
// ViewModels/Chat/UnifiedChatViewModel.swift (重构后)

/// 统一聊天 ViewModel（组合多个子 ViewModel）
@MainActor
class UnifiedChatViewModel: ObservableObject {
    // 子 ViewModel
    @Published var sessionViewModel: SessionViewModel
    @Published var messageViewModel: MessageViewModel
    @Published var voiceInputViewModel: VoiceInputViewModel

    private init() {
        // 初始化子 ViewModel
        let sessionService = ChatSessionService()
        let messageService = ChatMessageService()
        let voiceService = ChatVoiceInputService()

        sessionViewModel = SessionViewModel(
            sessionService: sessionService,
            apiService: APIService.shared
        )
        messageViewModel = MessageViewModel(
            messageService: messageService
        )
        voiceInputViewModel = VoiceInputViewModel(
            voiceService: voiceService
        )

        // 转发对外暴露的关键属性
        setupExposedProperties()
    }

    private func setupExposedProperties() {
        // 将子 ViewModel 的关键属性转发到外部
        // 保持原有 API 兼容性
    }
}
```

---

## 六、性能优化

### 6.1 图片处理优化

#### 当前问题

图片缩放在主线程同步执行，可能阻塞 UI。

#### 优化方案

```swift
// Services/ImageProcessing/ImageResizer.swift

import Foundation
import UIKit
import Accelerate

/// 图片处理服务
@MainActor
class ImageResizer {
    static let shared = ImageResizer()

    /// 异步缩放图片
    func resize(_ image: UIImage, maxDimension: CGFloat) async -> UIImage {
        await Task.detached(priority: .userInitiated) {
            // 在后台线程执行图片处理
            return await Task.detached(priority: .utility) {
                // 使用 vImage API (iOS 15+)
                if #available(iOS 15.0, *) {
                    return await resizeUsingImageIO(image, maxDimension: maxDimension)
                } else {
                    // 降级到 UIGraphics
                    return resizeUsingUIGraphics(image, maxDimension: maxDimension)
                }
            }.value
        }.value
    }

    @available(iOS 15.0, *)
    private func resizeUsingImageIO(_ image: UIImage, maxDimension: CGFloat) async -> UIImage {
        let scale = maxDimension / max(image.size.width, image.size.height)

        return await withCheckedThrowingContinuation { continuation in
            guard let cgImage = image.cgImage else {
                continuation.resume(returning: image)
                return
            }

            let options: [CFDictionaryKey: Any] = [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceThumbnailMaxPixelSize: max(Int(maxDimension)),
                kCGImageSourceCreateThumbnailFromImageIfRepresentable: true
            ]

            guard let thumbnail = CGImageSourceCreateWithData(cgImage.data as CFData, options: options as CFDictionary),
                  let scaledImage = CGImageSourceCreateThumbnailFromImage(thumbnail, maxDimension) else {
                continuation.resume(returning: image)
                return
            }

            continuation.resume(returning: UIImage(cgImage: scaledImage))
        }
    }

    private func resizeUsingUIGraphics(_ image: UIImage, maxDimension: CGFloat) -> UIImage {
        // 原有降级实现
        let size = image.size
        let ratio = min(maxDimension / size.width, maxDimension / size.height)
        let newSize = CGSize(width: size.width * ratio, height: size.height * ratio)

        UIGraphicsBeginImageContextWithOptions(newSize, false, 1.0)
        image.draw(in: CGRect(origin: .zero, size: newSize))
        let resizedImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()

        return resizedImage ?? image
    }
}
```

### 6.2 内存管理优化

```swift
// 在 ViewModel 中添加内存清理
deinit {
    // 取消所有 Combine 订阅
    cancellables.forEach { $0.cancel() }

    // 清理资源
    voiceService?.cleanup()
    messageService?.clearMessages()

    AppLogger.cleanup("[ViewModel] 资源已清理")
}
```

### 6.3 列表性能优化

```swift
// 使用 LazyVStack 和 LazyVGrid 优化长列表
// 确保现有实现已使用 LazyVStack (已在代码中使用)

// 对于大型数据集，考虑分页加载
private var currentPage = 0
private let pageSize = 20

func loadMoreEventsIfNeeded() async {
    guard !isLoadingMore else { return }

    isLoadingMore = true
    defer { isLoadingMore = false }

    let newEvents = await apiService.fetchEvents(
        page: currentPage,
        pageSize: pageSize
    )

    events.append(contentsOf: newEvents)
    currentPage += 1
}
```

---

## 七、代码规范改进

### 7.1 命名规范

```swift
// ✅ 好的命名
let currentSessionId: String
var isLoadingEvents: Bool
func fetchUserSessions() async throws -> [Session]

// ❌ 不好的命名
let sid: String
var loading: Bool
func get() -> [Session]
```

### 7.2 访问控制

```swift
// 明确访问级别
public struct PublicAPI {
    public func doSomething() { ... }  // 对外公开
}

internal struct InternalAPI {
    internal func doSomething() { ... }  // 模块内可见
}

private struct PrivateAPI {
    private func doSomething() { ... }  // 仅文件内可见
}

fileprivate struct FilePrivateAPI {
    fileprivate func doSomething() { ... }  // 仅扩展内可见
}
```

### 7.3 MARK 注释规范

```swift
// MARK: - Public Properties  // 公开属性
// MARK: - Private Properties  // 私有属性
// MARK: - Initialization  // 初始化
// MARK: - Public Methods  // 公开方法
// MARK: - Private Methods  // 私有方法
// MARK: - Actions  // 操作方法
// MARK: - Callbacks  // 回调
```

### 7.4 文档注释

```swift
/// 会话管理 ViewModel
///
/// 负责管理 AI 咨询会话的生命周期，包括：
/// - 创建新会话
/// - 恢复已有会话
/// - 管理会话状态（对话完成、病历生成）
///
/// # 注意
/// 此 ViewModel 不直接处理消息发送，消息管理由 ``MessageViewModel`` 负责。
///
/// # Author
/// Refactored on 2026-02-12
@MainActor
class SessionViewModel: ObservableObject {
    // ...
}
```

---

## 八、实施优先级

### 第一阶段 (1-2 周): 基础改进

| 优先级 | 任务 | 预计时间 | 风险 |
|--------|------|----------|------|
| 🔴 P0 | 统一日志系统 | 1-2 天 | 低 |
| 🔴 P0 | 清理 TODO 注释 | 0.5 天 | 低 |
| 🟡 P1 | 定义 AppError 类型 | 1 天 | 低 |
| 🟡 P1 | 创建 ErrorHandler | 1 天 | 低 |
| 🟡 P1 | 定义 AppConfiguration | 0.5 天 | 低 |

### 第二阶段 (2-4 周): 架构优化

| 优先级 | 任务 | 预计时间 | 风险 |
|--------|------|----------|------|
| 🟡 P1 | 拆分 APIService | 3-5 天 | 中 |
| 🟡 P1 | 拆分 UnifiedChatViewModel | 5-7 天 | 中 |
| 🟡 P1 | 创建 SessionViewModel | 2-3 天 | 中 |
| 🟢 P2 | 创建 MessageViewModel | 2-3 天 | 中 |
| 🟢 P2 | 创建 VoiceInputViewModel | 2-3 天 | 中 |

### 第三阶段 (4-6 周): 性能优化

| 优先级 | 任务 | 预计时间 | 风险 |
|--------|------|----------|------|
| 🟢 P2 | 图片处理异步化 | 1-2 天 | 中 |
| 🟢 P2 | 添加 deinit 内存清理 | 1-2 天 | 中 |
| 🟢 P2 | 优化列表加载 | 2-3 天 | 低 |

---

## 九、测试建议

### 9.1 单元测试

```swift
// Tests/ViewModels/SessionViewModelTests.swift

import XCTest
@testable import xinlingyisheng

final class SessionViewModelTests: XCTestCase {
    func testInitializeSession_WhenSuccess_CreatesSession() async throws {
        // 测试实现
    }

    func testInitializeSession_WhenFailure_ShowsError() async throws {
        // 测试错误处理
    }
}
```

### 9.2 UI 测试

使用 Xcode 的 UI 测试功能验证关键用户流程：
- 登录流程
- 创建会话
- 发送消息
- 语音录制
- 图片上传

---

## 十、回滚计划

如果重构过程中发现问题，每个阶段都应该保持代码可工作的状态：

1. **每个新文件独立测试** - 不要批量修改
2. **保留原有文件作为参考** - 添加 `_OLD` 后缀
3. **逐步迁移调用** - 先新接口并行，再切换
4. **充分测试后再删除旧代码**

---

*方案文档生成时间: 2026-02-12*
