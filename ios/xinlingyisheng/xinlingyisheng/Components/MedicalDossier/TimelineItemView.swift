import SwiftUI

struct TimelineItemView: View {
    let item: TimelineItem
    let isFirst: Bool
    let isLast: Bool
    
    var body: some View {
        HStack(alignment: .top, spacing: ScaleFactor.spacing(12)) {
            timelineIndicator
            contentSection
        }
    }
    
    private var timelineIndicator: some View {
        VStack(spacing: 0) {
            VStack(spacing: ScaleFactor.spacing(2)) {
                Text(item.date.formatted(.dateTime.month().day()))
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(DXYColors.textSecondary)
                Text(formatTime(item.contents.first?.message?.timestamp ?? item.date))
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)
            }
            .frame(width: ScaleFactor.size(50))
            
            Circle()
                .fill(isLast ? DossierColors.timelineNodeInactive : DossierColors.timelineNodeActive)
                .frame(width: ScaleFactor.size(10), height: ScaleFactor.size(10))
                .padding(.vertical, ScaleFactor.padding(8))
            
            if !isLast {
                Rectangle()
                    .fill(DossierColors.timelineConnector)
                    .frame(width: 2)
                    .frame(maxHeight: .infinity)
            }
        }
        .frame(width: ScaleFactor.size(60))
    }
    
    private var contentSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            ForEach(item.contents) { content in
                TimelineContentView(content: content)
            }
        }
        .padding(.bottom, ScaleFactor.padding(16))
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
}

struct TimelineContentView: View {
    let content: TimelineContent
    
    var body: some View {
        switch content.type {
        case .userMessage:
            if let message = content.message {
                MessageBubble(message: message, isUser: true)
            }
        case .aiMessage:
            if let message = content.message {
                MessageBubble(message: message, isUser: false)
            }
        case .attachment:
            if let attachment = content.attachment {
                AttachmentPreview(attachment: attachment)
            }
        case .sessionStart, .sessionEnd:
            SessionMarker(type: content.type)
        }
    }
}

struct MessageBubble: View {
    let message: DossierChatMessage
    let isUser: Bool
    
    @State private var isCopied = false
    
    var body: some View {
        HStack(alignment: .top, spacing: ScaleFactor.spacing(8)) {
            if !isUser {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.teal)
                    .frame(width: ScaleFactor.size(24), height: ScaleFactor.size(24))
                    .background(DXYColors.teal.opacity(0.15))
                    .clipShape(Circle())
            }
            
            VStack(alignment: isUser ? .trailing : .leading, spacing: ScaleFactor.spacing(4)) {
                Text(message.content)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(isUser ? .white : DXYColors.textPrimary)
                    .padding(.horizontal, ScaleFactor.padding(12))
                    .padding(.vertical, ScaleFactor.padding(10))
                    .background(isUser ? DXYColors.primaryPurple : Color(UIColor.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                
                if message.isImportant {
                    HStack(spacing: ScaleFactor.spacing(4)) {
                        Image(systemName: "star.fill")
                            .font(.system(size: AdaptiveFont.caption))
                        Text("重要")
                            .font(.system(size: AdaptiveFont.caption))
                    }
                    .foregroundColor(.orange)
                }
            }
            
            if isUser {
                Image(systemName: "person.fill")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.primaryPurple)
                    .frame(width: ScaleFactor.size(24), height: ScaleFactor.size(24))
                    .background(DXYColors.primaryPurple.opacity(0.15))
                    .clipShape(Circle())
            }
        }
        .contextMenu {
            Button(action: {
                UIPasteboard.general.string = message.content
                isCopied = true
            }) {
                Label("复制", systemImage: "doc.on.doc")
            }
            
            Button(action: {}) {
                Label(message.isImportant ? "取消标记" : "标记为重要", systemImage: message.isImportant ? "star.slash" : "star")
            }
        }
    }
}

struct AttachmentPreview: View {
    let attachment: Attachment
    @State private var showFullScreen = false
    
    var body: some View {
        Button(action: { showFullScreen = true }) {
            Group {
                switch attachment.type {
                case .image:
                    imagePreview
                case .report:
                    reportPreview
                case .audio:
                    audioPreview
                case .video:
                    videoPreview
                }
            }
        }
        .buttonStyle(PlainButtonStyle())
        .fullScreenCover(isPresented: $showFullScreen) {
            AttachmentFullScreenView(attachment: attachment, isPresented: $showFullScreen)
        }
    }
    
