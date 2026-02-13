import SwiftUI

// MARK: - 病历模块专用颜色
struct DossierColors {
    // MARK: - 基础颜色
    static let background = Color(red: 0.97, green: 0.97, blue: 0.95)      // #F7F7F2 浅米色
    static let teal = Color(red: 0.20, green: 0.70, blue: 0.60)            // #33B399 青色
    static let blue = Color(red: 0.20, green: 0.60, blue: 0.90)              // #3399FF 蓝色
    static let primaryPurple = Color(red: 0.55, green: 0.20, blue: 0.65)     // #8C33CC 紫色
    static let orange = Color(red: 1.0, green: 0.70, blue: 0.24)      // #FFB33D 橙色
    static let successGreen = Color(red: 0.30, green: 0.72, blue: 0.52)        // #4DB885 绿色
    static let textPrimary = Color(red: 0.20, green: 0.20, blue: 0.20)     // #333333 深灰
    static let textSecondary = Color(red: 0.42, green: 0.42, blue: 0.40)    // #6B6B66 中灰
    static let textTertiary = Color(red: 0.62, green: 0.62, blue: 0.60)     // #9E9E99 浅灰
    static let lightPurple = Color(red: 0.55, green: 0.20, blue: 0.65).opacity(0.3)  // 浅紫半透明
    static let cardBackground = Color.white

    // MARK: - 风险等级颜色
    static let riskLow = Color(red: 0.30, green: 0.72, blue: 0.52)        // #4DB885 绿色
    static let riskMedium = Color(red: 1.0, green: 0.70, blue: 0.24)      // #FFB33D 橙色
    static let riskHigh = Color(red: 0.94, green: 0.33, blue: 0.31)       // #F0544F 红色
    static let riskEmergency = Color(red: 0.80, green: 0.15, blue: 0.15)  // #CC2626 深红

    // MARK: - 事件状态颜色
    static let statusInProgress = DossierColors.riskLow                          // 进行中 - 青绿
    static let statusCompleted = Color(red: 0.60, green: 0.60, blue: 0.65) // 已完成 - 灰色
    static let statusExported = Color(red: 0.55, green: 0.20, blue: 0.65)  // 已导出 - 紫色

    // MARK: - 时间轴颜色
    static let timelineConnector = Color(red: 0.90, green: 0.90, blue: 0.92) // 连接线
    static let timelineNodeActive = DossierColors.riskLow                         // 活跃节点 - 青绿
    static let timelineNodeInactive = Color(red: 0.80, green: 0.80, blue: 0.82) // 非活跃节点

    // MARK: - 卡片背景渐变
    static let analysisCardGradient = LinearGradient(
        colors: [
            DossierColors.riskLow.opacity(0.08),
            DossierColors.statusExported.opacity(0.04)
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    // MARK: - 边框颜色
    static let cardBorder = Color(red: 0.90, green: 0.90, blue: 0.92)

    // MARK: - 分割线颜色
    static let divider = Color(red: 0.93, green: 0.93, blue: 0.94)

    // MARK: - 标签背景
    static let tagBackground = Color(red: 0.95, green: 0.95, blue: 0.96)

    // MARK: - 搜索背景
    static let searchBackground = Color(red: 0.96, green: 0.96, blue: 0.97)
}
