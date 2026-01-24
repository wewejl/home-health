import SwiftUI

// MARK: - 现代化科室智能体问诊界面（治愈系风格）
// 连接真实后端API，使用 UnifiedChatViewModel

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

    // 图片来源选择
    @State private var showImageSourcePicker = false

    // 会话管理
    @State private var showHistoryList = false
    @State private var showNewChatConfirm = false
    @State private var showLoginPrompt = false

    // 简化初始化（兼容旧接口）
    init(doctor: ModernDoctorInfo) {
        self.doctorId = doctor.id
        self.doctorName = doctor.name
        self.department = doctor.department
        self.doctorTitle = doctor.title
        self.doctorBio = doctor.bio
    }

    // 新的初始化方法
    init(doctorId: Int? = nil, doctorName: String, department: String, doctorTitle: String = "主治医师", doctorBio: String = "") {
        self.doctorId = doctorId
        self.doctorName = doctorName
        self.department = department
        self.doctorTitle = doctorTitle
        self.doctorBio = doctorBio
    }

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingConsultationBackground(layout: layout)

                VStack(spacing: 0) {
                    // 悬浮导航栏
                    HealingConsultationNavBar(
                        doctorName: doctorName,
                        isOnline: true,
                        onBack: { dismiss() },
                        onNewChat: { showNewChatConfirm = true },
                        onHistory: { showHistoryList = true },
                        onGenerateDossier: { viewModel.requestGenerateDossier() },
                        layout: layout
                    )

                    if viewModel.isLoading {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ProgressView()
                                .tint(HealingColors.forestMist)
                                .scaleEffect(1.2)
                            Text("初始化会话...")
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                        Spacer()
                    } else {
                        // 主内容区域
                        mainContentView(layout: layout)
                    }

                    Spacer(minLength: 0)
                }

                // 底部输入区域（固定）
                if !viewModel.isLoading {
                    HealingConsultationBottomInput(
                        messageText: $messageText,
                        viewModel: viewModel,
                        showActionMenu: $showActionMenu,
                        showImageSourcePicker: $showImageSourcePicker,
                        onSendMessage: sendMessage,
                        layout: layout
                    )
                }
            }
        }
        .navigationBarHidden(true)
        .tabBarHidden(true)
        .task {
            // 检查登录状态
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
            Button("去登录") {
                dismiss()
            }
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
            Button("拍照") {
                showCamera = true
            }
            Button("从相册选择") {
                showImagePicker = true
            }
            Button("取消", role: .cancel) {}
        }
        .alert("新建对话", isPresented: $showNewChatConfirm) {
            Button("确定") {
                Task {
                    await viewModel.startNewConversation()
                }
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("确定要新建对话吗？当前对话将被保存")
        }
        .alert("确认生成病历", isPresented: $viewModel.showGenerateConfirmation) {
            Button("取消", role: .cancel) {
                viewModel.cancelGenerateDossier()
            }
            Button("继续生成") {
                viewModel.confirmGenerateDossier()
            }
        } message: {
            Text(viewModel.generateConfirmationMessage)
        }
        .sheet(isPresented: $showHistoryList) {
            SessionHistoryView(
                doctorId: doctorId,
                doctorName: doctorName,
                onSelectSession: { sessionId in
                    showHistoryList = false
                    Task {
                        await viewModel.loadExistingSession(sessionId: sessionId)
                    }
                }
            )
        }
        .fullScreenCover(isPresented: $viewModel.isVoiceMode) {
            FullScreenVoiceModeView(
                viewModel: viewModel,
                onDismiss: {
                    viewModel.exitVoiceMode()
                },
                onSubtitleTap: {},
                onCameraTap: { showCamera = true },
                onPhotoLibraryTap: { showImageSourcePicker = true }
            )
        }
    }

    // MARK: - 主内容区域
    private func mainContentView(layout: AdaptiveLayout) -> some View {
        ScrollViewReader { proxy in
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: layout.cardSpacing) {
                    // 医生信息卡片（可折叠）
                    healingDoctorProfileCard(layout: layout)
                        .padding(.horizontal, layout.horizontalPadding)
                        .padding(.top, layout.cardSpacing / 2)

                    // 聊天消息列表
                    LazyVStack(spacing: layout.cardSpacing / 2) {
                        ForEach(viewModel.messages) { message in
                            HealingMessageBubbleAdapter(
                                message: message,
                                messageText: $messageText,
                                layout: layout
                            )
                            .id(message.id)
                            .transition(.asymmetric(
                                insertion: .scale(scale: 0.9).combined(with: .opacity),
                                removal: .opacity
                            ))
                        }
                    }
                    .padding(.horizontal, layout.horizontalPadding)
                    .animation(.spring(response: 0.3, dampingFraction: 0.7), value: viewModel.messages.count)

                    // 病历提示卡片
                    if viewModel.shouldShowDossierPrompt {
                        HealingDossierPromptCard(
                            eventId: viewModel.eventId,
                            isNewEvent: viewModel.isNewEvent,
                            onViewDossier: { viewDossier() },
                            onContinue: { viewModel.continueConversation() },
                            layout: layout
                        )
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    }

                    // 底部间距
                    Color.clear.frame(height: 180)
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
    private func healingDoctorProfileCard(layout: AdaptiveLayout) -> some View {
        VStack(spacing: 0) {
            Button(action: {
                withAnimation(.spring(response: 0.3)) {
                    isProfileExpanded.toggle()
                }
            }) {
                HStack(spacing: layout.cardSpacing / 2) {
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
                            .font(.system(size: layout.bodyFontSize + 2, weight: .bold))
                            .foregroundColor(.white)
                    }
                    .overlay(Circle().stroke(HealingColors.cardBackground, lineWidth: 3))
                    .shadow(color: HealingColors.forestMist.opacity(0.2), radius: 6, y: 3)

                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Text(doctorName)
                                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                                .foregroundColor(HealingColors.textPrimary)

                            Text(doctorTitle)
                                .font(.system(size: layout.captionFontSize))
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
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                    }

                    Spacer()

                    Image(systemName: "chevron.down")
                        .font(.system(size: layout.captionFontSize + 1, weight: .semibold))
                        .foregroundColor(HealingColors.textTertiary)
                        .rotationEffect(.degrees(isProfileExpanded ? 180 : 0))
                }
                .padding(layout.cardInnerPadding)
            }
            .buttonStyle(PlainButtonStyle())

            if isProfileExpanded && !doctorBio.isEmpty {
                VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                    Rectangle()
                        .fill(HealingColors.softSage.opacity(0.2))
                        .frame(height: 1)

                    Text(doctorBio)
                        .font(.system(size: layout.captionFontSize + 1))
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
}

// MARK: - 治愈系问诊背景
struct HealingConsultationBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.warmSand.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 右上角装饰
                Circle()
                    .fill(HealingColors.softSage.opacity(0.06))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: geo.size.width * 0.5, y: -geo.size.height * 0.15)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系导航栏
struct HealingConsultationNavBar: View {
    let doctorName: String
    let isOnline: Bool
    let onBack: () -> Void
    let onNewChat: () -> Void
    let onHistory: () -> Void
    let onGenerateDossier: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            // 返回按钮
            Button(action: onBack) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.05), radius: 4, y: 2)

                    Image(systemName: "chevron.left")
                        .font(.system(size: layout.captionFontSize + 2, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)
            }

            // 标题区域
            VStack(alignment: .leading, spacing: 2) {
                Text(doctorName)
                    .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                HStack(spacing: 4) {
                    Circle()
                        .fill(isOnline ? HealingColors.forestMist : HealingColors.textTertiary)
                        .frame(width: 6, height: 6)
                    Text(isOnline ? "在线服务" : "离线")
                        .font(.system(size: layout.captionFontSize - 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }

            Spacer()

            // 新建对话按钮
            Button(action: onNewChat) {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                    Image(systemName: "square.and.pencil")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.forestMist)
                }
            }

            // 历史记录按钮
            Button(action: onHistory) {
                ZStack {
                    Circle()
                        .fill(HealingColors.dustyBlue.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                    Image(systemName: "clock.arrow.circlepath")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.dustyBlue)
                }
            }

            // 生成病历按钮
            Button(action: onGenerateDossier) {
                ZStack {
                    Circle()
                        .fill(HealingColors.warmSand.opacity(0.2))
                        .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                    Image(systemName: "doc.text.fill")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.warmSand)
                }
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.9))
        .shadow(color: Color.black.opacity(0.02), radius: 6, y: 2)
    }
}

