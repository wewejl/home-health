import Foundation
import os.log

/// 应用统一日志工具
/// 在生产环境自动禁用详细日志，仅在开发环境输出
///
/// 使用方式:
/// ```swift
/// AppLogger.log("用户登录成功")
/// AppLogger.error("登录失败", error: error)
/// AppLogger.network("发送请求", url: url)
/// ```
enum AppLogger {
    /// 日志子系统标识符
    private static let subsystem = "com.xinlingyisheng.app"

    /// 是否为调试模式 (通过编译配置控制)
    #if DEBUG
    private static var isDebug: Bool { true }
    #else
    private static var isDebug: Bool { false }
    #endif

    // MARK: - 公共日志方法

    /// 普通日志
    static func log(
        _ message: String,
        category: String = "General",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("%{public}@", log: osLog, type: .info, message)
    }

    /// 调试日志 (仅在开发环境)
    static func debug(
        _ message: String,
        category: String = "Debug",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("%{public}@", log: osLog, type: .debug, message)
    }

    /// 信息日志
    static func info(
        _ message: String,
        category: String = "Info",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("%{public}@", log: osLog, type: .info, message)
    }

    /// 成功日志 (带 ✅ 前缀)
    static func success(
        _ message: String,
        category: String = "Success",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("✅ %{public}@", log: osLog, type: .info, message)
    }

    /// 警告日志 (带 ⚠️ 前缀)
    static func warning(
        _ message: String,
        category: String = "Warning",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("⚠️ %{public}@", log: osLog, type: .default, message)
    }

    /// 错误日志
    static func error(
        _ message: String,
        error: Error? = nil,
        category: String = "Error",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        let osLog = OSLog(subsystem: subsystem, category: category)
        if let error = error {
            os_log("❌ %{public}@: %{public}@", log: osLog, type: .error, message, error.localizedDescription)
        } else {
            os_log("❌ %{public}@", log: osLog, type: .error, message)
        }
    }

    /// 网络请求日志
    static func network(
        _ message: String,
        url: String? = nil,
        category: String = "Network",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        if let url = url {
            os_log("🌐 %{public}@: %{public}@", log: osLog, type: .info, message, url)
        } else {
            os_log("🌐 %{public}@", log: osLog, type: .info, message)
        }
    }

    /// 数据库操作日志
    static func database(
        _ message: String,
        category: String = "Database",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("💾 %{public}@", log: osLog, type: .info, message)
    }

    /// 性能日志
    static func performance(
        _ message: String,
        duration: TimeInterval? = nil,
        category: String = "Performance",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        if let duration = duration {
            os_log("⏱️ %{public}@: %.2fms", log: osLog, type: .info, message, duration * 1000)
        } else {
            os_log("⏱️ %{public}@", log: osLog, type: .info, message)
        }
    }

    /// 清理日志 (带 🗑️ 前缀)
    static func cleanup(
        _ message: String,
        category: String = "Cleanup",
        file: String = #file,
        function: String = #function,
        line: Int = #line
    ) {
        guard isDebug else { return }
        let osLog = OSLog(subsystem: subsystem, category: category)
        os_log("🗑️ %{public}@", log: osLog, type: .info, message)
    }
}
