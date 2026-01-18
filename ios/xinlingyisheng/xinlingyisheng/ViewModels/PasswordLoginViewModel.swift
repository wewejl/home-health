import Foundation
import SwiftUI
import Combine

// MARK: - 密码登录模式
enum PasswordLoginMode: String, CaseIterable {
    case login = "登录"
    case register = "注册"
    case resetPassword = "重置密码"
}

// MARK: - 密码登录UI状态
enum PasswordLoginUIState: Equatable {
    case idle
    case checkingPhone
    case sendingCode
    case codeSent
    case loggingIn
    case registering
    case resetting
    case success
    case error(String)
}

// MARK: - PasswordLoginViewModel
@MainActor
class PasswordLoginViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var phoneNumber: String = ""
    @Published var displayPhoneNumber: String = ""
    @Published var password: String = ""
    @Published var confirmPassword: String = ""
    @Published var verificationCode: String = ""
    @Published var isPasswordVisible: Bool = false
    @Published var isConfirmPasswordVisible: Bool = false
    @Published var isAgreed: Bool = false
    @Published var mode: PasswordLoginMode = .login
    @Published var uiState: PasswordLoginUIState = .idle
    @Published var countdown: Int = 0
    @Published var showError: Bool = false
    @Published var errorMessage: String = ""
    @Published var showCodeSentNotice: Bool = false
    
    // 手机号状态
    @Published var phoneExists: Bool = false
    @Published var phoneHasPassword: Bool = false
    @Published var phoneChecked: Bool = false
    
    // MARK: - Private Properties
    private var countdownTask: Task<Void, Never>?
    private var loginTask: Task<Void, Never>?
    private var checkPhoneTask: Task<Void, Never>?
    private let countdownDuration = 60
    
    // MARK: - Computed Properties
    var isPhoneValid: Bool {
        let phoneRegex = "^1[3-9]\\d{9}$"
        return phoneNumber.range(of: phoneRegex, options: .regularExpression) != nil
    }
    
    var isPasswordValid: Bool {
        password.count >= 6 && password.count <= 32 && !password.contains(" ")
    }
    
    var isConfirmPasswordValid: Bool {
        confirmPassword == password && !confirmPassword.isEmpty
    }
    
    var canSendCode: Bool {
        isPhoneValid && countdown == 0 && uiState != .sendingCode
    }
    
    var canLogin: Bool {
        isPhoneValid && isPasswordValid && isAgreed && uiState != .loggingIn
    }
    
    var canRegister: Bool {
        let basicValid = isPhoneValid && isPasswordValid && isConfirmPasswordValid && isAgreed && uiState != .registering
        // 如果验证码功能关闭，不要求验证码
        if !APIConfig.enableSMSVerification {
            return basicValid
        }
        return basicValid && verificationCode.count >= 4
    }
    
    var canResetPassword: Bool {
        let basicValid = isPhoneValid && isPasswordValid && isConfirmPasswordValid && uiState != .resetting
        // 如果验证码功能关闭，不要求验证码
        if !APIConfig.enableSMSVerification {
            return basicValid
        }
        return basicValid && verificationCode.count >= 4
    }
    
    var isLoading: Bool {
        switch uiState {
        case .checkingPhone, .sendingCode, .loggingIn, .registering, .resetting:
            return true
        default:
            return false
        }
    }
    
    var codeButtonText: String {
        if countdown > 0 {
            return "\(countdown)s"
        }
        return showCodeSentNotice ? "重新获取" : "获取验证码"
    }
    
    var maskedPhoneText: String {
        guard phoneNumber.count == 11 else { return "当前手机号" }
        let start = phoneNumber.prefix(3)
        let end = phoneNumber.suffix(4)
        return "\(start)****\(end)"
    }
    
    var passwordHint: String {
        if password.isEmpty { return "" }
        if password.count < 6 { return "密码至少6位" }
        if password.count > 32 { return "密码不能超过32位" }
        if password.contains(" ") { return "密码不能包含空格" }
        return ""
    }
    
    var confirmPasswordHint: String {
        if confirmPassword.isEmpty { return "" }
        if confirmPassword != password { return "两次密码不一致" }
        return ""
    }
    
    // MARK: - Public Methods
    
    /// 检查手机号状态
    func checkPhoneStatus() {
        guard isPhoneValid else { return }
        
        checkPhoneTask?.cancel()
        checkPhoneTask = Task {
            uiState = .checkingPhone
            
            do {
                let response = try await APIService.shared.checkPhone(phone: phoneNumber)
                
                guard !Task.isCancelled else { return }
                
                phoneExists = response.exists
                phoneHasPassword = response.has_password
                phoneChecked = true
                uiState = .idle
                
            } catch {
                guard !Task.isCancelled else { return }
                phoneChecked = false
                uiState = .idle
            }
        }
    }
    
    /// 发送验证码
    func sendVerificationCode() {
        guard isPhoneValid else {
            showErrorMessage("请输入正确的11位手机号")
            return
        }
        
        Task {
            uiState = .sendingCode
            
            do {
                try await APIService.shared.sendVerificationCode(phone: phoneNumber)
                
                uiState = .codeSent
                withAnimation(.easeInOut(duration: 0.3)) {
                    showCodeSentNotice = true
                }
                startCountdown()
                
            } catch let error as APIError {
                uiState = .error(error.errorDescription ?? "发送失败")
                showErrorMessage(error.errorDescription ?? "发送失败")
            } catch {
                uiState = .error(error.localizedDescription)
                showErrorMessage("网络错误：\(error.localizedDescription)")
            }
        }
    }
    
    /// 密码登录
    func loginWithPassword() {
        guard isPhoneValid else {
            showErrorMessage("请输入正确的11位手机号")
            return
        }
        
        guard isPasswordValid else {
            showErrorMessage("请输入正确的密码")
            return
        }
        
        guard isAgreed else {
            showErrorMessage("请先同意用户协议和隐私政策")
            return
        }
        
        loginTask?.cancel()
        loginTask = Task {
            uiState = .loggingIn
            
            do {
                let response = try await APIService.shared.loginWithPassword(
                    phone: phoneNumber,
                    password: password
                )
                
                guard !Task.isCancelled else { return }
                
                // 保存登录状态
                AuthManager.shared.login(
                    token: response.token,
                    refreshToken: response.refresh_token,
                    user: response.user,
                    isNewUser: response.is_new_user ?? false
                )
                
                uiState = .success
                
                // 发送登录成功通知
                NotificationCenter.default.post(name: .loginSucceeded, object: nil)
                
            } catch let error as APIError {
                guard !Task.isCancelled else { return }
                showErrorMessage(error.errorDescription ?? "登录失败")
                uiState = .idle
            } catch {
                guard !Task.isCancelled else { return }
                showErrorMessage("网络错误：\(error.localizedDescription)")
                uiState = .idle
            }
        }
    }
    
    /// 密码注册
    func registerWithPassword() {
        guard canRegister else {
            if !isPhoneValid {
                showErrorMessage("请输入正确的11位手机号")
            } else if !isPasswordValid {
                showErrorMessage(passwordHint.isEmpty ? "密码格式不正确" : passwordHint)
            } else if !isConfirmPasswordValid {
                showErrorMessage("两次密码不一致")
            } else if APIConfig.enableSMSVerification && verificationCode.count < 4 {
                showErrorMessage("请输入验证码")
            } else if !isAgreed {
                showErrorMessage("请先同意用户协议和隐私政策")
            }
            return
        }
        
        loginTask?.cancel()
        loginTask = Task {
            uiState = .registering
            
            do {
                let response = try await APIService.shared.registerWithPassword(
                    phone: phoneNumber,
                    code: verificationCode,
                    password: password
                )
                
                guard !Task.isCancelled else { return }
                
                // 保存登录状态
                AuthManager.shared.login(
                    token: response.token,
                    refreshToken: response.refresh_token,
                    user: response.user,
                    isNewUser: response.is_new_user ?? true
                )
                
                uiState = .success
                
                // 发送登录成功通知
                NotificationCenter.default.post(name: .loginSucceeded, object: nil)
                
            } catch let error as APIError {
                guard !Task.isCancelled else { return }
                if case .serverError(let msg) = error, msg.contains("验证码") {
                    showErrorMessage("验证码错误，请重新输入")
                    verificationCode = ""
                } else {
                    showErrorMessage(error.errorDescription ?? "注册失败")
                }
                uiState = .idle
            } catch {
                guard !Task.isCancelled else { return }
                showErrorMessage("网络错误：\(error.localizedDescription)")
                uiState = .idle
            }
        }
    }
    
    /// 重置密码
    func resetPassword() {
        guard canResetPassword else {
            if !isPhoneValid {
                showErrorMessage("请输入正确的11位手机号")
            } else if !isPasswordValid {
                showErrorMessage(passwordHint.isEmpty ? "密码格式不正确" : passwordHint)
            } else if !isConfirmPasswordValid {
                showErrorMessage("两次密码不一致")
            } else if APIConfig.enableSMSVerification && verificationCode.count < 4 {
                showErrorMessage("请输入验证码")
            }
            return
        }
        
        loginTask?.cancel()
        loginTask = Task {
            uiState = .resetting
            
            do {
                let response = try await APIService.shared.resetPassword(
                    phone: phoneNumber,
                    code: verificationCode,
                    newPassword: password
                )
                
                guard !Task.isCancelled else { return }
                
                // 重置成功后自动登录
                AuthManager.shared.login(
                    token: response.token,
                    refreshToken: response.refresh_token,
                    user: response.user,
                    isNewUser: false
                )
                
                uiState = .success
                
                // 发送登录成功通知
                NotificationCenter.default.post(name: .loginSucceeded, object: nil)
                
            } catch let error as APIError {
                guard !Task.isCancelled else { return }
                if case .serverError(let msg) = error, msg.contains("验证码") {
                    showErrorMessage("验证码错误，请重新输入")
                    verificationCode = ""
                } else {
                    showErrorMessage(error.errorDescription ?? "重置密码失败")
                }
                uiState = .idle
            } catch {
                guard !Task.isCancelled else { return }
                showErrorMessage("网络错误：\(error.localizedDescription)")
                uiState = .idle
            }
        }
    }
    
    /// 处理手机号输入
    func handlePhoneInput(_ input: String) {
        let digits = input.filter { $0.isNumber }
        let limitedDigits = String(digits.prefix(11))
        phoneNumber = limitedDigits
        displayPhoneNumber = formatPhoneNumber(limitedDigits)
        
        // 手机号变化时重置检查状态
        if limitedDigits.count < 11 {
            phoneChecked = false
            withAnimation(.easeInOut(duration: 0.2)) {
                showCodeSentNotice = false
            }
        } else if limitedDigits.count == 11 {
            checkPhoneStatus()
        }
    }
    
    /// 切换登录模式
    func switchMode(to newMode: PasswordLoginMode) {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
            mode = newMode
            // 清空密码相关字段
            password = ""
            confirmPassword = ""
            verificationCode = ""
            showCodeSentNotice = false
            uiState = .idle
        }
    }
    
    /// 切换协议同意状态
    func toggleAgreement() {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
            isAgreed.toggle()
        }
    }
    
    /// 重置状态
    func reset() {
        phoneNumber = ""
        displayPhoneNumber = ""
        password = ""
        confirmPassword = ""
        verificationCode = ""
        isPasswordVisible = false
        isConfirmPasswordVisible = false
        isAgreed = false
        mode = .login
        uiState = .idle
        countdown = 0
        showError = false
        showCodeSentNotice = false
        phoneChecked = false
        cancelAllTasks()
    }
    
    /// 清理资源
    func cleanup() {
        cancelAllTasks()
    }
    
    // MARK: - Private Methods
    
    private func formatPhoneNumber(_ digits: String) -> String {
        var result = ""
        for (index, char) in digits.enumerated() {
            if index == 3 || index == 7 {
                result += " "
            }
            result += String(char)
        }
        return result
    }
    
    private func startCountdown() {
        countdown = countdownDuration
        countdownTask?.cancel()
        
        countdownTask = Task {
            while countdown > 0 && !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 1_000_000_000)
                guard !Task.isCancelled else { return }
                countdown -= 1
            }
        }
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
        
        // 触发震动反馈
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.error)
    }
    
    private func cancelAllTasks() {
        countdownTask?.cancel()
        loginTask?.cancel()
        checkPhoneTask?.cancel()
        countdownTask = nil
        loginTask = nil
        checkPhoneTask = nil
    }
    
    deinit {
        countdownTask?.cancel()
        loginTask?.cancel()
        checkPhoneTask?.cancel()
    }
}
