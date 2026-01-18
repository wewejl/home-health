import SwiftUI

// MARK: - 现代化科室智能体问诊界面
// 连接真实后端API，使用 UnifiedChatViewModel

struct ModernConsultationView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel = UnifiedChatViewModel()
    
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
    
    // 新增: 图片来源选择
    @State private var showImageSourcePicker = false
    
    // 新增: 会话管理
    @State private var showHistoryList = false
    @State private var showNewChatConfirm = false
    
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
        ZStack {
            MedicalColors.bgPrimary
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 悬浮导航栏
                ModernNavigationBar(
                    doctorName: doctorName,
                    isOnline: true,
                    onBack: { dismiss() },
                    onNewChat: { showNewChatConfirm = true },
                    onHistory: { showHistoryList = true },
                    onGenerateDossier: { viewModel.requestGenerateDossier() }
                )
                
                if viewModel.isLoading {
                    Spacer()
                    ProgressView("初始化会话...")
                    Spacer()
                } else {
                    // 主内容区域
                    mainContentView
                }
                
                Spacer(minLength: 0)
            }
            
            // 底部输入区域（固定）
            if !viewModel.isLoading {
                bottomInputArea
            }
        }
        .navigationBarHidden(true)
        .tabBarHidden(true)
        .task {
            await viewModel.initializeSession(doctorId: doctorId, department: department)
        }
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "发生未知错误")
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
        // 图片来源选择对话框
        .confirmationDialog("选择图片来源", isPresented: $showImageSourcePicker, titleVisibility: .visible) {
            Button("📷 拍照") {
                showCamera = true
            }
            Button("🖼️ 从相册选择") {
                showImagePicker = true
            }
            Button("取消", role: .cancel) {}
        }
        // 新建对话确认
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
        // 生成病历确认对话框
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
        // 历史对话列表
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
    }
    
    // MARK: - 主内容区域
    private var mainContentView: some View {
        ScrollViewReader { proxy in
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: MedicalSpacing.lg) {
                    // 医生信息卡片（可折叠）
                    doctorProfileCard
                        .padding(.horizontal, MedicalSpacing.lg)
                        .padding(.top, MedicalSpacing.md)
                    
                    // 聊天消息列表
                    LazyVStack(spacing: MedicalSpacing.sm) {
                        ForEach(viewModel.messages) { message in
                            ModernMessageBubbleAdapter(message: message, messageText: $messageText)
                                .id(message.id)
                                .transition(.asymmetric(
                                    insertion: .scale(scale: 0.9).combined(with: .opacity),
                                    removal: .opacity
                                ))
                        }
                    }
                    .padding(.horizontal, MedicalSpacing.lg)
                    .animation(.spring(response: 0.3, dampingFraction: 0.7), value: viewModel.messages.count)
                    
                    // 中间建议卡片 - 已移除，保持与竞品一致的纯消息流交互
                    // 所有建议现在直接在AI消息中给出
                    // if !viewModel.adviceHistory.isEmpty {
                    //     ForEach(viewModel.adviceHistory) { advice in
                    //         AdviceCardView(advice: advice, onAccept: {
                    //             print("[DEBUG] 用户确认收到建议: \(advice.title)")
                    //         })
                    //             .padding(.horizontal, MedicalSpacing.lg)
                    //             .transition(.move(edge: .bottom).combined(with: .opacity))
                    //     }
                    // }
                    
                    // 诊断卡片 - 已移除，初步建议现在直接在AI消息中给出
                    // 只在用户明确要求生成最终诊断报告时才显示结构化卡片
                    // if let diagnosisCard = viewModel.diagnosisCard {
                    //     DiagnosisSummaryCard(
                    //         card: diagnosisCard,
                    //         onViewDossier: { viewDossier() }
                    //     )
                    //     .padding(.horizontal, MedicalSpacing.lg)
                    //     .transition(.move(edge: .bottom).combined(with: .opacity))
                    // }
                    
                    // 病历提示卡片
                    if viewModel.shouldShowDossierPrompt {
                        ModernDossierPromptCard(
                            eventId: viewModel.eventId,
                            isNewEvent: viewModel.isNewEvent,
                            onViewDossier: { viewDossier() },
                            onContinue: { viewModel.continueConversation() }
                        )
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    
                    // 底部间距
                    Color.clear.frame(height: 160)
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
    private var doctorProfileCard: some View {
        VStack(spacing: 0) {
            Button(action: {
                withAnimation(.spring(response: 0.3)) {
                    isProfileExpanded.toggle()
                }
            }) {
                HStack(spacing: MedicalSpacing.md) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [MedicalColors.primaryBlue, MedicalColors.secondaryTeal],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 56, height: 56)
                        
                        Text(String(doctorName.prefix(1)))
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(.white)
                    }
                    .overlay(Circle().stroke(Color.white, lineWidth: 3))
                    .shadow(color: Color.black.opacity(0.1), radius: 4, y: 2)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Text(doctorName)
                                .font(MedicalTypography.h3)
                                .foregroundColor(MedicalColors.textPrimary)
                            
                            Text(doctorTitle)
                                .font(MedicalTypography.caption)
                                .foregroundColor(MedicalColors.primaryBlue)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(MedicalColors.primaryBlue.opacity(0.1))
                                .cornerRadius(MedicalCornerRadius.sm)
                        }
                        
                        Text(department)
                            .font(MedicalTypography.bodySmall)
                            .foregroundColor(MedicalColors.textSecondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.down")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(MedicalColors.textMuted)
                        .rotationEffect(.degrees(isProfileExpanded ? 180 : 0))
                }
                .padding(MedicalSpacing.lg)
            }
            .buttonStyle(PlainButtonStyle())
            
            if isProfileExpanded && !doctorBio.isEmpty {
                VStack(alignment: .leading, spacing: MedicalSpacing.md) {
                    Divider().padding(.horizontal, MedicalSpacing.lg)
                    
                    Text(doctorBio)
                        .font(MedicalTypography.bodySmall)
                        .foregroundColor(MedicalColors.textSecondary)
                        .lineLimit(3)
                        .padding(.horizontal, MedicalSpacing.lg)
                        .padding(.bottom, MedicalSpacing.md)
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .background(MedicalColors.bgCard)
        .cornerRadius(MedicalCornerRadius.lg)
        .shadow(color: Color.black.opacity(0.06), radius: 12, y: 4)
    }
    
    // MARK: - 底部输入区域
    private var bottomInputArea: some View {
        VStack(spacing: 0) {
            Spacer()
            
            if viewModel.isVoiceMode {
                // 语音模式：显示语音控制栏
                VStack(spacing: 0) {
                    // 实时识别显示
                    if !viewModel.currentRecognition.isEmpty {
                        HStack {
                            Image(systemName: "mic.fill")
                                .foregroundColor(.green)
                            Text(viewModel.currentRecognition)
                                .foregroundColor(MedicalColors.textPrimary)
                            Spacer()
                            RecordingIndicator()
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(Color(.systemGray6))
                    }
                    
                    VoiceControlBar(viewModel: viewModel, onImageTap: {
                        showImageSourcePicker = true
                    })
                }
                .background(Color(hex: "#E8F5E9"))
            } else {
                // 文字模式：显示原有输入栏
                VStack(spacing: 0) {
                    // 动态功能按钮
                    if showActionMenu, let capabilities = viewModel.capabilities {
                        actionButtonsView(capabilities: capabilities)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    
                    // 输入栏
                    ModernInputBarWithVoice(
                        messageText: $messageText,
                        isSending: viewModel.isSending,
                        isDisabled: viewModel.isLoading,
                        onSend: { sendMessage() },
                        onMenuTap: {
                            withAnimation(.spring(response: 0.3)) {
                                showActionMenu.toggle()
                            }
                        },
                        onVoiceTap: {
                            viewModel.toggleVoiceMode()
                        }
                    )
                }
                .background(
                    MedicalColors.bgCard
                        .shadow(color: Color.black.opacity(0.06), radius: 12, y: -4)
                        .ignoresSafeArea(edges: .bottom)
                )
            }
        }
    }
    
    // MARK: - 动态功能按钮
    private func actionButtonsView(capabilities: AgentCapabilities) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: MedicalSpacing.md) {
                ForEach(viewModel.availableActions, id: \.self) { action in
                    Button(action: { triggerAction(action) }) {
                        VStack(spacing: 6) {
                            Image(systemName: action.icon)
                                .font(.system(size: 24))
                                .foregroundColor(actionColor(action))
                                .frame(width: 56, height: 56)
                                .background(actionColor(action).opacity(0.1))
                                .clipShape(Circle())
                            
                            Text(action.displayName)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(MedicalColors.textPrimary)
                        }
                        .frame(width: 80)
                    }
                }
            }
            .padding(.horizontal, MedicalSpacing.lg)
            .padding(.vertical, MedicalSpacing.md)
        }
        .background(MedicalColors.bgCard)
    }
    
    private func actionColor(_ action: AgentAction) -> Color {
        switch action {
        case .analyzeSkin: return MedicalColors.secondaryTeal
        case .interpretReport: return Color(hex: "#8B5CF6")
        case .interpretECG: return MedicalColors.statusError
        default: return MedicalColors.primaryBlue
        }
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
    
    private func triggerAction(_ action: AgentAction) {
        showActionMenu = false
        viewModel.triggerAction(action)
        
        // 需要上传图片时显示选择对话框
        if action != .conversation {
            showImageSourcePicker = true
        }
    }
    
    private func generateDossier() {
        viewModel.requestGenerateDossier()
    }
    
    private func viewDossier() {
        // TODO: 跳转到病历详情页
        print("View dossier: \(viewModel.eventId ?? "")")
    }
}

// MARK: - 现代化导航栏
struct ModernNavigationBar: View {
    let doctorName: String
    let isOnline: Bool
    let onBack: () -> Void
    let onNewChat: () -> Void
    let onHistory: () -> Void
    let onGenerateDossier: () -> Void
    
    var body: some View {
        HStack(spacing: MedicalSpacing.sm) {
            // 返回按钮
            Button(action: onBack) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(MedicalColors.textPrimary)
                    .frame(width: 36, height: 36)
                    .background(Color.white.opacity(0.9))
                    .clipShape(Circle())
                    .shadow(color: Color.black.opacity(0.06), radius: 4, y: 2)
            }
            
            // 标题区域
            VStack(alignment: .leading, spacing: 2) {
                Text(doctorName)
                    .font(MedicalTypography.h4)
                    .foregroundColor(MedicalColors.textPrimary)
                
                HStack(spacing: 4) {
                    Circle()
                        .fill(isOnline ? MedicalColors.successGreen : MedicalColors.textMuted)
                        .frame(width: 6, height: 6)
                    Text(isOnline ? "在线" : "离线")
                        .font(MedicalTypography.caption)
                        .foregroundColor(MedicalColors.textSecondary)
                }
            }
            
            Spacer()
            
            // 新建对话按钮
            Button(action: onNewChat) {
                Image(systemName: "square.and.pencil")
                    .font(.system(size: 16))
                    .foregroundColor(MedicalColors.primaryBlue)
                    .frame(width: 36, height: 36)
                    .background(MedicalColors.primaryBlue.opacity(0.1))
                    .clipShape(Circle())
            }
            
            // 历史记录按钮
            Button(action: onHistory) {
                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: 16))
                    .foregroundColor(MedicalColors.secondaryTeal)
                    .frame(width: 36, height: 36)
                    .background(MedicalColors.secondaryTeal.opacity(0.1))
                    .clipShape(Circle())
            }
            
            // 生成病历按钮
            Button(action: onGenerateDossier) {
                Image(systemName: "doc.text.fill")
                    .font(.system(size: 16))
                    .foregroundColor(MedicalColors.statusWarning)
                    .frame(width: 36, height: 36)
                    .background(MedicalColors.statusWarning.opacity(0.1))
                    .clipShape(Circle())
            }
        }
        .padding(.horizontal, MedicalSpacing.lg)
        .padding(.vertical, MedicalSpacing.md)
        .background(
            Color.white.opacity(0.95)
                .background(.ultraThinMaterial)
        )
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
    }
}

