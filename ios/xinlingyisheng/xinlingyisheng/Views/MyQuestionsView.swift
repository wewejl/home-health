import SwiftUI

// MARK: - 我的提问页（治愈系风格）
struct MyQuestionsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var sessions: [SessionModel] = []
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var selectedSession: SessionModel?

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack(alignment: .top) {
                // 治愈系背景
                HealingQuestionsBackground(layout: layout)

                VStack(spacing: 0) {
                    // 导航栏
                    HealingQuestionsNavBar(dismiss: dismiss, layout: layout)

                    if isLoading {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ProgressView()
                                .tint(HealingColors.forestMist)
                                .scaleEffect(1.2)
                            Text("加载提问记录中...")
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                        Spacer()
                    } else if let error = errorMessage {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ZStack {
                                Circle()
                                    .fill(HealingColors.terracotta.opacity(0.1))
                                    .frame(width: layout.iconLargeSize * 1.8, height: layout.iconLargeSize * 1.8)

                                Image(systemName: "exclamationmark.triangle")
                                    .font(.system(size: layout.titleFontSize, weight: .light))
                                    .foregroundColor(HealingColors.terracotta.opacity(0.6))
                            }

                            Text(error)
                                .font(.system(size: layout.bodyFontSize))
                                .foregroundColor(HealingColors.textSecondary)

                            Button(action: { loadSessions() }) {
                                HStack(spacing: layout.cardSpacing / 2) {
                                    Image(systemName: "arrow.clockwise")
                                        .font(.system(size: layout.captionFontSize))
                                    Text("重试")
                                        .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                                }
                                .foregroundColor(.white)
                                .padding(.horizontal, layout.cardInnerPadding + 4)
                                .padding(.vertical, layout.cardInnerPadding - 2)
                                .background(
                                    LinearGradient(
                                        colors: [HealingColors.deepSage, HealingColors.forestMist],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .clipShape(Capsule())
                            }
                        }
                        Spacer()
                    } else if sessions.isEmpty {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ZStack {
                                Circle()
                                    .fill(HealingColors.forestMist.opacity(0.1))
                                    .frame(width: layout.iconLargeSize * 2, height: layout.iconLargeSize * 2)

                                Image(systemName: "bubble.left.and.bubble.right")
                                    .font(.system(size: layout.titleFontSize, weight: .light))
                                    .foregroundColor(HealingColors.forestMist.opacity(0.5))
                            }

                            Text("暂无提问记录")
                                .font(.system(size: layout.bodyFontSize, weight: .medium))
                                .foregroundColor(HealingColors.textPrimary)

                            Text("开始您的第一次健康咨询吧")
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textTertiary)
                        }
                        Spacer()
                    } else {
                        ScrollView(.vertical, showsIndicators: false) {
                            LazyVStack(spacing: layout.cardSpacing / 2) {
                                ForEach(sessions) { session in
                                    HealingSessionCardView(session: session, layout: layout)
                                        .onTapGesture {
                                            selectedSession = session
                                        }
                                        .fluidFadeIn(delay: 0.05)
                                }
                            }
                            .padding(.horizontal, layout.horizontalPadding)
                            .padding(.top, layout.cardSpacing / 2)
                            .padding(.bottom, layout.cardInnerPadding * 6)
                        }
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .navigationDestinationCompat(item: $selectedSession) { session in
            HealingChatFromSessionView(session: session)
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

// MARK: - 治愈系提问背景
struct HealingQuestionsBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.warmSand.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 右上角装饰
                Circle()
                    .fill(HealingColors.softSage.opacity(0.06))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: geo.size.width * 0.5, y: -geo.size.height * 0.1)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系提问导航栏
struct HealingQuestionsNavBar: View {
    let dismiss: DismissAction
    let layout: AdaptiveLayout

    var body: some View {
        HStack {
            Button(action: { dismiss() }) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)

                    Image(systemName: "chevron.left")
                        .font(.system(size: layout.captionFontSize + 2, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)
            }

            Spacer()

            Text("我的提问")
                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Spacer()

            Color.clear.frame(width: layout.iconSmallSize + 8)
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
        .shadow(color: Color.black.opacity(0.02), radius: 4, x: 0, y: 2)
    }
}

// MARK: - 治愈系会话卡片
struct HealingSessionCardView: View {
    let session: SessionModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing) {
            // 头像
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [HealingColors.forestMist, HealingColors.deepSage],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)
                    .shadow(color: HealingColors.forestMist.opacity(0.2), radius: 6, x: 0, y: 3)

                Image(systemName: "person.fill")
                    .font(.system(size: layout.bodyFontSize))
                    .foregroundColor(.white)
            }

            VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                HStack {
                    Text(session.doctor_name ?? "AI医生助手")
                        .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)

                    Spacer()

                    Text(formatDate(session.updated_at))
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textTertiary)
                }

                Text(session.last_message ?? "暂无消息")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)
                    .lineLimit(2)
                    .lineSpacing(2)
            }

            Image(systemName: "chevron.right")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 3)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.1), lineWidth: 1)
        )
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

