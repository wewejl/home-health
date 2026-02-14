import Foundation
import SwiftUI
import Combine

@MainActor
class AuthManager: ObservableObject {
    static let shared = AuthManager()

    // MARK: - 全局通知
    static let unauthorizedNotification = Notification.Name("AuthManager.unauthorized")
    static let profileNeedsSetupNotification = Notification.Name("AuthManager.profileNeedsSetup")
    static let loginCompletedNotification = Notification.Name("AuthManager.loginCompleted")

    @Published var isLoggedIn: Bool = false
    @Published var currentUser: UserModel?
    @Published var token: String?
    @Published var refreshToken: String?
    @Published var showLogoutAlert: Bool = false
    @Published var logoutReason: String = ""
    @Published var isNewUser: Bool = false
    @Published var needsProfileSetup: Bool = false

    private let userKey = "current_user"
    private let keychainManager = KeychainManager.shared

    private init() {
        loadStoredAuth()
        setupNotificationObservers()
    }

    private func loadStoredAuth() {
        // 从 Keychain 读取 Token（安全存储）
        Task {
            do {
                let token = try await keychainManager.retrieveAsync(forKey: "auth_token")
                let refreshToken = try await keychainManager.retrieveAsync(forKey: "refresh_token")

                await MainActor.run {
                    self.token = token
                    self.refreshToken = refreshToken
                    self.isLoggedIn = true

                    // 从 UserDefaults 读取用户信息（非敏感数据）
                    if let userData = UserDefaults.standard.data(forKey: userKey),
                       let user = try? JSONDecoder().decode(UserModel.self, from: userData) {
                        self.currentUser = user
                        self.needsProfileSetup = !user.is_profile_completed
                    }
                }
                AppLogger.success("[Auth] Token 从 Keychain 加载成功")
            } catch {
                AppLogger.error("[Auth] 从 Keychain 加载 Token 失败", error: error)
            }
        }
    }
    
    private func setupNotificationObservers() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleUnauthorized),
            name: Self.unauthorizedNotification,
            object: nil
        )
    }
    
    @objc private func handleUnauthorized() {
        DispatchQueue.main.async {
            // 尝试刷新Token
            Task {
                let refreshed = await self.attemptTokenRefresh()
                if !refreshed {
                    await MainActor.run {
                        self.logoutReason = "登录已过期，请重新登录"
                        self.showLogoutAlert = true
                        self.logout()
                    }
                }
            }
        }
    }
    
    // MARK: - 登录
    func login(token: String, refreshToken: String? = nil, user: UserModel, isNewUser: Bool = false) {
        self.token = token
        self.refreshToken = refreshToken
        self.currentUser = user
        self.isLoggedIn = true
        self.isNewUser = isNewUser
        self.needsProfileSetup = !user.is_profile_completed

        // 持久化存储 - Token 使用 Keychain（安全存储）
        Task {
            do {
                try await keychainManager.saveAsync(token, forKey: "auth_token")
                if let refreshToken = refreshToken {
                    try await keychainManager.saveAsync(refreshToken, forKey: "refresh_token")
                }
                print("[Auth] Token 已保存到 Keychain")
            } catch {
                print("[Auth] 保存 Token 到 Keychain 失败: \(error.localizedDescription)")
            }
        }

        // 用户数据使用 UserDefaults 存储（非敏感数据）
        if let userData = try? JSONEncoder().encode(user) {
            UserDefaults.standard.set(userData, forKey: userKey)
        }

        // 日志埋点
        logEvent("login_success", data: ["user_id": user.id, "is_new_user": isNewUser])

        // 发送通知
        NotificationCenter.default.post(name: Self.loginCompletedNotification, object: nil)

        // 如果需要完善资料，发送通知
        if needsProfileSetup {
            NotificationCenter.default.post(name: Self.profileNeedsSetupNotification, object: nil)
        }
    }
    
    // MARK: - 登出
    func logout() {
        logEvent("logout", data: ["user_id": currentUser?.id ?? 0])

        self.token = nil
        self.refreshToken = nil
        self.currentUser = nil
        self.isLoggedIn = false
        self.isNewUser = false
        self.needsProfileSetup = false

        // 清除 Keychain 中的 Token
        Task {
            do {
                try await keychainManager.clearAllTokens()
                print("[Auth] Keychain 中的 Token 已清除")
            } catch {
                print("[Auth] 清除 Keychain Token 失败: \(error.localizedDescription)")
            }
        }

        // 清除 UserDefaults 中的用户数据
        UserDefaults.standard.removeObject(forKey: userKey)
    }
    
    // MARK: - 更新用户信息
    func updateUser(_ user: UserModel) {
        self.currentUser = user
        self.needsProfileSetup = !user.is_profile_completed
        
        if let userData = try? JSONEncoder().encode(user) {
            UserDefaults.standard.set(userData, forKey: userKey)
        }
        
        logEvent("profile_updated", data: ["user_id": user.id])
    }
    
    // MARK: - Token 刷新
    func attemptTokenRefresh() async -> Bool {
        guard let refreshToken = refreshToken else {
            print("[Auth] 无 refresh token，无法刷新")
            return false
        }

        do {
            let response = try await APIService.shared.refreshToken(refreshToken: refreshToken)

            await MainActor.run {
                self.token = response.token
                self.refreshToken = response.refresh_token
            }

            // 更新 Keychain 中的 Token
            try await keychainManager.saveAsync(response.token, forKey: "auth_token")
            // refresh_token 是非可选的 String，直接保存
            try await keychainManager.saveAsync(response.refresh_token, forKey: "refresh_token")

            print("[Auth] Token 刷新成功")
            logEvent("token_refreshed", data: [:])
            return true
        } catch {
            print("[Auth] Token 刷新失败: \(error.localizedDescription)")
            logEvent("token_refresh_failed", data: ["error": error.localizedDescription])
            return false
        }
    }
    
    // MARK: - Token 刷新 (抛出错误版本,供API重试使用)
    func refreshTokenIfNeeded() async throws {
        let success = await attemptTokenRefresh()
        if !success {
            throw APIError.unauthorized
        }
    }
    
    // MARK: - Token 验证
    var hasValidToken: Bool {
        guard let unwrappedToken = token else {
            return false
        }
        return !unwrappedToken.isEmpty
    }
    
    // MARK: - 日志埋点
    private func logEvent(_ event: String, data: [String: Any]) {
        // TODO: 接入正式埋点系统
        print("[AuthEvent] \(event): \(data)")
    }
}