// MARK: - 消息气泡适配器（适配 UnifiedChatMessage 到现代化 UI）
struct ModernMessageBubbleAdapter: View {
    let message: UnifiedChatMessage
    @Binding var messageText: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: MedicalSpacing.md) {
                if !message.isFromUser {
                    aiAvatar
                } else {
                    Spacer(minLength: 60)
                }
                
                VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 4) {
                    bubbleContent
                    
                    Text(message.timestamp.formatted(date: .omitted, time: .shortened))
                        .font(MedicalTypography.caption)
                        .foregroundColor(MedicalColors.textMuted)
                }
                
                if message.isFromUser {
                    // 用户没有头像
                } else {
                    Spacer(minLength: 60)
                }
            }
            
            // 快捷选项（仅 AI 消息显示）
            if !message.isFromUser && !message.quickOptions.isEmpty {
                quickOptionsView
                    .padding(.leading, 48) // 与消息对齐
            }
        }
    }
    
    private var aiAvatar: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [MedicalColors.primaryBlue, MedicalColors.secondaryTeal],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 36, height: 36)
            
            Image(systemName: "brain.head.profile")
                .font(.system(size: 16))
                .foregroundColor(.white)
        }
    }
    
    @ViewBuilder
    private var bubbleContent: some View {
        switch message.messageType {
        case .text:
            textBubble
        case .image(let image):
            imageBubble(image)
        case .structuredResult:
            textBubble
        case .loading:
            loadingBubble
        }
    }
    
    private var textBubble: some View {
        Group {
            if message.isFromUser {
                // 用户消息：使用普通 Text
                Text(message.content)
                    .font(MedicalTypography.bodyMedium)
                    .foregroundColor(.white)
            } else {
                // AI 消息：使用 Markdown 渲染
                MarkdownTextView(
                    message.content,
                    fontSize: 16,
                    textColor: MedicalColors.textPrimary
                )
            }
        }
        .padding(.horizontal, MedicalSpacing.lg)
        .padding(.vertical, MedicalSpacing.md)
        .background(
            message.isFromUser
                ? MedicalColors.primaryBlue
                : MedicalColors.aiMessageBg
        )
        .cornerRadius(MedicalCornerRadius.lg)
        .shadow(
            color: message.isFromUser
                ? MedicalColors.primaryBlue.opacity(0.2)
                : Color.black.opacity(0.04),
            radius: 8,
            y: 2
        )
    }
    
    private func imageBubble(_ image: UIImage) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(maxWidth: 240, maxHeight: 240)
                .cornerRadius(MedicalCornerRadius.md)
                .clipped()
            
            if !message.content.isEmpty {
                Text(message.content)
                    .font(MedicalTypography.bodySmall)
                    .foregroundColor(MedicalColors.textSecondary)
            }
        }
        .padding(8)
        .background(MedicalColors.bgCard)
        .cornerRadius(MedicalCornerRadius.lg)
        .shadow(color: Color.black.opacity(0.06), radius: 8, y: 2)
    }
    
    private var loadingBubble: some View {
        HStack(spacing: 8) {
            ProgressView()
                .scaleEffect(0.8)
            Text(message.content.isEmpty ? "正在思考中..." : message.content)
                .font(MedicalTypography.bodySmall)
                .foregroundColor(MedicalColors.textSecondary)
        }
        .padding(.horizontal, MedicalSpacing.lg)
        .padding(.vertical, MedicalSpacing.md)
        .background(MedicalColors.aiMessageBg)
        .cornerRadius(MedicalCornerRadius.lg)
    }
    
    private var quickOptionsView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(message.quickOptions) { option in
                    Button(action: {
                        // 追加到输入框，支持多选
                        if !messageText.isEmpty {
                            messageText += " "  // 用空格分隔
                        }
                        messageText += option.text
                    }) {
                        Text(option.text)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(MedicalColors.primaryBlue)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(MedicalColors.primaryBlue.opacity(0.1))
                            .cornerRadius(16)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(MedicalColors.primaryBlue.opacity(0.3), lineWidth: 1)
                            )
                    }
                }
            }
        }
    }
}

