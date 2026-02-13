# iOS 代码优化方案（修正版）

> **创建日期**: 2026-02-12
> **版本**: v2.0 (基于审核反馈修正)
> **审核依据**: `docs/iOS优化方案-审核报告.md`

---

## 修订说明

### 修正内容

| 类别 | 原方案问题 | 修正内容 |
|--------|-------------|----------|
| 日志 API | 使用了不存在的 `logger_fault` | 修正为 Apple 标准的 `Logger.error()` |
| 枚举完整性 | switch 语句缺少 default 分支 | 添加 default 分支 |
| 架构评估 | 未发现已有三服务架构 | 更新现状评估 |
| 实施建议 | 部分高风险重构建议 | 降低风险，聚焦实际可优化点 |

---

## 目录

1. [实际现状评估](#一实际现状评估)
2. [高优先级优化](#二高优先级优化-1-2周)
3. [中优先级优化](#三中优先级优化-2-4周)
4. [低优先级优化](#四低优先级优化-1-2月)

---

## 一、实际现状评估

### 1.1 已正确实现的架构

#### ✅ 服务层已按功能拆分

```
Services/
├── Chat/                              # 聊天相关服务
│   ├── ChatSessionService.swift         # 会话管理
│   ├── ChatMessageService.swift          # 消息管理
│   └── ChatVoiceInputService.swift       # 语音输入
├── Voice/
│   ├── PressAndHoldVoiceService.swift    # 按住说话
│   └── SimpleSpeechInputService.swift     # 简单语音输入
├── AuthManager.swift                   # 认证管理
├── APIService.swift                    # 通用 API
├── SessionStateManager.swift             # 会话状态
└── ...
```

**结论**: 服务层职责分离**已经做得很好**，不需要大规模重构。

---

#### ✅ 日志系统已存在

```swift
// 项目中已有的 AppLogger
AppLogger.debug("...")
AppLogger.info("...")
AppLogger.success("...")
AppLogger.error("...", error: ...)
AppLogger.cleanup("...")
```

**优化方向**: 推广使用现有 `AppLogger`，而非创建新系统。

---

#### ✅ 正确使用 Swift Concurrency

```swift
@MainActor
class AuthManager: ObservableObject { ... }

@MainActor
class UnifiedChatViewModel: ObservableObject { ... }
```

**结论**: 项目正确使用了 `@MainActor` 标记 UI 相关类。

---

### 1.2 确认需要优化的地方

#### ⚠️ 日志使用不一致

| 文件 | 当前方式 | 需要改进 |
|------|----------|-----------|
| AuthManager.swift | print() | 使用 AppLogger |
| APIService.swift | print() | 使用 AppLogger |
| SessionStateManager.swift | print() | 使用 AppLogger |

---

#### ⚠️ 图片处理可能在主线程

**位置**: `UnifiedChatViewModel.swift:433`

```swift
// 当前实现（可能阻塞主线程）
private func resizeImageIfNeeded(_ image: UIImage, maxDimension: CGFloat) -> UIImage {
    UIGraphicsBeginImageContextWithOptions(...)
    image.draw(in: ...)
    let resizedImage = UIGraphicsGetImageFromCurrentImageContext()
    UIGraphicsEndImageContext()
    return resizedImage ?? image
}
```

---

#### ⚠️ deinit 清理不统一

| 类 | deinit 实现 |
|-----|------------|
| UnifiedChatViewModel | ✅ 有 deinit |
| AuthManager | ❌ 无 deinit |
| MedicalDossierViewModel | ❌ 无 deinit |

---

## 二、高优先级优化（1-2周）

### 2.1 统一日志使用

#### 目标
将所有 `print()` 替换为 `AppLogger` 调用。

#### 实施步骤

**步骤 1**: 创建替换清单

| 文件 | 需要替换的位置 |
|------|----------------|
| AuthManager.swift | 10+ 处 print() |
| APIService.swift | 20+ 处 print() |
| SessionStateManager.swift | 5+ 处 print() |

**步骤 2**: 逐文件替换

```swift
// 替换前
print("[Auth] Token 从 Keychain 加载成功")

// 替换后
AppLogger.debug("Token 从 Keychain 加载成功")
```

**步骤 3**: 验证

运行应用，确保日志输出正常。

---

### 2.2 添加统一的 deinit 清理

#### 目标
为所有 `ObservableObject` ViewModel 添加 `deinit` 清理。

#### 实施模板

```swift
// ViewModel 添加 deinit 模板
nonisolated deinit {
    // 1. 取消所有 Combine 订阅
    cancellables.forEach { $0.cancel() }
    cancellables.removeAll()

    // 2. 清理资源
    voiceService?.cleanup()
    messageService?.clearMessages()

    // 3. 日志记录
    AppLogger.cleanup("[\(type(of: self))] 资源已清理")
}
```

#### 需要添加的文件

| ViewModel | 优先级 |
|-----------|--------|
| AuthManager | 高 |
| MedicalDossierViewModel | 高 |
| MedicalOrderViewModel | 中 |
| ProfileSetupViewModel | 中 |

---

### 2.3 图片处理异步化

#### 目标
将图片压缩操作移到后台线程执行。

#### 实施方案

**方案 A: 使用 Task.detached**

```swift
import Accelerate

// 图片处理服务
@MainActor
class ImageProcessingService {
    static let shared = ImageProcessingService()

    func resize(_ image: UIImage, maxDimension: CGFloat) async -> UIImage {
        await Task.detached(priority: .userInitiated) {
            // 在后台线程执行
            return await self.resizeInBackground(image, maxDimension: maxDimension)
        }.value
    }

    private func resizeInBackground(_ image: UIImage, maxDimension: CGFloat) async -> UIImage {
        // 使用 vImage API (iOS 15+)
        if #available(iOS 15.0, *) {
            return await resizeUsingImageIO(image, maxDimension: maxDimension)
        } else {
            // 降级到 UIGraphics
            return resizeUsingUIGraphics(image, maxDimension: maxDimension)
        }
    }

    @available(iOS 15.0, *)
    private func resizeUsingImageIO(_ image: UIImage, maxDimension: CGFloat) async -> UIImage {
        let scale = maxDimension / max(image.size.width, image.size.height)

        return await withCheckedThrowingContinuation { continuation in
            guard let cgImage = image.cgImage else {
                continuation.resume(returning: image)
                return
            }

            let options: [CFDictionaryKey: Any] = [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceThumbnailMaxPixelSize: max(Int(maxDimension)),
                kCGImageSourceCreateThumbnailFromImageIfRepresentable: true
            ]

            guard let thumbnail = CGImageSourceCreateWithData(cgImage.data as CFData, options: options as CFDictionary),
                  let scaledImage = CGImageSourceCreateThumbnailFromImage(thumbnail, maxDimension) else {
                continuation.resume(returning: image)
                return
            }

            continuation.resume(returning: UIImage(cgImage: scaledImage))
        }
    }
}
```

**方案 B: 简化方案（最小改动）**

如果不想引入新服务，只需在调用处添加 `async`：

```swift
// 在 UnifiedChatViewModel 中修改
func handleSelectedImage(_ image: UIImage) async {
    guard let sessionId = sessionService.sessionId else {
        print("[UnifiedChatVM] ❌ sessionId 为 nil, 无法处理图片")
        return
    }

    // 异步压缩图片
    let resizedImage = await ImageResizer.shared.resize(image, maxDimension: 1024)

    // 继续处理...
    await messageService.handleSelectedImage(resizedImage, sessionId: sessionId, action: action)
}
```

---

## 三、中优先级优化（2-4周）

### 3.1 减少不必要的 @Published 属性

#### 目标
审查 ViewModel 中的 `@Published` 属性，移除不需要 UI 响应的属性。

#### 实施步骤

**步骤 1**: 审查 UnifiedChatViewModel

| 属性 | 是否需要 @Published | 建议 |
|--------|------------------|------|
| sessionId | ✅ 需要 | 保留 |
| agentType | ✅ 需要 | 保留 |
| capabilities | ✅ 需要 | 保留 |
| currentDoctorId | ⚠️ 可能不需要 | 考虑改为内部状态 |
| streamingContent | ✅ 需要 | 保留（流式输出） |
| adviceHistory | ⚠️ 可能不需要 | 考虑按需加载 |

**步骤 2**: 优化示例

```swift
// ❌ 过度暴露
@Published var internalState: SomeInternalState?

// ✅ 只暴露 UI 需要的
@Published var isLoading: Bool = false  // UI 需要加载状态

// 内部状态不使用 @Published
private var internalState: SomeInternalState?
```

---

### 3.2 添加 API 响应缓存

#### 目标
对不常变化的 API 响应添加缓存，减少网络请求。

#### 实施方案

```swift
// Services/Cache/APICache.swift

import Foundation

/// API 响应缓存
@MainActor
class APICache {
    static let shared = APICache()

    private let cache = NSCache<NSString, CacheEntry>()

    private struct CacheEntry {
        let data: Data
        let expiryDate: Date
        var isValid: Bool {
            return Date() < expiryDate
        }
    }

    // 缓存配置
    private struct Config {
        static let shortCache: TimeInterval = 5 * 60      // 5分钟
        static let mediumCache: TimeInterval = 15 * 60    // 15分钟
        static let longCache: TimeInterval = 60 * 60      // 1小时
    }

    // 获取缓存
    func get<T: Decodable>(_ key: String, type: T.Type) async -> T? {
        guard let entry = cache.object(forKey: key as NSString),
              entry.isValid else {
            return nil
        }

        return try? JSONDecoder().decode(T.self, from: entry.data)
    }

    // 设置缓存
    func set<T: Encodable>(_ key: String, value: T, duration: TimeInterval = Config.mediumCache) {
        let expiryDate = Date().addingTimeInterval(duration)
        let data = (try? JSONEncoder().encode(value)) ?? Data()

        let entry = CacheEntry(data: data, expiryDate: expiryDate)
        cache.setObject(entry, forKey: key as NSString)
    }

    // 清除缓存
    func remove(_ key: String) {
        cache.removeObject(forKey: key as NSString)
    }

    func clearAll() {
        cache.removeAllObjects()
    }
}

// 使用示例
class DepartmentsService {
    private let cache = APICache.shared

    func getDepartments(forceRefresh: Bool = false) async throws -> [DepartmentModel] {
        let cacheKey = "departments_list"

        // 检查缓存
        if !forceRefresh, let cached: [DepartmentModel] = await cache.get(cacheKey, type: [DepartmentModel].self) {
            return cached
        }

        // 请求网络
        let result: [DepartmentModel] = try await APIService.shared.getDepartments()

        // 缓存结果（15分钟）
        await cache.set(cacheKey, value: result, duration: Config.mediumCache)

        return result
    }
}
```

---

### 3.3 改进错误处理用户提示

#### 目标
将技术错误转换为用户友好的提示信息。

#### 实施方案

```swift
// Models/DisplayError.swift

import Foundation

/// 用户可理解的错误类型
enum DisplayError: Error {
    case networkUnavailable(message: String)
    case unauthorized(message: String)
    case serverError(message: String)
    case invalidInput(message: String)
    case operationFailed(message: String)

    var userMessage: String {
        switch self {
        case .networkUnavailable(let msg):
            return msg
        case .unauthorized(let msg):
            return msg
        case .serverError(let msg):
            return msg
        case .invalidInput(let msg):
            return msg
        case .operationFailed(let msg):
            return msg
        }
    }

    var title: String {
        switch self {
        case .networkUnavailable: return "网络连接问题"
        case .unauthorized: return "登录已过期"
        case .serverError: return "服务器错误"
        case .invalidInput: return "输入错误"
        case .operationFailed: return "操作失败"
        }
    }

    // 从 APIError 转换
    static func from(_ error: Error) -> DisplayError {
        if let apiError = error as? APIError {
            switch apiError {
            case .networkError:
                return .networkUnavailable(message: "网络连接失败，请检查网络设置")
            case .unauthorized:
                return .unauthorized(message: "登录已过期，请重新登录")
            case .decodingError:
                return .serverError(message: "数据解析错误，请重试")
            default:
                return .operationFailed(message: "操作失败，请稍后重试")
            }
        }
        return .operationFailed(message: error.localizedDescription)
    }
}
```

---

## 四、低优先级优化（1-2月）

### 4.1 代码规范完善

#### 命名规范

```swift
// ✅ 好的命名
let currentSessionId: String
var isLoadingEvents: Bool
func fetchUserSessions() async throws -> [Session]

// ❌ 避免的命名
let sid: String
var loading: Bool
func get() -> [Session]
```

#### 访问控制

```swift
public class PublicAPI {
    public func doSomething() { ... }
}

internal class InternalAPI {
    internal func doSomething() { ... }
}

private class PrivateAPI {
    private func doSomething() { ... }
}

fileprivate class FilePrivateAPI {
    fileprivate func doSomething() { ... }
}
```

---

### 4.2 性能监控

#### 目标
添加关键性能指标监控。

#### 实施方案

```swift
// Utils/Performance/Monitor.swift

import Foundation
import os

/// 性能监控
@MainActor
class PerformanceMonitor {
    static let shared = PerformanceMonitor()

    private let logger = Logger(subsystem: "com.lingxiyisheng", category: "Performance")

    // 性能指标
    @Published var apiResponseTime: TimeInterval = 0
    @Published var memoryUsage: UInt64 = 0

    // 测量 API 响应时间
    func measure<T>(_ name: String, operation: () async throws -> T) async rethrows -> T {
        let start = Date()
        let result = try await operation()
        let duration = Date().timeIntervalSince(start)

        if duration > 1.0 {  // 超过1秒记录
            logger.warning("[Performance] \(name) took \(duration)s")
        }

        return result
    }

    // 测量内存使用
    func updateMemoryUsage() {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t()
        let result = withUnsafeMutablePointer(to: &info) {
            task_info(mach_task_self_,
                     TASK_BASIC_INFO,
                     $0,
                     &count)
        }
        let used = result.resident_size
        memoryUsage = used
    }
}

// 使用示例
let response = await PerformanceMonitor.shared.measure("getDepartments") {
    try await APIService.shared.getDepartments()
}
```

---

## 五、不建议的优化

### 5.1 完全拆分 UnifiedChatViewModel

**原因**:
1. 内部已经通过三个服务分离了职责
2. View 需要统一的访问接口
3. 完全拆分会增加状态同步复杂度

**建议**: 保持当前架构，只做小幅优化。

---

### 5.2 大规模重构 APIService

**原因**:
1. `APIService` 已是成熟稳定的单例模式
2. 很多 API 方法已在其他服务中实现
3. 协议抽象会增加复杂度而收益不明显

**建议**: 保持当前结构，只做必要的改进。

---

## 六、实施计划

### 6.1 第一周

| 任务 | 预计时间 | 负责人 |
|------|-----------|--------|
| 统一 AuthManager 日志 | 1天 | iOS 开发 |
| 统一 APIService 日志 | 1天 | iOS 开发 |
| 统一 SessionStateManager 日志 | 0.5天 | iOS 开发 |
| 为关键 ViewModel 添加 deinit | 1天 | iOS 开发 |
| 图片处理异步化（方案B） | 2天 | iOS 开发 |

---

### 6.2 第二周

| 任务 | 预计时间 | 负责人 |
|------|-----------|--------|
| 实现 API 缓存 | 2天 | iOS 开发 |
| 审查和优化 @Published 属性 | 1天 | iOS 开发 |
| 改进错误处理提示 | 1天 | iOS 开发 |
| 代码规范检查和修正 | 1天 | iOS 开发 |

---

### 6.3 后续（根据实际情况）

| 任务 | 预计时间 | 触发条件 |
|------|-----------|----------|
| 性能监控添加 | 1周 | 出现性能问题时 |
| 单元测试完善 | 2周 | 时间允许时 |
| UI 测试编写 | 1周 | 关键流程不稳定时 |

---

## 七、验证清单

### 7.1 优化后验证

- [ ] 日志输出正常，无丢失
- [ ] 图片上传不阻塞 UI
- [ ] 列表滚动流畅
- [ ] 内存占用无明显增加
- [ ] deinit 日志正常输出
- [ ] 错误提示用户友好
- [ ] API 缓存命中率达到预期

---

## 八、总结

### 核心原则

1. **最小改动**: 优先选择改动小、收益明显的优化
2. **保持稳定**: 不进行大规模架构重构
3. **逐步验证**: 每个优化都要测试验证
4. **文档同步**: 优化后更新相关文档

### 预期收益

| 优化项 | 预期收益 |
|--------|----------|
| 日志统一 | 便于调试和问题追踪 |
| 图片异步化 | UI 流畅度提升 |
| deinit 清理 | 内存占用减少 |
| API 缓存 | 网络请求减少，响应速度提升 |
| 错误处理改进 | 用户体验提升 |

---

*方案版本: v2.0 (修正版)*
*审核依据: docs/iOS优化方案-审核报告.md*
*生成日期: 2026-02-12*
