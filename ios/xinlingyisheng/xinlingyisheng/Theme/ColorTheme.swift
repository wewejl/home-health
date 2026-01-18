import SwiftUI

struct ColorTheme {
    static let primaryIndigo = Color(red: 0.25, green: 0.32, blue: 0.71)
    static let primaryTeal = Color(red: 0.20, green: 0.73, blue: 0.69)
    static let accentGreen = Color(red: 0.40, green: 0.85, blue: 0.55)
    
    static let backgroundLight = Color(red: 0.97, green: 0.97, blue: 0.98)
    static let backgroundDark = Color(red: 0.08, green: 0.08, blue: 0.12)
    
    static let cardLight = Color.white.opacity(0.7)
    static let cardDark = Color(red: 0.15, green: 0.15, blue: 0.20).opacity(0.7)
    
    static let textPrimary = Color.primary
    static let textSecondary = Color.secondary
    static let textTertiary = Color.gray.opacity(0.6)
}

extension Color {
    static func dynamicColor(light: Color, dark: Color) -> Color {
        return Color(UIColor { traitCollection in
            return traitCollection.userInterfaceStyle == .dark ?
                UIColor(dark) : UIColor(light)
        })
    }
}
