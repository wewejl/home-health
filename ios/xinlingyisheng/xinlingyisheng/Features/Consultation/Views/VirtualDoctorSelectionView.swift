import SwiftUI

/// 虚拟医生选择视图（治愈系风格 - 优化版）
struct VirtualDoctorSelectionView: View {
    @StateObject private var viewModel = VirtualDoctorViewModel()
    @State private var selectedDepartment: String?
    @State private var selectedPersonality: String?
    @State private var selectedDoctor: VirtualDoctor?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationView {
            ZStack {
                // 背景
                HealingColorTheme.background
                    .ignoresSafeArea()

                // 柔和的背景装饰
                decorativeBackground

                ScrollView {
                    VStack(spacing: 0) {
                        // 标题区 - 带装饰元素
                        headerWithDecoration

                        // 筛选区
                        filterSection

                        Divider()
                            .background(HealingColorTheme.borderLight)

                        // 医生列表
                        if viewModel.isLoading {
                            loadingState
                        } else if viewModel.doctors.isEmpty {
                            emptyState
                        } else {
                            doctorList
                        }
                    }
                    .padding(.bottom, 24)
                }
            }
            .navigationTitle("选择医生")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") {
                        dismiss()
                    }
                    .foregroundColor(HealingColorTheme.textSecondary)
                }
            }
        }
        .onAppear {
            viewModel.loadDoctors()
            viewModel.loadPersonalities()
            viewModel.loadSpecialties()
        }
        .navigationDestinationCompat(item: $selectedDoctor) { doctor in
            // 医生详情页 - 显示完整信息后确认进入问诊
            VirtualDoctorDetailView(doctor: doctor)
        }
        .alert("错误", isPresented: Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.clearError() } }
        )) {
            Button("确定") { viewModel.clearError() }
            Button("取消", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    // MARK: - Decorative Background

    private var decorativeBackground: some View {
        ZStack {
            // 右上角装饰 - 大圆
            Circle()
                .fill(HealingColorTheme.softSage.opacity(0.06))
                .frame(width: 180, height: 180)
                .offset(x: 80, y: -60)

            // 右中装饰 - 中圆
            Circle()
                .fill(HealingColorTheme.deepSage.opacity(0.04))
                .frame(width: 120, height: 120)
                .offset(x: 40, y: -30)

            // 左下角装饰
            Circle()
                .fill(HealingColorTheme.teal.opacity(0.03))
                .frame(width: 100, height: 100)
                .offset(x: -60, y: 80)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Header with Decoration

    private var headerWithDecoration: some View {
        HStack {
            // 左侧装饰 - 叶子图标
            Image(systemName: "leaf.fill")
                .font(.system(size: 18))
                .foregroundColor(HealingColorTheme.forestMist.opacity(0.25))

            VStack(alignment: .leading, spacing: 4) {
                Text("选择您的 AI 医生")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(HealingColorTheme.textPrimary)

                Text("不同风格的医生会提供不同的问诊体验")
                    .font(.system(size: 14))
                    .foregroundColor(HealingColorTheme.textSecondary)
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20)
        .padding(.top, 16)
        .padding(.bottom, 12)
    }

    // MARK: - Filter Section

    private var filterSection: some View {
        VStack(spacing: 20) {
            // 科室筛选
            if !viewModel.specialties.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 10) {
                        Image(systemName: "star.fill")
                            .font(.system(size: 14))
                            .foregroundColor(HealingColorTheme.orange)

                        Text("科室")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(HealingColorTheme.textPrimary)
                    }

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            // 全部选项
                            FilterChip(
                                title: "全部",
                                isSelected: selectedDepartment == nil
                            ) {
                                selectedDepartment = nil
                                applyFilters()
                            }

                            // 科室列表
                            ForEach(viewModel.specialties, id: \.code) { specialty in
                                FilterChip(
                                    title: specialty.name,
                                    isSelected: selectedDepartment == specialty.code
                                ) {
                                    selectedDepartment = specialty.code
                                    applyFilters()
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                }
            }

            // 性格筛选
            if !viewModel.personalities.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 10) {
                        Image(systemName: "heart.fill")
                            .font(.system(size: 14))
                            .foregroundColor(HealingColorTheme.forestMist)

                        Text("性格")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(HealingColorTheme.textPrimary)
                    }

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            // 全部选项
                            FilterChip(
                                title: "全部",
                                isSelected: selectedPersonality == nil
                            ) {
                                selectedPersonality = nil
                                applyFilters()
                            }

                            // 性格列表
                            ForEach(viewModel.personalities, id: \.code) { personality in
                                FilterChip(
                                    title: personality.name,
                                    isSelected: selectedPersonality == personality.code
                                ) {
                                    selectedPersonality = personality.code
                                    applyFilters()
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                }
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 12)
    }

    // MARK: - Doctor List

    private var doctorList: some View {
        LazyVStack(spacing: 14) {
            ForEach(viewModel.doctors) { doctor in
                Button(action: {
                    selectedDoctor = doctor
                }) {
                    DoctorRowCard(doctor: doctor)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding()
    }

    // MARK: - Loading State

    private var loadingState: some View {
        VStack(spacing: 20) {
            Spacer()

            ProgressView("加载中...")
                .tint(HealingColorTheme.forestMist)

            Text("正在为您寻找合适的医生...")
                .font(.system(size: 15))
                .foregroundColor(HealingColorTheme.textSecondary)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "stethoscope")
                .font(.system(size: 52))
                .foregroundColor(HealingColorTheme.forestMist.opacity(0.4))

            Text("暂无符合条件的医生")
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(HealingColorTheme.textPrimary)

            Text("请尝试调整筛选条件")
                .font(.system(size: 14))
                .foregroundColor(HealingColorTheme.textSecondary)

            Button("重置筛选") {
                selectedDepartment = nil
                selectedPersonality = nil
                applyFilters()
            }
            .font(.system(size: 15, weight: .semibold))
            .foregroundColor(.white)
            .padding(.horizontal, 24)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(HealingColorTheme.deepSage)
            )
            .shadow(
                color: HealingColorTheme.deepSage.opacity(0.3),
                radius: 8,
                x: 0,
                y: 4
            )
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    // MARK: - Helper Methods

    private func applyFilters() {
        // 从选中的科室代码获取科室 ID
        // 需要通过 specialties 列表查找对应的科室配置来获取 department_id
        var departmentId: Int? = nil
        if let deptCode = selectedDepartment {
            // 从 specialties 列表中查找对应的科室
            if let specialty = viewModel.specialties.first(where: { $0.code == deptCode }) {
                // 使用科室名称在医生列表中筛选
                // 后端 API 不支持按科室代码筛选，所以先传 nil
                // TODO: 后端需要添加按科室代码筛选的支持
                departmentId = nil
            }
        }

        viewModel.loadDoctors(
            departmentId: departmentId,
            personalityType: selectedPersonality
        )
    }
}

// MARK: - Filter Chip（治愈系风格）

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                // 选中时显示勾选
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 13, weight: .semibold))
                }

                Text(title)
                    .font(.system(size: 14, weight: isSelected ? .semibold : .regular))
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 9)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill(isSelected ? HealingColorTheme.successGreen.opacity(0.15) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(
                        isSelected ? HealingColorTheme.successGreen : HealingColorTheme.borderLight,
                        lineWidth: isSelected ? 2 : 1
                    )
            )
            .shadow(
                color: isSelected ? HealingColorTheme.deepSage.opacity(0.15) : Color.clear,
                radius: isSelected ? 6 : 0,
                x: 0,
                y: 2
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Doctor Row Card（治愈系风格）

struct DoctorRowCard: View {
    let doctor: VirtualDoctor

    var body: some View {
        HStack(spacing: 14) {
            // 头像 - 治愈系渐变
            Circle()
                .fill(
                    LinearGradient(
                        colors: [HealingColorTheme.softSage, HealingColorTheme.deepSage],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 52, height: 52)
                .overlay(
                    Circle()
                        .stroke(HealingColorTheme.forestMist.opacity(0.2), lineWidth: 2)
                )
                .shadow(
                    color: HealingColorTheme.forestMist.opacity(0.12),
                    radius: 8,
                    x: 0,
                    y: 3
                )

            // 信息区
            VStack(alignment: .leading, spacing: 6) {
                Text(doctor.name)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(HealingColorTheme.textPrimary)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    Text(doctor.title)
                        .font(.system(size: 13))
                        .foregroundColor(HealingColorTheme.textSecondary)

                    if let specialty = doctor.specialty {
                        HStack(spacing: 4) {
                            Image(systemName: "star.fill")
                                .font(.system(size: 11))
                                .foregroundColor(HealingColorTheme.orange)

                            Text(specialty)
                                .font(.system(size: 12))
                                .foregroundColor(HealingColorTheme.textPrimary)
                        }
                    }
                }

                if let intro = doctor.intro, !intro.isEmpty {
                    Text(intro)
                        .font(.system(size: 12))
                        .foregroundColor(HealingColorTheme.textTertiary)
                        .lineLimit(2)
                }
            }

            Spacer(minLength: 0)

            // 右箭头
            Image(systemName: "chevron.right")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(HealingColorTheme.borderLight)
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 18)
                .fill(HealingColorTheme.cardBackground)
                .shadow(
                    color: HealingColorTheme.forestMist.opacity(0.06),
                    radius: 10,
                    x: 0,
                    y: 3
                )
        )
    }
}

// MARK: - Preview

struct VirtualDoctorSelectionView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            VirtualDoctorSelectionView()
        }
    }
}
