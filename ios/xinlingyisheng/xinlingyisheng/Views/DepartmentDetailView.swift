import SwiftUI

// MARK: - 科室详情页（治愈系风格）
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
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack(alignment: .top) {
                // 治愈系背景
                HealingDepartmentBackground(layout: layout)

                VStack(spacing: 0) {
                    // 导航栏
                    HealingDepartmentNavBar(
                        title: departmentName,
                        dismiss: dismiss,
                        layout: layout
                    )

                    if isLoading {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ProgressView()
                                .tint(HealingColors.forestMist)
                                .scaleEffect(1.2)
                            Text("加载医生中...")
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                        Spacer()
                    } else if doctors.isEmpty {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            ZStack {
                                Circle()
                                    .fill(HealingColors.forestMist.opacity(0.1))
                                    .frame(width: layout.iconLargeSize * 2, height: layout.iconLargeSize * 2)

                                Image(systemName: "person.2.slash")
                                    .font(.system(size: layout.titleFontSize, weight: .light))
                                    .foregroundColor(HealingColors.forestMist.opacity(0.6))
                            }

                            Text("暂无医生数据")
                                .font(.system(size: layout.bodyFontSize))
                                .foregroundColor(HealingColors.textSecondary)

                            if departmentId != nil {
                                Button(action: { loadDoctors() }) {
                                    HStack(spacing: layout.cardSpacing / 2) {
                                        Image(systemName: "arrow.clockwise")
                                            .font(.system(size: layout.captionFontSize))
                                        Text("点击重试")
                                            .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                                    }
                                    .foregroundColor(.white)
                                    .padding(.horizontal, layout.cardInnerPadding + 4)
                                    .padding(.vertical, layout.cardInnerPadding - 2)
                                    .background(
                                        LinearGradient(
                                            colors: [HealingColors.deepSage, HealingColors.forestMist],
                                            startPoint: .leading,
                                            endPoint: .trailing
                                        )
                                    )
                                    .clipShape(Capsule())
                                }
                            }
                        }
                        Spacer()
                    } else {
                        ScrollView(.vertical, showsIndicators: false) {
                            VStack(spacing: layout.cardSpacing) {
                                // 搜索框
                                HealingDepartmentSearchBar(
                                    searchText: $searchText,
                                    layout: layout
                                )

                                // 筛选栏
                                HealingFilterBarView(layout: layout)

                                // 快捷筛选标签
                                HealingQuickFilterTagsView(layout: layout)

                                // 医生列表
                                LazyVStack(spacing: layout.cardSpacing / 2) {
                                    ForEach(filteredDoctors) { doctor in
                                        HealingDoctorCardView(
                                            doctor: doctor,
                                            layout: layout,
                                            onAskDoctor: {
                                                selectedDoctor = doctor
                                            }
                                        )
                                        .fluidFadeIn(delay: 0.05)
                                    }
                                }
                                .padding(.top, layout.cardSpacing / 2)
                            }
                            .padding(.horizontal, layout.horizontalPadding)
                            .padding(.bottom, adaptiveBottomPadding(layout: layout))
                        }
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
            Button("重试") { loadDoctors() }
            Button("取消", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "加载失败")
        }
    }

    private func adaptiveBottomPadding(layout: AdaptiveLayout) -> CGFloat {
        layout.cardInnerPadding * 8
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

// MARK: - 治愈系科室背景
struct HealingDepartmentBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.5),
                    HealingColors.warmSand.opacity(0.3)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 右上角光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geo.size.width * 0.4, y: -geo.size.height * 0.15)
                    .ignoresSafeArea()

                // 左下角光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.35, height: layout.decorativeCircleSize * 0.35)
                    .offset(x: -geo.size.width * 0.25, y: geo.size.height * 0.35)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系科室导航栏
struct HealingDepartmentNavBar: View {
    let title: String
    let dismiss: DismissAction
    let layout: AdaptiveLayout

    var body: some View {
        HStack {
            Button(action: { dismiss() }) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)

                    Image(systemName: "chevron.left")
                        .font(.system(size: layout.captionFontSize + 2, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)
            }

            Spacer()

            Text(title)
                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Spacer()

            Button(action: {}) {
                ZStack {
                    Circle()
                        .fill(HealingColors.cardBackground)
                        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)

                    Image(systemName: "square.and.pencil")
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
                .frame(width: layout.iconSmallSize + 8, height: layout.iconSmallSize + 8)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding)
        .background(HealingColors.cardBackground.opacity(0.8))
        .background(
            Rectangle()
                .fill(HealingColors.cardBackground.opacity(0.8))
                .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: 2)
        )
    }
}

