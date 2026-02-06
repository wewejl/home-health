//
//  WeChatStyleInputBar.swift
//  灵犀医生
//
//  治愈系风格的输入栏
//  - 左侧切换按钮（🎤/⌨️）
//  - 中间输入框/按住说话按钮
//  - 右侧静音开关/发送按钮
//  - 按住说话时显示美观的覆盖层
//  - 覆盖层覆盖整个屏幕，不仅仅是输入栏区域
//  - 符合治愈系设计风格
//  - inputMode 现在由 ViewModel 管理，确保在整个会话中保持状态
//

import SwiftUI

// MARK: - 治愈系风格输入栏
struct WeChatStyleInputBar: View {
    @Binding var messageText: String
    @ObservedObject var viewModel: UnifiedChatViewModel
    let isSending: Bool
    let isDisabled: Bool
    let onSend: () -> Void
    let onMenuTap: () -> Void
    let onImagePickerTap: () -> Void
    let layout: AdaptiveLayout

    // 按住说话状态 - 通过绑定与父视图共享
    @Binding var isPressing: Bool
    @Binding var isCanceling: Bool

    // 按压偏移（内部状态）
    @State private var pressOffset: CGFloat = 0

    // 覆盖层显示状态 - 通过绑定传递给父视图
    @Binding var showOverlay: Bool

    // inputMode 现在从 ViewModel 读取，由 ViewModel 管理
    // 这样可以确保状态在整个会话中保持不变
    private var inputMode: InputMode {
        viewModel.inputMode
    }

    var body: some View {
        mainInputBar
    }

    // MARK: - 主输入栏
    private var mainInputBar: some View {
        HStack(alignment: .bottom, spacing: layout.cardSpacing / 2) {
            // 左侧：切换按钮 或 照片按钮
            leftButton

            // 中间：输入框 或 按住说话按钮
            if inputMode == .text {
                textInputField
            } else {
                pressAndHoldButton
            }
        }
    }

    // MARK: - 左侧按钮
    @ViewBuilder
    private var leftButton: some View {
        if inputMode == .text {
            // 文字模式：显示照片按钮
            Button(action: onMenuTap) {
                ZStack {
                    Circle()
                        .fill(isDisabled ? HealingColors.textTertiary.opacity(0.2) : HealingColors.forestMist.opacity(0.12))
                        .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                        .overlay(
                            Circle()
                                .stroke(
                                    isDisabled ? Color.clear : HealingColors.forestMist.opacity(0.15),
                                    lineWidth: 1.5
                                )
                        )

                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(isDisabled ? HealingColors.textTertiary : HealingColors.forestMist)
                }
            }
            .disabled(isDisabled)
        } else {
            // 语音模式：显示切换回文字按钮
            Button(action: {
                triggerHapticFeedback(.light)
                withAnimation(.spring(response: 0.4)) {
                    viewModel.inputMode = .text
                }
            }) {
                ZStack {
                    Circle()
                        .fill(HealingColors.dustyBlue.opacity(0.12))
                        .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                        .overlay(
                            Circle()
                                .stroke(HealingColors.dustyBlue.opacity(0.2), lineWidth: 1.5)
                        )

                    Image(systemName: "keyboard")
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(HealingColors.dustyBlue)
                }
            }
        }
    }

