import SwiftUI

struct MyQuestionsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var sessions: [SessionModel] = []
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var selectedSession: SessionModel?
    
    var body: some View {
        ZStack(alignment: .top) {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 导航栏
                HStack {
                    Button(action: { dismiss() }) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: AdaptiveFont.title3, weight: .medium))
                            .foregroundColor(DXYColors.textPrimary)
                    }
                    
                    Spacer()
                    
                    Text("我的提问")
                        .font(.system(size: AdaptiveFont.title3, weight: .semibold))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Spacer()
                    
                    Color.clear.frame(width: ScaleFactor.size(24))
                }
                .padding(.horizontal, LayoutConstants.horizontalPadding)
                .padding(.vertical, AdaptiveSpacing.item)
                .background(DXYColors.cardBackground)
                
                if isLoading {
                    Spacer()
                    ProgressView()
                        .scaleEffect(1.2)
                    Spacer()
                } else if let error = errorMessage {
                    Spacer()
                    VStack(spacing: ScaleFactor.spacing(16)) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: AdaptiveFont.custom(48)))
                            .foregroundColor(DXYColors.textTertiary)
                        Text(error)
                            .font(.system(size: AdaptiveFont.subheadline))
                            .foregroundColor(DXYColors.textSecondary)
                        Button("重试") {
                            loadSessions()
                        }
                        .foregroundColor(DXYColors.primaryPurple)
                    }
                    Spacer()
                } else if sessions.isEmpty {
                    Spacer()
                    VStack(spacing: ScaleFactor.spacing(16)) {
                        Image(systemName: "bubble.left.and.bubble.right")
                            .font(.system(size: AdaptiveFont.custom(48)))
                            .foregroundColor(DXYColors.textTertiary)
                        Text("暂无提问记录")
                            .font(.system(size: AdaptiveFont.subheadline))
                            .foregroundColor(DXYColors.textSecondary)
                        Text("去问医生页面开始咨询吧")
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textTertiary)
                    }
                    Spacer()
                } else {
                    ScrollView(.vertical, showsIndicators: false) {
                        LazyVStack(spacing: ScaleFactor.spacing(12)) {
                            ForEach(sessions) { session in
                                SessionCardView(session: session)
                                    .onTapGesture {
                                        selectedSession = session
                                    }
                            }
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .navigationDestinationCompat(item: $selectedSession) { session in
            ChatFromSessionView(session: session)
        }
        .onAppear {
            loadSessions()
        }
    }
    
    private func loadSessions() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let result = try await APIService.shared.getSessions()
                await MainActor.run {
                    sessions = result
                    isLoading = false
                }
            } catch let error as APIError {
                await MainActor.run {
                    errorMessage = error.errorDescription
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = "加载失败"
                    isLoading = false
                }
            }
        }
    }
}

struct SessionCardView: View {
    let session: SessionModel
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            Circle()
                .fill(DXYColors.primaryPurple.opacity(0.2))
                .frame(width: ScaleFactor.size(48), height: ScaleFactor.size(48))
                .overlay(
                    Image(systemName: "person.fill")
                        .font(.system(size: AdaptiveFont.title2))
                        .foregroundColor(DXYColors.primaryPurple)
                )
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                HStack {
                    Text(session.doctor_name ?? "AI助手")
                        .font(.system(size: AdaptiveFont.body, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Spacer()
                    
                    Text(formatDate(session.updated_at))
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textTertiary)
                }
                
                Text(session.last_message ?? "暂无消息")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textSecondary)
                    .lineLimit(2)
            }
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(ScaleFactor.padding(16))
        .background(DXYColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 2)
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        let calendar = Calendar.current
        
        if calendar.isDateInToday(date) {
            formatter.dateFormat = "HH:mm"
        } else if calendar.isDateInYesterday(date) {
            return "昨天"
        } else {
            formatter.dateFormat = "MM-dd"
        }
        
        return formatter.string(from: date)
    }
}

struct ChatFromSessionView: View {
    let session: SessionModel
    @Environment(\.dismiss) private var dismiss
    @State private var messages: [MessageModel] = []
    @State private var messageText = ""
    @State private var isLoading = true
    @State private var isSending = false
    
