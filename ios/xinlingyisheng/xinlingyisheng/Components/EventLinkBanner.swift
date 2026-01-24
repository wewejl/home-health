import SwiftUI

// MARK: - 病历事件关联状态
enum EventLinkStatus {
    case none
    case creating
    case linked(eventId: String, title: String, isNew: Bool)
    case completed(eventId: String, title: String)
    case error(message: String)

    var isLinked: Bool {
        switch self {
        case .linked, .completed: return true
        default: return false
        }
    }

    var eventId: String? {
        switch self {
        case .linked(let id, _, _), .completed(let id, _): return id
        default: return nil
        }
    }
}

// MARK: - 事件关联横幅组件 - 自适应布局
struct EventLinkBanner: View {
    let status: EventLinkStatus
    var onTap: (() -> Void)?

    @State private var isAnimating = false

    var body: some View {
        Button(action: { onTap?() }) {
            HStack(spacing: ScaleFactor.spacing(10)) {
                iconView

                VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                    titleText
                    subtitleText
                }

                Spacer()

                if case .linked = status {
                    Image(systemName: "chevron.right")
                        .font(.system(size: AdaptiveFont.caption, weight: .medium))
                        .foregroundColor(DXYColors.textTertiary)
                }

                if case .completed = status {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DossierColors.riskLow)
                }
            }
            .padding(.horizontal, ScaleFactor.padding(14))
            .padding(.vertical, ScaleFactor.padding(10))
            .background(backgroundColor)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                    .stroke(borderColor, lineWidth: ScaleFactor.size(1))
            )
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(status.eventId == nil)
        .onAppear {
            if case .creating = status {
                withAnimation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true)) {
                    isAnimating = true
                }
            }
        }
    }

    @ViewBuilder
    private var iconView: some View {
        switch status {
        case .none:
            EmptyView()

        case .creating:
            Circle()
                .fill(DXYColors.teal.opacity(0.15))
                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                .overlay(
                    ProgressView()
                        .scaleEffect(0.7)
                        .tint(DXYColors.teal)
                )

        case .linked(_, _, let isNew):
            Circle()
                .fill(isNew ? DXYColors.teal.opacity(0.15) : Color.orange.opacity(0.15))
                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                .overlay(
                    Image(systemName: isNew ? "doc.badge.plus" : "doc.badge.arrow.up")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(isNew ? DXYColors.teal : .orange)
                )

        case .completed:
            Circle()
                .fill(DossierColors.riskLow.opacity(0.15))
                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                .overlay(
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DossierColors.riskLow)
                )

        case .error:
            Circle()
                .fill(Color.red.opacity(0.15))
                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                .overlay(
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(.red)
                )
        }
    }

    private var titleText: some View {
        Group {
            switch status {
            case .none:
                EmptyView()

            case .creating:
                Text("正在创建病历记录...")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(DXYColors.textSecondary)

            case .linked(_, _, let isNew):
                Text(isNew ? "已创建病历记录" : "已关联病历记录")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(isNew ? DXYColors.teal : .orange)

            case .completed:
                Text("病历记录已完成")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(DossierColors.riskLow)

            case .error:
                Text("病历记录创建失败")
                    .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                    .foregroundColor(.red)
            }
        }
    }

    private var subtitleText: some View {
        Group {
            switch status {
            case .none:
                EmptyView()

            case .creating:
                Text("问诊内容将自动保存")
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)

            case .linked(_, let title, _):
                Text(title)
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)
                    .lineLimit(1)

            case .completed(_, let title):
                Text(title)
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)
                    .lineLimit(1)

            case .error(let message):
                Text(message)
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textTertiary)
                    .lineLimit(1)
            }
        }
    }

    private var backgroundColor: Color {
        switch status {
        case .none: return .clear
        case .creating: return DXYColors.teal.opacity(0.05)
        case .linked(_, _, let isNew): return isNew ? DXYColors.teal.opacity(0.05) : Color.orange.opacity(0.05)
        case .completed: return DossierColors.riskLow.opacity(0.05)
        case .error: return Color.red.opacity(0.05)
        }
    }

    private var borderColor: Color {
        switch status {
        case .none: return .clear
        case .creating: return DXYColors.teal.opacity(0.2)
        case .linked(_, _, let isNew): return isNew ? DXYColors.teal.opacity(0.2) : Color.orange.opacity(0.2)
        case .completed: return DossierColors.riskLow.opacity(0.2)
        case .error: return Color.red.opacity(0.2)
        }
    }
}

