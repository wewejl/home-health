import SwiftUI

// MARK: - 动态功能按钮视图
/// 根据智能体能力动态渲染功能按钮
/// 无需为每个科室写专属逻辑，自动根据 capabilities 展示
struct DynamicActionButtonsView: View {
    let capabilities: AgentCapabilities
    let onActionTap: (AgentAction) -> Void
    let isDisabled: Bool
    
    init(
        capabilities: AgentCapabilities,
        isDisabled: Bool = false,
        onActionTap: @escaping (AgentAction) -> Void
    ) {
        self.capabilities = capabilities
        self.isDisabled = isDisabled
        self.onActionTap = onActionTap
    }
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(availableActions, id: \.self) { action in
                    ActionButton(action: action, isDisabled: isDisabled) {
                        onActionTap(action)
                    }
                }
            }
            .padding(.horizontal, 16)
        }
        .frame(height: 60)
        .background(Color.clear)
    }
    
    private var availableActions: [AgentAction] {
        capabilities.actions
            .compactMap { AgentAction(rawValue: $0) }
            .filter { $0 != .conversation } // 排除基础对话，只显示特殊功能
    }
}

// MARK: - 单个动作按钮
struct ActionButton: View {
    let action: AgentAction
    let isDisabled: Bool
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 6) {
                Image(systemName: action.icon)
                    .font(.system(size: 16))
                Text(action.displayName)
                    .font(.system(size: 14, weight: .medium))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                isDisabled 
                    ? Color.gray.opacity(0.1)
                    : action.buttonColor.opacity(0.1)
            )
            .foregroundColor(isDisabled ? .gray : action.buttonColor)
            .cornerRadius(20)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(
                        isDisabled ? Color.gray.opacity(0.3) : action.buttonColor.opacity(0.3),
                        lineWidth: 1
                    )
            )
        }
        .disabled(isDisabled)
    }
}

// MARK: - AgentAction 按钮样式扩展
extension AgentAction {
    var buttonColor: Color {
        switch self {
        case .conversation:
            return .blue
        case .analyzeSkin:
            return Color(red: 0.0, green: 0.6, blue: 0.6) // Teal
        case .interpretReport:
            return Color(red: 0.5, green: 0.3, blue: 0.7) // Purple
        case .interpretECG:
            return Color(red: 0.9, green: 0.3, blue: 0.3) // Red
        }
    }
}

// MARK: - 统一快捷选项视图
struct UnifiedQuickOptionsView: View {
    let options: [QuickOption]
    let onOptionTap: (QuickOption) -> Void
    
    var body: some View {
        if !options.isEmpty {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(options) { option in
                        Button(action: { onOptionTap(option) }) {
                            Text(option.text)
                                .font(.system(size: 13))
                                .padding(.horizontal, 12)
                                .padding(.vertical, 8)
                                .background(Color.blue.opacity(0.1))
                                .foregroundColor(.blue)
                                .cornerRadius(16)
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
            }
        }
    }
}

// MARK: - 上传操作按钮视图
/// 当用户触发需要上传图片的动作时显示
struct UploadActionButtonsView: View {
    let action: AgentAction
    let isUploading: Bool
    let isAnalyzing: Bool
    let onCameraTap: () -> Void
    let onLibraryTap: () -> Void
    
    var body: some View {
        VStack(spacing: 12) {
            // 提示文本
            Text(action.uploadHint)
                .font(.system(size: 13))
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            // 按钮组
            HStack(spacing: 16) {
                // 拍照按钮
                Button(action: onCameraTap) {
                    HStack(spacing: 6) {
                        Image(systemName: "camera.fill")
                            .font(.system(size: 16))
                        Text("拍照")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(action.buttonColor)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
                .disabled(isUploading || isAnalyzing)
                
                // 相册按钮
                Button(action: onLibraryTap) {
                    HStack(spacing: 6) {
                        Image(systemName: "photo.fill")
                            .font(.system(size: 16))
                        Text("相册")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color.gray.opacity(0.1))
                    .foregroundColor(action.buttonColor)
                    .cornerRadius(12)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(action.buttonColor.opacity(0.3), lineWidth: 1)
                    )
                }
                .disabled(isUploading || isAnalyzing)
            }
            
            // 状态提示
            if isUploading {
                HStack(spacing: 8) {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("正在上传...")
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                }
            } else if isAnalyzing {
                HStack(spacing: 8) {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("正在分析...")
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

// MARK: - AgentAction 上传提示扩展
extension AgentAction {
    var uploadHint: String {
        switch self {
        case .analyzeSkin:
            return "请拍摄或上传皮肤问题照片\n光线充足、皮损居中、对焦清晰"
        case .interpretReport:
            return "请上传检查报告图片\n确保文字清晰可读"
        case .interpretECG:
            return "请上传心电图图片\n确保图像完整清晰"
        default:
            return "请上传图片"
        }
    }
}

// MARK: - Preview
#if DEBUG
struct DynamicActionButtonsView_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            // 皮肤科能力
            DynamicActionButtonsView(
                capabilities: AgentCapabilities(
                    actions: ["conversation", "analyze_skin", "interpret_report"],
                    acceptsMedia: ["image/jpeg"],
                    uiComponents: ["TextBubble"],
                    description: "皮肤科"
                ),
                onActionTap: { _ in }
            )
            
            // 心内科能力
            DynamicActionButtonsView(
                capabilities: AgentCapabilities(
                    actions: ["conversation", "interpret_ecg"],
                    acceptsMedia: ["image/jpeg"],
                    uiComponents: ["TextBubble"],
                    description: "心内科"
                ),
                onActionTap: { _ in }
            )
            
            // 上传按钮示例
            UploadActionButtonsView(
                action: .analyzeSkin,
                isUploading: false,
                isAnalyzing: false,
                onCameraTap: {},
                onLibraryTap: {}
            )
            .padding()
        }
        .padding()
    }
}
#endif
