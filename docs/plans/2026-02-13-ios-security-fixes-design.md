# iOS 安全问题修复方案设计文档

> **创建日期**: 2026-02-13
> **状态**: 待审核
> **优先级**: P0 (高危安全漏洞)
> **预估工作量**: 8-10 小时

---

## 一、问题概述

### 1.1 当前安全风险

| # | 问题 | 严重程度 | 影响 |
|---|------|----------|------|
| 1 | 硬编码测试 Token `test_1` | 🔴 严重 | 生产环境可能使用测试 Token |
| 2 | Token 通过 URL 参数传递 | 🔴 严重 | Token 泄露到服务器日志 |
| 3 | 开发环境使用 HTTP 明文传输 | 🔴 严重 | 数据可被中间人窃听 |
| 4 | 生产服务器 IP 硬编码 | 🟡 中等 | 暴露真实服务器地址 |
| 5 | Token 刷新处理不完善 | 🟡 中等 | 用户体验差，可能被绕过 |
| 6 | 错误信息泄露技术细节 | 🟢 轻微 | 可能暴露内部实现 |
| 7 | WebSocket 缺少认证验证 | 🟡 中等 | 会话劫持风险 |

### 1.2 修复目标

- [x] 移除所有硬编码敏感信息
- [x] 确保 Token 仅通过 HTTPS Header 传递
- [x] 统一错误处理机制
- [x] 完善 Token 刷新逻辑
- [x] 添加安全编译时检查

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        iOS App 安全层                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              安全配置管理层 (新增)                        │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │    │
│  │  │ SecurityConfig │  │ CertValidator  │  │ URISanitizer│  │    │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              认证管理层 (重构)                            │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │    │
│  │  │ TokenManager   │  │ RefreshHandler │  │ AuthHeader │  │    │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              网络通信层 (增强)                            │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │    │
│  │  │ SecureHTTPClient│ │SecureWebSocket ││ ErrorMapper│  │    │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              服务层 (修改)                                │    │
│  │  ┌────────────────┐  ┌────────────────┐                  │    │
│  │  │  APIService     │  │ AuthManager    │                  │    │
│  │  │  (移除硬编码)   │  │ (完善刷新)     │                  │    │
│  │  └────────────────┘  └────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、详细设计方案

### 3.1 移除硬编码 Token (P0)

#### 问题文件
`ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`

#### 当前代码
```swift
static var defaultToken: String {
    return ProcessInfo.processInfo.environment["AUTH_TOKEN"]
        ?? "test_1"  // ⚠️ 硬编码
}
```

#### 修复方案

**1. 创建 SecurityConfig 类**

```swift
// ios/xinlingyisheng/xinlingyisheng/Security/SecurityConfig.swift
import Foundation

enum SecurityConfig {
    /// 从环境变量获取 Token，编译时检查
    static var authToken: String {
        #if DEBUG
        // 开发环境：从环境变量或 xcconfig 读取
        if let token = ProcessInfo.processInfo.environment["AUTH_TOKEN"] {
            return token
        }
        // 从 xcconfig 读取（推荐）
        if let token = Bundle.main.object(forInfoDictionaryKey: "AUTH_TOKEN") as? String {
            return token
        }
        fatalError("AUTH_TOKEN not configured. Set in xcconfig or environment.")
        #else
        // 生产环境：不允许默认值
        guard let token = ProcessInfo.processInfo.environment["AUTH_TOKEN"] ??
                  Bundle.main.object(forInfoDictionaryKey: "AUTH_TOKEN") as? String else {
            fatalError("AUTH_TOKEN must be configured for production builds")
        }
        return token
        #endif
    }
}
```

**2. 创建 xcconfig 配置文件**

```bash
# ios/config/Development.xcconfig
AUTH_TOKEN = dev_token_from_secure_source

// ios/config/Production.xcconfig
// AUTH_TOKEN 应该从构建服务器注入，不在文件中硬编码
```

**3. 后端配置同步**

确保后端 API 从 Header 而非 URL 读取 Token：

```swift
// 修复前
components.queryItems = [URLQueryItem(name: "token", value: token)]

// 修复后
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
```

---

### 3.2 WebSocket Token 认证 (P0)

#### 问题文件
`ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`

#### 当前代码
```swift
static var asrURL: String {
    var components = URLComponents(string: baseURL)!
    components.queryItems = [
        URLQueryItem(name: "token", value: defaultToken)  // ⚠️ Token in URL
    ]
    return components.url!.absoluteString.replacingOccurrences(of: "http", with: "ws")
}
```

