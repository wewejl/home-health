import SwiftUI

// MARK: - 个人中心页面（治愈系风格）

struct ProfileView: View {
    @StateObject private var authManager = AuthManager.shared
    @State private var showLogoutConfirm = false

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 渐变背景
                LinearGradient(
                    colors: [HealingColors.warmCream, HealingColors.softPeach.opacity(0.4)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.6, height: layout.decorativeCircleSize * 0.6)
                    .offset(x: geometry.size.width * 0.4, y: -geometry.size.height * 0.2)
                    .ignoresSafeArea()

                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: -geometry.size.width * 0.3, y: geometry.size.height * 0.3)
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: layout.cardSpacing + 4) {
                        // 用户信息卡片
                        HealingUserInfoCard(user: authManager.currentUser, layout: layout)

                        // 功能菜单
                        healingMenuSection(layout: layout)

                        // 退出登录按钮
                        healingLogoutButton(layout: layout)

                        // 品牌信息
                        healingBrandSection(layout: layout)
                    }
                    .padding(.horizontal, layout.horizontalPadding)
                    .padding(.top, layout.cardSpacing)
                    .padding(.bottom, layout.cardInnerPadding * 6)
                }
            }
        }
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

    // MARK: - 治愈系菜单区域
    private func healingMenuSection(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing / 2) {
            // 第一行
            HStack(spacing: layout.cardSpacing / 2) {
                HealingMenuCard(
                    icon: "doc.text.fill",
                    title: "问诊记录",
                    color: HealingColors.deepSage,
                    layout: layout
                ) {}

                HealingMenuCard(
                    icon: "heart.fill",
                    title: "健康档案",
                    color: HealingColors.mutedCoral,
                    layout: layout
                ) {}
            }

            // 第二行
            HStack(spacing: layout.cardSpacing / 2) {
                HealingMenuCard(
                    icon: "bell.fill",
                    title: "消息通知",
                    color: HealingColors.dustyBlue,
                    layout: layout,
                    hasBadge: true
                ) {}

                HealingMenuCard(
                    icon: "gearshape.fill",
                    title: "设置",
                    color: HealingColors.warmSand,
                    layout: layout
                ) {}
            }
        }
    }

    // MARK: - 治愈系退出按钮
    private func healingLogoutButton(layout: AdaptiveLayout) -> some View {
        Button(action: {
            showLogoutConfirm = true
        }) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "rectangle.portrait.and.arrow.right")
                    .font(.system(size: layout.captionFontSize + 4))

                Text("退出登录")
                    .font(.system(size: layout.bodyFontSize - 1, weight: .medium))
            }
            .foregroundColor(HealingColors.terracotta)
            .frame(maxWidth: .infinity)
            .padding(.vertical, layout.cardInnerPadding)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(HealingColors.cardBackground)
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(HealingColors.terracotta.opacity(0.2), lineWidth: 1.5)
                    )
            )
        }
    }

    // MARK: - 品牌区域
    private func healingBrandSection(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing / 2) {
            // Logo
            HStack(spacing: 6) {
                Image(systemName: "cross.fill")
                    .font(.system(size: layout.captionFontSize + 2))
                Text("鑫琳医生")
                    .font(.system(size: layout.captionFontSize + 1, weight: .medium))
            }
            .foregroundColor(HealingColors.forestMist.opacity(0.8))

            // 版本号
            Text("版本 1.0.0")
                .font(.system(size: layout.captionFontSize - 1))
                .foregroundColor(HealingColors.textTertiary)

            // Slogan
            Text("一起发现健康生活")
                .font(.system(size: layout.captionFontSize - 2))
                .foregroundColor(HealingColors.textTertiary)

            // 装饰点
            HStack(spacing: 6) {
                ForEach(0..<3) { _ in
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.3))
                        .frame(width: 4, height: 4)
                }
            }
            .padding(.top, 2)
        }
        .padding(.top, layout.cardSpacing)
    }
}

// MARK: - 治愈系用户信息卡片

struct HealingUserInfoCard: View {
    let user: UserModel?
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing) {
            // 头像
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [HealingColors.softSage, HealingColors.deepSage],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: layout.iconLargeSize * 1.8, height: layout.iconLargeSize * 1.8)

                Image(systemName: "person.fill")
                    .font(.system(size: layout.bodyFontSize + 4))
                    .foregroundColor(.white)
            }

            VStack(alignment: .leading, spacing: 4) {
                // 问候语
                Text(getGreeting())
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)

                // 昵称
                Text(user?.nickname ?? "用户")
                    .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                // 手机号
                HStack(spacing: 4) {
                    Image(systemName: "phone.fill")
                        .font(.system(size: layout.captionFontSize - 2))
                    Text(maskedPhone(user?.phone ?? ""))
                        .font(.system(size: layout.captionFontSize))
                }
                .foregroundColor(HealingColors.textSecondary)
            }

            Spacer()

            // 编辑按钮
            Button(action: {}) {
                ZStack {
                    Circle()
                        .fill(HealingColors.softSage.opacity(0.3))
                        .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                    Image(systemName: "pencil")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.forestMist)
                }
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        )
    }

    private func getGreeting() -> String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 0..<12: return "早上好"
        case 12..<18: return "下午好"
        default: return "晚上好"
        }
    }

    private func maskedPhone(_ phone: String) -> String {
        guard phone.count >= 11 else { return phone }
        let start = phone.prefix(3)
        let end = phone.suffix(4)
        return "\(start)****\(end)"
    }
}

// MARK: - 治愈系菜单卡片

struct HealingMenuCard: View {
    let icon: String
    let title: String
    let color: Color
    let layout: AdaptiveLayout
    var hasBadge: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: layout.cardSpacing / 2) {
                ZStack {
                    Circle()
                        .fill(color.opacity(0.15))
                        .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)

                    Image(systemName: icon)
                        .font(.system(size: layout.captionFontSize + 4))
                        .foregroundColor(color)

                    if hasBadge {
                        Circle()
                            .fill(HealingColors.terracotta)
                            .frame(width: 8, height: 8)
                            .offset(x: layout.iconLargeSize / 2, y: -layout.iconLargeSize / 2)
                    }
                }

                Text(title)
                    .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                    .foregroundColor(HealingColors.textPrimary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, layout.cardInnerPadding + 4)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(HealingColors.cardBackground)
                    .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Preview

#Preview {
    CompatibleNavigationStack {
        ProfileView()
    }
}
