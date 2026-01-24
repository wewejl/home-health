import SwiftUI

// MARK: - MedLive 疾病详情页（治愈系风格）
struct MedLiveDiseaseDetailView: View {
    @Environment(\.dismiss) private var dismiss

    // 支持两种初始化方式：传入完整模型，或传入 ID 自动加载
    let disease: MedLiveDiseaseModel?
    let diseaseId: Int?

    @State private var loadedDisease: MedLiveDiseaseModel?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var expandedSections: Set<String> = ["overview"]
    @State private var isFavorited = false

    // 便利初始化器：通过模型直接展示
    init(disease: MedLiveDiseaseModel) {
        self.disease = disease
        self.diseaseId = nil
    }

    // 便利初始化器：通过 ID 加载
    init(diseaseId: Int) {
        self.disease = nil
        self.diseaseId = diseaseId
    }

    private var displayDisease: MedLiveDiseaseModel? {
        disease ?? loadedDisease
    }

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            Group {
                if isLoading {
                    HealingDiseaseLoadingView(layout: layout)
                } else if let error = errorMessage {
                    HealingDiseaseErrorView(message: error, layout: layout) {
                        loadData()
                    }
                } else if let displayDisease = displayDisease {
                    diseaseContent(displayDisease, layout: layout)
                }
            }
        }
        .onAppear(perform: loadData)
        .navigationBarHidden(true)
    }

    // MARK: - 加载数据
    private func loadData() {
        guard disease == nil else {
            isLoading = false
            return
        }

        guard let diseaseId = diseaseId else {
            errorMessage = "缺少疾病 ID"
            isLoading = false
            return
        }

        Task {
            do {
                let disease = try await APIService.shared.getDiseaseDetailMedLive(diseaseId: diseaseId)
                await MainActor.run {
                    loadedDisease = disease
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }

    // MARK: - 疾病内容
    private func diseaseContent(_ disease: MedLiveDiseaseModel, layout: AdaptiveLayout) -> some View {
        ZStack {
            // 治愈系背景
            HealingDiseaseDetailBackground(layout: layout)

            VStack(spacing: 0) {
                // 顶部导航栏
                HealingDiseaseNavBar(
                    onDismiss: { dismiss() },
                    layout: layout
                )

                ScrollView(.vertical, showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 0) {
                        // 信任标签
                        HealingDiseaseTrustBadge(layout: layout)

                        // 疾病名称头部
                        HealingDiseaseHeader(disease: disease, layout: layout)

                        // 内容区块 - 全部展示，可折叠
                        HealingDiseaseSectionsList(
                            disease: disease,
                            expandedSections: $expandedSections,
                            layout: layout
                        )

                        // 底部品牌区
                        HealingDiseaseBrandFooter(layout: layout)
                    }
                }

                // 底部工具栏
                HealingDiseaseBottomToolbar(
                    isFavorited: $isFavorited,
                    layout: layout
                )
            }
        }
    }
}

// MARK: - 治愈系疾病详情背景
struct HealingDiseaseDetailBackground: View {
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

// MARK: - 治愈系加载视图
struct HealingDiseaseLoadingView: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .stroke(HealingColors.forestMist.opacity(0.3), lineWidth: 3)
                    .frame(width: layout.iconLargeSize * 1.2, height: layout.iconLargeSize * 1.2)

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
                    .frame(width: layout.iconLargeSize * 1.2, height: layout.iconLargeSize * 1.2)
                    .rotationEffect(.degrees(360))
                    .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: UUID())
            }

            Text("加载中...")
                .font(.system(size: layout.bodyFontSize))
                .foregroundColor(HealingColors.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(HealingDiseaseDetailBackground(layout: layout))
    }
}

// MARK: - 治愈系错误视图
struct HealingDiseaseErrorView: View {
    let message: String
    let layout: AdaptiveLayout
    let onRetry: () -> Void

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .fill(HealingColors.terracotta.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                Image(systemName: "exclamationmark.triangle")
                    .font(.system(size: layout.bodyFontSize + 8, weight: .light))
                    .foregroundColor(HealingColors.terracotta)
            }

            Text("加载失败")
                .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text(message)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, layout.cardInnerPadding * 2)

            Button(action: onRetry) {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: layout.captionFontSize + 1))
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
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(HealingDiseaseDetailBackground(layout: layout))
    }
}

// MARK: - 治愈系导航栏
struct HealingDiseaseNavBar: View {
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
struct HealingDiseaseTrustBadge: View {
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

            Text("三甲医生专业编审")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
    }
}

// MARK: - 治愈系疾病名称头部
struct HealingDiseaseHeader: View {
    let disease: MedLiveDiseaseModel
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            Text(disease.name)
                .font(.system(size: layout.titleFontSize, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)

            if let department = disease.department {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "cross.case.fill")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.forestMist)
                    Text(department)
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding + 2)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(HealingColors.cardBackground)
    }
}

// MARK: - 治愈系疾病区块列表
struct HealingDiseaseSectionsList: View {
    let disease: MedLiveDiseaseModel
    @Binding var expandedSections: Set<String>
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing - 2) {
            ForEach(disease.sections) { section in
                HealingDiseaseSectionCard(
                    section: section,
                    isExpanded: expandedSections.contains(section.id),
                    layout: layout
                ) {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        if expandedSections.contains(section.id) {
                            expandedSections.remove(section.id)
                        } else {
                            expandedSections.insert(section.id)
                        }
                    }
                }
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardSpacing)
        .padding(.bottom, layout.cardInnerPadding * 2)
    }
}