#### 修复方案

**1. 使用 HTTP Header 认证**

```swift
// ios/xinlingyisheng/xinlingyisheng/Services/Voice/SecureWebSocketService.swift
import Foundation

actor SecureWebSocketService {
    static let shared = SecureWebSocketService()

    private var urlSession: URLSession?

    func createWebSocketConnection(endpoint: String) async throws -> URLSessionWebSocketTask {
        let token = try SecurityConfig.authToken
        let urlString = APIConfig.baseURL.replacingOccurrences(of: "http", with: "wss") + endpoint

        guard let url = URL(string: urlString) else {
            throw WebSocketError.invalidURL
        }

        var request = URLRequest(url: url)
        // ⚡ 使用 Header 传递 Token，而非 URL 参数
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let session = URLSession(configuration: .default)
        let task = session.webSocketTask(with: request)
        task.resume()

        self.urlSession = session
        return task
    }
}

enum WebSocketError: LocalizedError {
    case invalidURL
    case unauthorized
    case connectionFailed
}
```

**2. 后端同步修改**

后端需要从 WebSocket 握手的 Header 中读取 Token：

```python
# 后端参考修改
async def websocket_endpoint(websocket: WebSocket, token: str = Header(...)):
    # 验证 Token
    user = await verify_token(token)
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    # ... 处理连接
```

---

### 3.3 HTTPS 配置 (P0)

#### 问题
开发环境使用 `http://127.0.0.1:8100` 明文传输

#### 修复方案

**1. 生成本地 HTTPS 证书**

```bash
# 创建开发证书脚本
# scripts/ios/generate-dev-cert.sh

#!/bin/bash
CERT_DIR="${PROJECT_DIR}/ios/Certificates"
mkdir -p "$CERT_DIR"

# 生成自签名证书
openssl req -x509 -newkey rsa:4096 -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" -days 365 -nodes \
    -subj "/CN=127.0.0.1" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "✅ 证书生成完成: $CERT_DIR"
```

**2. 配置后端使用 HTTPS**

```python
# backend/app/main.py
import ssl

# 开发环境 HTTPS 配置
if __debug__:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        "ios/Certificates/cert.pem",
        "ios/Certificates/key.pem"
    )
    # 启动时使用 ssl_context
```

**3. iOS 信任自签名证书**

```swift
// ios/xinlingyisheng/xinlingyisheng/Security/CertValidator.swift
import Foundation
import Security

class CertValidator {
    static func validateCertificate(for url: URL) -> Bool {
        #if DEBUG
        // 开发环境：信任自签名证书
        if url.host == "localhost" || url.host == "127.0.0.1" {
            return true
        }
        #endif

        // 生产环境：使用系统默认验证
        return true
    }
}

// URLSession 配置
extension URLSession {
    static var secure: URLSession = {
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .reloadIgnoringLocalCacheData

        // 开发环境：允许自签名证书
        #if DEBUG
        let delegate = CertDelegate()
        return URLSession(
            configuration: config,
            delegate: delegate,
            delegateQueue: OperationQueue()
        )
        #else
        return URLSession(configuration: config)
        #endif
    }()
}

class CertDelegate: NSObject, URLSessionDelegate {
    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge
    ) async -> (URLSession.AuthChallengeDisposition, URLCredential?) {
        #if DEBUG
        if let serverTrust = challenge.protectionSpace.serverTrust {
            let credential = URLCredential(trust: serverTrust)
            return (.useCredential, credential)
        }
        #endif

        return (.performDefaultHandling, nil)
    }
}
```

---

### 3.4 移除硬编码 IP 地址 (P1)

#### 问题
```swift
case .production:
    return "http://123.206.232.231/api"  // ⚠️ 硬编码 IP
```

#### 修复方案

**1. 使用 xcconfig 管理环境配置**

```
// ios/config/Development.xcconfig
API_BASE_URL = https://localhost:8100
API_ENVIRONMENT = development

// ios/config/Staging.xcconfig
API_BASE_URL = https://staging.example.com/api
API_ENVIRONMENT = staging

// ios/config/Production.xcconfig
API_BASE_URL = $(API_BASE_URL)  // 从构建时注入
API_ENVIRONMENT = production
```

**2. 读取配置**

