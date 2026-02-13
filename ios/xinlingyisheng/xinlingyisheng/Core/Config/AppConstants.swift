//
//  AppConstants.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一常量定义

import Foundation

/// 应用常量定义
///
/// 统一管理所有应用级别的常量，便于维护和修改
///
enum AppConstants {

    // MARK: - Numbers

    /// 零 - 表示无
    static let zero: CGFloat = 0

    /// 一
    static let one: CGFloat = 1

    // MARK: - Durations

    /// 动画短持续时间 - 0.2 秒
    static let animationDurationShort: TimeInterval = 0.2

    /// 动画中持续时间 - 0.3 秒
    static let animationDurationMedium: TimeInterval = 0.3

    /// 动画长持续时间 - 0.5 秒
    static let animationDurationLong: TimeInterval = 0.5

    /// 反馈震动时长
    static let feedbackDuration: TimeInterval = 0.05

    // MARK: - Sizes

    /// 按钮最小高度 - 44pt
    static let buttonMinHeight: CGFloat = 44

    /// 按钮标准高度 - 48pt
    static let buttonStandardHeight: CGFloat = 48

    /// 卡片圆角 - 12pt
    static let cardCornerRadius: CGFloat = 12

    /// 输入框圆角 - 8pt
    static let inputCornerRadius: CGFloat = 8

    /// 抽屉圆角 - 16pt
    static let sheetCornerRadius: CGFloat = 16

    // MARK: - Spacing

    /// 列表项间距 - 8pt
    static let listItemSpacing: CGFloat = 8

    /// 区块标题间距 - 16pt
    static let sectionTitleSpacing: CGFloat = 16

    // MARK: - Text

    /// 最大行数 - 防止长文本问题
    static let maxTextLines: Int = 5

    /// 标题最大行数
    static let maxTitleLines: Int = 2

    // MARK: - Network

    /// 网络请求超时时间 - 30 秒
    static let networkTimeout: TimeInterval = 30

    /// 图片上传最大大小 - 50MB
    static let maxImageSize: Int = 50 * 1024 * 1024

    // MARK: - Formatters

    /// 手机号格式化
    static let phoneFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "##########"
        return formatter
    }()

    /// 日期时间格式化
    static let dateTimeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter
    }()

    /// 时间格式化
    static let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter
    }()
}
