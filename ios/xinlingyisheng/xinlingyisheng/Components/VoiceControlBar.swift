import SwiftUI

// MARK: - 语音控制栏
struct VoiceControlBar: View {
    @ObservedObject var viewModel: UnifiedChatViewModel
    
    var body: some View {
        VStack(spacing: 12) {
            // 提示文字
            if viewModel.isAISpeaking {
                Text("点击或说话打断")
                    .font(.system(size: 14))
                    .foregroundColor(.gray)
            }
            
            // 控制按钮
            HStack(spacing: 32) {
                // 麦克风按钮
                VoiceButton(
                    icon: "mic.fill",
                    label: "麦克风",
                    isActive: viewModel.isRecording,
                    action: {}
                )
                
                // AI 功能按钮
                VoiceButton(
                    icon: "sparkles",
                    label: "AI生成",
                    isActive: false,
                    action: {}
                )
                
                // 图片按钮
                VoiceButton(
                    icon: "photo",
                    label: "图片",
                    isActive: false,
                    action: {}
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
            Text("内容由 AI 生成")
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
    VoiceControlBar(viewModel: UnifiedChatViewModel())
}