    // MARK: - 文字输入框
    private var textInputField: some View {
        HStack(alignment: .bottom, spacing: 0) {
            ZStack(alignment: .leading) {
                if messageText.isEmpty {
                    Text("输入消息...")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(HealingColors.textTertiary)
                        .padding(.leading, ScaleFactor.padding(16))
                }

                TextField("", text: $messageText, axis: .vertical)
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(HealingColors.textPrimary)
                    .lineLimit(1...5)
                    .padding(.horizontal, ScaleFactor.padding(12))
                    .padding(.vertical, ScaleFactor.padding(8))
                    .disabled(isDisabled)
            }

            // 右侧：发送按钮或语音按钮
            if messageText.isEmpty {
                // 显示语音按钮
                Button(action: {
                    triggerHapticFeedback(.light)
                    withAnimation(.spring(response: 0.4)) {
                        viewModel.inputMode = .voice
                    }
                }) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.dustyBlue.opacity(0.12))
                            .frame(width: ScaleFactor.size(36), height: ScaleFactor.size(36))
                            .overlay(
                                Circle()
                                    .stroke(HealingColors.dustyBlue.opacity(0.2), lineWidth: 1.5)
                            )

                        Image(systemName: "mic.fill")
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(HealingColors.dustyBlue)
                    }
                }
                .disabled(isDisabled)
            } else {
                // 显示发送按钮
                Button(action: onSend) {
                    ZStack {
                        if isSending || isDisabled {
                            Circle()
                                .fill(HealingColors.textTertiary.opacity(0.3))
                                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                        } else {
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [
                                            HealingColors.forestMist,
                                            HealingColors.deepSage
                                        ],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                                .shadow(
                                    color: HealingColors.forestMist.opacity(0.3),
                                    radius: 6,
                                    x: 0,
                                    y: 3
                                )
                        }

                        if isSending {
                            ProgressView()
                                .tint(.white)
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "arrow.up")
                                .font(.system(size: AdaptiveFont.caption2, weight: .semibold))
                                .foregroundColor(.white)
                        }
                    }
                    .padding(.trailing, ScaleFactor.padding(8))
                    .padding(.bottom, ScaleFactor.padding(6))
                }
            }
        }
        .background(
            RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
                .fill(HealingColors.warmCream)
                .overlay(
                    RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
                        .stroke(HealingColors.softSage.opacity(0.5), lineWidth: 1)
                )
                .shadow(
                    color: HealingColors.softSage.opacity(0.1),
                    radius: 8,
                    x: 0,
                    y: 2
                )
        )
    }

    // MARK: - 按住说话按钮（语音模式）
    private var pressAndHoldButton: some View {
        Button(action: {}) {
            Text("按住 说话")
                .font(.system(size: AdaptiveFont.caption, weight: .medium))
                .foregroundColor(isDisabled ? HealingColors.textTertiary : HealingColors.forestMist)
                .frame(maxWidth: .infinity)
                .frame(height: ScaleFactor.size(44))
                .background(
                    RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [
                                    HealingColors.forestMist.opacity(0.8),
                                    HealingColors.deepSage.opacity(0.6)
                                ],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
                                .stroke(HealingColors.forestMist.opacity(0.2), lineWidth: 1)
                        )
                )
        }
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { value in
                    if !isPressing {
                        // 开始按住
                        withAnimation(.spring(response: 0.3)) {
                            isPressing = true
                            pressOffset = 0
                            isCanceling = false
                        }

                        triggerHapticFeedback(.medium)

                        // 通知父视图显示覆盖层
                        DispatchQueue.main.async {
                            showOverlay = true
                        }

                        // 开始录音
                        Task {
                            await viewModel.startPressAndHoldRecording()
                        }
                    }

                    // 计算上滑偏移
                    let verticalOffset = value.translation.height
                    let cancelThreshold: CGFloat = -60

                    withAnimation(.spring(response: 0.3)) {
                        if verticalOffset < cancelThreshold {
                            pressOffset = verticalOffset
                            isCanceling = true
                        } else {
                            pressOffset = 0
                            isCanceling = false
                        }
                    }
                }
                .onEnded { value in
                    let cancelThreshold: CGFloat = -60

                    if isCanceling || value.translation.height < cancelThreshold {
                        // 取消
                        triggerHapticFeedback(.light)
                        Task {
                            await viewModel.cancelPressAndHoldRecording()
                        }
                    } else {
                        // 发送
                        triggerHapticFeedback(.medium)
                        Task {
                            await viewModel.stopPressAndHoldRecording()
                        }
                    }

                    withAnimation(.spring(response: 0.4)) {
                        isPressing = false
                        pressOffset = 0
                        isCanceling = false
                    }

                    // 通知父视图隐藏覆盖层
                    DispatchQueue.main.async {
                        showOverlay = false
                    }
                }
        )
        .disabled(isDisabled)
    }

    // MARK: - 触觉反馈
    private func triggerHapticFeedback(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.impactOccurred()
    }
}

