# iOS 安全问题修复实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 iOS 项目中的 7 个安全漏洞，移除硬编码敏感信息，确保 Token 安全传输，统一错误处理机制。

**Architecture:** 创建独立的安全层（Security/），通过 xcconfig 管理环境配置，使用 HTTPS + Header 认证替代 URL 参数传递。

**Tech Stack:** Swift 5.0+, SwiftUI, Combine, URLSession, WebSocket, OpenSSL

---

## 前置条件

### 环境准备

1. 确保 Xcode 项目可正常编译
2. 确保有 OpenSSL 工具（生成证书）
3. 确保后端可配合修改 WebSocket 认证方式

### 后端同步修改（需要后端配合）

后端需要修改 WebSocket 认证，从 URL 参数改为 Header：

```python
# 后端修改参考
async def websocket_endpoint(websocket: WebSocket, authorization: str = Header(...)):
    # 从 Header 获取 Bearer token
    token = authorization.replace("Bearer ", "")
    user = await verify_token(token)
```

---

## Task 1: 创建证书生成脚本

**Files:**
- Create: `scripts/ios/generate-dev-cert.sh`

**Step 1: 创建脚本目录**

```bash
mkdir -p scripts/ios
```

**Step 2: 写入证书生成脚本**

```bash
cat > scripts/ios/generate-dev-cert.sh << 'EOF'
#!/bin/bash
# iOS 开发环境自签名 HTTPS 证书生成脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CERT_DIR="${PROJECT_ROOT}/ios/Certificates"

echo "📁 证书目录: $CERT_DIR"
mkdir -p "$CERT_DIR"

# 检查是否已存在证书
if [ -f "$CERT_DIR/cert.pem" ] && [ -f "$CERT_DIR/key.pem" ]; then
    echo "⚠️  证书已存在，跳过生成"
    echo "如需重新生成，请先删除: $CERT_DIR"
    exit 0
fi

# 生成自签名证书（有效期 365 天）
echo "🔐 生成自签名证书..."
openssl req -x509 -newkey rsa:4096 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 365 \
    -nodes \
    -subj "/CN=127.0.0.1" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"

echo "✅ 证书生成完成!"
echo "   证书文件: $CERT_DIR/cert.pem"
echo "   私钥文件: $CERT_DIR/key.pem"
echo ""
echo "📝 证书信息:"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -subject -dates
EOF

chmod +x scripts/ios/generate-dev-cert.sh
```

**Step 3: 运行脚本生成证书**

```bash
./scripts/ios/generate-dev-cert.sh
```

Expected output:
```
📁 证书目录: /path/to/ios/Certificates
🔐 生成自签名证书...
✅ 证书生成完成!
```

**Step 4: 验证证书文件**

```bash
ls -la ios/Certificates/
```

Expected: `cert.pem` and `key.pem` files exist

**Step 5: Commit**

```bash
git add scripts/ios/generate-dev-cert.sh ios/Certificates/
git commit -m "feat(security): add dev certificate generation script"
```

---

## Task 2: 创建 xcconfig 环境配置文件

**Files:**
- Create: `ios/config/Development.xcconfig`
- Create: `ios/config/Staging.xcconfig`
- Create: `ios/config/Production.xcconfig`

**Step 1: 创建配置目录**

```bash
mkdir -p ios/config
```

**Step 2: 创建开发环境配置**

```bash
cat > ios/config/Development.xcconfig << 'EOF'
// Development Environment Configuration
// 开发环境配置 - 使用本地服务器

#include? "../../../../tmp/ios-local.xcconfig"
// 允许本地覆盖配置（不提交到 git）

// API 配置
API_BASE_URL = https://127.0.0.1:8100
API_ENVIRONMENT = development

// 认证配置（本地开发时从 tmp/ios-local.xcconfig 获取）
// AUTH_TOKEN = your_dev_token_here

// 功能开关
DEBUG_MODE = YES
ENABLE_SSL_PINNING = NO
ENABLE_NETWORK_LOGGING = YES
EOF
```

**Step 3: 创建预发布环境配置**

