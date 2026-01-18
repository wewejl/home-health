import SwiftUI

// MARK: - 对话完成提示卡片
/// 显示对话已完成并提示用户查看病历资料夹
struct ConversationCompletedCard: View {
    let eventId: String?
    let isNewEvent: Bool
    let onViewDossier: () -> Void
    let onContinueConversation: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            // 顶部图标和标题
            HStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(.green)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("对话已结束")
                        .font(.headline)
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Text(isNewEvent ? "已自动生成病历资料夹" : "已更新病历资料夹")
                        .font(.subheadline)
                        .foregroundColor(DXYColors.textSecondary)
                }
                
                Spacer()
            }
            
            // 操作按钮
            HStack(spacing: 12) {
                Button(action: onViewDossier) {
                    HStack(spacing: 6) {
                        Image(systemName: "doc.text.fill")
                            .font(.system(size: 14))
                        Text("查看病历")
                            .font(.system(size: 15, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(DXYColors.primaryPurple)
                    .cornerRadius(10)
                }
                
                Button(action: onContinueConversation) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 14))
                        Text("继续对话")
                            .font(.system(size: 15, weight: .medium))
                    }
                    .foregroundColor(DXYColors.primaryPurple)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(DXYColors.primaryPurple.opacity(0.1))
                    .cornerRadius(10)
                }
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.blue.opacity(0.05))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.blue.opacity(0.2), lineWidth: 1)
                )
        )
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }
}

// MARK: - Preview
struct ConversationCompletedCard_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            ConversationCompletedCard(
                eventId: "123",
                isNewEvent: true,
                onViewDossier: {},
                onContinueConversation: {}
            )
            
            ConversationCompletedCard(
                eventId: "123",
                isNewEvent: false,
                onViewDossier: {},
                onContinueConversation: {}
            )
        }
        .padding()
        .background(DXYColors.background)
    }
}
