import SwiftUI

// MARK: - 现代医疗问诊界面设计系统
// 基于 Soft UI Evolution + Minimalism 风格

// MARK: - 颜色系统（已迁移到统一的 DXYColors）
@available(*, deprecated, message: "使用 DXYColors 替代")
struct MedicalColors {
    // 使用统一的治愈系颜色
    static let primaryBlue = DXYColors.blue
    static let primaryBlueLight = DXYColors.blue.opacity(0.8)
    static let primaryBlueDark = DXYColors.blue.opacity(0.8)

    static let secondaryTeal = DXYColors.teal
    static let secondaryTealLight = DXYColors.teal.opacity(0.8)

    static let ctaOrange = DXYColors.orange
    static let successGreen = HealingColorTheme.successGreen

    // 使用治愈系暖色背景
    static let bgPrimary = DXYColors.background
    static let bgSecondary = DXYColors.searchBackground
    static let bgCard = DXYColors.cardBackground

    static let textPrimary = DXYColors.textPrimary
    static let textSecondary = DXYColors.textSecondary
    static let textMuted = DXYColors.textTertiary

    static let borderLight = HealingColorTheme.borderLight
    static let borderMedium = HealingColorTheme.borderMedium

    static let statusInfo = DXYColors.blue
    static let statusSuccess = HealingColorTheme.successGreen
    static let statusWarning = DXYColors.orange
    static let statusError = HealingColorTheme.errorRed

    static let aiMessageBg = DXYColors.primaryPurple.opacity(0.08)
    static let userMessageBg = DXYColors.primaryPurple

    static let hoverBg = DXYColors.searchBackground
    static let activeBg = HealingColorTheme.borderLight
}

// MARK: - 字体系统（使用统一的 UnifiedFont）
struct MedicalTypography {
    // Headings
    static let h1 = Font.system(size: UnifiedFont.largeTitle, weight: .bold)
    static let h2 = Font.system(size: UnifiedFont.title1, weight: .semibold)
    static let h3 = Font.system(size: UnifiedFont.title2, weight: .semibold)
    static let h4 = Font.system(size: UnifiedFont.title3, weight: .medium)

    // Body
    static let bodyLarge = Font.system(size: UnifiedFont.body, weight: .regular)
    static let bodyMedium = Font.system(size: UnifiedFont.subheadline, weight: .regular)
    static let bodySmall = Font.system(size: UnifiedFont.footnote, weight: .regular)

    // Special
    static let caption = Font.system(size: UnifiedFont.caption1)  // 已废弃
    static let caption1 = Font.system(size: UnifiedFont.caption1)
    static let caption2 = Font.system(size: UnifiedFont.caption2)
    static let button = Font.system(size: UnifiedFont.body, weight: .semibold)
    static let badge = Font.system(size: UnifiedFont.caption1, weight: .medium)
}

// MARK: - 间距系统
struct MedicalSpacing {
    static let xs: CGFloat = ScaleFactor.spacing(4)
    static let sm: CGFloat = ScaleFactor.spacing(8)
    static let md: CGFloat = ScaleFactor.spacing(12)
    static let lg: CGFloat = ScaleFactor.spacing(16)
    static let xl: CGFloat = ScaleFactor.spacing(24)
    static let xxl: CGFloat = ScaleFactor.spacing(32)

    // Semantic Spacing
    static let cardPadding: CGFloat = LayoutConstants.cardPadding
    static let sectionSpacing: CGFloat = LayoutConstants.sectionSpacing
    static let elementSpacing: CGFloat = ScaleFactor.spacing(12)
}

// MARK: - 圆角系统
struct MedicalCornerRadius {
    static let sm: CGFloat = LayoutConstants.cornerRadiusSmall
    static let md: CGFloat = ScaleFactor.size(12)
    static let lg: CGFloat = LayoutConstants.cornerRadius
    static let xl: CGFloat = ScaleFactor.size(20)
    static let full: CGFloat = 999
}

// MARK: - 阴影系统
struct MedicalShadows {
    static func card() -> some View {
        Color.black.opacity(0.06)
    }

    static let cardRadius: CGFloat = 12
    static let cardY: CGFloat = 4

    static let elevatedRadius: CGFloat = 20
    static let elevatedY: CGFloat = 8

    static let floatingRadius: CGFloat = 24
    static let floatingY: CGFloat = 12
}

// MARK: - Color Hex Extension
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
