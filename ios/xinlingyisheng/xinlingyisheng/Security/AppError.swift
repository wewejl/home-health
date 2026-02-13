import Foundation

/// 应用级错误类型
/// 提供用户友好的错误消息，不泄露技术细节
enum AppError: LocalizedError {
    case networkUnavailable
    case unauthorized
    case serverError(message: String?)
    case timeout
    case parseError
    case invalidConfiguration
    case unknown

    // MARK: - LocalizedError

    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "网络连接不可用"
        case .unauthorized:
            return "登录已过期，请重新登录"
        case .serverError(let message):
            return message ?? "服务器错误，请稍后重试"
        case .timeout:
            return "请求超时"
        case .parseError:
            return "数据解析失败"
        case .invalidConfiguration:
            return "应用配置错误"
        case .unknown:
            return "未知错误"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .networkUnavailable:
            return "请检查网络连接后重试"
        case .unauthorized:
            return "请重新登录以继续使用"
        case .serverError:
            return "请稍后重试"
        case .timeout:
            return "检查网络后重试"
        case .parseError, .invalidConfiguration, .unknown:
            return nil
        }
    }
}

/// API 错误映射
extension APIError {
    /// 转换为 AppError（隐藏技术细节）
    var toAppError: AppError {
        switch self {
        case .networkError:
            return .networkUnavailable
        case .unauthorized:
            return .unauthorized
        case .decodingError:
            return .parseError
        case .serverError(let message):
            return .serverError(message: message)
        case .invalidURL:
            return .invalidConfiguration
        }
    }
}
