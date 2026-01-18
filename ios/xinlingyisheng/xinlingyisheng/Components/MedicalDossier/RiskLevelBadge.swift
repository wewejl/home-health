import SwiftUI

struct DossierRiskLevelBadge: View {
    let riskLevel: DossierRiskLevel
    var style: BadgeStyle = .default
    
    enum BadgeStyle {
        case `default`
        case compact
        case large
    }
    
    var body: some View {
        HStack(spacing: spacing) {
            if style != .compact {
                Circle()
                    .fill(riskLevel.color)
                    .frame(width: dotSize, height: dotSize)
            }
            
            Text(riskLevel.displayName)
                .font(.system(size: fontSize, weight: .medium))
                .foregroundColor(riskLevel.color)
        }
        .padding(.horizontal, horizontalPadding)
        .padding(.vertical, verticalPadding)
        .background(riskLevel.color.opacity(0.12))
        .clipShape(Capsule())
    }
    
    private var spacing: CGFloat {
        switch style {
        case .default: return ScaleFactor.spacing(4)
        case .compact: return 0
        case .large: return ScaleFactor.spacing(6)
        }
    }
    
    private var dotSize: CGFloat {
        switch style {
        case .default: return ScaleFactor.size(6)
        case .compact: return 0
        case .large: return ScaleFactor.size(8)
        }
    }
    
    private var fontSize: CGFloat {
        switch style {
        case .default: return AdaptiveFont.footnote
        case .compact: return AdaptiveFont.caption
        case .large: return AdaptiveFont.subheadline
        }
    }
    
    private var horizontalPadding: CGFloat {
        switch style {
        case .default: return ScaleFactor.padding(8)
        case .compact: return ScaleFactor.padding(6)
        case .large: return ScaleFactor.padding(12)
        }
    }
    
    private var verticalPadding: CGFloat {
        switch style {
        case .default: return ScaleFactor.padding(4)
        case .compact: return ScaleFactor.padding(3)
        case .large: return ScaleFactor.padding(6)
        }
    }
}

struct AttachmentCountBadge: View {
    let icon: String
    let count: Int
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(4)) {
            Image(systemName: icon)
                .font(.system(size: AdaptiveFont.caption))
            Text("\(count)")
                .font(.system(size: AdaptiveFont.caption, weight: .medium))
        }
        .foregroundColor(DXYColors.textSecondary)
        .padding(.horizontal, ScaleFactor.padding(8))
        .padding(.vertical, ScaleFactor.padding(4))
        .background(DXYColors.tagBackground)
        .clipShape(Capsule())
    }
}

#Preview {
    VStack(spacing: 16) {
        HStack(spacing: 12) {
            DossierRiskLevelBadge(riskLevel: .low)
            DossierRiskLevelBadge(riskLevel: .medium)
            DossierRiskLevelBadge(riskLevel: .high)
            DossierRiskLevelBadge(riskLevel: .emergency)
        }
        
        HStack(spacing: 12) {
            DossierRiskLevelBadge(riskLevel: .low, style: .compact)
            DossierRiskLevelBadge(riskLevel: .medium, style: .compact)
        }
        
        HStack(spacing: 12) {
            AttachmentCountBadge(icon: "camera.fill", count: 4)
            AttachmentCountBadge(icon: "doc.text.fill", count: 2)
        }
    }
    .padding()
}
