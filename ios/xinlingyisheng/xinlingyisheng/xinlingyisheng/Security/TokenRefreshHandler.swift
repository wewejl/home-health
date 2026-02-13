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
            try await AuthManager.shared.refreshTokenIfNeeded()
            SecurityConfig.log("Token refreshed successfully")
            return true
        } catch {
            SecurityConfig.log("Token refresh failed: \(error.localizedDescription)")
            // 刷新失败，登出用户
            await forceLogoutWithReason("登录已过期")
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

    /// 强制登出
    private func forceLogoutWithReason(_ reason: String) async {
        // 清理 Token
        AuthManager.shared.logout()
        // 发送通知
        NotificationCenter.default.post(
            name: Notification.Name("AuthenticationRequired"),
            object: nil,
            userInfo: ["reason": reason]
        )
    }
}
