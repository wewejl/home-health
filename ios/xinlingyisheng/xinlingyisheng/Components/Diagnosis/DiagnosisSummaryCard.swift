import SwiftUI

/// 诊断卡片视图
struct DiagnosisSummaryCard: View {
    let card: DiagnosisCard
    let onViewDossier: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            // 顶部：风险徽章
            headerSection
            
            // 症状总结
            Text(card.summary)
                .font(.system(size: AdaptiveFont.body))
                .foregroundColor(DXYColors.textPrimary)
                .lineSpacing(4)
            
            // 鉴别诊断
            if !card.conditions.isEmpty {
                conditionsSection
            }
            
            // 推理步骤
            if !card.reasoningSteps.isEmpty {
                reasoningSection
            }
            
            // 护理建议
            if !card.carePlan.isEmpty {
                carePlanSection
            }
            
            // 引用证据（可折叠）
            if !card.references.isEmpty {
                referencesSection
            }
            
            // CTA 按钮
            Button(action: onViewDossier) {
                Text("查看/生成病历")
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DXYColors.teal)
                    .cornerRadius(AdaptiveSize.cornerRadiusSmall)
            }
            .padding(.top, ScaleFactor.padding(4))
        }
        .padding(ScaleFactor.padding(20))
        .background(Color.white)
        .cornerRadius(AdaptiveSize.cornerRadiusLarge)
        .shadow(color: Color.black.opacity(0.08), radius: 8, x: 0, y: 4)
    }
    
    // MARK: - Header Section
    private var headerSection: some View {
        HStack {
            RiskLevelBadge(level: card.riskLevel)
            Spacer()
            if card.needOfflineVisit {
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: AdaptiveFont.footnote))
                    Text("建议线下就诊")
                        .font(.system(size: AdaptiveFont.footnote))
                }
                .foregroundColor(.orange)
            }
        }
    }
    
    // MARK: - Conditions Section
    private var conditionsSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "stethoscope")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("可能的诊断")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            ForEach(Array(card.conditions.enumerated()), id: \.offset) { _, condition in
                ConditionRowView(condition: condition)
            }
        }
    }
    
    // MARK: - Reasoning Section
    private var reasoningSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "brain")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("推理过程")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            ReasoningTimelineView(steps: card.reasoningSteps)
        }
    }
    
    // MARK: - Care Plan Section
    private var carePlanSection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "heart.text.square")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("护理建议")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                ForEach(card.carePlan, id: \.self) { tip in
                    HStack(alignment: .top, spacing: ScaleFactor.spacing(6)) {
                        Text("•")
                            .foregroundColor(DXYColors.teal)
                        Text(tip)
                            .font(.system(size: AdaptiveFont.subheadline))
                            .foregroundColor(DXYColors.textSecondary)
                    }
                }
            }
        }
    }
    
    // MARK: - References Section
    private var referencesSection: some View {
        DisclosureGroup {
            EvidenceListView(refs: card.references)
        } label: {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "book")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                Text("引用证据 (\(card.references.count))")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
        }
        .tint(DXYColors.teal)
    }
}

// MARK: - Risk Level Badge
struct RiskLevelBadge: View {
    let level: String
    
    var badgeColor: Color {
        switch level.lowercased() {
        case "emergency": return .red
        case "high": return .orange
        case "medium": return .yellow
        default: return .green
        }
    }
    
    var displayText: String {
        switch level.lowercased() {
        case "emergency": return "紧急"
        case "high": return "高风险"
        case "medium": return "中风险"
        default: return "低风险"
        }
    }
    
    var body: some View {
        Text(displayText)
            .font(.system(size: AdaptiveFont.footnote, weight: .medium))
            .foregroundColor(.white)
            .padding(.horizontal, ScaleFactor.padding(10))
            .padding(.vertical, ScaleFactor.padding(4))
            .background(badgeColor)
            .cornerRadius(AdaptiveSize.cornerRadiusSmall)
    }
}