// MARK: - 问诊完成卡片 - 自适应布局
struct ConsultationCompleteCard: View {
    let eventTitle: String
    let eventId: String
    var onViewEvent: (() -> Void)?
    var onNewConsultation: (() -> Void)?

    var body: some View {
        VStack(spacing: ScaleFactor.spacing(16)) {
            // 成功图标
            ZStack {
                Circle()
                    .fill(DossierColors.riskLow.opacity(0.15))
                    .frame(width: ScaleFactor.size(64), height: ScaleFactor.size(64))

                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: AdaptiveFont.title1))
                    .foregroundColor(DossierColors.riskLow)
            }

            // 标题
            VStack(spacing: ScaleFactor.spacing(4)) {
                Text("问诊已完成")
                    .font(.system(size: AdaptiveFont.title3, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)

                Text("本次问诊记录已自动保存到病历资料夹")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textSecondary)
                    .multilineTextAlignment(.center)
            }

            // 事件卡片预览
            HStack(spacing: ScaleFactor.spacing(12)) {
                Circle()
                    .fill(DepartmentType.dermatology.color.opacity(0.15))
                    .frame(width: ScaleFactor.size(40), height: ScaleFactor.size(40))
                    .overlay(
                        Image(systemName: DepartmentType.dermatology.icon)
                            .font(.system(size: AdaptiveFont.body))
                            .foregroundColor(DepartmentType.dermatology.color)
                    )

                VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                    Text(eventTitle)
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                        .lineLimit(1)

                    Text("皮肤科 · 刚刚完成")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(DXYColors.textTertiary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.caption, weight: .medium))
                    .foregroundColor(DXYColors.textTertiary)
            }
            .padding(ScaleFactor.padding(12))
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
            .shadow(color: Color.black.opacity(0.06), radius: ScaleFactor.size(8), x: 0, y: ScaleFactor.size(2))
            .onTapGesture { onViewEvent?() }

            // 操作按钮
            HStack(spacing: ScaleFactor.spacing(12)) {
                Button(action: { onNewConsultation?() }) {
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Image(systemName: "plus.circle")
                            .font(.system(size: AdaptiveFont.subheadline))
                        Text("新问诊")
                            .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    }
                    .foregroundColor(DXYColors.teal)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DXYColors.teal.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(10)))
                }

                Button(action: { onViewEvent?() }) {
                    HStack(spacing: ScaleFactor.spacing(6)) {
                        Image(systemName: "doc.text")
                            .font(.system(size: AdaptiveFont.subheadline))
                        Text("查看病历")
                            .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DXYColors.teal)
                    .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(10)))
                }
            }
        }
        .padding(ScaleFactor.padding(20))
        .background(DXYColors.background)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 16) {
        EventLinkBanner(status: .creating)
        
        EventLinkBanner(status: .linked(eventId: "123", title: "手臂红疹问诊", isNew: true))
        
        EventLinkBanner(status: .linked(eventId: "123", title: "手臂红疹问诊", isNew: false))
        
        EventLinkBanner(status: .completed(eventId: "123", title: "手臂红疹问诊"))
        
        EventLinkBanner(status: .error(message: "网络连接失败"))
        
        Divider().padding(.vertical)
        
        ConsultationCompleteCard(
            eventTitle: "手臂红疹问诊",
            eventId: "123",
            onViewEvent: {},
            onNewConsultation: {}
        )
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
