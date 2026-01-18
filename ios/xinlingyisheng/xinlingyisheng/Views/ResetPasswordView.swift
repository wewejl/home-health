import SwiftUI

// MARK: - ResetPasswordView
struct ResetPasswordView: View {
    @StateObject private var viewModel = PasswordLoginViewModel()
    @FocusState private var focusedField: ResetField?
    @Environment(\.dismiss) private var dismiss
    
    var onSuccess: (() -> Void)?
    
    enum ResetField: Hashable {
        case phone, code, password, confirmPassword
    }
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                let horizontalPadding = AdaptiveSpacing.card
                
                ZStack {
                    ResetPasswordBackgroundView()
                    
                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 0) {
                            Spacer()
                                .frame(height: ScaleFactor.padding(20))
                            
                            ResetPasswordHeaderView()
                                .padding(.bottom, AdaptiveSpacing.section)
                            
                            ResetPasswordFormCard(
                                viewModel: viewModel,
                                focusedField: $focusedField
                            )
                            .padding(.horizontal, horizontalPadding)
                            
                            Spacer()
                                .frame(height: max(geometry.safeAreaInsets.bottom + 24, 40))
                        }
                        .frame(minHeight: geometry.size.height - 60)
                    }
                    .scrollDismissesKeyboardCompat()
                    
                    if viewModel.isLoading {
                        ResetPasswordLoadingOverlay()
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                            .foregroundColor(PremiumColorTheme.textPrimary)
                    }
                }
            }
        }
        .onAppear {
            viewModel.mode = .resetPassword
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                focusedField = .phone
            }
        }
        .onDisappear {
            viewModel.cleanup()
        }
        .onChangeCompat(of: viewModel.uiState) { newState in
            if newState == .success {
                onSuccess?()
            }
        }
        .alert("提示", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage)
        }
    }
}

// MARK: - 重置密码背景
struct ResetPasswordBackgroundView: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color.dynamicColor(
                        light: PremiumColorTheme.backgroundLight,
                        dark: PremiumColorTheme.backgroundDark
                    ),
                    Color.dynamicColor(
                        light: Color(red: 1.0, green: 0.97, blue: 0.95),
                        dark: Color(red: 0.08, green: 0.06, blue: 0.12)
                    )
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            
            GeometryReader { geo in
                let size = min(geo.size.width, geo.size.height) * 0.5
                
                Circle()
                    .fill(PremiumColorTheme.accentColor.opacity(0.15))
                    .frame(width: size, height: size)
                    .blur(radius: 60)
                    .offset(x: -geo.size.width * 0.2, y: geo.size.height * 0.2)
            }
        }
    }
}

// MARK: - 重置密码头部
struct ResetPasswordHeaderView: View {
    @State private var showContent = false
    
    private var titleSize: CGFloat { AdaptiveFont.largeTitle }
    private var subtitleSize: CGFloat { AdaptiveFont.subheadline }
    
    var body: some View {
        VStack(spacing: AdaptiveSpacing.item) {
            Image(systemName: "key.fill")
                .font(.system(size: ScaleFactor.size(60), weight: .light))
                .foregroundColor(PremiumColorTheme.accentColor)
            
            Text("重置密码")
                .font(.system(size: titleSize, weight: .bold, design: .default))
                .foregroundColor(PremiumColorTheme.textPrimary)
            
            Text(APIConfig.enableSMSVerification ? "通过验证码验证身份后设置新密码" : "为您的账号设置新密码")
                .font(.system(size: subtitleSize, weight: .regular, design: .rounded))
                .foregroundColor(PremiumColorTheme.textSecondary)
                .multilineTextAlignment(.center)
        }
        .opacity(showContent ? 1 : 0)
        .offset(y: showContent ? 0 : -15)
        .onAppear {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.8).delay(0.1)) {
                showContent = true
            }
        }
    }
}

// MARK: - 重置密码表单卡片
struct ResetPasswordFormCard: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    var focusedField: FocusState<ResetPasswordView.ResetField?>.Binding
    
    @State private var showContent = false
    
    private var cardPadding: CGFloat { ScaleFactor.padding(20) }
    private var itemSpacing: CGFloat { ScaleFactor.spacing(18) }
    
    var body: some View {
        GlassmorphicCard {
            VStack(spacing: itemSpacing) {
                // 手机号输入
                ResetPhoneSection(viewModel: viewModel, focusedField: focusedField)
                
                // 验证码功能开启时才显示
                if APIConfig.enableSMSVerification {
                    // 验证码已发送提示
                    if viewModel.showCodeSentNotice {
                        CodeSentNotice(phoneText: viewModel.maskedPhoneText)
                    }
                    
                    // 验证码输入
                    ResetCodeSection(viewModel: viewModel, focusedField: focusedField)
                }
                
                // 新密码输入
                PasswordInputField(
                    title: "新密码",
                    placeholder: "请输入6-32位新密码",
                    text: $viewModel.password,
                    isSecure: !viewModel.isPasswordVisible,
                    toggleVisibility: { viewModel.isPasswordVisible.toggle() },
                    hint: viewModel.passwordHint
                )
                
                // 确认新密码
                PasswordInputField(
                    title: "确认新密码",
                    placeholder: "请再次输入新密码",
                    text: $viewModel.confirmPassword,
                    isSecure: !viewModel.isConfirmPasswordVisible,
                    toggleVisibility: { viewModel.isConfirmPasswordVisible.toggle() },
                    hint: viewModel.confirmPasswordHint
                )
                
                // 重置按钮
                PrimaryButton(title: "重置密码", action: viewModel.resetPassword)
                    .padding(.top, ScaleFactor.padding(8))
                    .disabled(!viewModel.canResetPassword)
                    .opacity(viewModel.canResetPassword ? 1.0 : 0.6)
            }
            .padding(.horizontal, cardPadding)
            .padding(.vertical, cardPadding)
        }
        .opacity(showContent ? 1 : 0)
        .offset(y: showContent ? 0 : 12)
        .onAppear {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.8).delay(0.2)) {
                showContent = true
            }
        }
    }
}

