import SwiftUI

// MARK: - 鑫琳医生风格颜色
struct DXYColors {
    static let primaryPurple = Color(red: 0.36, green: 0.27, blue: 1.0)       // #5C44FF
    static let lightPurple = Color(red: 0.94, green: 0.91, blue: 1.0)         // #EFE7FF
    static let teal = Color(red: 0.20, green: 0.77, blue: 0.75)               // #34C6C0
    static let blue = Color(red: 0.28, green: 0.71, blue: 0.96)               // #47B5F5
    static let orange = Color(red: 1.0, green: 0.60, blue: 0.24)              // #FF9A3C
    static let background = Color(red: 0.97, green: 0.96, blue: 0.98)         // #F7F6FB
    static let cardBackground = Color.white
    static let searchBackground = Color(red: 0.97, green: 0.96, blue: 0.98)   // #F7F6FA
    static let tagBackground = Color(red: 0.95, green: 0.94, blue: 0.97)      // #F2F1F7
    static let textPrimary = Color.black
    static let textSecondary = Color(red: 0.45, green: 0.45, blue: 0.50)
    static let textTertiary = Color(red: 0.71, green: 0.71, blue: 0.77)       // #B6B5C5
    static let promotionPurple = Color(red: 0.97, green: 0.95, blue: 1.0)     // #F7F3FF
    static let promotionOrange = Color(red: 1.0, green: 0.97, blue: 0.91)     // #FFF7E8
}

// MARK: - 主入口视图（TabView 结构）
enum BrowseTarget: String, CaseIterable, Identifiable {
    case disease
    case drug
    
    var id: String { rawValue }
    var title: String {
        switch self {
        case .disease: return "查疾病"
        case .drug: return "查药品"
        }
    }
}

// MARK: - 查病查药容器
struct DiseaseDrugBrowseView: View {
    @Binding var selection: BrowseTarget

    var body: some View {
        VStack(spacing: 0) {
            // 顶部分段控制器
            segmentPicker

            // 内容区域
            Group {
                switch selection {
                case .disease:
                    DiseaseListView()
                case .drug:
                    DrugListView()
                }
            }
        }
    }

    // MARK: - 分段控制器
    private var segmentPicker: some View {
        HStack(spacing: 0) {
            ForEach(BrowseTarget.allCases) { target in
                Button(action: { selection = target }) {
                    Text(target.title)
                        .font(.system(size: AdaptiveFont.subheadline, weight: selection == target ? .semibold : .regular))
                        .foregroundColor(selection == target ? .white : DXYColors.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, ScaleFactor.padding(10))
                        .background(selection == target ? DXYColors.primaryPurple : Color.clear)
                }
                .buttonStyle(.plain)
            }
        }
        .background(DXYColors.searchBackground)
        .clipShape(Capsule())
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, ScaleFactor.padding(8))
        .background(Color.white)
    }
}

struct HomeView: View {
    @State private var selectedTab = 0
    @State private var browseSelection: BrowseTarget = .disease
    
    init() {
        // 自定义 TabBar 外观
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor.white
        appearance.shadowColor = UIColor.black.withAlphaComponent(0.06)
        
        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
    }
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // 首页
            HomeContentView(selectedTab: $selectedTab, browseSelection: $browseSelection)
                .tabItem {
                    Image(systemName: selectedTab == 0 ? "house.fill" : "house")
                    Text("首页")
                }
                .tag(0)
            
            // 问医生
            CompatibleNavigationStack {
                AskDoctorView()
            }
            .tabItem {
                Image(systemName: selectedTab == 1 ? "plus.square.fill" : "plus.square")
                Text("问医生")
            }
            .tag(1)
            
            // 病历资料夹
            CompatibleNavigationStack {
                MedicalDossierView()
            }
            .tabItem {
                Image(systemName: selectedTab == 2 ? "folder.fill" : "folder")
                Text("病历")
            }
            .tag(2)
            
            // 查病查药
            CompatibleNavigationStack {
                DiseaseDrugBrowseView(selection: $browseSelection)
                    .navigationBarBackgroundHidden()
            }
            .tabItem {
                Image(systemName: selectedTab == 3 ? "magnifyingglass.circle.fill" : "magnifyingglass.circle")
                Text("查病查药")
            }
            .tag(3)
            
            // 我的
            CompatibleNavigationStack {
                ProfileView()
            }
            .tabItem {
                Image(systemName: selectedTab == 4 ? "person.fill" : "person")
                Text("我的")
            }
            .tag(4)
        }
        .tint(DXYColors.primaryPurple)
    }
}

// MARK: - 首页内容视图
struct HomeContentView: View {
    @Binding var selectedTab: Int
    @Binding var browseSelection: BrowseTarget
    @State private var searchText = ""
    