// MARK: - 治愈系聊天详情页
struct HealingChatFromSessionView: View {
    let session: SessionModel
    @Environment(\.dismiss) private var dismiss
    @State private var messages: [MessageModel] = []
    @State private var messageText = ""
    @State private var isLoading = true
    @State private var isSending = false

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack(alignment: .bottom) {
                // 背景
                HealingColors.warmCream
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // 导航栏
                    HealingChatNavBar(session: session, dismiss: dismiss, layout: layout)

                    if isLoading {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ProgressView()
                                .tint(HealingColors.forestMist)
                                .scaleEffect(1.2)
                            Text("加载消息中...")
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                        Spacer()
                    } else {
                        ScrollViewReader { proxy in
                            ScrollView(.vertical, showsIndicators: false) {
                                LazyVStack(spacing: layout.cardSpacing) {
                                    ForEach(messages) { message in
                                        HealingMessageBubbleView(message: message, layout: layout)
                                            .id(message.id)
                                    }
                                }
                                .padding(.horizontal, layout.horizontalPadding)
                                .padding(.vertical, layout.cardSpacing)
                                .padding(.bottom, 80)
                            }
                            .onChangeCompat(of: messages.count) { _ in
                                if let lastMessage = messages.last {
                                    withAnimation(.easeOut(duration: 0.3)) {
                                        proxy.scrollTo(lastMessage.id, anchor: .bottom)
                                    }
                                }
                            }
                        }
                    }

                    Spacer(minLength: 0)
                }

                // 底部输入栏
                HealingChatInputBar(
                    messageText: $messageText,
                    isSending: $isSending,
                    onSend: sendMessage,
                    layout: layout
                )
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

// MARK: - 治愈系聊天导航栏
struct HealingChatNavBar: View {
    let session: SessionModel
    let dismiss: DismissAction
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            Button(action: { dismiss() }) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)

                    Image(systemName: "chevron.left")
                        .font(.system(size: layout.captionFontSize + 2, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)
            }

            // 医生头像
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [HealingColors.forestMist, HealingColors.deepSage],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: layout.iconSmallSize + 12, height: layout.iconSmallSize + 12)

                Image(systemName: "person.fill")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(.white)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text((session.doctor_name ?? "AI医生助手") + "医生")
                    .font(.system(size: layout.bodyFontSize - 1, weight: .medium))
                    .foregroundColor(HealingColors.textPrimary)

                Text("在线为您服务")
                    .font(.system(size: layout.captionFontSize - 1))
                    .foregroundColor(HealingColors.forestMist)
            }

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .shadow(color: Color.black.opacity(0.03), radius: 4, x: 0, y: 2)
    }
}

// MARK: - 治愈系消息气泡
struct HealingMessageBubbleView: View {
    let message: MessageModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack {
            if message.isFromUser {
                Spacer(minLength: 50)
            }

            VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(message.isFromUser ? .white : HealingColors.textPrimary)
                    .padding(.horizontal, layout.cardInnerPadding)
                    .padding(.vertical, layout.cardInnerPadding - 2)
                    .background(
                        message.isFromUser ?
                        LinearGradient(
                            colors: [HealingColors.forestMist, HealingColors.deepSage],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ) :
                        LinearGradient(
                            colors: [HealingColors.cardBackground, HealingColors.cardBackground],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .shadow(
                        color: message.isFromUser ?
                            HealingColors.forestMist.opacity(0.15) :
                            Color.black.opacity(0.05),
                        radius: 4,
                        x: 0,
                        y: 2
                    )

                Text(formatTime(message.created_at))
                    .font(.system(size: layout.captionFontSize - 1))
                    .foregroundColor(HealingColors.textTertiary)
            }

            if !message.isFromUser {
                Spacer(minLength: 50)
            }
        }
    }

    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
}

// MARK: - 治愈系聊天输入栏
struct HealingChatInputBar: View {
    @Binding var messageText: String
    @Binding var isSending: Bool
    let onSend: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: 0) {
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.2))
                .frame(height: 1)

            HStack(spacing: layout.cardSpacing / 2) {
                TextField("请输入您的问题...", text: $messageText)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textPrimary)
                    .padding(.horizontal, layout.cardInnerPadding)
                    .padding(.vertical, layout.cardInnerPadding - 4)
                    .background(HealingColors.warmCream.opacity(0.8))
                    .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))

                Button(action: onSend) {
                    if isSending {
                        ProgressView()
                            .tint(.white)
                            .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)
                    } else {
                        Image(systemName: "paperplane.fill")
                            .font(.system(size: layout.captionFontSize + 3))
                            .foregroundColor(.white)
                            .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)
                            .background(
                                LinearGradient(
                                    colors: messageText.isEmpty ?
                                        [HealingColors.textTertiary, HealingColors.textTertiary] :
                                        [HealingColors.forestMist, HealingColors.deepSage],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .clipShape(Circle())
                            .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 4, x: 0, y: 2)
                    }
                }
                .disabled(messageText.isEmpty || isSending)
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardInnerPadding)
            .background(HealingColors.cardBackground)
        }
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        MyQuestionsView()
    }
}
