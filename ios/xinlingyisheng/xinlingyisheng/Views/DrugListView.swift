import SwiftUI

// MARK: - 查药品页面（治愈系风格）
struct DrugListView: View {
    @Environment(\.dismiss) private var dismiss

    @State private var categories: [DrugCategoryWithDrugsModel] = []
    @State private var isLoading = true

    @State private var searchText = ""
    @State private var searchResults: [DrugListModel] = []
    @State private var isSearching = false
    @State private var hasSearched = false
    @State private var searchTask: Task<Void, Never>?

    private var normalizedSearchText: String {
        searchText.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingDrugListBackground(layout: layout)

                VStack(spacing: 0) {
                    // 导航栏
                    HealingDrugListNavBar(
                        onDismiss: { dismiss() },
                        layout: layout
                    )

                    // 信任横幅
                    HealingDrugListTrustBanner(layout: layout)

                    // 搜索区
                    HealingDrugListSearchBar(
                        searchText: $searchText,
                        onSearchChange: performSearch,
                        onSearchTap: { performSearch(query: searchText) },
                        layout: layout
                    )

                    // 内容区
                    contentArea(layout: layout)
                }
            }
        }
        .navigationBarBackgroundHidden()
        .onAppear(perform: loadCategories)
    }

    // MARK: - 内容区域
    private func contentArea(layout: AdaptiveLayout) -> some View {
        Group {
            if isLoading {
                HealingDrugListLoadingView(layout: layout)
            } else if !normalizedSearchText.isEmpty {
                HealingDrugListSearchResultsView(
                    searchResults: searchResults,
                    isSearching: isSearching,
                    hasSearched: hasSearched,
                    layout: layout
                )
            } else if categories.isEmpty {
                HealingDrugListEmptyView(
                    icon: "exclamationmark.triangle",
                    message: "暂时没有药品数据",
                    layout: layout
                )
            } else {
                HealingDrugListCategoriesView(
                    categories: categories,
                    layout: layout
                )
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 数据加载
    private func loadCategories() {
        guard categories.isEmpty else { return }

        isLoading = true
        Task {
            do {
                let result = try await APIService.shared.getDrugCategoriesWithDrugs()
                await MainActor.run {
                    categories = result
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }

    // MARK: - 搜索逻辑
    private func performSearch(query: String) {
        searchTask?.cancel()

        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            searchResults = []
            hasSearched = false
            isSearching = false
            return
        }

        isSearching = true
        hasSearched = true

        searchTask = Task {
            do {
                let response = try await APIService.shared.searchDrugs(query: trimmed)
                try Task.checkCancellation()

                await MainActor.run {
                    searchResults = response.items
                    isSearching = false
                }
            } catch is CancellationError {
                // Ignore cancellation
            } catch {
                await MainActor.run {
                    searchResults = []
                    isSearching = false
                }
            }
        }
    }
}

// MARK: - 治愈系药品列表背景
struct HealingDrugListBackground: View {
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

// MARK: - 治愈系导航栏
struct HealingDrugListNavBar: View {
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

            Text("查药品")
                .font(.system(size: layout.bodyFontSize + 1, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.9))
    }
}

// MARK: - 治愈系信任横幅
struct HealingDrugListTrustBanner: View {
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

            Text("药品说明放心查 · 灵犀医生官方出品")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
    }
}

// MARK: - 治愈系搜索栏
struct HealingDrugListSearchBar: View {
    @Binding var searchText: String
    let onSearchChange: (String) -> Void
    let onSearchTap: () -> Void
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textTertiary)

                TextField("请输入药品名/药品问题", text: $searchText)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textPrimary)
                    .onChangeCompat(of: searchText) { newValue in
                        onSearchChange(newValue)
                    }
                    .submitLabel(.search)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                        onSearchChange("")
                    } label: {
                        ZStack {
                            Circle()
                                .fill(HealingColors.textTertiary.opacity(0.2))
                                .frame(width: layout.captionFontSize + 6, height: layout.captionFontSize + 6)

                            Image(systemName: "xmark")
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(HealingColors.textTertiary)
                        }
                    }
                }
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardInnerPadding - 2)
            .background(HealingColors.warmCream.opacity(0.6))
            .clipShape(Capsule())

            Button(action: onSearchTap) {
                Text("搜索")
                    .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                    .foregroundColor(HealingColors.forestMist)
                    .padding(.horizontal, layout.cardInnerPadding)
                    .padding(.vertical, layout.cardInnerPadding - 2)
                    .background(HealingColors.forestMist.opacity(0.15))
                    .clipShape(Capsule())
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
    }
}

