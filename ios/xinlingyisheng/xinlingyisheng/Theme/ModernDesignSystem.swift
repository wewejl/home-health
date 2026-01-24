import SwiftUI

// MARK: - 现代医疗问诊界面设计系统
// 基于 Soft UI Evolution + Minimalism 风格

// MARK: - 颜色系统（已迁移到统一的 AppColor）
@available(*, deprecated, message: "使用 AppColor 替代")
struct MedicalColors {
    // 使用统一的治愈系颜色
    static let primaryBlue = AppColor.blue
    static let primaryBlueLight = AppColor.blue.opacity(0.8)
    static let primaryBlueDark = AppColor.blue.opacity(0.8)

    static let secondaryTeal = AppColor.teal
    static let secondaryTealLight = AppColor.teal.opacity(0.8)

    static let ctaOrange = AppColor.orange
    static let successGreen = AppColor.successGreen

    // 使用治愈系暖色背景
    static let bgPrimary = AppColor.background
    static let bgSecondary = AppColor.searchBackground
    static let bgCard = AppColor.cardBackground

    static let textPrimary = AppColor.textPrimary
    static let textSecondary = AppColor.textSecondary
    static let textMuted = AppColor.textMuted

    static let borderLight = AppColor.borderLight
    static let borderMedium = AppColor.borderMedium

    static let statusInfo = AppColor.blue
    static let statusSuccess = AppColor.successGreen
    static let statusWarning = AppColor.orange
    static let statusError = AppColor.errorRed

    static let aiMessageBg = AppColor.primaryPurple.opacity(0.08)
    static let userMessageBg = AppColor.primaryPurple

    static let hoverBg = AppColor.searchBackground
    static let activeBg = AppColor.borderLight
}

// MARK: - 字体系统
struct MedicalTypography {
    // Headings
    static let h1 = Font.system(size: 28, weight: .bold)
    static let h2 = Font.system(size: 24, weight: .semibold)
    static let h3 = Font.system(size: 20, weight: .semibold)
    static let h4 = Font.system(size: 18, weight: .medium)
    
    // Body
    static let bodyLarge = Font.system(size: 17, weight: .regular)
    static let bodyMedium = Font.system(size: 15, weight: .regular)
    static let bodySmall = Font.system(size: 13, weight: .regular)
    
    // Special
    static let caption = Font.system(size: 12, weight: .regular)
    static let button = Font.system(size: 16, weight: .semibold)
    static let badge = Font.system(size: 11, weight: .medium)
}

// MARK: - 间距系统
struct MedicalSpacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 24
    static let xxl: CGFloat = 32
    
    // Semantic Spacing
    static let cardPadding: CGFloat = 16
    static let sectionSpacing: CGFloat = 24
    static let elementSpacing: CGFloat = 12
}

// MARK: - 圆角系统
struct MedicalCornerRadius {
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 20
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
