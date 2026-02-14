import SwiftUI

/// 虚拟医生选择视图（治愈系风格）
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

                ScrollView {
                    VStack(spacing: 0) {
                        // 标题区
                        header

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

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("选择您的 AI 医生")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(HealingColorTheme.textPrimary)

            Text("不同风格的医生会提供不同的问诊体验")
                .font(.system(size: 15))
                .foregroundColor(HealingColorTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20)
        .padding(.top, 12)
    }

    // MARK: - Filter Section

    private var filterSection: some View {
        VStack(spacing: 16) {
            // 科室筛选
            if !viewModel.specialties.isEmpty {
                VStack(alignment: .leading, spacing: 10) {
                    Text("科室")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(HealingColorTheme.textSecondary)

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

                Divider()
                    .background(HealingColorTheme.borderLight)
            }

            // 性格筛选
            if !viewModel.personalities.isEmpty {
                VStack(alignment: .leading, spacing: 10) {
                    Text("性格")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(HealingColorTheme.textSecondary)

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
        .padding(.top, 8)
    }

    // MARK: - Doctor List

    private var doctorList: some View {
        LazyVStack(spacing: 12) {
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
        VStack(spacing: 16) {
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
        VStack(spacing: 16) {
            Image(systemName: "stethoscope")
                .font(.system(size: 48))
                .foregroundColor(HealingColorTheme.forestMist.opacity(0.5))

            Text("暂无符合条件的医生")
                .font(.system(size: 17, weight: .medium))
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
            .foregroundColor(HealingColorTheme.forestMist)
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(HealingColorTheme.softSage.opacity(0.2))
            )
            .padding(.horizontal, 4)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    // MARK: - Helper Methods

    private func applyFilters() {
        // 从选中的科室代码获取科室 ID
        let departmentId: Int? = nil
        if let deptCode = selectedDepartment {
            // 尝试从 specialties 中查找对应的科室配置
            // 注意：这里需要从后端数据获取正确的科室 ID 映射
            // 暂时先传递科室代码，后端会处理
        }

        viewModel.loadDoctors(
            departmentId: departmentId,
            personalityType: selectedPersonality
        )
    }
}

// MARK: - Filter Chip

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(HealingColorTheme.successGreen)
                }

                Text(title)
                    .font(.system(size: 14, weight: isSelected ? .semibold : .regular))
                    .foregroundColor(isSelected ? HealingColorTheme.textPrimary : HealingColorTheme.textSecondary)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(isSelected ? HealingColorTheme.successGreen.opacity(0.15) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(
                        isSelected ? HealingColorTheme.successGreen : HealingColorTheme.borderLight,
                        lineWidth: isSelected ? 0 : 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Doctor Row Card

struct DoctorRowCard: View {
    let doctor: VirtualDoctor

    var body: some View {
        HStack(spacing: 16) {
            // 头像
            Circle()
                .fill(
                    LinearGradient(
                        colors: [HealingColorTheme.softSage, HealingColorTheme.deepSage],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 56, height: 56)
                .overlay(
                    Circle()
                        .stroke(HealingColorTheme.forestMist.opacity(0.2), lineWidth: 1.5)
                )
                .shadow(
                    color: HealingColorTheme.forestMist.opacity(0.12),
                    radius: 6,
                    x: 0,
                    y: 2
                )

            Image(systemName: "person.fill")
                .font(.system(size: 22))
                .foregroundColor(.white)
                .frame(width: 56, height: 56)

            // 信息
            VStack(alignment: .leading, spacing: 4) {
                Text(doctor.name)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(HealingColorTheme.textPrimary)

                HStack(spacing: 6) {
                    Text(doctor.title)
                        .font(.system(size: 14))
                        .foregroundColor(HealingColorTheme.textSecondary)

                    if let specialty = doctor.specialty {
                        HStack(spacing: 4) {
                            Image(systemName: "star.fill")
                                .font(.system(size: 12))
                                .foregroundColor(HealingColorTheme.orange)

                            Text(specialty)
                                .font(.system(size: 13))
                                .foregroundColor(HealingColorTheme.textSecondary)
                        }
                    }
                }

                if let intro = doctor.intro, !intro.isEmpty {
                    Text(intro)
                        .font(.system(size: 13))
                        .foregroundColor(HealingColorTheme.textTertiary)
                        .lineLimit(2)
                }
            }

            Spacer(minLength: 0)

            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(HealingColorTheme.borderLight)
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 20)
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
