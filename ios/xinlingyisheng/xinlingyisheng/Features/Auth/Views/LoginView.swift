import SwiftUI

// MARK: - 登录方式枚举
enum LoginMethod: String, CaseIterable {
    case oneClick = "oneClick"
    case verification = "verification"

    var displayName: String {
        switch self {
        case .oneClick: return "一键登录"
        case .verification: return "验证码登录"
        }
    }

    var icon: String {
        switch self {
        case .oneClick: return "antenna.radiowaves.left.and.right"
        case .verification: return "message.fill"
        }
    }
}

// MARK: - 登录页面（全新高级设计）

struct LoginView: View {
    @StateObject private var viewModel = LoginViewModel()
    @FocusState private var focusedField: LoginField?
    @Environment(\.openURL) private var openURL
    @State private var selectedLoginMethod: LoginMethod = .oneClick

    var onLoginSuccess: (() -> Void)?

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)
            let safeTop = geometry.safeAreaInsets.top

            ZStack {
                // 背景层 - 全屏沉浸式
                PremiumLoginBackground()
                    .ignoresSafeArea()

                // 内容层
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 0) {
                        // 顶部品牌区域 - 占据视觉重心
                        PremiumBrandSection(safeTop: safeTop, layout: layout)
                            .padding(.bottom, ScaleFactor.spacing(32))

                        // 登录表单区域
                        PremiumLoginForm(
                            viewModel: viewModel,
                            focusedField: $focusedField,
                            layout: layout,
                            selectedLoginMethod: $selectedLoginMethod
                        )
                        .padding(.horizontal, layout.horizontalPadding + 4)

                        // 底部间距
                        Spacer(minLength: ScaleFactor.spacing(80))
                    }
                    .frame(maxWidth: .infinity)
                }
                .scrollDismissesKeyboard(.interactively)

                // 加载遮罩
                if viewModel.isLoading {
                    PremiumLoadingOverlay()
                        .transition(.opacity.combined(with: .scale(scale: 0.95)))
                }
            }
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    if focusedField == .phone {
                        Button("下一步") {
                            focusedField = .code
                        }
                        .font(.system(size: UnifiedFont.body, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                    } else if focusedField == .code {
                        Button("完成") {
                            focusedField = nil
                        }
                        .font(.system(size: UnifiedFont.body, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                    }
                }
            }
            .onAppear {
                DeviceInfoLogger.log(context: "LoginView")
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
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
    }
}

// MARK: - 高级背景

struct PremiumLoginBackground: View {
    @State private var phase: CGFloat = 0

    var body: some View {
        ZStack {
            // 主背景 - 暖奶油色
            HealingColors.warmCream

            // 顶部大弧形渐变
            GeometryReader { geo in
                let w = geo.size.width
                let h = geo.size.height

                // 顶部渐变弧
                Ellipse()
                    .fill(
                        RadialGradient(
                            gradient: Gradient(colors: [
                                HealingColors.deepSage.opacity(0.18),
                                HealingColors.softSage.opacity(0.08),
                                Color.clear
                            ]),
                            center: .top,
                            startRadius: 0,
                            endRadius: w * 0.9
                        )
                    )
                    .frame(width: w * 1.6, height: h * 0.6)
                    .offset(x: -w * 0.3, y: -h * 0.15)

                // 漂浮光斑 1
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: 220, height: 220)
                    .blur(radius: 60)
                    .offset(
                        x: w * 0.6 + sin(phase * .pi * 2) * 20,
                        y: h * 0.15 + cos(phase * .pi * 2) * 15
                    )

                // 漂浮光斑 2
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.06))
                    .frame(width: 180, height: 180)
                    .blur(radius: 50)
                    .offset(
                        x: w * 0.1 + cos(phase * .pi * 2) * 15,
                        y: h * 0.55 + sin(phase * .pi * 2) * 20
                    )

                // 漂浮光斑 3
                Circle()
                    .fill(HealingColors.lavenderHaze.opacity(0.05))
                    .frame(width: 120, height: 120)
                    .blur(radius: 40)
                    .offset(
                        x: w * 0.75 - cos(phase * .pi * 2) * 10,
                        y: h * 0.7 - sin(phase * .pi * 2) * 12
                    )
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 10).repeatForever(autoreverses: true)) {
                phase = 1
            }
        }
    }
}

// MARK: - 品牌区域