    private var imagePreview: some View {
        ZStack(alignment: .bottomLeading) {
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                .fill(Color.gray.opacity(0.2))
                .frame(width: ScaleFactor.size(120), height: ScaleFactor.size(120))
                .overlay(
                    Image(systemName: "photo")
                        .font(.system(size: AdaptiveFont.largeTitle))
                        .foregroundColor(DXYColors.textTertiary)
                )
            
            HStack(spacing: ScaleFactor.spacing(4)) {
                Image(systemName: "camera.fill")
                    .font(.system(size: AdaptiveFont.caption))
                Text(formatDate(attachment.createdAt))
                    .font(.system(size: AdaptiveFont.caption))
            }
            .foregroundColor(.white)
            .padding(.horizontal, ScaleFactor.padding(6))
            .padding(.vertical, ScaleFactor.padding(4))
            .background(Color.black.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 4, style: .continuous))
            .padding(ScaleFactor.padding(6))
        }
    }
    
    private var reportPreview: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            Image(systemName: "doc.text.fill")
                .font(.system(size: AdaptiveFont.title2))
                .foregroundColor(DXYColors.primaryPurple)
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                Text(attachment.fileName ?? "报告文件")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                    .lineLimit(1)
                
                Text("\(formatDate(attachment.createdAt))")
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)
            }
            
            Spacer()
            
            Text("查看")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.primaryPurple)
        }
        .padding(ScaleFactor.padding(12))
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                .stroke(DossierColors.cardBorder, lineWidth: 1)
        )
    }
    
    private var audioPreview: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            Image(systemName: "waveform")
                .font(.system(size: AdaptiveFont.title2))
                .foregroundColor(DXYColors.teal)
            
            Text("语音记录")
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
            
            Spacer()
        }
        .padding(ScaleFactor.padding(12))
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                .stroke(DossierColors.cardBorder, lineWidth: 1)
        )
    }
    
    private var videoPreview: some View {
        ZStack {
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                .fill(Color.gray.opacity(0.2))
                .frame(width: ScaleFactor.size(160), height: ScaleFactor.size(90))
            
            Image(systemName: "play.circle.fill")
                .font(.system(size: AdaptiveFont.largeTitle))
                .foregroundColor(.white)
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM-dd"
        return formatter.string(from: date)
    }
}

struct AttachmentFullScreenView: View {
    let attachment: Attachment
    @Binding var isPresented: Bool
    
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            
            VStack {
                HStack {
                    Spacer()
                    Button(action: { isPresented = false }) {
                        Image(systemName: "xmark")
                            .font(.system(size: 20, weight: .medium))
                            .foregroundColor(.white)
                            .padding()
                    }
                }
                
                Spacer()
                
                Image(systemName: "photo")
                    .font(.system(size: 64))
                    .foregroundColor(.gray)
                
                Text(attachment.fileName ?? "附件预览")
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(.white)
                    .padding(.top)
                
                Spacer()
            }
        }
    }
}

struct SessionMarker: View {
    let type: TimelineContentType
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Rectangle()
                .fill(DossierColors.divider)
                .frame(height: 1)
            
            Text(type == .sessionStart ? "对话开始" : "对话结束")
                .font(.system(size: AdaptiveFont.caption))
                .foregroundColor(DXYColors.textTertiary)
            
            Rectangle()
                .fill(DossierColors.divider)
                .frame(height: 1)
        }
    }
}

#Preview {
    ScrollView {
        VStack {
            TimelineItemView(
                item: TimelineItem(
                    date: Date(),
                    contents: [
                        TimelineContent(
                            type: .userMessage,
                            message: DossierChatMessage(
                                role: .user,
                                content: "医生您好，我手臂上出现了红疹"
                            )
                        )
                    ]
                ),
                isFirst: true,
                isLast: false
            )
            TimelineItemView(
                item: TimelineItem(
                    date: Date(),
                    contents: [
                        TimelineContent(
                            type: .aiMessage,
                            message: DossierChatMessage(
                                role: .assistant,
                                content: "请问您的红疹出现多久了？"
                            )
                        )
                    ]
                ),
                isFirst: false,
                isLast: true
            )
        }
        .padding()
    }
    .background(DXYColors.background)
}