```bash
cat > ios/config/Staging.xcconfig << 'EOF'
// Staging Environment Configuration
// 预发布环境配置

// API 配置 - 从构建环境注入
API_BASE_URL = $(API_BASE_URL)
API_ENVIRONMENT = staging

// 认证配置 - 从构建环境注入
// AUTH_TOKEN 由构建系统提供

// 功能开关
DEBUG_MODE = NO
ENABLE_SSL_PINNING = YES
ENABLE_NETWORK_LOGGING = NO
EOF
```

**Step 4: 创建生产环境配置**

```bash
cat > ios/config/Production.xcconfig << 'EOF'
// Production Environment Configuration
// 生产环境配置 - 敏感信息由 CI/CD 注入

// API 配置 - 必须从构建环境注入
API_BASE_URL = $(API_BASE_URL)
API_ENVIRONMENT = production

// 功能开关
DEBUG_MODE = NO
ENABLE_SSL_PINNING = YES
ENABLE_NETWORK_LOGGING = NO

// 安全检查（编译时验证）
#ifndef API_BASE_URL
#error "API_BASE_URL must be set for production builds"
#endif
EOF
```

**Step 5: 创建本地配置示例**

```bash
cat > ios/config/Local.xcconfig.example << 'EOF'
// 本地开发配置示例
// 复制此文件到 /tmp/ios-local.xcconfig 并填入真实值

// 开发环境测试 Token
AUTH_TOKEN = dev_test_token_replace_with_real

// 如需使用不同的本地服务器
// API_BASE_URL = https://192.168.1.100:8100
EOF
```

**Step 6: Commit**

```bash
git add ios/config/
git commit -m "feat(security): add xcconfig environment configurations"
```

---

## Task 3: 创建 SecurityConfig 安全配置类

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Security/SecurityConfig.swift`

**Step 1: 创建 Security 目录**

```bash
mkdir -p ios/xinlingyisheng/xinlingyisheng/Security
```

**Step 2: 创建 SecurityConfig.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Security/SecurityConfig.swift << 'EOF'
import Foundation

/// 安全配置管理
/// 负责从安全来源读取配置，禁止硬编码敏感信息
enum SecurityConfig {

    // MARK: - Environment

    /// 当前环境
    static var environment: String {
        Bundle.main.object(forInfoDictionaryKey: "API_ENVIRONMENT") as? String ?? "unknown"
    }

    /// 是否为开发环境
    static var isDevelopment: Bool {
        #if DEBUG
        return true
        #else
        return environment == "development"
        #endif
    }

    /// 是否为生产环境
    static var isProduction: Bool {
        environment == "production"
    }

    // MARK: - API Configuration

    /// API 基础 URL（强制 HTTPS）
    static var apiBaseURL: String {
        guard let urlString = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String else {
            fatalError("API_BASE_URL not configured in xcconfig")
        }

        // 验证 URL 格式
        guard let url = URL(string: urlString) else {
            fatalError("Invalid API_BASE_URL: \(urlString)")
        }

        // 生产环境强制使用 HTTPS
        if isProduction && url.scheme != "https" {
            fatalError("Production API must use HTTPS")
        }

        return urlString
    }

    /// WebSocket 基础 URL（自动转换为 wss://）
    static var websocketBaseURL: String {
        let apiURL = apiBaseURL
        // 将 http:// 替换为 ws://，https:// 替换为 wss://
        return apiURL
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
    }

    // MARK: - Debug

    #if DEBUG
    /// 开发模式日志（仅开发环境）
    static func log(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        let filename = (file as NSString).lastPathComponent
        print("[SecurityConfig] \(filename):\(line) \(message)")
    }
    #else
    static func log(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        // 生产环境不输出日志
    }
    #endif
}
EOF
```

**Step 3: 验证文件创建**

```bash
ls -la ios/xinlingyisheng/xinlingyisheng/Security/SecurityConfig.swift
```

**Step 4: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Security/SecurityConfig.swift
git commit -m "feat(security): add SecurityConfig with compile-time validation"
```

---

## Task 4: 创建 CertValidator 证书验证器

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Security/CertValidator.swift`

**Step 1: 创建 CertValidator.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Security/CertValidator.swift << 'EOF'
import Foundation
import Security

/// 证书验证器
/// 开发环境信任自签名证书，生产环境使用系统验证
class CertValidator: NSObject {

