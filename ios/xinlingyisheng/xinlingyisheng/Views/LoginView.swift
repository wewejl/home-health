import SwiftUI

// MARK: - LoginView
struct LoginView: View {
    @StateObject private var viewModel = LoginViewModel()
    @FocusState private var focusedField: LoginField?
    @Environment(\.openURL) private var openURL

    var onLoginSuccess: (() -> Void)?

    var body: some View {
        GeometryReader { geometry in
            let safeWidth = max(geometry.size.width, 1)
            let horizontalPadding = AdaptiveSpacing.card

            ZStack {
                LoginBackgroundView()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 0) {
                        Spacer()
                            .frame(height: adaptiveTopSpacing(safeTop: geometry.safeAreaInsets.top))

                        LoginHeaderView()
                            .padding(.bottom, AdaptiveSpacing.section)

                        LoginFormCard(
                            viewModel: viewModel,
                            focusedField: $focusedField,
                            openURL: openURL,
                            availableWidth: safeWidth - horizontalPadding * 2
                        )
                        .padding(.horizontal, horizontalPadding)

                        Spacer()
                            .frame(height: adaptiveBottomSpacing(safeBottom: geometry.safeAreaInsets.bottom))
                    }
                    .frame(minHeight: geometry.size.height)
                }
                .scrollDismissesKeyboardCompat()

                if viewModel.isLoading {
                    LoadingOverlay()
                }
            }
            .ignoresSafeArea(.container, edges: .all)
        }
        .onAppear {
            DeviceInfoLogger.log(context: "LoginView")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                focusedField = .phone
            }
        }
        .onDisappear {
            viewModel.cleanup()
        }
        .onChangeCompat(of: viewModel.uiState) { newState in
            if newState == .success {
                onLoginSuccess?()
            }
        }
        .alert("提示", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage)
        }
    }

    // MARK: - 自适应间距辅助函数
    private func adaptiveTopSpacing(safeTop: CGFloat) -> CGFloat {
        return max(safeTop + ScaleFactor.padding(20), ScaleFactor.size(44))
    }

    private func adaptiveBottomSpacing(safeBottom: CGFloat) -> CGFloat {
        return max(safeBottom + ScaleFactor.padding(24), ScaleFactor.size(40))
    }
}

// MARK: - 背景视图
struct LoginBackgroundView: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color.dynamicColor(
                        light: PremiumColorTheme.backgroundLight,
                        dark: PremiumColorTheme.backgroundDark
                    ),
                    Color.dynamicColor(
                        light: Color(red: 0.92, green: 0.95, blue: 0.98),
                        dark: Color(red: 0.05, green: 0.08, blue: 0.15)
                    )
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            GeometryReader { geo in
                let size = min(geo.size.width, geo.size.height) * 0.6

                Circle()
                    .fill(PremiumColorTheme.current.backgroundGlowColor)
                    .frame(width: size, height: size)
                    .blur(radius: 80)
                    .offset(x: -geo.size.width * 0.2, y: -geo.size.height * 0.15)

                Circle()
                    .fill(PremiumColorTheme.current.secondaryGlowColor)
                    .frame(width: size * 1.2, height: size * 1.2)
                    .blur(radius: 90)
                    .offset(x: geo.size.width * 0.3, y: geo.size.height * 0.4)
            }
        }
    }
}

// MARK: - 头部视图
struct LoginHeaderView: View {
    @State private var showContent = false

    private var logoSize: CGFloat { ScaleFactor.size(90) }
    private var titleSize: CGFloat { AdaptiveFont.largeTitle }
    private var subtitleSize: CGFloat { AdaptiveFont.subheadline }

    var body: some View {
        VStack(spacing: AdaptiveSpacing.item + 4) {
            LogoView(style: .aiVine, size: logoSize)

            Text("鑫琳医生")
                .font(.system(size: titleSize, weight: .bold, design: .default))
                .foregroundColor(PremiumColorTheme.textPrimary)

            Text("智能诊疗助手，随时获取专业建议")
                .font(.system(size: subtitleSize, weight: .regular, design: .rounded))
                .foregroundColor(PremiumColorTheme.textSecondary)
                .multilineTextAlignment(.center)
        }
        .opacity(showContent ? 1 : 0)
        .offset(y: showContent ? 0 : -20)
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.8).delay(0.1)) {
                showContent = true
            }
        }
    }
}

