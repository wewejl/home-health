//
//  AppFonts.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一字体系统
//

import SwiftUI

/// 应用字体系统
///
/// 统一管理字体大小和样式，支持动态字体大小调整
///
enum AppFonts {

    // MARK: - Font Sizes (相对单位，支持缩放)

    /// 大号 - 20pt
    static let large: CGFloat = 20

    /// 标题 1 - 18pt
    static let title1: CGFloat = 18

    /// 标题 2 - 16pt
    static let title2: CGFloat = 16

    /// 标题 3 - 14pt
    static let title3: CGFloat = 14

    /// 正文 - 14pt
    static let body: CGFloat = 14

    /// 号召 - 13pt
    static let callout: CGFloat = 13

    /// 小标题 - 12pt
    static let caption1: CGFloat = 12

    /// 小标题 2 - 9pt
    static let caption2: CGFloat = 9

    // MARK: - Font Weights

    /// 粗体
    static let bold: Font.Weight = .bold

    /// 半粗体
    static let semibold: Font.Weight = .semibold

    /// 中等
    static let medium: Font.Weight = .medium

    /// 常规
    static let regular: Font.Weight = .regular

    // MARK: - Font Families

    /// 系统字体 - 苹方/思源黑
    static let system = "SF Pro Text"

    /// 等宽字体 - 苹方等宽
    static let mono = "SF Mono"

    // MARK: - Combined Font API

    /// 获取指定大小和权重的字体
    static func font(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        Font.system(size: size, weight: weight)
    }

    /// 获取系统字体的指定大小
    static func systemFont(_ size: CGFloat) -> Font {
        Font.system(size: size, weight: .regular)
    }

    /// 获取等宽字体的指定大小
    static func monoFont(_ size: CGFloat) -> Font {
        Font.system(size: size, weight: .regular)
            .monospaced()
            .monospacedDigit()
    }
}

// MARK: - Preview Provider

#if DEBUG
struct AppFonts_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Large").font(AppFonts.font(.large, weight: .bold))
            Text("Title 1").font(AppFonts.font(.title1))
            Text("Title 2").font(AppFonts.font(.title2))
            Text("Title 3").font(AppFonts.font(.title3))
            Text("Body").font(AppFonts.font(.body))
            Text("Callout").font(AppFonts.font(.callout))
            Text("Caption 1").font(AppFonts.font(.caption1))
            Text("Caption 2").font(AppFonts.font(.caption2))
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
