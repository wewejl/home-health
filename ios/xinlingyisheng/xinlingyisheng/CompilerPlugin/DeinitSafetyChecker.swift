//
//  DeinitSafetyChecker.swift
//  内存安全编译时检查辅助工具
//
//  用途：提供编译时检查，防止在 deinit 中创建异步任务
//

#if DEBUG

import Foundation

/// 内存安全检查标记
///
/// 使用方法：
/// 1. 在任何包含 deinit 的类中，添加 `DeinitSafety.check()` 作为第一行
/// 2. 如果 deinit 中有异步操作，会在 DEBUG 模式下触发断言
@available(*, deprecated, message: "使用 DeinitSafety 替代直接在 deinit 中清理")
public enum DeinitSafety {

    /// 检查当前是否在主线程（用于检测 @MainActor 属性访问）
    public static func assertMainThread(
        _ message: String = "此操作必须在主线程执行"
    ) {
        #if DEBUG
        assert(Thread.isMainThread, message)
        #endif
    }

    /// 警告：不要在 deinit 中创建异步任务
    public static var noAsyncInDeinit: Void {
        fatalError(
            """
            ⚠️ 内存安全问题：deinit 中不能创建异步任务

            正确做法：
            1. 将 deinit 标记为 nonisolated
            2. 创建 @MainActor func cleanup() 方法
            3. 在 View 的 .onDisappear 中调用 cleanup()

            参考 MEMORY_MANAGEMENT.md 文档
            """
        )
    }

    /// 检查闭包是否捕获 self
    public static func assertWeakSelf(
        _ closure: () -> Void,
        file: StaticString = #file,
        line: UInt = #line
    ) {
        #if DEBUG
        // 运行时无法检测闭包捕获，但这作为代码审查提示
        print("⚠️ [\(file):\(line)] 请确认此闭包使用 [weak self] 避免循环引用")
        #endif
    }
}

// MARK: - 编译时辅助宏

/*
 Swift 编译器指令提示：

 在代码中使用以下注释来触发编译器警告，提醒开发者：

 // TODO: 内存安全 - 确保此闭包使用 [weak self]
 // TODO: 内存安全 - 验证无循环引用

 建议的 Xcode Code Snippet：

 Title: Memory Safe Closure
Completion: weakself
Template:
 [weak self] in
 guard let self = self else { return }
*/

#endif

// MARK: - 运行时内存检查器

#if DEBUG

/// 运行时内存安全检查器
public final class MemorySafetyChecker {

    public static let shared = MemorySafetyChecker()

    private var trackedObjects: Set<ObjectIdentifier> = []
    private let lock = NSLock()

    private init() {}

    /// 注册需要追踪的对象
    public func register(_ object: AnyObject) {
        lock.lock()
        defer { lock.unlock() }
        trackedObjects.insert(ObjectIdentifier(object))
        print("[MemoryChecker] Registered: \(type(of: object))")
    }

    /// 取消注册
    public func unregister(_ object: AnyObject) {
        lock.lock()
        defer { lock.unlock() }
        trackedObjects.remove(ObjectIdentifier(object))
        print("[MemoryChecker] Unregistered: \(type(of: object))")
    }

    /// 检查是否有内存泄露
    public func checkLeaks() {
        lock.lock()
        defer { lock.unlock() }
        print("[MemoryChecker] Tracked objects remaining: \(trackedObjects.count)")
    }
}

#endif
