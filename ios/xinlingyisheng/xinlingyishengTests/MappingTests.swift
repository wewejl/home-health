//
//  MappingTests.swift
//  xinlingyishengTests
//
//  TDD 测试：病历映射层单元测试
//

import XCTest
@testable import xinlingyisheng

/// 科室类型映射测试
final class DepartmentMappingTests: XCTestCase {

    // 🔴 RED: 测试后端值到前端值的映射
    func testBackendToFrontendMapping() {
        // 后端返回 "derma" 应映射到 .dermatology
        XCTAssertEqual(DepartmentMapping.fromBackend("derma"), .dermatology)

        // 后端返回 "cardio" 应映射到 .cardiology
        XCTAssertEqual(DepartmentMapping.fromBackend("cardio"), .cardiology)

        // 后端返回 "ortho" 应映射到 .orthopedics
        XCTAssertEqual(DepartmentMapping.fromBackend("ortho"), .orthopedics)

        // 后端返回 "neuro" 应映射到 .neurology
        XCTAssertEqual(DepartmentMapping.fromBackend("neuro"), .neurology)

        // 后端返回 "gastro" 应映射到 .gastroenterology
        XCTAssertEqual(DepartmentMapping.fromBackend("gastro"), .gastroenterology)

        // 后端返回 "general" 应映射到 .general
        XCTAssertEqual(DepartmentMapping.fromBackend("general"), .general)

        // 后端返回 "endo" 应映射到 .endocrinology
        XCTAssertEqual(DepartmentMapping.fromBackend("endo"), .endocrinology)

        // 后端返回 "respiratory" 应映射到 .respiratory
        XCTAssertEqual(DepartmentMapping.fromBackend("respiratory"), .respiratory)

        // 未知值应 fallback 到 .general
        XCTAssertEqual(DepartmentMapping.fromBackend("unknown"), .general)
        XCTAssertEqual(DepartmentMapping.fromBackend(""), .general)
    }

    // 🔴 RED: 测试前端值到后端值的映射
    func testFrontendToBackendMapping() {
        // 前端 .dermatology 应映射到 "derma"
        XCTAssertEqual(DepartmentMapping.toBackend(.dermatology), "derma")

        // 前端 .cardiology 应映射到 "cardio"
        XCTAssertEqual(DepartmentMapping.toBackend(.cardiology), "cardio")

        // 前端 .orthopedics 应映射到 "ortho"
        XCTAssertEqual(DepartmentMapping.toBackend(.orthopedics), "ortho")

        // 前端 .neurology 应映射到 "neuro"
        XCTAssertEqual(DepartmentMapping.toBackend(.neurology), "neuro")

        // 前端 .gastroenterology 应映射到 "gastro"
        XCTAssertEqual(DepartmentMapping.toBackend(.gastroenterology), "gastro")

        // 前端 .general 应映射到 "general"
        XCTAssertEqual(DepartmentMapping.toBackend(.general), "general")

        // 前端 .endocrinology 应映射到 "endo"
        XCTAssertEqual(DepartmentMapping.toBackend(.endocrinology), "endo")

        // 前端 .respiratory 应映射到 "respiratory"
        XCTAssertEqual(DepartmentMapping.toBackend(.respiratory), "respiratory")
    }

    // 🔴 RED: 测试往返转换一致性
    func testRoundTripConsistency() {
        let allTypes: [DepartmentType] = [
            .dermatology, .cardiology, .orthopedics, .neurology,
            .gastroenterology, .general, .endocrinology, .respiratory
        ]

        for type in allTypes {
            let backendValue = DepartmentMapping.toBackend(type)
            let frontendValue = DepartmentMapping.fromBackend(backendValue)
            XCTAssertEqual(
                frontendValue,
                type,
                "Round trip failed for \(type): \(type) -> \(backendValue) -> \(frontendValue)"
            )
        }
    }
}

/// 事件状态映射测试
final class EventStatusMappingTests: XCTestCase {

    // 🔴 RED: 测试后端值到前端值的映射
    func testBackendToFrontendMapping() {
        // 后端返回 "active" 应映射到 .active
        XCTAssertEqual(EventStatusMapping.fromBackend("active"), .active)

        // 后端返回 "in_progress" 应映射到 .inProgress
        XCTAssertEqual(EventStatusMapping.fromBackend("in_progress"), .inProgress)

        // 后端返回 "completed" 应映射到 .completed
        XCTAssertEqual(EventStatusMapping.fromBackend("completed"), .completed)

        // 后端返回 "exported" 应映射到 .exported
        XCTAssertEqual(EventStatusMapping.fromBackend("exported"), .exported)

        // 后端返回 "archived" 应映射到 .archived
        XCTAssertEqual(EventStatusMapping.fromBackend("archived"), .archived)

        // 未知值应 fallback 到 .active
        XCTAssertEqual(EventStatusMapping.fromBackend("unknown"), .active)
        XCTAssertEqual(EventStatusMapping.fromBackend(""), .active)
    }

    // 🔴 RED: 测试前端值到后端值的映射
    func testFrontendToBackendMapping() {
        // 前端 .active 应映射到 "active"
        XCTAssertEqual(EventStatusMapping.toBackend(.active), "active")

        // 前端 .inProgress 应映射到 "in_progress"
        XCTAssertEqual(EventStatusMapping.toBackend(.inProgress), "in_progress")

        // 前端 .completed 应映射到 "completed"
        XCTAssertEqual(EventStatusMapping.toBackend(.completed), "completed")

        // 前端 .exported 应映射到 "exported"
        XCTAssertEqual(EventStatusMapping.toBackend(.exported), "exported")

        // 前端 .archived 应映射到 "archived"
        XCTAssertEqual(EventStatusMapping.toBackend(.archived), "archived")
    }

    // 🔴 RED: 测试往返转换一致性
    func testRoundTripConsistency() {
        let allStatuses: [EventStatus] = [
            .active, .inProgress, .completed, .exported, .archived
        ]

        for status in allStatuses {
            let backendValue = EventStatusMapping.toBackend(status)
            let frontendValue = EventStatusMapping.fromBackend(backendValue)
            XCTAssertEqual(
                frontendValue,
                status,
                "Round trip failed for \(status): \(status) -> \(backendValue) -> \(frontendValue)"
            )
        }
    }
}
