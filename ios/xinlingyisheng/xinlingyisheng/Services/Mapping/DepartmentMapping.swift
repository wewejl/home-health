//
//  DepartmentMapping.swift
//  xinlingyisheng
//
//  科室类型前后端映射
//

import Foundation

/// 科室类型前后端映射
enum DepartmentMapping {

    /// 后端枚举值 → 前端枚举值 映射表
    private static let backendToFrontend: [String: DepartmentType] = [
        "derma": .dermatology,
        "cardio": .cardiology,
        "ortho": .orthopedics,
        "neuro": .neurology,
        "gastro": .gastroenterology,
        "general": .general,
        "endo": .gynecology,
        "respiratory": .pediatrics,
        "endocrinology": .gynecology
    ]

    /// 前端枚举值 → 后端枚举值 映射表（用于API请求）
    private static let frontendToBackend: [DepartmentType: String] = [
        .dermatology: "derma",
        .cardiology: "cardio",
        .orthopedics: "ortho",
        .neurology: "neuro",
        .gastroenterology: "gastro",
        .general: "general",
        .gynecology: "endo",
        .pediatrics: "respiratory"
    ]

    /// 从后端值解析
    static func fromBackend(_ rawValue: String) -> DepartmentType {
        backendToFrontend[rawValue] ?? .general
    }

    /// 转换为后端值
    static func toBackend(_ type: DepartmentType) -> String {
        frontendToBackend[type] ?? "general"
    }
}
