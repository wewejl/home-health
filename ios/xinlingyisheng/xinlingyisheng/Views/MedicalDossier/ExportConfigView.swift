import SwiftUI

// MARK: - 导出配置视图（治愈系风格）
struct ExportConfigView: View {
    let event: MedicalEvent
    @ObservedObject var viewModel: MedicalDossierViewModel

    @State private var config = ExportConfig()
    @State private var showPDFPreview = false
    @State private var generatedPDFData: Data?
    @State private var isGenerating = false

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingExportConfigBackground(layout: layout)

                VStack(spacing: 0) {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(spacing: layout.cardSpacing) {
                            // 导出范围
                            HealingExportScopeCard(
                                config: $config,
                                layout: layout
                            )

                            // 日期范围
                            if config.exportScope == .dateRange {
                                HealingExportDateRangeCard(
                                    config: $config,
                                    layout: layout
                                )
                            }

                            // 导出内容
                            HealingExportContentCard(
                                config: $config,
                                layout: layout
                            )

                            // 个人信息
                            HealingExportPersonalInfoCard(
                                config: $config,
                                layout: layout
                            )

                            // 隐私说明
                            HealingExportPrivacyNotice(layout: layout)
                        }
                        .padding(.horizontal, layout.horizontalPadding)
                        .padding(.top, layout.cardInnerPadding)
                        .padding(.bottom, layout.cardInnerPadding * 2)
                    }

                    // 预览按钮
                    HealingExportPreviewButton(
                        isGenerating: isGenerating,
                        layout: layout
                    ) {
                        generatePDF()
                    }
                }
            }
        }
        .navigationTitle("导出病历")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button(action: { dismiss() }) {
                    Text("取消")
                        .font(.system(size: layout.bodyFontSize - 1))
                        .foregroundColor(HealingColors.forestMist)
                }
            }
        }
        .sheet(isPresented: $showPDFPreview) {
            if let pdfData = generatedPDFData {
                PDFPreviewView(
                    pdfData: pdfData,
                    event: event,
                    onExportSuccess: {
                        viewModel.markAsExported(event)
                        dismiss()
                    }
                )
            }
        }
    }

    private var layout: AdaptiveLayout {
        AdaptiveLayout(screenWidth: UIScreen.main.bounds.width)
    }

    private func generatePDF() {
        isGenerating = true

        let user = AuthManager.shared.currentUser
        var age: Int? = nil
        if config.includeAge, let birthday = user?.birthday {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            if let birthDate = formatter.date(from: birthday) {
                let calendar = Calendar.current
                let ageComponents = calendar.dateComponents([.year], from: birthDate, to: Date())
                age = ageComponents.year
            }
        }

        let userInfo = ExportUserInfo(
            name: config.includeName ? user?.nickname : nil,
            gender: config.includeGender ? user?.displayGender : nil,
            age: age,
            phone: config.includePhone ? user?.phone : nil
        )

        DispatchQueue.global(qos: .userInitiated).async {
            let pdfData = PDFGenerator.shared.generatePDF(
                event: event,
                config: config,
                userInfo: userInfo
            )

            DispatchQueue.main.async {
                isGenerating = false
                generatedPDFData = pdfData
                showPDFPreview = true
            }
        }
    }
}

// MARK: - 治愈系导出配置背景
struct HealingExportConfigBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.softSage.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.15)
                    .ignoresSafeArea()

                // 底部装饰光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: -geo.size.width * 0.4, y: geo.size.height * 0.2)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系导出范围卡片
