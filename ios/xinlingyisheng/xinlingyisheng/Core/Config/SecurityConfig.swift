//
//  SecurityConfig.swift
//

import Foundation

enum SecurityConfig {
    private static let defaultAPIBaseURL = "http://localhost:8100"
    private static let env = ProcessInfo.processInfo.environment

    // 优先级: 环境变量 -> Info.plist -> 默认值
    static var apiBaseURL: String {
        if let value = resolvedValue(
            envKey: "API_BASE_URL",
            infoKey: "API_BASE_URL"
        ) {
            return value
        }
        return defaultAPIBaseURL
    }

    // 优先级: 环境变量/Info.plist 显式配置 -> 从 API_BASE_URL 自动推导
    static var websocketBaseURL: String {
        if let value = resolvedValue(
            envKey: "WS_BASE_URL",
            infoKey: "WS_BASE_URL"
        ) {
            return value
        }

        let apiURL = URL(string: apiBaseURL)
        let scheme = (apiURL?.scheme == "https") ? "wss" : "ws"
        let host = apiURL?.host ?? "localhost"
        let portPart = apiURL?.port.map { ":\($0)" } ?? ""
        return "\(scheme)://\(host)\(portPart)/ws"
    }

    // MARK: - Aliyun Dypns Config (号码认证服务)

    /// 阿里云号码认证 AppKey
    /// 方案Code: FC220000012370277 (灵犀健康)
    static var aliyunDypnsAppKey: String {
        return resolvedValue(
            envKey: "ALIYUN_DYPNS_APP_KEY",
            infoKey: "ALIYUN_DYPNS_APP_KEY"
        ) ?? "FC220000012370277"  // 默认使用灵犀健康的方案Code
    }

    /// 阿里云号码认证 AppSecret (仅服务端使用)
    static var aliyunDypnsAppSecret: String {
        return resolvedValue(
            envKey: "ALIYUN_DYPNS_APP_SECRET",
            infoKey: "ALIYUN_DYPNS_APP_SECRET"
        ) ?? ""
    }

    private static func resolvedValue(envKey: String, infoKey: String) -> String? {
        if let envValue = env[envKey]?.trimmingCharacters(in: .whitespacesAndNewlines),
           !envValue.isEmpty {
            return envValue
        }
        if let infoValue = Bundle.main.object(forInfoDictionaryKey: infoKey) as? String {
            let value = infoValue.trimmingCharacters(in: .whitespacesAndNewlines)
            if !value.isEmpty {
                return value
            }
        }
        return nil
    }

    static func log(_ message: String) {
        #if DEBUG
        print("[SecurityConfig] \(message)")
        #endif
    }
}
