//
//  AppSpacing.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一间距系统

import SwiftUI

/// 应用间距系统
///
/// 统一管理内边距、外边距、组件间距
///
/// 设计理念：使用 4pt 基准单位，所有间距为 4 的倍数
///
enum AppSpacing {

    // MARK: - Base Spacing Unit (支持屏幕缩放)

    /// 基础间距单位 - 4pt
    static let base: CGFloat = 4

    // MARK: - Micro Spacing (2pt)

    /// 超小间距 - 2pt (0.5x base)
    static let micro: CGFloat = base * 0.5

    /// 小间距 - 4pt
    static let tiny: CGFloat = base

    // MARK: - Small Spacing (4-8px)

    /// 小标题间距 - 6pt (1.5x base)
    static let small: CGFloat = base * 1.5

    /// 紧凑间距 - 8pt (2x base)
    static let compact: CGFloat = base * 2

    // MARK: - Medium Spacing (12-16px)

    /// 中等间距 - 12pt (3x base)
    static let medium: CGFloat = base * 3

    /// 标准间距 - 16pt (4x base)
    static let standard: CGFloat = base * 4

    // MARK: - Large Spacing (20-32px)

    /// 大间距 - 24pt (6x base)
    static let large: CGFloat = base * 6

    /// 超大间距 - 32pt (8x base)
    static let xLarge: CGFloat = base * 8

    // MARK: - Specific Spacing

    /// 按钮水平内边距 - 12pt
    static let buttonHorizontal: CGFloat = standard

    /// 按钮垂直内边距 - 6pt
    static let buttonVertical: CGFloat = compact

    /// 卡片内边距 - 16pt
    static let cardPadding: CGFloat = standard

    /// 区块间距 - 24pt
    static let sectionSpacing: CGFloat = large

    // MARK: - Corner Radius

    /// 卡片圆角 - 12pt
    static let cardCornerRadius: CGFloat = 12

    /// 按钮圆角 - 8pt
    static let buttonCornerRadius: CGFloat = 8

    /// 小圆角 - 4pt
    static let smallCornerRadius: CGFloat = 4
}

// MARK: - Preview Provider

#if DEBUG
struct AppSpacing_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Micro").padding(AppSpacing.micro)
            Text("Tiny").padding(AppSpacing.tiny)
            Text("Small").padding(AppSpacing.small)
            Text("Compact").padding(AppSpacing.compact)
            Text("Medium").padding(AppSpacing.medium)
            Text("Standard").padding(AppSpacing.standard)
            Text("Large").padding(AppSpacing.large)
            Text("XLarge").padding(AppSpacing.xLarge)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
