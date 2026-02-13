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

    var cardType: CardType = .standard
    var cornerRadius: CGFloat = AppSpacing.cardCornerRadius
    var shadowRadius: CGFloat = 8
    var padding: CGFloat = AppSpacing.standard

    // MARK: - Body

    var body: some View {
        content
    }

    // MARK: - Rendering

    var body: some View {
        Group {
            switch cardType {
            case .standard:
                content
                    .background(AppColors.cardBackground)
                    .cornerRadius(cornerRadius)
                    .shadow(color: AppColors.shadow, radius: shadowRadius)
            case .elevated:
                content
                    .background(AppColors.cardBackground)
                    .cornerRadius(cornerRadius)
                    .shadow(color: AppColors.shadow, radius: shadowRadius * 1.5)
            case .outlined:
                content
                    .background(AppColors.cardBackground)
                    .cornerRadius(cornerRadius)
                    .overlay(
                        RoundedRectangle(cornerRadius: cornerRadius)
                            .strokeBorder(AppColors.border, lineWidth: 1)
                    )
            case .filled:
                content
                    .background(AppColors.primary)
                    .cornerRadius(cornerRadius)
                    .foregroundColor(.white)
            }
        }
        .padding(padding)
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

            AppCard {
                Text("填允卡片")
                    .cardType(.filled)
            }

            AppCard {
                Text("描边卡片")
                    .cardType(.outlined)
            }
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
