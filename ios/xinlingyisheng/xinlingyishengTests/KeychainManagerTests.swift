//
//  KeychainManagerTests.swift
//  xinlingyishengTests
//
//  KeychainManager 单元测试
//  测试覆盖: 保存/读取、删除、更新、Token 专用方法
//

import XCTest
@testable import xinlingyisheng

/// KeychainManager 单元测试
final class KeychainManagerTests: XCTestCase {

    var keychain: KeychainManager!
    let testTimeout: TimeInterval = 3.0

    // 测试用键名前缀，避免与实际数据冲突
    let testKeyPrefix = "test_"

    override func setUp() async throws {
        try await super.setUp()
        keychain = KeychainManager.shared
        // 清理测试数据
        await cleanupTestData()
    }

    override func tearDown() async throws {
        // 清理测试数据
        await cleanupTestData()
        keychain = nil
        try await super.tearDown()
    }

    // MARK: - Helper Methods

    private func cleanupTestData() async {
        // 清理所有测试键
        let testKeys = [
            "\(testKeyPrefix)key",
            "\(testKeyPrefix)save_and_retrieve",
            "\(testKeyPrefix)delete_key",
            "\(testKeyPrefix)update_key",
            "\(testKeyPrefix)exists_key",
            "\(testKeyPrefix)special_chars",
            "\(testKeyPrefix)empty_value",
            "\(testKeyPrefix)long_value",
            "\(testKeyPrefix)unicode_value",
            "auth_token",
            "refresh_token"
        ]

        for key in testKeys {
            try? await keychain.deleteAsync(forKey: key)
        }
    }

    private func generateUniqueKey() -> String {
        return "\(testKeyPrefix)\(UUID().uuidString)"
    }

    // MARK: - Save/Retrieve Tests

