import SwiftUI

// MARK: - ProfileSetupView
struct ProfileSetupView: View {
    @StateObject private var viewModel = ProfileSetupViewModel()
    @Environment(\.dismiss) private var dismiss
    
    var onComplete: (() -> Void)?
    var allowSkip: Bool = true
    
    var body: some View {
        GeometryReader { geometry in
            let horizontalPadding = AdaptiveSpacing.card
            
            ZStack {
                ProfileSetupBackgroundView()
                
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 0) {
                        Spacer()
                            .frame(height: adaptiveTopSpacing(safeTop: geometry.safeAreaInsets.top))
                        
                        ProfileSetupHeaderView()
                            .padding(.bottom, AdaptiveSpacing.section)
                        
                        ProfileFormCard(viewModel: viewModel)
                            .padding(.horizontal, horizontalPadding)
                        
                        ActionButtonsSection(
                            viewModel: viewModel,
                            allowSkip: allowSkip,
                            onComplete: {
                                onComplete?()
                                dismiss()
                            }
                        )
                        .padding(.top, AdaptiveSpacing.section)
                        .padding(.horizontal, horizontalPadding)
                        
                        Spacer()
                            .frame(height: adaptiveBottomSpacing(safeBottom: geometry.safeAreaInsets.bottom))
                    }
                    .frame(minHeight: geometry.size.height)
                }
                .scrollDismissesKeyboardCompat()
                
                if viewModel.isLoading {
                    ProfileLoadingOverlay()
                }
            }
            .ignoresSafeArea(.container, edges: .all)
        }
        .onChangeCompat(of: viewModel.isCompleted) { completed in
            if completed {
                onComplete?()
                dismiss()
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
        return max(safeTop + ScaleFactor.padding(20), ScaleFactor.size(40))
    }
    
    private func adaptiveBottomSpacing(safeBottom: CGFloat) -> CGFloat {
        return max(safeBottom + ScaleFactor.padding(24), ScaleFactor.size(40))
    }
}

// MARK: - 背景视图
struct ProfileSetupBackgroundView: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color.dynamicColor(
                        light: PremiumColorTheme.backgroundLight,
                        dark: PremiumColorTheme.backgroundDark
                    ),
                    Color.dynamicColor(
                        light: Color(red: 0.95, green: 0.97, blue: 0.99),
                        dark: Color(red: 0.06, green: 0.09, blue: 0.16)
                    )
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            
            GeometryReader { geo in
                let size = min(geo.size.width, geo.size.height) * 0.5
                
                Circle()
                    .fill(PremiumColorTheme.current.backgroundGlowColor.opacity(0.6))
                    .frame(width: size, height: size)
                    .blur(radius: 70)
                    .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.1)
            }
        }
    }
}

// MARK: - 头部视图
struct ProfileSetupHeaderView: View {
    @State private var showContent = false
    
    private var titleSize: CGFloat {
        AdaptiveFont.largeTitle
    }
    
    private var subtitleSize: CGFloat {
        AdaptiveFont.subheadline
    }
    
