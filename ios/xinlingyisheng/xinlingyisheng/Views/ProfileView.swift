import SwiftUI

// MARK: - 个人中心页面
struct ProfileView: View {
    @StateObject private var authManager = AuthManager.shared
    @State private var showLogoutConfirm = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: AdaptiveSpacing.section) {
                // 用户信息卡片
                UserInfoCard(user: authManager.currentUser)
                
                // 功能菜单
                VStack(spacing: 0) {
                    MenuRow(icon: "doc.text", title: "我的问诊记录", showBadge: false)
                    Divider().padding(.leading, 56)
                    MenuRow(icon: "heart", title: "健康档案", showBadge: false)
                    Divider().padding(.leading, 56)
                    MenuRow(icon: "bell", title: "消息通知", showBadge: true)
                    Divider().padding(.leading, 56)
                    MenuRow(icon: "gearshape", title: "设置", showBadge: false)
                }
                .background(DXYColors.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: LayoutConstants.cornerRadius, style: .continuous))
                
                // 退出登录按钮
                Button(action: {
                    showLogoutConfirm = true
                }) {
                    HStack {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                            .font(.system(size: AdaptiveFont.title3))
                        Text("退出登录")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                    }
                    .foregroundColor(.red)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(16))
                    .background(DXYColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
                }
                
                // 版本信息
                Text("版本 1.0.0")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textTertiary)
                    .padding(.top, AdaptiveSpacing.section)
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
        }
        .background(DXYColors.background)
        .navigationTitle("我的")
        .navigationBarTitleDisplayMode(.inline)
        .alert("确认退出", isPresented: $showLogoutConfirm) {
            Button("取消", role: .cancel) {}
            Button("退出", role: .destructive) {
                authManager.logout()
            }
        } message: {
            Text("确定要退出登录吗？")
        }
    }
}

// MARK: - 用户信息卡片
struct UserInfoCard: View {
    let user: UserModel?
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(16)) {
            // 头像
            Circle()
                .fill(DXYColors.primaryPurple.opacity(0.2))
                .frame(width: ScaleFactor.size(64), height: ScaleFactor.size(64))
                .overlay(
                    Image(systemName: "person.fill")
                        .font(.system(size: AdaptiveFont.largeTitle))
                        .foregroundColor(DXYColors.primaryPurple)
                )
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                Text(user?.nickname ?? "用户")
                    .font(.system(size: AdaptiveFont.title3, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Text(maskedPhone(user?.phone ?? ""))
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textSecondary)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(ScaleFactor.padding(16))
        .background(DXYColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
    }
    
    private func maskedPhone(_ phone: String) -> String {
        guard phone.count >= 11 else { return phone }
        let start = phone.prefix(3)
        let end = phone.suffix(4)
        return "\(start)****\(end)"
    }
}

// MARK: - 菜单行
struct MenuRow: View {
    let icon: String
    let title: String
    let showBadge: Bool
    
    var body: some View {
        Button(action: {}) {
            HStack(spacing: ScaleFactor.spacing(16)) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(DXYColors.primaryPurple)
                    .frame(width: ScaleFactor.size(24))
                
                Text(title)
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(DXYColors.textPrimary)
                
                Spacer()
                
                if showBadge {
                    Circle()
                        .fill(Color.red)
                        .frame(width: ScaleFactor.size(8), height: ScaleFactor.size(8))
                }
                
                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textTertiary)
            }
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, AdaptiveSpacing.item)
        }
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        ProfileView()
    }
}