struct PremiumBrandSection: View {
    let safeTop: CGFloat
    let layout: AdaptiveLayout
    @State private var showLogo = false
    @State private var showTitle = false
    @State private var showSubtitle = false
    @State private var pulseScale: CGFloat = 1.0

    var body: some View {
        VStack(spacing: ScaleFactor.spacing(20)) {
            Spacer()
                .frame(height: safeTop + ScaleFactor.spacing(36))

            // Logo 组合
            ZStack {
                // 外圈脉冲光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.12))
                    .frame(width: 140, height: 140)
                    .scaleEffect(pulseScale)

                // 中圈
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [
                                HealingColors.softSage.opacity(0.25),
                                HealingColors.deepSage.opacity(0.12)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 120, height: 120)

                // 主 Logo 圆
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [
                                HealingColors.deepSage,
                                HealingColors.forestMist
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 88, height: 88)
                    .shadow(
                        color: HealingColors.forestMist.opacity(0.35),
                        radius: 24,
                        y: 12
                    )

                // 心形 + AI 标识
                VStack(spacing: 2) {
                    Image(systemName: "heart.fill")
                        .font(.system(size: 28, weight: .medium))
                        .foregroundColor(.white)

                    // AI 小标签
                    Text("AI")
                        .font(.system(size: 9, weight: .bold, design: .rounded))
                        .foregroundColor(HealingColors.softSage)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(
                            Capsule()
                                .fill(Color.white.opacity(0.9))
                        )
                }
            }
            .scaleEffect(showLogo ? 1 : 0.5)
            .opacity(showLogo ? 1 : 0)

            // 品牌名称
            VStack(spacing: ScaleFactor.spacing(8)) {
                Text("灵犀健康")
                    .font(.system(size: UnifiedFont.title1, weight: .bold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [
                                HealingColors.textPrimary,
                                HealingColors.forestMist
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .opacity(showTitle ? 1 : 0)
                    .offset(y: showTitle ? 0 : 10)

                // 功能标签行
                HStack(spacing: ScaleFactor.spacing(16)) {
                    PremiumFeatureTag(icon: "brain.head.profile", text: "AI 问诊")
                    PremiumFeatureTag(icon: "stethoscope", text: "专业分析")
                    PremiumFeatureTag(icon: "shield.checkered", text: "隐私保护")
                }
                .opacity(showSubtitle ? 1 : 0)
                .offset(y: showSubtitle ? 0 : 8)
            }
        }
        .onAppear {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.75).delay(0.15)) {
                showLogo = true
            }
            withAnimation(.spring(response: 0.6, dampingFraction: 0.8).delay(0.35)) {
                showTitle = true
            }
            withAnimation(.spring(response: 0.5, dampingFraction: 0.85).delay(0.5)) {
                showSubtitle = true
            }
            withAnimation(.easeInOut(duration: 3).repeatForever(autoreverses: true)) {
                pulseScale = 1.08
            }
        }
    }
}

// MARK: - 功能标签

struct PremiumFeatureTag: View {
    let icon: String
    let text: String

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 10, weight: .medium))
            Text(text)
                .font(.system(size: UnifiedFont.caption2, weight: .medium))
        }
        .foregroundColor(HealingColors.forestMist)
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(
            Capsule()
                .fill(HealingColors.forestMist.opacity(0.08))
        )
    }
}

// MARK: - 登录表单

