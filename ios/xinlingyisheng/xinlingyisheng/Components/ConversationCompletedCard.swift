import SwiftUI

// MARK: - 对话完成提示卡片
/// 显示对话已完成并提示用户查看病历资料夹
struct ConversationCompletedCard: View {
    let eventId: String?
    let isNewEvent: Bool
    let onViewDossier: () -> Void
    let onContinueConversation: () -> Void

    var body: some View {
        VStack(spacing: ScaleFactor.spacing(16)) {
            // 顶部图标和标题
            HStack(spacing: ScaleFactor.spacing(12)) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(HealingColorTheme.successGreen)

                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    Text("对话已结束")
                        .font(.headline)
                        .foregroundColor(DossierColors.textPrimary)

                    Text(isNewEvent ? "已自动生成病历资料夹" : "已更新病历资料夹")
                        .font(.subheadline)
                        .foregroundColor(DossierColors.textSecondary)
                }

                Spacer()
            }

            // 操作按钮
            HStack(spacing: ScaleFactor.spacing(12)) {
                Button(action: onViewDossier) {
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Image(systemName: "doc.text.fill")
                            .font(.system(size: AdaptiveFont.subheadline))
                        Text("查看病历")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DossierColors.primaryPurple)
                    .cornerRadius(ScaleFactor.size(10))
                }

                Button(action: onContinueConversation) {
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: AdaptiveFont.subheadline))
                        Text("继续对话")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                    }
                    .foregroundColor(DossierColors.primaryPurple)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DossierColors.primaryPurple.opacity(0.1))
                    .cornerRadius(ScaleFactor.size(10))
                }
            }
        }
        .padding(ScaleFactor.padding(16))
        .background(
            RoundedRectangle(cornerRadius: ScaleFactor.size(12))
                .fill(DossierColors.blue.opacity(0.05))
                .overlay(
                    RoundedRectangle(cornerRadius: ScaleFactor.size(12))
                        .stroke(DossierColors.blue.opacity(0.2), lineWidth: 1)
                )
        )
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(8))
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
        .background(DossierColors.background)
    }
}
