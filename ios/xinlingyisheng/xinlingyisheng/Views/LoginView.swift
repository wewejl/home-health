import SwiftUI

// MARK: - 登录页面（治愈系风格）

struct LoginView: View {
    @StateObject private var viewModel = LoginViewModel()
    @FocusState private var focusedField: LoginField?
    @Environment(\.openURL) private var openURL

    var onLoginSuccess: (() -> Void)?

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 背景层 - 治愈系渐变
                HealingLoginBackgroundView(layout: layout)
                    .ignoresSafeArea(.container, edges: .top)

                // 内容层 - 可滚动
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 0) {
                        // 顶部安全区域占位
                        Spacer(minLength: topSpacing(layout: layout))

                        // 头部
                        HealingLoginHeaderView(layout: layout)
                            .padding(.bottom, layout.cardSpacing)

                        // 表单卡片
                        HealingLoginFormCard(
                            viewModel: viewModel,
                            focusedField: $focusedField,
                            layout: layout
                        )
                        .padding(.horizontal, layout.horizontalPadding)

                        // 底部额外空间
                        Spacer(minLength: bottomSpacing(layout: layout))
                    }
                    .frame(maxWidth: .infinity)
                }

                // 加载遮罩
                if viewModel.isLoading {
                    HealingLoadingOverlay(layout: layout)
                }
            }
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    if focusedField == .phone {
                        Button("下一步") {
                            focusedField = .code
                        }
                        .font(.system(size: layout.bodyFontSize, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                    } else if focusedField == .code {
                        Button("完成") {
                            focusedField = nil
                        }
                        .font(.system(size: layout.bodyFontSize, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                    }
                }
            }
            .onAppear {
                DeviceInfoLogger.log(context: "LoginView")
                // 延迟聚焦手机号输入框
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
    }

    // MARK: - 布局常量
    private func topSpacing(layout: AdaptiveLayout) -> CGFloat {
        layout.cardInnerPadding * 3
    }

    private func bottomSpacing(layout: AdaptiveLayout) -> CGFloat {
        layout.cardInnerPadding * 10
    }
}

// MARK: - 治愈系背景视图

struct HealingLoginBackgroundView: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.6),
                    HealingColors.softSage.opacity(0.3)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            GeometryReader { geo in
                let size = min(geo.size.width, geo.size.height) * 0.7

                // 左上光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.12))
                    .frame(width: size, height: size)
                    .blur(radius: 60)
                    .offset(x: -geo.size.width * 0.2, y: -geo.size.height * 0.2)

                // 右下光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.08))
                    .frame(width: size * 1.3, height: size * 1.3)
                    .blur(radius: 80)
                    .offset(x: geo.size.width * 0.3, y: geo.size.height * 0.3)

                // 装饰性圆点
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.05))
                    .frame(width: layout.decorativeCircleSize * 0.25, height: layout.decorativeCircleSize * 0.25)
                    .offset(x: geo.size.width * 0.7, y: -geo.size.height * 0.3)

                Circle()
                    .fill(HealingColors.dustyBlue.opacity(0.05))
                    .frame(width: layout.decorativeCircleSize * 0.17, height: layout.decorativeCircleSize * 0.17)
                    .offset(x: geo.size.width * 0.2, y: geo.size.height * 0.6)
            }
        }
    }
}

// MARK: - 治愈系头部视图

struct HealingLoginHeaderView: View {
    @State private var showContent = false
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing / 2) {
            // Logo 区域
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [HealingColors.softSage, HealingColors.deepSage],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: logoSize, height: logoSize)

                Image(systemName: "cross.fill")
                    .font(.system(size: logoSize * 0.4, weight: .light))
                    .foregroundColor(.white)
            }

            Text("灵犀医生")
                .font(.system(size: layout.titleFontSize, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)

            Text("智能诊疗助手 · 随时获取专业建议")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
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

    private var logoSize: CGFloat {
        layout.iconLargeSize * 2.2
    }
}

// MARK: - 治愈系登录表单卡片

struct HealingLoginFormCard: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding
    let layout: AdaptiveLayout

    @State private var showContent = false

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            // 标题
            VStack(alignment: .leading, spacing: 4) {
                Text("手机号登录")
                    .font(.system(size: layout.bodyFontSize + 2, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Text("未注册的手机号将自动创建账号")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            // 手机号输入
            HealingPhoneInputSection(
                viewModel: viewModel,
                focusedField: focusedField,
                layout: layout
            )

            // 验证码已发送提示
            if viewModel.showCodeSentNotice {
                HealingCodeSentNotice(
                    phoneText: viewModel.maskedPhoneText,
                    layout: layout
                )
            }

            // 验证码输入
            HealingCodeInputSection(
                viewModel: viewModel,
                focusedField: focusedField,
                layout: layout
            )

            // 协议同意
            HealingAgreementSection(
                isAgreed: viewModel.isAgreed,
                onToggle: viewModel.toggleAgreement,
                layout: layout
            )

            // 登录按钮
            Button(action: viewModel.login) {
                HStack(spacing: layout.cardSpacing / 2) {
                    if viewModel.isLoading {
                        ProgressView()
                            .tint(.white)
                            .progressViewStyle(CircularProgressViewStyle())
                    } else {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: layout.captionFontSize + 2))

                        Text("登录 / 注册")
                            .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    }
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding + 2)
                .background(
                    LinearGradient(
                        colors: [HealingColors.deepSage, HealingColors.forestMist],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .clipShape(Capsule())
                .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 8, x: 0, y: 4)
            }
            .disabled(!viewModel.canLogin && !viewModel.isLoading)
            .opacity(viewModel.canLogin || viewModel.isLoading ? 1.0 : 0.6)
        }
        .padding(layout.cardInnerPadding + 6)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.06), radius: 16, x: 0, y: 6)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
        )
        .opacity(showContent ? 1 : 0)
        .offset(y: showContent ? 0 : 16)
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.8).delay(0.2)) {
                showContent = true
            }
        }
    }
}