// MARK: - 治愈系搜索框
struct HealingDepartmentSearchBar: View {
    @Binding var searchText: String
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: layout.bodyFontSize - 2))
                .foregroundColor(HealingColors.textTertiary)

            TextField("搜索医生 / 医院 / 擅长疾病", text: $searchText)
                .font(.system(size: layout.bodyFontSize - 2))
                .foregroundColor(HealingColors.textPrimary)

            if !searchText.isEmpty {
                Button(action: { searchText = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: layout.captionFontSize + 2))
                        .foregroundColor(HealingColors.textTertiary)
                }
            }
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardInnerPadding - 2)
        .background(HealingColors.warmCream.opacity(0.6))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系筛选栏
struct HealingFilterBarView: View {
    let layout: AdaptiveLayout

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
                    HStack(spacing: 4) {
                        Text(filter)
                            .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                            .foregroundColor(filter == "筛选" ? HealingColors.forestMist : HealingColors.textSecondary)

                        if hasDropdown {
                            Image(systemName: "chevron.down")
                                .font(.system(size: layout.captionFontSize - 2, weight: .semibold))
                                .foregroundColor(HealingColors.textTertiary)
                        } else {
                            Image(systemName: "slider.horizontal.3")
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.forestMist)
                        }
                    }
                }
                .buttonStyle(.plain)

                if filter != "筛选" {
                    Spacer()
                }
            }
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardInnerPadding - 2)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: Color.black.opacity(0.02), radius: 4, x: 0, y: 2)
    }
}

// MARK: - 治愈系快捷筛选标签
struct HealingQuickFilterTagsView: View {
    @State private var selectedTags: Set<String> = []
    let layout: AdaptiveLayout

    let tags = [
        ("crown.fill", "新人专享价", HealingColors.terracotta),
        ("yensign.circle.fill", "优质价格", HealingColors.warmSand),
        ("person.fill", "主任专家", HealingColors.forestMist)
    ]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing / 2) {
                ForEach(tags, id: \.1) { icon, text, color in
                    Button(action: {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                            if selectedTags.contains(text) {
                                selectedTags.remove(text)
                            } else {
                                selectedTags.insert(text)
                            }
                        }
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: icon)
                                .font(.system(size: layout.captionFontSize))
                            Text(text)
                                .font(.system(size: layout.captionFontSize, weight: .medium))
                        }
                        .foregroundColor(selectedTags.contains(text) ? .white : color)
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.vertical, layout.cardSpacing / 2)
                        .background(
                            selectedTags.contains(text) ?
                            LinearGradient(
                                colors: [color, color.opacity(0.8)],
                                startPoint: .leading,
                                endPoint: .trailing
                            ) :
                            LinearGradient(
                                colors: [color.opacity(0.15), color.opacity(0.1)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .clipShape(Capsule())
                    }
                }
            }
        }
    }
}

// MARK: - 治愈系医生卡片
struct HealingDoctorCardView: View {
    let doctor: DoctorInfo
    let layout: AdaptiveLayout
    var onAskDoctor: () -> Void = {}

