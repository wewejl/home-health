import SwiftUI

// MARK: - 科室详情页（医生列表）
struct DepartmentDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let departmentName: String
    let departmentId: Int?
    
    @State private var searchText = ""
    @State private var selectedSortIndex = 0
    @State private var selectedRegion = "全国"
    @State private var selectedDoctor: DoctorInfo?
    
    // 数据加载状态
    @State private var doctors: [DoctorInfo] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showError = false
    
    // 支持仅传入 departmentName 的初始化（向后兼容）
    init(departmentName: String, departmentId: Int? = nil) {
        self.departmentName = departmentName
        self.departmentId = departmentId
    }
    
    var body: some View {
        ZStack(alignment: .top) {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 导航栏
                DepartmentNavBar(title: departmentName, dismiss: dismiss)
                
                if isLoading {
                    Spacer()
                    ProgressView("加载中...")
                        .progressViewStyle(CircularProgressViewStyle())
                    Spacer()
                } else if doctors.isEmpty {
                    Spacer()
                    VStack(spacing: ScaleFactor.spacing(12)) {
                        Image(systemName: "person.2.slash")
                            .font(.system(size: AdaptiveFont.custom(48)))
                            .foregroundColor(DXYColors.textTertiary)
                        Text("暂无医生数据")
                            .font(.system(size: AdaptiveFont.body))
                            .foregroundColor(DXYColors.textSecondary)
                        if departmentId != nil {
                            Button("点击重试") {
                                loadDoctors()
                            }
                            .foregroundColor(DXYColors.primaryPurple)
                        }
                    }
                    Spacer()
                } else {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(spacing: 16) {
                            // 搜索框
                            DepartmentSearchBar(searchText: $searchText)
                            
                            // 筛选栏
                            FilterBarView()
                            
                            // 快捷筛选标签
                            QuickFilterTagsView()
                            
                            // 医生列表
                            LazyVStack(spacing: 0) {
                                ForEach(filteredDoctors) { doctor in
                                    DoctorCardView(doctor: doctor, onAskDoctor: {
                                        selectedDoctor = doctor
                                    })
                                    
                                    if doctor.id != filteredDoctors.last?.id {
                                        Divider()
                                            .padding(.horizontal, 16)
                                    }
                                }
                            }
                            .background(DXYColors.cardBackground)
                            .clipShape(RoundedRectangle(cornerRadius: LayoutConstants.cornerRadius, style: .continuous))
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                        .padding(.bottom, adaptiveBottomPadding)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .navigationDestinationCompat(item: $selectedDoctor) { doctor in
            ModernConsultationView(
                doctorId: doctor.id,
                doctorName: doctor.name,
                department: departmentName,
                doctorTitle: doctor.title,
                doctorBio: doctor.intro ?? "专业医生，为您提供优质医疗服务"
            )
        }
        .onAppear {
            loadDoctors()
        }
        .alert("提示", isPresented: $showError) {
            Button("重试") {
                loadDoctors()
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "加载失败")
        }
    }
    
    private var adaptiveBottomPadding: CGFloat {
        ScaleFactor.padding(40)
    }
    
    // 搜索过滤
    private var filteredDoctors: [DoctorInfo] {
        if searchText.isEmpty {
            return doctors
        }
        return doctors.filter { doctor in
            doctor.name.contains(searchText) ||
            doctor.hospital.contains(searchText) ||
            doctor.specialty.contains(searchText)
        }
    }
    
    // 加载医生数据
    private func loadDoctors() {
        // 如果没有 departmentId，显示错误信息
        guard let deptId = departmentId else {
            errorMessage = "科室ID缺失，无法加载医生数据"
            showError = true
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let doctorModels = try await APIService.shared.getDoctors(departmentId: deptId)
                await MainActor.run {
                    if doctorModels.isEmpty {
                        errorMessage = "该科室暂无医生数据"
                    } else {
                        doctors = doctorModels.map { DoctorInfo(from: $0, departmentName: departmentName) }
                    }
                    isLoading = false
                }
            } catch let error as APIError {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.errorDescription
                    showError = true
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = "网络连接失败"
                    showError = true
                }
            }
        }
    }
}

// MARK: - 医生信息模型（仅映射后端字段）
struct DoctorInfo: Identifiable, Hashable {
    static func == (lhs: DoctorInfo, rhs: DoctorInfo) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    let doctorId: Int
    var id: Int { doctorId }
    let name: String
    let title: String
    let canPrescribe: Bool
    let isTopHospital: Bool
    let hospital: String
    let department: String
    let specialty: String
    let intro: String?
    let rating: Double
    let monthlyAnswers: Int
    let avgResponseTime: String
    
