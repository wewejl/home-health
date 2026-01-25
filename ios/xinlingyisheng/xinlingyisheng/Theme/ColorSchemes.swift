import SwiftUI

// MARK: - 颜色主题枚举（已弃用）
/// 固定为治愈系紫色主题，不再支持主题切换
@available(*, deprecated, message: "使用 DXYColors 替代 - 已统一使用治愈系颜色")
enum ColorScheme: String, CaseIterable {
    case elegantPurple = "优雅紫韵"
    case deepOcean = "深海蓝调"
    case forestGreen = "森林绿意"
    case sunsetWarm = "日落暖橙"
    case minimalistGray = "极简灰度"

    var primaryColor: Color {
        switch self {
        case .elegantPurple:
            return DXYColors.primaryPurple
        case .deepOcean:
            return Color(red: 0.15, green: 0.35, blue: 0.65)
        case .forestGreen:
            return DXYColors.teal
        case .sunsetWarm:
            return DXYColors.orange
        case .minimalistGray:
            return Color(red: 0.30, green: 0.32, blue: 0.35)
        }
    }

    var secondaryColor: Color {
        switch self {
        case .elegantPurple:
            return DXYColors.lightPurple
        case .deepOcean:
            return Color(red: 0.25, green: 0.50, blue: 0.75)
        case .forestGreen:
            return HealingColorTheme.softSage
        case .sunsetWarm:
            return HealingColorTheme.mutedCoral
        case .minimalistGray:
            return Color(red: 0.50, green: 0.52, blue: 0.55)
        }
    }

    var accentColor: Color {
        switch self {
        case .elegantPurple:
            return DXYColors.teal
        case .deepOcean:
            return Color(red: 0.40, green: 0.70, blue: 0.90)
        case .forestGreen:
            return HealingColorTheme.successGreen
        case .sunsetWarm:
            return HealingColorTheme.terracotta
        case .minimalistGray:
            return Color(red: 0.70, green: 0.72, blue: 0.75)
        }
    }

    var gradientColors: [Color] {
        [primaryColor, primaryColor.opacity(0.7)]
    }
}

// MARK: - 主题颜色（已弃用）
@available(*, deprecated, message: "使用 DXYColors 替代")
struct PremiumColorTheme {
    static var current: ColorScheme = .elegantPurple

    static let backgroundLight = DXYColors.background
    static let backgroundDark = DXYColors.background.opacity(0.9)
    static let cardLight = DXYColors.cardBackground.opacity(0.75)
    static let cardDark = DXYColors.cardBackground.opacity(0.75)
    static let textPrimary = DXYColors.textPrimary
    static let textSecondary = DXYColors.textSecondary
    static let textTertiary = DXYColors.textTertiary
    static let successColor = HealingColorTheme.successGreen

    static var primaryColor: Color { DXYColors.primaryPurple }
    static var secondaryColor: Color { DXYColors.teal }
    static var accentColor: Color { DXYColors.orange }
    static var gradientColors: [Color] { HealingColorTheme.gradientColors }
}
