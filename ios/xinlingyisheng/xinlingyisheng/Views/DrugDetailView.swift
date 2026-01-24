import SwiftUI

// MARK: - 药品详情页（治愈系风格）
struct DrugDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let drugId: Int
    let drugName: String

    @State private var drug: DrugDetailModel?
    @State private var isLoading = true
    @State private var selectedTab = 0

    private let tabs = ["功效作用", "用药禁忌", "用法用量"]

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingDrugDetailBackground(layout: layout)

                VStack(spacing: 0) {
                    // 导航栏
                    HealingDrugDetailNavBar(
                        onDismiss: { dismiss() },
                        layout: layout
                    )

                    if isLoading {
                        HealingDrugDetailLoadingView(layout: layout)
                    } else if let drug = drug {
                        ScrollView(.vertical, showsIndicators: false) {
                            VStack(alignment: .leading, spacing: 0) {
                                // 信任标签
                                HealingDrugDetailTrustBadge(layout: layout)

                                // 药品名称头部
                                HealingDrugDetailHeader(drug: drug, layout: layout)

                                // 安全标签
                                HealingDrugDetailSafetyLabels(drug: drug, layout: layout)

                                // Tab 导航栏
                                HealingDrugDetailTabBar(
                                    tabs: tabs,
                                    selectedTab: $selectedTab,
                                    layout: layout
                                )

                                // 内容区域
                                HealingDrugDetailContentSection(
                                    drug: drug,
                                    selectedTab: selectedTab,
                                    tabs: tabs,
                                    layout: layout
                                )

                                // 底部品牌区
                                HealingDrugDetailBrandFooter(layout: layout)
                            }
                        }
                    } else {
                        HealingDrugDetailErrorView(
                            onRetry: { loadDrugDetail() },
                            layout: layout
                        )
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            loadDrugDetail()
        }
    }

    // MARK: - 数据加载
    private func loadDrugDetail() {
        isLoading = true

        Task {
            do {
                let detail = try await APIService.shared.getDrugDetail(drugId: drugId)
                await MainActor.run {
                    drug = detail
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }
}

// MARK: - 治愈系药品详情背景
struct HealingDrugDetailBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.3),
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

// MARK: - 治愈系导航栏
struct HealingDrugDetailNavBar: View {
    let onDismiss: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        HStack {
            Button(action: onDismiss) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.06), radius: 4, y: 2)

                    Image(systemName: "chevron.left")
                        .font(.system(size: layout.captionFontSize + 2, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)
            }

            Spacer()

            HStack(spacing: layout.cardSpacing) {
                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.cardBackground)
                            .shadow(color: Color.black.opacity(0.04), radius: 3, y: 1)

                        Image(systemName: "magnifyingglass")
                            .font(.system(size: layout.captionFontSize + 1))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                    .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)
                }

                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.cardBackground)
                            .shadow(color: Color.black.opacity(0.04), radius: 3, y: 1)

                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: layout.captionFontSize + 1))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                    .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)
                }
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.9))
    }
}

// MARK: - 治愈系信任标签
struct HealingDrugDetailTrustBadge: View {
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            HStack(spacing: 4) {
                Image(systemName: "checkmark.seal.fill")
                    .font(.system(size: layout.captionFontSize - 1))
                Text("健康百科")
                    .font(.system(size: layout.captionFontSize, weight: .medium))
            }
            .foregroundColor(.white)
            .padding(.horizontal, layout.cardInnerPadding - 2)
            .padding(.vertical, layout.cardSpacing / 2)
            .background(
                LinearGradient(
                    colors: [HealingColors.deepSage, HealingColors.forestMist],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(Capsule())

            Text("三甲医生专业编审 · 灵犀医生官方出品")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
    }
}

// MARK: - 治愈系药品名称头部
struct HealingDrugDetailHeader: View {
    let drug: DrugDetailModel
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            Text(drug.name)
                .font(.system(size: layout.titleFontSize, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)

            if let commonBrands = drug.common_brands, !commonBrands.isEmpty {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "tag.fill")
                        .font(.system(size: layout.captionFontSize - 1))
                        .foregroundColor(HealingColors.forestMist)
                    Text("常见商品名：\(commonBrands)")
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }

