//
//  AppCard.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一卡片组件

import SwiftUI

/// 统一卡片组件
///
/// 提供标准卡片样式，支持多种类型和布局
///
struct AppCard<Content: View>: View {

    // MARK: - Types

    enum CardType {
        case standard
        case elevated
        case outlined
        case filled
    }

    // MARK: - Properties

    let cardType: CardType
    let cornerRadius: CGFloat
    let shadowRadius: CGFloat
    let padding: CGFloat
    let content: Content

    // MARK: - Body

    var body: some View {
        content
            .background(AppColors.cardBackground)
            .cornerRadius(cornerRadius)
            .shadow(color: AppColors.shadow, radius: shadowRadius)
            .padding(padding)
    }

    // MARK: - Initializer

    init(
        cardType: CardType = .standard,
        cornerRadius: CGFloat = AppSpacing.cardCornerRadius,
        shadowRadius: CGFloat = 8,
        padding: CGFloat = AppSpacing.standard,
        @ViewBuilder content: () -> Content
    ) {
        self.cardType = cardType
        self.cornerRadius = cornerRadius
        self.shadowRadius = shadowRadius
        self.padding = padding
        self.content = content()
    }
}

// MARK: - Convenience Initializers

extension AppCard {

    /// 标准卡片
    init(@ViewBuilder content: () -> Content) {
        self.init(cardType: .standard, content: content)
    }

    /// 填充卡片
    init(filled: Bool = false, @ViewBuilder content: () -> Content) {
        self.init(cardType: filled ? .filled : .standard, content: content)
    }

    /// 描边卡片
    init(outlined: Bool = true, @ViewBuilder content: () -> Content) {
        self.init(cardType: .outlined, content: content)
    }
}

// MARK: - Preview

#if DEBUG
struct AppCard_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppCard {
                Text("卡片内容")
            }

            AppCard(filled: true) {
                Text("填充卡片")
                    .foregroundColor(.white)
            }

            AppCard(outlined: true) {
                Text("描边卡片")
            }
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