// MARK: - 输入栏
struct ModernInputBar: View {
    @Binding var messageText: String
    let isSending: Bool
    let isDisabled: Bool
    let onSend: () -> Void
    let onMenuTap: () -> Void
    
    var body: some View {
        HStack(alignment: .bottom, spacing: MedicalSpacing.md) {
            // 功能菜单按钮
            Button(action: onMenuTap) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 28))
                    .foregroundColor(isDisabled ? MedicalColors.textMuted : MedicalColors.primaryBlue)
            }
            .disabled(isDisabled)
            
            // 文本输入框
            ZStack(alignment: .leading) {
                if messageText.isEmpty {
                    Text("输入消息...")
                        .font(MedicalTypography.bodyMedium)
                        .foregroundColor(MedicalColors.textMuted)
                        .padding(.leading, MedicalSpacing.lg)
                }
                
                TextField("", text: $messageText, axis: .vertical)
                    .font(MedicalTypography.bodyMedium)
                    .foregroundColor(MedicalColors.textPrimary)
                    .lineLimit(1...5)
                    .padding(.horizontal, MedicalSpacing.md)
                    .padding(.vertical, MedicalSpacing.sm)
                    .disabled(isDisabled)
            }
            .frame(minHeight: 40)
            .background(MedicalColors.bgSecondary)
            .cornerRadius(MedicalCornerRadius.md)
            
            // 发送按钮
            Button(action: onSend) {
                ZStack {
                    Circle()
                        .fill(
                            messageText.isEmpty || isDisabled
                                ? MedicalColors.textMuted.opacity(0.3)
                                : MedicalColors.primaryBlue
                        )
                        .frame(width: 36, height: 36)
                    
                    if isSending {
                        ProgressView()
                            .scaleEffect(0.7)
                            .tint(.white)
                    } else {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.white)
                    }
                }
            }
            .disabled(messageText.isEmpty || isDisabled || isSending)
        }
        .padding(.horizontal, MedicalSpacing.lg)
        .padding(.vertical, MedicalSpacing.md)
    }
}

