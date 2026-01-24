import Foundation
import SwiftUI
import Combine

// MARK: - 登录状态枚举
enum LoginStep {
    case phoneInput
    case codeInput
}

enum LoginUIState: Equatable {
    case idle
    case sendingCode
    case codeSent
    case loggingIn
    case success
    case error(LoginErrorState)
}

enum LoginErrorState: Equatable {
    case phoneInvalid
    case codeEmpty
    case codeInvalid
    case agreementRequired
    case server(String)
    case network(String)
    
    var message: String {
        switch self {
        case .phoneInvalid:
            return "请输入正确的11位手机号"
        case .codeEmpty:
            return "请输入验证码"
        case .codeInvalid:
            return "验证码错误，请重新输入"
        case .agreementRequired:
            return "请先同意用户协议和隐私政策"
        case .server(let msg):
            return msg
        case .network(let msg):
            return "网络错误：\(msg)"
        }
    }
}

// MARK: - LoginViewModel
@MainActor
class LoginViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var phoneNumber: String = ""
    @Published var displayPhoneNumber: String = ""
    @Published var verificationCode: String = ""
    @Published var isAgreed: Bool = false
    @Published var step: LoginStep = .phoneInput
    @Published var uiState: LoginUIState = .idle
    @Published var countdown: Int = 0
    @Published var showError: Bool = false
    @Published var errorMessage: String = ""
    @Published var showCodeSentNotice: Bool = false
    
    // MARK: - Private Properties
    private var countdownTask: Task<Void, Never>?
    private var sendCodeTask: Task<Void, Never>?
    private var loginTask: Task<Void, Never>?
    private let countdownDuration = 60
    
    // MARK: - Computed Properties
    var isPhoneValid: Bool {
        let phoneRegex = "^1[3-9]\\d{9}$"
        return phoneNumber.range(of: phoneRegex, options: .regularExpression) != nil
    }
    
    var canSendCode: Bool {
        isPhoneValid && countdown == 0 && uiState != .sendingCode
    }
    
    var canLogin: Bool {
        isPhoneValid && verificationCode.count >= 4 && isAgreed && uiState != .loggingIn
    }
    
    var isLoading: Bool {
        uiState == .sendingCode || uiState == .loggingIn
    }
    
    var codeButtonText: String {
        if countdown > 0 {
            return "\(countdown)s"
        }
        return uiState == .codeSent || showCodeSentNotice ? "重新获取" : "获取验证码"
    }
    
    var maskedPhoneText: String {
        guard phoneNumber.count == 11 else { return "当前手机号" }
        let start = phoneNumber.prefix(3)
        let end = phoneNumber.suffix(4)
        return "\(start)****\(end)"
    }
    
    // MARK: - Public Methods
    
    /// 发送验证码
    func sendVerificationCode() {
        guard isPhoneValid else {
            showErrorMessage(.phoneInvalid)
            return
        }

        // 防止重复发送：如果正在发送或已发送且倒计时未结束，直接返回
        if uiState == .sendingCode || countdown > 0 {
            return
        }

        // 取消之前的任务
        sendCodeTask?.cancel()

        sendCodeTask = Task {
            uiState = .sendingCode

            do {
                // 调用 API 发送验证码
                try await APIService.shared.sendVerificationCode(phone: phoneNumber)

                guard !Task.isCancelled else { return }

                uiState = .codeSent
                withAnimation(.easeInOut(duration: 0.3)) {
                    showCodeSentNotice = true
                }
                startCountdown()

                // 自动切换到验证码输入步骤
                if step == .phoneInput {
                    withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                        step = .codeInput
                    }
                }

            } catch let error as APIError {
                guard !Task.isCancelled else { return }
                uiState = .error(.server(error.errorDescription ?? "发送失败"))
                showErrorMessage(.server(error.errorDescription ?? "发送失败"))
            } catch {
                guard !Task.isCancelled else { return }
                // 恢复到空闲状态
                uiState = .idle
                showErrorMessage(.network(error.localizedDescription))
            }
        }
    }
    
    /// 登录
    func login() {
        // 验证
        guard isPhoneValid else {
            showErrorMessage(.phoneInvalid)
            return
        }
        
        guard !verificationCode.isEmpty else {
            showErrorMessage(.codeEmpty)
            return
        }
        
        guard isAgreed else {
            showErrorMessage(.agreementRequired)
            return
        }
        
        // 取消之前的任务
        loginTask?.cancel()
        
        loginTask = Task {
            uiState = .loggingIn
            
            do {
                let response = try await APIService.shared.login(phone: phoneNumber, code: verificationCode)
                
                guard !Task.isCancelled else { return }
                
                // 保存登录状态
                AuthManager.shared.login(
                    token: response.token,
                    refreshToken: response.refresh_token,
                    user: response.user,
                    isNewUser: response.is_new_user ?? false
                )
                
                uiState = .success
                
                // 日志埋点
                logAuthEvent(response.is_new_user == true ? "register_success" : "login_success")
                
                // 发送登录成功通知
                NotificationCenter.default.post(name: .loginSucceeded, object: nil)
                
            } catch let error as APIError {
                guard !Task.isCancelled else { return }
                
                if case .serverError(let msg) = error {
                    if msg.contains("验证码") {
                        showErrorMessage(.codeInvalid)
                        verificationCode = ""
                    } else {
                        showErrorMessage(.server(msg))
                    }
                } else {
                    showErrorMessage(.server(error.errorDescription ?? "登录失败"))
                }
                uiState = .idle
                
            } catch {
                guard !Task.isCancelled else { return }
                showErrorMessage(.network(error.localizedDescription))
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
        
        // 手机号变化时重置验证码发送状态
        if limitedDigits.count < 11 {
            withAnimation(.easeInOut(duration: 0.2)) {
                showCodeSentNotice = false
            }
        }
    }
    
    /// 手机号输入完成
    func onPhoneComplete() {
        if isPhoneValid && countdown == 0 && uiState != .sendingCode {
            sendVerificationCode()
        }
    }
    
    /// 验证码输入完成
    func onCodeComplete() {
        if canLogin {
            login()
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
        verificationCode = ""
        isAgreed = false
        step = .phoneInput
        uiState = .idle
        countdown = 0
        showError = false
        showCodeSentNotice = false
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
    
    private func showErrorMessage(_ error: LoginErrorState) {
        errorMessage = error.message
        showError = true
        
        // 触发震动反馈
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.error)
    }
    
    private func cancelAllTasks() {
        countdownTask?.cancel()
        sendCodeTask?.cancel()
        loginTask?.cancel()
        countdownTask = nil
        sendCodeTask = nil
        loginTask = nil
    }
    
    private func logAuthEvent(_ event: String, extra: [String: Any] = [:]) {
        // TODO: 接入正式埋点系统
        var data: [String: Any] = ["event": event, "phone_suffix": String(phoneNumber.suffix(4))]
        data.merge(extra) { _, new in new }
        print("[LoginEvent] \(data)")
    }
    
    deinit {
        countdownTask?.cancel()
        sendCodeTask?.cancel()
        loginTask?.cancel()
    }
}

// MARK: - Notification Names
extension Notification.Name {
    static let loginSucceeded = Notification.Name("LoginSucceeded")
}