// MARK: - Condition Row View
struct ConditionRowView: View {
    let condition: DiagnosisCondition
    
    var barColor: Color {
        if condition.confidence >= 0.7 { return .orange }
        if condition.confidence >= 0.4 { return .yellow }
        return .green
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
            HStack {
                Text(condition.name)
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                Spacer()
                Text("\(Int(condition.confidence * 100))%")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(barColor)
            }
            
            // 进度条
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.gray.opacity(0.15))
                        .frame(height: 6)
                    
                    RoundedRectangle(cornerRadius: 3)
                        .fill(barColor)
                        .frame(width: geometry.size.width * condition.confidence, height: 6)
                }
            }
            .frame(height: 6)
            
            // 依据
            if !condition.rationale.isEmpty {
                FlowLayout(spacing: ScaleFactor.spacing(4)) {
                    ForEach(condition.rationale, id: \.self) { reason in
                        Text(reason)
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.textTertiary)
                            .padding(.horizontal, ScaleFactor.padding(6))
                            .padding(.vertical, ScaleFactor.padding(2))
                            .background(DXYColors.tagBackground)
                            .cornerRadius(4)
                    }
                }
            }
        }
        .padding(ScaleFactor.padding(12))
        .background(DXYColors.background)
        .cornerRadius(AdaptiveSize.cornerRadiusSmall)
    }
}

// MARK: - Reasoning Timeline View
struct ReasoningTimelineView: View {
    let steps: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(Array(steps.enumerated()), id: \.offset) { index, step in
                HStack(alignment: .top, spacing: ScaleFactor.spacing(10)) {
                    // 时间线圆点和线
                    VStack(spacing: 0) {
                        Circle()
                            .fill(DXYColors.teal)
                            .frame(width: 8, height: 8)
                        
                        if index < steps.count - 1 {
                            Rectangle()
                                .fill(DXYColors.teal.opacity(0.3))
                                .frame(width: 2, height: 24)
                        }
                    }
                    
                    Text(step)
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DXYColors.textSecondary)
                        .padding(.bottom, index < steps.count - 1 ? ScaleFactor.padding(16) : 0)
                }
            }
        }
    }
}

// MARK: - Evidence List View
struct EvidenceListView: View {
    let refs: [KnowledgeRef]
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            ForEach(refs) { ref in
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    Text(ref.title)
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Text(ref.snippet)
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textSecondary)
                        .lineLimit(2)
                    
                    if let source = ref.source {
                        Text("来源: \(source)")
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.teal)
                    }
                }
                .padding(ScaleFactor.padding(10))
                .background(DXYColors.background)
                .cornerRadius(AdaptiveSize.cornerRadiusSmall)
            }
        }
        .padding(.top, ScaleFactor.padding(8))
    }
}

// MARK: - Preview
#Preview {
    ScrollView {
        DiagnosisSummaryCard(
            card: DiagnosisCard(
                summary: "手臂出现红色皮疹，伴有瘙痒，已持续3天。皮损呈对称分布，边界较清楚。",
                conditions: [
                    DiagnosisCondition(name: "湿疹", confidence: 0.8, rationale: ["红疹", "瘙痒", "对称分布"]),
                    DiagnosisCondition(name: "接触性皮炎", confidence: 0.5, rationale: ["外露部位", "边界清楚"])
                ],
                riskLevel: "low",
                needOfflineVisit: false,
                urgency: nil,
                carePlan: ["保持皮肤清洁干燥", "避免抓挠患处", "可使用温和保湿霜"],
                references: [
                    KnowledgeRef(id: "ref-001", title: "湿疹诊疗指南", snippet: "湿疹是一种常见的皮肤炎症...", source: "中华皮肤科杂志")
                ],
                reasoningSteps: ["收集症状信息", "分析皮损特征", "检索医学文献", "生成鉴别诊断"]
            ),
            onViewDossier: {}
        )
        .padding()
    }
    .background(DXYColors.background)
}
