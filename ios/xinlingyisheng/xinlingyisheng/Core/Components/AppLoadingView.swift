//
//  AppLoadingView.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一加载状态视图

import SwiftUI

/// 加载状态视图
///
/// 显示加载指示器和可选文字，支持多种样式
///
struct AppLoadingView: View {

    // MARK: - Types

    enum LoadingStyle {
        case indicator
        case text
        case both
    }

    // MARK: - Properties

    var style: LoadingStyle = .both
    var message: String?
    var isLoading: Bool = true

    // MARK: - Body

    var body: some View {
        if isLoading {
            switch style {
            case .indicator:
                ProgressView()
                    .progressViewStyle(CicularProgressViewStyle())
                    .scaleEffect(0.8)
            case .text:
                Text(message ?? "加载中...")
                    .font(.caption1)
            case .both:
                VStack(spacing: AppSpacing.small) {
                    ProgressView()
                        .progressViewStyle(CicularProgressViewStyle())
                        .scaleEffect(0.8)

                    if let message = message {
                        Text(message)
                            .font(.caption1)
                    }
                }
            }
        } else {
            EmptyView()
        }
    }
}

// MARK: - Preview

#if DEBUG
struct AppLoadingView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppLoadingView(message: "正在加载...")

            AppLoadingView(message: "正在加载数据", style: .indicator)

            AppLoadingView(message: "请稍候...", style: .text)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
