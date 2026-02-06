//
//  ModernConsultationView.swift
//  灵犀医生
//
//  现代化科室智能体问诊界面（治愈系风格）
//  连接真实后端API，使用 UnifiedChatViewModel
//  完全重写修复布局问题
//

import SwiftUI

// MARK: - 现代化问诊界面
struct ModernConsultationView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel = UnifiedChatViewModel()
    @StateObject private var authManager = AuthManager.shared

    // 医生/科室信息
    let doctorId: Int?
    let doctorName: String
    let department: String
    let doctorTitle: String
    let doctorBio: String

    // UI 状态
    @State private var messageText = ""
    @State private var isProfileExpanded = true
    @State private var showActionMenu = false
    @State private var showImagePicker = false
    @State private var showCamera = false
    @State private var showImageSourcePicker = false
    @State private var showHistoryList = false
    @State private var showNewChatConfirm = false
    @State private var showLoginPrompt = false
    @State private var isMuted = false

    // 按住说话状态
    @State private var showPressAndHoldOverlay = false
    @State private var isPressing = false
    @State private var isCanceling = false

    // 初始化
    init(doctor: ModernDoctorInfo) {
        self.doctorId = doctor.id
        self.doctorName = doctor.name
        self.department = doctor.department
        self.doctorTitle = doctor.title
        self.doctorBio = doctor.bio
    }

    init(doctorId: Int? = nil, doctorName: String, department: String, doctorTitle: String = "主治医师", doctorBio: String = "") {
        self.doctorId = doctorId
        self.doctorName = doctorName
        self.department = department
        self.doctorTitle = doctorTitle
        self.doctorBio = doctorBio
    }

    var body: some View {
        ZStack {
            // 主内容区域
            GeometryReader { geometry in
                let layout = AdaptiveLayout(screenWidth: geometry.size.width)

                ZStack {
                    // 背景色
                    HealingColors.background
                        .ignoresSafeArea()

                    VStack(spacing: 0) {
                        // 顶部导航栏
                        navBar(layout: layout)

                        // 主内容
                        if viewModel.isLoading {
                            loadingView(layout: layout)
                        } else {
                            contentView(layout: layout)
                        }
                    }

                    // 底部输入栏
                    if !viewModel.isLoading {
                        VStack {
                            Spacer()
                            WeChatStyleInputBar(
                                messageText: $messageText,
                                viewModel: viewModel,
                                isSending: viewModel.isSending,
                                isDisabled: viewModel.isLoading,
                                onSend: sendMessage,
                                onMenuTap: {
                                    showImageSourcePicker = true
                                },
                                onImagePickerTap: {
                                    showImageSourcePicker = true
                                },
                                layout: layout,
                                isPressing: $isPressing,
                                isCanceling: $isCanceling,
                                showOverlay: $showPressAndHoldOverlay
                            )
                        }
                    }
                }
            }

            // 按住说话覆盖层 - 底部卡片式，不覆盖聊天内容
            if showPressAndHoldOverlay {
                GeometryReader { overlayGeometry in
                    let layout = AdaptiveLayout(screenWidth: overlayGeometry.size.width)
                    PressAndHoldOverlayView(
                        viewModel: viewModel,
                        layout: layout,
                        isPresented: $showPressAndHoldOverlay,
                        isPressing: isPressing,
                        isCanceling: isCanceling
                    )
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .zIndex(100)
            }
        }
        .navigationBarHidden(true)
        .tabBarHidden(true)
        .task {
            if !authManager.isLoggedIn {
                showLoginPrompt = true
                return
            }
            await viewModel.initializeSession(doctorId: doctorId, department: department)
        }
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "发生未知错误")
        }
        .alert("需要登录", isPresented: $showLoginPrompt) {
            Button("去登录") { dismiss() }
            Button("取消", role: .cancel) {}
        } message: {
            Text("请先登录后再开始问诊")
        }
        .alert("高风险提示", isPresented: $viewModel.showRiskAlert) {
            Button("我知道了", role: .cancel) {}
        } message: {
            Text(viewModel.riskAlertMessage)
        }
        .sheet(isPresented: $showImagePicker) {
            ImagePicker(sourceType: .photoLibrary) { image in
                Task { await viewModel.handleSelectedImage(image) }
            }
        }
        .sheet(isPresented: $showCamera) {
            ImagePicker(sourceType: .camera) { image in
                Task { await viewModel.handleSelectedImage(image) }
            }
        }
        .confirmationDialog("选择图片来源", isPresented: $showImageSourcePicker, titleVisibility: .visible) {
            Button("拍照") { showCamera = true }
            Button("从相册选择") { showImagePicker = true }
            Button("取消", role: .cancel) {}
        }
        .alert("新建对话", isPresented: $showNewChatConfirm) {
            Button("确定") {
                Task { await viewModel.startNewConversation() }
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("确定要新建对话吗？当前对话将被保存")
        }
        .alert("确认生成病历", isPresented: $viewModel.showGenerateConfirmation) {
            Button("取消", role: .cancel) { viewModel.cancelGenerateDossier() }
            Button("继续生成") { viewModel.confirmGenerateDossier() }
        } message: {
            Text(viewModel.generateConfirmationMessage)
        }
        .sheet(isPresented: $showHistoryList) {
            SessionHistoryView(
                doctorId: doctorId,
                doctorName: doctorName,
                onSelectSession: { sessionId in
                    showHistoryList = false
                    Task { await viewModel.loadExistingSession(sessionId: sessionId) }
                }
            )
        }
        .onDisappear {
            viewModel.cleanup()
        }
    }

    // MARK: - 导航栏
    private func navBar(layout: AdaptiveLayout) -> some View {
        HStack(spacing: layout.cardSpacing / 2) {
            // 返回按钮
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: UnifiedFont.footnote, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
                    .frame(width: 44, height: 44)
                    .background(
                        Circle()
                            .fill(HealingColors.cardBackground)
                            .shadow(color: Color.black.opacity(0.05), radius: 4, y: 2)
                    )
            }

            // 标题
            VStack(alignment: .leading, spacing: 2) {
                Text(doctorName)
                    .font(.system(size: UnifiedFont.footnote, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                HStack(spacing: 4) {
                    Circle()
                        .fill(HealingColors.forestMist)
                        .frame(width: 6, height: 6)
                    Text("在线服务")
                        .font(.system(size: AdaptiveFont.caption - 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }

            Spacer()

            // 新建对话
            navBarButton(icon: "square.and.pencil", color: HealingColors.forestMist) {
                showNewChatConfirm = true
            }

            // 历史记录
            navBarButton(icon: "clock.arrow.circlepath", color: HealingColors.dustyBlue) {
                showHistoryList = true
            }

            // 静音按钮
            navBarButton(icon: isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill", color: HealingColors.forestMist) {
                isMuted.toggle()
                viewModel.toggleVoiceMute(isMuted)
                triggerHapticFeedback(.light)
            }

            // 生成病历
            navBarButton(icon: "doc.text.fill", color: HealingColors.warmSand) {
                viewModel.requestGenerateDossier()
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, 12)
        .background(HealingColors.cardBackground.opacity(0.9))
    }

    private func navBarButton(icon: String, color: Color, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(color)
                .frame(width: 36, height: 36)
                .background(
                    Circle()
                        .fill(color.opacity(0.15))
                )
        }
    }

    // MARK: - 加载视图
    private func loadingView(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            Spacer()
            ProgressView()
                .tint(HealingColors.forestMist)
            Text("初始化会话...")
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(HealingColors.textSecondary)
            Spacer()
        }
    }

    // MARK: - 内容视图
    private func contentView(layout: AdaptiveLayout) -> some View {
        ScrollViewReader { proxy in
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: layout.cardSpacing) {
                    // 医生信息卡片
                    doctorProfileCard(layout: layout)
                        .padding(.horizontal, layout.horizontalPadding)
                        .padding(.top, layout.cardSpacing / 2)

                    // 消息列表
                    LazyVStack(spacing: layout.cardSpacing / 2) {
                        ForEach(viewModel.messages) { message in
                            ChatMessageBubble(
                                message: message,
                                messageText: $messageText,
                                layout: layout
                            )
                            .id(message.id)
                        }
                    }
                    .padding(.horizontal, layout.horizontalPadding)

                    // 病历提示卡片
                    if viewModel.shouldShowDossierPrompt {
                        dossierPromptCard(layout: layout)
                            .padding(.horizontal, layout.horizontalPadding)
                    }

                    // 底部间距
                    Color.clear.frame(height: 100)
                }
            }
            .onChange(of: viewModel.messages.count) {
                if let lastMessage = viewModel.messages.last {
                    withAnimation {
                        proxy.scrollTo(lastMessage.id, anchor: .bottom)
                    }
                }
            }
        }
    }

    // MARK: - 医生信息卡片
    private func doctorProfileCard(layout: AdaptiveLayout) -> some View {
        VStack(spacing: 0) {
            Button(action: {
                withAnimation(.spring(response: 0.3)) {
                    isProfileExpanded.toggle()
                }
            }) {
                HStack(spacing: layout.cardSpacing / 2) {
                    // 头像
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [HealingColors.forestMist, HealingColors.deepSage],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)

                        Text(String(doctorName.prefix(1)))
                            .font(.system(size: UnifiedFont.title3, weight: .bold))
                            .foregroundColor(.white)
                    }
                    .overlay(Circle().stroke(HealingColors.cardBackground, lineWidth: 3))
                    .shadow(color: HealingColors.forestMist.opacity(0.2), radius: 6, y: 3)

                    // 信息
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Text(doctorName)
                                .font(.system(size: UnifiedFont.body, weight: .semibold))
                                .foregroundColor(HealingColors.textPrimary)

                            Text(doctorTitle)
                                .font(.system(size: UnifiedFont.caption))
                                .foregroundColor(HealingColors.forestMist)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(HealingColors.forestMist.opacity(0.15))
                                .clipShape(Capsule())
                        }

                        HStack(spacing: 4) {
                            Circle()
                                .fill(HealingColors.forestMist)
                                .frame(width: 6, height: 6)
                            Text(department)
                                .font(.system(size: UnifiedFont.caption))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                    }

                    Spacer()

                    Image(systemName: "chevron.down")
                        .font(.system(size: UnifiedFont.caption, weight: .semibold))
                        .foregroundColor(HealingColors.textTertiary)
                        .rotationEffect(.degrees(isProfileExpanded ? 180 : 0))
                }
                .padding(layout.cardInnerPadding)
            }
            .buttonStyle(PlainButtonStyle())

            // 展开的简介
            if isProfileExpanded && !doctorBio.isEmpty {
                VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                    Rectangle()
                        .fill(HealingColors.softSage.opacity(0.2))
                        .frame(height: 1)

                    Text(doctorBio)
                        .font(.system(size: UnifiedFont.caption))
                        .foregroundColor(HealingColors.textSecondary)
                        .lineLimit(3)
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.bottom, layout.cardInnerPadding)
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 10, y: 4)
    }

    // MARK: - 病历提示卡片
    private func dossierPromptCard(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            HStack(spacing: layout.cardSpacing / 2) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [
                                    HealingColors.forestMist.opacity(0.2),
                                    HealingColors.deepSage.opacity(0.12)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)
                        .shadow(color: HealingColors.forestMist.opacity(0.2), radius: 6, y: 2)

                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: UnifiedFont.subheadline))
                        .foregroundColor(HealingColors.forestMist)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("对话完成")
                        .font(.system(size: UnifiedFont.body, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)

                    Text(viewModel.isNewEvent ? "已为您创建新的病历资料夹" : "已更新病历资料夹")
                        .font(.system(size: UnifiedFont.caption))
                        .foregroundColor(HealingColors.textSecondary)
                }

                Spacer()
            }

            // 按钮
            HStack(spacing: layout.cardSpacing) {
                Button(action: { viewModel.continueConversation() }) {
                    Text("继续对话")
                        .font(.system(size: UnifiedFont.caption, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, layout.cardInnerPadding)
                        .background(
                            Capsule()
                                .fill(HealingColors.forestMist.opacity(0.12))
                                .overlay(
                                    Capsule()
                                        .stroke(HealingColors.forestMist.opacity(0.2), lineWidth: 1)
                                )
                        )
                }

                Button(action: { viewDossier() }) {
                    HStack(spacing: 4) {
                        Image(systemName: "doc.text.fill")
                            .font(.system(size: UnifiedFont.caption))
                        Text("查看病历")
                            .font(.system(size: UnifiedFont.caption, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding)
                    .background(
                        LinearGradient(
                            colors: [
                                HealingColors.forestMist,
                                HealingColors.deepSage,
                                HealingColors.forestMist.opacity(0.95)
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                    .shadow(color: HealingColors.forestMist.opacity(0.35), radius: 10, y: 4)
                }
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.06), radius: 14, y: 6)
        )
    }

    // MARK: - Actions
    private func sendMessage() {
        let text = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        messageText = ""
        Task {
            await viewModel.sendMessage(content: text)
        }
    }

    private func viewDossier() {
        print("View dossier: \(viewModel.eventId ?? "")")
    }

    // MARK: - 触觉反馈
    private func triggerHapticFeedback(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.impactOccurred()
    }
}

// MARK: - 消息气泡
struct ChatMessageBubble: View {
    let message: UnifiedChatMessage
    @Binding var messageText: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 4) {
            if !message.isFromUser {
                HStack(spacing: 8) {
                    aiAvatar
                    bubbleContent
                }
            } else {
                HStack {
                    Spacer()
                    bubbleContent
                }
            }

            Text(message.timestamp.formatted(date: .omitted, time: .shortened))
                .font(.system(size: AdaptiveFont.caption - 1))
                .foregroundColor(HealingColors.textTertiary)
                .padding(message.isFromUser ? .trailing : .leading, 8)
        }
    }

    private var aiAvatar: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [HealingColors.forestMist, HealingColors.deepSage],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 32, height: 32)

            Image(systemName: "heart.fill")
                .font(.system(size: 12))
                .foregroundColor(.white)
        }
    }

    @ViewBuilder
    private var bubbleContent: some View {
        switch message.messageType {
        case .text, .structuredResult:
            textBubble
        case .image(let image):
            imageBubble(image)
        case .loading:
            loadingBubble
        }
    }

    @ViewBuilder
    private var textBubble: some View {
        if message.isFromUser {
            Text(message.content)
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 20, style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [
                                    HealingColors.forestMist,
                                    HealingColors.deepSage,
                                    HealingColors.forestMist.opacity(0.95)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .shadow(color: Color.black.opacity(0.06), radius: 10, y: 3)
                )
        } else {
            Text(message.content)
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(HealingColors.textPrimary)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 20, style: .continuous)
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.06), radius: 10, y: 3)
                )
        }
    }

    private func imageBubble(_ image: UIImage) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(maxWidth: 240, maxHeight: 240)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

            if !message.content.isEmpty {
                Text(message.content)
                    .font(.system(size: UnifiedFont.caption))
                    .foregroundColor(HealingColors.textSecondary)
            }
        }
        .padding(8)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 6, y: 2)
    }

    private var loadingBubble: some View {
        HStack(spacing: 8) {
            ProgressView()
                .tint(HealingColors.forestMist)
            Text(message.content.isEmpty ? "正在思考中..." : message.content)
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(HealingColors.textSecondary)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

// MARK: - 数据模型
struct ModernDoctorInfo {
    let id: Int
    let name: String
    let title: String
    let department: String
    let bio: String
    let isOnline: Bool
    let rating: String
    let consultCount: String
    let responseTime: String

    static let demo = ModernDoctorInfo(
        id: 1,
        name: "AI 智能体",
        title: "智能问诊",
        department: "皮肤科",
        bio: "基于先进 AI 技术，提供专业的皮肤问诊服务，支持皮肤图像分析和检查报告解读。",
        isOnline: true,
        rating: "98%",
        consultCount: "10k+",
        responseTime: "实时"
    )
}

// MARK: - Preview
#Preview {
    ModernConsultationView(doctor: .demo)
}