// MARK: - 治愈系消息气泡适配器
struct HealingMessageBubbleAdapter: View {
    let message: UnifiedChatMessage
    @Binding var messageText: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
            HStack(alignment: .top, spacing: layout.cardSpacing / 2) {
                if !message.isFromUser {
                    healingAIAvatar
                } else {
                    Spacer(minLength: 50)
                }

                VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 4) {
                    bubbleContent

                    Text(message.timestamp.formatted(date: .omitted, time: .shortened))
                        .font(.system(size: layout.captionFontSize - 1))
                        .foregroundColor(HealingColors.textTertiary)
                }

                // 用户消息：右侧不留空间（贴边显示）
                // AI 消息：右侧留空间（平衡布局）
                if !message.isFromUser {
                    Spacer(minLength: 50)
                }
            }

            // 快捷选项（仅 AI 消息显示）
            if !message.isFromUser && !message.quickOptions.isEmpty {
                healingQuickOptionsView
                    .padding(.leading, layout.iconLargeSize + 12)
            }
        }
    }

    private var healingAIAvatar: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [HealingColors.forestMist, HealingColors.deepSage],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)

            Image(systemName: "heart.fill")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(.white)
        }
    }

    @ViewBuilder
    private var bubbleContent: some View {
        switch message.messageType {
        case .text:
            healingTextBubble
        case .image(let image):
            healingImageBubble(image)
        case .structuredResult:
            healingTextBubble
        case .loading:
            healingLoadingBubble
        }
    }

    private var healingTextBubble: some View {
        Group {
            if message.isFromUser {
                Text(message.content)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(.white)
                    .padding(.horizontal, layout.cardInnerPadding)
                    .padding(.vertical, layout.cardInnerPadding - 2)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.forestMist, HealingColors.deepSage],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                    .shadow(
                        color: HealingColors.forestMist.opacity(0.15),
                        radius: 6,
                        y: 2
                    )
            } else {
                MarkdownTextView(
                    message.content,
                    fontSize: layout.captionFontSize + 1,
                    textColor: HealingColors.textPrimary
                )
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardInnerPadding - 2)
                .background(HealingColors.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                .shadow(
                    color: Color.black.opacity(0.03),
                    radius: 6,
                    y: 2
                )
            }
        }
    }

    private func healingImageBubble(_ image: UIImage) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(maxWidth: 240, maxHeight: 240)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

            if !message.content.isEmpty {
                Text(message.content)
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
            }
        }
        .padding(8)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 6, y: 2)
    }

    private var healingLoadingBubble: some View {
        HStack(spacing: 8) {
            ProgressView()
                .tint(HealingColors.forestMist)
                .scaleEffect(0.8)
            Text(message.content.isEmpty ? "正在思考中..." : message.content)
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardInnerPadding - 2)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private var healingQuickOptionsView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing / 2) {
                ForEach(message.quickOptions) { option in
                    Button(action: {
                        if !messageText.isEmpty {
                            messageText += " "
                        }
                        messageText += option.text
                    }) {
                        Text(option.text)
                            .font(.system(size: layout.captionFontSize, weight: .medium))
                            .foregroundColor(HealingColors.forestMist)
                            .padding(.horizontal, layout.cardInnerPadding)
                            .padding(.vertical, layout.cardSpacing / 2)
                            .background(HealingColors.forestMist.opacity(0.12))
                            .clipShape(Capsule())
                    }
                }
            }
        }
    }
}

