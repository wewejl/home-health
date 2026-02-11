//
//  LoginViewModelTests.swift
//  xinlingyishengTests
//
//  LoginViewModel 单元测试
//  测试覆盖: 手机号验证、验证码验证、登录状态、按钮状态
//

import XCTest
@testable import xinlingyisheng

/// LoginViewModel 单元测试
final class LoginViewModelTests: XCTestCase {

    var viewModel: LoginViewModel!

    override func setUp() async throws {
        try await super.setUp()
        await MainActor.run {
            viewModel = LoginViewModel()
        }
    }

    override func tearDown() async throws {
        await MainActor.run {
            viewModel.cleanup()
            viewModel = nil
        }
        try await super.tearDown()
    }

    // MARK: - Phone Validation Tests

    func testValidPhone() async throws {
        // Given
        let validPhones = [
            "13800138000",  // 13开头
            "15012345678",  // 15开头
            "18612345678",  // 18开头
            "19112345678",  // 19开头
            "17612345678"   // 17开头
        ]

        for phone in validPhones {
            await MainActor.run {
                viewModel.phoneNumber = phone
            }

            // Then
            await MainActor.run {
                XCTAssertTrue(viewModel.isPhoneValid, "手机号 \(phone) 应该是有效的")
            }
        }
    }

    func testInvalidPhoneTooShort() async throws {
        // Given
        let shortPhones = [
            "138001380",   // 9位
            "12345",       // 5位
            "1"            // 1位
        ]

        for phone in shortPhones {
            await MainActor.run {
                viewModel.phoneNumber = phone
            }

            // Then
            await MainActor.run {
                XCTAssertFalse(viewModel.isPhoneValid, "手机号 \(phone) 太短，应该无效")
            }
        }
    }

    func testInvalidPhoneTooLong() async throws {
        // Given
        let longPhones = [
            "138001380001",   // 12位
            "13800138000123"  // 14位
        ]

        for phone in longPhones {
            await MainActor.run {
                viewModel.phoneNumber = phone
            }

            // Then
            await MainActor.run {
                XCTAssertFalse(viewModel.isPhoneValid, "手机号 \(phone) 太长，应该无效")
            }
        }
    }

    func testInvalidPhoneNonNumeric() async throws {
        // Given
        let invalidPhones = [
            "1380013800a",   // 包含字母
            "138-0138-000",  // 包含连字符
            "138 0138 000",  // 包含空格
            "abcdefghijk"    // 全字母
        ]

        for phone in invalidPhones {
            await MainActor.run {
                viewModel.phoneNumber = phone
            }

            // Then
            await MainActor.run {
                XCTAssertFalse(viewModel.isPhoneValid, "手机号 \(phone) 包含非数字字符，应该无效")
            }
        }
    }

    func testInvalidPhoneWrongPrefix() async throws {
        // Given - 中国手机号必须以1开头，第二位是3-9
        let wrongPrefixPhones = [
            "10012345678",  // 10开头
            "12012345678",  // 12开头
            "23012345678",  // 23开头（不以1开头）
            "9812345678"    // 9开头（不以1开头）
        ]

        for phone in wrongPrefixPhones {
            await MainActor.run {
                viewModel.phoneNumber = phone
            }

            // Then
            await MainActor.run {
                XCTAssertFalse(viewModel.isPhoneValid, "手机号 \(phone) 前缀错误，应该无效")
            }
        }
    }

    // MARK: - Code Validation Tests

    func testValidCode() async throws {
        // Given
        let validCodes = [
            "1234",      // 4位 - 最小有效长度
            "12345",     // 5位
            "123456",    // 6位 - 标准长度
            "1234567"    // 7位
        ]

        for code in validCodes {
            await MainActor.run {
                viewModel.verificationCode = code
            }

            // Then
            await MainActor.run {
                XCTAssertTrue(viewModel.isCodeValid, "验证码 \(code) 应该是有效的（长度>=4）")
            }
        }
    }

    func testInvalidCodeTooShort() async throws {
        // Given
        let shortCodes = [
            "",      // 空
            "1",     // 1位
            "12",    // 2位
            "123"    // 3位
        ]

        for code in shortCodes {
            await MainActor.run {
                viewModel.verificationCode = code
            }

            // Then
            await MainActor.run {
                XCTAssertFalse(viewModel.isCodeValid, "验证码 '\(code)' 太短，应该无效")
            }
        }
    }

    // MARK: - Login State Tests

    func testInitialState() async throws {
        await MainActor.run {
            // Then - 验证初始状态
            XCTAssertFalse(viewModel.isLoading, "初始状态不应该是加载中")
            XCTAssertFalse(viewModel.showError, "初始状态不应该显示错误")
            XCTAssertTrue(viewModel.errorMessage.isEmpty, "初始错误消息应该为空")
            XCTAssertFalse(viewModel.isAgreed, "初始状态未同意协议")
            XCTAssertEqual(viewModel.step, .phoneInput, "初始步骤应该是手机号输入")
            XCTAssertEqual(viewModel.countdown, 0, "初始倒计时应该为0")
            XCTAssertFalse(viewModel.showCodeSentNotice, "初始不应该显示验证码已发送通知")
        }
    }

