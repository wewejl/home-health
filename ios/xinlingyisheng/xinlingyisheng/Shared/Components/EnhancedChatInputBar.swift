import SwiftUI

// MARK: - 增强版统一输入栏 V2
/// 符合设计规范的统一输入栏，集成快捷功能区和隐私提示
struct EnhancedChatInputBarV2: View {
    @Binding var messageText: String
    var isSending: Bool = false
    var isDisabled: Bool = false
    var capabilities: AgentCapabilities?
    var onSend: () -> Void
    var onPhotoTap: () -> Void = {}
    var onDossierTap: () -> Void = {}
    var onActionTap: (QuickAction) -> Void = { _ in }
    
    @StateObject private var speechService = SimpleSpeechInputService.shared
    @State private var showSpeechError = false
    
    var body: some View {
        VStack(spacing: 0) {
            // 快捷功能区（仅当有能力配置时显示）
            if let caps = capabilities, !caps.actions.isEmpty {
                quickActionsRow
                
                Divider()
                    .padding(.horizontal, ScaleFactor.padding(16))
            }
            
            // 隐私提示
            privacyHint
            
            // 输入区域
            inputArea
        }
        .background(DossierColors.cardBackground)
        .onChangeCompat(of: speechService.recognizedText) { newValue in
            if !newValue.isEmpty {
                messageText = newValue
            }
        }
        .alert("语音识别", isPresented: $showSpeechError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(speechService.errorMessage ?? "语音识别出错")
        }
        .onChangeCompat(of: speechService.errorMessage) { newValue in
            if newValue != nil {
                showSpeechError = true
            }
        }
    }
    
    // MARK: - 快捷功能行
    private var quickActionsRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: ScaleFactor.spacing(12)) {
                ForEach(quickActions, id: \.id) { action in
                    QuickActionChip(
                        icon: action.icon,
                        title: action.title,
                        color: action.color,
                        isDisabled: isDisabled || isSending,
                        action: {
                            handleQuickAction(action)
                        }
                    )
                }
            }
            .padding(.horizontal, ScaleFactor.padding(16))
        }
        .padding(.vertical, ScaleFactor.padding(12))
    }
    
    // MARK: - 隐私提示
    private var privacyHint: some View {
        HStack(spacing: ScaleFactor.spacing(6)) {
            if speechService.isRecording {
                // 录音状态
                Circle()
                    .fill(Color.red)
                    .frame(width: ScaleFactor.size(8), height: ScaleFactor.size(8))
                Text("正在录音，请说话...")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(.red)
            } else {
                // 隐私提示
                Image(systemName: "lock.shield")
                    .font(.system(size: AdaptiveFont.footnote))
                Text("对话内容已加密保护")
                    .font(.system(size: AdaptiveFont.footnote))
            }
        }
        .foregroundColor(DossierColors.textTertiary)
        .padding(.vertical, ScaleFactor.padding(8))
    }
    
    // MARK: - 输入区域
    private var inputArea: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 语音按钮
            Button(action: {
                Task {
                    await speechService.toggleRecording()
                }
            }) {
                Image(systemName: speechService.isRecording ? "waveform.circle.fill" : "waveform.circle")
                    .font(.system(size: ScaleFactor.font(28)))
                    .foregroundColor(speechService.isRecording ? .red : DossierColors.textTertiary)
            }
            .disabled(isDisabled || isSending)
            
            // 输入框
            HStack {
                TextField("请描述您的问题...", text: $messageText)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DossierColors.textPrimary)
                    .disabled(isDisabled || isSending)
            }
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(10))
            .background(DossierColors.searchBackground)
            .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(20), style: .continuous))
            
            // 发送按钮
            Button(action: {
                if !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    onSend()
                }
            }) {
                Circle()
                    .fill(canSend ? DossierColors.primaryPurple : DossierColors.textTertiary)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .overlay(
                        Group {
                            if isSending {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "arrow.up")
                                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                                    .foregroundColor(.white)
                            }
                        }
                    )
            }
            .disabled(!canSend)
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.bottom, ScaleFactor.padding(24))
    }
    
    // MARK: - 计算属性
    private var canSend: Bool {
        !isDisabled && !isSending && !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
    
    private var quickActions: [QuickAction] {
        QuickAction.from(capabilities: capabilities)
    }
    
    // MARK: - 处理快捷功能点击
    private func handleQuickAction(_ action: QuickAction) {
        switch action.actionType {
        case .photoAnalysis:
            onPhotoTap()
        case .medicalDossier:
            onDossierTap()
        default:
            onActionTap(action)
        }
    }
}

