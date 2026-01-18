import SwiftUI

// MARK: - 专科数据渲染视图
// 根据 AgentResponseV2 的 specialtyData 动态渲染专科特有的 UI 组件

struct SpecialtyDataView: View {
    let specialtyData: SpecialtyDataV2
    let agentType: AgentType
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 根据智能体类型渲染不同的组件
            switch agentType {
            case .dermatology:
                dermatologyView
            case .cardiology:
                cardiologyView
            case .general, .orthopedics:
                generalView
            }
        }
    }
    
    // MARK: - 皮肤科视图
    @ViewBuilder
    private var dermatologyView: some View {
        // 症状列表
        if let symptoms = specialtyData.symptoms, !symptoms.isEmpty {
            SymptomsTagView(symptoms: symptoms)
        }
        
        // 诊断卡
        if let diagnosisCard = specialtyData.diagnosisCard {
            DiagnosisCardViewV2(card: diagnosisCard)
        }
    }
    
    // MARK: - 心内科视图
    @ViewBuilder
    private var cardiologyView: some View {
        // 诊断卡（如果有）
        if let diagnosisCard = specialtyData.diagnosisCard {
            DiagnosisCardViewV2(card: diagnosisCard)
        }
        
        // 症状列表
        if let symptoms = specialtyData.symptoms, !symptoms.isEmpty {
            SymptomsTagView(symptoms: symptoms)
        }
    }
    
    // MARK: - 通用视图
    @ViewBuilder
    private var generalView: some View {
        if let symptoms = specialtyData.symptoms, !symptoms.isEmpty {
            SymptomsTagView(symptoms: symptoms)
        }
        
        if let diagnosisCard = specialtyData.diagnosisCard {
            DiagnosisCardViewV2(card: diagnosisCard)
        }
    }
}

// MARK: - 症状标签视图
struct SymptomsTagView: View {
    let symptoms: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("已收集症状")
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.secondary)
            
            FlowLayoutV2(spacing: 8) {
                ForEach(symptoms, id: \.self) { symptom in
                    Text(symptom)
                        .font(.caption)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(Color.blue.opacity(0.1))
                        .foregroundColor(.blue)
                        .cornerRadius(12)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - 诊断卡视图 V2
struct DiagnosisCardViewV2: View {
    let card: DiagnosisCardV2
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 标题
            HStack {
                Image(systemName: "stethoscope")
                    .foregroundColor(.blue)
                Text("初步分析")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            // 摘要
            Text(card.summary)
                .font(.body)
                .foregroundColor(.primary)
            
            // 诊断条目
            if let conditions = card.conditions, !conditions.isEmpty {
                Divider()
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("可能情况")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)
                    
                    ForEach(conditions, id: \.name) { condition in
                        HStack {
                            Text(condition.name)
                                .font(.subheadline)
                            Spacer()
                            ConfidenceBadge(confidence: condition.confidence)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }
}

// MARK: - 置信度徽章
struct ConfidenceBadge: View {
    let confidence: Double
    
    var color: Color {
        if confidence >= 0.7 {
            return .green
        } else if confidence >= 0.4 {
            return .orange
        } else {
            return .gray
        }
    }
    
    var body: some View {
        Text("\(Int(confidence * 100))%")
            .font(.caption)
            .fontWeight(.medium)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.15))
            .foregroundColor(color)
            .cornerRadius(8)
    }
}

// MARK: - 进度指示器
struct ConsultationProgressView: View {
    let stage: ConsultationStage
    let progress: Int
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(stage.displayName)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                Spacer()
                Text("\(progress)%")
                    .font(.caption)
                    .foregroundColor(.blue)
            }
            
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.gray.opacity(0.2))
                        .frame(height: 4)
                        .cornerRadius(2)
                    
                    Rectangle()
                        .fill(Color.blue)
                        .frame(width: geometry.size.width * CGFloat(progress) / 100, height: 4)
                        .cornerRadius(2)
                }
            }
            .frame(height: 4)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

// MARK: - 风险等级徽章 V2
struct RiskLevelBadgeV2: View {
    let riskLevel: RiskLevel
    
    var backgroundColor: Color {
        switch riskLevel {
        case .low: return .green.opacity(0.15)
        case .medium: return .orange.opacity(0.15)
        case .high: return .red.opacity(0.15)
        case .emergency: return .purple.opacity(0.15)
        }
    }
    
    var foregroundColor: Color {
        switch riskLevel {
        case .low: return .green
        case .medium: return .orange
        case .high: return .red
        case .emergency: return .purple
        }
    }
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: riskLevel == .emergency ? "exclamationmark.triangle.fill" : "shield.fill")
                .font(.caption2)
            Text(riskLevel.displayName)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(backgroundColor)
        .foregroundColor(foregroundColor)
        .cornerRadius(12)
    }
}

// MARK: - Flow Layout V2 (自动换行布局)
struct FlowLayoutV2: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResultV2(in: proposal.replacingUnspecifiedDimensions().width, subviews: subviews, spacing: spacing)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResultV2(in: bounds.width, subviews: subviews, spacing: spacing)
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x, y: bounds.minY + result.positions[index].y), proposal: .unspecified)
        }
    }
    
    struct FlowResultV2 {
        var size: CGSize = .zero
        var positions: [CGPoint] = []
        
        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var rowHeight: CGFloat = 0
            
            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)
                
                if x + size.width > maxWidth && x > 0 {
                    x = 0
                    y += rowHeight + spacing
                    rowHeight = 0
                }
                
                positions.append(CGPoint(x: x, y: y))
                rowHeight = max(rowHeight, size.height)
                x += size.width + spacing
                
                self.size.width = max(self.size.width, x)
            }
            
            self.size.height = y + rowHeight
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        SymptomsTagView(symptoms: ["红疹", "瘙痒", "脱皮", "肿胀"])
        
        ConsultationProgressView(stage: .diagnosing, progress: 80)
        
        HStack {
            RiskLevelBadgeV2(riskLevel: .low)
            RiskLevelBadgeV2(riskLevel: .medium)
            RiskLevelBadgeV2(riskLevel: .high)
            RiskLevelBadgeV2(riskLevel: .emergency)
        }
    }
    .padding()
}
