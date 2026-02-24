import SwiftUI

// MARK: - 思考气泡视图
/// 显示 AI 思考过程的组件
/// 支持：思考中动画、折叠/展开、完整思考历史
struct ThinkingBubbleView: View {
    let thinkingState: ThinkingState
    @Binding var isExpanded: Bool

    @State private var isPulsing = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // 思考标题栏
            header

            // 思考内容区
            if isExpanded {
                content
                    .transition(.asymmetric(
                        insertion: .opacity.combined(with: .move(edge: .top)),
                        removal: .opacity.combined(with: .move(edge: .top))
                    ))
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.blue.opacity(0.08))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.blue.opacity(0.2), lineWidth: 1)
        )
    }

    // MARK: - 思考标题栏
    private var header: some View {
        HStack(spacing: 8) {
            // 图标
            Image(systemName: iconName)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(iconColor)
                .symbolEffect(.pulse, options: .repeating, isActive: isThinking)

            // 标题
            Text(titleText)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.primary)

            Spacer()

            // 展开/收起按钮
            if hasContent {
                Button(action: {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                        isExpanded.toggle()
                    }
                }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - 思考内容
    private var content: some View {
        VStack(alignment: .leading, spacing: 10) {
            switch thinkingState {
            case .idle:
                EmptyView()

            case .thinking:
                // 思考中占位
                HStack(spacing: 8) {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("正在分析您的描述...")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)

            case .completed(let entries):
                // 完整思考历史
                ForEach(entries) { entry in
                    ThoughtEntryView(entry: entry)
                }
            }
        }
    }

    // MARK: - 计算属性
    private var isThinking: Bool {
        if case .thinking = thinkingState {
            return true
        }
        return false
    }

    private var hasContent: Bool {
        switch thinkingState {
        case .idle:
            return false
        case .thinking:
            return false
        case .completed(let entries):
            return !entries.isEmpty
        }
    }

    private var iconName: String {
        switch thinkingState {
        case .idle:
            return "brain"
        case .thinking:
            return "brain.head.profile"
        case .completed:
            return "checkmark.circle.fill"
        }
    }

    private var iconColor: Color {
        switch thinkingState {
        case .idle:
            return .secondary
        case .thinking:
            return .blue
        case .completed:
            return .green
        }
    }

    private var titleText: String {
        switch thinkingState {
        case .idle:
            return "AI 思考过程"
        case .thinking:
            return "正在思考..."
        case .completed(let entries):
            return "思考完成 (\(entries.count) 步)"
        }
    }
}

// MARK: - 单条思考条目视图
struct ThoughtEntryView: View {
    let entry: ThoughtEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // 步骤标题
            HStack(spacing: 6) {
                // 步骤编号
                Text("步骤 \(entry.step)")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        RoundedRectangle(cornerRadius: 4)
                            .fill(stepColor)
                    )

                // 动作标签
                if !entry.action.isEmpty {
                    Text(actionText)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }

                Spacer()

                // 工具标签
                if let tool = entry.toolUsed {
                    Text(tool)
                        .font(.system(size: 10))
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(
                            RoundedRectangle(cornerRadius: 4)
                                .fill(Color.purple)
                        )
                }
            }

            // 思考内容
            Text(entry.thought)
                .font(.system(size: 12))
                .foregroundColor(.primary)
                .lineLimit(nil)
                .fixedSize(horizontal: false, vertical: true)

            // 意图分析（如果有）
            if let intent = entry.intentAnalysis, !intent.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "lightbulb")
                        .font(.system(size: 10))
                        .foregroundColor(.orange)
                    Text(intent)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }

            // 状态评估（如果有）
            if let assessment = entry.stateAssessment, !assessment.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "chart.bar.doc.horizontal")
                        .font(.system(size: 10))
                        .foregroundColor(.blue)
                    Text(assessment)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 10)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.gray.opacity(0.08))
        )
    }

    private var stepColor: Color {
        switch entry.step {
        case 1:
            return .blue
        case 2:
            return .green
        case 3:
            return .orange
        default:
            return .purple
        }
    }

    private var actionText: String {
        switch entry.action {
        case "respond":
            return "回复用户"
        case "ask_question":
            return "追问"
        case "use_tool":
            return "使用工具"
        case "complete":
            return "完成"
        default:
            return entry.action
        }
    }
}

// MARK: - 预览
#Preview("思考中") {
    VStack(alignment: .leading, spacing: 12) {
        ThinkingBubbleView(
            thinkingState: .thinking,
            isExpanded: .constant(false)
        )

        ThinkingBubbleView(
            thinkingState: .thinking,
            isExpanded: .constant(true)
        )
    }
    .padding()
    .background(Color(uiColor: .systemGroupedBackground))
}

#Preview("思考完成") {
    let sampleEntries = [
        ThoughtEntry(
            step: 1,
            thought: "用户描述了手臂红斑、瘙痒症状，需要了解持续时间和诱因",
            intentAnalysis: "用户意图：诊断皮肤问题",
            stateAssessment: "已知：部位（手臂）、症状（红斑、瘙痒）",
            decision: "询问持续时间",
            action: "ask_question"
        ),
        ThoughtEntry(
            step: 2,
            thought: "用户表示症状持续3天，可能与使用新洗衣液有关",
            intentAnalysis: "获得关键信息：持续时间3天，可能的诱因",
            decision: "提供初步建议",
            action: "respond"
        )
    ]

    return VStack(alignment: .leading, spacing: 12) {
        ThinkingBubbleView(
            thinkingState: .completed(sampleEntries),
            isExpanded: .constant(true)
        )
    }
    .padding()
    .background(Color(uiColor: .systemGroupedBackground))
}

#Preview("折叠状态") {
    let sampleEntries = [
        ThoughtEntry(
            step: 1,
            thought: "分析用户输入...",
            action: "analyze"
        ),
        ThoughtEntry(
            step: 2,
            thought: "调用知识库查询...",
            action: "use_tool",
            toolUsed: "knowledge_search"
        )
    ]

    return VStack(alignment: .leading, spacing: 12) {
        ThinkingBubbleView(
            thinkingState: .completed(sampleEntries),
            isExpanded: .constant(false)
        )
    }
    .padding()
    .background(Color(uiColor: .systemGroupedBackground))
}
