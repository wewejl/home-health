import SwiftUI

/// 中间建议卡片视图
struct AdviceCardView: View {
    let advice: AdviceEntry
    let onAccept: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            // 标题 + 标签
            HStack {
                Text("💡 \(advice.category ?? "建议")")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DossierColors.textPrimary)

                Spacer()

                Text("初步建议")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DossierColors.teal)
                    .padding(.horizontal, ScaleFactor.padding(8))
                    .padding(.vertical, ScaleFactor.padding(4))
                    .background(DossierColors.teal.opacity(0.1))
                    .cornerRadius(AdaptiveSize.cornerRadiusSmall)
            }

            // 内容
            Text(advice.advice)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DossierColors.textPrimary)
                .lineSpacing(4)

            // 推理依据
            if let symptoms = advice.relatedSymptoms, !symptoms.isEmpty {
                FlowLayout(spacing: ScaleFactor.spacing(4)) {
                    ForEach(symptoms, id: \.self) { symptom in
                        Text(symptom)
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DossierColors.textSecondary)
                            .padding(.horizontal, ScaleFactor.padding(8))
                            .padding(.vertical, ScaleFactor.padding(4))
                            .background(DossierColors.background)
                            .cornerRadius(AdaptiveSize.cornerRadiusSmall)
                    }
                }
            }

            // 采纳按钮
            Button(action: onAccept) {
                Text("好的，知道了")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DossierColors.teal)
            }
            .padding(.top, ScaleFactor.padding(4))
        }
        .padding(ScaleFactor.padding(16))
        .background(DossierColors.teal.opacity(0.05))
        .cornerRadius(AdaptiveSize.cornerRadius)
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 16) {
        AdviceCardView(
            advice: AdviceEntry(
                advice: "根据您描述的症状，建议您先保持皮肤清洁干燥，避免抓挠患处。可以适当使用温和的保湿霜。",
                reasoning: "收集症状信息，分析皮损特征，检索医学文献，生成鉴别诊断",
                category: "皮肤护理",
                relatedSymptoms: ["红斑", "丘疹", "瘙痒"],
                timestamp: Date()
            ),
            onAccept: {}
        )

        AdviceCardView(
            advice: AdviceEntry(
                advice: "请注意观察皮疹的变化情况，如果出现扩散或加重，请及时就医。",
                reasoning: "分析皮损分布，评估疾病进展",
                category: "病情观察",
                relatedSymptoms: ["颜色变化", "面积扩大"],
                timestamp: Date()
            ),
            onAccept: {}
        )
    }
    .padding()
}