    var body: some View {
        VStack(spacing: AdaptiveSpacing.item) {
            Image(systemName: "person.crop.circle.badge.plus")
                .font(.system(size: adaptiveIconSize, weight: .light))
                .foregroundColor(PremiumColorTheme.primaryColor)
            
            Text("完善个人资料")
                .font(.system(size: titleSize, weight: .bold, design: .default))
                .foregroundColor(PremiumColorTheme.textPrimary)
            
            Text("填写基本信息，获得更好的服务体验")
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
    
    private var adaptiveIconSize: CGFloat {
        ScaleFactor.size(64)
    }
}

// MARK: - 表单卡片
struct ProfileFormCard: View {
    @ObservedObject var viewModel: ProfileSetupViewModel
    @State private var showContent = false
    
    private var cardPadding: CGFloat {
        ScaleFactor.padding(20)
    }
    
    private var itemSpacing: CGFloat {
        ScaleFactor.spacing(20)
    }
    
    var body: some View {
        GlassmorphicCard {
            VStack(spacing: itemSpacing) {
                ProfileFormSection(title: "基本信息", isRequired: true) {
                    VStack(spacing: AdaptiveSpacing.item) {
                        ProfileTextField(
                            title: "昵称",
                            placeholder: "请输入昵称",
                            text: $viewModel.nickname,
                            icon: "person.fill"
                        )
                        
                        GenderSelector(selectedGender: $viewModel.selectedGender)
                        
                        BirthdaySelector(
                            birthday: $viewModel.birthday,
                            showPicker: $viewModel.showBirthdayPicker,
                            displayText: viewModel.displayBirthday
                        )
                    }
                }
                
                Divider()
                    .background(PremiumColorTheme.textTertiary.opacity(0.3))
                
                ProfileFormSection(title: "紧急联系人", isRequired: false) {
                    VStack(spacing: AdaptiveSpacing.item) {
                        ProfileTextField(
                            title: "姓名",
                            placeholder: "紧急联系人姓名（选填）",
                            text: $viewModel.emergencyContactName,
                            icon: "person.2.fill"
                        )
                        
                        ProfileTextField(
                            title: "电话",
                            placeholder: "紧急联系人电话（选填）",
                            text: $viewModel.emergencyContactPhone,
                            icon: "phone.fill",
                            keyboardType: .phonePad
                        )
                        
                        ProfileTextField(
                            title: "关系",
                            placeholder: "与您的关系（选填）",
                            text: $viewModel.emergencyContactRelation,
                            icon: "heart.fill"
                        )
                    }
                }
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

// MARK: - 表单分组
struct ProfileFormSection<Content: View>: View {
    let title: String
    let isRequired: Bool
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack(spacing: ScaleFactor.spacing(4)) {
                Text(title)
                    .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    .foregroundColor(PremiumColorTheme.textPrimary)
                
                if isRequired {
                    Text("*")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .bold))
                        .foregroundColor(PremiumColorTheme.accentColor)
                }
            }
            
            content
        }
    }
}

// MARK: - 文本输入框
struct ProfileTextField: View {
    let title: String
    let placeholder: String
    @Binding var text: String
    var icon: String = "textformat"
    var keyboardType: UIKeyboardType = .default
    
    private var fontSize: CGFloat {
        AdaptiveFont.body
    }
    
    private var iconSize: CGFloat {
        AdaptiveFont.title3
    }
    
    var body: some View {
        HStack(spacing: AdaptiveSpacing.item) {
            Image(systemName: icon)
                .font(.system(size: iconSize, weight: .medium))
                .foregroundColor(PremiumColorTheme.textSecondary)
                .frame(width: ScaleFactor.size(24))
            
            TextField(placeholder, text: $text)
                .font(.system(size: fontSize, weight: .regular, design: .rounded))
                .keyboardType(keyboardType)
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(
            RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusSmall, style: .continuous)
                .fill(Color.dynamicColor(
                    light: Color.white.opacity(0.5),
                    dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.5)
                ))
        )
    }
}

// MARK: - 性别选择器
struct GenderSelector: View {
    @Binding var selectedGender: ProfileSetupViewModel.Gender
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(10)) {
            Image(systemName: "person.fill.viewfinder")
                .font(.system(size: adaptiveIconSize, weight: .medium))
                .foregroundColor(PremiumColorTheme.textSecondary)
                .frame(width: ScaleFactor.size(24))
            
            Text("性别")
                .font(.system(size: adaptiveFontSize))
                .foregroundColor(PremiumColorTheme.textSecondary)
            
            Spacer()
            
            HStack(spacing: ScaleFactor.spacing(8)) {
                ForEach(ProfileSetupViewModel.Gender.allCases.filter { $0 != .notSet }, id: \.rawValue) { gender in
                    GenderButton(
                        gender: gender,
                        isSelected: selectedGender == gender,
                        action: { selectedGender = gender }
                    )
                }
            }
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                .fill(Color.dynamicColor(
                    light: Color.white.opacity(0.5),
                    dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.5)
                ))
        )
    }
    
    private var adaptiveIconSize: CGFloat {
        AdaptiveFont.title3
    }
    
    private var adaptiveFontSize: CGFloat {
        AdaptiveFont.body
    }
}