    @State private var isPressed = false

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 顶部：头像 + 基本信息
            HStack(alignment: .top, spacing: layout.cardSpacing) {
                // 头像
                ZStack(alignment: .bottomLeading) {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [doctor.avatarColor, doctor.avatarColor.opacity(0.6)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: layout.iconLargeSize + 8, height: layout.iconLargeSize + 8)
                        .overlay(
                            Circle()
                                .stroke(HealingColors.cardBackground, lineWidth: 2)
                        )
                        .shadow(color: doctor.avatarColor.opacity(0.3), radius: 8, x: 0, y: 4)

                    Image(systemName: "person.fill")
                        .font(.system(size: layout.bodyFontSize + 4))
                        .foregroundColor(.white)

                    if doctor.hasRecommendBadge {
                        HStack(spacing: 2) {
                            Image(systemName: "hand.thumbsup.fill")
                                .font(.system(size: layout.captionFontSize - 3))
                            Text("力荐")
                                .font(.system(size: layout.captionFontSize - 3, weight: .semibold))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 2)
                        .background(
                            Capsule()
                                .fill(HealingColors.terracotta)
                        )
                        .offset(x: -4, y: 4)
                    }
                }

                VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                    // 姓名 + 职称 + 标签
                    HStack(spacing: layout.cardSpacing / 3) {
                        Text(doctor.name)
                            .font(.system(size: layout.bodyFontSize + 1, weight: .semibold))
                            .foregroundColor(HealingColors.textPrimary)

                        Text(doctor.title)
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)

                        if doctor.canPrescribe {
                            HStack(spacing: 2) {
                                Image(systemName: "prescription")
                                    .font(.system(size: layout.captionFontSize - 2))
                                Text("处方")
                                    .font(.system(size: layout.captionFontSize - 2, weight: .medium))
                            }
                            .foregroundColor(HealingColors.forestMist)
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(HealingColors.softSage.opacity(0.25))
                            .clipShape(Capsule())
                        }

                        if doctor.isTopHospital {
                            Text("三甲")
                                .font(.system(size: layout.captionFontSize - 1, weight: .medium))
                                .foregroundColor(.white)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 2)
                                .background(
                                    Capsule()
                                        .fill(HealingColors.dustyBlue)
                                )
                        }
                    }

                    // 医院 + 科室
                    HStack(spacing: layout.cardSpacing / 2) {
                        Image(systemName: "building.2.fill")
                            .font(.system(size: layout.captionFontSize - 1))
                            .foregroundColor(HealingColors.textTertiary)

                        Text(doctor.hospital)
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                            .lineLimit(1)

                        Text("·")
                            .foregroundColor(HealingColors.textTertiary)

                        Text(doctor.department)
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                    }

                    // 擅长
                    HStack(spacing: 4) {
                        Image(systemName: "star.fill")
                            .font(.system(size: layout.captionFontSize - 2))
                            .foregroundColor(HealingColors.warmSand)

                        Text("擅长：\(doctor.specialty)")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.textSecondary)
                            .lineLimit(2)
                    }
                }

                Spacer(minLength: 0)
            }

            // 统计信息
            HStack(spacing: layout.cardSpacing) {
                // 评分
                HStack(spacing: 4) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.terracotta.opacity(0.15))
                            .frame(width: layout.iconSmallSize - 4, height: layout.iconSmallSize - 4)

                        Image(systemName: "heart.fill")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.terracotta)
                    }

                    VStack(alignment: .leading, spacing: 1) {
                        Text("评分")
                            .font(.system(size: layout.captionFontSize - 2))
                            .foregroundColor(HealingColors.textTertiary)
                        Text(String(format: "%.1f", doctor.rating))
                            .font(.system(size: layout.captionFontSize, weight: .semibold))
                            .foregroundColor(HealingColors.terracotta)
                    }
                }

                // 月回答
                HStack(spacing: 4) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.forestMist.opacity(0.15))
                            .frame(width: layout.iconSmallSize - 4, height: layout.iconSmallSize - 4)

                        Image(systemName: "bubble.left.fill")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.forestMist)
                    }

                    VStack(alignment: .leading, spacing: 1) {
                        Text("月回答")
                            .font(.system(size: layout.captionFontSize - 2))
                            .foregroundColor(HealingColors.textTertiary)
                        Text("\(doctor.monthlyAnswers)")
                            .font(.system(size: layout.captionFontSize, weight: .semibold))
                            .foregroundColor(HealingColors.forestMist)
                    }
                }

                // 响应时间
                HStack(spacing: 4) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.dustyBlue.opacity(0.15))
                            .frame(width: layout.iconSmallSize - 4, height: layout.iconSmallSize - 4)

                        Image(systemName: "clock.fill")
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.dustyBlue)
                    }

                    VStack(alignment: .leading, spacing: 1) {
                        Text("响应")
                            .font(.system(size: layout.captionFontSize - 2))
                            .foregroundColor(HealingColors.textTertiary)
                        Text(doctor.avgResponseTime)
                            .font(.system(size: layout.captionFontSize, weight: .semibold))
                            .foregroundColor(HealingColors.dustyBlue)
                    }
                }

                Spacer()
            }

            // 底部：问医生按钮
            Button(action: onAskDoctor) {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "cross.case.fill")
                        .font(.system(size: layout.captionFontSize + 1))

                    Text("咨询医生")
                        .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding)
                .background(
                    LinearGradient(
                        colors: [HealingColors.deepSage, HealingColors.forestMist],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .clipShape(Capsule())
                .shadow(color: HealingColors.forestMist.opacity(0.25), radius: 8, x: 0, y: 4)
            }
        }
        .padding(layout.cardInnerPadding + 2)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.15), lineWidth: 1)
        )
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
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

    // UI 展示用字段
    var badges: [String] { [] }
    var avatarColor: Color {
        let colors: [Color] = [
            HealingColors.terracotta,
            HealingColors.forestMist,
            HealingColors.dustyBlue,
            HealingColors.warmSand,
            HealingColors.mutedCoral
        ]
        return colors[doctorId % colors.count]
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

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DepartmentDetailView(departmentName: "皮肤科")
    }
}
