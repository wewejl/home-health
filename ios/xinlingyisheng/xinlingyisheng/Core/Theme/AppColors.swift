//
//  AppColors.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一的应用颜色系统
//  设计理念: 温暖、自然、治愈，营造舒适的问诊环境
//
//  说明: 此文件整合并替换了 HealingColorTheme 和 PremiumColorTheme 的颜色定义
//

import SwiftUI

/// 应用颜色系统
///
/// 统一管理所有应用颜色，使用语义化命名便于后续维护和主题切换
///
enum AppColors {

    // MARK: - Primary Colors

    /// 主品牌色 - 鼠尾草绿（灵犀健康主色）
    static let primary = Color(red: 0xB5 / 255, green: 0xD1 / 255, blue: 0xC2 / 255)

    /// 主品牌色浅变
    static let primaryLight = Color(red: 0xB7 / 255, green: 0xE9 / 255, blue: 0xB9 / 255)

    /// 主品牌色深变
    static let primaryDark = Color(red: 0xA3 / 255, green: 0x9F / 255, blue: 0xA8 / 255)

    // MARK: - Semantic Colors

    /// 成功绿 - 用于成功状态、确认按钮
    static let success = Color(red: 0x4D / 255, green: 0xB8 / 255, blue: 0x85 / 255)

    /// 警告橙 - 用于警告提示
    static let warning = Color(red: 0xF5 / 255, green: 0xA6 / 255, blue: 0x23 / 255)

    /// 错误红 - 用于错误提示、删除按钮
    static let error = Color(red: 0xD9 / 255, green: 0x59 / 255, blue: 0x59 / 255)

    /// 信息蓝 - 用于信息提示、次要文字
    static let info = Color(red: 0x51 / 255, green: 0xA6 / 255, blue: 0x6B / 255)

    // MARK: - Background Colors

    /// 页面背景 - 暖米色
    static let background = Color(red: 0xF7 / 255, green: 0xF2 / 255, blue: 0xE8 / 255)

    /// 卡片背景 - 白色
    static let cardBackground = Color.white

    // MARK: - Text Colors

    /// 主要文字 - 深灰
    static let textPrimary = Color(red: 0x38 / 255, green: 0x38 / 255, blue: 0x33 / 255)

    /// 次要文字 - 中灰
    static let textSecondary = Color(red: 0x6B / 255, green: 0x66 / 255, blue: 0x40 / 255)

    /// 辅助文字 - 浅灰
    static let textTertiary = Color(red: 0x9E / 255, green: 0x9E / 255, blue: 0x99 / 255)

    /// 占位符文字 - 中性灰
    static let textMuted = Color(red: 0x70 / 255, green: 0x70 / 255, blue: 0x70 / 255)

    // MARK: - Border Colors

    /// 边框浅色
    static let borderLight = Color(red: 0xE0 / 255, green: 0xE0 / 255, blue: 0xE0 / 255)

    /// 边框深色
    static let borderDark = Color.black.opacity(0.1)

    // MARK: - Overlay Colors

    /// 遮罩层
    static let overlay = Color.black.opacity(0.4)

    /// 模态背景
    static let modalBackground = Color.white

    // MARK: - Special Colors

    /// 品牌紫 - 用于突出显示
    static let accent = Color(red: 0x51 / 255, green: 0x7A / 255, blue: 0x85 / 255)

    /// 链接色
    static let link = Color(red: 0x51 / 255, green: 0x7A / 255, blue: 0xB6 / 255)

    /// 分割线
    static let divider = Color(red: 0xF0 / 255, green: 0xF0 / 255, blue: 0xF0 / 255)
}

// MARK: - Preview Provider

#if DEBUG
struct AppColors_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Primary").foregroundColor(AppColors.primary)
            Text("Success").foregroundColor(AppColors.success)
            Text("Warning").foregroundColor(AppColors.warning)
            Text("Error").foregroundColor(AppColors.error)
            Text("Info").foregroundColor(AppColors.info)
            Text("Background").foregroundColor(AppColors.background)
            Text("Card Background").foregroundColor(AppColors.cardBackground)
            Text("Text Primary").foregroundColor(AppColors.textPrimary)
            Text("Accent").foregroundColor(AppColors.accent)
            Text("Link").foregroundColor(AppColors.link)
        }
        }
        .padding()
        .previewLayout(.sizeThatFits)
}
#endif
