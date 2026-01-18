import SwiftUI

// MARK: - 现代医疗问诊界面设计系统
// 基于 Soft UI Evolution + Minimalism 风格

// MARK: - 颜色系统
struct MedicalColors {
    // Primary Colors - 医疗蓝
    static let primaryBlue = Color(hex: "#3B82F6")
    static let primaryBlueLight = Color(hex: "#60A5FA")
    static let primaryBlueDark = Color(hex: "#2563EB")
    
    // Secondary Colors - 青色
    static let secondaryTeal = Color(hex: "#0891B2")
    static let secondaryTealLight = Color(hex: "#22D3EE")
    
    // CTA & Success
    static let ctaOrange = Color(hex: "#F97316")
    static let successGreen = Color(hex: "#059669")
    
    // Background
    static let bgPrimary = Color(hex: "#F8FAFC")
    static let bgSecondary = Color(hex: "#ECFEFF")
    static let bgCard = Color(hex: "#FFFFFF")
    
    // Text
    static let textPrimary = Color(hex: "#1E293B")
    static let textSecondary = Color(hex: "#475569")
    static let textMuted = Color(hex: "#64748B")
    
    // Border
    static let borderLight = Color(hex: "#E2E8F0")
    static let borderMedium = Color(hex: "#CBD5E1")
    
    // Status Colors
    static let statusInfo = primaryBlue
    static let statusSuccess = successGreen
    static let statusWarning = Color(hex: "#F59E0B")
    static let statusError = Color(hex: "#EF4444")
    
    // AI Message Background
    static let aiMessageBg = Color(hex: "#EFF6FF")
    static let userMessageBg = primaryBlue
    
    // Hover & Active States
    static let hoverBg = Color(hex: "#F1F5F9")
    static let activeBg = Color(hex: "#E2E8F0")
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
