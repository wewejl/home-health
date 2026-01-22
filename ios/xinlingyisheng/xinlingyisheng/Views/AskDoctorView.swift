import SwiftUI

// MARK: - 问医生页面主视图
struct AskDoctorView: View {
    @State private var searchText = ""
    @State private var selectedDepartment: DepartmentModel?
    @State private var showMyQuestions = false
    // API数据状态
    @State private var departments: [DepartmentModel] = []
    @State private var isLoadingDepartments = false
    @State private var departmentError: String?
    @State private var showError = false
    
    var body: some View {
        ZStack(alignment: .top) {
            // 背景
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 自定义导航栏
                AskDoctorNavBar(showMyQuestions: $showMyQuestions)
                
                if isLoadingDepartments {
                    Spacer()
                    ProgressView("加载科室中...")
                        .progressViewStyle(CircularProgressViewStyle())
                    Spacer()
                } else if departments.isEmpty {
                    Spacer()
                    VStack(spacing: ScaleFactor.spacing(12)) {
                        Image(systemName: "building.2.slash")
                            .font(.system(size: AdaptiveFont.custom(48)))
                            .foregroundColor(DXYColors.textTertiary)
                        Text("暂无科室数据")
                            .font(.system(size: AdaptiveFont.body))
                            .foregroundColor(DXYColors.textSecondary)
                        Button("点击重试") {
                            loadDepartments()
                        }
                        .foregroundColor(DXYColors.primaryPurple)
                    }
                    Spacer()
                } else {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(spacing: AdaptiveSpacing.section) {
                            // 搜索区域
                            AskDoctorSearchView(searchText: $searchText)
                            
                            // 信任标签
                            TrustBadgesView()

                            // 科室列表（从 API 加载）
                            DepartmentListView(
                                departments: filteredDepartments,
                                selectedDepartment: $selectedDepartment
                            )
                            
                            // 底部品牌区
                            BrandFooterView()
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                        .padding(.bottom, adaptiveBottomPadding)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .navigationDestinationCompat(item: $selectedDepartment) { dept in
            DepartmentDetailView(departmentName: dept.name, departmentId: dept.id)
        }
        .navigationDestinationCompat(isPresented: $showMyQuestions) {
            MyQuestionsView()
        }
        .onAppear {
            if departments.isEmpty {
                loadDepartments()
            }
        }
        .alert("提示", isPresented: $showError) {
            Button("重试") { loadDepartments() }
            Button("取消", role: .cancel) {}
        } message: {
            Text(departmentError ?? "加载失败")
        }
    }
    
    // 搜索过滤
    private var filteredDepartments: [DepartmentModel] {
        if searchText.isEmpty {
            return departments
        }
        return departments.filter { dept in
            dept.name.contains(searchText) ||
            (dept.description?.contains(searchText) ?? false)
        }
    }
    
    // 加载科室数据
    private func loadDepartments() {
        isLoadingDepartments = true
        departmentError = nil
        
        Task {
            do {
                let departmentModels = try await APIService.shared.getDepartments()
                await MainActor.run {
                    departments = departmentModels
                    isLoadingDepartments = false
                }
            } catch let error as APIError {
                await MainActor.run {
                    isLoadingDepartments = false
                    departmentError = error.errorDescription
                    showError = true
                }
            } catch {
                await MainActor.run {
                    isLoadingDepartments = false
                    departmentError = "网络连接失败"
                    showError = true
                }
            }
        }
    }
    
    private var adaptiveBottomPadding: CGFloat {
        ScaleFactor.padding(40)
    }
}

// MARK: - 科室列表视图（使用 API 数据）
struct DepartmentListView: View {
    let departments: [DepartmentModel]
    @Binding var selectedDepartment: DepartmentModel?
    
    let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12)
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(16)) {
            Text("全部科室")
                .font(.system(size: AdaptiveFont.title3, weight: .bold))
                .foregroundColor(DXYColors.textPrimary)
            
            LazyVGrid(columns: columns, spacing: ScaleFactor.spacing(12)) {
                ForEach(departments) { dept in
                    DepartmentCardView(department: dept) {
                        selectedDepartment = dept
                    }
                }
            }
        }
        .padding(ScaleFactor.padding(16))
        .background(DXYColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
    }
}

// MARK: - 科室卡片视图
struct DepartmentCardView: View {
    let department: DepartmentModel
    var onTap: () -> Void = {}
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: ScaleFactor.spacing(10)) {
                // 左侧图标
                Image(systemName: SFSymbolResolver.resolve(department.icon))
                    .font(.system(size: AdaptiveFont.title1, weight: .light))
                    .foregroundColor(DXYColors.primaryPurple)
                    .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    Text(department.name)
                        .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                        .foregroundColor(DXYColors.textPrimary)
                        .lineLimit(1)
                    
                    if let desc = department.description {
                        Text(desc)
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.textTertiary)
                            .lineLimit(2)
                            .multilineTextAlignment(.leading)
                    }
                }
                
                Spacer(minLength: 0)
            }
            .padding(ScaleFactor.padding(12))
            .frame(maxWidth: .infinity, minHeight: ScaleFactor.size(70), alignment: .topLeading)
            .background(DXYColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                    .stroke(Color.gray.opacity(0.1), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - 自定义导航栏
struct AskDoctorNavBar: View {
    @Binding var showMyQuestions: Bool
    
    var body: some View {
        Text("问医生")
            .font(.system(size: AdaptiveFont.title3, weight: .semibold))
            .foregroundColor(DXYColors.textPrimary)
            .frame(maxWidth: .infinity)
            .overlay(alignment: .trailing) {
                Button(action: { showMyQuestions = true }) {
                    Text("我的提问")
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DXYColors.textSecondary)
                }
            }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(DXYColors.cardBackground)
    }
}

// MARK: - 搜索区域
struct AskDoctorSearchView: View {
    @Binding var searchText: String
    
    let hotTags = ["血糖监测", "血压管理", "感冒发烧", "皮肤问题", "儿童健康"]
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            // 搜索框
            HStack(spacing: ScaleFactor.spacing(8)) {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(DXYColors.textTertiary)
                    
                    TextField("疾病 / 症状 / 医院 / 医生名", text: $searchText)
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DXYColors.textPrimary)
                }
                .padding(.horizontal, ScaleFactor.padding(14))
                .padding(.vertical, ScaleFactor.padding(12))
                .background(DXYColors.searchBackground)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                
                Button(action: {}) {
                    Text("搜索")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, ScaleFactor.padding(18))
                        .padding(.vertical, ScaleFactor.padding(12))
                        .background(DXYColors.primaryPurple)
                        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                }
            }
            
            // 热搜标签
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    ForEach(hotTags, id: \.self) { tag in
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
        .padding(.top, ScaleFactor.padding(8))
    }
}

// MARK: - 信任标签
struct TrustBadgesView: View {
    let badges = [
        ("checkmark.seal.fill", "医生实名认证"),
        ("shield.checkered", "平台双重质控"),
        ("clock.fill", "医生7×24h在线")
    ]
    
    var body: some View {
        HStack(spacing: 0) {
            ForEach(badges, id: \.1) { icon, text in
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Image(systemName: icon)
                        .font(.system(size: AdaptiveFont.caption))
                    Text(text)
                        .font(.system(size: AdaptiveFont.footnote))
                }
                .foregroundColor(DXYColors.textTertiary)
                
                if text != badges.last?.1 {
                    Spacer()
                }
            }
        }
        .padding(.horizontal, ScaleFactor.padding(4))
    }
}


// MARK: - 底部品牌区
struct BrandFooterView: View {
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "cross.fill")
                    .font(.system(size: AdaptiveFont.subheadline))
                Text("鑫琳医生")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
            }
            .foregroundColor(DXYColors.primaryPurple.opacity(0.6))
            
            Text("一起发现健康生活")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(.top, ScaleFactor.padding(24))
        .padding(.bottom, ScaleFactor.padding(16))
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        AskDoctorView()
    }
}