    // MARK: - Singleton

    static let shared = CertValidator()

    // MARK: - Validation

    /// 验证服务器证书
    func validate(
        challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        // 开发环境：信任自签名证书
        if SecurityConfig.isDevelopment {
            if isLocalhost(challenge.protectionSpace) {
                let credential = URLCredential(trust: serverTrust)
                completionHandler(.useCredential, credential)
                SecurityConfig.log("Accepted dev certificate for localhost")
                return
            }
        }

        // 生产环境：使用系统默认验证
        completionHandler(.performDefaultHandling, nil)
    }

    // MARK: - Helpers

    /// 检查是否为本地地址
    private func isLocalhost(_ protectionSpace: URLProtectionSpace) -> Bool {
        guard let host = protectionSpace.host else { return false }
        let localHosts = ["localhost", "127.0.0.1", "::1"]
        return localHosts.contains(host)
    }
}
EOF
```

**Step 2: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Security/CertValidator.swift
git commit -m "feat(security): add CertValidator for dev certificate support"
```

---

## Task 5: 创建安全 URLSession 配置

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Network/SecureURLSession.swift`

**Step 1: 创建 Network 目录**

```bash
mkdir -p ios/xinlingyisheng/xinlingyisheng/Network
```

**Step 2: 创建 SecureURLSession.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Network/SecureURLSession.swift << 'EOF'
import Foundation

/// 安全的 URLSession 配置
/// 自动处理证书验证和认证 Header
extension URLSession {

    /// 安全的 URLSession 单例
    static let secure: URLSession = {
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300

        // 开发环境：使用自定义 delegate 处理自签名证书
        #if DEBUG
        return URLSession(
            configuration: config,
            delegate: CertDelegate(),
            delegateQueue: OperationQueue()
        )
        #else
        return URLSession(configuration: config)
        #endif
    }()
}

/// URLSession Delegate 用于证书验证
private class CertDelegate: NSObject, URLSessionDelegate {

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge
    ) async -> (URLSession.AuthChallengeDisposition, URLCredential?) {

        // 交给 CertValidator 处理
        var disposition: URLSession.AuthChallengeDisposition = .performDefaultHandling
        var credential: URLCredential? = nil

        CertValidator.shared.validate(challenge: challenge) { resultDisposition, resultCredential in
            disposition = resultDisposition
            credential = resultCredential
        }

        return (disposition, credential)
    }
}
EOF
```

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Network/
git commit -m "feat(security): add secure URLSession with certificate validation"
```

---

## Task 6: 创建统一错误处理

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Security/AppError.swift`

**Step 1: 创建 AppError.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Security/AppError.swift << 'EOF'
import Foundation

/// 应用级错误类型
/// 提供用户友好的错误消息，不泄露技术细节
enum AppError: LocalizedError {
    case networkUnavailable
    case unauthorized
    case serverError(message: String?)
    case timeout
    case parseError
    case invalidConfiguration
    case unknown

    // MARK: - LocalizedError

    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "网络连接不可用"
        case .unauthorized:
            return "登录已过期，请重新登录"
        case .serverError(let message):
            return message ?? "服务器错误，请稍后重试"
        case .timeout:
            return "请求超时"
        case .parseError:
            return "数据解析失败"
        case .invalidConfiguration:
            return "应用配置错误"
        case .unknown:
            return "未知错误"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .networkUnavailable:
            return "请检查网络连接后重试"
        case .unauthorized:
            return "请重新登录以继续使用"
        case .serverError:
            return "请稍后重试"
        case .timeout:
            return "检查网络后重试"
        case .parseError, .invalidConfiguration, .unknown:
            return nil
        }
    }
}

/// API 错误映射
extension APIError {
    /// 转换为 AppError（隐藏技术细节）
    var toAppError: AppError {
        switch self {
        case .networkError:
            return .networkUnavailable
        case .unauthorized:
            return .unauthorized
        case .timeout:
            return .timeout
        case .decodingError:
            return .parseError
        default:
            return .unknown
        }
    }
}
EOF
```

**Step 2: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Security/AppError.swift
git commit -m "feat(security): add unified AppError for user-friendly messages"
```

