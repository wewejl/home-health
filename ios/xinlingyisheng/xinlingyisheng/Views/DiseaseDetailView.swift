import SwiftUI

// MARK: - 疾病详情页（治愈系风格）
struct DiseaseDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let diseaseId: Int
    let diseaseName: String

    @State private var disease: DiseaseDetailModel?
    @State private var isLoading = true
    @State private var selectedTab = 0
    @State private var isFavorited = false
    @State private var scrollOffset: CGFloat = 0

    private let tabs = ["简介", "症状", "病因", "诊断", "治疗", "护理"]

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 渐变背景
                LinearGradient(
                    colors: [HealingColors.warmCream, HealingColors.softPeach.opacity(0.5)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.6, height: layout.decorativeCircleSize * 0.6)
                    .offset(x: geometry.size.width * 0.3, y: -geometry.size.height * 0.2)
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // 毛玻璃导航栏
                    healingNavigationBar(layout: layout, scrollOffset: scrollOffset)

                    if isLoading {
                        Spacer()
                        healingLoadingView(layout: layout)
                        Spacer()
                    } else if let disease = disease {
                        ScrollView(.vertical, showsIndicators: false) {
                            VStack(alignment: .leading, spacing: 0) {
                                // 信任标签
                                healingTrustBadge(layout: layout)

                                // 疾病名称卡片
                                healingDiseaseHeader(disease, layout: layout)

                                // 作者信息
                                if disease.author_name != nil {
                                    healingAuthorSection(disease, layout: layout)
                                }

                                // Tab 导航
                                healingTabBar(layout: layout)

                                // 内容区域
                                healingContentSection(disease, layout: layout)

                                // 底部留白
                                Spacer()
                                    .frame(height: layout.cardInnerPadding * 10)
                            }
                            .background(
                                GeometryReader { geo in
                                    Color.clear.preference(
                                        key: ScrollOffsetPreferenceKey.self,
                                        value: -geo.frame(in: .named("scroll")).minY
                                    )
                                }
                            )
                        }
                        .coordinateSpace(name: "scroll")
                        .onPreferenceChange(ScrollOffsetPreferenceKey.self) { value in
                            scrollOffset = value
                        }

                        // 浮动底部工具栏
                        healingBottomToolbar(layout: layout)
                    } else {
                        Spacer()
                        healingErrorView(layout: layout)
                        Spacer()
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            loadDiseaseDetail()
        }
    }

    // MARK: - 毛玻璃导航栏
    private func healingNavigationBar(layout: AdaptiveLayout, scrollOffset: CGFloat) -> some View {
        HStack {
            Button(action: { dismiss() }) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground.opacity(0.9))
                        .shadow(color: Color.black.opacity(0.08), radius: 4, x: 0, y: 2)

                    Image(systemName: "chevron.left")
                        .font(.system(size: layout.bodyFontSize - 2, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)
            }

            Spacer()

            HStack(spacing: layout.cardSpacing) {
                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.cardBackground.opacity(0.9))
                            .shadow(color: Color.black.opacity(0.08), radius: 4, x: 0, y: 2)

                        Image(systemName: "magnifyingglass")
                            .font(.system(size: layout.captionFontSize + 4))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                    .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)
                }

                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.cardBackground.opacity(0.9))
                            .shadow(color: Color.black.opacity(0.08), radius: 4, x: 0, y: 2)

                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: layout.captionFontSize + 4))
                            .foregroundColor(HealingColors.textSecondary)
                    }
                    .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)
                }
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 0)
                .fill(HealingColors.cardBackground.opacity(min(0.95, max(0.85, scrollOffset / 150))))
                .background(
                    Color.white.opacity(min(0.3, max(0, scrollOffset / 200)))
                )
        )
    }

    // MARK: - 治愈系信任标签
    private func healingTrustBadge(layout: AdaptiveLayout) -> some View {
        HStack(spacing: layout.cardSpacing / 2) {
            // 书本图标
            ZStack {
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.15))
                    .frame(width: layout.iconSmallSize, height: layout.iconSmallSize)

                Image(systemName: "book.fill")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.forestMist)
            }

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text("健康百科")
                        .font(.system(size: layout.captionFontSize, weight: .semibold))
                        .foregroundColor(HealingColors.forestMist)

                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: layout.captionFontSize - 1))
                        .foregroundColor(HealingColors.mutedCoral)
                }

                Text("三甲医生专业编审 · 灵犀医生官方出品")
                    .font(.system(size: layout.captionFontSize - 1))
                    .foregroundColor(HealingColors.textSecondary)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: layout.captionFontSize - 2, weight: .semibold))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 3)
        )
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardSpacing / 2)
    }

    // MARK: - 治愈系疾病头部
    private func healingDiseaseHeader(_ disease: DiseaseDetailModel, layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 疾病名称
            Text(disease.name)
                .font(.system(size: layout.titleFontSize, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)
                .lineSpacing(4)

            // 科室标签
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "stethoscope")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.deepSage)

                Text("就诊科室：")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)

                Button(action: {}) {
                    HStack(spacing: 4) {
                        Text(disease.recommended_department ?? disease.department_name ?? "未知科室")
                            .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: layout.captionFontSize - 1))
                    }
                    .foregroundColor(HealingColors.forestMist)
                    .padding(.horizontal, layout.cardInnerPadding - 2)
                    .padding(.vertical, 4)
                    .background(
                        Capsule()
                            .fill(HealingColors.softSage.opacity(0.3))
                    )
                }
            }

            // 修订日期
            if let updatedAt = disease.updated_at {
                HStack(spacing: 4) {
                    Image(systemName: "clock")
                        .font(.system(size: layout.captionFontSize))
                    Text(formatDate(updatedAt) + " 修订")
                        .font(.system(size: layout.captionFontSize))
                }
                .foregroundColor(HealingColors.textTertiary)
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        )
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardSpacing / 2)
    }

    // MARK: - 治愈系作者信息
    private func healingAuthorSection(_ disease: DiseaseDetailModel, layout: AdaptiveLayout) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing) {
                if let authorName = disease.author_name {
                    HealingAuthorCard(
                        avatar: disease.author_avatar,
                        name: authorName,
                        title: disease.author_title ?? "",
                        role: "词条作者",
                        layout: layout
                    )
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
        }
        .padding(.top, layout.cardSpacing / 2)
    }

    // MARK: - 治愈系 Tab 导航
    private func healingTabBar(layout: AdaptiveLayout) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing / 2) {
                ForEach(Array(tabs.enumerated()), id: \.offset) { index, tab in
                    Button(action: {
                        withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                            selectedTab = index
                        }
                    }) {
                        Text(tab)
                            .font(.system(size: layout.captionFontSize + 1, weight: selectedTab == index ? .semibold : .regular))
                            .foregroundColor(selectedTab == index ? .white : HealingColors.textSecondary)
                            .padding(.horizontal, layout.cardInnerPadding + 2)
                            .padding(.vertical, layout.cardSpacing / 2 + 2)
                            .background(
                                Capsule()
                                    .fill(selectedTab == index ? HealingColors.forestMist : HealingColors.warmSand.opacity(0.5))
                            )
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
        }
        .padding(.top, layout.cardSpacing)
        .padding(.bottom, layout.cardSpacing / 2)
    }

    // MARK: - 治愈系内容区域
    private func healingContentSection(_ disease: DiseaseDetailModel, layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            let content: String? = {
                switch selectedTab {
                case 0: return disease.overview
                case 1: return disease.symptoms
                case 2: return disease.causes
                case 3: return disease.diagnosis
                case 4: return disease.treatment
                case 5: return disease.care
                default: return nil
                }
            }()

            if let content = content, !content.isEmpty {
                HealingContentCard(title: tabs[selectedTab], content: content, layout: layout)
                    .id(tabs[selectedTab])
                    .transition(.opacity.combined(with: .move(edge: .trailing)))
            } else {
                VStack(spacing: layout.cardSpacing) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.textTertiary.opacity(0.1))
                            .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                        Image(systemName: "doc.text")
                            .font(.system(size: layout.bodyFontSize + 4))
                            .foregroundColor(HealingColors.textTertiary)
                    }

                    Text("暂无\(tabs[selectedTab])内容")
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textTertiary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding * 6)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .animation(.spring(response: 0.4, dampingFraction: 0.85), value: selectedTab)
    }

    // MARK: - 浮动底部工具栏
    private func healingBottomToolbar(layout: AdaptiveLayout) -> some View {
        HStack(spacing: 0) {
            HealingToolbarButton(
                icon: "list.bullet.rectangle",
                title: "目录",
                layout: layout
            ) {}

            HealingToolbarButton(
                icon: "bubble.left.and.bubble.right",
                title: "反馈",
                layout: layout
            ) {}

            HealingToolbarButton(
                icon: isFavorited ? "star.fill" : "star",
                title: "收藏",
                isActive: isFavorited,
                layout: layout
            ) {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                    isFavorited.toggle()
                }
            }
        }
        .padding(.horizontal, layout.cardSpacing)
        .padding(.vertical, layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.08), radius: 12, x: 0, y: 4)
        )
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.bottom, layout.cardInnerPadding * 2)
    }

    // MARK: - 加载视图
    private func healingLoadingView(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .stroke(HealingColors.forestMist.opacity(0.2), lineWidth: 3)
                    .frame(width: layout.iconLargeSize * 2, height: layout.iconLargeSize * 2)

                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(
                        LinearGradient(
                            colors: [HealingColors.deepSage, HealingColors.forestMist],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(lineWidth: 3, lineCap: .round)
                    )
                    .frame(width: layout.iconLargeSize * 2, height: layout.iconLargeSize * 2)
                    .rotationEffect(.degrees(360))
                    .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: UUID())
            }

            Text("加载中...")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
        }
    }

    // MARK: - 错误视图
    private func healingErrorView(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .fill(HealingColors.terracotta.opacity(0.15))
                    .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                Image(systemName: "exclamationmark.triangle")
                    .font(.system(size: layout.bodyFontSize + 4))
                    .foregroundColor(HealingColors.terracotta)
            }

            Text("加载失败")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textTertiary)

            Button(action: loadDiseaseDetail) {
                HStack(spacing: 4) {
                    Image(systemName: "arrow.clockwise")
                    Text("重试")
                }
                .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, layout.cardInnerPadding + 4)
                .padding(.vertical, layout.cardSpacing / 2)
                .background(
                    Capsule()
                        .fill(
                            LinearGradient(
                                colors: [HealingColors.deepSage, HealingColors.forestMist],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                )
            }
        }
    }

    // MARK: - 数据加载
    private func loadDiseaseDetail() {
        isLoading = true

        Task {
            do {
                let detail = try await APIService.shared.getDiseaseDetail(diseaseId: diseaseId)
                await MainActor.run {
                    disease = detail
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }

    // MARK: - 辅助方法
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy年MM月dd日"
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - 滚动偏移量监听
struct ScrollOffsetPreferenceKey: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

// MARK: - 治愈系作者卡片
struct HealingAuthorCard: View {
    let avatar: String?
    let name: String
    let title: String
    let role: String
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            // 头像
            ZStack {
                Circle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)

                if let avatar = avatar, !avatar.isEmpty {
                    AsyncImage(url: URL(string: avatar)) { image in
                        image
                            .resizable()
                            .scaledToFill()
                    } placeholder: {
                        Image(systemName: "person.fill")
                            .font(.system(size: layout.bodyFontSize))
                            .foregroundColor(HealingColors.textTertiary)
                    }
                    .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)
                    .clipShape(Circle())
                } else {
                    Image(systemName: "person.fill")
                        .font(.system(size: layout.bodyFontSize))
                        .foregroundColor(HealingColors.textTertiary)
                }
            }

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(name)
                        .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)

                    // 认证徽章
                    ZStack {
                        Circle()
                            .fill(HealingColors.mutedCoral.opacity(0.2))
                            .frame(width: 18, height: 18)

                        Image(systemName: "checkmark")
                            .font(.system(size: 8, weight: .bold))
                            .foregroundColor(HealingColors.mutedCoral)
                    }

                    Text(role)
                        .font(.system(size: layout.captionFontSize - 1))
                        .foregroundColor(HealingColors.textTertiary)
                        .padding(.leading, 2)
                }

                Text(title)
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
                    .lineLimit(1)
            }
        }
        .padding(layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 3)
        )
    }
}