// MARK: - 带语音按钮的输入栏
struct ModernInputBarWithVoice: View {
    @Binding var messageText: String
    let isSending: Bool
    let isDisabled: Bool
    let onSend: () -> Void
    let onMenuTap: () -> Void
    let onVoiceTap: () -> Void
    
    var body: some View {
        HStack(alignment: .bottom, spacing: MedicalSpacing.md) {
            // 功能菜单按钮
            Button(action: onMenuTap) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 28))
                    .foregroundColor(isDisabled ? MedicalColors.textMuted : MedicalColors.primaryBlue)
            }
            .disabled(isDisabled)
            
            // 文本输入框
            ZStack(alignment: .leading) {
                if messageText.isEmpty {
                    Text("输入消息...")
                        .font(MedicalTypography.bodyMedium)
                        .foregroundColor(MedicalColors.textMuted)
                        .padding(.leading, MedicalSpacing.lg)
                }
                
                TextField("", text: $messageText, axis: .vertical)
                    .font(MedicalTypography.bodyMedium)
                    .foregroundColor(MedicalColors.textPrimary)
                    .lineLimit(1...5)
                    .padding(.horizontal, MedicalSpacing.md)
                    .padding(.vertical, MedicalSpacing.sm)
                    .disabled(isDisabled)
            }
            .frame(minHeight: 40)
            .background(MedicalColors.bgSecondary)
            .cornerRadius(MedicalCornerRadius.md)
            
            // 语音按钮
            Button(action: onVoiceTap) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 22))
                    .foregroundColor(isDisabled ? MedicalColors.textMuted : MedicalColors.secondaryTeal)
            }
            .disabled(isDisabled)
            
            // 发送按钮
            Button(action: onSend) {
                ZStack {
                    Circle()
                        .fill(
                            messageText.isEmpty || isDisabled
                                ? MedicalColors.textMuted.opacity(0.3)
                                : MedicalColors.primaryBlue
                        )
                        .frame(width: 36, height: 36)
                    
                    if isSending {
                        ProgressView()
                            .scaleEffect(0.7)
                            .tint(.white)
                    } else {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.white)
                    }
                }
            }
            .disabled(messageText.isEmpty || isDisabled || isSending)
        }
        .padding(.horizontal, MedicalSpacing.lg)
        .padding(.vertical, MedicalSpacing.md)
    }
}