// MARK: - 按住说话覆盖层（底部卡片式设计）
// 这是独立的覆盖层组件，应该在 ModernConsultationView 中使用
//
// 底部卡片设计特点：
// 1. 不覆盖聊天内容，用户仍能看到对话历史
// 2. 从底部滑入，动画流畅
// 3. 半透明背景，视觉效果柔和
// 4. 保留上滑取消手势
// 5. 实时显示识别文字
struct PressAndHoldOverlayView: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    let layout: AdaptiveLayout
    @Binding var isPresented: Bool

    // 状态 - 从按钮传递
    let isPressing: Bool
    let isCanceling: Bool

    // 动画状态（内部管理）
    @State private var pulseScale: CGFloat = 1.0

    var body: some View {
        VStack {
            Spacer()

            // 底部卡片容器
            bottomCardView
                .padding(.horizontal, layout.horizontalPadding)
                .padding(.bottom, layout.cardSpacing)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
        .onAppear {
            pulseScale = 1.0
        }
    }

    // MARK: - 底部卡片
    private var bottomCardView: some View {
        VStack(spacing: layout.cardSpacing) {
            // 顶部指示条（类似 sheet）
            RoundedRectangle(cornerRadius: 3)
                .fill(HealingColors.textTertiary.opacity(0.3))
                .frame(width: 36, height: 5)
                .padding(.top, layout.cardSpacing / 2)

            // 主内容区
            HStack(spacing: layout.cardSpacing) {
                // 左侧：录音状态
                VStack(spacing: layout.cardSpacing / 2) {
                    // 状态图标
                    if isCanceling {
                        cancelIconView
                    } else {
                        recordingIconView
                    }

                    // 提示文字
                    instructionText
                }
                .frame(maxWidth: .infinity)

                // 右侧：识别文字区域
                if !viewModel.recognizedText.isEmpty {
                    recognitionTextView
                } else {
                    // 占位提示
                    placeholderTextView
                }
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.bottom, layout.cardInnerPadding)
        }
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(
                            isCanceling ? HealingColors.terracotta.opacity(0.3) : HealingColors.forestMist.opacity(0.2),
                            lineWidth: 1
                        )
                )
                .shadow(color: Color.black.opacity(0.1), radius: 20, y: 10)
        )
    }

    // MARK: - 录音图标
    private var recordingIconView: some View {
        ZStack {
            // 外圈波纹
            Circle()
                .stroke(
                    HealingColors.forestMist.opacity(0.3),
                    lineWidth: 2
                )
                .frame(width: 64, height: 64)
                .scaleEffect(pulseScale)

            // 主圆圈
            Circle()
                .fill(
                    LinearGradient(
                        colors: [
                            HealingColors.forestMist,
                            HealingColors.deepSage
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 56, height: 56)
                .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 8, y: 4)

            // 波形图标
            Image(systemName: "waveform")
                .font(.system(size: 20))
                .foregroundColor(.white)
        }
        .animation(
            .easeInOut(duration: 1.0)
                .repeatForever(autoreverses: true),
            value: pulseScale
        )
    }

    // MARK: - 取消图标
    private var cancelIconView: some View {
        ZStack {
            // 主圆圈
            Circle()
                .fill(HealingColors.terracotta)
                .frame(width: 56, height: 56)
                .shadow(color: HealingColors.terracotta.opacity(0.4), radius: 10, y: 4)

            Image(systemName: "xmark")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(.white)
        }
    }

    // MARK: - 提示文字
    private var instructionText: some View {
        VStack(spacing: 4) {
            Text(isCanceling ? "松开取消" : "松开发送")
                .font(.system(size: AdaptiveFont.caption, weight: .semibold))
                .foregroundColor(isCanceling ? HealingColors.terracotta : HealingColors.forestMist)

            HStack(spacing: 4) {
                Image(systemName: "chevron.up")
                    .font(.system(size: AdaptiveFont.caption2))
                Text(isCanceling ? "下滑继续录音" : "上滑可取消")
                    .font(.system(size: AdaptiveFont.caption2))
            }
            .foregroundColor(HealingColors.textSecondary)
        }
    }

    // MARK: - 识别文字区域
    private var recognitionTextView: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 4) {
                Circle()
                    .fill(HealingColors.forestMist)
                    .frame(width: 6, height: 6)
                    .opacity(pulseScale * 0.5 + 0.5)

                Text("正在识别")
                    .font(.system(size: AdaptiveFont.caption2))
                    .foregroundColor(HealingColors.forestMist)
            }

            Text(viewModel.recognizedText)
                .font(.system(size: AdaptiveFont.caption))
                .foregroundColor(HealingColors.textPrimary)
                .lineLimit(3)
                .multilineTextAlignment(.leading)
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(HealingColors.warmCream.opacity(0.6))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(HealingColors.softSage.opacity(0.3), lineWidth: 1)
                        )
                )
        }
        .frame(maxWidth: .infinity)
        .animation(
            .easeInOut(duration: 1.0)
                .repeatForever(autoreverses: true),
            value: pulseScale
        )
    }

    // MARK: - 占位提示
    private var placeholderTextView: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("正在录音...")
                .font(.system(size: AdaptiveFont.caption2))
                .foregroundColor(HealingColors.textSecondary)

            Text("请说话")
                .font(.system(size: AdaptiveFont.caption))
                .foregroundColor(HealingColors.textTertiary)
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(HealingColors.warmCream.opacity(0.4))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
                        )
                )
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Preview
#Preview("治愈系输入栏") {
    ZStack {
        // 背景
        HealingColors.background.ignoresSafeArea()

        VStack {
            Spacer()

            WeChatStyleInputBar(
                messageText: .constant(""),
                viewModel: {
                    let vm = UnifiedChatViewModel()
                    vm.recognizedText = "我头痛已经三天了，还有点发热"
                    return vm
                }(),
                isSending: false,
                isDisabled: false,
                onSend: {},
                onMenuTap: {},
                onImagePickerTap: {},
                layout: AdaptiveLayout(screenWidth: 393),
                isPressing: .constant(false),
                isCanceling: .constant(false),
                showOverlay: .constant(false)
            )

            Spacer()
                .frame(height: 100)
        }
    }
}
