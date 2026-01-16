---
trigger: always_on
priority: critical
---

# API 接口契约文档

**版本**: V2.0  
**更新日期**: 2026-01-17  
**Base URL**: `http://localhost:8100` (开发环境)

> 🆕 **V2.0 更新**: 新增统一多智能体架构 `/v2/sessions` 端点，返回统一的 `AgentResponse` 格式。

> ⚠️ **重要**: 本文档是前后端接口的**单一真相源**。所有接口定义、字段类型、枚举值必须以本文档为准。

---

## 目录

1. [通用规范](#通用规范)
2. [数据类型约定](#数据类型约定)
3. [认证接口](#认证接口)
4. [会话接口](#会话接口)
5. [**V2 统一会话接口 (新)**](#v2-统一会话接口)
6. [病历事件接口](#病历事件接口)
7. [AI 算法接口](#ai-算法接口)
8. [错误处理](#错误处理)

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
  "should_show_dossier_prompt": false,
  "advice_history": [
    {
      "id": "adv-001",
      "title": "初步护理建议",
      "content": "建议保持皮肤清洁干燥，避免抓挠",
      "evidence": ["湿疹护理指南"],
      "timestamp": "2026-01-15T10:31:00Z"
    }
  ],
  "diagnosis_card": {
    "summary": "手臂出现红疹伴瘙痒",
    "conditions": [
      {
        "name": "湿疹",
        "confidence": 0.8,
        "rationale": ["红疹", "瘙痒", "对称分布"]
      }
    ],
    "risk_level": "low",
    "need_offline_visit": false,
    "urgency": null,
    "care_plan": ["保持清洁", "避免刺激"],
    "references": [
      {
        "id": "ref-001",
        "title": "湿疹诊疗指南",
        "snippet": "湿疹是一种常见皮肤炎症...",
        "source": "中华皮肤科杂志"
      }
    ],
    "reasoning_steps": ["收集症状", "检索知识库", "生成诊断"]
  },
  "knowledge_refs": [
    {
      "id": "kb-001",
      "title": "湿疹诊疗指南",
      "snippet": "湿疹是一种常见的皮肤炎症...",
      "source": "中华皮肤科杂志"
    }
  ],
  "reasoning_steps": ["分析症状", "匹配知识库", "生成建议"]
}
```

#### 诊断展示增强字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `advice_history` | `Array<AdviceEntry>?` | 中间建议历史列表 |
| `diagnosis_card` | `DiagnosisCard?` | 结构化诊断卡 |
| `knowledge_refs` | `Array<KnowledgeRef>?` | 知识库引用列表 |
| `reasoning_steps` | `Array<String>?` | 推理步骤列表 |

##### AdviceEntry
```typescript
interface AdviceEntry {
  id: string;
  title: string;
  content: string;
  evidence: string[];
  timestamp: string;  // ISO 8601
}
```

##### DiagnosisCard
```typescript
interface DiagnosisCard {
  summary: string;
  conditions: DiagnosisCondition[];
  risk_level: "low" | "medium" | "high" | "emergency";
  need_offline_visit: boolean;
  urgency?: string;
  care_plan: string[];
  references: KnowledgeRef[];
  reasoning_steps: string[];
}
```

##### DiagnosisCondition
```typescript
interface DiagnosisCondition {
  name: string;
  confidence: number;  // 0-1
  rationale: string[];
}
```

##### KnowledgeRef
```typescript
interface KnowledgeRef {
  id: string;
  title: string;
  snippet: string;
  source?: string;
  link?: string;
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

## V2 统一会话接口

> 🆕 **新架构**: V2 接口使用统一的 `AgentResponse` 响应格式，支持多智能体扩展。

### 1. 创建会话 V2

```http
POST /v2/sessions
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
  "agent_type": "dermatology",
  "doctor_name": "AI皮肤科医生",
  "status": "active",
  "created_at": "2026-01-17T10:30:00Z"
}
```

### 2. 发送消息 V2 (统一响应格式)

```http
POST /v2/sessions/{session_id}/messages
Content-Type: application/json
Accept: text/event-stream
```

**请求体**:
```json
{
  "content": "我手臂有红疹，很痒",
  "attachments": [],
  "action": "conversation"
}
```

**SSE 响应流**:
```
event: meta
data: {"session_id": "xxx", "agent_type": "dermatology"}

event: chunk
data: {"text": "根据您的描述"}

event: chunk
data: {"text": "，可能是湿疹"}

event: complete
data: <AgentResponse JSON>
```

### 3. AgentResponse 统一响应格式

```typescript
interface AgentResponse {
  // 基础字段（必填）
  message: string;           // AI 回复内容
  stage: string;             // 当前阶段: greeting | collecting | analyzing | diagnosing | completed
  progress: number;          // 进度百分比 0-100
  
  // 可选字段
  quick_options: string[];   // 快捷回复选项
  risk_level?: string;       // 风险等级: low | medium | high | emergency
  
  // 病历事件相关
  event_id?: string;         // 病历事件ID
  is_new_event: boolean;     // 是否创建新事件
  should_show_dossier_prompt: boolean;  // 是否提示生成病历
  
  // 专科扩展数据
  specialty_data?: {
    diagnosis_card?: DiagnosisCardV2;
    symptoms?: string[];
    [key: string]: any;
  };
  
  // 状态持久化
  next_state: object;        // 下次调用需要的状态
}
```

### 4. 获取智能体列表 V2

```http
GET /v2/sessions/agents
```

**响应**:
```json
{
  "general": {
    "display_name": "全科AI医生",
    "description": "通用医疗咨询",
    "actions": ["conversation"],
    "accepts_media": []
  },
  "dermatology": {
    "display_name": "皮肤科AI医生",
    "description": "专业的皮肤科问诊智能体",
    "actions": ["conversation", "analyze_skin", "interpret_report"],
    "accepts_media": ["image/jpeg", "image/png", "application/pdf"]
  }
}
```

### 5. 获取智能体能力 V2

```http
GET /v2/sessions/agents/{agent_type}/capabilities
```

**响应**:
```json
{
  "display_name": "皮肤科AI医生",
  "description": "专业的皮肤科问诊智能体",
  "actions": ["conversation", "analyze_skin", "interpret_report"],
  "accepts_media": ["image/jpeg", "image/png", "application/pdf"]
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

**错误响应** (400 Bad Request):
```json
{
  "detail": "会话信息不完整: 尚未明确主诉、尚未收集到症状信息。请继续对话后再生成病历。"
}
```

**可能的验证错误**:
- `尚未明确主诉` - chief_complaint 为空
- `尚未收集到症状信息` - symptoms 数组为空
- `对话刚开始，请先描述您的问题` - stage 为 "greeting"
- `对话信息太少，请继续描述症状` - 消息数少于3条且 stage 为 "collecting"

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

### V1.1 (2026-01-16)
- 新增诊断展示增强字段：`advice_history`, `diagnosis_card`, `knowledge_refs`, `reasoning_steps`
- 新增数据类型：`AdviceEntry`, `DiagnosisCard`, `DiagnosisCondition`, `KnowledgeRef`
- 新增皮肤科知识检索工具和结构化诊断输出

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
