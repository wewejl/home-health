//
//  xinlingyishengUITests.swift
//  xinlingyishengUITests
//
//  Created on 2026-02-01.
//

import XCTest

final class xinlingyishengUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    override func tearDownWithError() throws {
    }

    @MainActor
    func testExample() throws {
        let app = XCUIApplication()
        app.launch()

        // 测试应用是否成功启动
        XCTAssertTrue(app.exists, "应用应该成功启动")
    }

    @MainActor
    func testLaunchPerformance() throws {
        if #available(iOS 13.0, *) {
            measure(metrics: [XCTApplicationLaunchMetric()]) {
                XCUIApplication().launch()
            }
        }
    }
}
