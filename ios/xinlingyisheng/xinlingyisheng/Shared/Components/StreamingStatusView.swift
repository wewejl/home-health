import SwiftUI

// MARK: - 流式响应状态视图 (阶段 3) - 自适应布局
/// 显示 AI 思考状态和工具调用进度的视觉反馈

struct StreamingStatusView: View {
    let isThinking: Bool
    let thinkingMessage: String
    let activeToolCalls: [String]
    let completedTools: [String]
    let getToolDisplayName: (String) -> String

    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            // 思考状态
            if isThinking || !activeToolCalls.isEmpty {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    // 思考动画
                    thinkingIndicator

                    VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                        if !thinkingMessage.isEmpty {
                            Text(thinkingMessage)
                                .font(Font.system(size: AdaptiveFont.footnote, weight: .medium))
                                .foregroundColor(DossierColors.textPrimary)
                        }

                        // 工具调用进度
                        if !activeToolCalls.isEmpty {
                            Text(formatToolProgress())
                                .font(Font.system(size: AdaptiveFont.caption1))
                                .foregroundColor(DossierColors.textSecondary)
                        }
                    }

                    Spacer()
                }
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.vertical, ScaleFactor.padding(12))
                .background(DossierColors.lightPurple.opacity(0.5))
                .cornerRadius(AdaptiveSize.cornerRadiusSmall)
            }

            // 工具调用历史（显示最近完成的工具）
            if !completedTools.isEmpty {
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(6)) {
                    ForEach(completedTools, id: \.self) { tool in
                        HStack(spacing: ScaleFactor.spacing(6)) {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: AdaptiveFont.subheadline))
                                .foregroundColor(DossierColors.riskLow)

                            Text(getToolDisplayName(tool))
                                .font(Font.system(size: AdaptiveFont.caption1))
                                .foregroundColor(DossierColors.textSecondary)
                        }
                        .padding(.horizontal, ScaleFactor.padding(12))
                        .padding(.vertical, ScaleFactor.padding(6))
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(AdaptiveSize.cornerRadiusSmall / 2)
                    }
                }
                .padding(.leading, ScaleFactor.padding(16))
            }
        }
        .padding(.vertical, ScaleFactor.padding(8))
    }

    private var thinkingIndicator: some View {
        HStack(spacing: ScaleFactor.spacing(4)) {
            ForEach(0..<3) { index in
                Circle()
                    .fill(DossierColors.primaryPurple)
                    .frame(width: ScaleFactor.size(8), height: ScaleFactor.size(8))
                    .scaleEffect(thinkingScale(for: index))
                    .animation(
                        Animation.easeInOut(duration: 0.6)
                            .repeatForever(autoreverses: false)
                            .delay(Double(index) * 0.2),
                        value: isThinking || !activeToolCalls.isEmpty
                    )
            }
        }
    }

    private func thinkingScale(for index: Int) -> CGFloat {
        let offset = Double(index) * 0.2
        let time = Date().timeIntervalSince1970
        let scale = 0.8 + 0.4 * sin(time * 5 + offset)
        return scale
    }

    private func formatToolProgress() -> String {
        if activeToolCalls.isEmpty {
            return ""
        }
        let tools = activeToolCalls.map { getToolDisplayName($0) }
        return "正在: " + tools.joined(separator: " → ")
    }
}

// MARK: - 紧凑型状态指示器 - 自适应布局
/// 用于消息气泡内联显示的小型状态指示器

struct StreamingStatusIndicator: View {
    let isThinking: Bool
    let activeToolCalls: [String]

