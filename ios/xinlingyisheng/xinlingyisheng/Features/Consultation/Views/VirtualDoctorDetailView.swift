import SwiftUI

/// 虚拟医生详情视图（治愈系风格）
/// 显示虚拟医生详细信息，用户确认后进入问诊
struct VirtualDoctorDetailView: View {
    let doctor: VirtualDoctor
    @StateObject private var viewModel = VirtualDoctorViewModel()
    @State private var doctorDetail: VirtualDoctorDetail?
    @State private var showConsultation = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationView {
            ZStack {
                // 背景
                HealingColorTheme.background
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // 标题区
                    header

                    // 医生详情卡片
                    if let detail = doctorDetail {
                        doctorDetailCard(detail: detail)
                    } else {
                        Spacer()
                        ProgressView("加载中...")
                            .tint(HealingColorTheme.forestMist)
                        Spacer()
                    }

                    Spacer()

                    // 开始问诊按钮
                    if doctorDetail != nil {
                        startConsultationButton
                    }
                }
                .padding()
            }
            .navigationTitle("医生详情")
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
            loadDoctorDetail()
        }
        .navigationDestinationCompat(isPresented: $showConsultation) {
            if let detail = doctorDetail {
                ModernConsultationView(
                    doctorId: doctor.id,
                    doctorName: doctor.name,
                    department: detail.specialty ?? "通用",
                    doctorTitle: doctor.title,
                    doctorBio: doctor.intro ?? ""
                )
            }
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("AI 医生")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(HealingColorTheme.textPrimary)

            Text("了解您的医生后开始问诊")
                .font(.system(size: 14))
                .foregroundColor(HealingColorTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.bottom, 8)
    }

    // MARK: - Doctor Detail Card

    private func doctorDetailCard(detail: VirtualDoctorDetail) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // 头像区域
            HStack(spacing: 16) {
                // 圆形头像占位
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [HealingColorTheme.softSage, HealingColorTheme.deepSage],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 72, height: 72)
                        .shadow(
                            color: HealingColorTheme.forestMist.opacity(0.15),
                            radius: 8,
                            x: 0,
                            y: 2
                        )

                    Image(systemName: "person.fill")
                        .font(.system(size: 32))
                        .foregroundColor(HealingColorTheme.forestMist)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text(doctor.name)
                        .font(.system(size: 22, weight: .bold))
                        .foregroundColor(HealingColorTheme.textPrimary)

                    Text(doctor.title)
                        .font(.system(size: 16))
                        .foregroundColor(HealingColorTheme.textSecondary)
                }

                Spacer()
            }

            Divider()
                .background(HealingColorTheme.borderLight)

            // 基本信息
            VStack(alignment: .leading, spacing: 14) {
                if let specialty = detail.specialty {
                    InfoRow(
                        icon: "star.fill",
                        title: "科室",
                        value: specialty,
                        color: HealingColorTheme.orange
                    )
                }

                if let personalityType = detail.personalityType {
                    let personalityName = viewModel.getPersonalityName(code: personalityType)
                    InfoRow(
                        icon: "heart.fill",
                        title: "性格",
                        value: personalityName,
                        color: HealingColorTheme.teal
                    )
                }

                if let intro = doctor.intro, !intro.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("简介")
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(HealingColorTheme.textSecondary)

                        Text(intro)
                            .font(.system(size: 15))
                            .foregroundColor(HealingColorTheme.textPrimary)
                            .lineLimit(nil)
                    }
                    .padding(.top, 8)
                }
            }
            .padding(.vertical, 8)
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: 24)
                .fill(HealingColorTheme.cardBackground)
                .shadow(
                    color: HealingColorTheme.forestMist.opacity(0.08),
                    radius: 12,
                    x: 0,
                    y: 4
                )
        )
    }

    // MARK: - Start Consultation Button

    private var startConsultationButton: some View {
        Button(action: {
            showConsultation = true
        }) {
            HStack(spacing: 12) {
                Image(systemName: "message.fill")
                    .font(.system(size: 18, weight: .semibold))
                Text("开始问诊")
                    .font(.system(size: 17, weight: .semibold))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 18)
            .background(
                LinearGradient(
                        colors: [HealingColorTheme.deepSage, HealingColorTheme.forestMist],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
            )
            .clipShape(RoundedRectangle(cornerRadius: 16))
        }
        .buttonStyle(PlainButtonStyle())
        .padding(.horizontal, 20)
    }

    // MARK: - Load Doctor Detail

    private func loadDoctorDetail() {
        viewModel.loadDoctorDetail(id: doctor.id)
        // loadDoctorDetail 是同步方法，实际操作在内部 Task 中
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            doctorDetail = viewModel.selectedDoctor
        }
    }
}

// MARK: - Info Row

struct InfoRow: View {
    let icon: String
    let title: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 32, height: 32)

                Image(systemName: icon)
                    .font(.system(size: 15))
                    .foregroundColor(color)
            }

            Text(title)
                .font(.system(size: 14))
                .foregroundColor(HealingColorTheme.textSecondary)

            Text(value)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(HealingColorTheme.textPrimary)

            Spacer()
        }
    }
}

// MARK: - Preview

struct VirtualDoctorDetailView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            VirtualDoctorDetailView(
                doctor: VirtualDoctor(
                        id: 1,
                        name: "张医生",
                        title: "主治医师",
                        departmentId: 1,
                        specialty: "内科",
                        intro: "擅长心血管疾病的诊断和治疗",
                        personalityType: "friendly",
                        greetingTemplate: "你好 {name}"
                )
            )
        }
    }
}