struct HealingExportScopeCard: View {
    @Binding var config: ExportConfig
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                    Image(systemName: "doc.on.doc")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.forestMist)
                }

                Text("导出范围")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 选项
            VStack(spacing: 0) {
                ForEach(ExportScope.allCases, id: \.self) { scope in
                    Button(action: { config.exportScope = scope }) {
                        HStack(spacing: layout.cardSpacing / 2) {
                            ZStack {
                                Circle()
                                    .fill(config.exportScope == scope ?
                                            HealingColors.forestMist.opacity(0.2) :
                                            HealingColors.textTertiary.opacity(0.1))
                                    .frame(width: layout.iconSmallSize - 6, height: layout.iconSmallSize - 6)

                                if config.exportScope == scope {
                                    Circle()
                                        .fill(HealingColors.forestMist)
                                        .frame(width: layout.captionFontSize - 4, height: layout.captionFontSize - 4)
                                }
                            }

                            Text(scope.displayName)
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.textPrimary)

                            Spacer()
                        }
                        .padding(.horizontal, layout.cardInnerPadding)
                        .padding(.vertical, layout.cardInnerPadding - 2)
                        .background(config.exportScope == scope ?
                                    HealingColors.forestMist.opacity(0.1) :
                                    Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                    }
                    .buttonStyle(PlainButtonStyle())

                    if scope != ExportScope.allCases.last {
                        Rectangle()
                            .fill(HealingColors.softSage.opacity(0.3))
                            .frame(height: 1)
                            .padding(.leading, 40)
                    }
                }
            }
            .padding(layout.cardSpacing / 2)
            .background(HealingColors.warmCream.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系日期范围卡片
struct HealingExportDateRangeCard: View {
    @Binding var config: ExportConfig
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(HealingColors.dustyBlue.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                    Image(systemName: "calendar")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.dustyBlue)
                }

                Text("时间范围")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 日期选择器
            HStack(spacing: layout.cardSpacing) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("开始日期")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textSecondary)

                    DatePicker("", selection: $config.startDate, displayedComponents: .date)
                        .labelsHidden()
                        .datePickerStyle(.compact)
                        .tint(HealingColors.dustyBlue)
                }
                .frame(maxWidth: .infinity)
                .padding(layout.cardInnerPadding - 2)
                .background(HealingColors.warmCream.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                VStack(alignment: .leading, spacing: 4) {
                    Text("结束日期")
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textSecondary)

                    DatePicker("", selection: $config.endDate, displayedComponents: .date)
                        .labelsHidden()
                        .datePickerStyle(.compact)
                        .tint(HealingColors.dustyBlue)
                }
                .frame(maxWidth: .infinity)
                .padding(layout.cardInnerPadding - 2)
                .background(HealingColors.warmCream.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.dustyBlue.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系导出内容卡片
struct HealingExportContentCard: View {
    @Binding var config: ExportConfig
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(HealingColors.mutedCoral.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                    Image(systemName: "doc.text")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.mutedCoral)
                }

                Text("导出内容")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 选项列表
            VStack(spacing: 0) {
                HealingExportToggleRow(
                    title: "对话摘要（AI 提炼）",
                    isOn: $config.includeDialogueSummary
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "附件图片（含缩略图）",
                    isOn: $config.includeAttachments
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "AI 分析结果",
                    isOn: $config.includeAIAnalysis
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "完整对话记录",
                    isOn: $config.includeFullDialogue
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "用户备注",
                    isOn: $config.includeNotes
                )
            }
            .background(HealingColors.warmCream.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.mutedCoral.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系个人信息卡片
struct HealingExportPersonalInfoCard: View {
    @Binding var config: ExportConfig
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(HealingColors.warmSand.opacity(0.3))
                        .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                    Image(systemName: "person.text.rectangle")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.warmSand)
                }

                Text("个人信息")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 选项列表
            VStack(spacing: 0) {
                HealingExportToggleRow(
                    title: "姓名",
                    isOn: $config.includeName
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "性别",
                    isOn: $config.includeGender
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "年龄",
                    isOn: $config.includeAge
                )

                Rectangle()
                    .fill(HealingColors.softSage.opacity(0.3))
                    .frame(height: 1)
                    .padding(.leading, 52)

                HealingExportToggleRow(
                    title: "手机号码",
                    isOn: $config.includePhone
                )
            }
            .background(HealingColors.warmCream.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.warmSand.opacity(0.3), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系隐私说明
struct HealingExportPrivacyNotice: View {
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 3) {
            ZStack {
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.15))
                    .frame(width: layout.iconSmallSize - 2, height: layout.iconSmallSize - 2)

                Image(systemName: "lock.shield.fill")
                    .font(.system(size: 10))
                    .foregroundColor(HealingColors.forestMist)
            }

            Text("个人信息仅用于病历导出，不会上传至服务器")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardSpacing / 2)
        .background(HealingColors.forestMist.opacity(0.08))
        .clipShape(Capsule())
    }
}

// MARK: - 治愈系导出开关行
struct HealingExportToggleRow: View {
    let title: String
    @Binding var isOn: Bool

    var body: some View {
        Button(action: { isOn.toggle() }) {
            HStack {
                Text(title)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                ZStack {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(isOn ? HealingColors.forestMist.opacity(0.2) :
                                    HealingColors.textTertiary.opacity(0.1))
                        .frame(width: layout.iconLargeSize - 8, height: layout.iconSmallSize - 6)

                    Circle()
                        .fill(isOn ? HealingColors.forestMist : HealingColors.textTertiary)
                        .frame(width: layout.iconSmallSize - 6, height: layout.iconSmallSize - 6)
                        .offset(x: isOn ? 10 : -10)
                }
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardSpacing / 2)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private var layout: AdaptiveLayout {
        AdaptiveLayout(screenWidth: UIScreen.main.bounds.width)
    }
}

// MARK: - 治愈系预览按钮
struct HealingExportPreviewButton: View {
    let isGenerating: Bool
    let layout: AdaptiveLayout
    let action: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(height: 1)

            Button(action: action) {
                HStack(spacing: layout.cardSpacing / 2) {
                    if isGenerating {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "doc.text.viewfinder")
                            .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    }
                    Text(isGenerating ? "生成中..." : "预览并导出")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding + 2)
                .background(
                    LinearGradient(
                        colors: [HealingColors.forestMist, HealingColors.deepSage],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .shadow(color: HealingColors.forestMist.opacity(0.4), radius: 8, y: 3)
            }
            .disabled(isGenerating)
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardSpacing)
            .background(HealingColors.cardBackground.opacity(0.9))
        }
    }
}

#Preview {
    let mockEvent = MedicalEvent(
        title: "皮肤红疹",
        department: .dermatology,
        status: .inProgress,
        summary: "AI判断：过敏性皮炎",
        riskLevel: .medium as DossierRiskLevel
    )

    NavigationView {
        ExportConfigView(event: mockEvent, viewModel: MedicalDossierViewModel())
    }
}