// MARK: - 上传操作按钮视图 V2
/// 当用户触发拍照分析后显示的上传按钮区域
struct UploadActionButtonsViewV2: View {
    var isUploading: Bool = false
    var isAnalyzing: Bool = false
    var onCameraTap: () -> Void
    var onLibraryTap: () -> Void
    var onCancel: () -> Void = {}
    
    var isDisabled: Bool {
        isUploading || isAnalyzing
    }
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            if isUploading {
                // 上传中状态
                uploadingState
            } else if isAnalyzing {
                // 分析中状态
                analyzingState
            } else {
                // 正常按钮状态
                actionButtons
            }
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(DossierColors.blue.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(12)))
    }
    
    // MARK: - 上传中状态
    private var uploadingState: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            ProgressView()
                .scaleEffect(0.9)
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                Text("正在上传图片...")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DossierColors.textPrimary)
                
                Text("图片将保存到本地")
                    .font(.system(size: AdaptiveFont.caption1))
                    .foregroundColor(DossierColors.textSecondary)
            }
            
            Spacer()
        }
    }
    
    // MARK: - 分析中状态
    private var analyzingState: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            ProgressView()
                .scaleEffect(0.9)
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                Text("AI正在分析中...")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DossierColors.textPrimary)
                
                Text("请稍候，分析结果即将呈现")
                    .font(.system(size: AdaptiveFont.caption1))
                    .foregroundColor(DossierColors.textSecondary)
            }
            
            Spacer()
        }
    }
    
    // MARK: - 操作按钮
    private var actionButtons: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            // 提示文字
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "camera.viewfinder")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DossierColors.blue)
                
                Text("选择照片进行AI分析")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DossierColors.textPrimary)
                
                Spacer()
                
                // 取消按钮
                Button(action: onCancel) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: AdaptiveFont.title3))
                        .foregroundColor(DossierColors.textTertiary)
                }
            }
            
            // 按钮组
            HStack(spacing: ScaleFactor.spacing(12)) {
                // 拍照按钮
                Button(action: onCameraTap) {
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Image(systemName: "camera.fill")
                            .font(.system(size: AdaptiveFont.body))
                        Text("拍摄照片")
                            .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DossierColors.blue)
                    .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(10)))
                }
                .disabled(isDisabled)
                
                // 相册按钮
                Button(action: onLibraryTap) {
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Image(systemName: "photo.on.rectangle")
                            .font(.system(size: AdaptiveFont.body))
                        Text("从相册选择")
                            .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    }
                    .foregroundColor(DossierColors.blue)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(
                        RoundedRectangle(cornerRadius: ScaleFactor.size(10))
                            .stroke(DossierColors.blue, lineWidth: 1.5)
                    )
                }
                .disabled(isDisabled)
            }
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        // 增强输入栏
        EnhancedChatInputBarV2(
            messageText: .constant(""),
            capabilities: AgentCapabilities(
                displayName: "皮肤科智能体",
                description: "皮肤科智能体",
                actions: ["analyze_skin", "medical_dossier", "symptom_assessment"],
                acceptsMedia: ["image/jpeg", "image/png"]
            ),
            onSend: { print("Send") },
            onPhotoTap: { print("Photo") },
            onDossierTap: { print("Dossier") }
        )
        
        Divider()
        
        // 上传按钮区域 - 正常状态
        UploadActionButtonsViewV2(
            onCameraTap: { print("Camera") },
            onLibraryTap: { print("Library") }
        )
        
        // 上传按钮区域 - 上传中
        UploadActionButtonsViewV2(
            isUploading: true,
            onCameraTap: {},
            onLibraryTap: {}
        )
        
        // 上传按钮区域 - 分析中
        UploadActionButtonsViewV2(
            isAnalyzing: true,
            onCameraTap: {},
            onLibraryTap: {}
        )
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