// MARK: - 治愈系疾病区块卡片
struct HealingDiseaseSectionCard: View {
    let section: DiseaseSection
    let isExpanded: Bool
    let layout: AdaptiveLayout
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 卡片头部 - 可点击展开/折叠
            Button(action: onTap) {
                HStack(spacing: layout.cardSpacing / 2) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.forestMist.opacity(0.15))
                            .frame(width: layout.iconSmallSize, height: layout.iconSmallSize)

                        Image(systemName: section.icon)
                            .font(.system(size: layout.captionFontSize + 2))
                            .foregroundColor(HealingColors.forestMist)
                    }

                    Text(section.title)
                        .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textTertiary)
                }
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardInnerPadding)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(HealingColors.cardBackground)
            }
            .buttonStyle(PlainButtonStyle())

            // 卡片内容
            if isExpanded {
                VStack(alignment: .leading, spacing: layout.cardSpacing) {
                    // 文本内容
                    if let content = section.content, !content.isEmpty {
                        Text(content)
                            .font(.system(size: layout.captionFontSize + 1))
                            .foregroundColor(HealingColors.textPrimary)
                            .lineSpacing(4)
                    }

                    // 结构化子项
                    if let items = section.items, !items.isEmpty {
                        VStack(alignment: .leading, spacing: layout.cardSpacing - 2) {
                            ForEach(items) { item in
                                HealingContentItemView(item: item, layout: layout)
                            }
                        }
                    }
                }
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardInnerPadding)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(HealingColors.warmCream.opacity(0.5))
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系内容项视图
struct HealingContentItemView: View {
    let item: ContentItem
    let layout: AdaptiveLayout

    var body: some View {
        HStack(alignment: .top, spacing: layout.cardSpacing / 2) {
            // 层级缩进指示器
            if item.level > 0 {
                VStack(spacing: 0) {
                    ForEach(0..<item.level, id: \.self) { _ in
                        Rectangle()
                            .fill(HealingColors.forestMist.opacity(0.3))
                            .frame(width: 2)
                    }
                }
                .frame(height: 16)
            } else {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.2))
                        .frame(width: layout.captionFontSize + 2, height: layout.captionFontSize + 2)

                    Circle()
                        .fill(HealingColors.forestMist)
                        .frame(width: layout.captionFontSize - 6, height: layout.captionFontSize - 6)
                }
                .padding(.top, 4)
            }

            VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                if let title = item.title, !title.isEmpty {
                    Text(title)
                        .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)
                }

                Text(item.content)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)
                    .lineSpacing(3)
            }

            Spacer()
        }
    }
}

// MARK: - 治愈系底部工具栏
struct HealingDiseaseBottomToolbar: View {
    @Binding var isFavorited: Bool
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: 0) {
            HealingDiseaseToolbarButton(
                icon: "list.bullet",
                title: "目录",
                color: HealingColors.dustyBlue,
                layout: layout
            ) {}

            HealingDiseaseToolbarButton(
                icon: "text.bubble",
                title: "反馈",
                color: HealingColors.warmSand,
                layout: layout
            ) {}

            HealingDiseaseToolbarButton(
                icon: isFavorited ? "star.fill" : "star",
                title: "收藏",
                color: isFavorited ? HealingColors.mutedCoral : HealingColors.terracotta,
                isActive: isFavorited,
                layout: layout
            ) {
                withAnimation(.spring(response: 0.3)) {
                    isFavorited.toggle()
                }
            }
        }
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: -3)
    }
}

// MARK: - 治愈系工具栏按钮
struct HealingDiseaseToolbarButton: View {
    let icon: String
    let title: String
    let color: Color
    var isActive: Bool = false
    let layout: AdaptiveLayout
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    if isActive {
                        Circle()
                            .fill(color.opacity(0.2))
                            .frame(width: layout.iconSmallSize + 4, height: layout.iconSmallSize + 4)
                    }

                    Image(systemName: icon)
                        .font(.system(size: layout.captionFontSize + 2))
                        .foregroundColor(isActive ? color : HealingColors.textSecondary)
                }

                Text(title)
                    .font(.system(size: layout.captionFontSize - 1))
                    .foregroundColor(isActive ? color : HealingColors.textSecondary)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 治愈系底部品牌区
struct HealingDiseaseBrandFooter: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing / 2) {
            HStack(spacing: 6) {
                Image(systemName: "cross.fill")
                    .font(.system(size: layout.captionFontSize + 1))
                Text("鑫琳医生")
                    .font(.system(size: layout.captionFontSize + 1, weight: .medium))
            }
            .foregroundColor(HealingColors.forestMist.opacity(0.7))

            Text("一起发现健康生活")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(.top, layout.cardSpacing)
        .padding(.bottom, layout.cardInnerPadding * 2)
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        MedLiveDiseaseDetailView(disease: MedLiveDiseaseModel.sampleTricuspidValveDisease)
    }
}
