//
//  AppError.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一错误类型定义

import Foundation

/// 应用错误类型
///
/// 统一管理所有应用错误类型，支持用户友好的错误提示
///
enum AppError: LocalizedError {

    // MARK: - Network Errors

    /// 网络请求失败
    case networkRequestFailed(String)

    /// 网络超时
    case networkTimeout

    /// 无网络连接
    case noNetworkConnection

    /// 服务器错误
    case serverError(statusCode: Int, message: String?)

    // MARK: - Authentication Errors

    /// 未登录
    case notAuthenticated

    /// Token 过期
    case tokenExpire

    /// 登录失败
    case loginFailed(String)

    /// 验证码发送失败
    case verificationCodeFailed(String)

    // MARK: - Data Errors

    /// 数据解析失败
    case dataParsingFailed

    /// 数据为空
    case emptyData

    /// 无数据
    case noDataFound

    // MARK: - User Input Errors

    /// 输入无效
    case invalidInput(String)

    /// 手机号格式错误
    case invalidPhoneFormat

    /// 验证码格式错误
    case invalidVerificationCode

    // MARK: - Storage Errors

    /// 存储失败
    case storageFailed(String)

    /// 读取失败
    case readFailed(String)

    // MARK: - General Errors

    /// 未知错误
    case unknown(String)

    /// 操作失败
    case operationFailed(String)

    // MARK: - Localized Error Protocol

    var errorDescription: String? {
        switch self {
        case .networkRequestFailed(let message):
            return "网络请求失败: \(message)"
        case .networkTimeout:
            return "网络连接超时，请检查网络设置"
        case .noNetworkConnection:
            return "无网络连接，请检查网络设置"
        case .serverError(let code, let message):
            return "服务器错误(\(code)): \(message ?? "未知错误")"
        case .notAuthenticated:
            return "请先登录"
        case .tokenExpire:
            return "登录已过期，请重新登录"
        case .loginFailed(let message):
            return "登录失败: \(message)"
        case .verificationCodeFailed(let message):
            return "发送验证码失败: \(message)"
        case .dataParsingFailed:
            return "数据解析失败"
        case .emptyData:
            return "暂无数据"
        case .noDataFound:
            return "未找到相关数据"
        case .invalidInput(let message):
            return "输入无效: \(message)"
        case .invalidPhoneFormat:
            return "手机号格式不正确"
        case .invalidVerificationCode:
            return "验证码格式不正确"
        case .storageFailed(let message):
            return "存储失败: \(message)"
        case .readFailed(let message):
            return "读取失败: \(message)"
        case .unknown(let message):
            return "未知错误: \(message)"
        case .operationFailed(let message):
            return "操作失败: \(message)"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .noNetworkConnection, .networkTimeout, .networkRequestFailed:
            return "请检查网络连接后重试"
        case .notAuthenticated, .tokenExpire:
            return "请重新登录"
        case .serverError:
            return "请稍后重试或联系客服"
        case .invalidInput, .invalidPhoneFormat, .invalidVerificationCode:
            return "请检查输入后重试"
        default:
            return nil
        }
    }

    /// 用户友好的错误消息
    var userFriendlyMessage: String {
        return errorDescription ?? "操作失败，请重试"
    }
}

// MARK: - Preview Provider

#if DEBUG
struct AppError_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Network Request Failed")
                .foregroundColor(AppColors.error)
            Text("Network Timeout")
                .foregroundColor(AppColors.warning)
            Text("No Network Connection")
                .foregroundColor(AppColors.textPrimary)
            Text("Not Authenticated")
                .foregroundColor(AppColors.error)
            Text("Token Expired")
                .foregroundColor(AppColors.warning)
            Text("Login Failed")
                .foregroundColor(AppColors.error)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