// MARK: - 治愈系底部输入区域
struct HealingConsultationBottomInput: View {
    @Binding var messageText: String
    @ObservedObject var viewModel: UnifiedChatViewModel
    @Binding var showActionMenu: Bool
    @Binding var showImageSourcePicker: Bool
    let onSendMessage: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            if viewModel.isVoiceMode {
                // 语音模式：显示专业级语音控制栏
                VoiceControlBar(
                    viewModel: viewModel,
                    onImageTap: { showImageSourcePicker = true },
                    onClose: nil
                )
            } else {
                // 文字模式：显示输入栏
                VStack(spacing: 0) {
                    // 动态功能按钮
                    if showActionMenu, let capabilities = viewModel.capabilities {
                        healingActionButtonsView(capabilities: capabilities, layout: layout)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }

                    // 输入栏
                    HealingInputBarWithVoice(
                        messageText: $messageText,
                        isSending: viewModel.isSending,
                        isDisabled: viewModel.isLoading,
                        onSend: onSendMessage,
                        onMenuTap: {
                            withAnimation(.spring(response: 0.3)) {
                                showActionMenu.toggle()
                            }
                        },
                        onVoiceTap: {
                            viewModel.enterVoiceMode()
                        },
                        layout: layout
                    )
                }
                .background(
                    HealingColors.cardBackground
                        .shadow(color: Color.black.opacity(0.04), radius: 10, y: -4)
                        .ignoresSafeArea(edges: .bottom)
                )
            }
        }
    }

    private func healingActionButtonsView(capabilities: AgentCapabilities, layout: AdaptiveLayout) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing / 2) {
                ForEach(viewModel.availableActions, id: \.self) { action in
                    Button(action: {
                        showActionMenu = false
                        viewModel.triggerAction(action)
                        if action != .conversation {
                            showImageSourcePicker = true
                        }
                    }) {
                        VStack(spacing: layout.cardSpacing / 3) {
                            ZStack {
                                Circle()
                                    .fill(healingActionColor(action).opacity(0.15))
                                    .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)

                                Image(systemName: action.icon)
                                    .font(.system(size: layout.captionFontSize + 2))
                                    .foregroundColor(healingActionColor(action))
                            }

                            Text(action.displayName)
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textPrimary)
                        }
                        .frame(width: layout.iconLargeSize * 1.5)
                    }
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardSpacing / 2)
        }
        .background(HealingColors.cardBackground)
    }

    private func healingActionColor(_ action: AgentAction) -> Color {
        switch action {
        case .analyzeSkin: return HealingColors.dustyBlue
        case .interpretReport: return HealingColors.warmSand
        case .interpretECG: return HealingColors.terracotta
        default: return HealingColors.forestMist
        }
    }
}

