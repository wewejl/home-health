import Foundation

/// 安全的 URLSession 配置
/// 自动处理证书验证和认证 Header
extension URLSession {

    /// 安全的 URLSession 单例
    static let secure: URLSession = {
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300

        // 开发环境：使用自定义 delegate 处理自签名证书
        #if DEBUG
        return URLSession(
            configuration: config,
            delegate: CertDelegate(),
            delegateQueue: OperationQueue()
        )
        #else
        return URLSession(configuration: config)
        #endif
    }()
}

/// URLSession Delegate 用于证书验证
private class CertDelegate: NSObject, URLSessionDelegate {

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge
    ) async -> (URLSession.AuthChallengeDisposition, URLCredential?) {

        // 交给 CertValidator 处理
        var disposition: URLSession.AuthChallengeDisposition = .performDefaultHandling
        var credential: URLCredential? = nil

        CertValidator.shared.validate(challenge: challenge) { resultDisposition, resultCredential in
            disposition = resultDisposition
            credential = resultCredential
        }

        return (disposition, credential)
    }
}