// MARK: - 重置密码手机号输入
struct ResetPhoneSection: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    var focusedField: FocusState<ResetPasswordView.ResetField?>.Binding
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
            Text("手机号")
                .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                .foregroundColor(PremiumColorTheme.textSecondary)
            
            PhoneNumberTextField(
                phoneNumber: $viewModel.phoneNumber,
                displayNumber: $viewModel.displayPhoneNumber,
                isFocused: focusedField.wrappedValue == .phone,
                onComplete: {
                    focusedField.wrappedValue = .code
                    if viewModel.canSendCode {
                        viewModel.sendVerificationCode()
                    }
                }
            )
            .focused(focusedField, equals: .phone)
            .onChangeCompat(of: viewModel.displayPhoneNumber) { newValue in
                viewModel.handlePhoneInput(newValue)
            }
        }
    }
}

// MARK: - 重置密码验证码输入
struct ResetCodeSection: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    var focusedField: FocusState<ResetPasswordView.ResetField?>.Binding
    
    var body: some View {
        VStack(alignment: .leading, spacing: AdaptiveSpacing.item) {
            HStack {
                Text("验证码")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(PremiumColorTheme.textSecondary)
                Spacer()
                ResetSendCodeButton(viewModel: viewModel)
            }
            
            VerificationCodeInput(
                code: $viewModel.verificationCode,
                codeLength: 6,
                onComplete: { _ in
                    focusedField.wrappedValue = .password
                },
                style: VerificationCodeStyle(
                    baseFill: Color.dynamicColor(
                        light: Color.white.opacity(0.65),
                        dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.85)
                    ),
                    emptyBorder: Color.white.opacity(0.25),
                    activeBorder: PremiumColorTheme.accentColor,
                    filledBorder: PremiumColorTheme.accentColor.opacity(0.55),
                    successBorder: PremiumColorTheme.successColor,
                    textColor: PremiumColorTheme.textPrimary
                )
            )
            .focused(focusedField, equals: .code)
        }
    }
}

// MARK: - 重置密码发送验证码按钮
struct ResetSendCodeButton: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    
    private var isDisabled: Bool { !viewModel.canSendCode }
    private var buttonColor: Color {
        isDisabled ? PremiumColorTheme.textTertiary : PremiumColorTheme.accentColor
    }
    private var backgroundColor: Color {
        isDisabled ? PremiumColorTheme.textTertiary.opacity(0.1) : PremiumColorTheme.accentColor.opacity(0.18)
    }
    
    var body: some View {
        Button(action: viewModel.sendVerificationCode) {
            HStack(spacing: 6) {
                if viewModel.uiState == .sendingCode {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: buttonColor))
                        .scaleEffect(0.8)
                        .frame(width: 16, height: 16)
                } else if viewModel.countdown > 0 {
                    ZStack {
                        Circle()
                            .stroke(buttonColor.opacity(0.3), lineWidth: 2)
                            .frame(width: ScaleFactor.size(16), height: ScaleFactor.size(16))
                        Circle()
                            .trim(from: 0, to: CGFloat(viewModel.countdown) / 60.0)
                            .stroke(buttonColor, lineWidth: 2)
                            .frame(width: ScaleFactor.size(16), height: ScaleFactor.size(16))
                            .rotationEffect(.degrees(-90))
                    }
                }
                Text(viewModel.codeButtonText)
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium, design: .rounded))
                    .foregroundColor(buttonColor)
            }
            .padding(.horizontal, ScaleFactor.padding(12))
            .padding(.vertical, ScaleFactor.padding(8))
            .background(
                RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                    .fill(backgroundColor)
            )
        }
        .disabled(isDisabled)
        .animation(.easeInOut(duration: 0.2), value: isDisabled)
    }
}

// MARK: - 重置密码加载遮罩
struct ResetPasswordLoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()
            
            VStack(spacing: ScaleFactor.spacing(16)) {
                ProgressView()
                    .scaleEffect(1.5)
                    .tint(.white)
                Text("重置中...")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(.white)
            }
            .padding(ScaleFactor.padding(32))
            .background(
                RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous)
                    .fill(Color.black.opacity(0.6))
            )
        }
        .transition(.opacity)
    }
}

#Preview {
    ResetPasswordView()
}