// MARK: - 治愈系输入栏（带语音按钮）
struct HealingInputBarWithVoice: View {
    @Binding var messageText: String
    let isSending: Bool
    let isDisabled: Bool
    let onSend: () -> Void
    let onMenuTap: () -> Void
    let onVoiceTap: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        HStack(alignment: .bottom, spacing: layout.cardSpacing / 2) {
            // 功能菜单按钮
            Button(action: onMenuTap) {
                ZStack {
                    Circle()
                        .fill(isDisabled ? HealingColors.textTertiary.opacity(0.3) : HealingColors.forestMist.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)

                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: layout.captionFontSize + 5))
                        .foregroundColor(isDisabled ? HealingColors.textTertiary : HealingColors.forestMist)
                }
            }
            .disabled(isDisabled)

            // 输入框容器
            HStack(alignment: .bottom, spacing: 0) {
                ZStack(alignment: .leading) {
                    if messageText.isEmpty {
                        Text("输入消息...")
                            .font(.system(size: layout.captionFontSize + 1))
                            .foregroundColor(HealingColors.textTertiary)
                            .padding(.leading, layout.cardInnerPadding)
                    }

                    TextField("", text: $messageText, axis: .vertical)
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textPrimary)
                        .lineLimit(1...5)
                        .padding(.horizontal, layout.cardInnerPadding - 4)
                        .padding(.vertical, layout.cardSpacing / 2)
                        .disabled(isDisabled)
                }

                // 右侧按钮
                if messageText.isEmpty {
                    Button(action: onVoiceTap) {
                        Image(systemName: "mic.fill")
                            .font(.system(size: layout.captionFontSize + 3))
                            .foregroundColor(isDisabled ? HealingColors.textTertiary : HealingColors.dustyBlue)
                            .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)
                    }
                    .disabled(isDisabled)
                } else {
                    Button(action: onSend) {
                        ZStack {
                            Circle()
                                .fill(
                                    isSending || isDisabled
                                        ? HealingColors.textTertiary.opacity(0.3)
                                        : HealingColors.forestMist
                                )
                                .frame(width: layout.iconSmallSize - 6, height: layout.iconSmallSize - 6)

                            if isSending {
                                ProgressView()
                                    .scaleEffect(0.6)
                                    .tint(.white)
                            } else {
                                Image(systemName: "arrow.up")
                                    .font(.system(size: layout.captionFontSize + 1, weight: .bold))
                                    .foregroundColor(.white)
                            }
                        }
                        .padding(.trailing, 6)
                        .padding(.bottom, 6)
                    }
                    .disabled(isDisabled || isSending)
                }
            }
            .background(HealingColors.warmCream.opacity(0.6))
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
            )
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
    }
}

// MARK: - 治愈系病历提示卡片
struct HealingDossierPromptCard: View {
    let eventId: String?
    let isNewEvent: Bool
    let onViewDossier: () -> Void
    let onContinue: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            // 图标 + 标题
            HStack(spacing: layout.cardSpacing / 2) {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)

                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: layout.captionFontSize + 4))
                        .foregroundColor(HealingColors.forestMist)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("对话完成")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)

                    Text(isNewEvent ? "已为您创建新的病历资料夹" : "已更新病历资料夹")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textSecondary)
                }

                Spacer()
            }

            // 操作按钮
            HStack(spacing: layout.cardSpacing) {
                Button(action: onContinue) {
                    Text("继续对话")
                        .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, layout.cardInnerPadding)
                        .background(HealingColors.forestMist.opacity(0.12))
                        .clipShape(Capsule())
                }

                Button(action: onViewDossier) {
                    HStack(spacing: 4) {
                        Image(systemName: "doc.text.fill")
                            .font(.system(size: layout.captionFontSize))
                        Text("查看病历")
                            .font(.system(size: layout.captionFontSize + 1, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.forestMist, HealingColors.deepSage],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                    .shadow(color: HealingColors.forestMist.opacity(0.25), radius: 8, y: 3)
                }
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 10, y: 4)
        .padding(.horizontal, layout.horizontalPadding)
    }
}

// MARK: - 数据模型（兼容旧接口）
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