    var body: some View {
        ZStack {
            // 背景
            DXYColors.background
                .ignoresSafeArea()
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: AdaptiveSpacing.section) {
                    // 品牌信息行
                    BrandHeaderView()
                        .padding(.top, 8)
                    
                    // 搜索区域
                    SearchSectionView(searchText: $searchText)
                    
                    // 三个核心功能入口
                    CoreFunctionsView(selectedTab: $selectedTab, browseSelection: $browseSelection)
                    
                    // AI智能体入口
                    AIFeaturesSection()
                    
                    // 科室网格
                    DepartmentGridView()
                }
                .padding(.horizontal, LayoutConstants.horizontalPadding)
                .padding(.bottom, adaptiveBottomPadding)
            }
        }
        .navigationBarHidden(true)
    }
    
    private var adaptiveBottomPadding: CGFloat {
        ScaleFactor.padding(20)
    }
}

// MARK: - 占位视图
struct PlaceholderView: View {
    let title: String
    let icon: String
    
    var body: some View {
        ZStack {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: ScaleFactor.spacing(16)) {
                Image(systemName: SFSymbolResolver.resolve(icon))
                    .font(.system(size: AdaptiveFont.custom(48)))
                    .foregroundColor(DXYColors.textTertiary)
                Text(title)
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textSecondary)
                Text("功能开发中...")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
            }
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
    }
}


// MARK: - 品牌信息头部
struct BrandHeaderView: View {
    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                Text("鑫琳医生")
                    .font(.system(size: AdaptiveFont.largeTitle, weight: .bold))
                    .foregroundColor(DXYColors.textPrimary)
                
                HStack(spacing: ScaleFactor.spacing(6)) {
                    HStack(spacing: ScaleFactor.spacing(3)) {
                        Image(systemName: "checkmark.seal.fill")
                            .font(.system(size: AdaptiveFont.caption))
                        Text("专业医疗")
                    }
                    .foregroundColor(DXYColors.primaryPurple)
                    .padding(.horizontal, ScaleFactor.padding(8))
                    .padding(.vertical, ScaleFactor.padding(4))
                    .background(DXYColors.lightPurple)
                    .clipShape(Capsule())
                    
                    HStack(spacing: ScaleFactor.spacing(3)) {
                        Image(systemName: "heart.fill")
                            .font(.system(size: AdaptiveFont.caption))
                        Text("贴心服务")
                    }
                    .foregroundColor(DXYColors.teal)
                    .padding(.horizontal, ScaleFactor.padding(8))
                    .padding(.vertical, ScaleFactor.padding(4))
                    .background(DXYColors.teal.opacity(0.15))
                    .clipShape(Capsule())
                }
                .font(.system(size: AdaptiveFont.footnote, weight: .medium))
            }
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "envelope")
                    .font(.system(size: AdaptiveFont.title2, weight: .regular))
                    .foregroundColor(DXYColors.textTertiary)
            }
        }
    }
}

// MARK: - 搜索区域
struct SearchSectionView: View {
    @Binding var searchText: String
    
    let tags = ["每日辟谣", "奥司他韦", "甲流", "玛巴洛沙韦", "湿疹"]
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            // 搜索框
            HStack(spacing: 0) {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(DXYColors.textTertiary)
                    
                    TextField("疾病 / 症状 / 药品 / 问题", text: $searchText)
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DXYColors.textPrimary)
                }
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.vertical, ScaleFactor.padding(12))
                .background(DXYColors.searchBackground)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                
                Button(action: {}) {
                    Text("搜索")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, ScaleFactor.padding(16))
                        .padding(.vertical, ScaleFactor.padding(12))
                        .background(DXYColors.primaryPurple)
                        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                }
                .padding(.leading, ScaleFactor.padding(8))
            }
            
            // 标签
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    ForEach(tags, id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textSecondary)
                            .padding(.horizontal, ScaleFactor.padding(12))
                            .padding(.vertical, ScaleFactor.padding(6))
                            .background(DXYColors.tagBackground)
                            .clipShape(Capsule())
                    }
                }
            }
        }
    }
}

// MARK: - 核心功能入口
struct CoreFunctionsView: View {
    @Binding var selectedTab: Int
    @Binding var browseSelection: BrowseTarget
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(24)) {
            CoreFunctionItem(
                icon: "plus.bubble",
                title: "问医生",
                subtitle: "全国三甲...",
                backgroundColor: DXYColors.teal,
                action: { selectedTab = 1 }
            )
            
            CoreFunctionItem(
                icon: "stethoscope",
                title: "查疾病",
                subtitle: "权威疾病...",
                backgroundColor: Color(red: 0.42, green: 0.42, blue: 1.0),
                action: {
                    browseSelection = .disease
                    selectedTab = 3
                }
            )
            
            CoreFunctionItem(
                icon: "pills",
                title: "查药品",
                subtitle: "7万药品说...",
                backgroundColor: DXYColors.blue,
                action: {
                    browseSelection = .drug
                    selectedTab = 3
                }
            )
        }
        .padding(.top, 8)
    }
}

