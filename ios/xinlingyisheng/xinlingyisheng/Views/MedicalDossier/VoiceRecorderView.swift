import SwiftUI

// MARK: - 语音录制视图（治愈系风格）
struct VoiceRecorderView: View {
    @StateObject private var viewModel = VoiceTranscriptionViewModel()
    @Binding var transcribedText: String
    @Binding var extractedSymptoms: [String]
    let onDismiss: () -> Void

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            VStack(spacing: layout.cardSpacing + 4) {
                // 标题
                HStack {
                    Text("语音输入")
                        .font(.system(size: layout.bodyFontSize + 1, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)
                    Spacer()
                    Button(action: onDismiss) {
                        ZStack {
                            Circle()
                                .fill(HealingColors.textTertiary.opacity(0.15))
                                .frame(width: 28, height: 28)

                            Image(systemName: "xmark")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(HealingColors.textTertiary)
                        }
                    }
                }
                .padding(.horizontal, layout.horizontalPadding)
                .padding(.top, layout.cardInnerPadding)

                Spacer()

                // 录音可视化
                recordingVisualization(layout: layout)

                // 时长显示
                Text(viewModel.formattedDuration)
                    .font(.system(size: layout.titleFontSize + 4, weight: .light, design: .monospaced))
                    .foregroundColor(viewModel.isRecording ? HealingColors.forestMist : HealingColors.textSecondary)

                // 状态提示
                statusText(layout: layout)

                Spacer()

                // 控制按钮
                controlButtons(layout: layout)

                // 转写结果
                if !viewModel.transcribedText.isEmpty {
                    transcriptionResultView(layout: layout)
                }

                // 错误提示
                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.terracotta)
                        .padding(.horizontal)
                }
            }
            .padding(.bottom, layout.cardInnerPadding * 2)
            .background(HealingColors.cardBackground)
            .onChange(of: viewModel.transcribedText) { _, newValue in
                transcribedText = newValue
            }
            .onChange(of: viewModel.extractedSymptoms) { _, newValue in
                extractedSymptoms = newValue
            }
        }
    }

    private func recordingVisualization(layout: AdaptiveLayout) -> some View {
        ZStack {
            // 外圈动画
            Circle()
                .stroke(HealingColors.forestMist.opacity(0.2), lineWidth: 3)
                .frame(width: 160, height: 160)

            if viewModel.isRecording {
                Circle()
                    .stroke(HealingColors.forestMist.opacity(0.3), lineWidth: 3)
                    .frame(width: 160 + CGFloat(viewModel.audioLevel) * 40, height: 160 + CGFloat(viewModel.audioLevel) * 40)
                    .animation(.easeInOut(duration: 0.1), value: viewModel.audioLevel)
            }

            // 主按钮
            Circle()
                .fill(viewModel.isRecording ? HealingColors.forestMist : HealingColors.warmCream.opacity(0.5))
                .frame(width: 120, height: 120)
                .overlay(
                    Group {
                        if viewModel.isTranscribing {
                            ProgressView()
                                .scaleEffect(1.5)
                                .tint(HealingColors.forestMist)
                        } else {
                            Image(systemName: viewModel.isRecording ? "waveform" : "mic.fill")
                                .font(.system(size: 40))
                                .foregroundColor(viewModel.isRecording ? .white : HealingColors.forestMist)
                        }
                    }
                )
                .shadow(color: HealingColors.forestMist.opacity(0.3), radius: viewModel.isRecording ? 20 : 5)
        }
    }

    @ViewBuilder
    private func statusText(layout: AdaptiveLayout) -> some View {
        Group {
            if viewModel.isTranscribing {
                HStack(spacing: layout.cardSpacing / 2) {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("正在转写...")
                }
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
            } else if viewModel.isRecording {
                Text("正在录音，请描述您的症状")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.forestMist)
            } else if viewModel.transcribedText.isEmpty {
                Text("点击开始录音")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textTertiary)
            } else {
                Text("录音已转写完成")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.forestMist)
            }
        }
    }

    private func controlButtons(layout: AdaptiveLayout) -> some View {
        HStack(spacing: layout.cardSpacing + 8) {
            if viewModel.isRecording {
                // 取消按钮
                Button(action: {
                    viewModel.cancelRecording()
                }) {
                    VStack(spacing: 4) {
                        Image(systemName: "xmark")
                            .font(.system(size: 20))
                            .foregroundColor(.white)
                            .frame(width: 50, height: 50)
                            .background(HealingColors.textTertiary)
                            .clipShape(Circle())
                        Text("取消")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                }

                // 停止按钮
                Button(action: {
                    viewModel.stopRecording()
                }) {
                    VStack(spacing: 4) {
                        Image(systemName: "stop.fill")
                            .font(.system(size: 20))
                            .foregroundColor(.white)
                            .frame(width: 50, height: 50)
                            .background(HealingColors.terracotta)
                            .clipShape(Circle())
                        Text("完成")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                }
            } else {
                // 开始录音按钮
                Button(action: {
                    if !viewModel.transcribedText.isEmpty {
                        viewModel.reset()
                    }
                    viewModel.startRecording()
                }) {
                    VStack(spacing: 4) {
                        Image(systemName: "mic.fill")
                            .font(.system(size: 24))
                            .foregroundColor(.white)
                            .frame(width: 64, height: 64)
                            .background(
                                LinearGradient(
                                    colors: [HealingColors.forestMist, HealingColors.deepSage],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .clipShape(Circle())
                            .shadow(color: HealingColors.forestMist.opacity(0.4), radius: 8, y: 4)
                        Text(viewModel.transcribedText.isEmpty ? "开始录音" : "重新录音")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                }
                .disabled(viewModel.isTranscribing)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
    }

    private func transcriptionResultView(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(height: 1)

            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.forestMist)
                Text("转写结果")
                    .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                    .foregroundColor(HealingColors.textSecondary)
            }

            Text(viewModel.transcribedText)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .padding(layout.cardInnerPadding)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(HealingColors.warmCream.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

            if !viewModel.extractedSymptoms.isEmpty {
                VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                    HStack(spacing: 4) {
                        Image(systemName: "list.bullet")
                            .font(.system(size: layout.captionFontSize - 1))
                            .foregroundColor(HealingColors.forestMist)
                        Text("识别到的症状")
                            .font(.system(size: layout.captionFontSize, weight: .medium))
                            .foregroundColor(HealingColors.textSecondary)
                    }

                    FlowLayout(spacing: 6) {
                        ForEach(viewModel.extractedSymptoms, id: \.self) { symptom in
                            Text(symptom)
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.dustyBlue)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(HealingColors.dustyBlue.opacity(0.15))
                                .clipShape(Capsule())
                        }
                    }
                }
            }

            // 使用结果按钮
            Button(action: {
                transcribedText = viewModel.transcribedText
                extractedSymptoms = viewModel.extractedSymptoms
                onDismiss()
            }) {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "checkmark")
                        .font(.system(size: layout.captionFontSize + 1))
                    Text("使用此结果")
                        .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
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
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 3)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardSpacing)
    }
}

// MARK: - 语音输入按钮
struct VoiceInputButton: View {
    @State private var showRecorder = false
    @Binding var text: String
    @Binding var symptoms: [String]

    var body: some View {
        Button(action: { showRecorder = true }) {
            ZStack {
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.15))
                    .frame(width: 44, height: 44)

                Image(systemName: "mic.fill")
                    .font(.system(size: 18))
                    .foregroundColor(HealingColors.forestMist)
            }
        }
        .sheet(isPresented: $showRecorder) {
            VoiceRecorderView(
                transcribedText: $text,
                extractedSymptoms: $symptoms,
                onDismiss: { showRecorder = false }
            )
            .presentationDetents([.medium, .large])
        }
    }
}

#Preview {
    @Previewable @State var text = ""
    @Previewable @State var symptoms: [String] = []

    return VoiceRecorderView(
        transcribedText: $text,
        extractedSymptoms: $symptoms,
        onDismiss: {}
    )
}
