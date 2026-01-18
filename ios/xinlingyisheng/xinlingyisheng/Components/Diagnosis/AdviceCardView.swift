import SwiftUI

/// 中间建议卡片视图
struct AdviceCardView: View {
    let advice: AdviceEntry
    let onAccept: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            // 标题 + 标签
            HStack {
                Text("💡 \(advice.title)")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Spacer()
                
                Text("初步建议")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.teal)
                    .padding(.horizontal, ScaleFactor.padding(8))
                    .padding(.vertical, ScaleFactor.padding(4))
                    .background(DXYColors.teal.opacity(0.1))
                    .cornerRadius(AdaptiveSize.cornerRadiusSmall)
            }
            
            // 内容
            Text(advice.content)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
                .lineSpacing(4)
            
            // 依据标签
            if !advice.evidence.isEmpty {
                FlowLayout(spacing: ScaleFactor.spacing(4)) {
                    ForEach(advice.evidence, id: \.self) { evidence in
                        Text(evidence)
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textSecondary)
                            .padding(.horizontal, ScaleFactor.padding(8))
                            .padding(.vertical, ScaleFactor.padding(4))
                            .background(DXYColors.background)
                            .cornerRadius(AdaptiveSize.cornerRadiusSmall)
                    }
                }
            }
            
            // 采纳按钮
            Button(action: onAccept) {
                Text("好的，知道了")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.teal)
            }
            .padding(.top, ScaleFactor.padding(4))
        }
        .padding(ScaleFactor.padding(16))
        .background(DXYColors.teal.opacity(0.05))
        .cornerRadius(AdaptiveSize.cornerRadius)
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 16) {
        AdviceCardView(
            advice: AdviceEntry(
                id: "adv-001",
                title: "初步护理建议",
                content: "根据您描述的症状，建议您先保持皮肤清洁干燥，避免抓挠患处。可以适当使用温和的保湿霜。",
                evidence: ["湿疹护理指南", "皮肤科临床手册"],
                timestamp: "2026-01-16T10:00:00"
            ),
            onAccept: {}
        )
        
        AdviceCardView(
            advice: AdviceEntry(
                id: "adv-002",
                title: "观察建议",
                content: "请注意观察皮疹的变化情况，如果出现扩散或加重，请及时就医。",
                evidence: [],
                timestamp: "2026-01-16T10:05:00"
            ),
            onAccept: {}
        )
    }
    .padding()
}
