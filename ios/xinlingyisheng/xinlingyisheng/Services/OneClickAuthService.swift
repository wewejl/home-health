//
//  OneClickAuthService.swift
//  鑫琳医生 - 阿里云一键登录服务
//
//  集成阿里云号码认证服务，实现无感知一键登录
//

import Foundation
import UIKit
import Combine

// MARK: - 错误类型
enum OneClickAuthError: LocalizedError {
    case networkNotAvailable
    case sdkNotInitialized
    case tokenTimeout
    case tokenGetFailed(String)
    case verifyFailed(String)
    case cancelled

    var errorDescription: String? {
        switch self {
        case .networkNotAvailable:
            return "请使用移动数据网络进行一键登录"
        case .sdkNotInitialized:
            return "SDK初始化失败"
        case .tokenTimeout:
            return "获取Token超时"
        case .tokenGetFailed(let msg):
            return "获取Token失败: \(msg)"
        case .verifyFailed(let msg):
            return "验证失败: \(msg)"
        case .cancelled:
            return "用户取消登录"
        }
    }
}

// MARK: - 登录结果
struct OneClickAuthResult {
    let token: String
    let refreshToken: String
    let user: UserModel
    let isNewUser: Bool
}

// MARK: - 阿里云号码认证SDK桥接
/// 由于阿里云SDK是Objective-C编写，我们需要创建桥接
/// 在实际使用前，需要在Bridging-Header中引入ATAuthSDK.h
@objc class AliyunDypnsBridge: NSObject {

    static let shared = AliyunDypnsBridge()

    @objc var appKey: String = ""

    private override init() {
        super.init()
    }

    @objc func configure(withAppKey key: String) {
        self.appKey = key
        // 实际SDK初始化会在运行时完成
        print("[OneClick] SDK配置完成，AppKey: \(key.prefix(6))...")
    }

    @objc func getCurrentToken() async throws -> String {
        // 检查网络环境（仅移动网络支持）
        guard isCellularNetwork() else {
            throw OneClickAuthError.networkNotAvailable
        }

        // 模拟获取Token（实际调用SDK）
        // 在真实环境中，这里会调用 ATAuthSDK 的 getToken 方法
        try await Task.sleep(nanoseconds: UInt64(1.5 * 1_000_000_000))

        // 返回模拟Token（实际应从SDK获取）
        return "mock_token_\(Date().timeIntervalSince1970)"
    }

    @objc func checkNetwork() -> Bool {
        return isCellularNetwork()
    }

    private func isCellularNetwork() -> Bool {
        // 检查是否使用移动数据网络
        let networkState = getNetworkState()
        return networkState == 4 // 4 = WWAN (移动数据)
    }

    private func getNetworkState() -> Int {
        // 0 = 无网络, 1 = WiFi, 2 = 2G, 3 = 3G, 4 = 4G, 5 = 5G
        // 简化实现，实际应使用 Reachability 或 NWPathMonitor
        var zeroAddress = sockaddr_in()
        zeroAddress.sin_len = UInt8(MemoryLayout.size(ofValue: zeroAddress))
        zeroAddress.sin_family = sa_family_t(AF_INET)

        guard let reachability = withUnsafePointer(to: &zeroAddress, {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                SCNetworkReachabilityCreateWithAddress(kCFAllocatorDefault, $0)
            }
        }) else {
            return 0
        }

        var flags: SCNetworkReachabilityFlags = []
        if !SCNetworkReachabilityGetFlags(reachability, &flags) {
            return 0
        }

        let isReachable = flags.contains(.reachable)
        let needsConnection = flags.contains(.connectionRequired)
        let isWWAN = flags.contains(.isWWAN)

        if !isReachable || needsConnection {
            return 0
        }

        return isWWAN ? 4 : 1
    }
}

// MARK: - 一键登录服务
@MainActor
class OneClickAuthService: ObservableObject {

    static let shared = OneClickAuthService()

    @Published var isLoading: Bool = false
    @Published var errorMessage: String?

    private let bridge = AliyunDypnsBridge.shared

    // AppKey 从配置文件读取
    private var appKey: String {
        return APIConfig.aliyunDypnsAppKey
    }

    private init() {
        configureSDK()
    }

    // MARK: - SDK 配置
    private func configureSDK() {
        guard !appKey.isEmpty || !appKey.contains("YOUR_") else {
            print("[OneClick] AppKey 未配置，将使用测试模式")
            return
        }

        bridge.configure(withAppKey: appKey)
        print("[OneClick] SDK 初始化完成")
    }

    // MARK: - 检查是否可用
    func isAvailable() -> Bool {
        // 必须是移动网络
        guard bridge.checkNetwork() else {
            print("[OneClick] 非移动网络，不可用")
            return false
        }
        return true
    }

    // MARK: - 一键登录
    func oneClickLogin() async throws -> OneClickAuthResult {
        isLoading = true
        errorMessage = nil

        defer {
            isLoading = false
        }

        // 1. 检查网络环境
        guard isAvailable() else {
            throw OneClickAuthError.networkNotAvailable
        }

        // 2. 获取Token
        let accessToken: String
        do {
            accessToken = try await bridge.getCurrentToken()
            print("[OneClick] 获取Token成功")
        } catch {
            print("[OneClick] 获取Token失败: \(error)")
            throw error
        }

        // 3. 发送到后端验证
        do {
            let response = try await APIService.shared.verifyOneClickLogin(token: accessToken)

            // 4. 返回结果
            return OneClickAuthResult(
                token: response.token,
                refreshToken: response.refresh_token ?? "",
                user: response.user,
                isNewUser: response.is_new_user ?? false
            )
        } catch let error as APIError {
            print("[OneClick] 后端验证失败: \(error)")
            throw OneClickAuthError.verifyFailed(error.localizedDescription)
        }
    }

    // MARK: - 取消登录
    func cancel() {
        isLoading = false
        errorMessage = nil
    }
}

// MARK: - SystemConfiguration 桥接
import SystemConfiguration
