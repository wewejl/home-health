//
//  SecurityConfig.swift
//

import Foundation

enum SecurityConfig {
    static let apiBaseURL = "http://localhost:8100"
    static let websocketBaseURL = "ws://localhost:8100/ws"

    static func log(_ message: String) {
        #if DEBUG
        print("[SecurityConfig] \(message)")
        #endif
    }
}