// MARK: - 治愈系内容卡片
struct HealingContentCard: View {
    let title: String
    let content: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题区域
            HStack(spacing: layout.cardSpacing / 2) {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)

                    Image(systemName: iconNameForTitle(title))
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.forestMist)
                }

                Text(title)
                    .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                // 装饰元素
                HStack(spacing: 2) {
                    ForEach(0..<3) { _ in
                        Circle()
                            .fill(HealingColors.forestMist.opacity(0.3))
                            .frame(width: 4, height: 4)
                    }
                }
            }

            // 分隔线
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [HealingColors.forestMist.opacity(0.5), HealingColors.forestMist.opacity(0.1)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 2)
                .frame(maxWidth: .infinity)

            // 内容文本
            Text(parseMarkdown(content))
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .lineSpacing(6)
        }
        .padding(layout.cardInnerPadding + 4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        )
    }

    private func iconNameForTitle(_ title: String) -> String {
        switch title {
        case "简介": return "doc.text"
        case "症状": return "cross.case"
        case "病因": return "magnifyingglass"
        case "诊断": return "stethoscope"
        case "治疗": return "pills"
        case "护理": return "heart.fill"
        default: return "doc.text"
        }
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

// MARK: - 治愈系工具栏按钮
struct HealingToolbarButton: View {
    let icon: String
    let title: String
    var isActive: Bool = false
    let layout: AdaptiveLayout
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                ZStack {
                    if isActive {
                        Circle()
                            .fill(HealingColors.mutedCoral.opacity(0.2))
                            .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)
                    }

                    Image(systemName: icon)
                        .font(.system(size: layout.captionFontSize + 4))
                        .foregroundColor(isActive ? HealingColors.mutedCoral : HealingColors.textSecondary)
                }

                Text(title)
                    .font(.system(size: layout.captionFontSize - 1, weight: isActive ? .semibold : .regular))
                    .foregroundColor(isActive ? HealingColors.mutedCoral : HealingColors.textSecondary)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 向后兼容的工具栏按钮（用于其他未重构的页面）
struct ToolbarButton: View {
    let icon: String
    let title: String
    var isActive: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: ScaleFactor.spacing(4)) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(isActive ? HealingColors.mutedCoral : HealingColors.textSecondary)

                Text(title)
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(isActive ? HealingColors.mutedCoral : HealingColors.textSecondary)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DiseaseDetailView(diseaseId: 1, diseaseName: "婴儿湿疹")
    }
}
