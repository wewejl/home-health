import SwiftUI

// MARK: - 全屏语音模式视图（专业版）
struct FullScreenVoiceModeView: View {
    // MARK: - ViewModel
    @StateObject private var viewModel = VoiceModeViewModel()
    
    // MARK: - 外部回调
    var onDismiss: () -> Void = {}
    var onSubtitleTap: () -> Void = {}
    var onCameraTap: () -> Void = {}
    var onPhotoLibraryTap: () -> Void = {}
    var onSendMessage: ((String) async -> String?)?
    
    // MARK: - 颜色定义（使用统一设计系统 DXYColors）
    private let voiceBackgroundColor = DXYColors.background           // 统一背景色 #F7F6FB
    private let recordingPurple = DXYColors.primaryPurple             // 录音状态紫色 #5C44FF
    private let textGray = DXYColors.textSecondary                    // 次要文字色
    private let textDarkGray = DXYColors.textPrimary                  // 主要文字色
    private let buttonBgGray = Color(red: 0.95, green: 0.94, blue: 0.97)  // 按钮背景 #F2F1F7
    private let dangerRed = Color(red: 1.0, green: 0.35, blue: 0.35)  // 危险红色
    private let mutedGray = DXYColors.textTertiary                    // 静音灰色
    
    // MARK: - 动画状态
    @State private var pulseAnimation = false
    
