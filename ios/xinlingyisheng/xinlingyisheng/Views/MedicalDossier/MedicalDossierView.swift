import SwiftUI

// MARK: - 病历资料夹视图（治愈系风格）
struct MedicalDossierView: View {
    @StateObject private var viewModel = MedicalDossierViewModel()
    @State private var selectedEvent: MedicalEvent?

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingDossierBackground(layout: layout)

                VStack(spacing: 0) {
                    headerSection(layout: layout)

                    searchSection(layout: layout)

                    filterSection(layout: layout)

                    contentSection(layout: layout)
                }
            }
        }
        .navigationTitle("病历资料夹")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            await viewModel.refresh()
        }
        .navigationDestinationCompat(item: $selectedEvent) { event in
            EventDetailView(event: event, viewModel: viewModel)
        }
    }

    private func headerSection(layout: AdaptiveLayout) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                Text("我的病历")
                    .font(.system(size: layout.titleFontSize + 4, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "doc.text.fill")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.forestMist)
                    Text("AI 智能整理，一键导出")
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardInnerPadding)
        .padding(.bottom, layout.cardSpacing + 2)
    }

    private func searchSection(layout: AdaptiveLayout) -> some View {
        HStack(spacing: layout.cardSpacing) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textTertiary)

                TextField("搜索病历", text: $viewModel.searchText)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textPrimary)

                if !viewModel.searchText.isEmpty {
                    Button(action: { viewModel.searchText = "" }) {
                        ZStack {
                            Circle()
                                .fill(HealingColors.textTertiary.opacity(0.2))
                                .frame(width: layout.iconSmallSize - 18, height: layout.iconSmallSize - 18)

                            Image(systemName: "xmark")
                                .font(.system(size: 8, weight: .bold))
                                .foregroundColor(HealingColors.textTertiary)
                        }
                    }
                }
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardInnerPadding - 2)
            .background(HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: Color.black.opacity(0.03), radius: 4, y: 2)
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.bottom, layout.cardSpacing)
    }

    private func filterSection(layout: AdaptiveLayout) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing) {
                ForEach(EventFilter.allCases, id: \.self) { filter in
                    HealingFilterChip(
                        title: filter.displayName,
                        count: viewModel.eventCounts[filter] ?? 0,
                        isSelected: viewModel.selectedFilter == filter,
                        layout: layout
                    ) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            viewModel.selectedFilter = filter
                        }
                    }
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
        }
        .padding(.bottom, layout.cardSpacing)
    }

    @ViewBuilder
    private func contentSection(layout: AdaptiveLayout) -> some View {
        if viewModel.isLoading {
            HealingDossierLoadingView(layout: layout)
        } else if viewModel.events.isEmpty {
            HealingDossierEmptyStateView(layout: layout)
        } else if viewModel.filteredEvents.isEmpty {
            HealingDossierSearchEmptyView(
                searchText: viewModel.searchText,
                layout: layout
            )
        } else {
            eventListView(layout: layout)
        }
    }

    private func loadingView(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            ProgressView()
                .scaleEffect(1.2)
                .tint(HealingColors.forestMist)
            Text("加载中...")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func eventListView(layout: AdaptiveLayout) -> some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: layout.cardSpacing) {
                ForEach(viewModel.filteredEvents) { event in
                    SwipeableEventCard(
                        event: event,
                        onTap: {
                            selectedEvent = event
                        },
                        onArchive: {
                            viewModel.archiveEvent(event)
                        },
                        onDelete: {
                            viewModel.deleteEvent(event)
                        }
                    )
                    .transition(.asymmetric(
                        insertion: .opacity.combined(with: .move(edge: .top)),
                        removal: .opacity.combined(with: .move(edge: .trailing))
                    ))
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.bottom, layout.cardInnerPadding * 2)
        }
    }
}

// MARK: - 治愈系病历夹背景
struct HealingDossierBackground: View {
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

// MARK: - 治愈系筛选芯片
struct HealingFilterChip: View {
    let title: String
    let count: Int
    let isSelected: Bool
    let layout: AdaptiveLayout
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: layout.cardSpacing / 3) {
                Text(title)
                    .font(.system(size: layout.captionFontSize + 1, weight: isSelected ? .semibold : .regular))

                if count > 0 {
                    Text("(\(count))")
                        .font(.system(size: layout.captionFontSize))
                }
            }
            .foregroundColor(isSelected ? .white : HealingColors.textSecondary)
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardInnerPadding - 2)
            .background(chipBackground)
            .clipShape(Capsule())
            .shadow(
                color: isSelected ? HealingColors.forestMist.opacity(0.3) : Color.black.opacity(0.04),
                radius: isSelected ? 6 : 3,
                y: 2
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    @ViewBuilder
    private var chipBackground: some View {
        if isSelected {
            LinearGradient(
                colors: [HealingColors.forestMist, HealingColors.deepSage],
                startPoint: .leading,
                endPoint: .trailing
            )
        } else {
            HealingColors.cardBackground
        }
    }
}

// MARK: - 治愈系加载视图
struct HealingDossierLoadingView: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            Spacer()

            ProgressView()
                .scaleEffect(1.2)
                .tint(HealingColors.forestMist)

            Text("加载中...")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
    }
}

// MARK: - 治愈系空状态视图
struct HealingDossierEmptyStateView: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing + 4) {
            Spacer()

            ZStack {
                Circle()
                    .fill(HealingColors.textTertiary.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                Image(systemName: "doc.text.fill")
                    .font(.system(size: layout.bodyFontSize + 8, weight: .light))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Text("暂无病历记录")
                .font(.system(size: layout.bodyFontSize + 1, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text("与医生对话后，病历会自动整理到这里")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)
                .multilineTextAlignment(.center)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
    }
}

// MARK: - 治愈系搜索空状态
struct HealingDossierSearchEmptyView: View {
    let searchText: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing) {
            Spacer()

            ZStack {
                Circle()
                    .fill(HealingColors.textTertiary.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 1.2, height: layout.iconLargeSize * 1.2)

                Image(systemName: "magnifyingglass")
                    .font(.system(size: layout.bodyFontSize + 4, weight: .light))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Text("未找到相关病历")
                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text("试试搜索其他关键词")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
    }
}

#Preview {
    CompatibleNavigationStack {
        MedicalDossierView()
    }
}