// MARK: - 登录表单卡片
struct LoginFormCard: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding
    let openURL: OpenURLAction
    let availableWidth: CGFloat

    @State private var showContent = false

    private var cardPadding: CGFloat { ScaleFactor.padding(20) }
    private var itemSpacing: CGFloat { ScaleFactor.spacing(18) }
    private var titleSize: CGFloat { AdaptiveFont.title2 }

    var body: some View {
        GlassmorphicCard {
            VStack(spacing: itemSpacing) {
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                    Text("手机号登录")
                        .font(.system(size: titleSize, weight: .bold, design: .default))
                        .foregroundColor(PremiumColorTheme.textPrimary)

                    Text("未注册的手机号将自动创建账号")
                        .font(.system(size: AdaptiveFont.footnote, weight: .regular, design: .rounded))
                        .foregroundColor(PremiumColorTheme.textSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, ScaleFactor.padding(4))

                PhoneInputSection(viewModel: viewModel, focusedField: focusedField)

                if viewModel.showCodeSentNotice {
                    CodeSentNotice(phoneText: viewModel.maskedPhoneText)
                }

                CodeInputSection(
                    viewModel: viewModel,
                    focusedField: focusedField,
                    availableWidth: availableWidth - cardPadding * 2
                )

                AgreementSection(
                    isAgreed: viewModel.isAgreed,
                    onToggle: viewModel.toggleAgreement,
                    openURL: openURL
                )

                PrimaryButton(title: "登录 / 注册", action: viewModel.login)
                    .padding(.top, ScaleFactor.padding(8))
                    .disabled(!viewModel.canLogin && !viewModel.isLoading)
                    .opacity(viewModel.canLogin || viewModel.isLoading ? 1.0 : 0.6)
            }
            .padding(.horizontal, cardPadding)
            .padding(.vertical, cardPadding)
        }
        .opacity(showContent ? 1 : 0)
        .offset(y: showContent ? 0 : ScaleFactor.size(16))
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.8).delay(0.2)) {
                showContent = true
            }
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                if focusedField.wrappedValue == .phone {
                    Button("下一步") { focusedField.wrappedValue = .code }
                        .font(.system(size: AdaptiveFont.body, weight: .medium))
                        .foregroundColor(PremiumColorTheme.primaryColor)
                } else if focusedField.wrappedValue == .code {
                    Button("完成") { focusedField.wrappedValue = nil }
                        .font(.system(size: AdaptiveFont.body, weight: .medium))
                        .foregroundColor(PremiumColorTheme.primaryColor)
                }
            }
        }
    }
}

// MARK: - 手机号输入区域
struct PhoneInputSection: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding

    var body: some View {
        PhoneNumberTextField(
            phoneNumber: $viewModel.phoneNumber,
            displayNumber: $viewModel.displayPhoneNumber,
            isFocused: focusedField.wrappedValue == .phone,
            onComplete: {
                focusedField.wrappedValue = .code
                viewModel.onPhoneComplete()
            }
        )
        .onChangeCompat(of: viewModel.displayPhoneNumber) { newValue in
            viewModel.handlePhoneInput(newValue)
        }
    }
}

// MARK: - 验证码已发送提示
struct CodeSentNotice: View {
    let phoneText: String

    var body: some View {
        HStack(spacing: ScaleFactor.spacing(6)) {
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(PremiumColorTheme.primaryColor)
                .font(.system(size: AdaptiveFont.subheadline))
            Text("验证码已发送至 \(phoneText)")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(PremiumColorTheme.textSecondary)
            Spacer()
        }
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}

// MARK: - 验证码输入区域
struct CodeInputSection: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding
    let availableWidth: CGFloat

    var body: some View {
        VStack(alignment: .leading, spacing: AdaptiveSpacing.item) {
            HStack {
                Text("验证码")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(PremiumColorTheme.textSecondary)
                Spacer()
                SendCodeButton(viewModel: viewModel)
            }

            VerificationCodeInput(
                code: $viewModel.verificationCode,
                codeLength: 6,
                onComplete: { _ in
                    focusedField.wrappedValue = nil
                    viewModel.onCodeComplete()
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
                ),
                isExternallyFocused: focusedField.wrappedValue == .code
            )
            .frame(maxWidth: .infinity)
        }
    }
}

// MARK: - 发送验证码按钮
struct SendCodeButton: View {
    @ObservedObject var viewModel: LoginViewModel

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

// MARK: - 协议同意区域
struct AgreementSection: View {
    let isAgreed: Bool
    let onToggle: () -> Void
    let openURL: OpenURLAction

    var body: some View {
        Button(action: onToggle) {
            HStack(alignment: .center, spacing: ScaleFactor.spacing(10)) {
                Image(systemName: isAgreed ? "checkmark.square.fill" : "square")
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(isAgreed ? PremiumColorTheme.primaryColor : PremiumColorTheme.textSecondary)

                VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                    Text("同意并遵守以下条款")
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(PremiumColorTheme.textSecondary)
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        AgreementLink(title: "《用户协议》", type: .terms, openURL: openURL)
                        AgreementLink(title: "《隐私政策》", type: .privacy, openURL: openURL)
                    }
                }
                .font(.system(size: AdaptiveFont.footnote, weight: .regular, design: .rounded))
                Spacer()
            }
        }
        .buttonStyle(.plain)
        .padding(.top, AdaptiveSpacing.item)
        .contentShape(Rectangle())
    }
}

// MARK: - 协议链接
struct AgreementLink: View {
    let title: String
    let type: AgreementLinkType
    let openURL: OpenURLAction

    var body: some View {
        Button(action: { if let url = type.url { openURL(url) } }) {
            Text(title)
                .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                .foregroundColor(PremiumColorTheme.secondaryColor)
                .underline()
        }
        .buttonStyle(.plain)
    }
}

enum AgreementLinkType {
    case terms, privacy
    var url: URL? {
        switch self {
        case .terms: return URL(string: AppURLConstants.termsOfServiceURL)
        case .privacy: return URL(string: AppURLConstants.privacyPolicyURL)
        }
    }
}

// MARK: - App URL Constants
enum AppURLConstants {
    // TODO: 替换为正式的协议链接
    static let termsOfServiceURL = "https://xinlinyisheng.com/terms"
    static let privacyPolicyURL = "https://xinlinyisheng.com/privacy"
    static let helpCenterURL = "https://xinlingyisheng.com/help"
    static let feedbackURL = "https://xinlinyisheng.com/feedback"
}

// MARK: - 加载遮罩
struct LoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: ScaleFactor.spacing(16)) {
                ProgressView()
                    .scaleEffect(1.5)
                    .tint(.white)
                Text("登录中...")
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
    LoginView()
}