struct CoreFunctionItem: View {
    let icon: String
    let title: String
    let subtitle: String
    let backgroundColor: Color
    var action: () -> Void = {}
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: ScaleFactor.spacing(8)) {
                ZStack {
                    Circle()
                        .fill(backgroundColor)
                        .frame(width: ScaleFactor.size(64), height: ScaleFactor.size(64))
                    
                    Image(systemName: icon)
                        .font(.system(size: AdaptiveFont.largeTitle, weight: .light))
                        .foregroundColor(.white)
                }
                
                Text(title)
                    .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Text(subtitle)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textTertiary)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(PlainButtonStyle())
        .scaleEffect(isPressed ? 0.96 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}


// MARK: - AI智能体功能区
struct AIFeaturesSection: View {
    @State private var showConsultation = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            Text("AI智能问诊")
                .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
            
            // 智能问诊入口（连接真实后端 API）
            Button(action: { showConsultation = true }) {
                HStack(spacing: 12) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [DXYColors.blue, DXYColors.teal],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 48, height: 48)
                        
                        Image(systemName: "brain.head.profile")
                            .font(.system(size: 22, weight: .medium))
                            .foregroundColor(.white)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Text("科室智能体问诊")
                                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                                .foregroundColor(DXYColors.textPrimary)
                            
                            Text("AI")
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(.white)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(DXYColors.blue)
                                .clipShape(Capsule())
                        }
                        
                        Text("智能问诊，支持皮肤分析和报告解读")
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textSecondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.right")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(DXYColors.textTertiary)
                }
                .padding(14)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .shadow(color: Color.black.opacity(0.06), radius: 8, y: 2)
            }
            .buttonStyle(PlainButtonStyle())
            .fullScreenCover(isPresented: $showConsultation) {
                ModernConsultationView(doctor: .demo)
            }
        }
    }
}

// MARK: - 科室网格（从 API 加载）
struct DepartmentGridView: View {
    @State private var departments: [DepartmentModel] = []
    @State private var isLoading = false
    @State private var selectedDepartment: DepartmentModel?
    
    let columns = [
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible())
    ]
    
    var body: some View {
        VStack {
            if isLoading {
                ProgressView()
                    .frame(height: 120)
            } else if departments.isEmpty {
                Text("加载科室中...")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
                    .frame(height: ScaleFactor.size(120))
            } else {
                LazyVGrid(columns: columns, spacing: ScaleFactor.spacing(20)) {
                    ForEach(displayDepartments) { dept in
                        DepartmentItem(
                            icon: SFSymbolResolver.resolve(dept.icon),
                            name: dept.name,
                            badge: nil
                        )
                        .onTapGesture {
                            selectedDepartment = dept
                        }
                    }
                    // 更多科室入口
                    DepartmentItem(icon: "square.grid.2x2", name: "更多科室", badge: nil)
                }
            }
        }
        .padding(.vertical, ScaleFactor.padding(16))
        .padding(.horizontal, ScaleFactor.padding(8))
        .background(DXYColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        .onAppear {
            loadDepartments()
        }
        .navigationDestinationCompat(item: $selectedDepartment) { dept in
            DepartmentDetailView(departmentName: dept.name, departmentId: dept.id)
        }
    }
    
    // 只显示前 7 个科室
    private var displayDepartments: [DepartmentModel] {
        Array(departments.prefix(7))
    }
    
    private func loadDepartments() {
        guard departments.isEmpty else { return }
        isLoading = true
        
        Task {
            do {
                let depts = try await APIService.shared.getDepartments()
                await MainActor.run {
                    departments = depts
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

struct DepartmentItem: View {
    let icon: String
    let name: String
    let badge: String?
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(8)) {
            ZStack(alignment: .topTrailing) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.largeTitle, weight: .light))
                    .foregroundColor(DXYColors.primaryPurple)
                    .frame(width: ScaleFactor.size(48), height: ScaleFactor.size(48))
                
                if let badge = badge {
                    Text(badge)
                        .font(.system(size: AdaptiveFont.custom(9), weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, ScaleFactor.padding(4))
                        .padding(.vertical, ScaleFactor.padding(2))
                        .background(badge == "流感" ? Color.red : DXYColors.orange)
                        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(4)))
                        .offset(x: ScaleFactor.size(8), y: ScaleFactor.size(-4))
                }
            }
            
            Text(name)
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textPrimary)
                .lineLimit(1)
        }
    }
}

// MARK: - Preview
#Preview {
    HomeView()
}
