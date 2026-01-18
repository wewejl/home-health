import Foundation

// MARK: - 会话状态管理器
/// 管理活跃会话状态，支持会话恢复
class SessionStateManager {
    static let shared = SessionStateManager()
    
    private let userDefaults = UserDefaults.standard
    private let activeSessionKey = "ActiveSessions"
    
    private init() {}
    
    // MARK: - 活跃会话管理
    
    /// 保存活跃会话
    /// - Parameters:
    ///   - doctorId: 医生ID
    ///   - sessionId: 会话ID
    func saveActiveSession(doctorId: Int, sessionId: String) {
        var sessions = getActiveSessions()
        sessions[String(doctorId)] = sessionId
        userDefaults.set(sessions, forKey: activeSessionKey)
        print("✅ [SessionStateManager] 保存活跃会话: doctorId=\(doctorId), sessionId=\(sessionId)")
    }
    
    /// 获取活跃会话ID
    /// - Parameter doctorId: 医生ID
    /// - Returns: 会话ID，如果不存在则返回nil
    func getActiveSession(doctorId: Int) -> String? {
        let sessions = getActiveSessions()
        print("✅ [SessionStateManager] getActiveSession - 当前所有会话: \(sessions)")
        let sessionId = sessions[String(doctorId)]
        if let id = sessionId {
            print("✅ [SessionStateManager] 找到活跃会话: doctorId=\(doctorId), sessionId=\(id)")
        } else {
            print("⚠️ [SessionStateManager] 未找到活跃会话: doctorId=\(doctorId)")
        }
        return sessionId
    }
    
    /// 清除活跃会话
    /// - Parameter doctorId: 医生ID
    func clearActiveSession(doctorId: Int) {
        var sessions = getActiveSessions()
        sessions.removeValue(forKey: String(doctorId))
        userDefaults.set(sessions, forKey: activeSessionKey)
        print("🗑️ [SessionStateManager] 清除活跃会话: doctorId=\(doctorId)")
    }
    
    /// 清除所有活跃会话
    func clearAllActiveSessions() {
        userDefaults.removeObject(forKey: activeSessionKey)
        print("🗑️ [SessionStateManager] 清除所有活跃会话")
    }
    
    /// 获取所有活跃会话
    private func getActiveSessions() -> [String: String] {
        return userDefaults.dictionary(forKey: activeSessionKey) as? [String: String] ?? [:]
    }
    
    // MARK: - 会话信息缓存
    
    private let sessionInfoKey = "SessionInfoCache"
    
    /// 缓存会话信息
    func cacheSessionInfo(_ info: CachedSessionInfo) {
        var cache = getAllCachedSessionInfo()
        cache[info.sessionId] = info
        
        if let encoded = try? JSONEncoder().encode(cache) {
            userDefaults.set(encoded, forKey: sessionInfoKey)
        }
    }
    
    /// 获取缓存的会话信息
    func getCachedSessionInfo(sessionId: String) -> CachedSessionInfo? {
        return getAllCachedSessionInfo()[sessionId]
    }
    
    /// 获取所有缓存的会话信息
    private func getAllCachedSessionInfo() -> [String: CachedSessionInfo] {
        guard let data = userDefaults.data(forKey: sessionInfoKey),
              let cache = try? JSONDecoder().decode([String: CachedSessionInfo].self, from: data) else {
            return [:]
        }
        return cache
    }
}

// MARK: - 缓存的会话信息
struct CachedSessionInfo: Codable {
    let sessionId: String
    let doctorId: Int?
    let doctorName: String
    let department: String
    let agentType: String
    let lastMessage: String?
    let updatedAt: Date
}
