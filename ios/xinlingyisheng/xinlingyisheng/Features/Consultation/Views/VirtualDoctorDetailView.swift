import SwiftUI

/// 虚拟医生详情视图
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

                    // 医生详情卡片
                    if let detail = doctorDetail {
                        doctorDetailCard(detail: detail)
                    } else {
                        ProgressView("加载中...")
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
                .font(.title)
                .fontWeight(.bold)

            Text("了解您的医生后开始问诊")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Doctor Detail Card

    private func doctorDetailCard(detail: VirtualDoctorDetail) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // 头像区域
            HStack(spacing: 16) {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [Color.blue.opacity(0.3), Color.purple.opacity(0.3)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 80, height: 80)
                    .overlay {
                        Image(systemName: "person.fill")
                            .font(.system(size: 40))
                            .foregroundColor(.white)
                    }

                VStack(alignment: .leading, spacing: 8) {
                    Text(doctor.name)
                        .font(.title2)
                        .fontWeight(.bold)

                    Text(doctor.title)
                        .font(.headline)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }

            Divider()

            // 基本信息
            VStack(alignment: .leading, spacing: 12) {
                if let specialty = detail.specialty {
                    InfoRow(icon: "star.fill", title: "科室", value: specialty)
                }

                if let personalityType = detail.personalityType {
                    let personalityName = viewModel.getPersonalityName(code: personalityType)
                    InfoRow(icon: "heart.fill", title: "性格", value: personalityName)
                }

                if let intro = doctor.intro, !intro.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("简介")
                            .font(.headline)
                            .foregroundColor(.secondary)

                        Text(intro)
                            .font(.body)
                    }
                    .padding(.top, 8)
                }
            }
            .padding(.vertical, 8)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
        )
    }

    // MARK: - Start Consultation Button

    private var startConsultationButton: some View {
        Button(action: {
            showConsultation = true
        }) {
            HStack(spacing: 12) {
                Image(systemName: "message.fill")
                    .font(.headline)
                Text("开始问诊")
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                LinearGradient(
                    colors: [Color.blue, Color.purple],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - Load Doctor Detail

    private func loadDoctorDetail() {
        Task {
            await viewModel.loadDoctorDetail(id: doctor.id)
            await MainActor.run {
                doctorDetail = viewModel.selectedDoctor
            }
        }
    }
}

// MARK: - Info Row

struct InfoRow: View {
    let icon: String
    let title: String
    let value: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(.blue)
                .frame(width: 24)

            Text(title)
                .font(.subheadline)
                .foregroundColor(.secondary)

            Text(value)
                .font(.subheadline)
                .fontWeight(.semibold)

            Spacer()
        }
    }
}

// MARK: - Preview

struct VirtualDoctorDetailView_Previews: PreviewProvider {
    static var previews: some View {
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