struct PremiumLoginForm: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding
    let layout: AdaptiveLayout
    @Binding var selectedLoginMethod: LoginMethod

    @State private var showContent = false
    @State private var isOneClickLoading = false

    var body: some View {
        VStack(spacing: ScaleFactor.spacing(20)) {
            // 登录方式选择器
            LoginMethodSelector(
                selectedMethod: $selectedLoginMethod
            )

            if selectedLoginMethod == .oneClick {
                // 一键登录区域
                OneClickLoginSection(
                    isLoading: isOneClickLoading,
                    onLogin: handleOneClickLogin
                )
            } else {
                // 表单标题
                VStack(alignment: .leading, spacing: 4) {
                    Text("手机号登录")
                        .font(.system(size: UnifiedFont.title3, weight: .bold))
                        .foregroundColor(HealingColors.textPrimary)

                    Text("未注册的手机号将自动创建账号")
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textTertiary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                // 手机号输入区
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                    Label("手机号码", systemImage: "phone.fill")
                        .font(.system(size: UnifiedFont.caption1, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    PhoneNumberTextField(
                        phoneNumber: $viewModel.phoneNumber,
                        displayNumber: $viewModel.displayPhoneNumber,
                        isFocused: focusedField.wrappedValue == .phone,
                        onPhoneChange: { phone, display in
                            viewModel.handlePhoneInput(display)
                        },
                        onComplete: {
                            focusedField.wrappedValue = .code
                            viewModel.onPhoneComplete()
                        }
                    )
                }

                // 验证码发送提示
                if viewModel.showCodeSentNotice {
                    PremiumCodeSentBanner(phoneText: viewModel.maskedPhoneText)
                }

                // 验证码区域
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                    HStack {
                        Label("验证码", systemImage: "lock.shield.fill")
                            .font(.system(size: UnifiedFont.caption1, weight: .medium))
                            .foregroundColor(HealingColors.textSecondary)

                        Spacer()

                        PremiumSendCodeButton(viewModel: viewModel)
                    }

                    VerificationCodeInput(
                        code: $viewModel.verificationCode,
                        codeLength: 6,
                        onComplete: { _ in
                            focusedField.wrappedValue = nil
                            viewModel.onCodeComplete()
                        },
                        style: VerificationCodeStyle(
                            baseFill: HealingColors.warmCream.opacity(0.6),
                            emptyBorder: HealingColors.softSage.opacity(0.3),
                            activeBorder: HealingColors.forestMist,
                            filledBorder: HealingColors.forestMist.opacity(0.6),
                            successBorder: HealingColors.forestMist,
                            textColor: HealingColors.textPrimary
                        ),
                        isExternallyFocused: focusedField.wrappedValue == .code
                    )
                }
            }

            // 协议区域
            PremiumAgreementSection(
                isAgreed: viewModel.isAgreed,
                onToggle: viewModel.toggleAgreement
            )

            // 登录按钮
            if selectedLoginMethod == .oneClick {
                PremiumOneClickLoginButton(
                    isLoading: isOneClickLoading,
                    action: handleOneClickLogin
                )
            } else {
                PremiumLoginButton(
                    isLoading: viewModel.isLoading,
                    isEnabled: viewModel.canLogin || viewModel.isLoading,
                    action: viewModel.login
                )
            }
        }
        .padding(ScaleFactor.padding(24))
        .background(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .fill(.ultraThinMaterial)
                .shadow(color: Color.black.opacity(0.06), radius: 24, x: 0, y: 12)
                .overlay(
                    RoundedRectangle(cornerRadius: 28, style: .continuous)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.white.opacity(0.6),
                                    HealingColors.softSage.opacity(0.2)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 1
                        )
                )
        )
        .opacity(showContent ? 1 : 0)
        .offset(y: showContent ? 0 : 20)
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.8).delay(0.3)) {
                showContent = true
            }
        }
    }

    // MARK: - 一键登录处理
    private func handleOneClickLogin() {
        isOneClickLoading = true

        Task {
            do {
                let result = try await OneClickAuthService.shared.oneClickLogin()

                await MainActor.run {
                    AuthManager.shared.login(
                        token: result.token,
                        refreshToken: result.refreshToken,
                        user: result.user,
                        isNewUser: result.isNewUser
                    )
                    isOneClickLoading = false
                }

            } catch {
                await MainActor.run {
                    isOneClickLoading = false
                    viewModel.errorMessage = error.localizedDescription
                    viewModel.showError = true
                }
            }
        }
    }
}

// MARK: - 验证码已发送横幅

struct PremiumCodeSentBanner: View {
    let phoneText: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 16))
                .foregroundColor(HealingColors.successGreen)

            Text("验证码已发送至 \(phoneText)")
                .font(.system(size: UnifiedFont.caption1))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(HealingColors.successGreen.opacity(0.08))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(HealingColors.successGreen.opacity(0.15), lineWidth: 1)
                )
        )
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}

// MARK: - 发送验证码按钮

struct PremiumSendCodeButton: View {
    @ObservedObject var viewModel: LoginViewModel

    private var isDisabled: Bool { !viewModel.canSendCode }

