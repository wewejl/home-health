import SwiftUI

enum ColorScheme: String, CaseIterable {
    case deepOcean = "深海蓝调"
    case elegantPurple = "优雅紫韵"
    case forestGreen = "森林绿意"
    case sunsetWarm = "日落暖橙"
    case minimalistGray = "极简灰度"
    
    var primaryColor: Color {
        switch self {
        case .deepOcean:
            return Color(red: 0.15, green: 0.35, blue: 0.65)
        case .elegantPurple:
            return Color(red: 0.52, green: 0.37, blue: 0.95)
        case .forestGreen:
            return Color(red: 0.20, green: 0.55, blue: 0.45)
        case .sunsetWarm:
            return Color(red: 0.95, green: 0.50, blue: 0.35)
        case .minimalistGray:
            return Color(red: 0.30, green: 0.32, blue: 0.35)
        }
    }
    
    var secondaryColor: Color {
        switch self {
        case .deepOcean:
            return Color(red: 0.25, green: 0.60, blue: 0.85)
        case .elegantPurple:
            return Color(red: 0.75, green: 0.57, blue: 1.00)
        case .forestGreen:
            return Color(red: 0.35, green: 0.75, blue: 0.60)
        case .sunsetWarm:
            return Color(red: 0.98, green: 0.70, blue: 0.50)
        case .minimalistGray:
            return Color(red: 0.50, green: 0.52, blue: 0.55)
        }
    }
    
    var accentColor: Color {
        switch self {
        case .deepOcean:
            return Color(red: 0.40, green: 0.75, blue: 0.95)
        case .elegantPurple:
            return Color(red: 0.92, green: 0.75, blue: 1.00)
        case .forestGreen:
            return Color(red: 0.50, green: 0.90, blue: 0.70)
        case .sunsetWarm:
            return Color(red: 1.00, green: 0.85, blue: 0.65)
        case .minimalistGray:
            return Color(red: 0.70, green: 0.72, blue: 0.75)
        }
    }
    
    var gradientColors: [Color] {
        [primaryColor, secondaryColor]
    }
    
    var backgroundGlowColor: Color {
        primaryColor.opacity(0.12)
    }
    
    var secondaryGlowColor: Color {
        secondaryColor.opacity(0.08)
    }
}

@available(*, deprecated, message: "使用 AppColor 替代 - 已统一使用治愈系颜色")
struct PremiumColorTheme {
    // 固定为治愈系颜色，不再切换主题
    static var current: ColorScheme = .elegantPurple

    static let backgroundLight = AppColor.background
    static let backgroundDark = AppColor.background.opacity(0.9)

    static let cardLight = AppColor.cardBackground.opacity(0.75)
    static let cardDark = AppColor.cardBackground.opacity(0.75)

    static let textPrimary = AppColor.textPrimary
    static let textSecondary = AppColor.textSecondary
    static let textTertiary = AppColor.textTertiary
    static let successColor = AppColor.successGreen

    static var primaryColor: Color {
        AppColor.primaryPurple
    }

    static var secondaryColor: Color {
        AppColor.teal
    }

    static var accentColor: Color {
        AppColor.orange
    }

    static var gradientColors: [Color] {
        AppColor.gradientColors
    }
}
