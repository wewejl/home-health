import SwiftUI

// MARK: - 问医生页面主视图（治愈系风格）
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
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack(alignment: .top) {
                // 背景
                HealingColors.background
                    .ignoresSafeArea()

                // 右上角装饰光晕 - 使用统一的相对偏移
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: layout.decorativeCircleSize * 0.3, y: -layout.decorativeCircleSize * 0.05)
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // 自定义导航栏
                    AskDoctorNavBar(showMyQuestions: $showMyQuestions, layout: layout)

                    if isLoadingDepartments {
                        Spacer()
                        ProgressView("加载科室中...")
                            .tint(HealingColors.forestMist)
                            .progressViewStyle(CircularProgressViewStyle())
                        Spacer()
                    } else if departments.isEmpty {
                        Spacer()
                        VStack(spacing: layout.cardSpacing) {
                            Image(systemName: "building.2.slash")
                                .font(.system(size: UnifiedFont.body, weight: .light))
                                .foregroundColor(HealingColors.textTertiary)
                            Text("暂无科室数据")
                                .font(.system(size: layout.bodyFontSize, weight: .regular))
                                .foregroundColor(HealingColors.textSecondary)
                            Button("点击重试") {
                                loadDepartments()
                            }
                            .buttonStyle(HealingButtonStyle())
                        }
                        Spacer()
                    } else {
                        ScrollView(.vertical, showsIndicators: false) {
                            VStack(spacing: layout.cardSpacing + 8) {
                                // 搜索区域
                                AskDoctorSearchView(searchText: $searchText, layout: layout)

                                // 信任标签
                                TrustBadgesView(layout: layout)

                                // 科室列表（从 API 加载）
                                DepartmentListView(
                                    departments: filteredDepartments,
                                    selectedDepartment: $selectedDepartment,
                                    layout: layout
                                )

                                // 底部品牌区
                                BrandFooterView(layout: layout)
                            }
                            .padding(.horizontal, layout.horizontalPadding)
                            .padding(.bottom, adaptiveBottomPadding(layout))
                        }
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
                // 获取所有科室
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

    private func adaptiveBottomPadding(_ layout: AdaptiveLayout) -> CGFloat {
        layout.cardInnerPadding * 8
    }
}

// MARK: - 科室列表视图（治愈系风格）
struct DepartmentListView: View {
    let departments: [DepartmentModel]
    @Binding var selectedDepartment: DepartmentModel?
    let layout: AdaptiveLayout