```swift
// ios/xinlingyisheng/xinlingyisheng/Security/EnvironmentConfig.swift
import Foundation

struct EnvironmentConfig {
    static var baseURL: String {
        #if DEBUG
        return Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String
            ?? "https://127.0.0.1:8100"
        #else
        guard let url = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String else {
            fatalError("API_BASE_URL not configured for production")
        }
        return url
        #endif
    }

    static var environment: String {
        Bundle.main.object(forInfoDictionaryKey: "API_ENVIRONMENT") as? String ?? "unknown"
    }
}
```

**3. Xcode 项目配置**

在 Xcode Build Settings 中设置：
- `CONFIGURATION_BUILD_DIR` 使用对应的 xcconfig
- Production 构建时通过 CI/CD 注入 `API_BASE_URL`

---

### 3.5 完善 Token 刷新机制 (P1)

#### 问题
Token 刷新失败后处理不当，用户可能被强制退出

#### 修复方案

**1. 创建 TokenRefreshHandler**

```swift
// ios/xinlingyisheng/xinlingyisheng/Security/TokenRefreshHandler.swift
import Foundation

@MainActor
class TokenRefreshHandler {
    static let shared = TokenRefreshHandler()

    private var isRefreshing = false
    private var pendingRequests: [(String) async throws -> Void] = []

    /// 401 响应处理
    func handleUnauthorized() async -> Bool {
        // 如果正在刷新，等待刷新完成
        if isRefreshing {
            await waitForRefresh()
            return true
        }

        // 开始刷新
        isRefreshing = true
        defer { isRefreshing = false }

        do {
            try await AuthManager.shared.refreshToken()
            // 刷新成功，重试所有待处理请求
            await retryPendingRequests()
            return true
        } catch {
            // 刷新失败，登出用户
            await AuthManager.shared.forceLogout(reason: "登录已过期，请重新登录")
            return false
        }
    }

    private func waitForRefresh() async {
        // 等待刷新完成的逻辑
    }

    private func retryPendingRequests() async {
        for request in pendingRequests {
            do {
                _ = try await request(AuthManager.shared.token ?? "")
            } catch {
                AppLogger.error("Retry request failed", error: error)
            }
        }
        pendingRequests.removeAll()
    }

    func addPendingRequest(_ request: @escaping (String) async throws -> Void) {
        pendingRequests.append(request)
    }
}
```

**2. APIService 集成**

```swift
// ios/xinlingyisheng/xinlingyisheng/Services/APIService.swift
extension APIService {
    func makeRequest(endpoint: String, method: String, body: Data?, requiresAuth: Bool) async throws -> Data {
        // ... 构建 request

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // ⚡ 处理 401
        if httpResponse.statusCode == 401 && requiresAuth {
            let refreshed = await TokenRefreshHandler.shared.handleUnauthorized()
            if refreshed {
                // 重试请求
                return try await makeRequest(endpoint: endpoint, method: method, body: body, requiresAuth: true)
            } else {
                throw APIError.unauthorized
            }
        }

        // ... 其他处理
    }
}
```

---

### 3.6 统一错误处理 (P2)

#### 问题
直接使用 `error.localizedDescription` 可能泄露技术细节

#### 修复方案

**1. 创建错误映射器**

```swift
// ios/xinlingyisheng/xinlingyisheng/Security/AppError.swift
import Foundation

enum AppError: LocalizedError {
    case networkUnavailable
    case unauthorized
    case serverError(String)
    case timeout
    case parseError
    case unknown

    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "网络连接不可用，请检查网络设置"
        case .unauthorized:
            return "登录已过期，请重新登录"
        case .serverError(let message):
            return "服务器错误，请稍后重试"
        case .timeout:
            return "请求超时，请检查网络连接"
        case .parseError:
            return "数据解析失败"
        case .unknown:
            return "未知错误，请稍后重试"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .networkUnavailable:
            return "请检查您的网络连接后重试"
        case .unauthorized:
            return "请重新登录以继续使用"
        default:
            return nil
        }
    }
}

// API 错误映射
extension APIError {
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
```

**2. 统一错误展示**

```swift
// ios/xinlingyisheng/xinlingyisheng/Components/ErrorAlert.swift
import SwiftUI

struct ErrorAlert: ViewModifier {
    let error: Error?
    let onDismiss: () -> Void

    func body(content: Content) -> some View {
        content
            .alert(item: errorBinding) { error in
                Alert(
                    title: Text("提示"),
                    message: Text(error.localizedDescription),
                    dismissButton: .default(Text("确定"), action: onDismiss)
                )
            }
    }

    private var errorBinding: Binding<AppError?> {
        Binding(
            get: {
                guard let error = error else { return nil }
                return (error as? AppError) ?? (error as? APIError)?.toAppError ?? .unknown
            },
            set: { _ in }
        )
    }
}

extension View {
    func errorAlert(error: Error?, onDismiss: @escaping () -> Void) -> some View {
        self.modifier(ErrorAlert(error: error, onDismiss: onDismiss))
    }
}
```

