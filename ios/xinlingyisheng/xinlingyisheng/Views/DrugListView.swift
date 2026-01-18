import SwiftUI

// MARK: - 查药品页面
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
        .onAppear(perform: loadCategories)
    }
    
    // MARK: - 顶部导航栏
    private var navigationBar: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            Spacer()
            
            Text("查药品")
                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
            
            Spacer()
            
            Color.clear
                .frame(width: ScaleFactor.size(18), height: ScaleFactor.size(18))
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
            
            Text("药品说明放心查 · 鑫琳医生官方出品")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textSecondary)
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, ScaleFactor.padding(10))
        .background(Color.white)
    }
    
    // MARK: - 搜索区
    private var searchBar: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            HStack(spacing: ScaleFactor.spacing(8)) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(DXYColors.textTertiary)
                
                TextField("请输入药品名/药品问题", text: $searchText)
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
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.vertical, AdaptiveSpacing.item)
            .background(DXYColors.searchBackground)
            .clipShape(Capsule())
            
            Button {
                performSearch(query: searchText)
            } label: {
                Text("搜索")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.primaryPurple)
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, AdaptiveSpacing.item)
        .background(Color.white)
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
            } else if categories.isEmpty {
                emptyState(
                    icon: "exclamationmark.triangle",
                    message: "暂时没有药品数据"
                )
            } else {
                categoriesListView
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
                    message: "未找到相关药品"
                )
            } else {
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 0) {
                        ForEach(searchResults) { drug in
                            NavigationLink {
                                DrugDetailView(drugId: drug.id, drugName: drug.name)
                            } label: {
                                DrugRowView(drug: drug)
                            }
                            .buttonStyle(.plain)
                            
                            Divider()
                                .padding(.leading, 16)
                        }
                    }
                    .background(Color.white)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius))
                    .padding(.horizontal, ScaleFactor.padding(16))
                    .padding(.top, ScaleFactor.padding(12))
                }
            }
        }
    }
    
    // MARK: - 分类药品列表视图
    private var categoriesListView: some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: ScaleFactor.spacing(12)) {
                ForEach(categories) { category in
                    DrugCategoryCardView(category: category)
                }
            }
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(12))
        }
    }
    
    // MARK: - 公共空态
    private func emptyState(icon: String, message: String) -> some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            Image(systemName: icon)
                .font(.system(size: AdaptiveFont.custom(40)))
                .foregroundColor(DXYColors.textTertiary)
            Text(message)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textTertiary)
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

// MARK: - 药品分类卡片
struct DrugCategoryCardView: View {
    let category: DrugCategoryWithDrugsModel
    
    private let columns = [
        GridItem(.flexible(), spacing: 0),
        GridItem(.flexible(), spacing: 0)
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 分类标题
            Text(category.name)
                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.top, ScaleFactor.padding(16))
                .padding(.bottom, ScaleFactor.padding(8))
            
            // 药品网格
            LazyVGrid(columns: columns, spacing: 0) {
                ForEach(category.drugs) { drug in
                    NavigationLink {
                        DrugDetailView(drugId: drug.id, drugName: drug.name)
                    } label: {
                        DrugGridItemView(drug: drug)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.bottom, ScaleFactor.padding(8))
        }
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius))
    }
}

// MARK: - 药品网格项
struct DrugGridItemView: View {
    let drug: DrugListModel
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(4)) {
            Text(drug.name)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
                .lineLimit(1)
            
            if drug.is_hot {
                Image(systemName: "flame.fill")
                    .font(.system(size: AdaptiveFont.custom(10)))
                    .foregroundColor(.orange)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.custom(10)))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(14))
    }
}

// MARK: - 药品行视图
struct DrugRowView: View {
    let drug: DrugListModel
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Text(drug.name)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
            
            if drug.is_hot {
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
        DrugListView()
    }
}