    var columns: [GridItem] {
        [
            GridItem(.flexible(), spacing: layout.cardSpacing - 2),
            GridItem(.flexible(), spacing: layout.cardSpacing - 2)
        ]
    }

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            Text("全部科室")
                .font(.system(size: layout.bodyFontSize, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)

            LazyVGrid(columns: columns, spacing: layout.cardSpacing - 2) {
                ForEach(departments) { dept in
                    HealingDepartmentCard(department: dept, layout: layout) {
                        selectedDepartment = dept
                    }
                    .fluidFadeIn(delay: 0.1)
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
    }
}

// MARK: - 治愈系科室卡片
struct HealingDepartmentCard: View {
    let department: DepartmentModel
    let layout: AdaptiveLayout
    let onTap: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: layout.cardSpacing / 2) {
                // 左侧图标 - 增强效果
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [
                                    HealingColors.deepSage.opacity(isPressed ? 0.25 : 0.18),
                                    HealingColors.softSage.opacity(isPressed ? 0.2 : 0.12)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .overlay(
                            Circle()
                                .stroke(HealingColors.forestMist.opacity(isPressed ? 0.2 : 0.1), lineWidth: 1)
                        )
                        .shadow(
                            color: HealingColors.forestMist.opacity(isPressed ? 0.2 : 0.12),
                            radius: isPressed ? 6 : 4,
                            x: 0,
                            y: 2
                        )

                    Image(systemName: SFSymbolResolver.resolve(department.icon))
                        .font(.system(size: AdaptiveFont.title3, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                }
                .frame(width: 36 * layout.iconScale, height: 36 * layout.iconScale)
                .scaleEffect(isPressed ? 0.95 : 1.0)

                VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                    Text(department.name)
                        .font(.system(size: AdaptiveFont.caption1, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)
                        .lineLimit(1)

                    if let desc = department.description {
                        Text(desc)
                            .font(.system(size: AdaptiveFont.custom(7), weight: .regular))
                            .foregroundColor(HealingColors.textTertiary)
                            .lineLimit(2)
                            .multilineTextAlignment(.leading)
                    }
                }

                Spacer(minLength: 0)
            }
            .padding(layout.cardInnerPadding - 2)
            .frame(maxWidth: .infinity, minHeight: layout.cardInnerPadding * 4, alignment: .topLeading)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(HealingColors.cardBackground)
                    .shadow(
                        color: Color.black.opacity(isPressed ? 0.06 : 0.08),
                        radius: isPressed ? 6 : 10,
                        x: 0,
                        y: isPressed ? 2 : 4
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(
                                HealingColors.softSage.opacity(isPressed ? 0.25 : 0.15),
                                lineWidth: 1
                            )
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .animation(.easeInOut(duration: 0.12), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - 治愈系导航栏
struct AskDoctorNavBar: View {
    @Binding var showMyQuestions: Bool
    let layout: AdaptiveLayout

    var body: some View {
        HStack {
            Text("问医生")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)
                .frame(maxWidth: .infinity, alignment: .center)

            Button(action: { showMyQuestions = true }) {
                HStack(spacing: 4) {
                    Text("我的提问")
                        .font(.system(size: UnifiedFont.caption1, weight: .medium))
                    Image(systemName: "chevron.right")
                        .font(.system(size: UnifiedFont.caption1, weight: .semibold))
                }
                .foregroundColor(HealingColors.forestMist)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.vertical, layout.cardInnerPadding - 2)
        .background(HealingColors.cardBackground)
    }
}

// MARK: - 治愈系搜索区域
struct AskDoctorSearchView: View {
    @Binding var searchText: String
    let layout: AdaptiveLayout

    let hotTags = ["血糖监测", "血压管理", "感冒发烧", "皮肤问题", "儿童健康"]

    var body: some View {
        VStack(spacing: layout.cardSpacing - 2) {
            // 搜索框
            HStack(spacing: layout.cardSpacing / 2) {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textTertiary)

                    TextField("疾病 / 症状 / 医院 / 医生名", text: $searchText)
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textPrimary)
                }
                .padding(.horizontal, layout.cardInnerPadding - 2)
                .padding(.vertical, layout.cardInnerPadding - 4)
                .background(HealingColors.warmCream)
                .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))

                Button(action: {}) {
                    Text("搜索")
                        .font(.system(size: UnifiedFont.caption1, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.vertical, layout.cardInnerPadding - 4)
                        .background(
                            LinearGradient(
                                colors: [HealingColors.deepSage, HealingColors.forestMist],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                }
            }

            // 热搜标签
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: layout.cardSpacing / 2) {
                    ForEach(hotTags, id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: UnifiedFont.caption1))
                            .foregroundColor(HealingColors.textSecondary)
                            .padding(.horizontal, layout.cardInnerPadding - 2)
                            .padding(.vertical, layout.cardSpacing / 2)
                            .background(HealingColors.warmSand.opacity(0.6))
                            .clipShape(Capsule())
                    }
                }
            }
        }
        .padding(.top, layout.cardSpacing / 2)
    }
}

// MARK: - 治愈系信任标签
struct TrustBadgesView: View {
    let layout: AdaptiveLayout

    let badges = [
        ("checkmark.seal.fill", "医生实名认证"),
        ("shield.checkered", "平台双重质控"),
        ("clock.fill", "医生7×24h在线")
    ]

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Array(badges.enumerated()), id: \.offset) { _, element in
                let (icon, text) = element
                HStack(spacing: 4) {
                    Image(systemName: icon)
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.deepSage)

                    Text(text)
                        .font(.system(size: UnifiedFont.caption1))
                }
                .foregroundColor(HealingColors.textTertiary)

                if text != badges.last?.1 {
                    Spacer()
                }
            }
        }
        .padding(.horizontal, ScaleFactor.padding(4))
    }
}


// MARK: - 治愈系底部品牌区
struct BrandFooterView: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing / 2) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "cross.fill")
                    .font(.system(size: UnifiedFont.footnote))
                Text("灵犀健康")
                    .font(.system(size: UnifiedFont.footnote, weight: .medium))
            }
            .foregroundColor(HealingColors.forestMist.opacity(0.7))

            Text("一起发现健康生活")
                .font(.system(size: UnifiedFont.caption1))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(.top, layout.cardSpacing)
        .padding(.bottom, layout.cardInnerPadding)
    }
}

// MARK: - 治愈系按钮样式
struct HealingButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundColor(HealingColors.forestMist)
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(8))
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(HealingColors.softSage.opacity(0.15))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(HealingColors.deepSage.opacity(0.3), lineWidth: 1)
            )
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        AskDoctorView()
    }
}
