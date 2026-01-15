---
trigger: always_on
priority: critical
---

# API 接口契约文档

**版本**: V1.0  
**更新日期**: 2026-01-15  
**Base URL**: `http://localhost:8100` (开发环境)

> ⚠️ **重要**: 本文档是前后端接口的**单一真相源**。所有接口定义、字段类型、枚举值必须以本文档为准。

---

## 目录

1. [通用规范](#通用规范)
2. [数据类型约定](#数据类型约定)
3. [认证接口](#认证接口)
4. [会话接口](#会话接口)
5. [病历事件接口](#病历事件接口)
6. [AI 算法接口](#ai-算法接口)
7. [错误处理](#错误处理)

---

## 通用规范

### 认证方式

所有需要认证的接口使用 **Bearer Token**：

```http
Authorization: Bearer <jwt_token>
```

### 响应格式

成功响应：
```json
{
  "data": { ... },
  "message": "操作成功"
}
```

错误响应：
```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

- `200` - 成功
- `201` - 创建成功
- `204` - 删除成功（无返回内容）
- `400` - 请求参数错误
- `401` - 未认证或认证过期
- `403` - 无权访问
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## 数据类型约定

### ⚠️ 关键字段类型（必须严格遵守）

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `event_id` | **String** | 病历事件ID（UUID格式） | `"b3ebf9eb-8695-4ad6-b9b3-5e559dc47997"` |
| `session_id` | **String** | 会话ID（UUID格式） | `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` |
| `user_id` | **Integer** | 用户ID | `123` |
| `doctor_id` | **Integer** | 医生ID | `456` |
| `department_id` | **Integer** | 科室ID | `1` |

### 枚举类型

#### EventStatus (事件状态)
```typescript
type EventStatus = "active" | "completed" | "archived" | "exported"
```

#### RiskLevel (风险等级)
```typescript
type RiskLevel = "low" | "medium" | "high" | "emergency"
```

#### AgentType (智能体类型)
```typescript
type AgentType = "cardio" | "derma" | "ortho" | "neuro" | "general" | "endo" | "gastro" | "respiratory"
```

**iOS 命名映射**:
- `dermatology` → `derma` (皮肤科)
- `cardiology` → `cardio` (心血管科)
- `orthopedics` → `ortho` (骨科)
- `neurology` → `neuro` (神经科)
- `endocrinology` → `endo` (内分泌科)
- `gastroenterology` → `gastro` (消化科)

#### AttachmentType (附件类型)
```typescript
type AttachmentType = "image" | "report" | "voice"
```

---

## 认证接口

### 1. 用户登录

```http
POST /auth/login
```

**请求体**:
```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "phone": "13800138000",
    "nickname": "用户昵称"
  }
}
```

---

## 会话接口

### 1. 创建统一会话

```http
POST /sessions
```

**请求体**:
```json
{
  "doctor_id": 1,
  "agent_type": "dermatology"
}
```

**响应**:
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "agent_type": "derma",
  "created_at": "2026-01-15T10:30:00Z"
}
```

### 2. 发送消息（流式）

```http
POST /sessions/{session_id}/messages
Content-Type: application/json
```

**请求体**:
```json
{
  "content": "我最近皮肤有点痒",
  "attachments": [
    {
      "type": "image",
      "data": "base64_encoded_image_data"
    }
  ],
  "action": "conversation"
}
```

**响应** (Server-Sent Events):
```
data: {"chunk": "根据您的描述"}
data: {"chunk": "，可能是"}
data: {"chunk": "过敏反应"}
data: [DONE]
```

**最终响应**:
```json
{
  "message": "根据您的描述，可能是过敏反应...",
  "structured_data": {
    "symptoms": ["瘙痒", "红疹"],
    "risk_level": "low"
  },
  "quick_options": ["继续描述", "上传照片"],
  "stage": "collecting",
  "event_id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
  "is_new_event": true,
  "should_show_dossier_prompt": false
}
```

### 3. 获取消息历史

```http
GET /sessions/{session_id}/messages?limit=50
```

**响应**:
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "sender": "user",
      "content": "我最近皮肤有点痒",
      "message_type": "text",
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
  "has_more": false
}
```

---

## 病历事件接口

### 1. 聚合会话到病历事件 ⚠️

```http
POST /medical-events/aggregate
```

**请求体**:
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_type": "dermatology"
}
```

**响应**:
```json
{
  "event_id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
  "message": "会话已聚合到病历事件",
  "is_new_event": true,
  "session_summary": {
    "chief_complaint": "皮肤瘙痒",
    "symptoms": ["瘙痒", "红疹"],
    "risk_level": "low",
    "message_count": 5,
    "has_images": true
  }
}
```

**⚠️ 关键字段类型**:
- `event_id`: **String** (UUID格式)
- `is_new_event`: **Boolean**

### 2. 获取病历事件列表

```http
GET /medical-events?page=1&page_size=20
```

**查询参数**:
- `keyword`: 搜索关键词
- `department`: 科室筛选
- `agent_type`: 智能体类型
- `status`: 状态筛选
- `risk_level`: 风险等级
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）

**响应**:
```json
{
  "events": [
    {
      "id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
      "title": "皮肤科 2026-01-15",
      "department": "皮肤科",
      "agent_type": "derma",
      "status": "active",
      "risk_level": "low",
      "start_time": "2026-01-15T10:30:00Z",
      "end_time": null,
      "summary": "患者主诉皮肤瘙痒...",
      "chief_complaint": "皮肤瘙痒",
      "attachment_count": 2,
      "session_count": 1,
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T10:35:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### 3. 获取病历事件详情

```http
GET /medical-events/{event_id}
```

**响应**:
```json
{
  "id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
  "title": "皮肤科 2026-01-15",
  "department": "皮肤科",
  "agent_type": "derma",
  "status": "active",
  "risk_level": "low",
  "start_time": "2026-01-15T10:30:00Z",
  "end_time": null,
  "summary": "患者主诉皮肤瘙痒...",
  "chief_complaint": "皮肤瘙痒",
  "ai_analysis": {
    "symptoms": ["瘙痒", "红疹"],
    "possible_diagnosis": ["过敏性皮炎", "湿疹"],
    "recommendations": ["避免抓挠", "保持皮肤清洁"],
    "follow_up_reminders": ["3天后复诊"],
    "timeline": [
      {
        "time": "2026-01-15",
        "event": "症状开始",
        "type": "symptom_onset"
      }
    ]
  },
  "sessions": [
    {
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "session_type": "derma",
      "timestamp": "2026-01-15T10:30:00Z",
      "summary": "皮肤科问诊 - 皮肤瘙痒"
    }
  ],
  "attachments": [],
  "notes": [],
  "attachment_count": 0,
  "session_count": 1,
  "export_count": 0,
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:35:00Z"
}
```

### 4. 创建病历事件

```http
POST /medical-events
```

**请求体**:
```json
{
  "title": "皮肤科就诊",
  "department": "皮肤科",
  "agent_type": "derma",
  "chief_complaint": "皮肤瘙痒",
  "risk_level": "low"
}
```

**响应**: 同详情接口

### 5. 更新病历事件

```http
PUT /medical-events/{event_id}
```

**请求体**:
```json
{
  "title": "更新后的标题",
  "status": "completed",
  "risk_level": "medium"
}
```

### 6. 归档病历事件

```http
POST /medical-events/{event_id}/archive
```

**响应**: 同详情接口

### 7. 删除病历事件

```http
DELETE /medical-events/{event_id}?confirm=true
```

**响应**: 204 No Content

---

## AI 算法接口

### 1. 生成 AI 摘要

```http
POST /ai/summary
```

**请求体**:
```json
{
  "event_id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
  "force_regenerate": false
}
```

**响应**:
```json
{
  "event_id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
  "summary": "患者主诉皮肤瘙痒2天...",
  "key_points": ["持续性瘙痒", "局部红疹"],
  "symptoms": ["瘙痒", "红疹"],
  "possible_diagnosis": ["过敏性皮炎"],
  "risk_level": "low",
  "recommendations": ["避免抓挠", "保持清洁"],
  "confidence": 0.85,
  "message": "摘要生成成功"
}
```

### 2. 智能聚合分析

```http
POST /ai/smart-aggregate
```

**请求体**:
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_type": "derma",
  "department": "皮肤科",
  "chief_complaint": "皮肤红疹"
}
```

**响应**:
```json
{
  "action": "add_to_existing",
  "target_event_id": "b3ebf9eb-8695-4ad6-b9b3-5e559dc47997",
  "confidence": 0.95,
  "reasoning": "同一天同一科室的问诊",
  "should_merge": true
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误

#### 401 Unauthorized
```json
{
  "detail": "未认证或认证过期"
}
```

#### 404 Not Found
```json
{
  "detail": "会话不存在: session-uuid"
}
```

#### 400 Bad Request
```json
{
  "detail": "请求参数错误: event_id 必须为字符串"
}
```

---

## iOS 客户端集成指南

### 数据模型定义

```swift
// ⚠️ 关键：event_id 必须为 String
struct AggregateSessionResponse: Decodable {
    let event_id: String  // UUID 格式
    let message: String
    let is_new_event: Bool
}

struct MedicalEventDTO: Decodable {
    let id: String  // UUID 格式
    let title: String
    let department: String
    let agent_type: String
    let status: String
    let risk_level: String
    // ...
}
```

### API 调用示例

```swift
func aggregateSession(sessionId: String, sessionType: String) async throws -> AggregateSessionResponse {
    let endpoint = APIConfig.baseURL + "/medical-events/aggregate"
    
    let requestBody: [String: Any] = [
        "session_id": sessionId,
        "session_type": sessionType
    ]
    
    let jsonData = try JSONSerialization.data(withJSONObject: requestBody)
    
    var request = URLRequest(url: URL(string: endpoint)!)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    request.httpBody = jsonData
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(AggregateSessionResponse.self, from: data)
}
```

---

## 版本历史

### V1.0 (2026-01-15)
- 初始版本
- 明确 `event_id` 为 String (UUID) 类型
- 统一枚举类型定义
- 添加 iOS 集成指南

---

## 相关文档

- [全局开发规范](./DEVELOPMENT_GUIDELINES.md)
- [iOS 开发指南](./IOS_DEVELOPMENT_GUIDE.md)
- [后端 API 详细文档](../backend/docs/AI_API_DOCUMENTATION.md)

---

**文档维护者**: 项目团队  
**最后更新**: 2026-01-15  
**下次审查**: 每次接口变更时必须更新
