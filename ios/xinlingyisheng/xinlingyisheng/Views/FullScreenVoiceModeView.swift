import SwiftUI

// MARK: - 全屏语音模式视图（治愈系风格）
struct FullScreenVoiceModeView: View {
    // MARK: - ViewModel
    @ObservedObject var viewModel: UnifiedChatViewModel

    // MARK: - 外部回调
    var onDismiss: () -> Void = {}
    var onSubtitleTap: () -> Void = {}
    var onCameraTap: () -> Void = {}
    var onPhotoLibraryTap: () -> Void = {}

    // MARK: - 动画状态
    @State private var pulseAnimation = false

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingVoiceBackground(layout: layout)

                VStack(spacing: 0) {
                    // 顶部导航栏
                    HealingVoiceTopNavBar(
                        onSubtitleTap: {
                            onSubtitleTap()
                            onDismiss()
                        },
                        layout: layout
                    )

                    // 对话历史区域
                    HealingVoiceConversationScrollView(
                        viewModel: viewModel,
                        layout: layout
                    )

                    Spacer(minLength: 0)

                    // 实时识别区域
                    HealingVoiceRealtimeArea(
                        viewModel: viewModel,
                        pulseAnimation: $pulseAnimation,
                        layout: layout
                    )

                    // 底部控制栏
                    HealingVoiceBottomControlBar(
                        viewModel: viewModel,
                        onCameraTap: onCameraTap,
                        onPhotoLibraryTap: onPhotoLibraryTap,
                        layout: layout
                    )
                }

                // 退出确认弹窗
                if viewModel.showExitConfirmation {
                    HealingVoiceExitConfirmationDialog(
                        viewModel: viewModel,
                        layout: layout
                    )
                }
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
            // 确保语音服务完全停止（防止未正常退出的情况）
            viewModel.stopVoiceMode()
        }
    }

    // MARK: - Setup
    private func setupViewModel() {
        viewModel.onVoiceImageRequest = { sourceType in
            switch sourceType {
            case .camera: onCameraTap()
            case .photoLibrary: onPhotoLibraryTap()
            }
        }
    }

    private func startPulseAnimation() {
        withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) {
            pulseAnimation = true
        }
    }
}

// MARK: - 治愈系语音背景
struct HealingVoiceBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.softSage.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.06))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.2)
                    .ignoresSafeArea()

                // 底部装饰光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: -geo.size.width * 0.3, y: geo.size.height * 0.3)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系语音顶部导航栏
struct HealingVoiceTopNavBar: View {
    let onSubtitleTap: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        HStack {
            // 左侧：头像 + 名称
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
                        .frame(width: layout.iconSmallSize + 12, height: layout.iconSmallSize + 12)
                        .shadow(color: HealingColors.forestMist.opacity(0.2), radius: 6, x: 0, y: 3)

                    Image(systemName: "heart.fill")
                        .font(.system(size: layout.captionFontSize + 2))
                        .foregroundColor(.white)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text("鑫琳医生")
                        .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)

                    Text("随时为您服务")
                        .font(.system(size: layout.captionFontSize - 1))
                        .foregroundColor(HealingColors.forestMist.opacity(0.8))
                }
            }

            Spacer()

            // 右侧：字幕按钮
            Button(action: onSubtitleTap) {
                HStack(spacing: 4) {
                    Image(systemName: "captions.bubble.fill")
                        .font(.system(size: layout.captionFontSize))
                    Text("字幕")
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                }
                .foregroundColor(HealingColors.forestMist)
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardSpacing / 2)
                .background(HealingColors.cardBackground)
                .clipShape(Capsule())
                .shadow(color: Color.black.opacity(0.04), radius: 4, x: 0, y: 2)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
        .shadow(color: Color.black.opacity(0.02), radius: 4, x: 0, y: 2)
    }
}

