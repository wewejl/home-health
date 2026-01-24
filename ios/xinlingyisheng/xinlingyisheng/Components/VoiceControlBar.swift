import SwiftUI

// MARK: - 专业级语音控制栏 - 自适应布局
struct VoiceControlBar: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    var onImageTap: (() -> Void)? = nil
    var onClose: (() -> Void)? = nil

    @State private var pulseAnimation = false

    var body: some View {
        VStack(spacing: 0) {
            // 实时识别文字显示区域
            if !viewModel.recognizedText.isEmpty {
                recognitionTextView
            }

            // 主控制区域
            VStack(spacing: ScaleFactor.spacing(20)) {
                // 状态提示
                statusIndicator

                // 中央麦克风按钮
                centerMicButton

                // 底部操作栏
                bottomActions
            }
            .padding(.vertical, ScaleFactor.padding(24))
            .padding(.horizontal, ScaleFactor.padding(20))
        }
        .background(
            LinearGradient(
                colors: [MedicalColors.bgPrimary, MedicalColors.bgSecondary],
                startPoint: .top,
                endPoint: .bottom
            )
        )
        .onAppear {
            withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) {
                pulseAnimation = true
            }
        }
    }

    // MARK: - 识别文字显示
    private var recognitionTextView: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 波形动画指示器
            WaveformIndicator()

            Text(viewModel.recognizedText)
                .font(.system(size: AdaptiveFont.body, weight: .medium))
                .foregroundColor(MedicalColors.textPrimary)
                .lineLimit(2)

            Spacer()
        }
        .padding(.horizontal, ScaleFactor.padding(20))
        .padding(.vertical, ScaleFactor.padding(16))
        .background(Color.white.opacity(0.9))
    }

    // MARK: - 状态指示器
    private var statusIndicator: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            if viewModel.voiceState == .aiSpeaking {
                Image(systemName: "speaker.wave.2.fill")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(MedicalColors.primaryBlue)
                Text("AI 正在回复")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(MedicalColors.textSecondary)
            } else if viewModel.voiceState == .listening {
                Circle()
                    .fill(MedicalColors.successGreen)
                    .frame(width: ScaleFactor.size(8), height: ScaleFactor.size(8))
                Text("正在聆听...")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(MedicalColors.successGreen)
            } else {
                Text("点击开始语音对话")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(MedicalColors.textSecondary)
            }
        }
    }

    // MARK: - 中央麦克风按钮
    private var centerMicButton: some View {
        Button(action: {
            if viewModel.voiceState == .aiSpeaking {
                // AI 正在说话 - 打断
                viewModel.interruptAISpeaking()
            } else if viewModel.voiceState == .idle {
                // 待机状态 - 开始录音
                viewModel.enterVoiceMode()
            } else if viewModel.voiceState == .listening {
                // 正在聆听 - 停止录音并发送
                viewModel.stopRecordingAndSend()
            }
        }) {
            ZStack {
                // 外圈脉冲动画（录音时显示）
                if viewModel.voiceState == .listening {
                    Circle()
                        .stroke(Color.green.opacity(0.3), lineWidth: ScaleFactor.size(2))
                        .frame(width: ScaleFactor.size(100), height: ScaleFactor.size(100))
                        .scaleEffect(pulseAnimation ? 1.2 : 1.0)

                    Circle()
                        .stroke(Color.green.opacity(0.2), lineWidth: ScaleFactor.size(2))
                        .frame(width: ScaleFactor.size(120), height: ScaleFactor.size(120))
                        .scaleEffect(pulseAnimation ? 1.3 : 1.0)
                }

                // 主按钮
                Circle()
                    .fill(
                        viewModel.voiceState == .listening
                            ? LinearGradient(colors: [Color(hex: "#22C55E"), Color(hex: "#16A34A")], startPoint: .top, endPoint: .bottom)
                            : viewModel.voiceState == .aiSpeaking
                                ? LinearGradient(colors: [MedicalColors.primaryBlue, MedicalColors.primaryBlueDark], startPoint: .top, endPoint: .bottom)
                                : LinearGradient(colors: [Color(hex: "#E5E7EB"), Color(hex: "#D1D5DB")], startPoint: .top, endPoint: .bottom)
                    )
                    .frame(width: ScaleFactor.size(80), height: ScaleFactor.size(80))
                    .shadow(color: viewModel.voiceState == .listening ? Color.green.opacity(0.4) : Color.black.opacity(0.1), radius: ScaleFactor.size(10), y: ScaleFactor.size(4))

                // 图标
                Image(systemName: {
                    switch viewModel.voiceState {
                    case .idle:
                        return "mic.fill"
                    case .listening:
                        return "checkmark.circle.fill"
                    case .aiSpeaking:
                        return "speaker.wave.2.fill"
                    case .processing:
                        return "hourglass"
                    case .error:
                        return "exclamationmark.triangle.fill"
                    }
                }())
                    .font(.system(size: AdaptiveFont.title1, weight: .medium))
                    .foregroundColor(.white)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - 底部操作栏
    private var bottomActions: some View {
        HStack(spacing: ScaleFactor.spacing(40)) {
            // 图片按钮
            Button(action: { onImageTap?() }) {
                VStack(spacing: ScaleFactor.spacing(6)) {
                    ZStack {
                        Circle()
                            .fill(Color.white)
                            .frame(width: ScaleFactor.size(48), height: ScaleFactor.size(48))
                            .shadow(color: Color.black.opacity(0.06), radius: ScaleFactor.size(4), y: ScaleFactor.size(2))

                        Image(systemName: "photo.on.rectangle")
                            .font(.system(size: AdaptiveFont.title3))
                            .foregroundColor(MedicalColors.textSecondary)
                    }
                    Text("图片")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(MedicalColors.textMuted)
                }
            }

            // 关闭按钮
            Button(action: {
                viewModel.exitVoiceMode()
                onClose?()
            }) {
                VStack(spacing: ScaleFactor.spacing(6)) {
                    ZStack {
                        Circle()
                            .fill(Color.white)
                            .frame(width: ScaleFactor.size(48), height: ScaleFactor.size(48))
                            .shadow(color: Color.black.opacity(0.06), radius: ScaleFactor.size(4), y: ScaleFactor.size(2))

                        Image(systemName: "keyboard")
                            .font(.system(size: AdaptiveFont.title3))
                            .foregroundColor(MedicalColors.textSecondary)
                    }
                    Text("键盘")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(MedicalColors.textMuted)
                }
            }
        }
    }
}

// MARK: - 波形动画指示器
struct WaveformIndicator: View {
    @State private var animating = false

    var body: some View {
        HStack(spacing: ScaleFactor.spacing(3)) {
            ForEach(0..<4) { index in
                RoundedRectangle(cornerRadius: ScaleFactor.size(2))
                    .fill(Color.green)
                    .frame(width: ScaleFactor.size(3), height: animating ? CGFloat.random(in: ScaleFactor.size(8)...ScaleFactor.size(20)) : ScaleFactor.size(8))
                    .animation(
                        .easeInOut(duration: 0.4)
                        .repeatForever()
                        .delay(Double(index) * 0.1),
                        value: animating
                    )
            }
        }
        .frame(width: ScaleFactor.size(20), height: ScaleFactor.size(20))
        .onAppear { animating = true }
    }
}

// MARK: - Preview
#Preview {
    VoiceControlBar(viewModel: UnifiedChatViewModel(), onImageTap: {})
}
