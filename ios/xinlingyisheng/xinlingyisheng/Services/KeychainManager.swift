import Foundation
import Security

/// Keychain 管理器 - 安全存储敏感信息（如 Token）
/// 使用 Keychain 而非 UserDefaults 存储 Token，防止越狱设备读取
/// Keychain 失败时自动降级到 UserDefaults（带警告）
actor KeychainManager {
    static let shared = KeychainManager()

    private init() {
        // 配置 UserDefaults 前缀，避免冲突
        UserDefaults.standard.register(defaults: ["keychain_fallback_enabled": true])
    }

    // MARK: - 错误类型
    enum KeychainError: Error, LocalizedError {
        case itemNotFound
        case duplicateItem
        case unexpectedStatus(OSStatus)

        var errorDescription: String? {
            switch self {
            case .itemNotFound:
                return "未找到 Keychain 项"
            case .duplicateItem:
                return "Keychain 项已存在"
            case .unexpectedStatus(let status):
                return "Keychain 操作失败，状态码: \(status)"
            }
        }
    }

    // MARK: - UserDefaults 降级存储

    /// UserDefaults 前缀
    private var userDefaultsPrefix: String {
        return "secure_fallback_"
    }

    /// 保存到 UserDefaults（降级方案）
    private func saveToUserDefaults(_ value: String, forKey key: String) {
        let fullKey = userDefaultsPrefix + key
        UserDefaults.standard.set(value, forKey: fullKey)
        AppLogger.warning("[Keychain] 降级到 UserDefaults 存储: \(key)")
    }

    /// 从 UserDefaults 读取（降级方案）
    private func retrieveFromUserDefaults(forKey key: String) -> String? {
        let fullKey = userDefaultsPrefix + key
        return UserDefaults.standard.string(forKey: fullKey)
    }

    /// 从 UserDefaults 删除（降级方案）
    private func deleteFromUserDefaults(forKey key: String) {
        let fullKey = userDefaultsPrefix + key
        UserDefaults.standard.removeObject(forKey: fullKey)
    }

    // MARK: - 通用方法

    /// 保存字符串到 Keychain（失败时自动降级到 UserDefaults）
    func save(_ value: String, forKey key: String) throws {
        // 先尝试 Keychain
        do {
            // 先删除已存在的项（避免重复）
            try? deleteFromKeychain(forKey: key)

            // 从字符串创建数据
            guard let data = value.data(using: .utf8) else {
                throw KeychainError.unexpectedStatus(-1)
            }

            // 构建 Keychain 查询
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrAccount as String: key,
                kSecValueData as String: data,
                kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
            ]

            // 添加到 Keychain
            let status = SecItemAdd(query as CFDictionary, nil)
            guard status == errSecSuccess else {
                throw KeychainError.unexpectedStatus(status)
            }

            AppLogger.success("[Keychain] 保存成功: \(key)")

        } catch {
            // Keychain 失败，降级到 UserDefaults
            AppLogger.error("[Keychain] 保存失败，降级到 UserDefaults: \(key)", error: error)
            saveToUserDefaults(value, forKey: key)
        }
    }

    /// 从 Keychain 读取字符串（失败时自动降级到 UserDefaults）
    func retrieve(forKey key: String) throws -> String {
        // 先尝试 Keychain
        do {
            let value = try retrieveFromKeychain(forKey: key)
            return value
        } catch {
            // Keychain 失败，尝试 UserDefaults
            if let fallbackValue = retrieveFromUserDefaults(forKey: key) {
                AppLogger.warning("[Keychain] 从 UserDefaults 读取（降级模式）: \(key)")
                return fallbackValue
            }
            throw error
        }
    }

    /// 从 Keychain 读取（内部方法）
    private func retrieveFromKeychain(forKey key: String) throws -> String {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess else {
            if status == errSecItemNotFound {
                throw KeychainError.itemNotFound
            }
            throw KeychainError.unexpectedStatus(status)
        }

        guard let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            throw KeychainError.unexpectedStatus(errSecDecode)
        }

        return value
    }

    /// 从 Keychain 删除项（同时清除 UserDefaults 降级数据）
    func delete(forKey key: String) throws {
        // 删除 Keychain 项
        do {
            try deleteFromKeychain(forKey: key)
        } catch {
            AppLogger.warning("[Keychain] 删除 Keychain 失败: \(key)")
        }

        // 同时清除 UserDefaults 降级数据
        deleteFromUserDefaults(forKey: key)
    }

    /// 从 Keychain 删除（内部方法）
    private func deleteFromKeychain(forKey key: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]

        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.unexpectedStatus(status)
        }
    }

    /// 检查 Keychain 中是否存在某项
    func exists(forKey key: String) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]

        let status = SecItemCopyMatching(query as CFDictionary, nil)
        return status == errSecSuccess
    }

    // MARK: - Token 专用方法

    /// 保存访问令牌
    func saveAccessToken(_ token: String) throws {
        try save(token, forKey: "auth_token")
    }

    /// 获取访问令牌
    func getAccessToken() throws -> String {
        return try retrieve(forKey: "auth_token")
    }

    /// 保存刷新令牌
    func saveRefreshToken(_ token: String) throws {
        try save(token, forKey: "refresh_token")
    }

    /// 获取刷新令牌
    func getRefreshToken() throws -> String {
        return try retrieve(forKey: "refresh_token")
    }

    /// 删除所有认证相关令牌
    func clearAllTokens() throws {
        try? delete(forKey: "auth_token")
        try? delete(forKey: "refresh_token")
    }
}

// MARK: - 便利的异步方法

extension KeychainManager {
    /// 保存字符串到 Keychain（异步）
    func saveAsync(_ value: String, forKey key: String) async throws {
        try save(value, forKey: key)
    }

    /// 从 Keychain 读取字符串（异步）
    func retrieveAsync(forKey key: String) async throws -> String {
        return try retrieve(forKey: key)
    }

    /// 从 Keychain 删除项（异步）
    func deleteAsync(forKey key: String) async throws {
        try delete(forKey: key)
    }
}