// MARK: - 性别按钮
struct GenderButton: View {
    let gender: ProfileSetupViewModel.Gender
    let isSelected: Bool
    let action: () -> Void
    
    private var buttonSize: CGFloat {
        ScaleFactor.size(40)
    }
    
    var body: some View {
        Button(action: action) {
            Text(gender.displayName)
                .font(.system(size: AdaptiveFont.subheadline, weight: isSelected ? .semibold : .regular))
                .foregroundColor(isSelected ? .white : PremiumColorTheme.textSecondary)
                .frame(width: buttonSize * 1.8, height: buttonSize)
                .background(
                    RoundedRectangle(cornerRadius: LayoutConstants.compactSpacing, style: .continuous)
                        .fill(isSelected ? PremiumColorTheme.primaryColor : Color.clear)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                        .stroke(isSelected ? Color.clear : PremiumColorTheme.textTertiary.opacity(0.5), lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - 生日选择器
struct BirthdaySelector: View {
    @Binding var birthday: Date
    @Binding var showPicker: Bool
    let displayText: String
    
    var body: some View {
        VStack(spacing: 0) {
            Button(action: { withAnimation { showPicker.toggle() } }) {
                HStack(spacing: AdaptiveSpacing.item) {
                    Image(systemName: "calendar")
                        .font(.system(size: adaptiveIconSize, weight: .medium))
                        .foregroundColor(PremiumColorTheme.textSecondary)
                        .frame(width: 24)
                    
                    Text("生日")
                        .font(.system(size: adaptiveFontSize))
                        .foregroundColor(PremiumColorTheme.textSecondary)
                    
                    Spacer()
                    
                    Text(displayText)
                        .font(.system(size: adaptiveFontSize))
                        .foregroundColor(PremiumColorTheme.textPrimary)
                    
                    Image(systemName: showPicker ? "chevron.up" : "chevron.down")
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(PremiumColorTheme.textTertiary)
                }
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.vertical, ScaleFactor.padding(12))
                .background(
                    RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusSmall, style: .continuous)
                        .fill(Color.dynamicColor(
                            light: Color.white.opacity(0.5),
                            dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.5)
                        ))
                )
            }
            .buttonStyle(.plain)
            
            if showPicker {
                DatePicker(
                    "",
                    selection: $birthday,
                    in: ...Date(),
                    displayedComponents: .date
                )
                .datePickerStyle(.wheel)
                .labelsHidden()
                .environment(\.locale, Locale(identifier: "zh_CN"))
                .padding(.top, LayoutConstants.compactSpacing)
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
            }
        }
    }
    
    private var adaptiveIconSize: CGFloat {
        AdaptiveFont.title3
    }
    
    private var adaptiveFontSize: CGFloat {
        AdaptiveFont.body
    }
}

// MARK: - 操作按钮区
struct ActionButtonsSection: View {
    @ObservedObject var viewModel: ProfileSetupViewModel
    let allowSkip: Bool
    let onComplete: () -> Void
    
    @State private var showContent = false
    
    var body: some View {
        VStack(spacing: AdaptiveSpacing.item) {
            PrimaryButton(title: "保存", action: viewModel.submitProfile)
                .disabled(!viewModel.isFormValid)
                .opacity(viewModel.isFormValid ? 1.0 : 0.6)
            
            if allowSkip {
                Button(action: viewModel.skipSetup) {
                    Text("稍后完善")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(PremiumColorTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
        }
        .opacity(showContent ? 1 : 0)
        .onAppear {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.8).delay(0.3)) {
                showContent = true
            }
        }
    }
}

// MARK: - 加载遮罩
struct ProfileLoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()
            
            VStack(spacing: ScaleFactor.spacing(16)) {
                ProgressView()
                    .scaleEffect(1.5)
                    .tint(.white)
                Text("保存中...")
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
    ProfileSetupView()
}
