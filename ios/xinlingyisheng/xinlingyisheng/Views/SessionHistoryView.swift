import SwiftUI

// MARK: - 历史对话列表视图
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
        NavigationView {
            ZStack {
                MedicalColors.bgPrimary
                    .ignoresSafeArea()
                
                if isLoading {
                    VStack(spacing: 16) {
                        ProgressView()
                            .scaleEffect(1.2)
                        Text("加载中...")
                            .font(MedicalTypography.bodyMedium)
                            .foregroundColor(MedicalColors.textSecondary)
                    }
                } else if sessions.isEmpty {
                    emptyStateView
                } else {
                    sessionListView
                }
            }
            .navigationTitle("历史对话")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("关闭") {
                        dismiss()
                    }
                    .foregroundColor(MedicalColors.primaryBlue)
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
    
    // MARK: - 空状态视图
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 56))
                .foregroundColor(MedicalColors.textMuted)
            
            Text("暂无历史对话")
                .font(MedicalTypography.h3)
                .foregroundColor(MedicalColors.textPrimary)
            
            Text("与\(doctorName)的对话将显示在这里")
                .font(MedicalTypography.bodyMedium)
                .foregroundColor(MedicalColors.textSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(MedicalSpacing.xl)
    }
    
    // MARK: - 会话列表视图
    private var sessionListView: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(sessions, id: \.session_id) { session in
                    SessionHistoryCard(
                        session: session,
                        onTap: {
                            onSelectSession(session.session_id)
                        }
                    )
                }
            }
            .padding(MedicalSpacing.lg)
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

// MARK: - 会话历史卡片
struct SessionHistoryCard: View {
    let session: SessionModel
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 10) {
                // 顶部: 智能体类型 + 时间
                HStack {
                    // 智能体类型标签
                    Text(agentTypeDisplayName)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(agentTypeColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(agentTypeColor.opacity(0.1))
                        .cornerRadius(4)
                    
                    // 状态标签
                    Text(session.status == "active" ? "进行中" : "已完成")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(session.status == "active" ? MedicalColors.successGreen : MedicalColors.textMuted)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(
                            (session.status == "active" ? MedicalColors.successGreen : MedicalColors.textMuted).opacity(0.1)
                        )
                        .cornerRadius(4)
                    
                    Spacer()
                    
                    // 时间
                    Text(formattedDate)
                        .font(MedicalTypography.caption)
                        .foregroundColor(MedicalColors.textMuted)
                }
                
                // 最后一条消息预览
                Text(session.last_message ?? "开始新对话")
                    .font(MedicalTypography.bodyMedium)
                    .foregroundColor(MedicalColors.textPrimary)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
                
                // 底部: 消息图标
                HStack(spacing: 4) {
                    Image(systemName: "bubble.left.fill")
                        .font(.system(size: 11))
                        .foregroundColor(MedicalColors.textMuted)
                    Text("点击继续对话")
                        .font(.system(size: 12))
                        .foregroundColor(MedicalColors.textSecondary)
                    
                    Spacer()
                    
                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(MedicalColors.textMuted)
                }
            }
            .padding(MedicalSpacing.lg)
            .background(MedicalColors.bgCard)
            .cornerRadius(MedicalCornerRadius.lg)
            .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
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
        case "dermatology": return MedicalColors.secondaryTeal
        case "cardiology": return MedicalColors.statusError
        case "orthopedics": return Color(hex: "#8B5CF6")
        default: return MedicalColors.primaryBlue
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
        doctorName: "张医生",
        onSelectSession: { _ in }
    )
}
