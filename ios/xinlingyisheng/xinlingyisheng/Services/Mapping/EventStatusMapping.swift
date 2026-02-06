//
//  EventStatusMapping.swift
//  xinlingyisheng
//
//  事件状态前后端映射
//

import Foundation

/// 事件状态前后端映射
enum EventStatusMapping {

    private static let backendToFrontend: [String: EventStatus] = [
        "active": .active,
        "in_progress": .inProgress,
        "completed": .completed,
        "exported": .exported,
        "archived": .archived
    ]

    private static let frontendToBackend: [EventStatus: String] = [
        .active: "active",
        .inProgress: "in_progress",
        .completed: "completed",
        .exported: "exported",
        .archived: "archived"
    ]

    static func fromBackend(_ rawValue: String) -> EventStatus {
        backendToFrontend[rawValue] ?? .active
    }

    static func toBackend(_ status: EventStatus) -> String {
        frontendToBackend[status] ?? "active"
    }
}
