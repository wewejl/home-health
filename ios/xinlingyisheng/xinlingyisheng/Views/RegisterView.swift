import SwiftUI

// MARK: - RegisterView
struct RegisterView: View {
    @StateObject private var viewModel = PasswordLoginViewModel()
    @FocusState private var focusedField: RegisterField?
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    
    var onSuccess: (() -> Void)?
    
    enum RegisterField: Hashable {
        case phone, code, password, confirmPassword
    }
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                let horizontalPadding = AdaptiveSpacing.card
                
                ZStack {
                    RegisterBackgroundView()
                    
                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 0) {
                            Spacer()
                                .frame(height: ScaleFactor.padding(20))
                            
                            RegisterHeaderView()
                                .padding(.bottom, ScaleFactor.spacing(18))
                            
                            RegisterFormCard(
                                viewModel: viewModel,
                                focusedField: $focusedField,
                                openURL: openURL
                            )
                            .padding(.horizontal, horizontalPadding)
                            
                            Spacer()
                                .frame(height: max(geometry.safeAreaInsets.bottom + 24, 40))
                        }
                        .frame(minHeight: geometry.size.height - 60)
                    }
                    .scrollDismissesKeyboardCompat()
                    
                    if viewModel.isLoading {
                        RegisterLoadingOverlay()
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
            viewModel.mode = .register
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

// MARK: - 注册背景
struct RegisterBackgroundView: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color.dynamicColor(
                        light: PremiumColorTheme.backgroundLight,
                        dark: PremiumColorTheme.backgroundDark
                    ),
                    Color.dynamicColor(
                        light: Color(red: 0.95, green: 0.97, blue: 1.0),
                        dark: Color(red: 0.06, green: 0.09, blue: 0.16)
                    )
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            
            GeometryReader { geo in
                let size = min(geo.size.width, geo.size.height) * 0.5
                
                Circle()
                    .fill(PremiumColorTheme.current.backgroundGlowColor.opacity(0.5))
                    .frame(width: size, height: size)
                    .blur(radius: 60)
                    .offset(x: geo.size.width * 0.4, y: -geo.size.height * 0.1)
            }
        }
    }
}

// MARK: - 注册头部
struct RegisterHeaderView: View {
    @State private var showContent = false
    
    private var titleSize: CGFloat { AdaptiveFont.largeTitle }
    private var subtitleSize: CGFloat { AdaptiveFont.subheadline }
    
    var body: some View {
        VStack(spacing: AdaptiveSpacing.item) {
            Image(systemName: "person.badge.plus")
                .font(.system(size: ScaleFactor.size(60), weight: .light))
                .foregroundColor(PremiumColorTheme.primaryColor)
            
            Text("创建账号")
                .font(.system(size: titleSize, weight: .bold, design: .default))
                .foregroundColor(PremiumColorTheme.textPrimary)
            
            Text("注册后可使用密码快捷登录")
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

// MARK: - 注册表单卡片
struct RegisterFormCard: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    var focusedField: FocusState<RegisterView.RegisterField?>.Binding
    let openURL: OpenURLAction
    
    @State private var showContent = false
    
    private var cardPadding: CGFloat { ScaleFactor.padding(20) }
    private var itemSpacing: CGFloat { ScaleFactor.spacing(18) }
    
    var body: some View {
        GlassmorphicCard {
            VStack(spacing: itemSpacing) {
                // 手机号输入
                RegisterPhoneSection(viewModel: viewModel, focusedField: focusedField)
                
                // 验证码功能开启时才显示
                if APIConfig.enableSMSVerification {
                    // 验证码已发送提示
                    if viewModel.showCodeSentNotice {
                        CodeSentNotice(phoneText: viewModel.maskedPhoneText)
                    }
                    
                    // 验证码输入
                    RegisterCodeSection(viewModel: viewModel, focusedField: focusedField)
                }
                
                // 密码输入
                PasswordInputField(
                    title: "设置密码",
                    placeholder: "请输入6-32位密码",
                    text: $viewModel.password,
                    isSecure: !viewModel.isPasswordVisible,
                    toggleVisibility: { viewModel.isPasswordVisible.toggle() },
                    hint: viewModel.passwordHint
                )
                
                // 确认密码
                PasswordInputField(
                    title: "确认密码",
                    placeholder: "请再次输入密码",
                    text: $viewModel.confirmPassword,
                    isSecure: !viewModel.isConfirmPasswordVisible,
                    toggleVisibility: { viewModel.isConfirmPasswordVisible.toggle() },
                    hint: viewModel.confirmPasswordHint
                )
                
                // 协议同意
                AgreementSection(
                    isAgreed: viewModel.isAgreed,
                    onToggle: viewModel.toggleAgreement,
                    openURL: openURL
                )
                
                // 注册按钮
                PrimaryButton(title: "注册", action: viewModel.registerWithPassword)
                    .padding(.top, ScaleFactor.padding(8))
                    .disabled(!viewModel.canRegister)
                    .opacity(viewModel.canRegister ? 1.0 : 0.6)
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

// MARK: - 注册手机号输入
struct RegisterPhoneSection: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    var focusedField: FocusState<RegisterView.RegisterField?>.Binding
    
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

// MARK: - 注册验证码输入
struct RegisterCodeSection: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    var focusedField: FocusState<RegisterView.RegisterField?>.Binding
    
    var body: some View {
        VStack(alignment: .leading, spacing: AdaptiveSpacing.item) {
            HStack {
                Text("验证码")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(PremiumColorTheme.textSecondary)
                Spacer()
                RegisterSendCodeButton(viewModel: viewModel)
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
                    activeBorder: PremiumColorTheme.primaryColor,
                    filledBorder: PremiumColorTheme.primaryColor.opacity(0.55),
                    successBorder: PremiumColorTheme.successColor,
                    textColor: PremiumColorTheme.textPrimary
                )
            )
            .focused(focusedField, equals: .code)
        }
    }
}

// MARK: - 注册发送验证码按钮
struct RegisterSendCodeButton: View {
    @ObservedObject var viewModel: PasswordLoginViewModel
    
    private var isDisabled: Bool { !viewModel.canSendCode }
    private var buttonColor: Color {
        isDisabled ? PremiumColorTheme.textTertiary : PremiumColorTheme.primaryColor
    }
    private var backgroundColor: Color {
        isDisabled ? PremiumColorTheme.textTertiary.opacity(0.1) : PremiumColorTheme.primaryColor.opacity(0.18)
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

// MARK: - 注册加载遮罩
struct RegisterLoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()
            
            VStack(spacing: ScaleFactor.spacing(16)) {
                ProgressView()
                    .scaleEffect(1.5)
                    .tint(.white)
                Text("注册中...")
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
    RegisterView()
}