    func testSaveAndRetrieve() async throws {
        // Given
        let key = generateUniqueKey()
        let value = "test_value_123"

        // When
        try await keychain.saveAsync(value, forKey: key)
        let retrieved = try await keychain.retrieveAsync(forKey: key)

        // Then
        XCTAssertEqual(retrieved, value, "保存和检索的值应该一致")

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testSaveAndRetrieveDifferentValues() async throws {
        // Given
        let key = generateUniqueKey()
        let testValues = [
            "simple_string",
            "string with spaces",
            "string!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "1234567890",
            "aBcDeFgHiJkLmNoPqRsTuVwXyZ"
        ]

        for value in testValues {
            // When
            try await keychain.saveAsync(value, forKey: key)

            // Then
            let retrieved = try await keychain.retrieveAsync(forKey: key)
            XCTAssertEqual(retrieved, value, "值 '\(value)' 应该被正确保存和检索")
        }

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testRetrieveNonExistentKey() async throws {
        // Given
        let key = "\(testKeyPrefix)non_existent_key_\(UUID().uuidString)"

        // When & Then
        do {
            _ = try await keychain.retrieveAsync(forKey: key)
            XCTFail("应该抛出 KeychainError.itemNotFound 错误")
        } catch KeychainManager.KeychainError.itemNotFound {
            // 预期行为 - 测试通过
        } catch {
            XCTFail("应该抛出 KeychainError.itemNotFound，实际抛出: \(error.localizedDescription)")
        }
    }

    func testDeleteKey() async throws {
        // Given
        let key = generateUniqueKey()
        let value = "value_to_delete"
        try await keychain.saveAsync(value, forKey: key)

        // 验证保存成功
        let retrievedBeforeDelete = try? await keychain.retrieveAsync(forKey: key)
        XCTAssertEqual(retrievedBeforeDelete, value, "删除前应该能检索到值")

        // When
        try await keychain.deleteAsync(forKey: key)

        // Then - 验证已删除
        do {
            _ = try await keychain.retrieveAsync(forKey: key)
            XCTFail("删除后应该抛出错误")
        } catch KeychainManager.KeychainError.itemNotFound {
            // 预期行为 - 测试通过
        } catch {
            XCTFail("应该抛出 KeychainError.itemNotFound，实际抛出: \(error)")
        }

        // 再次删除不应该报错（幂等性）
        try? await keychain.deleteAsync(forKey: key)
    }

    func testUpdateValue() async throws {
        // Given
        let key = generateUniqueKey()
        let originalValue = "original_value"
        let updatedValue = "updated_value"

        // When - 保存原始值
        try await keychain.saveAsync(originalValue, forKey: key)
        var retrieved = try await keychain.retrieveAsync(forKey: key)
        XCTAssertEqual(retrieved, originalValue, "原始值应该正确")

        // When - 更新值
        try await keychain.saveAsync(updatedValue, forKey: key)
        retrieved = try await keychain.retrieveAsync(forKey: key)

        // Then
        XCTAssertEqual(retrieved, updatedValue, "更新后的值应该正确")

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testUpdateMultipleTimes() async throws {
        // Given
        let key = generateUniqueKey()
        let values = ["value1", "value2", "value3", "value4", "value5"]

        // When & Then - 多次更新
        for value in values {
            try await keychain.saveAsync(value, forKey: key)
            let retrieved = try await keychain.retrieveAsync(forKey: key)
            XCTAssertEqual(retrieved, value, "更新后的值应该是最新的")
        }

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testExists() async throws {
        // Given
        let key = generateUniqueKey()

        // When & Then - 不存在时
        var exists = keychain.exists(forKey: key)
        XCTAssertFalse(exists, "键 '\(key)' 不应该存在")

        // When - 保存后
        try await keychain.saveAsync("value", forKey: key)
        exists = keychain.exists(forKey: key)

        // Then
        XCTAssertTrue(exists, "键 '\(key)' 应该存在")

        // When - 删除后
        try await keychain.deleteAsync(forKey: key)
        exists = keychain.exists(forKey: key)

        // Then
        XCTAssertFalse(exists, "删除后键 '\(key)' 不应该存在")
    }

    func testExistsWithNonExistentKey() async throws {
        // Given
        let key = "\(testKeyPrefix)never_existed_\(UUID().uuidString)"

        // When & Then
        let exists = keychain.exists(forKey: key)
        XCTAssertFalse(exists, "不存在的键应该返回 false")
    }

    // MARK: - Edge Cases Tests

    func testEmptyString() async throws {
        // Given
        let key = generateUniqueKey()
        let emptyValue = ""

        // When
        try await keychain.saveAsync(emptyValue, forKey: key)
        let retrieved = try await keychain.retrieveAsync(forKey: key)

        // Then
        XCTAssertEqual(retrieved, emptyValue, "空字符串应该被正确保存")

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testLongString() async throws {
        // Given
        let key = generateUniqueKey()
        // 创建一个较长的字符串（模拟 JWT token）
        let longValue = String(repeating: "a", count: 1000)

        // When
        try await keychain.saveAsync(longValue, forKey: key)
        let retrieved = try await keychain.retrieveAsync(forKey: key)

        // Then
        XCTAssertEqual(retrieved, longValue, "长字符串应该被正确保存")
        XCTAssertEqual(retrieved.count, longValue.count, "长度应该一致")

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testUnicodeCharacters() async throws {
        // Given
        let key = generateUniqueKey()
        let unicodeValues = [
            "Hello World 你好世界",
            "Test 测试 Ñoño",
            "Emoji test 🎉🔑💾",
            "Mixed content with 中文, 日本語, and 한국어"
        ]

        for value in unicodeValues {
            // When
            try await keychain.saveAsync(value, forKey: key)

            // Then
            let retrieved = try await keychain.retrieveAsync(forKey: key)
            XCTAssertEqual(retrieved, value, "Unicode 值 '\(value)' 应该被正确保存")
        }

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testSpecialCharacters() async throws {
        // Given
        let key = generateUniqueKey()
        let specialValue = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"

        // When
        try await keychain.saveAsync(specialValue, forKey: key)
        let retrieved = try await keychain.retrieveAsync(forKey: key)

        // Then
        XCTAssertEqual(retrieved, specialValue, "特殊字符应该被正确保存")

        // 清理
        try? await keychain.deleteAsync(forKey: key)
    }

    func testKeyWithSpecialCharacters() async throws {
        // Given
        let keys = [
            "test.key.with.dots",
            "test-key-with-dashes",
            "test_key_with_underscores",
            "test.key-with-mixed_separators"
        ]

        for key in keys {
            // When
            try await keychain.saveAsync("value_\(key)", forKey: key)

            // Then
            let retrieved = try await keychain.retrieveAsync(forKey: key)
            XCTAssertNotNil(retrieved, "键 '\(key)' 应该能保存和检索")

            // 清理
            try? await keychain.deleteAsync(forKey: key)
        }
    }

    // MARK: - Token Methods Tests

    func testSaveAndGetAccessToken() async throws {
        // Given
        let token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_access_token"

        // When
        try await keychain.saveAccessToken(token)
        let retrieved = try await keychain.getAccessToken()

        // Then
        XCTAssertEqual(retrieved, token, "访问令牌应该被正确保存和检索")

        // 清理
        try? await keychain.deleteAsync(forKey: "auth_token")
    }

    func testSaveAndGetRefreshToken() async throws {
        // Given
        let token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_refresh_token"

        // When
        try await keychain.saveRefreshToken(token)
        let retrieved = try await keychain.getRefreshToken()

        // Then
        XCTAssertEqual(retrieved, token, "刷新令牌应该被正确保存和检索")

        // 清理
        try? await keychain.deleteAsync(forKey: "refresh_token")
    }

    func testClearAllTokens() async throws {
        // Given
        let accessToken = "test_access_token_xyz"
        let refreshToken = "test_refresh_token_abc"

        try await keychain.saveAccessToken(accessToken)
        try await keychain.saveRefreshToken(refreshToken)

        // 验证保存成功
        var accessExists = keychain.exists(forKey: "auth_token")
        var refreshExists = keychain.exists(forKey: "refresh_token")
        XCTAssertTrue(accessExists, "访问令牌应该已保存")
        XCTAssertTrue(refreshExists, "刷新令牌应该已保存")

        // When
        try await keychain.clearAllTokens()

        // Then
        accessExists = keychain.exists(forKey: "auth_token")
        refreshExists = keychain.exists(forKey: "refresh_token")
        XCTAssertFalse(accessExists, "访问令牌应该被清除")
        XCTAssertFalse(refreshExists, "刷新令牌应该被清除")
    }

    func testClearAllTokensPartial() async throws {
        // Given - 只保存访问令牌
        try await keychain.saveAccessToken("access_only")
        let accessExistsBefore = keychain.exists(forKey: "auth_token")
        XCTAssertTrue(accessExistsBefore, "访问令牌应该已保存")

        // When
        try await keychain.clearAllTokens()

        // Then
        let accessExistsAfter = keychain.exists(forKey: "auth_token")
        XCTAssertFalse(accessExistsAfter, "访问令牌应该被清除")
    }

    // MARK: - Multiple Items Tests

    func testMultipleItemsWithDifferentKeys() async throws {
        // Given
        let items = [
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        ]

        // When - 保存多个项目
        for (key, value) in items {
            try await keychain.saveAsync(value, forKey: "\(testKeyPrefix)\(key)")
        }

        // Then - 验证所有项目
        for (key, expectedValue) in items {
            let fullKey = "\(testKeyPrefix)\(key)"
            let retrieved = try await keychain.retrieveAsync(forKey: fullKey)
            XCTAssertEqual(retrieved, expectedValue, "键 '\(fullKey)' 的值应该正确")
        }

        // 清理
        for key in items.keys {
            try? await keychain.deleteAsync(forKey: "\(testKeyPrefix)\(key)")
        }
    }

    func testOverwriteDifferentKeys() async throws {
        // Given
        let key1 = generateUniqueKey()
        let key2 = generateUniqueKey()
        let value1 = "value_for_key1"
        let value2 = "value_for_key2"

        // When - 保存两个不同的键值对
        try await keychain.saveAsync(value1, forKey: key1)
        try await keychain.saveAsync(value2, forKey: key2)

        // Then - 验证两者都存在且值正确
        let retrieved1 = try await keychain.retrieveAsync(forKey: key1)
        let retrieved2 = try await keychain.retrieveAsync(forKey: key2)

        XCTAssertEqual(retrieved1, value1, "key1 的值应该正确")
        XCTAssertEqual(retrieved2, value2, "key2 的值应该正确")

        // When - 更新其中一个键的值
        let newValue1 = "new_value_for_key1"
        try await keychain.saveAsync(newValue1, forKey: key1)

        // Then - 验证 key1 更新了，key2 不受影响
        let newRetrieved1 = try await keychain.retrieveAsync(forKey: key1)
        let retrieved2Again = try await keychain.retrieveAsync(forKey: key2)

        XCTAssertEqual(newRetrieved1, newValue1, "key1 的值应该更新")
        XCTAssertEqual(retrieved2Again, value2, "key2 的值不应该被影响")

        // 清理
        try? await keychain.deleteAsync(forKey: key1)
        try? await keychain.deleteAsync(forKey: key2)
    }
}
