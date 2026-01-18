import SwiftUI

// MARK: - 快捷功能芯片
/// 符合设计规范的快捷功能芯片组件
/// 用于输入栏上方的功能快捷入口
struct QuickActionChip: View {
    let icon: String
    let title: String
    let color: Color
    var isDisabled: Bool = false
    var action: () -> Void
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: {
            if !isDisabled {
                // 触感反馈
                let impactFeedback = UIImpactFeedbackGenerator(style: .light)
                impactFeedback.impactOccurred()
                action()
            }
        }) {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.subheadline))
                
                Text(title)
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
            }
            .foregroundColor(isDisabled ? color.opacity(0.5) : color)
            .padding(.horizontal, ScaleFactor.padding(12))
            .padding(.vertical, ScaleFactor.padding(8))
            .background(
                RoundedRectangle(cornerRadius: ScaleFactor.size(16))
                    .fill(isDisabled ? color.opacity(0.06) : color.opacity(0.12))
            )
            .scaleEffect(isPressed ? 0.95 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isPressed)
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(isDisabled)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in 
                    if !isDisabled { isPressed = true }
                }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - 快捷功能芯片行
/// 水平滚动的快捷功能芯片容器
struct QuickActionChipRow: View {
    let actions: [QuickAction]
    var isDisabled: Bool = false
    var onActionTap: (QuickAction) -> Void
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: ScaleFactor.spacing(12)) {
                ForEach(actions, id: \.id) { action in
                    QuickActionChip(
                        icon: action.icon,
                        title: action.title,
                        color: action.color,
                        isDisabled: isDisabled,
                        action: { onActionTap(action) }
                    )
                }
            }
            .padding(.horizontal, ScaleFactor.padding(16))
        }
    }
}

// MARK: - 快捷功能模型
struct QuickAction: Identifiable, Equatable {
    let id: String
    let icon: String
    let title: String
    let color: Color
    let actionType: ActionType
    
    enum ActionType: String {
        case photoAnalysis = "photo_analysis"
        case medicalDossier = "medical_dossier"
        case symptomAssessment = "symptom_assessment"
        case appointment = "appointment"
    }
    
    // 预定义的快捷功能
    static let photoAnalysis = QuickAction(
        id: "photo_analysis",
        icon: "camera.fill",
        title: "拍照分析",
        color: Color(red: 0.23, green: 0.51, blue: 0.96), // 蓝色
        actionType: .photoAnalysis
    )
    
    static let medicalDossier = QuickAction(
        id: "medical_dossier",
        icon: "folder.fill",
        title: "病历资料夹",
        color: Color(red: 0.36, green: 0.27, blue: 1.0), // 紫色 DXYColors.primaryPurple
        actionType: .medicalDossier
    )
    
    static let symptomAssessment = QuickAction(
        id: "symptom_assessment",
        icon: "list.clipboard.fill",
        title: "症状评估",
        color: Color(red: 0.20, green: 0.77, blue: 0.75), // 青色 DXYColors.teal
        actionType: .symptomAssessment
    )
    
    static let appointment = QuickAction(
        id: "appointment",
        icon: "calendar.badge.plus",
        title: "预约转诊",
        color: Color(red: 1.0, green: 0.60, blue: 0.24), // 橙色 DXYColors.orange
        actionType: .appointment
    )
    
    // 皮肤科默认功能
    static var dermatologyActions: [QuickAction] {
        [.photoAnalysis, .medicalDossier, .symptomAssessment]
    }
    
    // 通用科室功能
    static var generalActions: [QuickAction] {
        [.medicalDossier, .symptomAssessment]
    }
}

// MARK: - 从AgentCapabilities转换
extension QuickAction {
    /// 根据智能体能力生成快捷功能列表
    static func from(capabilities: AgentCapabilities?) -> [QuickAction] {
        guard let caps = capabilities else {
            return generalActions
        }
        
        var actions: [QuickAction] = []
        
        for actionName in caps.actions {
            switch actionName {
            case "analyze_skin", "analyzeSkin":
                actions.append(.photoAnalysis)
            case "medical_dossier", "medicalDossier":
                actions.append(.medicalDossier)
            case "symptom_assessment", "symptomAssessment":
                actions.append(.symptomAssessment)
            case "appointment":
                actions.append(.appointment)
            default:
                break
            }
        }
        
        // 确保至少有病历资料夹功能
        if !actions.contains(where: { $0.actionType == .medicalDossier }) {
            actions.append(.medicalDossier)
        }
        
        return actions
    }
}

// MARK: - 带标题的快捷功能区
struct QuickActionSection: View {
    let title: String?
    let actions: [QuickAction]
    var isDisabled: Bool = false
    var onActionTap: (QuickAction) -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            if let title = title {
                Text(title)
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(DXYColors.textSecondary)
                    .padding(.horizontal, ScaleFactor.padding(16))
            }
            
            QuickActionChipRow(
                actions: actions,
                isDisabled: isDisabled,
                onActionTap: onActionTap
            )
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        // 单个芯片
        HStack {
            QuickActionChip(
                icon: "camera.fill",
                title: "拍照分析",
                color: .blue,
                action: { print("Photo") }
            )
            
            QuickActionChip(
                icon: "folder.fill",
                title: "病历资料夹",
                color: .purple,
                action: { print("Dossier") }
            )
            
            QuickActionChip(
                icon: "list.clipboard.fill",
                title: "症状评估",
                color: .teal,
                isDisabled: true,
                action: { print("Assessment") }
            )
        }
        
        Divider()
        
        // 芯片行
        QuickActionChipRow(
            actions: QuickAction.dermatologyActions,
            onActionTap: { action in
                print("Tapped: \(action.title)")
            }
        )
        
        Divider()
        
        // 带标题的区域
        QuickActionSection(
            title: "快捷功能",
            actions: QuickAction.dermatologyActions,
            onActionTap: { action in
                print("Section tapped: \(action.title)")
            }
        )
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