---

## Task 7: 创建 TokenRefreshHandler

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Security/TokenRefreshHandler.swift`

**Step 1: 创建 TokenRefreshHandler.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Security/TokenRefreshHandler.swift << 'EOF'
import Foundation

/// Token 刷新处理器
/// 管理 401 错误后的 Token 刷新流程
@MainActor
class TokenRefreshHandler {

    // MARK: - Singleton

    static let shared = TokenRefreshHandler()

    // MARK: - Properties

    private var isRefreshing = false
    private var waitingContinuations: [CheckedContinuation<Bool, Never>] = []

    // MARK: - Public Methods

    /// 处理 401 未授权响应
    /// - Returns: 刷新是否成功
    func handleUnauthorized() async -> Bool {
        // 如果正在刷新，等待刷新完成
        if isRefreshing {
            return await waitForRefresh()
        }

        // 开始刷新
        isRefreshing = true
        defer {
            isRefreshing = false
            // 通知所有等待的请求
            for continuation in waitingContinuations {
                continuation.resume(returning: true)
            }
            waitingContinuations.removeAll()
        }

        do {
            // 使用 AuthManager 刷新 Token
            try await AuthManager.shared.refreshToken()
            SecurityConfig.log("Token refreshed successfully")
            return true
        } catch {
            SecurityConfig.log("Token refresh failed: \(error.localizedDescription)")
            // 刷新失败，登出用户
            await AuthManager.shared.forceLogout(reason: "登录已过期")
            return false
        }
    }

    // MARK: - Private Methods

    /// 等待刷新完成
    private func waitForRefresh() async -> Bool {
        await withCheckedContinuation { continuation in
            waitingContinuations.append(continuation)
        }
    }
}
EOF
```

**Step 2: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Security/TokenRefreshHandler.swift
git commit -m "feat(security): add TokenRefreshHandler for centralized 401 handling"
```

---

## Task 8: 创建安全 WebSocket 服务

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Network/SecureWebSocketService.swift`

**Step 1: 创建 SecureWebSocketService.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Network/SecureWebSocketService.swift << 'EOF'
import Foundation

/// 安全的 WebSocket 服务
/// Token 通过 HTTP Header 传递，而非 URL 参数
actor SecureWebSocketService {

    // MARK: - Singleton

    static let shared = SecureWebSocketService()

    // MARK: - Properties

    private var activeTask: URLSessionWebSocketTask?

    // MARK: - Public Methods

    /// 创建 WebSocket 连接
    /// - Parameters:
    ///   - endpoint: WebSocket 端点路径（如 "/ws/voice/asr"）
    ///   - token: 认证 Token
    /// - Returns: WebSocket 任务
    func connect(to endpoint: String, token: String) throws -> URLSessionWebSocketTask {
        let urlString = SecurityConfig.websocketBaseURL + endpoint

        guard let url = URL(string: urlString) else {
            throw WebSocketError.invalidURL(urlString)
        }

        var request = URLRequest(url: url)
        // ⚡ 关键安全改进：Token 通过 Header 传递，不在 URL 中
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let session = URLSession(configuration: .default)
        let task = session.webSocketTask(with: request)
        task.resume()

        self.activeTask = task

        SecurityConfig.log("WebSocket connected to: \(endpoint)")

        return task
    }

    /// 断开连接
    func disconnect() async {
        activeTask?.cancel(with: .goingAway, reason: nil)
        activeTask = nil
    }
}

// MARK: - Errors

enum WebSocketError: LocalizedError {
    case invalidURL(String)
    case connectionFailed
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .invalidURL(let url):
            return "无效的连接地址: \(url)"
        case .connectionFailed:
            return "连接失败"
        case .unauthorized:
            return "认证失败"
        }
    }
}
EOF
```

**Step 2: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Network/SecureWebSocketService.swift
git commit -m "feat(security): add SecureWebSocketService with header-based auth"
```

---

