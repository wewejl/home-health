//
//  AppConfig.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一应用配置管理

import Foundation

/// 应用配置管理
///
/// 集中管理应用级别的配置常量，支持不同环境
///
enum AppConfig {

    // MARK: - API Configuration

    /// API 基础地址
    static let apiBaseURL = "http://localhost:8100"

    /// API 超时时间（秒）
    static let apiTimeout: TimeInterval = 30

    /// API 重试次数
    static let apiMaxRetries = 3

    // MARK: - Application Settings

    /// 应用名称
    static let appName = "灵犀健康"

    /// 应用版本
    static let appVersion = "1.0.0"

    /// Bundle 标识符
    static let appBundleIdentifier = "com.example.xinlingyisheng"

    // MARK: - Feature Flags

    /// 是否启用调试模式
    static let isDebug: Bool = {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }()

    /// 是否启用测试模式
    static let isTestMode: Bool = false

    /// 是否启用日志
    static let isLoggingEnabled: Bool = true

    // MARK: - Storage Keys

    /// Token 存储键
    static let keyAccessToken = "app_access_token"

    /// Refresh Token 存储键
    static let keyRefreshToken = "app_refresh_token"

    /// 用户 ID 存储键
    static let keyUserId = "app_user_id"

    /// 上次登录手机号
    static let keyLastPhone = "app_last_phone"
}

// MARK: - Preview Provider

#if DEBUG
struct AppConfig_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("API Base URL").render(AppConfig.apiBaseURL)
            Text("Is Debug").render(AppConfig.isDebug.description)
            Text("Is Test Mode").render(AppConfig.isTestMode.description)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
