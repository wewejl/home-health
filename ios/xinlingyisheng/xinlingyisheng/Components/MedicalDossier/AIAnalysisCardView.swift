import SwiftUI

struct AIAnalysisCardView: View {
    let analysis: AIAnalysis
    @State private var isExpanded = true
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(16)) {
            headerSection
            
            if isExpanded {
                Divider()
                    .background(DXYColors.teal.opacity(0.2))
                
                chiefComplaintSection
                
                symptomsSection
                
                diagnosisSection
                
                recommendationsSection
                
                if analysis.needOfflineVisit {
                    visitReminderSection
                }
                
                disclaimerSection
            }
        }
        .padding(ScaleFactor.padding(20))
        .background(DossierColors.analysisCardGradient)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusLarge, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusLarge, style: .continuous)
                .stroke(DXYColors.teal.opacity(0.2), lineWidth: 1)
        )
    }
    
    private var headerSection: some View {
        Button(action: {
            withAnimation(.spring(response: 0.3)) {
                isExpanded.toggle()
            }
        }) {
            HStack {
                HStack(spacing: ScaleFactor.spacing(6)) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(DXYColors.teal)
                    Text("AI 分析报告")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        .foregroundColor(DXYColors.textPrimary)
                }
                
                Spacer()
                
                DossierRiskLevelBadge(riskLevel: analysis.riskLevel)
                
                Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(DXYColors.textTertiary)
                    .padding(.leading, ScaleFactor.padding(8))
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private var chiefComplaintSection: some View {
        AnalysisSectionView(
            title: "主诉",
            icon: "text.quote",
            content: analysis.chiefComplaint
        )
    }
    
    private var symptomsSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "list.bullet")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("症状列表")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            FlowLayout(spacing: ScaleFactor.spacing(8)) {
                ForEach(analysis.symptoms, id: \.self) { symptom in
                    Text(symptom)
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textSecondary)
                        .padding(.horizontal, ScaleFactor.padding(10))
                        .padding(.vertical, ScaleFactor.padding(6))
                        .background(Color.white.opacity(0.8))
                        .clipShape(Capsule())
                }
            }
        }
    }
    
    private var diagnosisSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "stethoscope")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("可能诊断")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            VStack(spacing: ScaleFactor.spacing(10)) {
                ForEach(analysis.possibleDiagnosis) { diagnosis in
                    DiagnosisProgressBar(name: diagnosis.name, confidence: diagnosis.confidence)
                }
            }
            .padding(ScaleFactor.padding(12))
            .background(Color.white.opacity(0.6))
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
        }
    }
    
    private var recommendationsSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "lightbulb")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("处理建议")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                ForEach(Array(analysis.recommendations.enumerated()), id: \.offset) { index, recommendation in
                    HStack(alignment: .top, spacing: ScaleFactor.spacing(8)) {
                        Text("\(index + 1).")
                            .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                            .foregroundColor(DXYColors.teal)
                        Text(recommendation)
                            .font(.system(size: AdaptiveFont.subheadline))
                            .foregroundColor(DXYColors.textSecondary)
                    }
                }
            }
        }
    }
    
    private var visitReminderSection: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: AdaptiveFont.body))
                .foregroundColor(.orange)
            
            Text(analysis.visitUrgency ?? "建议及时就医")
                .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                .foregroundColor(.orange)
        }
        .padding(ScaleFactor.padding(12))
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.orange.opacity(0.15))
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
    }
    
    private var disclaimerSection: some View {
        HStack(spacing: ScaleFactor.spacing(6)) {
            Image(systemName: "info.circle")
                .font(.system(size: AdaptiveFont.caption))
            Text("AI 分析仅供参考，不构成医疗诊断建议")
                .font(.system(size: AdaptiveFont.caption))
        }
        .foregroundColor(DXYColors.textTertiary)
        .padding(.top, ScaleFactor.padding(4))
    }
}

struct AnalysisSectionView: View {
    let title: String
    let icon: String
    let content: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text(title)
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            Text(content)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textSecondary)
                .lineSpacing(4)
        }
    }
}

struct DiagnosisProgressBar: View {
    let name: String
    let confidence: Double
    
    var barColor: Color {
        if confidence >= 0.7 { return DossierColors.riskHigh }
        if confidence >= 0.4 { return DossierColors.riskMedium }
        return DossierColors.riskLow
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
            HStack {
                Text(name)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textPrimary)
                
                Spacer()
                
                Text("\(Int(confidence * 100))%")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(barColor)
            }
            
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.gray.opacity(0.15))
                        .frame(height: 6)
                    
                    RoundedRectangle(cornerRadius: 3)
                        .fill(barColor)
                        .frame(width: geometry.size.width * confidence, height: 6)
                        .animation(.easeOut(duration: 0.5), value: confidence)
                }
            }
            .frame(height: 6)
        }
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrangeSubviews(proposal: proposal, subviews: subviews)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrangeSubviews(proposal: proposal, subviews: subviews)
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x,
                                      y: bounds.minY + result.positions[index].y),
                         proposal: .unspecified)
        }
    }
    
    private func arrangeSubviews(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        var positions: [CGPoint] = []
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var lineHeight: CGFloat = 0
        var maxWidth: CGFloat = 0
        
        let maxProposedWidth = proposal.width ?? .infinity
        
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            
            if currentX + size.width > maxProposedWidth && currentX > 0 {
                currentX = 0
                currentY += lineHeight + spacing
                lineHeight = 0
            }
            
            positions.append(CGPoint(x: currentX, y: currentY))
            lineHeight = max(lineHeight, size.height)
            currentX += size.width + spacing
            maxWidth = max(maxWidth, currentX - spacing)
        }
        
        return (CGSize(width: maxWidth, height: currentY + lineHeight), positions)
    }
}

#Preview {
    let mockAnalysis = AIAnalysis(
        chiefComplaint: "手臂出现红色皮疹，伴有瘙痒",
        symptoms: ["红色斑疹", "轻度瘙痒", "局部肿胀"],
        possibleDiagnosis: [
            Diagnosis(name: "过敏性皮炎", confidence: 0.78),
            Diagnosis(name: "湿疹", confidence: 0.15),
            Diagnosis(name: "接触性皮炎", confidence: 0.07)
        ],
        recommendations: [
            "避免搔抓患处",
            "保持皮肤清洁干燥",
            "可使用炉甘石洗剂止痒",
            "如症状加重请及时就医"
        ],
        riskLevel: .medium,
        needOfflineVisit: true,
        visitUrgency: "建议3天内到皮肤科门诊就诊"
    )
    
    return ScrollView {
        AIAnalysisCardView(analysis: mockAnalysis)
            .padding()
    }
    .background(DXYColors.background)
}