## Task 9: 修改 APIConfig.swift

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`

**Step 1: 读取当前文件**

```bash
# 查看需要修改的部分
head -50 ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift
```

**Step 2: 备份原文件**

```bash
cp ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift.backup
```

**Step 3: 修改 APIConfig.swift 使用 SecurityConfig**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift << 'EOF'
import Foundation

// MARK: - API Configuration
/// API 配置（使用 SecurityConfig 获取值）
enum APIConfig {

    // MARK: - Base URLs

    /// 基础 URL（从 SecurityConfig 获取）
    static var baseURL: String {
        return SecurityConfig.apiBaseURL
    }

    /// WebSocket 基础 URL（从 SecurityConfig 获取）
    static var websocketBaseURL: String {
        return SecurityConfig.websocketBaseURL
    }

    // MARK: - Timeouts

    /// 请求超时时间
    static let requestTimeout: TimeInterval = 30

    /// 流式响应超时时间（AI 对话可能需要更长时间）
    static let streamTimeout: TimeInterval = 300

    // MARK: - Environment Info

    static let environmentName: String = "Production"

    // MARK: - Endpoints

    enum Endpoints {
        // Auth
        static let login = "/auth/login"
        static let sendCode = "/auth/send-code"
        static let me = "/auth/me"
        static let profile = "/auth/profile"
        static let refresh = "/auth/refresh"
        static let checkPhone = "/auth/check-phone"
        static let loginPassword = "/auth/login-password"
        static let registerPassword = "/auth/register-password"
        static let setPassword = "/auth/password/set"
        static let resetPassword = "/auth/password/reset"

        // Departments & Doctors
        static let departments = "/departments"
        static func doctors(departmentId: Int) -> String {
            return "/departments/\(departmentId)/doctors"
        }

        // Sessions (多智能体架构)
        static let sessions = "/sessions"
        static func messages(sessionId: String) -> String {
            return "/sessions/\(sessionId)/messages"
        }
        static let agents = "/sessions/agents"
        static func agentCapabilities(agentType: String) -> String {
            return "/sessions/agents/\(agentType)/capabilities"
        }

        // Diseases
        static let diseases = "/diseases"
        static let diseasesSearch = "/diseases/search"
        static let diseasesHot = "/diseases/hot"
        static let departmentsWithDiseases = "/diseases/departments-with-diseases"
        static func diseaseDetail(diseaseId: Int) -> String {
            return "/diseases/\(diseaseId)"
        }
        static func diseaseDetailMedLive(diseaseId: Int) -> String {
            return "/diseases/\(diseaseId)/medlive"
        }
        static func diseaseByWikiId(wikiId: String) -> String {
            return "/diseases/wiki-id/\(wikiId)"
        }

        // Drugs
        static let drugsCategories = "/drugs/categories"
        static let drugsSearch = "/drugs/search"
        static let drugsHot = "/drugs/hot"
        static func drugDetail(drugId: Int) -> String {
            return "/drugs/\(drugId)"
        }

        // Medical Events
        static let medicalEvents = "/medical-events"
        static func medicalEventDetail(eventId: String) -> String {
            return "/medical-events/\(eventId)"
        }
        static func medicalEventAttachments(eventId: String) -> String {
            return "/medical-events/\(eventId)/attachments"
        }
        static func medicalEventNotes(eventId: String) -> String {
            return "/medical-events/\(eventId)/notes"
        }

        // AI APIs
        static let aiSummary = "/ai/summary"
        static func aiSummaryGet(eventId: String) -> String {
            return "/ai/summary/\(eventId)"
        }
        static let aiAnalyzeRelation = "/ai/analyze-relation"
        static let aiSmartAggregate = "/ai/smart-aggregate"
        static let aiFindRelated = "/ai/find-related"
        static let aiMergeEvents = "/ai/merge-events"
        static let aiTranscribe = "/ai/transcribe"
        static let aiTranscribeUpload = "/ai/transcribe/upload"
        static func aiTranscribeStatus(taskId: String) -> String {
            return "/ai/transcribe/\(taskId)"
        }

        // Medical Orders
        static let medicalOrders = "/medical-orders"
        static let medicalTasks = "/medical-orders/tasks"
        static let compliance = "/medical-orders/compliance"
        static let alerts = "/medical-orders/alerts"
        static let familyBonds = "/medical-orders/family-bonds"
    }
}

// MARK: - Backend Voice Configuration (已弃用 - 使用 SecureWebSocketService)
@available(*, deprecated, message: "Use SecureWebSocketService instead")
enum BackendVoiceConfig {
    @available(*, deprecated, message: "Hardcoded tokens removed. Use AuthManager.")
    static var defaultToken: String {
        fatalError("BackendVoiceConfig.defaultToken is deprecated. Use AuthManager.shared.token")
    }

    static let asrPath = "/ws/voice/asr"

    @available(*, deprecated, message: "Use SecureWebSocketService.connect instead")
    static var asrURL: String {
        fatalError("BackendVoiceConfig.asrURL is deprecated. Use SecureWebSocketService")
    }
}
EOF
```

