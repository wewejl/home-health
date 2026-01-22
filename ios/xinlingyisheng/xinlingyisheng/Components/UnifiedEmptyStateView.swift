import SwiftUI

// MARK: - 统一空状态组件
/// 用于显示空状态的通用组件，支持多种预设样式和自定义配置
struct UnifiedEmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    var action: EmptyStateAction?

    var body: some View {
        VStack(spacing: ScaleFactor.spacing(16)) {
            Spacer()

            Image(systemName: icon)
                .font(.system(size: AdaptiveFont.custom(48)))
                .foregroundColor(DXYColors.textTertiary)

            VStack(spacing: ScaleFactor.spacing(4)) {
                Text(title)
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(DXYColors.textSecondary)

                Text(message)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
                    .multilineTextAlignment(.center)
            }

            if let action = action {
                Button(action: action.handler) {
                    Text(action.title)
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, ScaleFactor.padding(20))
                        .padding(.vertical, ScaleFactor.padding(10))
                        .background(DXYColors.primaryPurple)
                        .clipShape(Capsule())
                }
                .padding(.top, ScaleFactor.spacing(4))
            }

            Spacer()
        }
        .frame(maxWidth: .infinity)
        .padding()
    }
}

// MARK: - 空状态操作按钮
struct EmptyStateAction {
    let title: String
    let handler: () -> Void
}

// MARK: - 预设样式
extension UnifiedEmptyStateView {
    /// 搜索结果为空
    static func searchEmpty(query: String) -> UnifiedEmptyStateView {
        UnifiedEmptyStateView(
            icon: "magnifyingglass",
            title: "未找到相关内容",
            message: "尝试搜索其他关键词"
        )
    }

    /// 数据加载失败
    static func loadFailed(retryAction: @escaping () -> Void) -> UnifiedEmptyStateView {
        UnifiedEmptyStateView(
            icon: "exclamationmark.triangle",
            title: "加载失败",
            message: "请检查网络连接后重试",
            action: EmptyStateAction(title: "重试", handler: retryAction)
        )
    }

    /// 暂无数据
    static func noData(message: String = "暂时没有数据") -> UnifiedEmptyStateView {
        UnifiedEmptyStateView(
            icon: "tray",
            title: "暂无内容",
            message: message
        )
    }

    /// 网络错误
    static func networkError(retryAction: @escaping () -> Void) -> UnifiedEmptyStateView {
        UnifiedEmptyStateView(
            icon: "wifi.slash",
            title: "网络连接失败",
            message: "请检查网络设置",
            action: EmptyStateAction(title: "重试", handler: retryAction)
        )
    }
}

// MARK: - 预览
#Preview("基础样式") {
    UnifiedEmptyStateView(
        icon: "tray",
        title: "暂无内容",
        message: "暂时没有数据"
    )
    .background(DXYColors.background)
}

#Preview("搜索为空") {
    UnifiedEmptyStateView.searchEmpty(query: "测试")
        .background(DXYColors.background)
}

#Preview("加载失败") {
    UnifiedEmptyStateView.loadFailed(retryAction: {})
        .background(DXYColors.background)
}

#Preview("无数据") {
    UnifiedEmptyStateView.noData()
        .background(DXYColors.background)
}