    var body: some View {
        Button(action: viewModel.sendVerificationCode) {
            HStack(spacing: 5) {
                if viewModel.uiState == .sendingCode {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: HealingColors.forestMist))
                        .scaleEffect(0.7)
                } else if viewModel.countdown > 0 {
                    // 倒计时圆环
                    ZStack {
                        Circle()
                            .stroke(HealingColors.forestMist.opacity(0.15), lineWidth: 2)
                            .frame(width: 20, height: 20)

                        Circle()
                            .trim(from: 0, to: CGFloat(viewModel.countdown) / 60.0)
                            .stroke(HealingColors.forestMist, style: StrokeStyle(lineWidth: 2, lineCap: .round))
                            .frame(width: 20, height: 20)
                            .rotationEffect(.degrees(-90))
                    }
                }

                Text(viewModel.codeButtonText)
                    .font(.system(size: UnifiedFont.caption1, weight: .semibold))
            }
            .foregroundColor(isDisabled ? HealingColors.textTertiary : HealingColors.forestMist)
            .padding(.horizontal, 14)
            .padding(.vertical, 7)
            .background(
                Capsule()
                    .fill(
                        isDisabled
                            ? HealingColors.warmSand.opacity(0.3)
                            : HealingColors.forestMist.opacity(0.1)
                    )
            )
        }
        .disabled(isDisabled)
    }
}

// MARK: - 协议同意

struct PremiumAgreementSection: View {
    let isAgreed: Bool
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            HStack(alignment: .top, spacing: 10) {
                // 选择框
                ZStack {
                    RoundedRectangle(cornerRadius: 6, style: .continuous)
                        .fill(isAgreed ? HealingColors.forestMist : Color.clear)
                        .frame(width: 20, height: 20)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6, style: .continuous)
                                .stroke(
                                    isAgreed ? HealingColors.forestMist : HealingColors.borderLight,
                                    lineWidth: 1.5
                                )
                        )

                    if isAgreed {
                        Image(systemName: "checkmark")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.white)
                    }
                }
                .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isAgreed)

                // 文字
                Group {
                    Text("我已阅读并同意 ")
                        .foregroundColor(HealingColors.textTertiary)
                    + Text("《用户协议》")
                        .foregroundColor(HealingColors.forestMist)
                    + Text(" 和 ")
                        .foregroundColor(HealingColors.textTertiary)
                    + Text("《隐私政策》")
                        .foregroundColor(HealingColors.forestMist)
                }
                .font(.system(size: UnifiedFont.caption1))
                .multilineTextAlignment(.leading)

                Spacer()
            }
        }
        .buttonStyle(.plain)
    }
}

// MARK: - 登录按钮

struct PremiumLoginButton: View {
    let isLoading: Bool
    let isEnabled: Bool
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                if isLoading {
                    ProgressView()
                        .tint(.white)
                        .scaleEffect(0.9)
                } else {
                    Text("登录 / 注册")
                        .font(.system(size: UnifiedFont.body, weight: .bold))

                    Image(systemName: "arrow.right")
                        .font(.system(size: 14, weight: .bold))
                        .offset(x: isPressed ? 3 : 0)
                }
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                Group {
                    if isEnabled {
                        LinearGradient(
                            colors: [
                                HealingColors.deepSage,
                                HealingColors.forestMist
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    } else {
                        LinearGradient(
                            colors: [
                                HealingColors.softSage.opacity(0.5),
                                HealingColors.deepSage.opacity(0.4)
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    }
                }
            )
            .clipShape(Capsule())
            .shadow(
                color: isEnabled ? HealingColors.forestMist.opacity(0.35) : Color.clear,
                radius: isPressed ? 8 : 16,
                x: 0,
                y: isPressed ? 4 : 8
            )
            .scaleEffect(isPressed ? 0.97 : 1.0)
        }
        .disabled(!isEnabled)
        .animation(.easeInOut(duration: 0.15), value: isEnabled)
        .onLongPressGesture(minimumDuration: 0, maximumDistance: .infinity, pressing: { pressing in
            withAnimation(.easeInOut(duration: 0.1)) {
                isPressed = pressing
            }
        }, perform: {})
    }
}

// MARK: - 加载遮罩

struct PremiumLoadingOverlay: View {
    @State private var rotation: Double = 0

    var body: some View {
        ZStack {
            Color.black.opacity(0.35)
                .ignoresSafeArea()

            VStack(spacing: 20) {
                ZStack {
                    // 外圈
                    Circle()
                        .stroke(HealingColors.softSage.opacity(0.3), lineWidth: 3)
                        .frame(width: 52, height: 52)

                    // 旋转弧
                    Circle()
                        .trim(from: 0, to: 0.65)
                        .stroke(
                            LinearGradient(
                                colors: [HealingColors.deepSage, Color.white],
                                startPoint: .leading,
                                endPoint: .trailing
                            ),
                            style: StrokeStyle(lineWidth: 3, lineCap: .round)
                        )
                        .frame(width: 52, height: 52)
                        .rotationEffect(.degrees(rotation))
                }

                Text("登录中…")
                    .font(.system(size: UnifiedFont.footnote, weight: .medium))
                    .foregroundColor(.white)
            }
            .padding(40)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .shadow(color: .black.opacity(0.2), radius: 20)
            )
        }
        .onAppear {
            withAnimation(.linear(duration: 1).repeatForever(autoreverses: false)) {
                rotation = 360
            }
        }
    }
}

