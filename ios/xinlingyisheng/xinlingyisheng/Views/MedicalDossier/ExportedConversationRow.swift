import SwiftUI

/// 导出记录列表项
struct ExportedConversationRow: View {
    let export: ExportedConversation
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 图标
            ZStack {
                RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall)
                    .fill(AppColor.primaryPurple.opacity(0.1))
                    .frame(width: ScaleFactor.size(50), height: ScaleFactor.size(50))
                
                Image(systemName: "doc.text.fill")
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(AppColor.primaryPurple)
            }
            
            // 信息
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                Text(export.title)
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(AppColor.textPrimary)
                
                HStack(spacing: ScaleFactor.spacing(8)) {
                    Label(export.department, systemImage: "stethoscope")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(AppColor.textSecondary)
                    
                    Text("•")
                        .foregroundColor(AppColor.textSecondary)
                    
                    Text("\(export.messageCount) 条对话")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(AppColor.textSecondary)
                }
                
                Text(export.formattedExportDate)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(AppColor.textTertiary)
            }
            
            Spacer()
            
            // 文件大小和箭头
            VStack(alignment: .trailing, spacing: ScaleFactor.spacing(4)) {
                Text(export.formattedFileSize)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(AppColor.textSecondary)
                
                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(AppColor.textTertiary)
            }
        }
        .padding(.vertical, ScaleFactor.padding(8))
    }
}

#Preview {
    ExportedConversationRow(
        export: ExportedConversation(
            id: "1",
            title: "皮肤科咨询 - 2026-01-18",
            department: "皮肤科",
            doctorName: "AI皮肤科医生",
            exportDate: Date(),
            pdfFileName: "conversation_2026-01-18_001.pdf",
            messageCount: 12,
            fileSize: 245760
        )
    )
    .padding()
}
