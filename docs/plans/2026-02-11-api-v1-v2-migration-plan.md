# API V1/V2 合并方案设计

> **创建时间**: 2026-02-11
> **状态**: 待评审
> **优先级**: P1
> **预估工作量**: 16 小时

---

## 一、问题分析

### 1.1 现状

后端存在两套会话 API：
- **V1**: `sessions.py` - 已废弃，代码已删除
- **V2**: `sessions_v2.py` - 当前使用，路径 `/v2/sessions`

根据技术债务清单描述，两套 API "并存" 导致维护成本高。

### 1.2 核实发现

经过代码审查，**V1 版本实际已被删除**：

| 检查项 | 结果 |
|---------|------|
| `backend/app/routes/sessions.py` | ❌ 文件不存在 |
| `main.py` 中引用 | ❌ 只有 V2 路由 (`sessions_v2_router`) |
| V1 注释 | ✅ 代码注释："V1 已废弃" |

**结论**: API V1/V2 并存问题**实际不存在**——V1 已完全移除，只保留 V2。

---

## 二、客户端使用分析

### 2.1 前端 (React)

| API 调用 | 端点 | 说明 |
|-----------|--------|------|
| `getPatientConsultations` | `/api/doctor/patients/{id}/consultations` | 医生工作台专用，非 sessions API |
| `getConsultation` | `/api/doctor/consultations/{id}` | 医生工作台专用，非 sessions API |

**前端不直接调用 sessions API**，而是使用医生工作台封装的接口。

### 2.2 iOS (Swift)

| 服务 | 文件 | 端点 | 状态 |
|------|------|------|--------|
| UnifiedChatAPIService | `UnifiedChatAPIService.swift` | `/sessions` | ⚠️ 存在但已废弃 |
| UnifiedChatAPIServiceV2 | `UnifiedChatAPIServiceV2.swift` | `/v2/sessions` | ✅ 当前使用 |

**iOS 正在使用 V2 API**，V1 服务类虽存在但已废弃。

---

## 三、根本问题

技术债务清单中记录的 "API V1/V2 并存" 问题，实际上是**命名和代码清理问题**：

1. **V1 路由文件已删除** - 问题已自然解决
2. **iOS V1 服务类未删除** - 这是遗留代码
3. **技术债务文档未更新** - 记录与现状不符

---

## 四、解决方案

### 方案 A：清理遗留代码 (推荐)

**目标**: 移除已废弃的 V1 代码，更新文档

#### 前端
- ✅ 无需操作（前端不使用 sessions API）

#### iOS
| 操作 | 文件 | 工作量 |
|------|------|----------|
| 删除 `UnifiedChatAPIService.swift` | `ios/.../Services/UnifiedChatAPIService.swift` | 1 小时 |
| 搜索并移除 V1 服务引用 | 各 ViewModel | 2 小时 |
| 验证编译 | - | 0.5 小时 |

#### 后端
- ✅ 无需操作（V1 已删除）

#### 文档
| 操作 | 文件 | 工作量 |
|------|------|----------|
| 更新 `tech-debt.md`，标记此项为"已还清" | `docs/planning/tech-debt.md` | 0.5 小时 |

**总工作量**: 约 4 小时

---

### 方案 B：统一端点路径 (备选)

**目标**: 移除 V2 的 `/v2/` 前缀，使其成为主版本

#### 优点
- API 路径更简洁 (`/sessions` 而非 `/v2/sessions`)
- 未来版本演进更清晰

#### 缺点
- 需要修改 iOS 客户端
- 破坏性变更，风险较高

#### 工作量
| 模块 | 工作量 |
|------|----------|
| 后端路由修改 | 2 小时 |
| iOS 端点修改 | 3 小时 |
| 测试验证 | 2 小时 |
| **总计** | **7 小时** |

---

## 五、推荐方案

### 推荐：方案 A (清理遗留代码)

**理由**:
1. **问题已自然解决** - V1 后端代码已删除
2. **风险低** - 仅删除遗留代码，无破坏性变更
3. **工作量小** - 约 4 小时 vs 7+ 小时
4. **优先级低** - 不影响当前功能

### 实施步骤

```
Phase 1: iOS 清理 (3.5 小时)
  1. 搜索 UnifiedChatAPIService 引用
  2. 删除 UnifiedChatAPIService.swift
  3. 更新所有引用为 UnifiedChatAPIServiceV2
  4. 编译验证

Phase 2: 文档更新 (0.5 小时)
  1. 更新 tech-debt.md
  2. 说明 V1 已删除，仅遗留 iOS 代码需清理
```

---

## 六、决策建议

| 决策点 | 建议 |
|---------|------|
| 是否需要保留 `/v2/` 前缀 | ❌ 不需要，当前无版本冲突 |
| 是否需要统一 V1/V2 | ✅ 是，但只需删除遗留 V1 |
| 优先级 | P2（低），不影响功能 |

---

## 七、风险与依赖

| 风险 | 概率 | 缓解措施 |
|-------|--------|----------|
| iOS 隐藏的 V1 调用 | 低 | 全局搜索 "UnifiedChatAPIService" |
| 破坏现有功能 | 极低 | V1 已废弃，仅删除代码 |

---

## 八、完成标准

- [ ] iOS 移除 `UnifiedChatAPIService.swift`
- [ ] iOS 验证编译通过
- [ ] iOS 全局搜索确认无 V1 引用
- [ ] `tech-debt.md` 更新为"已还清"
- [ ] 测试 iOS 聊天功能正常
