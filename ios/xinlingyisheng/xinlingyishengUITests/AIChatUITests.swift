//
//  AIChatUITests.swift
//  xinlingyishengUITests
//
//  AI 智能体对话端到端测试
//

import XCTest

final class AIChatUITests: XCTestCase {

    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
    }

    override func tearDownWithError() throws {
        app = nil
    }

    /// 测试完整的登录和 AI 对话流程
    @MainActor
    func testLoginAndAIChat() throws {
        app.launch()

        // 等待应用加载
        sleep(2)

        // 检查是否需要登录
        let tabBar = app.tabBars.firstMatch
        if !tabBar.waitForExistence(timeout: 3) {
            // 需要登录
            performLogin()
        }

        // 验证登录成功 - 应该看到 TabBar
        XCTAssertTrue(tabBar.waitForExistence(timeout: 5), "登录后应该显示主界面")

        // 点击首页/问诊标签
        let homeTab = app.tabBars.buttons["首页"]
        if homeTab.exists {
            homeTab.tap()
            sleep(1)
        }

        // 查找并点击 AI 问诊入口
        let aiConsultationButton = app.buttons.containing(NSPredicate(format: "label CONTAINS 'AI' OR label CONTAINS '问诊'")).firstMatch
        if aiConsultationButton.waitForExistence(timeout: 3) {
            aiConsultationButton.tap()
            sleep(2)
        }

        // 输入健康问题
        let textField = app.textFields.element(boundBy: 0)
        let textView = app.textViews.element(boundBy: 0)

        if textField.exists {
            textField.tap()
            sleep(1)
            textField.typeText("我头痛头晕三天了")
        } else if textView.exists {
            textView.tap()
            sleep(1)
            textView.typeText("我头痛头晕三天了")
        }

        sleep(1)

        // 点击发送按钮
        let sendButton = app.buttons.containing(NSPredicate(format: "label CONTAINS '发送' OR label CONTAINS '发送' OR label CONTAINS '>'")).firstMatch
        if sendButton.exists {
            sendButton.tap()
        } else {
            // 尝试使用坐标点击
            let coordinate = app.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.9))
            coordinate.tap()
        }

        // 等待 AI 响应
        sleep(5)

        // 截图保存
        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        add(attachment)

        // 验证对话界面显示
        let chatInterface = app.scrollViews.firstMatch
        XCTAssertTrue(chatInterface.exists, "应该显示对话界面")
    }

    /// 执行登录操作
    @MainActor
    private func performLogin() {
        // 查找手机号输入框
        let phoneField = app.textFields["phone"]
        let altPhoneField = app.textFields.containing(NSPredicate(format: "placeholderValue CONTAINS '手机'")).firstMatch

        if phoneField.exists {
            phoneField.tap()
            sleep(1)
            phoneField.typeText("13800138000")
        } else if altPhoneField.exists {
            altPhoneField.tap()
            sleep(1)
            altPhoneField.typeText("13800138000")
        }

        // 点击获取验证码按钮
        let getCodeButton = app.buttons.containing(NSPredicate(format: "label CONTAINS '获取验证码' OR label CONTAINS '获取'")).firstMatch
        if getCodeButton.exists {
            getCodeButton.tap()
            sleep(1)
        }

        // 输入验证码
        let codeField = app.textFields.containing(NSPredicate(format: "placeholderValue CONTAINS '验证码'")).firstMatch
        let altCodeField = app.secureTextFields.element(boundBy: 0)

        if codeField.exists {
            codeField.tap()
            sleep(1)
            codeField.typeText("123456")
        } else if altCodeField.exists {
            altCodeField.tap()
            sleep(1)
            altCodeField.typeText("123456")
        }

        // 点击登录按钮
        let loginButton = app.buttons.containing(NSPredicate(format: "label CONTAINS '登录'")).firstMatch
        if loginButton.exists {
            loginButton.tap()
        }

        // 等待登录完成
        sleep(3)
    }
}
