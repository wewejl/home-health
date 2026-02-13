import Foundation

/// 安全配置管理
/// 负责从安全来源读取配置，禁止硬编码敏感信息
enum SecurityConfig {

    // MARK: - Environment

    /// 当前环境
    static var environment: String {
        Bundle.main.object(forInfoDictionaryKey: "API_ENVIRONMENT") as? String ?? "unknown"
    }

    /// 是否为开发环境
    static var isDevelopment: Bool {
        #if DEBUG
        return true
        #else
        return environment == "development"
        #endif
    }

    /// 是否为生产环境
    static var isProduction: Bool {
        environment == "production"
    }

    // MARK: - API Configuration

    /// API 基础 URL（强制 HTTPS）
    static var apiBaseURL: String {
        guard let urlString = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String else {
            fatalError("API_BASE_URL not configured in xcconfig")
        }

        // 验证 URL 格式
        guard let url = URL(string: urlString) else {
            fatalError("Invalid API_BASE_URL: \(urlString)")
        }

        // 生产环境强制使用 HTTPS
        if isProduction && url.scheme != "https" {
            fatalError("Production API must use HTTPS")
        }

        return urlString
    }

    /// WebSocket 基础 URL（自动转换为 wss://）
    static var websocketBaseURL: String {
        let apiURL = apiBaseURL
        // 将 http:// 替换为 ws://，https:// 替换为 wss://
        return apiURL
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
    }

    // MARK: - Debug

    #if DEBUG
    /// 开发模式日志（仅开发环境）
    static func log(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        let filename = (file as NSString).lastPathComponent
        print("[SecurityConfig] \(filename):\(line) \(message)")
    }
    #else
    static func log(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        // 生产环境不输出日志
    }
    #endif
}
