import SwiftUI

// MARK: - 查疾病列表（治愈系风格）
struct DiseaseListView: View {
    @Environment(\.dismiss) private var dismiss

    @State private var departments: [DepartmentWithDiseasesModel] = []
    @State private var selectedDepartmentIndex: Int = 0
    @State private var isLoading = true

    @State private var searchText = ""
    @State private var searchResults: [DiseaseListModel] = []
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
                // 背景
                HealingColors.background
                    .ignoresSafeArea()

                // 装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.06))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geometry.size.width * 0.4, y: -geometry.size.height * 0.15)
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    navigationBar(layout: layout)
                    trustBanner(layout: layout)
                    searchBar(layout: layout)
                    contentArea(layout: layout)
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear(perform: loadDepartments)
    }

    // MARK: - 治愈系导航栏
    private func navigationBar(layout: AdaptiveLayout) -> some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: layout.bodyFontSize, weight: .medium))
                    .foregroundColor(HealingColors.textPrimary)
            }

            Spacer()

            Text("查疾病")
                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Spacer()

            // 临时测试按钮 - 查看三尖瓣疾病 MedLive 数据
            NavigationLink {
                MedLiveDiseaseDetailView(disease: MedLiveDiseaseModel.sampleTricuspidValveDisease)
            } label: {
                Image(systemName: "star.fill")
                    .font(.system(size: layout.bodyFontSize))
                    .foregroundColor(HealingColors.terracotta)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
    }

    // MARK: - 治愈系信任横幅
    private func trustBanner(layout: AdaptiveLayout) -> some View {
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

            Text("疾病百科放心查 · 鑫琳医生官方出品")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
    }

    // MARK: - 治愈系搜索区
    private func searchBar(layout: AdaptiveLayout) -> some View {
        HStack(spacing: layout.cardSpacing / 2) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: layout.bodyFontSize - 2))
                    .foregroundColor(HealingColors.textTertiary)

                TextField("搜索疾病或症状", text: $searchText)
                    .font(.system(size: layout.bodyFontSize - 2))
                    .foregroundColor(HealingColors.textPrimary)
                    .onChangeCompat(of: searchText) { newValue in
                        performSearch(query: newValue)
                    }
                    .submitLabel(.search)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                        searchResults = []
                        hasSearched = false
                        isSearching = false
                        searchTask?.cancel()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: layout.bodyFontSize - 2))
                            .foregroundColor(HealingColors.textTertiary)
                    }
                }
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardInnerPadding - 2)
            .background(HealingColors.warmCream.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

            Button {
                performSearch(query: searchText)
            } label: {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: layout.bodyFontSize - 2, weight: .semibold))
                    .foregroundColor(.white)
                    .frame(width: layout.cardInnerPadding * 3, height: layout.cardInnerPadding * 3)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.deepSage, HealingColors.forestMist],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Circle())
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.bottom, layout.cardSpacing / 2)
    }

    // MARK: - 内容区域
    private func contentArea(layout: AdaptiveLayout) -> some View {
        Group {
            if isLoading {
                VStack {
                    Spacer()
                    ProgressView("加载中...")
                        .tint(HealingColors.forestMist)
                    Spacer()
                }
            } else if !normalizedSearchText.isEmpty {
                searchResultsView(layout: layout)
            } else if departments.isEmpty {
                emptyState(
                    icon: "exclamationmark.triangle",
                    message: "暂时没有科室数据"
                )
            } else {
                departmentDiseaseList(layout: layout)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 搜索结果视图（治愈系风格）
    private func searchResultsView(layout: AdaptiveLayout) -> some View {
        Group {
            if isSearching {
                VStack {
                    Spacer()
                    ProgressView()
                        .tint(HealingColors.forestMist)
                    Spacer()
                }
            } else if hasSearched && searchResults.isEmpty {
                emptyState(
                    icon: "magnifyingglass",
                    message: "未找到相关疾病"
                )
            } else {
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: layout.cardSpacing / 2) {
                        ForEach(searchResults) { disease in
                            NavigationLink {
                                MedLiveDiseaseDetailView(diseaseId: disease.id)
                            } label: {
                                HealingDiseaseRow(disease: disease, layout: layout)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, layout.horizontalPadding)
                    .padding(.top, layout.cardSpacing / 2)
                }
            }
        }
    }

    // MARK: - 科室/热门疾病列表（治愈系风格）
    private func departmentDiseaseList(layout: AdaptiveLayout) -> some View {
        GeometryReader { geometry in
            HStack(spacing: 0) {
                // 左侧科室列表
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 0) {
                        ForEach(Array(departments.enumerated()), id: \.element.id) { index, department in
                            Button {
                                withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                    selectedDepartmentIndex = index
                                }
                            } label: {
                                HealingDepartmentRow(
                                    department: department,
                                    isSelected: selectedDepartmentIndex == index,
                                    layout: layout
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .frame(width: geometry.size.width * 0.26)
                .background(HealingColors.cardBackground)

                // 右侧疾病列表
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 0) {
                        // 热门标题
                        HStack {
                            Image(systemName: "flame.fill")
                                .font(.system(size: layout.captionFontSize + 2))
                                .foregroundColor(HealingColors.terracotta)

                            Text("热门疾病")
                                .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                                .foregroundColor(HealingColors.textPrimary)

                            Spacer()
                        }
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.vertical, layout.cardInnerPadding)

                        if let diseases = selectedDepartment?.hot_diseases, !diseases.isEmpty {
                            ForEach(diseases) { disease in
                                NavigationLink {
                                    MedLiveDiseaseDetailView(diseaseId: disease.id)
                                } label: {
                                    HealingDiseaseRow(disease: disease, layout: layout)
                                }
                                .buttonStyle(.plain)

                                if disease.id != diseases.last?.id {
                                    Divider()
                                        .padding(.leading, layout.cardInnerPadding)
                                        .opacity(0.3)
                                }
                            }
                        } else {
                            emptyState(
                                icon: "list.bullet.clipboard",
                                message: "暂无热门疾病"
                            )
                            .padding(.horizontal, layout.cardInnerPadding)
                        }
                    }
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                    .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
                    .padding(.horizontal, layout.cardSpacing / 2)
                    .padding(.vertical, layout.cardSpacing / 2)
                }
                .frame(width: geometry.size.width * 0.74)
                .background(HealingColors.background)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private var selectedDepartment: DepartmentWithDiseasesModel? {
        guard departments.indices.contains(selectedDepartmentIndex) else { return nil }
        return departments[selectedDepartmentIndex]
    }

    // MARK: - 公共空态
    private func emptyState(icon: String, message: String) -> some View {
        UnifiedEmptyStateView(
            icon: icon,
            title: "",
            message: message
        )
    }
    
    // MARK: - 数据加载
    private func loadDepartments() {
        guard departments.isEmpty else { return }
        
        isLoading = true
        Task {
            do {
                let result = try await APIService.shared.getDepartmentsWithDiseases()
                await MainActor.run {
                    departments = result
                    selectedDepartmentIndex = 0
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
                let response = try await APIService.shared.searchDiseases(query: trimmed)
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

// MARK: - 治愈系科室行
struct HealingDepartmentRow: View {
    let department: DepartmentWithDiseasesModel
    let isSelected: Bool
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: 0) {
            // 选中指示器
            RoundedRectangle(cornerRadius: 2, style: .continuous)
                .fill(HealingColors.forestMist)
                .frame(width: 3)

            Text(department.name)
                .font(.system(size: layout.bodyFontSize - 3, weight: isSelected ? .semibold : .regular))
                .foregroundColor(isSelected ? HealingColors.forestMist : HealingColors.textSecondary)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, layout.cardInnerPadding)
        }
        .background(
            isSelected ?
            HealingColors.softSage.opacity(0.2) :
            HealingColors.cardBackground
        )
    }
}

// MARK: - 治愈系疾病行
struct HealingDiseaseRow: View {
    let disease: DiseaseListModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            Text(disease.name)
                .font(.system(size: layout.bodyFontSize - 2, weight: .medium))
                .foregroundColor(HealingColors.textPrimary)

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: layout.captionFontSize, weight: .semibold))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardInnerPadding - 2)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DiseaseListView()
    }
}