import Foundation
import os.log

/// 安全的 WebSocket 服务
/// Token 通过 HTTP Header 传递，而非 URL 参数
actor SecureWebSocketService {

    // MARK: - Singleton

    static let shared = SecureWebSocketService()

    // MARK: - Properties

    private var activeTask: URLSessionWebSocketTask?

    // 存储 Base URL 的副本（避免在非隔离上下文中访问静态属性）
    private nonisolated static let cachedBaseURL = "ws://localhost:8100/ws"

    // MARK: - 非隔离日志
    private nonisolated func log(_ message: String) {
        os_log("[WebSocket] %{public}@", log: .default, type: .info, message)
    }

    // MARK: - Public Methods

    /// 创建 WebSocket 连接
    /// - Parameters:
    ///   - endpoint: WebSocket 端点路径（如 "/ws/voice/asr"）
    ///   - token: 认证 Token
    /// - Returns: WebSocket 任务
    func connect(to endpoint: String, token: String) throws -> URLSessionWebSocketTask {
        let baseURL = Self.cachedBaseURL
        let urlString = baseURL + endpoint

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

        log("WebSocket connected to: \(endpoint)")

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