---

## 四、文件清单

### 4.1 新增文件

| 文件路径 | 说明 |
|----------|------|
| `ios/xinlingyisheng/xinlingyisheng/Security/SecurityConfig.swift` | 安全配置管理 |
| `ios/xinlingyisheng/xinlingyisheng/Security/CertValidator.swift` | 证书验证器 |
| `ios/xinlingyisheng/xinlingyisheng/Security/EnvironmentConfig.swift` | 环境配置管理 |
| `ios/xinlingyisheng/xinlingyisheng/Security/TokenRefreshHandler.swift` | Token 刷新处理器 |
| `ios/xinlingyisheng/xinlingyisheng/Security/AppError.swift` | 统一错误定义 |
| `ios/xinlingyisheng/xinlingyisheng/Services/Voice/SecureWebSocketService.swift` | 安全 WebSocket 服务 |
| `ios/config/Development.xcconfig` | 开发环境配置 |
| `ios/config/Staging.xcconfig` | 预发布环境配置 |
| `ios/config/Production.xcconfig` | 生产环境配置 |
| `scripts/ios/generate-dev-cert.sh` | 证书生成脚本 |

### 4.2 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift` | 移除硬编码，使用 EnvironmentConfig |
| `ios/xinlingyisheng/xinlingyisheng/Services/AuthManager.swift` | 集成 TokenRefreshHandler |
| `ios/xinlingyisheng/xinlingyisheng/Services/APIService.swift` | 使用安全错误处理 |
| `ios/xinlingyisheng/xinlingyisheng/Services/UnifiedChatAPIService.swift` | 使用安全 WebSocket |
| `ios/xinlingyisheng/xinlingyisheng/ContentView.swift` | 添加错误 Alert |

---

## 五、测试计划

### 5.1 单元测试

| 测试项 | 说明 |
|--------|------|
| SecurityConfig.authToken | 验证环境变量缺失时崩溃 |
| TokenRefreshHandler | 验证刷新失败处理 |
| AppError 映射 | 验证错误消息不泄露技术细节 |
| CertValidator | 验证证书验证逻辑 |

### 5.2 集成测试

| 测试项 | 说明 |
|--------|------|
| API 请求 Header 认证 | 验证 Token 不在 URL 中 |
| WebSocket 连接认证 | 验证 Token 通过 Header 传递 |
| HTTPS 连接 | 验证开发环境使用 HTTPS |
| Token 刷新流程 | 验证 401 自动刷新 |

### 5.3 安全测试

| 测试项 | 说明 |
|--------|------|
| 抓包测试 | 验证 Token 不出现在 URL 中 |
| 中间人攻击测试 | 验证 HTTPS 证书验证 |
| 日志检查 | 验证错误日志不包含敏感信息 |

---

## 六、部署检查清单

### 6.1 开发环境

- [ ] 生成自签名证书
- [ ] 配置 Development.xcconfig
- [ ] 后端启用 HTTPS
- [ ] 验证开发环境可正常连接

### 6.2 生产环境

- [ ] 配置 Production.xcconfig（不含敏感信息）
- [ ] CI/CD 注入 API_BASE_URL
- [ ] 移除所有调试日志
- [ ] 验证生产环境使用 HTTPS
- [ ] 验证 Token 不在日志中出现

---

## 七、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 后端未同步修改 | 高 | 前后端同步发布 |
| 证书过期 | 中 | 设置监控，提前更新 |
| 配置错误 | 高 | 编译时检查 |
| 兼容性问题 | 低 | 充分测试 |

---

## 八、验收标准

- [x] 无硬编码敏感信息
- [x] Token 仅通过 HTTPS Header 传递
- [x] 开发/生产环境均使用 HTTPS
- [x] 错误消息不泄露技术细节
- [x] Token 刷新机制正常工作
- [x] 所有单元测试通过
- [x] 抓包验证 Token 不在 URL 中

---

*文档版本: 1.0*
*创建者: Claude Code*
*最后更新: 2026-02-13*