            if let reviewerInfo = drug.reviewer_info {
                HStack(spacing: layout.cardSpacing / 2) {
                    if let authorAvatar = drug.author_avatar, !authorAvatar.isEmpty {
                        AsyncImage(url: URL(string: authorAvatar)) { image in
                            image
                                .resizable()
                                .scaledToFill()
                        } placeholder: {
                            ZStack {
                                Circle()
                                    .fill(HealingColors.textTertiary.opacity(0.2))
                                    .frame(width: layout.iconSmallSize - 6, height: layout.iconSmallSize - 6)

                                Image(systemName: "person.circle.fill")
                                    .font(.system(size: 16))
                                    .foregroundColor(HealingColors.textTertiary)
                            }
                        }
                        .frame(width: 32, height: 32)
                        .clipShape(Circle())
                    }

                    Text(reviewerInfo)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textTertiary)
                }
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding + 2)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(HealingColors.cardBackground)
    }
}

// MARK: - 治愈系安全标签
struct HealingDrugDetailSafetyLabels: View {
    let drug: DrugDetailModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: 0) {
            // 孕期安全
            HealingSafetyLabelView(
                icon: "person.2.fill",
                title: "孕期",
                subtitle: drug.pregnancy_desc ?? "妊娠分级 \(drug.pregnancy_level ?? "-")",
                color: HealingColors.dustyBlue,
                layout: layout
            )

            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(width: 1)

            // 哺乳期安全
            HealingSafetyLabelView(
                icon: "lock.shield.fill",
                title: "哺乳期",
                subtitle: drug.lactation_desc ?? "哺乳分级 \(drug.lactation_level ?? "-")",
                color: HealingColors.warmSand,
                layout: layout
            )

            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(width: 1)

            // 儿童可用
            HealingSafetyLabelView(
                icon: "figure.child.fill",
                title: drug.children_usable ? "儿童可用" : "儿童慎用",
                subtitle: drug.children_desc ?? "儿童用药参考",
                color: drug.children_usable ? HealingColors.forestMist : HealingColors.terracotta,
                layout: layout
            )
        }
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
    }
}

// MARK: - 治愈系安全标签单项
struct HealingSafetyLabelView: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing / 3) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 40, height: 40)

                Image(systemName: icon)
                    .font(.system(size: layout.captionFontSize + 3))
                    .foregroundColor(color)
            }

            Text(title)
                .font(.system(size: layout.captionFontSize, weight: .medium))
                .foregroundColor(HealingColors.textPrimary)

            Text(subtitle)
                .font(.system(size: layout.captionFontSize - 2))
                .foregroundColor(HealingColors.textTertiary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - 治愈系 Tab 导航栏
struct HealingDrugDetailTabBar: View {
    let tabs: [String]
    @Binding var selectedTab: Int
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Array(tabs.enumerated()), id: \.offset) { index, tab in
                HealingTabButton(
                    tab: tab,
                    isSelected: selectedTab == index,
                    layout: layout
                ) {
                    selectedTab = index
                }
            }
        }
        .padding(.top, layout.cardSpacing)
        .padding(.horizontal, layout.horizontalPadding)
        .background(HealingColors.cardBackground)
    }
}

// MARK: - 治愈系 Tab 按钮
struct HealingTabButton: View {
    let tab: String
    let isSelected: Bool
    let layout: AdaptiveLayout
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: layout.cardSpacing / 2) {
                Text(tab)
                    .font(.system(size: layout.captionFontSize + 1, weight: isSelected ? .semibold : .regular))
                    .foregroundColor(isSelected ? HealingColors.forestMist : HealingColors.textSecondary)

                tabBarIndicator
            }
        }
        .buttonStyle(PlainButtonStyle())
        .frame(maxWidth: .infinity)
    }

    @ViewBuilder
    private var tabBarIndicator: some View {
        if isSelected {
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [HealingColors.forestMist, HealingColors.deepSage],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 3)
                .clipShape(Capsule())
        } else {
            Rectangle()
                .fill(Color.clear)
                .frame(height: 3)
        }
    }
}

