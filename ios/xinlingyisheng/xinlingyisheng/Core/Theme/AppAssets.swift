//
//  AppAssets.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一图片资源管理

import SwiftUI

/// 应用图片资源管理
///
/// 集中管理所有图片名称和加载逻辑
/// 支持动态图片加载和缓存
///
enum AppAssets {

    // MARK: - Logo

    /// 应用 Logo - 主图标
    static let logo = Image("logo")

    /// 应用 Logo 小尺寸
    static let logoSmall = Image("logo_small")

    // MARK: - Icons

    /// 成功图标
    static let iconSuccess = Image(systemName: "checkmark.circle.fill")

    /// 警告图标
    static let iconWarning = Image(systemName: "exclamationmark.triangle.fill")

    /// 错误图标
    static let iconError = Image(systemName: "xmark.circle.fill")

    /// 信息图标
    static let iconInfo = Image(systemName: "info.circle.fill")

    /// 医生图标
    static let iconDoctor = Image(systemName: "stethoscope.circle.fill")

    /// 药品图标
    static let iconPill = Image(systemName: "pill.fill")

    /// 问诊图标
    static let iconChat = Image(systemName: "message.circle.fill")

    /// 时间图标
    static let iconTime = Image(systemName: "clock.fill")

    /// 日历图标
    static let iconCalendar = Image(systemName: "calendar")

    // MARK: - Illustrations

    /// 问诊插图
    static let illustrationChat = Image("illustration_chat")

    /// 医生插图
    static let illustrationDoctor = Image("illustration_doctor")

    /// 空状态插图
    static let illustrationEmpty = Image("illustration_empty")

    // MARK: - Placeholder Images

    /// 头像占位符
    static let avatarPlaceholder = Image("avatar_placeholder")

    /// 医疗记录占位符
    static let recordPlaceholder = Image("record_placeholder")
}

// MARK: - Preview Provider

#if DEBUG
struct AppAssets_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Image("Logo").render(AppAssets.logo)
            Image("Logo Small").render(AppAssets.logoSmall)
            Image("Icon Success").render(AppAssets.iconSuccess)
            Image("Icon Warning").render(AppAssets.iconWarning)
            Image("Icon Error").render(AppAssets.iconError)
            Image("Icon Info").render(AppAssets.iconInfo)
            Image("Icon Doctor").render(AppAssets.iconDoctor)
            Image("Icon Pill").render(AppAssets.iconPill)
            Image("Icon Chat").render(AppAssets.iconChat)
            Image("Icon Time").render(AppAssets.iconTime)
            Image("Icon Calendar").render(AppAssets.iconCalendar)
        }
        .previewLayout(.sizeThatFits)
    }
}
#endif
