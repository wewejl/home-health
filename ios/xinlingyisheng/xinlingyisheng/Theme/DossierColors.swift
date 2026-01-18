import SwiftUI

// MARK: - 病历模块专用颜色
struct DossierColors {
    // 风险等级颜色
    static let riskLow = Color(red: 0.30, green: 0.72, blue: 0.52)        // #4DB885 绿色
    static let riskMedium = Color(red: 1.0, green: 0.70, blue: 0.24)      // #FFB33D 橙色
    static let riskHigh = Color(red: 0.94, green: 0.33, blue: 0.31)       // #F0544F 红色
    static let riskEmergency = Color(red: 0.80, green: 0.15, blue: 0.15)  // #CC2626 深红
    
    // 事件状态颜色
    static let statusInProgress = DXYColors.teal                          // 进行中 - 青绿
    static let statusCompleted = Color(red: 0.60, green: 0.60, blue: 0.65) // 已完成 - 灰色
    static let statusExported = DXYColors.primaryPurple                   // 已导出 - 紫色
    
    // 时间轴颜色
    static let timelineConnector = Color(red: 0.90, green: 0.90, blue: 0.92) // 连接线
    static let timelineNodeActive = DXYColors.teal                         // 活跃节点
    static let timelineNodeInactive = Color(red: 0.80, green: 0.80, blue: 0.82) // 非活跃节点
    
    // 卡片背景渐变
    static let analysisCardGradient = LinearGradient(
        colors: [
            DXYColors.teal.opacity(0.08),
            DXYColors.primaryPurple.opacity(0.04)
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
    
    // 边框颜色
    static let cardBorder = Color(red: 0.90, green: 0.90, blue: 0.92)
    
    // 分割线颜色
    static let divider = Color(red: 0.93, green: 0.93, blue: 0.94)
}
