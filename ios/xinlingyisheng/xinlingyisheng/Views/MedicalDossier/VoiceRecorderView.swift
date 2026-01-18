import SwiftUI

struct VoiceRecorderView: View {
    @StateObject private var viewModel = VoiceTranscriptionViewModel()
    @Binding var transcribedText: String
    @Binding var extractedSymptoms: [String]
    let onDismiss: () -> Void
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(24)) {
            // 标题
            HStack {
                Text("语音输入")
                    .font(.system(size: AdaptiveFont.title3, weight: .bold))
                    .foregroundColor(DXYColors.textPrimary)
                Spacer()
                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(DXYColors.textTertiary)
                }
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.top, ScaleFactor.padding(20))
            
            Spacer()
            
            // 录音可视化
            recordingVisualization
            
            // 时长显示
            Text(viewModel.formattedDuration)
                .font(.system(size: AdaptiveFont.largeTitle, weight: .light, design: .monospaced))
                .foregroundColor(viewModel.isRecording ? DXYColors.primaryPurple : DXYColors.textSecondary)
            
            // 状态提示
            statusText
            
            Spacer()
            
            // 控制按钮
            controlButtons
            
            // 转写结果
            if !viewModel.transcribedText.isEmpty {
                transcriptionResultView
            }
            
            // 错误提示
            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(.red)
                    .padding(.horizontal)
            }
        }
        .padding(.bottom, ScaleFactor.padding(30))
        .background(Color.white)
        .onChange(of: viewModel.transcribedText) { _, newValue in
            transcribedText = newValue
        }
        .onChange(of: viewModel.extractedSymptoms) { _, newValue in
            extractedSymptoms = newValue
        }
    }
    
    private var recordingVisualization: some View {
        ZStack {
            // 外圈动画
            Circle()
                .stroke(DXYColors.primaryPurple.opacity(0.2), lineWidth: 3)
                .frame(width: 160, height: 160)
            
            if viewModel.isRecording {
                Circle()
                    .stroke(DXYColors.primaryPurple.opacity(0.3), lineWidth: 3)
                    .frame(width: 160 + CGFloat(viewModel.audioLevel) * 40, height: 160 + CGFloat(viewModel.audioLevel) * 40)
                    .animation(.easeInOut(duration: 0.1), value: viewModel.audioLevel)
            }
            
            // 主按钮
            Circle()
                .fill(viewModel.isRecording ? DXYColors.primaryPurple : DXYColors.background)
                .frame(width: 120, height: 120)
                .overlay(
                    Group {
                        if viewModel.isTranscribing {
                            ProgressView()
                                .scaleEffect(1.5)
                                .tint(DXYColors.primaryPurple)
                        } else {
                            Image(systemName: viewModel.isRecording ? "waveform" : "mic.fill")
                                .font(.system(size: 40))
                                .foregroundColor(viewModel.isRecording ? .white : DXYColors.primaryPurple)
                        }
                    }
                )
                .shadow(color: DXYColors.primaryPurple.opacity(0.3), radius: viewModel.isRecording ? 20 : 0)
        }
    }
    
    private var statusText: some View {
        Group {
            if viewModel.isTranscribing {
                HStack(spacing: 8) {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("正在转写...")
                }
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textSecondary)
            } else if viewModel.isRecording {
                Text("正在录音，请描述您的症状")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.primaryPurple)
            } else if viewModel.transcribedText.isEmpty {
                Text("点击开始录音")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
            } else {
                Text("录音已转写完成")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.teal)
            }
        }
    }
    
    private var controlButtons: some View {
        HStack(spacing: ScaleFactor.spacing(40)) {
            if viewModel.isRecording {
                // 取消按钮
                Button(action: {
                    viewModel.cancelRecording()
                }) {
                    VStack(spacing: 6) {
                        Image(systemName: "xmark")
                            .font(.system(size: 24))
                            .foregroundColor(.white)
                            .frame(width: 56, height: 56)
                            .background(DXYColors.textTertiary)
                            .clipShape(Circle())
                        Text("取消")
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.textSecondary)
                    }
                }
                
                // 停止按钮
                Button(action: {
                    viewModel.stopRecording()
                }) {
                    VStack(spacing: 6) {
                        Image(systemName: "stop.fill")
                            .font(.system(size: 24))
                            .foregroundColor(.white)
                            .frame(width: 56, height: 56)
                            .background(Color.red)
                            .clipShape(Circle())
                        Text("完成")
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.textSecondary)
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
                    VStack(spacing: 6) {
                        Image(systemName: "mic.fill")
                            .font(.system(size: 28))
                            .foregroundColor(.white)
                            .frame(width: 72, height: 72)
                            .background(DXYColors.primaryPurple)
                            .clipShape(Circle())
                        Text(viewModel.transcribedText.isEmpty ? "开始录音" : "重新录音")
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.textSecondary)
                    }
                }
                .disabled(viewModel.isTranscribing)
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
    }
    
    private var transcriptionResultView: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            Divider()
            
            Text("转写结果")
                .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                .foregroundColor(DXYColors.textTertiary)
            
            Text(viewModel.transcribedText)
                .font(.system(size: AdaptiveFont.body))
                .foregroundColor(DXYColors.textPrimary)
                .padding(ScaleFactor.padding(12))
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(DXYColors.background)
                .clipShape(RoundedRectangle(cornerRadius: 8))
            
            if !viewModel.extractedSymptoms.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("识别到的症状")
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(DXYColors.textTertiary)
                    
                    FlowLayout(spacing: 6) {
                        ForEach(viewModel.extractedSymptoms, id: \.self) { symptom in
                            Text(symptom)
                                .font(.system(size: AdaptiveFont.footnote))
                                .foregroundColor(DXYColors.teal)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(DXYColors.teal.opacity(0.1))
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
                Text("使用此结果")
                    .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(14))
                    .background(DXYColors.primaryPurple)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.top, ScaleFactor.padding(16))
    }
}

struct VoiceInputButton: View {
    @State private var showRecorder = false
    @Binding var text: String
    @Binding var symptoms: [String]
    
    var body: some View {
        Button(action: { showRecorder = true }) {
            Image(systemName: "mic.fill")
                .font(.system(size: AdaptiveFont.title3))
                .foregroundColor(DXYColors.primaryPurple)
                .frame(width: 44, height: 44)
                .background(DXYColors.primaryPurple.opacity(0.1))
                .clipShape(Circle())
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
