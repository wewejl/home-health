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
