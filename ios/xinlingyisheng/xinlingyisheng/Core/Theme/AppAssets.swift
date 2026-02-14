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
}

// MARK: - Preview Provider

#if DEBUG
struct AppAssets_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Image(systemName: "heart.fill")
            Image(systemName: "person.fill")
            Image(systemName: "calendar")
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
