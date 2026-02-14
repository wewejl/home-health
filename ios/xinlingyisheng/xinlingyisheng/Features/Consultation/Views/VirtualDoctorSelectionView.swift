import SwiftUI

/// 虚拟医生选择视图
struct VirtualDoctorSelectionView: View {
    @StateObject private var viewModel = VirtualDoctorViewModel()
    @State private var selectedDepartment: String?
    @State private var selectedPersonality: String?
    @State private var selectedDoctor: VirtualDoctor?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationView {
            ZStack {
                // 背景渐变
                LinearGradient(
                    colors: [Color.blue.opacity(0.1), Color.purple.opacity(0.1)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                VStack(spacing: 20) {
                    // 标题
                    header

                    // 筛选区
                    filterSection

                    Divider()

                    // 医生列表
                    if viewModel.isLoading {
                        ProgressView("加载中...")
                        Spacer()
                    } else if viewModel.doctors.isEmpty {
                        emptyState
                    } else {
                        doctorList
                    }
                }
                .padding()
            }
            .navigationTitle("选择医生")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") {
                        dismiss()
                    }
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
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("选择您的 AI 医生")
                .font(.title)
                .fontWeight(.bold)

            Text("不同风格的医生会提供不同的问诊体验")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Filter Section

    private var filterSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 科室筛选
            if !viewModel.specialties.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("科室")
                        .font(.subheadline)
                        .fontWeight(.semibold)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            FilterChip(
                                title: "全部",
                                isSelected: selectedDepartment == nil
                            ) {
                                selectedDepartment = nil
                                applyFilters()
                            }

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
                        .padding(.horizontal, 4)
                    }
                }
            }

            // 性格筛选
            if !viewModel.personalities.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("性格")
                        .font(.subheadline)
                        .fontWeight(.semibold)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            FilterChip(
                                    title: "全部",
                                    isSelected: selectedPersonality == nil
                                ) {
                                selectedPersonality = nil
                                applyFilters()
                            }

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
                        .padding(.horizontal, 4)
                    }
                }
            }
        }
    }

    // MARK: - Doctor List

    private var doctorList: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
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
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "stethoscope")
                .font(.system(size: 60))
                .foregroundColor(.gray)

            Text("暂无符合条件的医生")
                .font(.headline)
                .foregroundColor(.secondary)

            Text("请尝试调整筛选条件")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
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
                Text(title)
                    .font(.subheadline)
                    .fontWeight(isSelected ? .semibold : .regular)

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.caption)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(isSelected ? Color.blue : Color.gray.opacity(0.2))
            )
            .foregroundColor(isSelected ? .white : .primary)
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
                        colors: [Color.blue.opacity(0.3), Color.purple.opacity(0.3)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 60, height: 60)
                .overlay {
                    Image(systemName: "person.fill")
                        .font(.title2)
                        .foregroundColor(.white)
                }

            // 信息
            VStack(alignment: .leading, spacing: 6) {
                Text(doctor.name)
                    .font(.headline)
                    .fontWeight(.semibold)

                Text(doctor.title)
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                if let specialty = doctor.specialty {
                    HStack(spacing: 6) {
                        Image(systemName: "star.fill")
                            .font(.caption)
                            .foregroundColor(.yellow)

                        Text(specialty)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.gray)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
        )
    }
}

// MARK: - Preview

struct VirtualDoctorSelectionView_Previews: PreviewProvider {
    static var previews: some View {
        VirtualDoctorSelectionView()
    }
}
