import SwiftUI

struct ExportConfigView: View {
    let event: MedicalEvent
    @ObservedObject var viewModel: MedicalDossierViewModel
    
    @State private var config = ExportConfig()
    @State private var showPDFPreview = false
    @State private var generatedPDFData: Data?
    @State private var isGenerating = false
    
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ZStack {
                DXYColors.background
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(spacing: ScaleFactor.spacing(20)) {
                            exportScopeSection
                            
                            if config.exportScope == .dateRange {
                                dateRangeSection
                            }
                            
                            exportContentSection
                            
                            personalInfoSection
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                        .padding(.vertical, ScaleFactor.padding(16))
                    }
                    
                    previewButton
                }
            }
            .navigationTitle("导出病历")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                    .foregroundColor(DXYColors.primaryPurple)
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
    }
    
    private var exportScopeSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            sectionHeader(title: "导出范围", icon: "doc.on.doc")
            
            VStack(spacing: 0) {
                ForEach(ExportScope.allCases, id: \.self) { scope in
                    Button(action: { config.exportScope = scope }) {
                        HStack {
                            Image(systemName: config.exportScope == scope ? "circle.inset.filled" : "circle")
                                .font(.system(size: AdaptiveFont.title3))
                                .foregroundColor(config.exportScope == scope ? DXYColors.primaryPurple : DXYColors.textTertiary)
                            
                            Text(scope.displayName)
                                .font(.system(size: AdaptiveFont.body))
                                .foregroundColor(DXYColors.textPrimary)
                            
                            Spacer()
                        }
                        .padding(.horizontal, ScaleFactor.padding(16))
                        .padding(.vertical, ScaleFactor.padding(14))
                    }
                    .buttonStyle(PlainButtonStyle())
                    
                    if scope != ExportScope.allCases.last {
                        Divider()
                            .padding(.leading, ScaleFactor.padding(48))
                    }
                }
            }
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
        }
    }
    
    private var dateRangeSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack(spacing: ScaleFactor.spacing(12)) {
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    Text("开始日期")
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textTertiary)
                    
                    DatePicker("", selection: $config.startDate, displayedComponents: .date)
                        .labelsHidden()
                        .datePickerStyle(.compact)
                        .tint(DXYColors.primaryPurple)
                }
                .frame(maxWidth: .infinity)
                .padding(ScaleFactor.padding(12))
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    Text("结束日期")
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textTertiary)
                    
                    DatePicker("", selection: $config.endDate, displayedComponents: .date)
                        .labelsHidden()
                        .datePickerStyle(.compact)
                        .tint(DXYColors.primaryPurple)
                }
                .frame(maxWidth: .infinity)
                .padding(ScaleFactor.padding(12))
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
            }
        }
    }
    
    private var exportContentSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            sectionHeader(title: "导出内容", icon: "doc.text")
            
            VStack(spacing: 0) {
                ToggleRow(title: "对话摘要（AI 提炼）", isOn: $config.includeDialogueSummary)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "附件图片（含缩略图）", isOn: $config.includeAttachments)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "AI 分析结果", isOn: $config.includeAIAnalysis)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "完整对话记录", isOn: $config.includeFullDialogue)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "用户备注", isOn: $config.includeNotes)
            }
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
        }
    }
    
    private var personalInfoSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            sectionHeader(title: "个人信息", icon: "person.text.rectangle")
            
            VStack(spacing: 0) {
                ToggleRow(title: "姓名", isOn: $config.includeName)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "性别", isOn: $config.includeGender)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "年龄", isOn: $config.includeAge)
                Divider().padding(.leading, ScaleFactor.padding(16))
                ToggleRow(title: "手机号码", isOn: $config.includePhone)
            }
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
            
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "lock.shield")
                    .font(.system(size: AdaptiveFont.caption))
                Text("个人信息仅用于病历导出，不会上传至服务器")
                    .font(.system(size: AdaptiveFont.caption))
            }
            .foregroundColor(DXYColors.textTertiary)
        }
    }
    
    private func sectionHeader(title: String, icon: String) -> some View {
        HStack(spacing: ScaleFactor.spacing(6)) {
            Image(systemName: icon)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.teal)
            Text(title)
                .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                .foregroundColor(DXYColors.textPrimary)
        }
    }
    
    private var previewButton: some View {
        VStack(spacing: 0) {
            Divider()
            
            Button(action: generatePDF) {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    if isGenerating {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "doc.text.viewfinder")
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    }
                    Text(isGenerating ? "生成中..." : "预览并导出")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, ScaleFactor.padding(16))
                .background(DXYColors.primaryPurple)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
            }
            .disabled(isGenerating)
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.vertical, ScaleFactor.padding(12))
            .background(Color.white)
        }
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

struct ToggleRow: View {
    let title: String
    @Binding var isOn: Bool
    
    var body: some View {
        Button(action: { isOn.toggle() }) {
            HStack {
                Text(title)
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(DXYColors.textPrimary)
                
                Spacer()
                
                Image(systemName: isOn ? "checkmark.square.fill" : "square")
                    .font(.system(size: AdaptiveFont.title3))
                    .foregroundColor(isOn ? DXYColors.primaryPurple : DXYColors.textTertiary)
            }
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(14))
        }
        .buttonStyle(PlainButtonStyle())
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
    
    ExportConfigView(event: mockEvent, viewModel: MedicalDossierViewModel())
}