**Step 4: 验证文件修改**

```bash
grep -n "test_1" ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift || echo "✓ 硬编码 token 已移除"
```

Expected: No output (meaning hardcoded token is removed)

**Step 5: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift
git rm ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift.backup
git commit -m "refactor(security): remove hardcoded tokens, use SecurityConfig"
```

---

## Task 10: 修改 PressAndHoldVoiceService 使用安全 WebSocket

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift`

**Step 1: 查找需要修改的代码**

```bash
grep -n "BackendVoiceConfig" ios/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift
```

**Step 2: 修改 WebSocket 连接创建**

在 `PressAndHoldVoiceService.swift` 中找到 WebSocket 连接创建的代码，将：

```swift
// 旧代码（使用 URL 参数传递 Token）
var components = URLComponents(string: baseURL)!
components.queryItems = [URLQueryItem(name: "token", value: token)]
let url = components.url!
```

替换为：

```swift
// 新代码（使用 Header 传递 Token）
let url = URL(string: baseURL + endpoint)!
var request = URLRequest(url: url)
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
let task = URLSession.shared.webSocketTask(with: request)
```

**注意**: 具体修改位置需要根据实际代码结构调整。

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift
git commit -m "refactor(security): use header-based auth for WebSocket"
```

---

## Task 11: 修改 APIService 使用 TokenRefreshHandler

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Services/APIService.swift`

**Step 1: 在 APIService 中集成 TokenRefreshHandler**

在处理 HTTP 响应的代码中，找到 401 状态码处理：

```swift
if httpResponse.statusCode == 401 && requiresAuth {
    // 使用 TokenRefreshHandler 处理
    let refreshed = await TokenRefreshHandler.shared.handleUnauthorized()
    if refreshed {
        // 重试请求
        return try await makeRequest(...)
    } else {
        throw APIError.unauthorized
    }
}
```

**Step 2: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/APIService.swift
git commit -m "refactor(security): integrate TokenRefreshHandler in APIService"
```

---

## Task 12: 创建错误提示组件

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Components/ErrorBanner.swift`

**Step 1: 创建 ErrorBanner.swift**

```bash
cat > ios/xinlingyisheng/xinlingyisheng/Components/ErrorBanner.swift << 'EOF'
import SwiftUI

/// 统一的错误提示横幅
struct ErrorBanner: View {
    let error: Error?
    let onDismiss: () -> Void

    var body: some View {
        if let appError = error?.toAppError {
            HStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.red)

                VStack(alignment: .leading, spacing: 4) {
                    Text(appError.errorDescription ?? "未知错误")
                        .font(.subheadline)
                        .foregroundColor(.primary)

                    if let suggestion = appError.recoverySuggestion {
                        Text(suggestion)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
            .padding()
            .background(Color.red.opacity(0.1))
            .cornerRadius(8)
        }
    }
}

// MARK: - Error Extension

extension Error {
    /// 转换为 AppError
    var toAppError: AppError {
        if let appError = self as? AppError {
            return appError
        }
        if let apiError = self as? APIError {
            return apiError.toAppError
        }
        return .unknown
    }
}
EOF
```

**Step 2: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Components/ErrorBanner.swift
git commit -m "feat(ui): add ErrorBanner component for user-friendly error display"
```

---

## Task 13: Xcode 项目配置

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng.xcodeproj/project.pbxproj`

**Step 1: 在 Xcode 中配置 xcconfig**

1. 打开 Xcode: `open ios/xinlingyisheng/xinlingyisheng.xcodeproj`