    // UI 展示用字段（使用默认值，后端可扩展）
    var badges: [String] { [] }
    var avatarColor: Color {
        let colors: [Color] = [.blue, .purple, .pink, .orange, .green, .cyan]
        return colors[doctorId % colors.count].opacity(0.3)
    }
    var hasRecommendBadge: Bool { doctorId % 2 == 0 }
    
    // 从 API 模型初始化
    init(from model: DoctorModel, departmentName: String) {
        self.doctorId = model.id
        self.name = model.name
        self.title = model.title ?? "主治医师"
        self.canPrescribe = model.can_prescribe
        self.isTopHospital = model.is_top_hospital
        self.hospital = model.hospital ?? "未知医院"
        self.department = departmentName
        self.specialty = model.specialty ?? ""
        self.intro = model.intro
        self.rating = model.rating
        self.monthlyAnswers = model.monthly_answers
        self.avgResponseTime = model.avg_response_time
    }
}

// MARK: - 科室导航栏
struct DepartmentNavBar: View {
    let title: String
    let dismiss: DismissAction
    
    var body: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .contentShape(Rectangle())
            }
            
            Spacer()
            
            Text(title)
                .font(.system(size: AdaptiveFont.title3, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "square.and.pencil")
                    .font(.system(size: AdaptiveFont.title3, weight: .regular))
                    .foregroundColor(DXYColors.textPrimary)
            }
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(DXYColors.cardBackground)
    }
}

// MARK: - 搜索框
struct DepartmentSearchBar: View {
    @Binding var searchText: String
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: AdaptiveFont.body))
                .foregroundColor(DXYColors.textTertiary)
            
            TextField("疾病 / 症状 / 医院 / 医生名", text: $searchText)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(DXYColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusLarge, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusLarge, style: .continuous)
                .stroke(Color.gray.opacity(0.15), lineWidth: 1)
        )
        .padding(.top, ScaleFactor.padding(8))
    }
}

// MARK: - 筛选栏
struct FilterBarView: View {
    let filters = [
        ("综合排序", true),
        ("全国", true),
        ("医生擅长", true),
        ("筛选", false)
    ]
    
    var body: some View {
        HStack(spacing: 0) {
            ForEach(filters, id: \.0) { filter, hasDropdown in
                Button(action: {}) {
                    HStack(spacing: ScaleFactor.spacing(4)) {
                        Text(filter)
                            .font(.system(size: AdaptiveFont.subheadline))
                            .foregroundColor(filter == "筛选" ? DXYColors.primaryPurple : DXYColors.textSecondary)
                        
                        if hasDropdown {
                            Image(systemName: "chevron.down")
                                .font(.system(size: AdaptiveFont.custom(10), weight: .medium))
                                .foregroundColor(DXYColors.textTertiary)
                        } else {
                            Image(systemName: "slider.horizontal.3")
                                .font(.system(size: AdaptiveFont.footnote))
                                .foregroundColor(DXYColors.primaryPurple)
                        }
                    }
                }
                
                if filter != "筛选" {
                    Spacer()
                }
            }
        }
        .padding(.horizontal, 4)
    }
}

// MARK: - 快捷筛选标签
struct QuickFilterTagsView: View {
    @State private var selectedTags: Set<String> = []
    
    let tags = [
        ("crown.fill", "新人专享价", DXYColors.orange),
        ("yensign.circle.fill", "49元以下", DXYColors.teal),
        ("person.fill", "只看主任", DXYColors.primaryPurple)
    ]
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(tags, id: \.1) { icon, text, color in
                    Button(action: {
                        if selectedTags.contains(text) {
                            selectedTags.remove(text)
                        } else {
                            selectedTags.insert(text)
                        }
                    }) {
                        HStack(spacing: ScaleFactor.spacing(4)) {
                            Image(systemName: icon)
                                .font(.system(size: AdaptiveFont.footnote))
                            Text(text)
                                .font(.system(size: AdaptiveFont.footnote))
                        }
                        .foregroundColor(selectedTags.contains(text) ? .white : color)
                        .padding(.horizontal, ScaleFactor.padding(12))
                        .padding(.vertical, ScaleFactor.padding(8))
                        .background(
                            selectedTags.contains(text) ? color : color.opacity(0.12)
                        )
                        .clipShape(Capsule())
                    }
                }
            }
        }
    }
}

