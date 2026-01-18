import Foundation
import SwiftUI
import Combine

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
    
    private let tokenKey = "auth_token"
    private let refreshTokenKey = "refresh_token"
    private let userKey = "current_user"
    
    private init() {
        loadStoredAuth()
        setupNotificationObservers()
    }
    
    private func loadStoredAuth() {
        if let token = UserDefaults.standard.string(forKey: tokenKey) {
            self.token = token
            self.refreshToken = UserDefaults.standard.string(forKey: refreshTokenKey)
            self.isLoggedIn = true
            
            if let userData = UserDefaults.standard.data(forKey: userKey),
               let user = try? JSONDecoder().decode(UserModel.self, from: userData) {
                self.currentUser = user
                self.needsProfileSetup = !user.is_profile_completed
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
        
        // 持久化存储
        UserDefaults.standard.set(token, forKey: tokenKey)
        if let refreshToken = refreshToken {
            UserDefaults.standard.set(refreshToken, forKey: refreshTokenKey)
        }
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
        
        UserDefaults.standard.removeObject(forKey: tokenKey)
        UserDefaults.standard.removeObject(forKey: refreshTokenKey)
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
                
                UserDefaults.standard.set(response.token, forKey: tokenKey)
                UserDefaults.standard.set(response.refresh_token, forKey: refreshTokenKey)
            }
            
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
        return token != nil && !token!.isEmpty
    }
    
    // MARK: - 日志埋点
    private func logEvent(_ event: String, data: [String: Any]) {
        // TODO: 接入正式埋点系统
        print("[AuthEvent] \(event): \(data)")
    }
}