    var body: some View {
        ZStack(alignment: .bottom) {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 导航栏
                HStack(spacing: ScaleFactor.spacing(12)) {
                    Button(action: { dismiss() }) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: AdaptiveFont.title3, weight: .medium))
                            .foregroundColor(DXYColors.textPrimary)
                    }
                    
                    Circle()
                        .fill(DXYColors.primaryPurple.opacity(0.2))
                        .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                        .overlay(
                            Image(systemName: "person.fill")
                                .font(.system(size: AdaptiveFont.subheadline))
                                .foregroundColor(DXYColors.primaryPurple)
                        )
                    
                    Text("\(session.doctor_name ?? "AI助手")医生")
                        .font(.system(size: AdaptiveFont.body, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Spacer()
                }
                .padding(.horizontal, LayoutConstants.horizontalPadding)
                .padding(.vertical, AdaptiveSpacing.item)
                .background(DXYColors.cardBackground)
                
                if isLoading {
                    Spacer()
                    ProgressView()
                    Spacer()
                } else {
                    ScrollViewReader { proxy in
                        ScrollView(.vertical, showsIndicators: false) {
                            LazyVStack(spacing: ScaleFactor.spacing(16)) {
                                ForEach(messages) { message in
                                    MessageBubbleView(message: message)
                                        .id(message.id)
                                }
                            }
                            .padding(LayoutConstants.horizontalPadding)
                            .padding(.bottom, 80)
                        }
                        .onChangeCompat(of: messages.count) { _ in
                            if let lastMessage = messages.last {
                                withAnimation {
                                    proxy.scrollTo(lastMessage.id, anchor: .bottom)
                                }
                            }
                        }
                    }
                }
                
                Spacer(minLength: 0)
            }
            
            // 底部输入栏
            VStack(spacing: 0) {
                Divider()
                HStack(spacing: ScaleFactor.spacing(12)) {
                    TextField("请输入您的问题...", text: $messageText)
                        .font(.system(size: AdaptiveFont.subheadline))
                        .padding(.horizontal, ScaleFactor.padding(16))
                        .padding(.vertical, ScaleFactor.padding(12))
                        .background(DXYColors.searchBackground)
                        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(20), style: .continuous))
                    
                    Button(action: sendMessage) {
                        if isSending {
                            ProgressView()
                                .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                        } else {
                            Image(systemName: "paperplane.fill")
                                .font(.system(size: AdaptiveFont.title3))
                                .foregroundColor(.white)
                                .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                                .background(
                                    messageText.isEmpty ? DXYColors.textTertiary : DXYColors.primaryPurple
                                )
                                .clipShape(Circle())
                        }
                    }
                    .disabled(messageText.isEmpty || isSending)
                }
                .padding(.horizontal, LayoutConstants.horizontalPadding)
                .padding(.vertical, AdaptiveSpacing.item)
                .background(DXYColors.cardBackground)
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            loadMessages()
        }
    }
    
    private func loadMessages() {
        isLoading = true
        
        Task {
            do {
                let result = try await APIService.shared.getMessages(sessionId: session.session_id)
                await MainActor.run {
                    messages = result.messages
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }
    
    private func sendMessage() {
        guard !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        let content = messageText
        messageText = ""
        isSending = true
        
        Task {
            do {
                let result = try await APIService.shared.sendMessage(sessionId: session.session_id, content: content)
                await MainActor.run {
                    messages.append(result.user_message)
                    messages.append(result.ai_message)
                    isSending = false
                }
            } catch {
                await MainActor.run {
                    messageText = content
                    isSending = false
                }
            }
        }
    }
}

struct MessageBubbleView: View {
    let message: MessageModel
    
    var body: some View {
        HStack {
            if message.isFromUser {
                Spacer(minLength: ScaleFactor.size(60))
            }
            
            VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: ScaleFactor.spacing(4)) {
                Text(message.content)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(message.isFromUser ? .white : DXYColors.textPrimary)
                    .padding(.horizontal, ScaleFactor.padding(14))
                    .padding(.vertical, ScaleFactor.padding(10))
                    .background(
                        message.isFromUser ? DXYColors.primaryPurple : DXYColors.cardBackground
                    )
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
                
                Text(formatTime(message.created_at))
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)
            }
            
            if !message.isFromUser {
                Spacer(minLength: ScaleFactor.size(60))
            }
        }
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
}

#Preview {
    CompatibleNavigationStack {
        MyQuestionsView()
    }
}