// MARK: - 医生卡片
struct DoctorCardView: View {
    let doctor: DoctorInfo
    var onAskDoctor: () -> Void = {}
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            // 顶部：头像 + 基本信息
            HStack(alignment: .top, spacing: ScaleFactor.spacing(12)) {
                // 头像
                ZStack(alignment: .bottomLeading) {
                    Circle()
                        .fill(doctor.avatarColor)
                        .frame(width: ScaleFactor.size(56), height: ScaleFactor.size(56))
                        .overlay(
                            Image(systemName: "person.fill")
                                .font(.system(size: AdaptiveFont.title1))
                                .foregroundColor(.white)
                        )
                    
                    if doctor.hasRecommendBadge {
                        Text("患者力荐")
                            .font(.system(size: AdaptiveFont.custom(8), weight: .medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, ScaleFactor.padding(4))
                            .padding(.vertical, ScaleFactor.padding(2))
                            .background(DXYColors.orange)
                            .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(4)))
                            .offset(x: ScaleFactor.size(-4), y: ScaleFactor.size(4))
                    }
                }
                
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                    // 姓名 + 职称 + 标签
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Text(doctor.name)
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                            .foregroundColor(DXYColors.textPrimary)
                        
                        Text(doctor.title)
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textSecondary)
                        
                        if doctor.canPrescribe {
                            Text("可开处方")
                                .font(.system(size: AdaptiveFont.caption, weight: .medium))
                                .foregroundColor(DXYColors.primaryPurple)
                                .padding(.horizontal, ScaleFactor.padding(6))
                                .padding(.vertical, ScaleFactor.padding(2))
                                .background(DXYColors.lightPurple)
                                .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(4)))
                        }
                        
                        if doctor.isTopHospital {
                            Text("三甲")
                                .font(.system(size: AdaptiveFont.caption, weight: .medium))
                                .foregroundColor(DXYColors.teal)
                                .padding(.horizontal, ScaleFactor.padding(6))
                                .padding(.vertical, ScaleFactor.padding(2))
                                .background(DXYColors.teal.opacity(0.15))
                                .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(4)))
                        }
                    }
                    
                    // 医院 + 科室
                    HStack(spacing: ScaleFactor.spacing(8)) {
                        Text(doctor.hospital)
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textSecondary)
                            .lineLimit(1)
                        
                        Text(doctor.department)
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textSecondary)
                    }
                    
                    // 擅长
                    Text("擅长：\(doctor.specialty)")
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textSecondary)
                        .lineLimit(1)
                }
                
                Spacer(minLength: 0)
            }
            
            // 评分 + 回答数 + 响应时间
            HStack(spacing: ScaleFactor.spacing(12)) {
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Text("用户评分")
                        .foregroundColor(DXYColors.textTertiary)
                    Text(String(format: "%.2f", doctor.rating))
                        .foregroundColor(DXYColors.orange)
                        .fontWeight(.medium)
                }
                
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Text("月回答")
                        .foregroundColor(DXYColors.textTertiary)
                    Text("\(doctor.monthlyAnswers)")
                        .foregroundColor(DXYColors.orange)
                        .fontWeight(.medium)
                }
                
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Text("平...")
                        .foregroundColor(DXYColors.textTertiary)
                    Text(doctor.avgResponseTime)
                        .foregroundColor(DXYColors.teal)
                        .fontWeight(.medium)
                }
            }
            .font(.system(size: AdaptiveFont.footnote))
            
            // 徽章标签
            if !doctor.badges.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: ScaleFactor.spacing(8)) {
                        ForEach(doctor.badges, id: \.self) { badge in
                            Text(badge)
                                .font(.system(size: AdaptiveFont.caption))
                                .foregroundColor(DXYColors.textTertiary)
                                .padding(.horizontal, ScaleFactor.padding(8))
                                .padding(.vertical, ScaleFactor.padding(4))
                                .background(DXYColors.tagBackground)
                                .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(4)))
                        }
                    }
                }
            }
            
            // 底部：问医生按钮
            HStack {
                Spacer()
                
                Button(action: onAskDoctor) {
                    Text("问医生")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DXYColors.primaryPurple)
                        .padding(.horizontal, ScaleFactor.padding(20))
                        .padding(.vertical, ScaleFactor.padding(10))
                        .background(DXYColors.lightPurple)
                        .clipShape(Capsule())
                }
            }
        }
        .padding(ScaleFactor.padding(16))
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DepartmentDetailView(departmentName: "皮肤科")
    }
}
