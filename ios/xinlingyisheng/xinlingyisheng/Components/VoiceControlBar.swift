import SwiftUI

// MARK: - 专业级语音控制栏
struct VoiceControlBar: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    var onImageTap: (() -> Void)? = nil
    var onClose: (() -> Void)? = nil
    
    @State private var pulseAnimation = false
    
    var body: some View {
        VStack(spacing: 0) {
            // 实时识别文字显示区域
            if !viewModel.currentRecognition.isEmpty {
                recognitionTextView
            }
            
            // 主控制区域
            VStack(spacing: 20) {
                // 状态提示
                statusIndicator
                
                // 中央麦克风按钮
                centerMicButton
                
                // 底部操作栏
                bottomActions
            }
            .padding(.vertical, 24)
            .padding(.horizontal, 20)
        }
        .background(
            LinearGradient(
                colors: [Color(hex: "#F0FDF4"), Color(hex: "#DCFCE7")],
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
        HStack(spacing: 12) {
            // 波形动画指示器
            WaveformIndicator()
            
            Text(viewModel.currentRecognition)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(MedicalColors.textPrimary)
                .lineLimit(2)
            
            Spacer()
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.white.opacity(0.9))
    }
    
    // MARK: - 状态指示器
    private var statusIndicator: some View {
        HStack(spacing: 8) {
            if viewModel.isAISpeaking {
                Image(systemName: "speaker.wave.2.fill")
                    .font(.system(size: 14))
                    .foregroundColor(MedicalColors.primaryBlue)
                Text("AI 正在回复")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(MedicalColors.textSecondary)
            } else if viewModel.isRecording {
                Circle()
                    .fill(Color.green)
                    .frame(width: 8, height: 8)
                Text("正在聆听...")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(Color(hex: "#16A34A"))
            } else {
                Text("点击开始语音对话")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(MedicalColors.textSecondary)
            }
        }
    }
    
    // MARK: - 中央麦克风按钮
    private var centerMicButton: some View {
        Button(action: {
            if viewModel.isAISpeaking {
                viewModel.interruptAISpeech()
            }
        }) {
            ZStack {
                // 外圈脉冲动画（录音时显示）
                if viewModel.isRecording {
                    Circle()
                        .stroke(Color.green.opacity(0.3), lineWidth: 2)
                        .frame(width: 100, height: 100)
                        .scaleEffect(pulseAnimation ? 1.2 : 1.0)
                    
                    Circle()
                        .stroke(Color.green.opacity(0.2), lineWidth: 2)
                        .frame(width: 120, height: 120)
                        .scaleEffect(pulseAnimation ? 1.3 : 1.0)
                }
                
                // 主按钮
                Circle()
                    .fill(
                        viewModel.isRecording
                            ? LinearGradient(colors: [Color(hex: "#22C55E"), Color(hex: "#16A34A")], startPoint: .top, endPoint: .bottom)
                            : viewModel.isAISpeaking
                                ? LinearGradient(colors: [MedicalColors.primaryBlue, MedicalColors.primaryBlueDark], startPoint: .top, endPoint: .bottom)
                                : LinearGradient(colors: [Color(hex: "#E5E7EB"), Color(hex: "#D1D5DB")], startPoint: .top, endPoint: .bottom)
                    )
                    .frame(width: 80, height: 80)
                    .shadow(color: viewModel.isRecording ? Color.green.opacity(0.4) : Color.black.opacity(0.1), radius: 10, y: 4)
                
                // 图标
                Image(systemName: viewModel.isAISpeaking ? "speaker.wave.2.fill" : "mic.fill")
                    .font(.system(size: 32, weight: .medium))
                    .foregroundColor(.white)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    // MARK: - 底部操作栏
    private var bottomActions: some View {
        HStack(spacing: 40) {
            // 图片按钮
            Button(action: { onImageTap?() }) {
                VStack(spacing: 6) {
                    ZStack {
                        Circle()
                            .fill(Color.white)
                            .frame(width: 48, height: 48)
                            .shadow(color: Color.black.opacity(0.06), radius: 4, y: 2)
                        
                        Image(systemName: "photo.on.rectangle")
                            .font(.system(size: 20))
                            .foregroundColor(MedicalColors.textSecondary)
                    }
                    Text("图片")
                        .font(.system(size: 12))
                        .foregroundColor(MedicalColors.textMuted)
                }
            }
            
            // 关闭按钮
            Button(action: {
                viewModel.toggleVoiceMode()
                onClose?()
            }) {
                VStack(spacing: 6) {
                    ZStack {
                        Circle()
                            .fill(Color.white)
                            .frame(width: 48, height: 48)
                            .shadow(color: Color.black.opacity(0.06), radius: 4, y: 2)
                        
                        Image(systemName: "keyboard")
                            .font(.system(size: 20))
                            .foregroundColor(MedicalColors.textSecondary)
                    }
                    Text("键盘")
                        .font(.system(size: 12))
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
        HStack(spacing: 3) {
            ForEach(0..<4) { index in
                RoundedRectangle(cornerRadius: 2)
                    .fill(Color.green)
                    .frame(width: 3, height: animating ? CGFloat.random(in: 8...20) : 8)
                    .animation(
                        .easeInOut(duration: 0.4)
                        .repeatForever()
                        .delay(Double(index) * 0.1),
                        value: animating
                    )
            }
        }
        .frame(width: 20, height: 20)
        .onAppear { animating = true }
    }
}

// MARK: - Preview
#Preview {
    VoiceControlBar(viewModel: UnifiedChatViewModel(), onImageTap: {})
}