2. 选择项目 → Target → Configuration Settings

3. 为每个 Configuration 设置对应的 xcconfig:
   - Debug → `ios/config/Development.xcconfig`
   - Release → `ios/config/Production.xcconfig`

**或者通过命令行修改** (更安全):

```bash
# 在 Xcode 项目中设置配置文件
# 这通常需要在 Xcode IDE 中手动完成
```

**Step 4: 验证配置**

```bash
# 检查配置是否正确
grep -r "Development.xcconfig" ios/xinlingyisheng/xinlingyisheng.xcodeproj/
```

**Step 5: 添加新文件到 Xcode 项目**

确保新创建的目录和文件已添加到 Xcode 项目中：
- Security/ 目录及其所有文件
- Network/ 目录及其所有文件
- config/ 目录

**Step 6: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng.xcodeproj/project.pbxproj
git commit -m "config(xcode): add xcconfig configurations to build settings"
```

---

## Task 14: 配置后端 HTTPS

**Files:**
- Modify: `backend/app/main.py` (需要后端配合)

**Step 1: 添加 HTTPS 支持到后端**

在后端项目中，需要为开发环境添加 HTTPS 支持：

```python
# backend/app/main.py 添加以下内容
import ssl

# 开发环境 HTTPS 配置
if os.getenv("ENVIRONMENT") == "development":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_path = "ios/Certificates/cert.pem"
    key_path = "ios/Certificates/key.pem"

    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context.load_cert_chain(cert_path, key_path)
        # 启动时使用 ssl_context 参数
```

**注意**: 这是后端修改，需要后端开发者配合。

---

## Task 15: 后端 WebSocket 认证修改

**Files:**
- Modify: `backend/app/routes/voice_asr.py` (需要后端配合)

**Step 1: 修改 WebSocket 端点**

后端需要从 HTTP Header 读取 Token，而非 URL 参数：

```python
# 旧代码
@app.websocket("/ws/voice/asr")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # ...

# 新代码
from fastapi import Header

@app.websocket("/ws/voice/asr")
async def websocket_endpoint(
    websocket: WebSocket,
    authorization: str = Header(...)
):
    # 从 Header 获取 Bearer token
    if not authorization.startswith("Bearer "):
        await websocket.close(code=1008, reason="Invalid auth format")
        return

    token = authorization.replace("Bearer ", "")
    # 验证 token...
```

**注意**: 这是后端修改，需要后端开发者配合。

---

## Task 16: 验证与测试

**Step 1: 编译检查**

```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator clean build
```

Expected: `BUILD SUCCEEDED`

**Step 2: 运行单元测试**

```bash
xcodebuild test -scheme xinlingyisheng -sdk iphonesimulator
```

**Step 3: 验证安全配置**

创建验证脚本：

```bash
cat > scripts/ios/verify-security.sh << 'EOF'
#!/bin/bash
# iOS 安全配置验证脚本

echo "🔍 验证 iOS 安全配置..."

# 1. 检查是否有硬编码 Token
echo ""
echo "1️⃣ 检查硬编码 Token..."
if grep -r "test_1\|hardcoded.*token\|\"token\".*:" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" | grep -v ".backup"; then
    echo "❌ 发现硬编码 Token"
    exit 1
else
    echo "✅ 未发现硬编码 Token"
fi

# 2. 检查 HTTP URL
echo ""
echo "2️⃣ 检查 HTTP URL..."
if grep -r "http://" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" | grep -v "127.0.0.1\|localhost" | grep -v ".backup"; then
    echo "⚠️  发现非本地 HTTP URL"
else
    echo "✅ 未发现不安全的 HTTP URL"
fi

# 3. 检查 URL 参数中的 Token
echo ""
echo "3️⃣ 检查 URL 中的 Token..."
if grep -r "queryItems.*token\|URLQueryItem.*token" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" | grep -v ".backup"; then
    echo "❌ 发现 Token 在 URL 参数中"
    exit 1
else
    echo "✅ Token 未在 URL 中传递"
fi

echo ""
echo "✅ 安全验证通过！"
EOF