// MARK: - 病历提示卡片
struct ModernDossierPromptCard: View {
    let eventId: String?
    let isNewEvent: Bool
    let onViewDossier: () -> Void
    let onContinue: () -> Void
    
    var body: some View {
        VStack(spacing: MedicalSpacing.lg) {
            // 图标 + 标题
            HStack(spacing: MedicalSpacing.md) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 32))
                    .foregroundColor(MedicalColors.successGreen)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("对话完成")
                        .font(MedicalTypography.h4)
                        .foregroundColor(MedicalColors.textPrimary)
                    
                    Text(isNewEvent ? "已为您创建新的病历资料夹" : "已更新病历资料夹")
                        .font(MedicalTypography.bodySmall)
                        .foregroundColor(MedicalColors.textSecondary)
                }
                
                Spacer()
            }
            
            // 操作按钮
            HStack(spacing: MedicalSpacing.md) {
                // 继续对话
                Button(action: onContinue) {
                    Text("继续对话")
                        .font(MedicalTypography.button)
                        .foregroundColor(MedicalColors.primaryBlue)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(MedicalColors.primaryBlue.opacity(0.1))
                        .cornerRadius(MedicalCornerRadius.md)
                }
                
                // 查看病历
                Button(action: onViewDossier) {
                    Text("查看病历")
                        .font(MedicalTypography.button)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(
                            LinearGradient(
                                colors: [MedicalColors.primaryBlue, MedicalColors.primaryBlueDark],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(MedicalCornerRadius.md)
                        .shadow(color: MedicalColors.primaryBlue.opacity(0.3), radius: 8, y: 4)
                }
            }
        }
        .padding(20)
        .background(MedicalColors.bgCard)
        .cornerRadius(MedicalCornerRadius.lg)
        .shadow(color: Color.black.opacity(0.08), radius: 16, y: 6)
        .padding(.horizontal, MedicalSpacing.lg)
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