// MARK: - 登录方式选择器

struct LoginMethodSelector: View {
    @Binding var selectedMethod: LoginMethod

    var body: some View {
        HStack(spacing: 8) {
            ForEach(LoginMethod.allCases, id: \.self) { method in
                LoginMethodButton(method: method, isSelected: selectedMethod == method) {
                    selectedMethod = method
                }
            }
        }
        .padding(.horizontal, 4)
    }

    private func LoginMethodButton(method: LoginMethod, isSelected: Bool, onTap: @escaping () -> Void) -> some View {
        Button(action: onTap) {
            HStack(spacing: 6) {
                Image(systemName: method.icon)
                    .font(.system(size: 13, weight: .medium))
                Text(method.displayName)
                    .font(.system(size: UnifiedFont.subheadline, weight: .medium))
            }
            .foregroundColor(isSelected ? .white : HealingColors.textSecondary)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                Group {
                    if isSelected {
                        Capsule()
                            .fill(
                                LinearGradient(
                                    colors: [HealingColors.deepSage, HealingColors.forestMist],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                    } else {
                        Capsule()
                            .fill(HealingColors.warmSand.opacity(0.3))
                    }
                }
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - 一键登录区域

struct OneClickLoginSection: View {
    let isLoading: Bool
    let onLogin: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            // 说明文字
            VStack(alignment: .leading, spacing: 4) {
                Text("一键登录")
                    .font(.system(size: UnifiedFont.title3, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Text("使用本机号码快速登录，无需输入")
                    .font(.system(size: UnifiedFont.footnote))
                    .foregroundColor(HealingColors.textTertiary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            // 提示信息
            HStack(spacing: 8) {
                Image(systemName: "info.circle.fill")
                    .font(.system(size: 12))
                    .foregroundColor(HealingColors.forestMist)

                Text("请使用移动数据网络（4G/5G）进行一键登录")
                    .font(.system(size: UnifiedFont.caption2))
                    .foregroundColor(HealingColors.textSecondary)

                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(HealingColors.forestMist.opacity(0.08))
            )
        }
    }
}

// MARK: - 一键登录按钮

struct PremiumOneClickLoginButton: View {
    let isLoading: Bool
    let action: () -> Void

    @State private var isPressed = false
    @State private var pulseScale: CGFloat = 1.0

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                if isLoading {
                    ProgressView()
                        .tint(.white)
                        .scaleEffect(0.9)
                } else {
                    Image(systemName: "antenna.radiowaves.left.and.right")
                        .font(.system(size: 18, weight: .semibold))
                        .offset(x: isPressed ? 3 : 0)

                    Text("一键登录")
                        .font(.system(size: UnifiedFont.body, weight: .bold))

                    Text("秒登录")
                        .font(.system(size: UnifiedFont.caption1, weight: .medium))
                        .foregroundColor(.white.opacity(0.8))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(
                            Capsule()
                                .fill(.white.opacity(0.2))
                        )
                }
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                ZStack {
                    // 脉冲效果
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.3))
                        .frame(width: 80, height: 80)
                        .scaleEffect(pulseScale)
                        .opacity(isLoading ? 0 : 1)

                    LinearGradient(
                        colors: [
                            HealingColors.forestMist,
                            HealingColors.deepSage
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                }
            )
            .clipShape(Capsule())
            .shadow(
                color: HealingColors.forestMist.opacity(0.4),
                radius: isPressed ? 10 : 20,
                x: 0,
                y: isPressed ? 5 : 10
            )
            .scaleEffect(isPressed ? 0.97 : 1.0)
        }
        .disabled(isLoading)
        .animation(.easeInOut(duration: 0.15), value: isPressed)
        .onLongPressGesture(minimumDuration: 0, maximumDistance: .infinity, pressing: { pressing in
            withAnimation(.easeInOut(duration: 0.1)) {
                isPressed = pressing
            }
        }, perform: {})
        .onAppear {
            if !isLoading {
                withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                    pulseScale = 1.3
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    LoginView()
}
