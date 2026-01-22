import SwiftUI

// MARK: - 查疾病列表
struct DiseaseListView: View {
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
        ZStack {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                navigationBar
                trustBanner
                searchBar
                contentArea
            }
        }
        .navigationBarBackgroundHidden()
        .onAppear(perform: loadDepartments)
    }
    
    // MARK: - 顶部导航栏
    private var navigationBar: some View {
        HStack {
            Spacer()
            
            Text("查疾病")
                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
            
            Spacer()
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, ScaleFactor.padding(12))
        .background(Color.white)
    }
    
    // MARK: - 信任横幅
    private var trustBanner: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Text("健康百科")
                .font(.system(size: AdaptiveFont.caption, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, ScaleFactor.padding(8))
                .padding(.vertical, ScaleFactor.padding(4))
                .background(DXYColors.primaryPurple)
                .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(4)))
            
            Text("疾病症状全了解 · 鑫琳医生官方出品")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textSecondary)
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, LayoutConstants.compactSpacing)
        .background(
            RoundedRectangle(cornerRadius: LayoutConstants.compactSpacing)
                .fill(Color.white)
                .shadow(color: Color.black.opacity(0.05), radius: 6, x: 0, y: 3)
        )
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, LayoutConstants.compactSpacing)
    }
    
    // MARK: - 搜索区
    private var searchBar: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            HStack(spacing: ScaleFactor.spacing(8)) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(DXYColors.textTertiary)
                
                TextField("请输入疾病/症状", text: $searchText)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textPrimary)
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
                            .font(.system(size: AdaptiveFont.body))
                            .foregroundColor(DXYColors.textTertiary)
                    }
                }
            }
            .padding(.horizontal, ScaleFactor.padding(12))
            .padding(.vertical, ScaleFactor.padding(10))
            .background(DXYColors.searchBackground)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall))
            
            Button {
                performSearch(query: searchText)
            } label: {
                Text("搜索")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, ScaleFactor.padding(18))
                    .padding(.vertical, ScaleFactor.padding(10))
                    .background(DXYColors.primaryPurple)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall))
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.bottom, LayoutConstants.compactSpacing)
    }
    
    // MARK: - 内容区域
    private var contentArea: some View {
        Group {
            if isLoading {
                VStack {
                    Spacer()
                    ProgressView("加载中...")
                    Spacer()
                }
            } else if !normalizedSearchText.isEmpty {
                searchResultsView
            } else if departments.isEmpty {
                emptyState(
                    icon: "exclamationmark.triangle",
                    message: "暂时没有科室数据"
                )
            } else {
                departmentDiseaseList
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    // MARK: - 搜索结果视图
    private var searchResultsView: some View {
        Group {
            if isSearching {
                VStack {
                    Spacer()
                    ProgressView()
                    Spacer()
                }
            } else if hasSearched && searchResults.isEmpty {
                emptyState(
                    icon: "magnifyingglass",
                    message: "未找到相关疾病"
                )
            } else {
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 0) {
                        ForEach(searchResults) { disease in
                            NavigationLink {
                                DiseaseDetailView(diseaseId: disease.id, diseaseName: disease.name)
                            } label: {
                                DiseaseRowView(disease: disease)
                            }
                            .buttonStyle(.plain)
                            
                            Divider()
                                .padding(.leading, 16)
                        }
                    }
                    .background(Color.white)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall))
                    .padding(.horizontal, ScaleFactor.padding(16))
                    .padding(.top, ScaleFactor.padding(8))
                }
            }
        }
    }
    
    // MARK: - 科室/热门疾病列表
    private var departmentDiseaseList: some View {
        GeometryReader { geometry in
            HStack(spacing: 0) {
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 0) {
                        ForEach(Array(departments.enumerated()), id: \.element.id) { index, department in
                            Button {
                                selectedDepartmentIndex = index
                            } label: {
                                DepartmentRowView(
                                    department: department,
                                    isSelected: selectedDepartmentIndex == index
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .frame(width: geometry.size.width * 0.28)
                .background(Color.white)
                
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 0) {
                        HStack {
                            Text("热门")
                                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                                .foregroundColor(DXYColors.textPrimary)
                            Spacer()
                        }
                        .padding(.horizontal, ScaleFactor.padding(16))
                        .padding(.vertical, ScaleFactor.padding(12))
                        
                        if let diseases = selectedDepartment?.hot_diseases, !diseases.isEmpty {
                            ForEach(diseases) { disease in
                                NavigationLink {
                                    DiseaseDetailView(diseaseId: disease.id, diseaseName: disease.name)
                                } label: {
                                    DiseaseRowView(disease: disease)
                                }
                                .buttonStyle(.plain)
                                
                                Divider()
                                    .padding(.leading, 16)
                            }
                        } else {
                            emptyState(
                                icon: "list.bullet.clipboard",
                                message: "暂无热门疾病"
                            )
                            .padding(.horizontal, ScaleFactor.padding(16))
                        }
                    }
                    .background(Color.white)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius))
                    .padding(.horizontal, ScaleFactor.padding(12))
                    .padding(.vertical, ScaleFactor.padding(8))
                }
                .frame(width: geometry.size.width * 0.72)
                .background(DXYColors.background)
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

// MARK: - 科室行
struct DepartmentRowView: View {
    let department: DepartmentWithDiseasesModel
    let isSelected: Bool
    
    var body: some View {
        HStack(spacing: 0) {
            Rectangle()
                .fill(isSelected ? DXYColors.primaryPurple : Color.clear)
                .frame(width: ScaleFactor.size(3))
            
            Text(department.name)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(isSelected ? DXYColors.primaryPurple : DXYColors.textSecondary)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, ScaleFactor.padding(16))
        }
        .background(isSelected ? DXYColors.lightPurple : Color.white)
    }
}

// MARK: - 疾病行
struct DiseaseRowView: View {
    let disease: DiseaseListModel
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Text(disease.name)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
            
            if disease.is_hot {
                Image(systemName: "flame.fill")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(.orange)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .frame(height: ScaleFactor.size(56))
        .background(Color.white)
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DiseaseListView()
    }
}