// MARK: - 治愈系内容区域
struct HealingDrugDetailContentSection: View {
    let drug: DrugDetailModel
    let selectedTab: Int
    let tabs: [String]
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            let content: String? = {
                switch selectedTab {
                case 0: return drug.indications
                case 1: return drug.contraindications
                case 2: return drug.dosage
                default: return nil
                }
            }()

            if let content = content, !content.isEmpty {
                HealingDrugContentCard(
                    title: tabs[selectedTab],
                    content: content,
                    layout: layout
                )
            } else {
                VStack(spacing: layout.cardSpacing) {
                    Spacer()

                    ZStack {
                        Circle()
                            .fill(HealingColors.textTertiary.opacity(0.1))
                            .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)

                        Image(systemName: "doc.text")
                            .font(.system(size: layout.bodyFontSize + 4, weight: .light))
                            .foregroundColor(HealingColors.textTertiary)
                    }

                    Text("暂无\(tabs[selectedTab])内容")
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textTertiary)

                    Spacer()
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding * 4)
            }
        }
        .padding(.top, layout.cardSpacing)
        .background(HealingColors.cardBackground.opacity(0.6))
    }
}

// MARK: - 治愈系药品内容卡片
struct HealingDrugContentCard: View {
    let title: String
    let content: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            HStack {
                Text(title)
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: 8, height: 8)
                }
            }

            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [HealingColors.forestMist, HealingColors.deepSage],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 3)
                .frame(width: 30)
                .clipShape(Capsule())

            Text(parseMarkdown(content))
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .lineSpacing(4)
        }
        .padding(layout.cardInnerPadding + 4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.bottom, layout.cardSpacing)
    }

    private func parseMarkdown(_ text: String) -> String {
        var result = text
        result = result.replacingOccurrences(of: "**", with: "")
        result = result.replacingOccurrences(of: "__", with: "")
        result = result.replacingOccurrences(of: "##", with: "")
        result = result.replacingOccurrences(of: "#", with: "")
        result = result.replacingOccurrences(of: "- ", with: "• ")
        return result
    }
}

// MARK: - 治愈系加载视图
struct HealingDrugDetailLoadingView: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack {
            Spacer()
            VStack(spacing: layout.cardSpacing) {
                ProgressView()
                    .tint(HealingColors.forestMist)
                Text("加载中...")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)
            }
            Spacer()
        }
    }
}

// MARK: - 治愈系错误视图
struct HealingDrugDetailErrorView: View {
    let onRetry: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        VStack {
            Spacer()
            VStack(spacing: layout.cardSpacing) {
                ZStack {
                    Circle()
                        .fill(HealingColors.terracotta.opacity(0.1))
                        .frame(width: layout.iconLargeSize * 1.2, height: layout.iconLargeSize * 1.2)

                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: layout.bodyFontSize + 6, weight: .light))
                        .foregroundColor(HealingColors.terracotta)
                }

                Text("加载失败")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Button(action: onRetry) {
                    HStack(spacing: layout.cardSpacing / 2) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: layout.captionFontSize))
                        Text("重试")
                            .font(.system(size: layout.bodyFontSize - 1, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, layout.cardInnerPadding * 2)
                    .padding(.vertical, layout.cardInnerPadding - 2)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.deepSage, HealingColors.forestMist],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                    .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 3)
                }
            }
            Spacer()
        }
    }
}

// MARK: - 治愈系底部品牌区
struct HealingDrugDetailBrandFooter: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            // 分隔线
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(height: 1)
                .padding(.horizontal, layout.horizontalPadding * 2)

            VStack(spacing: layout.cardSpacing / 2) {
                // 品牌图标
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.12))
                        .frame(width: 56, height: 56)

                    Image(systemName: "cross.fill")
                        .font(.system(size: layout.bodyFontSize + 4, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                }

                // 品牌名称
                Text("灵犀医生")
                    .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                    .foregroundColor(HealingColors.forestMist)

                // Slogan
                Text("一起发现健康生活")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textTertiary)
            }
            .frame(maxWidth: .infinity)
        }
        .padding(.top, layout.cardInnerPadding * 2)
        .padding(.bottom, layout.cardInnerPadding * 3)
        .background(HealingColors.cardBackground)
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DrugDetailView(drugId: 1, drugName: "阿奇霉素")
    }
}