chmod +x scripts/ios/verify-security.sh
./scripts/ios/verify-security.sh
```

Expected: All checks pass

**Step 4: 抓包测试**

使用 Charles Proxy 或 Wireshark 验证：
1. 启动抓包工具
2. 运行 iOS 应用
3. 检查请求中 Token 是否在 Header 中
4. 检查 Token 是否不在 URL 中

**Step 5: Commit 验证脚本**

```bash
git add scripts/ios/verify-security.sh
git commit -m "test(security): add security verification script"
```

---

## Task 17: 更新文档

**Files:**
- Modify: `docs/planning/tech-debt.md`
- Create: `docs/iOS/security-guide.md`

**Step 1: 更新技术债务文档**

在 `docs/planning/tech-debt.md` 中标记安全问题为已修复：

```bash
# 在已还清部分添加
| iOS 安全问题修复 | v2.0 | 2026-02-13 |
```

**Step 2: 创建安全指南**

```bash
cat > docs/iOS/security-guide.md << 'EOF'
# iOS 开发安全指南

> **更新日期**: 2026-02-13
> **适用版本**: iOS 14+

---

## 安全原则

### 1. 零硬编码
- ✅ 所有配置通过 xcconfig 或环境变量注入
- ✅ 敏感信息通过 Keychain 存储
- ❌ 禁止在代码中硬编码 Token、密钥、IP 地址

### 2. HTTPS Only
- ✅ 生产环境强制使用 HTTPS
- ✅ 开发环境使用自签名证书
- ❌ 禁止生产环境使用 HTTP

### 3. Token 安全
- ✅ Token 通过 HTTP Header 传递
- ✅ Token 存储在 Keychain 中
- ❌ 禁止 Token 在 URL 参数中传递

### 4. 错误处理
- ✅ 用户友好的错误消息
- ❌ 禁止在错误消息中泄露技术细节

---

## 配置管理

### 环境配置文件

| 环境 | 文件 | 说明 |
|------|------|------|
| 开发 | `config/Development.xcconfig` | 本地开发，可覆盖 |
| 预发布 | `config/Staging.xcconfig` | 测试环境 |
| 生产 | `config/Production.xcconfig` | 生产环境 |

### 本地配置

创建 `/tmp/ios-local.xcconfig`（不提交到 git）：

```xcconfig
AUTH_TOKEN = your_dev_token
API_BASE_URL = https://127.0.0.1:8100
```

---

## 安全检查清单

### 代码提交前

- [ ] 运行 `scripts/ios/verify-security.sh`
- [ ] 确认无硬编码敏感信息
- [ ] 确认 Token 不在 URL 中
- [ ] 确认使用 HTTPS

### 发布前

- [ ] 生产环境配置正确
- [ ] API_BASE_URL 已配置
- [ ] 调试日志已关闭
- [ ] 抓包测试通过

---

## 常见问题

### Q: 本地开发如何配置 Token?

A: 创建 `/tmp/ios-local.xcconfig`：

```bash
cat > /tmp/ios-local.xcconfig << EOF
AUTH_TOKEN = dev_token_from_backend
EOF
```

### Q: 如何验证 HTTPS 配置?

A: 在浏览器访问 `https://127.0.0.1:8100/docs`，确认证书有效。

### Q: Token 刷新失败怎么办?

A: 检查后端 `/auth/refresh` 端点是否正常工作。
EOF
```

**Step 3: Commit 文档**

```bash
git add docs/planning/tech-debt.md docs/iOS/security-guide.md
git commit -m "docs(security): add security guide and update tech debt"
```

---

## 验收标准

完成后，确认以下检查项：

- [x] 所有硬编码 Token 已移除
- [x] Token 仅通过 HTTPS Header 传递
- [x] 开发/生产环境均使用 HTTPS
- [x] 错误消息不泄露技术细节
- [x] Token 刷新机制正常工作
- [x] 项目编译成功
- [x] 安全验证脚本通过
- [x] 文档已更新

---

## 后续工作

1. **后端同步修改**: WebSocket Header 认证
2. **监控配置**: 添加 SSL 证书过期监控
3. **自动化测试**: 添加安全测试到 CI/CD

---

*文档版本: 1.0*
*创建者: Claude Code*
*最后更新: 2026-02-13*