    var body: some View {
        ZStack {
            // 全屏浅紫色背景（使用 DXYColors 统一色）
            voiceBackgroundColor
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 顶部导航栏
                topNavigationBar
                
                // 中央内容区域
                Spacer()
                centerContent
                Spacer()
                
                // 底部控制栏
                bottomControlBar
            }
            
            // 退出确认弹窗
            if viewModel.showExitConfirmation {
                exitConfirmationDialog
            }
        }
        .onAppear {
            setupViewModel()
            startPulseAnimation()
            Task {
                await viewModel.startVoiceMode()
            }
        }
        .onDisappear {
            viewModel.stopVoiceMode()
        }
    }
    
    // MARK: - Setup
    private func setupViewModel() {
        print("[FullScreenVoiceModeView] 🔧 setupViewModel 被调用")
        print("[FullScreenVoiceModeView] 🔧 onSendMessage 是否存在: \(onSendMessage != nil)")
        viewModel.onDismiss = onDismiss
        viewModel.onSendMessage = onSendMessage
        viewModel.onImageRequest = { sourceType in
            switch sourceType {
            case .camera:
                onCameraTap()
            case .photoLibrary:
                onPhotoLibraryTap()
            }
        }
        print("[FullScreenVoiceModeView] 🔧 viewModel.onSendMessage 设置完成: \(viewModel.onSendMessage != nil)")
    }
    
    private func startPulseAnimation() {
        withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) {
            pulseAnimation = true
        }
    }
    
    // MARK: - 顶部导航栏
    private var topNavigationBar: some View {
        HStack {
            // 左侧：头像 + 名称
            HStack(spacing: 10) {
                // AI 头像（紫色圆形背景 + 笑脸图标）
                ZStack {
                    Circle()
                        .fill(DXYColors.lightPurple)
                        .frame(width: 36, height: 36)

                    Image(systemName: "face.smiling")
                        .font(.system(size: 18))
                        .foregroundColor(DXYColors.primaryPurple)
                }
                
                Text("小荷AI医生")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(textDarkGray)
            }
            
            Spacer()
            
            // 右侧：字幕按钮
            Button(action: {
                onSubtitleTap()
                onDismiss()
            }) {
                Text("字幕")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(textDarkGray)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.white)
                    .cornerRadius(20)
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 16)
        .padding(.bottom, 20)
    }
    
    // MARK: - 中央内容区域
    @ViewBuilder
    private var centerContent: some View {
        VStack(spacing: 24) {
            switch viewModel.state {
            case .idle:
                idleStateContent
            case .listening:
                listeningStateContent
            case .processing:
                processingStateContent
            case .aiSpeaking:
                aiSpeakingStateContent
            case .error(let message):
                errorStateContent(message)
            }
        }
        .padding(.horizontal, 24)
    }
    
    // MARK: - 待机状态内容
    private var idleStateContent: some View {
        VStack(spacing: 40) {
            Spacer()
            
            // 麦克风状态图标
            if viewModel.isMicrophoneMuted {
                Image(systemName: "mic.slash.fill")
                    .font(.system(size: 48))
                    .foregroundColor(mutedGray)
                
                Text("麦克风已关闭")
                    .font(.system(size: 20, weight: .medium))
                    .foregroundColor(textGray)
            } else {
                Text("请说话")
                    .font(.system(size: 28, weight: .regular))
                    .foregroundColor(textGray)
            }
            
            Spacer()
            
            Text(viewModel.isMicrophoneMuted ? "点击麦克风按钮开启" : "开始说话")
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(textGray)
        }
        .frame(maxHeight: .infinity)
    }
    
    // MARK: - 识别中状态内容
    private var listeningStateContent: some View {
        VStack(spacing: 32) {
            Spacer()
            
            // 识别文字气泡
            if !viewModel.recognizedText.isEmpty {
                Text(viewModel.recognizedText)
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(textDarkGray)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
                    .background(Color.white)
                    .cornerRadius(16)
                    .shadow(color: Color.black.opacity(0.06), radius: 8, y: 4)
                    .transition(.scale.combined(with: .opacity))
            }
            
            Spacer()
            
            // 音量指示器
            HStack(spacing: 8) {
                // 波形动画
                HStack(spacing: 3) {
                    ForEach(0..<4, id: \.self) { index in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(recordingPurple)
                            .frame(width: 3, height: 8 + CGFloat(viewModel.audioLevel) * 12 * CGFloat(index + 1) / 4)
                            .animation(.easeInOut(duration: 0.1), value: viewModel.audioLevel)
                    }
                }
                .frame(height: 20)

                Text("正在聆听...")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(recordingPurple)
            }
        }
        .frame(maxHeight: .infinity)
    }
    
    // MARK: - 处理中状态内容
    private var processingStateContent: some View {
        VStack(spacing: 32) {
            Spacer()
            
            // 显示用户刚才说的话
            if !viewModel.recognizedText.isEmpty {
                Text(viewModel.recognizedText)
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(textDarkGray)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
                    .background(Color.white)
                    .cornerRadius(16)
                    .shadow(color: Color.black.opacity(0.06), radius: 8, y: 4)
            }
            
            Spacer()
            
            // 加载动画
            HStack(spacing: 8) {
                ProgressView()
                    .scaleEffect(0.8)
                
                Text("正在思考...")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(textGray)
            }
        }
        .frame(maxHeight: .infinity)
    }
    
    // MARK: - AI播报状态内容
    private var aiSpeakingStateContent: some View {
        VStack(spacing: 32) {
            Spacer()
            
            // AI回复气泡
            HStack(alignment: .top, spacing: 12) {
                Text(viewModel.aiResponseText)
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(textDarkGray)
                    .lineSpacing(4)
                
                // 播报动画图标
                Image(systemName: "speaker.wave.2.fill")
                    .font(.system(size: 16))
                    .foregroundColor(DXYColors.primaryPurple)
                    .opacity(pulseAnimation ? 1.0 : 0.5)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.white)
            .cornerRadius(16)
            .shadow(color: Color.black.opacity(0.06), radius: 8, y: 4)
            
            Spacer()
            
            Text("点击或说话打断")
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(textGray)
        }
        .frame(maxHeight: .infinity)
        .onTapGesture {
            viewModel.interruptAISpeaking()
        }
    }
    
    // MARK: - 错误状态内容
    private func errorStateContent(_ message: String) -> some View {
        VStack(spacing: 24) {
            Spacer()
            
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 48))
                .foregroundColor(dangerRed)
            
            Text(message)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(textDarkGray)
                .multilineTextAlignment(.center)
            
            Button(action: {
                Task {
                    await viewModel.startVoiceMode()
                }
            }) {
                Text("重试")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 32)
                    .padding(.vertical, 12)
                    .background(DXYColors.primaryPurple)
                    .cornerRadius(20)
            }
            
            Spacer()
        }
        .frame(maxHeight: .infinity)
    }
    
    // MARK: - 底部控制栏
    private var bottomControlBar: some View {
        VStack(spacing: 16) {
            // 4个圆形按钮：麦克风、拍照、相册、退出
            HStack(spacing: 32) {
                // 1. 麦克风按钮（静音/取消静音）
                VoiceModeCircleButton(
                    icon: viewModel.isMicrophoneMuted ? "mic.slash.fill" : "mic.fill",
                    label: viewModel.isMicrophoneMuted ? "已静音" : "麦克风",
                    isHighlighted: viewModel.state == .listening && !viewModel.isMicrophoneMuted,
                    highlightColor: recordingPurple,
                    iconColor: viewModel.isMicrophoneMuted ? mutedGray : DXYColors.textSecondary
                ) {
                    viewModel.toggleMicrophone()
                    // 提供触觉反馈
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                }
                
                // 2. 拍照按钮
                VoiceModeCircleButton(
                    icon: "camera.fill",
                    label: "拍照",
                    isHighlighted: false,
                    highlightColor: .clear
                ) {
                    viewModel.requestCamera()
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                }
                
                // 3. 相册按钮
                VoiceModeCircleButton(
                    icon: "photo.on.rectangle",
                    label: "相册",
                    isHighlighted: false,
                    highlightColor: .clear
                ) {
                    viewModel.requestPhotoLibrary()
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                }
                
                // 4. 退出按钮
                VoiceModeCircleButton(
                    icon: "xmark",
                    label: "退出",
                    isHighlighted: false,
                    highlightColor: .clear,
                    iconColor: dangerRed
                ) {
                    viewModel.requestExit()
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                }
            }
            
            // 底部提示文字
            Text("内容由 AI 生成，仅供参考")
                .font(.system(size: 12, weight: .regular))
                .foregroundColor(DXYColors.textTertiary)
                .padding(.bottom, 8)
        }
        .padding(.horizontal, 24)
        .padding(.bottom, 24)
    }
    
    // MARK: - 退出确认弹窗
    private var exitConfirmationDialog: some View {
        ZStack {
            // 半透明遮罩
            Color.black.opacity(0.4)
                .ignoresSafeArea()
                .onTapGesture {
                    viewModel.cancelExit()
                }
            
            // 弹窗卡片
            VStack(spacing: 24) {
                // 标题
                Text("是否退出语音模式?")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(textDarkGray)
                
                // 按钮组
                HStack(spacing: 16) {
                    // 取消按钮
                    Button(action: {
                        viewModel.cancelExit()
                    }) {
                        Text("取消")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(DXYColors.textSecondary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(buttonBgGray)
                            .cornerRadius(8)
                    }

                    // 确认按钮
                    Button(action: {
                        viewModel.confirmExit()
                    }) {
                        Text("确认")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(DXYColors.primaryPurple)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(Color.white)
                            .cornerRadius(8)
                    }
                }
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 24)
            .background(Color.white)
            .cornerRadius(16)
            .shadow(color: Color.black.opacity(0.15), radius: 20, y: 10)
            .padding(.horizontal, 48)
        }
    }
}

// MARK: - 圆形按钮组件
struct VoiceModeCircleButton: View {
    let icon: String
    let label: String
    let isHighlighted: Bool
    let highlightColor: Color
    var iconColor: Color = DXYColors.textSecondary
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                ZStack {
                    Circle()
                        .fill(isHighlighted ? highlightColor : Color.white)
                        .frame(width: 56, height: 56)
                        .shadow(color: Color.black.opacity(0.08), radius: 8, y: 4)

                    Image(systemName: icon)
                        .font(.system(size: 22))
                        .foregroundColor(isHighlighted ? .white : iconColor)
                }

                Text(label)
                    .font(.system(size: 12, weight: .regular))
                    .foregroundColor(DXYColors.textSecondary)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Preview
#Preview("待机状态") {
    FullScreenVoiceModeView()
}

#Preview("识别中") {
    FullScreenVoiceModeView()
}

#Preview("AI播报") {
    FullScreenVoiceModeView()
}
