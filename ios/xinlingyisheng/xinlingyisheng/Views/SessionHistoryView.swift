import SwiftUI

// MARK: - 历史对话列表视图（治愈系风格）
struct SessionHistoryView: View {
    let doctorId: Int?
    let doctorName: String
    let onSelectSession: (String) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var sessions: [SessionModel] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showError = false

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            NavigationView {
                ZStack {
                    // 治愈系背景
                    HealingSessionHistoryBackground(layout: layout)

                    if isLoading {
                        HealingSessionHistoryLoadingView(layout: layout)
                    } else if sessions.isEmpty {
                        HealingSessionHistoryEmptyView(
                            doctorName: doctorName,
                            layout: layout
                        )
                    } else {
                        HealingSessionHistoryListView(
                            sessions: sessions,
                            layout: layout
                        ) {
                            onSelectSession($0)
                        }
                    }
                }
                .navigationTitle("历史对话")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("关闭") {
                            dismiss()
                        }
                        .foregroundColor(HealingColors.forestMist)
                        .font(.system(size: layout.bodyFontSize - 1))
                    }
                }
                .task {
                    await loadSessions()
                }
                .alert("加载失败", isPresented: $showError) {
                    Button("重试") {
                        Task { await loadSessions() }
                    }
                    Button("取消", role: .cancel) {}
                } message: {
                    Text(errorMessage ?? "未知错误")
                }
            }
        }
    }

    // MARK: - 加载会话
    private func loadSessions() async {
        isLoading = true
        defer { isLoading = false }

        do {
            // 获取所有会话
            let allSessions = try await APIService.shared.getSessions()

            // 筛选该医生的会话
            if let doctorId = doctorId {
                sessions = allSessions.filter { $0.doctor_id == doctorId }
            } else {
                sessions = allSessions
            }

            // 按更新时间倒序排列
            sessions.sort { $0.updated_at > $1.updated_at }

            print("[SessionHistory] 加载了 \(sessions.count) 个会话")

        } catch {
            errorMessage = "加载失败: \(error.localizedDescription)"
            showError = true
        }
    }
}

// MARK: - 治愈系会话历史背景
struct HealingSessionHistoryBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.softSage.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.15)
                    .ignoresSafeArea()

                // 底部装饰光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: -geo.size.width * 0.4, y: geo.size.height * 0.2)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系加载视图
struct HealingSessionHistoryLoadingView: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            Spacer()

            ProgressView()
                .scaleEffect(1.2)
                .tint(HealingColors.forestMist)

            Text("加载中...")
                .font(.system(size: layout.bodyFontSize))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
    }
}

// MARK: - 治愈系空状态视图
struct HealingSessionHistoryEmptyView: View {
    let doctorName: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing + 4) {
            Spacer()

            ZStack {
                Circle()
                    .fill(HealingColors.textTertiary.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                Image(systemName: "bubble.left.and.bubble.right")
                    .font(.system(size: layout.bodyFontSize + 12, weight: .light))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Text("暂无历史对话")
                .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text("与\(doctorName)的对话将显示在这里")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
                .multilineTextAlignment(.center)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
    }
}

// MARK: - 治愈系会话列表视图
struct HealingSessionHistoryListView: View {
    let sessions: [SessionModel]
    let layout: AdaptiveLayout
    let onSelectSession: (String) -> Void

    var body: some View {
        ScrollView {
            LazyVStack(spacing: layout.cardSpacing) {
                ForEach(sessions, id: \.session_id) { session in
                    HealingSessionHistoryCard(
                        session: session,
                        layout: layout
                    ) {
                        onSelectSession(session.session_id)
                    }
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardSpacing)
        }
    }
}

// MARK: - 治愈系会话历史卡片
struct HealingSessionHistoryCard: View {
    let session: SessionModel
    let layout: AdaptiveLayout
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: layout.cardSpacing) {
                // 顶部: 智能体类型 + 时间
                HStack(spacing: layout.cardSpacing / 2) {
                    // 智能体类型标签
                    Text(agentTypeDisplayName)
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                        .foregroundColor(agentTypeColor)
                        .padding(.horizontal, layout.cardInnerPadding - 2)
                        .padding(.vertical, layout.cardSpacing / 3)
                        .background(agentTypeColor.opacity(0.15))
                        .clipShape(Capsule())

                    // 状态标签
                    Text(session.status == "active" ? "进行中" : "已完成")
                        .font(.system(size: layout.captionFontSize - 1, weight: .medium))
                        .foregroundColor(session.status == "active" ? HealingColors.forestMist : HealingColors.textTertiary)
                        .padding(.horizontal, layout.cardInnerPadding - 2)
                        .padding(.vertical, layout.cardSpacing / 3)
                        .background(
                            (session.status == "active" ? HealingColors.forestMist : HealingColors.textTertiary).opacity(0.15)
                        )
                        .clipShape(Capsule())

                    Spacer()

                    // 时间
                    Text(formattedDate)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textTertiary)
                }

                // 最后一条消息预览
                Text(session.last_message ?? "开始新对话")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textPrimary)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                // 底部: 消息图标
                HStack(spacing: layout.cardSpacing / 2) {
                    HStack(spacing: 4) {
                        ZStack {
                            Circle()
                                .fill(HealingColors.textTertiary.opacity(0.15))
                                .frame(width: 20, height: 20)

                            Image(systemName: "bubble.left.fill")
                                .font(.system(size: 10))
                                .foregroundColor(HealingColors.textTertiary)
                        }

                        Text("点击继续对话")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: layout.captionFontSize, weight: .semibold))
                        .foregroundColor(HealingColors.textTertiary)
                }
            }
            .padding(layout.cardInnerPadding + 2)
            .background(HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    // 智能体类型显示名称
    private var agentTypeDisplayName: String {
        switch session.agent_type {
        case "dermatology": return "皮肤科"
        case "cardiology": return "心内科"
        case "orthopedics": return "骨科"
        case "general": return "通用问诊"
        default: return session.agent_type ?? "问诊"
        }
    }

    // 智能体类型颜色
    private var agentTypeColor: Color {
        switch session.agent_type {
        case "dermatology": return HealingColors.dustyBlue
        case "cardiology": return HealingColors.mutedCoral
        case "orthopedics": return HealingColors.warmSand
        default: return HealingColors.forestMist
        }
    }

    // 格式化时间
    private var formattedDate: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        formatter.locale = Locale(identifier: "zh_CN")
        return formatter.localizedString(for: session.updated_at, relativeTo: Date())
    }
}

// MARK: - Preview
#Preview {
    SessionHistoryView(
        doctorId: 1,
        doctorName: "灵犀医生",
        onSelectSession: { _ in }
    )
}