// MARK: - 治愈系对话历史滚动区域
struct HealingVoiceConversationScrollView: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    let layout: AdaptiveLayout

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(spacing: layout.cardSpacing) {
                    // 对话历史消息
                    ForEach(Array(viewModel.messages.enumerated()), id: \.element.id) { index, message in
                        healingChatMessageBubble(message, isLatest: index == viewModel.messages.count - 1)
                    }

                    Color.clear.frame(height: layout.cardSpacing)
                }
                .padding(.horizontal, layout.horizontalPadding)
                .padding(.top, layout.cardSpacing)
            }
            .onChange(of: viewModel.messages.count) { oldValue, newValue in
                if newValue > oldValue {
                    withAnimation(.easeOut(duration: 0.3)) {
                        if let lastId = viewModel.messages.last?.id {
                            proxy.scrollTo(lastId, anchor: .bottom)
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func healingChatMessageBubble(_ message: UnifiedChatMessage, isLatest: Bool) -> some View {
        HStack {
            if message.isFromUser {
                Spacer()

                Text(message.content)
                    .font(.system(size: layout.captionFontSize + 1, weight: isLatest ? .medium : .regular))
                    .foregroundColor(HealingColors.textPrimary)
                    .padding(.horizontal, layout.cardInnerPadding)
                    .padding(.vertical, layout.cardInnerPadding - 2)
                    .background(
                        Group {
                            if isLatest {
                                LinearGradient(
                                    colors: [HealingColors.forestMist.opacity(0.15), HealingColors.forestMist.opacity(0.08)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            } else {
                                HealingColors.forestMist.opacity(0.08)
                            }
                        }
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(
                                isLatest ? HealingColors.forestMist.opacity(0.3) : HealingColors.forestMist.opacity(0.15),
                                lineWidth: isLatest ? 1.5 : 1
                            )
                    )
                    .shadow(
                        color: isLatest ? HealingColors.forestMist.opacity(0.1) : Color.clear,
                        radius: isLatest ? 6 : 0,
                        y: isLatest ? 3 : 0
                    )
            } else {
                // AI 消息
                HStack(alignment: .top, spacing: layout.cardSpacing / 3) {
                    // AI 头像
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [HealingColors.forestMist, HealingColors.deepSage],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                        Image(systemName: "heart.fill")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(.white)
                    }

                    Text(message.content)
                        .font(.system(size: layout.captionFontSize + 1, weight: isLatest ? .medium : .regular))
                        .foregroundColor(HealingColors.textPrimary)
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.vertical, layout.cardInnerPadding - 2)
                        .background(HealingColors.cardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                        .shadow(
                            color: isLatest ? Color.black.opacity(0.06) : Color.black.opacity(0.02),
                            radius: isLatest ? 6 : 3,
                            y: isLatest ? 2 : 1
                        )

                    Spacer()
                }
            }
        }
        .id(message.id)
    }
}

// MARK: - 治愈系实时识别区域
struct HealingVoiceRealtimeArea: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    @Binding var pulseAnimation: Bool
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing / 2) {
            // 状态指示器
            voiceStateIndicator

            // 实时识别文字气泡
            if !viewModel.recognizedText.isEmpty && viewModel.voiceState == .listening {
                HStack {
                    Spacer()
                    Text(viewModel.recognizedText)
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textPrimary)
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.vertical, layout.cardInnerPadding - 2)
                        .background(HealingColors.cardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        .shadow(color: Color.black.opacity(0.04), radius: 4, y: 2)
                }
                .padding(.horizontal, layout.horizontalPadding)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }

            // 分隔线
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(height: 1)
        }
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.6))
    }

    @ViewBuilder
    private var voiceStateIndicator: some View {
        switch viewModel.voiceState {
        case .idle:
            if viewModel.isMicrophoneMuted {
                HStack(spacing: 6) {
                    Image(systemName: "mic.slash.fill")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textTertiary)
                    Text("麦克风已关闭")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textSecondary)
                }
            } else {
                HStack(spacing: 6) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.forestMist.opacity(0.15))
                            .frame(width: layout.iconSmallSize - 12, height: layout.iconSmallSize - 12)

                        Image(systemName: "waveform")
                            .font(.system(size: layout.captionFontSize - 2))
                            .foregroundColor(HealingColors.forestMist)
                    }
                    Text("请说话...")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }

        case .listening:
            HStack(spacing: layout.cardSpacing / 2) {
                // 波形动画
                HStack(spacing: 3) {
                    ForEach(0..<4, id: \.self) { index in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(HealingColors.forestMist)
                            .frame(width: 3, height: 6 + CGFloat(viewModel.audioLevel) * 10 * CGFloat(index + 1) / 4)
                            .animation(.easeInOut(duration: 0.1), value: viewModel.audioLevel)
                    }
                }
                .frame(height: 20)

                Text("正在聆听...")
                    .font(.system(size: layout.captionFontSize, weight: .medium))
                    .foregroundColor(HealingColors.forestMist)
            }

        case .processing:
            HStack(spacing: 6) {
                ProgressView()
                    .tint(HealingColors.forestMist)
                    .scaleEffect(0.8)
                Text("正在思考...")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
            }

        case .aiSpeaking:
            HStack(spacing: 6) {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: 20, height: 20)

                    Image(systemName: "speaker.wave.2.fill")
                        .font(.system(size: layout.captionFontSize - 2))
                        .foregroundColor(HealingColors.forestMist)
                        .opacity(pulseAnimation ? 1.0 : 0.5)
                }
                Text("AI 播报中，说话可打断")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
            }

        case .error(let voiceError):
            HStack(spacing: 6) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.terracotta)
                Text(voiceError.localizedDescription)
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.terracotta)
            }
        }
    }
}

