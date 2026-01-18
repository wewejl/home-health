import SwiftUI

struct RelatedEventRow: View {
    let relatedEvent: FindRelatedResponse.RelatedEvent
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            Circle()
                .fill(relationColor)
                .frame(width: 8, height: 8)
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(relatedEvent.event_id.prefix(8) + "...")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    if let relationType = relatedEvent.relation_type {
                        Text(relationDisplayName(relationType))
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(.white)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(relationColor)
                            .clipShape(Capsule())
                    }
                }
                
                if let reasoning = relatedEvent.reasoning {
                    Text(reasoning)
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textSecondary)
                        .lineLimit(2)
                }
                
                if let confidence = relatedEvent.confidence {
                    HStack(spacing: 4) {
                        Image(systemName: "chart.bar.fill")
                            .font(.system(size: 10))
                        Text("置信度: \(Int(confidence * 100))%")
                            .font(.system(size: AdaptiveFont.caption))
                    }
                    .foregroundColor(DXYColors.textTertiary)
                }
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textTertiary)
        }
        .padding(ScaleFactor.padding(12))
        .background(DXYColors.background)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
    
    private var relationColor: Color {
        guard let relationType = relatedEvent.relation_type else {
            return DXYColors.textTertiary
        }
        
        switch relationType {
        case "same_condition":
            return DXYColors.primaryPurple
        case "follow_up":
            return DXYColors.teal
        case "complication":
            return Color.orange
        case "unrelated":
            return DXYColors.textTertiary
        default:
            return DXYColors.textSecondary
        }
    }
    
    private func relationDisplayName(_ type: String) -> String {
        switch type {
        case "same_condition": return "同一病情"
        case "follow_up": return "随访"
        case "complication": return "并发症"
        case "unrelated": return "不相关"
        default: return type
        }
    }
}

#Preview {
    let mockEvent = FindRelatedResponse.RelatedEvent(
        event_id: "abc123-def456-ghi789",
        relation_type: "same_condition",
        confidence: 0.88,
        reasoning: "7天前的同科室问诊，症状相似"
    )
    
    return RelatedEventRow(relatedEvent: mockEvent)
        .padding()
        .background(Color.white)
}
