//
//  AuthManagerTests.swift
//  xinlingyishengTests
//
//  AuthManager 单元测试
//  测试覆盖: Token 管理、登录/登出、用户资料更新
//

import XCTest
@testable import xinlingyisheng

/// AuthManager 单元测试
final class AuthManagerTests: XCTestCase {

    var authManager: AuthManager!
    let testTimeout: TimeInterval = 5.0

    override func setUp() async throws {
        try await super.setUp()
        await MainActor.run {
            authManager = AuthManager.shared
        }
        // 清理测试数据
        await cleanupTestData()
    }

    override func tearDown() async throws {
        // 清理测试数据
        await cleanupTestData()
        await MainActor.run {
            authManager = nil
        }
        try await super.tearDown()
    }

    // MARK: - Helper Methods

    private func cleanupTestData() async {
        // 清除可能存在的测试 token
        let keychain = KeychainManager.shared
        try? await keychain.deleteAsync(forKey: "auth_token")
        try? await keychain.deleteAsync(forKey: "refresh_token")

        // 清除 UserDefaults 中的用户数据
        UserDefaults.standard.removeObject(forKey: "current_user")

        // 等待异步操作完成
        await MainActor.run {
            authManager?.token = nil
            authManager?.refreshToken = nil
            authManager?.currentUser = nil
            authManager?.isLoggedIn = false
        }
    }

    private func createTestUser() -> UserModel {
        return UserModel(
            id: 999,
            phone: "13800138000",
            nickname: "测试用户",
            avatar_url: nil,
            gender: "male",
            birthday: "1990-01-01",
            emergency_contact_name: nil,
            emergency_contact_phone: nil,
            emergency_contact_relation: nil,
            is_profile_completed: true,
            created_at: Date(),
            updated_at: Date()
        )
    }

    // MARK: - Token Management Tests

    func testSaveAccessToken() async throws {
        // Given
        let token = "test_access_token_123"

        // When
        await MainActor.run {
            authManager.login(
                token: token,
                refreshToken: nil,
                user: createTestUser(),
                isNewUser: false
            )
        }

        // 等待异步保存完成
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5秒

        // Then - 验证 Keychain 中的 token
        let keychain = KeychainManager.shared
        do {
            let retrieved = try await keychain.retrieveAsync(forKey: "auth_token")
            XCTAssertEqual(retrieved, token, "保存的访问令牌应该与检索的一致")
        } catch {
            XCTFail("获取访问令牌失败: \(error.localizedDescription)")
        }

        // Then - 验证 AuthManager 状态
        await MainActor.run {
            XCTAssertEqual(authManager.token, token, "AuthManager 的 token 应该更新")
            XCTAssertTrue(authManager.isLoggedIn, "登录状态应该为 true")
            XCTAssertNotNil(authManager.currentUser, "当前用户不应为 nil")
        }
    }

    func testSaveRefreshToken() async throws {
        // Given
        let accessToken = "test_access_token"
        let refreshToken = "test_refresh_token_456"

        // When
        await MainActor.run {
            authManager.login(
                token: accessToken,
                refreshToken: refreshToken,
                user: createTestUser(),
                isNewUser: false
            )
        }

        // 等待异步保存完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // Then - 验证 Keychain 中的 refresh token
        let keychain = KeychainManager.shared
        do {
            let retrieved = try await keychain.retrieveAsync(forKey: "refresh_token")
            XCTAssertEqual(retrieved, refreshToken, "保存的刷新令牌应该与检索的一致")
        } catch {
            XCTFail("获取刷新令牌失败: \(error.localizedDescription)")
        }

        // Then - 验证 AuthManager 状态
        await MainActor.run {
            XCTAssertEqual(authManager.refreshToken, refreshToken, "AuthManager 的 refreshToken 应该更新")
        }
    }