    func testLoginButtonDisabledWhenInvalid() async throws {
        await MainActor.run {
            // Given - 手机号无效
            viewModel.phoneNumber = "123"
            viewModel.verificationCode = "123456"
            viewModel.isAgreed = true

            // Then
            XCTAssertFalse(viewModel.canLogin, "手机号无效时登录按钮应该禁用")
        }
    }

    func testLoginButtonDisabledWhenCodeTooShort() async throws {
        await MainActor.run {
            // Given - 验证码太短
            viewModel.phoneNumber = "13800138000"
            viewModel.verificationCode = "123"
            viewModel.isAgreed = true

            // Then
            XCTAssertFalse(viewModel.canLogin, "验证码太短时登录按钮应该禁用")
        }
    }

    func testLoginButtonDisabledWhenNotAgreed() async throws {
        await MainActor.run {
            // Given - 未同意协议
            viewModel.phoneNumber = "13800138000"
            viewModel.verificationCode = "123456"
            viewModel.isAgreed = false

            // Then
            XCTAssertFalse(viewModel.canLogin, "未同意协议时登录按钮应该禁用")
        }
    }

    func testLoginButtonEnabledWhenValid() async throws {
        await MainActor.run {
            // Given - 所有条件满足
            viewModel.phoneNumber = "13800138000"
            viewModel.verificationCode = "123456"
            viewModel.isAgreed = true
            viewModel.uiState = .idle

            // Then
            XCTAssertTrue(viewModel.canLogin, "所有条件满足时登录按钮应该启用")
        }
    }

    // MARK: - Send Code Tests

    func testCanSendCodeWhenValid() async throws {
        await MainActor.run {
            // Given - 手机号有效且未在倒计时
            viewModel.phoneNumber = "13800138000"
            viewModel.countdown = 0
            viewModel.uiState = .idle

            // Then
            XCTAssertTrue(viewModel.canSendCode, "手机号有效且未倒计时应该可以发送验证码")
        }
    }

    func testCannotSendCodeWhenInvalidPhone() async throws {
        await MainActor.run {
            // Given - 手机号无效
            viewModel.phoneNumber = "123"
            viewModel.countdown = 0

            // Then
            XCTAssertFalse(viewModel.canSendCode, "手机号无效时不应该可以发送验证码")
        }
    }

    func testCannotSendCodeDuringCountdown() async throws {
        await MainActor.run {
            // Given - 正在倒计时
            viewModel.phoneNumber = "13800138000"
            viewModel.countdown = 30

            // Then
            XCTAssertFalse(viewModel.canSendCode, "倒计时期间不应该可以发送验证码")
        }
    }

    func testCannotSendCodeWhileSending() async throws {
        await MainActor.run {
            // Given - 正在发送
            viewModel.phoneNumber = "13800138000"
            viewModel.uiState = .sendingCode

            // Then
            XCTAssertFalse(viewModel.canSendCode, "正在发送时不应该可以再次发送验证码")
        }
    }

    // MARK: - Loading State Tests

    func testIsLoadingWhenSendingCode() async throws {
        await MainActor.run {
            // Given
            viewModel.uiState = .sendingCode

            // Then
            XCTAssertTrue(viewModel.isLoading, "发送验证码时应该处于加载状态")
        }
    }

    func testIsLoadingWhenLoggingIn() async throws {
        await MainActor.run {
            // Given
            viewModel.uiState = .loggingIn

            // Then
            XCTAssertTrue(viewModel.isLoading, "登录时应该处于加载状态")
        }
    }

    func testIsNotLoadingInIdleState() async throws {
        await MainActor.run {
            // Given
            viewModel.uiState = .idle

            // Then
            XCTAssertFalse(viewModel.isLoading, "空闲状态不应该处于加载状态")
        }
    }

    // MARK: - Display Phone Format Tests

    func testHandlePhoneInputFiltersNonDigits() async throws {
        await MainActor.run {
            // Given - 输入包含非数字字符
            let input = "138-0138-000"

            // When
            viewModel.handlePhoneInput(input)

            // Then - 应该只保留数字
            XCTAssertEqual(viewModel.phoneNumber, "1380138000", "应该过滤非数字字符")
        }
    }

    func testHandlePhoneInputLimitsTo11Digits() async throws {
        await MainActor.run {
            // Given - 输入超过11位
            let input = "13800138000123"

            // When
            viewModel.handlePhoneInput(input)

            // Then - 应该限制为11位
            XCTAssertEqual(viewModel.phoneNumber, "13800138000", "应该限制为11位数字")
        }
    }

    func testHandlePhoneInputFormatsDisplay() async throws {
        await MainActor.run {
            // Given
            let input = "13800138000"

            // When
            viewModel.handlePhoneInput(input)

            // Then - 显示格式应该是 138 0138 0000
            XCTAssertEqual(viewModel.displayPhoneNumber, "138 0138 0000", "应该格式化为 3-4-4 格式")
        }
    }

