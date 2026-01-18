import SwiftUI

// MARK: - 语音控制栏
struct VoiceControlBar: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    var onImageTap: (() -> Void)? = nil
    
    var body: some View {
        VStack(spacing: 12) {
            // 提示文字
            if viewModel.isAISpeaking {
                HStack {
                    Image(systemName: "speaker.wave.2.fill")
                        .foregroundColor(.blue)
                    Text("AI 正在播报，点击打断")
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                }
                .onTapGesture {
                    viewModel.interruptAISpeech()
                }
            } else if viewModel.isRecording {
                HStack {
                    Image(systemName: "waveform")
                        .foregroundColor(.green)
                    Text("正在聆听...")
                        .font(.system(size: 14))
                        .foregroundColor(.green)
                }
            } else {
                Text("点击麦克风开始说话")
                    .font(.system(size: 14))
                    .foregroundColor(.gray)
            }
            
            // 控制按钮
            HStack(spacing: 32) {
                // 麦克风按钮 - 点击打断 AI 或显示状态
                VoiceButton(
                    icon: viewModel.isRecording ? "mic.fill" : "mic",
                    label: viewModel.isRecording ? "聆听中" : "麦克风",
                    isActive: viewModel.isRecording,
                    action: {
                        // 如果 AI 正在播报，打断它
                        if viewModel.isAISpeaking {
                            viewModel.interruptAISpeech()
                        }
                        // 麦克风在语音模式下自动开启，此按钮仅显示状态
                    }
                )
                
                // 图片按钮
                VoiceButton(
                    icon: "photo",
                    label: "图片",
                    isActive: false,
                    action: {
                        onImageTap?()
                    }
                )
                
                // 关闭按钮
                VoiceButton(
                    icon: "xmark",
                    label: "关闭",
                    isActive: false,
                    isDestructive: true,
                    action: {
                        viewModel.toggleVoiceMode()
                    }
                )
            }
            
            // 底部提示
            Text("内容由 AI 生成，仅供参考")
                .font(.system(size: 12))
                .foregroundColor(.gray.opacity(0.6))
        }
        .padding(.vertical, 16)
        .padding(.horizontal, 20)
        .background(Color(hex: "#E8F5E9"))
    }
}

// MARK: - 语音按钮
struct VoiceButton: View {
    let icon: String
    let label: String
    var isActive: Bool = false
    var isDestructive: Bool = false
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                ZStack {
                    Circle()
                        .fill(backgroundColor)
                        .frame(width: 48, height: 48)
                    
                    Image(systemName: icon)
                        .font(.system(size: 20))
                        .foregroundColor(iconColor)
                }
                
                Text(label)
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
            }
        }
    }
    
    private var backgroundColor: Color {
        if isDestructive { return Color.red.opacity(0.1) }
        if isActive { return Color.green.opacity(0.2) }
        return Color.white
    }
    
    private var iconColor: Color {
        if isDestructive { return .red }
        if isActive { return .green }
        return .gray
    }
}

// MARK: - Preview
#Preview {
    VoiceControlBar(viewModel: UnifiedChatViewModel(), onImageTap: {})
}