// MARK: - 治愈系底部控制栏
struct HealingVoiceBottomControlBar: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    let onCameraTap: () -> Void
    let onPhotoLibraryTap: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            // 4个圆形按钮
            HStack(spacing: layout.cardSpacing * 1.5) {
                // 麦克风按钮
                HealingVoiceCircleButton(
                    icon: viewModel.isMicrophoneMuted ? "mic.slash.fill" : "mic.fill",
                    label: viewModel.isMicrophoneMuted ? "已静音" : "麦克风",
                    isHighlighted: viewModel.voiceState == .listening && !viewModel.isMicrophoneMuted,
                    highlightColor: HealingColors.forestMist,
                    iconColor: viewModel.isMicrophoneMuted ? HealingColors.textTertiary : HealingColors.textSecondary,
                    layout: layout
                ) {
                    viewModel.toggleMicrophone()
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                }

                // 拍照按钮
                HealingVoiceCircleButton(
                    icon: "camera.fill",
                    label: "拍照",
                    isHighlighted: false,
                    highlightColor: .clear,
                    iconColor: HealingColors.dustyBlue,
                    layout: layout
                ) {
                    viewModel.requestVoiceCamera()
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    onCameraTap()
                }

                // 相册按钮
                HealingVoiceCircleButton(
                    icon: "photo.on.rectangle",
                    label: "相册",
                    isHighlighted: false,
                    highlightColor: .clear,
                    iconColor: HealingColors.warmSand,
                    layout: layout
                ) {
                    viewModel.requestVoicePhotoLibrary()
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    onPhotoLibraryTap()
                }

                // 退出按钮
                HealingVoiceCircleButton(
                    icon: "xmark",
                    label: "退出",
                    isHighlighted: false,
                    highlightColor: .clear,
                    iconColor: HealingColors.terracotta,
                    layout: layout
                ) {
                    viewModel.requestVoiceExit()
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                }
            }

            // 底部提示
            HStack(spacing: 4) {
                Image(systemName: "info.circle.fill")
                    .font(.system(size: layout.captionFontSize - 1))
                Text("内容由 AI 生成，仅供参考")
                    .font(.system(size: layout.captionFontSize - 1))
            }
            .foregroundColor(HealingColors.textTertiary)
            .padding(.bottom, layout.cardSpacing / 2)
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: -4)
    }
}

// MARK: - 治愈系圆形按钮组件
struct HealingVoiceCircleButton: View {
    let icon: String
    let label: String
    let isHighlighted: Bool
    let highlightColor: Color
    let iconColor: Color
    let layout: AdaptiveLayout
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: action) {
            VStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(isHighlighted ? highlightColor : HealingColors.cardBackground)
                        .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)
                        .shadow(
                            color: isHighlighted ? highlightColor.opacity(0.3) : Color.black.opacity(0.06),
                            radius: isHighlighted ? 10 : 6,
                            y: isHighlighted ? 4 : 3
                        )
                        .overlay(
                            Circle()
                                .stroke(isHighlighted ? Color.clear : highlightColor.opacity(0.2), lineWidth: 1)
                        )

                    Image(systemName: icon)
                        .font(.system(size: layout.captionFontSize + 3))
                        .foregroundColor(isHighlighted ? .white : iconColor)
                }
                .scaleEffect(isPressed ? 0.92 : 1.0)

                Text(label)
                    .font(.system(size: layout.captionFontSize - 1))
                    .foregroundColor(HealingColors.textSecondary)
            }
        }
        .buttonStyle(PlainButtonStyle())
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - 治愈系退出确认弹窗
struct HealingVoiceExitConfirmationDialog: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            Color.black.opacity(0.35)
                .ignoresSafeArea()
                .onTapGesture {
                    viewModel.cancelVoiceExit()
                }

            VStack(spacing: layout.cardSpacing) {
                // 图标
                ZStack {
                    Circle()
                        .fill(HealingColors.terracotta.opacity(0.1))
                        .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)

                    Image(systemName: "door.left.hand.open")
                        .font(.system(size: layout.bodyFontSize))
                        .foregroundColor(HealingColors.terracotta)
                }

                Text("是否退出语音模式?")
                    .font(.system(size: layout.bodyFontSize + 1, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Text("退出后将结束本次语音对话")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)

                HStack(spacing: layout.cardSpacing) {
                    Button("取消") {
                        viewModel.cancelVoiceExit()
                    }
                    .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                    .foregroundColor(HealingColors.textSecondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding)
                    .background(HealingColors.warmCream.opacity(0.8))
                    .clipShape(Capsule())

                    Button("确认退出") {
                        viewModel.exitVoiceMode()
                    }
                    .font(.system(size: layout.captionFontSize + 1, weight: .semibold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.terracotta, HealingColors.terracotta.opacity(0.8)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                    .shadow(color: HealingColors.terracotta.opacity(0.3), radius: 6, x: 0, y: 3)
                }
            }
            .padding(layout.cardInnerPadding * 2)
            .background(HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .shadow(color: Color.black.opacity(0.1), radius: 20, y: 10)
            .padding(.horizontal, layout.cardInnerPadding * 3)
        }
    }
}

// MARK: - Preview
#Preview("语音对话界面") {
    FullScreenVoiceModeView(
        viewModel: UnifiedChatViewModel()
    )
}
