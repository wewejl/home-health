import SwiftUI

// MARK: - 治愈系日式诊所风格颜色系统
/// 统一的应用颜色系统 - 替代旧的 MedicalColors 和 PremiumColorTheme
/// 设计理念：温暖、自然、治愈，营造舒适的问诊环境

struct HealingColorTheme {
    // MARK: - 主色系 - 柔和的鼠尾草绿

    /// 浅鼠尾草 - 用于浅色背景点缀
    static let softSage = Color(red: 0.71, green: 0.82, blue: 0.76)          // #B5D1C2

    /// 深鼠尾草 - 用于强调色
    static let deepSage = Color(red: 0.45, green: 0.62, blue: 0.54)          // #739E89

    /// 森林雾 - 主品牌色（紫色系）
    static let forestMist = Color(red: 0.32, green: 0.48, blue: 0.42)        // #517A6B

    // MARK: - 温暖系 - 奶油与陶土

    /// 奶油色 - 主背景色
    static let warmCream = Color(red: 0.97, green: 0.95, blue: 0.91)         // #F7F2E8

    /// 桃桃色 - 用于浅色背景
    static let softPeach = Color(red: 0.96, green: 0.90, blue: 0.85)         // #F5E6D9

    /// 陶土色 - 强调色
    static let terracotta = Color(red: 0.82, green: 0.52, blue: 0.42)        // #D1856B

    /// 暖沙色 - 用于搜索背景、卡片背景
    static let warmSand = Color(red: 0.88, green: 0.82, blue: 0.74)          // #E0D2BD

    // MARK: - 点缀色

    /// 柔和珊瑚色 - 用于提示、警告
    static let mutedCoral = Color(red: 0.90, green: 0.62, blue: 0.55)        // #E69E8D

    /// 尘雾蓝 - 用于信息类图标
    static let dustyBlue = Color(red: 0.65, green: 0.72, blue: 0.80)         // #A6B8CC

    /// 薰雾紫 - 用于中性状态
    static let lavenderHaze = Color(red: 0.78, green: 0.73, blue: 0.85)      // #C7BAD9

    // MARK: - 背景色

    /// 主背景色
    static let background = warmCream

    /// 卡片背景色
    static let cardBackground = Color.white

    /// 搜索/二级背景
    static let searchBackground = warmSand

    /// 标签背景
    static let tagBackground = warmSand.opacity(0.6)

    // MARK: - 文字颜色

    /// 主要文字
    static let textPrimary = Color(red: 0.22, green: 0.22, blue: 0.20)       // #383833

    /// 次要文字
    static let textSecondary = Color(red: 0.42, green: 0.42, blue: 0.40)      // #6B6B66

    /// 辅助文字
    static let textTertiary = Color(red: 0.62, green: 0.62, blue: 0.60)      // #9E9E99

    /// 弱化文字（占位符等）
    static let textMuted = Color(red: 0.70, green: 0.70, blue: 0.70)         // #B3B3B3

    // MARK: - 功能色

    /// 主色 - 品牌紫
    static let primaryPurple = forestMist

    /// 浅紫色 - 用于背景点缀
    static let lightPurple = softSage.opacity(0.3)

    /// 青色 - 成功/确认
    static let teal = deepSage

    /// 蓝色 - 信息类
    static let blue = dustyBlue

    /// 橙色 - 警告/强调
    static let orange = terracotta

    /// 成功绿
    static let successGreen = Color(red: 0.30, green: 0.72, blue: 0.52)   // 保持原有绿色

    /// 错误红
    static let errorRed = Color(red: 0.85, green: 0.35, blue: 0.35)

    // MARK: - 边框颜色

    /// 浅色边框
    static let borderLight = Color(red: 0.85, green: 0.80, blue: 0.75)

    /// 中等边框
    static let borderMedium = Color(red: 0.70, green: 0.65, blue: 0.60)

    // MARK: - 渐变色

    /// 品牌渐变
    static let gradientColors: [Color] = [softSage, deepSage]

    /// 主色渐变
    static let primaryGradient = LinearGradient(
        colors: [softSage, deepSage],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    // MARK: - 透明度变体

    /// 主色半透明背景
    static let primaryBackground = primaryPurple.opacity(0.12)

    /// 次色半透明背景
    static let secondaryBackground = softSage.opacity(0.08)
}

// MARK: - AppColor 兼容层 - 指向统一的 DXYColors
/// 全局统一颜色访问点，重定向到 DXYColors
/// 所有代码应优先使用 DXYColors，AppColor 仅为兼容保留
@available(*, deprecated, message: "使用 DXYColors 替代")
struct AppColor {
    // 背景色
    static let background = DXYColors.background
    static let cardBackground = DXYColors.cardBackground
    static let searchBackground = DXYColors.searchBackground
    static let tagBackground = DXYColors.tagBackground

    // 文字色
    static let textPrimary = DXYColors.textPrimary
    static let textSecondary = DXYColors.textSecondary
    static let textTertiary = DXYColors.textTertiary
    static let textMuted = DXYColors.textTertiary

    // 品牌色
    static let primaryPurple = DXYColors.primaryPurple
    static let lightPurple = DXYColors.lightPurple
    static let teal = DXYColors.teal
    static let blue = DXYColors.blue
    static let orange = DXYColors.orange

    // 功能色
    static let successGreen = HealingColorTheme.successGreen
    static let errorRed = HealingColorTheme.errorRed

    // 边框
    static let borderLight = HealingColorTheme.borderLight
    static let borderMedium = HealingColorTheme.borderMedium

    // 其他
    static let promotionPurple = DXYColors.promotionPurple
    static let promotionOrange = DXYColors.promotionOrange

    // 渐变
    static let gradientColors = HealingColorTheme.gradientColors
    static let primaryGradient = HealingColorTheme.primaryGradient
}