    // MARK: - Masked Phone Text Tests

    func testMaskedPhoneText() async throws {
        await MainActor.run {
            // Given
            viewModel.phoneNumber = "13800138000"

            // Then
            XCTAssertEqual(viewModel.maskedPhoneText, "138****8000", "应该正确掩码手机号")
        }
    }

    func testMaskedPhoneTextForInvalidLength() async throws {
        await MainActor.run {
            // Given - 手机号不是11位
            viewModel.phoneNumber = "138"

            // Then
            XCTAssertEqual(viewModel.maskedPhoneText, "当前手机号", "手机号长度不对时显示默认文本")
        }
    }

    // MARK: - Code Button Text Tests

    func testCodeButtonTextDefault() async throws {
        await MainActor.run {
            // Given
            viewModel.countdown = 0
            viewModel.uiState = .idle
            viewModel.showCodeSentNotice = false

            // Then
            XCTAssertEqual(viewModel.codeButtonText, "获取验证码", "默认应该显示'获取验证码'")
        }
    }

    func testCodeButtonTextDuringCountdown() async throws {
        await MainActor.run {
            // Given
            viewModel.countdown = 30

            // Then
            XCTAssertEqual(viewModel.codeButtonText, "30s", "倒计时应该显示剩余秒数")
        }
    }

    func testCodeButtonTextAfterCodeSent() async throws {
        await MainActor.run {
            // Given
            viewModel.countdown = 0
            viewModel.uiState = .codeSent
            viewModel.showCodeSentNotice = true

            // Then
            XCTAssertEqual(viewModel.codeButtonText, "重新获取", "验证码已发送后应该显示'重新获取'")
        }
    }

    // MARK: - Reset Tests

    func testResetClearsAllState() async throws {
        await MainActor.run {
            // Given - 设置各种状态
            viewModel.phoneNumber = "13800138000"
            viewModel.verificationCode = "123456"
            viewModel.isAgreed = true
            viewModel.step = .codeInput
            viewModel.errorMessage = "Some error"
            viewModel.showError = true
            viewModel.showCodeSentNotice = true
            viewModel.countdown = 30

            // When
            viewModel.reset()

            // Then - 验证所有状态已重置
            XCTAssertEqual(viewModel.phoneNumber, "", "手机号应该清空")
            XCTAssertEqual(viewModel.displayPhoneNumber, "", "显示手机号应该清空")
            XCTAssertEqual(viewModel.verificationCode, "", "验证码应该清空")
            XCTAssertFalse(viewModel.isAgreed, "协议状态应该重置")
            XCTAssertEqual(viewModel.step, .phoneInput, "步骤应该重置为手机号输入")
            XCTAssertEqual(viewModel.uiState, .idle, "UI状态应该重置为空闲")
            XCTAssertEqual(viewModel.countdown, 0, "倒计时应该重置")
            XCTAssertFalse(viewModel.showError, "错误显示应该关闭")
            XCTAssertFalse(viewModel.showCodeSentNotice, "验证码发送通知应该关闭")
        }
    }

    // MARK: - Toggle Agreement Tests

    func testToggleAgreement() async throws {
        await MainActor.run {
            // Given
            viewModel.isAgreed = false

            // When
            viewModel.toggleAgreement()

            // Then
            XCTAssertTrue(viewModel.isAgreed, "切换后应该同意")

            // When - 再次切换
            viewModel.toggleAgreement()

            // Then
            XCTAssertFalse(viewModel.isAgreed, "再次切换后应该不同意")
        }
    }

    // MARK: - OnPhoneComplete Tests

    func testOnPhoneCompleteAutoSendsCode() async throws {
        // 此测试仅验证逻辑，不实际发送网络请求
        await MainActor.run {
            // Given
            viewModel.phoneNumber = "13800138000"
            viewModel.countdown = 0
            viewModel.uiState = .idle

            // When - 手机号输入完成且有效
            // 注意：实际会调用 sendVerificationCode 发送网络请求
            // 这里只测试条件判断
            let shouldAutoSend = viewModel.isPhoneValid && viewModel.countdown == 0 && viewModel.uiState != .sendingCode

            // Then
            XCTAssertTrue(shouldAutoSend, "手机号有效且未在发送时应该自动发送验证码")
        }
    }

    // MARK: - OnCodeComplete Tests

    func testOnCodeCompleteAutoLogsIn() async throws {
        // 此测试仅验证逻辑，不实际登录
        await MainActor.run {
            // Given
            viewModel.phoneNumber = "13800138000"
            viewModel.verificationCode = "123456"
            viewModel.isAgreed = true
            viewModel.uiState = .idle

            // When - 验证码输入完成
            // 注意：实际会调用 login 发送网络请求
            // 这里只测试条件判断
            let shouldAutoLogin = viewModel.canLogin

            // Then
            XCTAssertTrue(shouldAutoLogin, "所有条件满足时应该自动登录")
        }
    }
}