    func testClearAllTokens() async throws {
        // Given - 先保存 tokens
        let accessToken = "test_access_token"
        let refreshToken = "test_refresh_token"

        await MainActor.run {
            authManager.login(
                token: accessToken,
                refreshToken: refreshToken,
                user: createTestUser(),
                isNewUser: false
            )
        }

        // 等待保存完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // 验证保存成功
        await MainActor.run {
            XCTAssertNotNil(authManager.token, "Token 应该已保存")
            XCTAssertNotNil(authManager.refreshToken, "RefreshToken 应该已保存")
            XCTAssertTrue(authManager.isLoggedIn, "登录状态应该为 true")
        }

        // When - 登出
        await MainActor.run {
            authManager.logout()
        }

        // 等待清除完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // Then - 验证状态已清除
        await MainActor.run {
            XCTAssertNil(authManager.token, "Token 应该被清除")
            XCTAssertNil(authManager.refreshToken, "RefreshToken 应该被清除")
            XCTAssertNil(authManager.currentUser, "当前用户应该被清除")
            XCTAssertFalse(authManager.isLoggedIn, "登录状态应该为 false")
            XCTAssertFalse(authManager.isNewUser, "新用户标志应该被清除")
            XCTAssertFalse(authManager.needsProfileSetup, "资料完善标志应该被清除")
        }

        // Then - 验证 Keychain 已清除
        let keychain = KeychainManager.shared
        let tokenExists = keychain.exists(forKey: "auth_token")
        let refreshExists = keychain.exists(forKey: "refresh_token")

        XCTAssertFalse(tokenExists, "访问令牌应该从 Keychain 中清除")
        XCTAssertFalse(refreshExists, "刷新令牌应该从 Keychain 中清除")
    }

    // MARK: - Login Tests

    func testLoginWithCode() async throws {
        // Given
        let testToken = "login_test_token"
        let testRefreshToken = "login_test_refresh_token"
        let testUser = createTestUser()

        // When - 模拟登录
        await MainActor.run {
            authManager.login(
                token: testToken,
                refreshToken: testRefreshToken,
                user: testUser,
                isNewUser: true
            )
        }

        // 等待异步操作完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // Then
        await MainActor.run {
            XCTAssertEqual(authManager.token, testToken, "Token 应该设置正确")
            XCTAssertEqual(authManager.refreshToken, testRefreshToken, "RefreshToken 应该设置正确")
            XCTAssertEqual(authManager.currentUser?.id, testUser.id, "用户 ID 应该匹配")
            XCTAssertEqual(authManager.currentUser?.phone, testUser.phone, "手机号应该匹配")
            XCTAssertTrue(authManager.isLoggedIn, "登录状态应该为 true")
            XCTAssertTrue(authManager.isNewUser, "新用户标志应该为 true")
            XCTAssertFalse(authManager.needsProfileSetup, "测试用户资料已完善，不需要完善资料")
        }
    }

    func testLoginWithIncompleteProfile() async throws {
        // Given - 创建资料不完整的用户
        let incompleteUser = UserModel(
            id: 998,
            phone: "13800138001",
            nickname: nil,
            avatar_url: nil,
            gender: nil,
            birthday: nil,
            emergency_contact_name: nil,
            emergency_contact_phone: nil,
            emergency_contact_relation: nil,
            is_profile_completed: false,
            created_at: Date(),
            updated_at: Date()
        )

        // When
        await MainActor.run {
            authManager.login(
                token: "test_token",
                refreshToken: nil,
                user: incompleteUser,
                isNewUser: false
            )
        }

        // 等待异步操作完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // Then
        await MainActor.run {
            XCTAssertTrue(authManager.needsProfileSetup, "应该需要完善资料")
        }
    }

    func testLogout() async throws {
        // Given - 先登录
        let testUser = createTestUser()
        await MainActor.run {
            authManager.login(
                token: "logout_test_token",
                refreshToken: "logout_test_refresh",
                user: testUser,
                isNewUser: false
            )
        }

        // 等待保存完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // 验证已登录
        await MainActor.run {
            XCTAssertTrue(authManager.isLoggedIn, "应该已登录")
            XCTAssertNotNil(authManager.currentUser, "用户不应该为 nil")
        }

        // When - 登出
        await MainActor.run {
            authManager.logout()
        }

        // 等待清除完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // Then
        await MainActor.run {
            XCTAssertNil(authManager.token, "Token 应该为 nil")
            XCTAssertNil(authManager.refreshToken, "RefreshToken 应该为 nil")
            XCTAssertNil(authManager.currentUser, "用户应该为 nil")
            XCTAssertFalse(authManager.isLoggedIn, "登录状态应该为 false")
            XCTAssertFalse(authManager.isNewUser, "新用户标志应该为 false")
            XCTAssertFalse(authManager.needsProfileSetup, "资料完善标志应该为 false")
        }
    }