// MARK: - 治愈系手机号输入区域

struct HealingPhoneInputSection: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "phone.fill")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)

                Text("手机号码")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)
            }

            HStack {
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
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardInnerPadding - 2)
            .background(HealingColors.warmCream.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
    }
}

// MARK: - 治愈系验证码已发送提示

struct HealingCodeSentNotice: View {
    let phoneText: String
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            ZStack {
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.15))
                    .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.forestMist)
            }

            Text("验证码已发送至 \(phoneText)")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(HealingColors.forestMist.opacity(0.1))
        )
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}

// MARK: - 治愈系验证码输入区域

struct HealingCodeInputSection: View {
    @ObservedObject var viewModel: LoginViewModel
    var focusedField: FocusState<LoginField?>.Binding
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            HStack {
                Image(systemName: "key.fill")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)

                Text("验证码")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)

                Spacer()

                HealingSendCodeButton(viewModel: viewModel, layout: layout)
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
}

// MARK: - 治愈系发送验证码按钮

struct HealingSendCodeButton: View {
    @ObservedObject var viewModel: LoginViewModel
    let layout: AdaptiveLayout

    private var isDisabled: Bool { !viewModel.canSendCode }
    private var buttonColor: Color {
        isDisabled ? HealingColors.textTertiary : HealingColors.forestMist
    }

    var body: some View {
        Button(action: viewModel.sendVerificationCode) {
            HStack(spacing: 6) {
                if viewModel.uiState == .sendingCode {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: buttonColor))
                        .scaleEffect(0.8)
                        .frame(width: layout.iconSmallSize / 2, height: layout.iconSmallSize / 2)
                } else if viewModel.countdown > 0 {
                    ZStack {
                        Circle()
                            .stroke(buttonColor.opacity(0.2), lineWidth: 2)
                            .frame(width: layout.iconSmallSize - 4, height: layout.iconSmallSize - 4)

                        Circle()
                            .trim(from: 0, to: CGFloat(viewModel.countdown) / 60.0)
                            .stroke(
                                LinearGradient(
                                    colors: [HealingColors.deepSage, HealingColors.forestMist],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ),
                                style: StrokeStyle(lineWidth: 2, lineCap: .round)
                            )
                            .frame(width: layout.iconSmallSize - 4, height: layout.iconSmallSize - 4)
                            .rotationEffect(.degrees(-90))
                            .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: UUID())
                    }
                }

                Text(viewModel.codeButtonText)
                    .font(.system(size: layout.captionFontSize, weight: .medium))
                    .foregroundColor(buttonColor)
            }
        }
        .disabled(isDisabled)
    }
}

// MARK: - 治愈系协议同意区域

struct HealingAgreementSection: View {
    let isAgreed: Bool
    let onToggle: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        Button(action: onToggle) {
            HStack(alignment: .center, spacing: 8) {
                ZStack {
                    RoundedRectangle(cornerRadius: 6, style: .continuous)
                        .fill(isAgreed ? HealingColors.forestMist : HealingColors.warmSand.opacity(0.5))
                        .frame(width: layout.captionFontSize + 8, height: layout.captionFontSize + 8)

                    Image(systemName: isAgreed ? "checkmark" : "")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.white)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text("同意并遵守以下条款")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.textSecondary)

                    HStack(spacing: 4) {
                        HealingAgreementLink(title: "《用户协议》", url: "terms")
                        Text("·")
                            .foregroundColor(HealingColors.textTertiary)
                        HealingAgreementLink(title: "《隐私政策》", url: "privacy")
                    }
                }
                Spacer()
            }
        }
        .buttonStyle(.plain)
        .padding(.top, 8)
    }
}

// MARK: - 治愈系协议链接

struct HealingAgreementLink: View {
    let title: String
    let url: String

    var body: some View {
        Link(destination: URL(string: url) ?? URL(string: "https://xinlinyisheng.com")!) {
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(HealingColors.forestMist)
                .underline(true, color: HealingColors.forestMist)
        }
    }
}

// MARK: - 治愈系加载遮罩

struct HealingLoadingOverlay: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: layout.cardSpacing) {
                ZStack {
                    Circle()
                        .stroke(HealingColors.forestMist.opacity(0.3), lineWidth: 3)
                        .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                    Circle()
                        .trim(from: 0, to: 0.7)
                        .stroke(
                            LinearGradient(
                                colors: [HealingColors.deepSage, HealingColors.forestMist],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            style: StrokeStyle(lineWidth: 3, lineCap: .round)
                        )
                        .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)
                        .rotationEffect(.degrees(360))
                        .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: UUID())
                }

                Text("登录中...")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(.white)
            }
            .padding(layout.cardInnerPadding * 4)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(Color.black.opacity(0.7))
            )
        }
        .transition(.opacity)
    }
}

// MARK: - Preview

#Preview {
    LoginView()
}