// MARK: - 治愈系加载视图
struct HealingDrugListLoadingView: View {
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

// MARK: - 治愈系空态视图
struct HealingDrugListEmptyView: View {
    let icon: String
    let message: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            Spacer()

            ZStack {
                Circle()
                    .fill(HealingColors.textTertiary.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 1.2, height: layout.iconLargeSize * 1.2)

                Image(systemName: icon)
                    .font(.system(size: layout.bodyFontSize + 8, weight: .light))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Text(message)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
    }
}

// MARK: - 治愈系搜索结果视图
struct HealingDrugListSearchResultsView: View {
    let searchResults: [DrugListModel]
    let isSearching: Bool
    let hasSearched: Bool
    let layout: AdaptiveLayout

    var body: some View {
        Group {
            if isSearching {
                VStack {
                    Spacer()
                    ProgressView()
                        .tint(HealingColors.forestMist)
                    Spacer()
                }
            } else if hasSearched && searchResults.isEmpty {
                HealingDrugListEmptyView(
                    icon: "magnifyingglass",
                    message: "未找到相关药品",
                    layout: layout
                )
            } else {
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 0) {
                        ForEach(searchResults) { drug in
                            NavigationLink {
                                DrugDetailView(drugId: drug.id, drugName: drug.name)
                            } label: {
                                HealingDrugListRowItem(drug: drug, layout: layout)
                            }
                            .buttonStyle(.plain)

                            if drug.id != searchResults.last?.id {
                                Rectangle()
                                    .fill(HealingColors.softSage.opacity(0.2))
                                    .frame(height: 1)
                                    .padding(.leading, layout.iconLargeSize + 8)
                            }
                        }
                    }
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
                    .padding(.horizontal, layout.horizontalPadding)
                    .padding(.top, layout.cardSpacing)
                }
                .padding(.bottom, layout.cardInnerPadding * 2)
            }
        }
    }
}

// MARK: - 治愈系药品行项
struct HealingDrugListRowItem: View {
    let drug: DrugListModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            Text(drug.name)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .lineLimit(1)

            if drug.is_hot {
                HStack(spacing: 2) {
                    Image(systemName: "flame.fill")
                        .font(.system(size: layout.captionFontSize - 2))
                    Text("热门")
                        .font(.system(size: layout.captionFontSize - 3, weight: .medium))
                }
                .foregroundColor(HealingColors.terracotta)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: layout.captionFontSize - 1))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardInnerPadding + 2)
        .contentShape(Rectangle())
    }
}

// MARK: - 治愈系分类列表视图
struct HealingDrugListCategoriesView: View {
    let categories: [DrugCategoryWithDrugsModel]
    let layout: AdaptiveLayout

    private var columns: [GridItem] {
        [
            GridItem(.flexible(), spacing: layout.cardSpacing - 2),
            GridItem(.flexible(), spacing: layout.cardSpacing - 2)
        ]
    }

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: layout.cardSpacing) {
                ForEach(categories) { category in
                    HealingDrugListCategoryCard(
                        category: category,
                        columns: columns,
                        layout: layout
                    )
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardSpacing)
        }
    }
}

// MARK: - 治愈系药品分类卡片
struct HealingDrugListCategoryCard: View {
    let category: DrugCategoryWithDrugsModel
    let columns: [GridItem]
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing - 2) {
            // 分类标题
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "pills.fill")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.forestMist)

                Text(category.name)
                    .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                Text("\(category.drugs.count)种")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textTertiary)
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.top, layout.cardInnerPadding)
            .padding(.bottom, layout.cardSpacing / 2)

            // 药品网格
            LazyVGrid(columns: columns, spacing: 0) {
                ForEach(category.drugs) { drug in
                    NavigationLink {
                        DrugDetailView(drugId: drug.id, drugName: drug.name)
                    } label: {
                        HealingDrugListGridItem(drug: drug, layout: layout)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.bottom, layout.cardSpacing / 2)
        }
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系药品网格项
struct HealingDrugListGridItem: View {
    let drug: DrugListModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 3) {
            Text(drug.name)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .lineLimit(1)

            if drug.is_hot {
                Image(systemName: "flame.fill")
                    .font(.system(size: layout.captionFontSize - 2))
                    .foregroundColor(HealingColors.terracotta)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: layout.captionFontSize - 2))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(.horizontal, layout.cardInnerPadding - 2)
        .padding(.vertical, layout.cardInnerPadding - 2)
        .contentShape(Rectangle())
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DrugListView()
    }
}