    // MARK: - User Profile Tests

    func testUpdateProfile() async throws {
        // Given - 先登录
        let originalUser = createTestUser()
        await MainActor.run {
            authManager.login(
                token: "update_test_token",
                refreshToken: nil,
                user: originalUser,
                isNewUser: false
            )
        }

        // 等待保存完成
        try await Task.sleep(nanoseconds: 500_000_000)

        // Given - 创建更新后的用户
        let updatedUser = UserModel(
            id: originalUser.id,
            phone: originalUser.phone,
            nickname: "更新后的用户名",
            avatar_url: "https://example.com/avatar.jpg",
            gender: "female",
            birthday: "1995-05-15",
            emergency_contact_name: "紧急联系人",
            emergency_contact_phone: "13900139000",
            emergency_contact_relation: "配偶",
            is_profile_completed: true,
            created_at: originalUser.created_at,
            updated_at: Date()
        )

        // When - 更新用户信息
        await MainActor.run {
            authManager.updateUser(updatedUser)
        }

        // Then
        await MainActor.run {
            XCTAssertEqual(authManager.currentUser?.nickname, "更新后的用户名", "昵称应该更新")
            XCTAssertEqual(authManager.currentUser?.gender, "female", "性别应该更新")
            XCTAssertEqual(authManager.currentUser?.birthday, "1995-05-15", "生日应该更新")
            XCTAssertFalse(authManager.needsProfileSetup, "资料已完善，不需要完善资料")
        }

        // 验证 UserDefaults 中的数据
        if let userData = UserDefaults.standard.data(forKey: "current_user"),
           let savedUser = try? JSONDecoder().decode(UserModel.self, from: userData) {
            XCTAssertEqual(savedUser.nickname, "更新后的用户名", "UserDefaults 中的昵称应该更新")
        } else {
            XCTFail("应该能从 UserDefaults 中读取用户数据")
        }
    }

    func testUpdateProfileWithIncompleteStatus() async throws {
        // Given
        let incompleteUser = UserModel(
            id: 997,
            phone: "13800138002",
            nickname: nil,
            avatar_url: nil,
            gender: nil,
            birthday: nil,
            emergency_contact_name: nil,
            emergency_contact_phone: nil,
            emergency_contact_relation: nil,
            is_profile_completed: false,
            created_at: Date(),
            updated_at: Date()
        )

        // When - 更新为资料不完整的用户
        await MainActor.run {
            authManager.login(
                token: "test_token",
                refreshToken: nil,
                user: createTestUser(),
                isNewUser: false
            )
            authManager.updateUser(incompleteUser)
        }

        // Then
        await MainActor.run {
            XCTAssertTrue(authManager.needsProfileSetup, "应该需要完善资料")
        }
    }

    // MARK: - Token Validation Tests

    func testHasValidTokenWhenTokenExists() async throws {
        // Given
        await MainActor.run {
            authManager.login(
                token: "valid_token",
                refreshToken: nil,
                user: createTestUser(),
                isNewUser: false
            )
        }

        // Then
        await MainActor.run {
            XCTAssertTrue(authManager.hasValidToken, "应该有有效的 token")
        }
    }

    func testHasValidTokenWhenTokenNil() async throws {
        // Given - 登出状态
        await MainActor.run {
            authManager.logout()
        }

        // Then
        await MainActor.run {
            XCTAssertFalse(authManager.hasValidToken, "Token 为 nil 时不应该有有效 token")
        }
    }

    func testHasValidTokenWhenTokenEmpty() async throws {
        // Given - 设置空 token
        await MainActor.run {
            authManager.token = ""
        }

        // Then
        await MainActor.run {
            XCTAssertFalse(authManager.hasValidToken, "空 token 不应该被认为是有效的")
        }
    }
}
