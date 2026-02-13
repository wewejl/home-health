//
//  CertValidator.swift
//  灵犀医生
//
//  证书验证器
//  开发环境信任自签名证书，生产环境使用系统验证
//

import Foundation
import Security

// MARK: - 证书验证器
/// 证书验证器
/// 开发环境信任自签名证书，生产环境使用系统验证
class CertValidator: NSObject {

    // MARK: - Singleton

    static let shared = CertValidator()

    // MARK: - Validation

    /// 验证服务器证书
    func validate(
        challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        // 开发环境：信任自签名证书
        if SecurityConfig.isDevelopment {
            if isLocalhost(challenge.protectionSpace) {
                let credential = URLCredential(trust: serverTrust)
                completionHandler(.useCredential, credential)
                SecurityConfig.log("Accepted dev certificate for localhost")
                return
            }
        }

        // 生产环境：使用系统默认验证
        completionHandler(.performDefaultHandling, nil)
    }

    // MARK: - Helpers

    /// 检查是否为本地地址
    private func isLocalhost(_ protectionSpace: URLProtectionSpace) -> Bool {
        guard let host = protectionSpace.host else { return false }
        let localHosts = ["localhost", "127.0.0.1", "::1"]
        return localHosts.contains(host)
    }
}