    var body: some View {
        HStack(spacing: ScaleFactor.spacing(6)) {
            if isThinking {
                HStack(spacing: ScaleFactor.spacing(3)) {
                    ForEach(0..<3) { index in
                        Circle()
                            .fill(DossierColors.primaryPurple)
                            .frame(width: ScaleFactor.size(6), height: ScaleFactor.size(6))
                            .scaleEffect(thinkingScale(for: index))
                            .animation(
                                Animation.easeInOut(duration: 0.6)
                                    .repeatForever(autoreverses: false)
                                    .delay(Double(index) * 0.2),
                                value: true
                            )
                    }
                }
            }

            if !activeToolCalls.isEmpty {
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Image(systemName: "gear")
                        .font(.system(size: AdaptiveFont.caption1))
                        .foregroundColor(DossierColors.primaryPurple)
                        .rotationEffect(.degrees(rotationAngle))
                        .animation(
                            Animation.linear(duration: 1)
                                .repeatForever(autoreverses: false),
                            value: true
                        )

                    Text(activeToolCalls.first ?? "")
                        .font(.system(size: AdaptiveFont.caption1, weight: .medium))
                        .foregroundColor(DossierColors.textSecondary)
                }
            }
        }
        .padding(.horizontal, ScaleFactor.padding(10))
        .padding(.vertical, ScaleFactor.padding(6))
        .background(DossierColors.lightPurple.opacity(0.3))
        .cornerRadius(AdaptiveSize.cornerRadiusSmall)
    }

    private func thinkingScale(for index: Int) -> CGFloat {
        let offset = Double(index) * 0.2
        let time = Date().timeIntervalSince1970
        let scale = 0.7 + 0.3 * sin(time * 5 + offset)
        return scale
    }

    private var rotationAngle: Double {
        let time = Date().timeIntervalSince1970
        return time * 360
    }
}

// MARK: - 工具调用状态卡片 - 自适应布局
/// 显示单个工具的详细执行状态

struct ToolCallStatusCard: View {
    let tool: String
    let status: String
    let getToolDisplayName: (String) -> String

    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 状态图标
            ZStack {
                Circle()
                    .fill(statusBackgroundColor.opacity(0.15))
                    .frame(width: ScaleFactor.size(40), height: ScaleFactor.size(40))

                Image(systemName: statusIcon)
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(statusBackgroundColor)
            }

            // 工具信息
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                Text(getToolDisplayName(tool))
                    .font(Font.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    .foregroundColor(DossierColors.textPrimary)

                Text(statusText)
                    .font(Font.system(size: AdaptiveFont.caption1))
                    .foregroundColor(DossierColors.textSecondary)
            }

            Spacer()
        }
        .padding(ScaleFactor.padding(12))
        .background(DossierColors.cardBackground)
        .cornerRadius(AdaptiveSize.cornerRadiusSmall)
        .shadow(color: Color.black.opacity(0.04), radius: ScaleFactor.size(8), y: ScaleFactor.size(2))
    }

    private var statusIcon: String {
        switch status {
        case "calling", "executing":
            return "gearshape.2"
        case "success":
            return "checkmark.circle.fill"
        case "error":
            return "xmark.circle.fill"
        default:
            return "circle"
        }
    }

    private var statusBackgroundColor: Color {
        switch status {
        case "calling", "executing":
            return DossierColors.primaryPurple
        case "success":
            return DossierColors.riskLow
        case "error":
            return Color.red
        default:
            return DossierColors.textTertiary
        }
    }

    private var statusText: String {
        switch status {
        case "calling":
            return "准备调用..."
        case "executing":
            return "正在执行..."
        case "success":
            return "执行完成"
        case "error":
            return "执行失败"
        default:
            return status
        }
    }
}

// MARK: - 预览

struct StreamingStatusView_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            // 思考状态
            StreamingStatusView(
                isThinking: true,
                thinkingMessage: "🤔 正在分析您的症状...",
                activeToolCalls: [],
                completedTools: [],
                getToolDisplayName: { tool in
                    switch tool {
                    case "search_medical_knowledge": return "查询医学知识"
                    case "assess_risk": return "评估风险等级"
                    default: return tool
                    }
                }
            )

            // 工具调用中
            StreamingStatusView(
                isThinking: false,
                thinkingMessage: "",
                activeToolCalls: ["search_medical_knowledge"],
                completedTools: [],
                getToolDisplayName: { tool in
                    switch tool {
                    case "search_medical_knowledge": return "查询医学知识"
                    case "assess_risk": return "评估风险等级"
                    default: return tool
                    }
                }
            )

            // 完成状态
            StreamingStatusView(
                isThinking: false,
                thinkingMessage: "",
                activeToolCalls: [],
                completedTools: ["search_medical_knowledge", "assess_risk"],
                getToolDisplayName: { tool in
                    switch tool {
                    case "search_medical_knowledge": return "查询医学知识"
                    case "assess_risk": return "评估风险等级"
                    default: return tool
                    }
                }
            )
        }
        .padding()
        .background(DossierColors.background)
    }
}
