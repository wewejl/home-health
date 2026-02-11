# API 文档

## 概述

### 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `http://localhost:8100` |
| **API 版本** | v1（兼容保留）, v2（推荐使用） |
| **认证方式** | JWT Bearer Token |
| **数据格式** | JSON |
| **字符编码** | UTF-8 |

> **v2 API 推荐**：V2 API 提供了统一的响应格式（AgentResponse）和完整的端点支持，是新开发的推荐版本。V1 API 保留用于兼容性。

### 认证方式

#### 用户认证

用户端 API 使用 JWT Token 认证：

```http
Authorization: Bearer <access_token>
```

**获取 Token 方式：**

1. 短信验证码登录：`POST /auth/login`
2. 密码登录：`POST /auth/login-password`
3. 刷新 Token：`POST /auth/refresh`

#### 管理员认证

管理后台 API 使用独立的 JWT 密钥：

```http
Authorization: Bearer <admin_access_token>
```

**获取 Token 方式：** `POST /admin/auth/login`

### 测试模式

后端支持测试模式，可在测试环境跳过部分验证：

- **验证码**: `000000` 为万能验证码
- **Token 验证**: 部分接口可跳过认证
- **数据隔离**: 测试模式下可查看所有数据

---

## 用户端 API

### 认证相关 (`/auth`)

#### 发送验证码

```http
POST /auth/send-code
```

**请求体：**
```json
{
  "phone": "13800138000"
}
```

**响应：**
```json
{
  "message": "验证码已发送",
  "expires_in": 300
}
```

**防刷策略：**
- 同一手机号 60 秒内只能发送一次
- 同一手机号每小时最多 10 次
- 同一 IP 每小时最多 30 次
- 全局速率限制: 每分钟 5 次

#### 验证码登录

```http
POST /auth/login
```

**请求体：**
```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

**响应：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "phone": "13800138000",
    "nickname": "用户",
    "avatar_url": null,
    "is_profile_completed": false
  },
  "is_new_user": true
}
```

#### 刷新 Token

```http
POST /auth/refresh
```

**请求体：**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 获取当前用户信息

```http
GET /auth/me
Authorization: Bearer <token>
```

#### 更新用户资料

```http
PUT /auth/profile
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "nickname": "张三",
  "avatar_url": "https://example.com/avatar.jpg",
  "gender": "male",
  "birthday": "1990-01-01",
  "emergency_contact_name": "李四",
  "emergency_contact_phone": "13900139000",
  "emergency_contact_relation": "配偶"
}
```

#### 密码登录

```http
POST /auth/login-password
```

**请求体：**
```json
{
  "phone": "13800138000",
  "password": "password123"
}
```

#### 重置密码

```http
POST /auth/password/reset
```

**请求体：**
```json
{
  "phone": "13800138000",
  "code": "123456",
  "new_password": "newpass123"
}
```

---

### 会话管理 (`/sessions`, `/v2/sessions`)

> **注意**：V2 API 是当前推荐使用的版本，新增了完整的端点支持和统一响应格式。

#### V2 创建会话

```http
POST /v2/sessions
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "doctor_id": 1,
  "agent_type": "general"
}
```

**支持的智能体类型：**
- `general` - 全科
- `dermatology` - 皮肤科
- `cardiology` - 心血管科
- `orthopedics` - 骨科

**响应（统一格式）：**
```json
{
  "session_id": "uuid-string",
  "doctor_id": 1,
  "doctor_name": "AI助手",
  "agent_type": "general",
  "last_message": null,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### V2 获取会话列表（新增）

```http
GET /v2/sessions
Authorization: Bearer <token>
```

**响应：** 返回当前用户的所有会话列表

#### V2 获取会话消息（新增）

```http
GET /v2/sessions/{session_id}/messages?limit=20&before=100
Authorization: Bearer <token>
```

**响应：**
```json
{
  "messages": [...],
  "has_more": true
}
```

#### V2 发送消息（流式）

```http
POST /v2/sessions/{session_id}/messages
Authorization: Bearer <token>
Accept: text/event-stream
```

**请求体：**
```json
{
  "content": "你好，我头疼",
  "attachments": [
    {
      "type": "image",
      "base64": "data:image/jpeg;base64,..."
    }
  ],
  "action": "conversation"
}
```

**V2 SSE 响应流（统一 AgentResponse 格式）：**
```
event: meta
data: {"session_id": "uuid", "agent_type": "general"}

event: chunk
data: {"text": "你好"}

event: complete
data: {
  "message": "完整响应文本",
  "stage": "completed",
  "progress": 100,
  "quick_options": [...],
  "specialty_data": {...},
  "next_state": {...},
  "event_id": "...",
  "is_new_event": false,
  "should_show_dossier_prompt": false
}
```

#### V2 获取智能体列表

```http
GET /v2/sessions/agents
```

#### V2 获取智能体能力

```http
GET /v2/sessions/agents/{agent_type}/capabilities
```

---

#### V1 创建会话（保留兼容）

```http
POST /sessions
Authorization: Bearer <token>
```

#### V1 获取会话列表（保留兼容）

```http
GET /sessions
Authorization: Bearer <token>
```

#### V1 获取会话消息（保留兼容）

```http
GET /sessions/{session_id}/messages?limit=20
Authorization: Bearer <token>
```

---

### AI 服务 (`/ai`)

#### 生成 AI 摘要

```http
POST /ai/summary
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "event_id": "1",
  "force_regenerate": false
}
```

**响应：**
```json
{
  "event_id": "1",
  "summary": "患者主诉头痛，伴随恶心...",
  "key_points": ["头痛3天", "伴随恶心", "无发热"],
  "symptoms": ["头痛", "恶心"],
  "symptom_details": {...},
  "possible_diagnosis": ["偏头痛", "紧张性头痛"],
  "risk_level": "low",
  "risk_warning": null,
  "recommendations": ["休息", "避免强光刺激"],
  "follow_up_reminders": ["观察症状变化"],
  "timeline": [...],
  "confidence": 0.85,
  "message": "摘要生成成功"
}
```

#### 分析事件关联性

```http
POST /ai/analyze-relation
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "event_id_a": "1",
  "event_id_b": "2"
}
```

#### 智能聚合分析

```http
POST /ai/smart-aggregate
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "session_id": "uuid",
  "session_type": "derma",
  "department": "皮肤科",
  "chief_complaint": "皮疹"
}
```

#### 合并事件

```http
POST /ai/merge-events
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "event_ids": ["1", "2", "3"],
  "new_title": "连续就医记录"
}
```

#### 语音转写

```http
POST /ai/transcribe
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "audio_url": "https://example.com/audio.wav",
  "audio_base64": "base64_encoded_audio_data",
  "language": "zh",
  "extract_symptoms": true
}
```

**响应：**
```json
{
  "task_id": "task_uuid",
  "status": "completed",
  "text": "转写文本内容",
  "duration": 15.5,
  "confidence": 0.95,
  "segments": [...],
  "extracted_symptoms": ["头痛", "恶心"],
  "language": "zh"
}
```

#### 上传音频转写

```http
POST /ai/transcribe/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**表单参数：**
- `file`: 音频文件
- `language`: 语言 (默认: zh)
- `extract_symptoms`: 是否提取症状 (默认: true)

---

### 语音服务 (`/ws/voice`)

#### ASR 语音识别 (WebSocket)

```
ws://localhost:8100/ws/voice/asr?token=<access_token>&language=auto
```

**支持的语言：**
- `auto` - 自动检测
- `zh` - 中文
- `en` - 英文
- `yue` - 粤语
- `sichuanese` - 四川话
- `ja` - 日语
- `ko` - 韩语

**客户端 → 服务端：**
```json
{"action": "start", "format": "m4a"}
// 二进制音频数据
{"action": "finish"}
```

**服务端 → 客户端：**
```json
{"event": "asr_ready", "task_id": "xxx"}
{"event": "asr_partial", "text": "中间结果"}
{"event": "asr_final", "text": "最终结果", "language": "zh", "confidence": 0.95}
{"event": "error", "message": "错误信息"}
```

#### 获取语音服务状态

```http
GET /ws/voice/status
```

**响应：**
```json
{
  "service": "voice_asr",
  "provider": "glm",
  "asr_connections": 2,
  "glm_configured": true,
  "endpoints": {
    "asr": "/ws/voice/asr"
  },
  "config": {
    "asr_sample_rate": 16000,
    "asr_format": "pcm",
    "glm_asr_model": "glm-asr-2512",
    "supported_languages": ["auto", "zh", "en", "yue", "sichuanese", "ja", "ko"]
  }
}
```

---

### 科室与医生 (`/departments`)

#### 获取科室列表

```http
GET /departments?primary_only=false
```

**查询参数：**
- `primary_only` - 只返回主要科室（问医生页面使用）

**响应：**
```json
[
  {
    "id": 1,
    "name": "皮肤科",
    "icon": "dermatology",
    "sort_order": 1,
    "is_primary": true
  }
]
```

#### 获取科室医生列表

```http
GET /departments/{department_id}/doctors
Authorization: Bearer <token>
```

---

### 疾病查询 (`/diseases`)

#### 获取疾病列表

```http
GET /diseases?department_id=1&is_hot=true
```

**查询参数：**
- `department_id` - 按科室筛选
- `is_hot` - 只返回热门疾病

#### 搜索疾病

```http
GET /diseases/search?q=感冒&department_id=1&limit=20&offset=0
```

**响应：**
```json
{
  "total": 42,
  "items": [...]
}
```

#### 获取热门疾病

```http
GET /diseases/hot?department_id=1&limit=10
```

#### 获取科室及疾病

```http
GET /diseases/departments-with-diseases?limit=100
```

#### 获取疾病详情

```http
GET /diseases/{disease_id}
```

#### 获取疾病详情（MedLive 格式）

```http
GET /diseases/{disease_id}/medlive
```

#### 通过 Wiki ID 获取疾病

```http
GET /diseases/wiki-id/{wiki_id}
```

---

### 药品查询 (`/drugs`)

#### 获取药品分类及热门药品

```http
GET /drugs/categories?limit=10
```

**响应：**
```json
[
  {
    "id": 1,
    "name": "感冒药",
    "icon": "cold",
    "display_type": "grid",
    "drugs": [...]
  }
]
```

#### 获取热门药品

```http
GET /drugs/hot?limit=20&category_id=1
```

#### 搜索药品

```http
GET /drugs/search?q=阿莫西林&category_id=1&limit=20&offset=0
```

**响应：**
```json
{
  "total": 15,
  "items": [...]
}
```

#### 获取药品详情

```http
GET /drugs/{drug_id}
```

---

### 医疗事件 (`/medical-events`)

#### 创建医疗事件

```http
POST /medical-events
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "title": "皮肤问题",
  "department": "皮肤科",
  "agent_type": "derma",
  "chief_complaint": "面部起红疹",
  "risk_level": "low"
}
```

#### 获取医疗事件列表

```http
GET /medical-events?keyword=头痛&department=皮肤科&status=active&page=1&page_size=20
Authorization: Bearer <token>
```

**查询参数：**
- `keyword` - 搜索关键词
- `department` - 科室筛选
- `agent_type` - 智能体类型
- `status` - 状态筛选 (active/archived)
- `risk_level` - 风险等级 (low/medium/high/emergency)
- `start_date` / `end_date` - 日期范围
- `page` / `page_size` - 分页
- `sort_by` - 排序字段 (created_at/updated_at/start_time)
- `sort_order` - 排序方向 (asc/desc)

**响应：**
```json
{
  "events": [...],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

#### 获取医疗事件详情

```http
GET /medical-events/{event_id}
Authorization: Bearer <token>
```

#### 更新医疗事件

```http
PUT /medical-events/{event_id}
Authorization: Bearer <token>
```

#### 删除医疗事件

```http
DELETE /medical-events/{event_id}?confirm=true
Authorization: Bearer <token>
```

#### 归档医疗事件

```http
POST /medical-events/{event_id}/archive
Authorization: Bearer <token>
```

#### 聚合会话到医疗事件

```http
POST /medical-events/aggregate
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "session_id": "uuid",
  "session_type": "derma"
}
```

#### 生成事件摘要

```http
POST /medical-events/{event_id}/generate-summary?force_regenerate=false
Authorization: Bearer <token>
```

#### 添加附件

```http
POST /medical-events/{event_id}/attachments
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "type": "image",
  "url": "https://example.com/image.jpg",
  "thumbnail_url": "https://example.com/thumb.jpg",
  "filename": "photo.jpg",
  "file_size": 102400,
  "mime_type": "image/jpeg",
  "metadata": {},
  "description": "皮肤照片"
}
```

#### 删除附件

```http
DELETE /medical-events/{event_id}/attachments/{attachment_id}
Authorization: Bearer <token>
```

#### 添加备注

```http
POST /medical-events/{event_id}/notes
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "content": "患者反馈症状有所缓解",
  "is_important": true
}
```

#### 更新/删除备注

```http
PUT /medical-events/{event_id}/notes/{note_id}
DELETE /medical-events/{event_id}/notes/{note_id}
Authorization: Bearer <token>
```

#### 创建导出

```http
POST /medical-events/export
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "event_ids": ["1", "2"],
  "export_type": "share_link",
  "share_password": "123456",
  "expires_in_days": 7,
  "max_views": 10
}
```

#### 获取导出记录

```http
GET /medical-events/exports
Authorization: Bearer <token>
```

#### 访问共享链接（无需登录）

```http
GET /medical-events/share/{token}?password=123456
```

---

### 医嘱管理 (`/medical-orders`)

#### 创建医嘱

```http
POST /medical-orders
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "title": "每日测量血压",
  "order_type": "medication",
  "instructions": "每天早晚各测量一次",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "frequency": "daily",
  "tasks": [
    {
      "title": "测量血压",
      "scheduled_time": "08:00",
      "type": "measurement",
      "value_config": {"type": "blood_pressure"}
    }
  ]
}
```

#### 获取医嘱列表

```http
GET /medical-orders?status=active
Authorization: Bearer <token>
```

#### 获取医嘱详情

```http
GET /medical-orders/{order_id}
Authorization: Bearer <token>
```

#### 更新医嘱

```http
PUT /medical-orders/{order_id}
Authorization: Bearer <token>
```

#### 激活医嘱

```http
POST /medical-orders/{order_id}/activate
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "confirm": true
}
```

#### 获取指定日期的任务

```http
GET /medical-orders/tasks/{task_date}
Authorization: Bearer <token>
```

**日期格式：** `YYYY-MM-DD`

**响应：**
```json
{
  "date": "2024-01-01",
  "pending": [...],
  "completed": [...],
  "overdue": [...],
  "summary": {
    "date": "2024-01-01",
    "total": 5,
    "completed": 3,
    "overdue": 1,
    "pending": 1,
    "rate": 0.6
  }
}
```

#### 完成任务打卡

```http
POST /medical-orders/tasks/{task_id}/complete
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "completion_type": "value",
  "value": {"type": "blood_pressure", "systolic": 120, "diastolic": 80},
  "photo_url": null,
  "notes": "血压正常"
}
```

**打卡类型：**
- `check` - 简单打卡确认
- `photo` - 照片证明
- `value` - 数值录入
- `medication` - 用药记录

#### 获取依从性数据

```http
GET /medical-orders/compliance/daily?task_date=2024-01-01
GET /medical-orders/compliance/weekly
GET /medical-orders/compliance/order/{order_id}
GET /medical-orders/compliance/abnormal?days=30
Authorization: Bearer <token>
```

#### 家属关系管理

```http
POST /medical-orders/family-bonds
GET /medical-orders/family-bonds
DELETE /medical-orders/family-bonds/{bond_id}
Authorization: Bearer <token>
```

**创建家属关系请求体：**
```json
{
  "patient_id": 1,
  "family_member_phone": "13900139000",
  "relationship": "配偶",
  "notification_level": "all"
}
```

#### 预警管理

```http
GET /medical-orders/alerts?active_only=true&limit=50
POST /medical-orders/alerts/{alert_id}/acknowledge
POST /medical-orders/alerts/check
Authorization: Bearer <token>
```

---

### 远程查房 (`/rounding`)

#### 获取患者列表

```http
GET /rounding/patients?active_only=true
Authorization: Bearer <token>
```

**响应：**
```json
{
  "patients": [...],
  "stats": {
    "total": 20,
    "abnormal": 3,
    "high_risk": 5
  }
}
```

#### 获取患者详情

```http
GET /rounding/patients/{patient_id}
Authorization: Bearer <token>
```

**响应：**
```json
{
  "id": 1,
  "name": "张三",
  "nickname": "老张",
  "avatar": "https://example.com/avatar.jpg",
  "condition": "慢病",
  "last_seen": "2小时前",
  "last_consultation": "1天前",
  "alerts": [...],
  "total_tasks": 5,
  "completed_tasks": 3,
  "completion_rate": 60,
  "recent_messages": [...],
  "today_tasks": [...],
  "compliance_rate": 75,
  "daily_compliance": [...]
}
```

#### 获取异常患者

```http
GET /rounding/patients/abnormal
Authorization: Bearer <token>
```

#### 获取统计数据

```http
GET /rounding/stats
Authorization: Bearer <token>
```

---

### 反馈 (`/sessions`)

#### 创建会话反馈

```http
POST /sessions/{session_id}/feedback
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "message_id": 123,
  "rating": 5,
  "feedback_type": "helpful",
  "feedback_text": "很有帮助"
}
```

#### 创建消息反馈

```http
POST /sessions/messages/{message_id}/feedback
Authorization: Bearer <token>
```

---

### 病历夹管理 (`/medical-folders`)

#### 创建病历夹

```http
POST /medical-folders
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "皮肤科病历",
  "description": "存放皮肤科相关病历",
  "color": "#7B5FEA",
  "icon": "folder",
  "sort_order": 1
}
```

**响应：**
```json
{
  "id": "uuid-string",
  "user_id": 1,
  "name": "皮肤科病历",
  "description": "存放皮肤科相关病历",
  "color": "#7B5FEA",
  "icon": "folder",
  "sort_order": 1,
  "record_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 获取病历夹列表

```http
GET /medical-folders
Authorization: Bearer <token>
```

#### 获取病历夹详情

```http
GET /medical-folders/{folder_id}
Authorization: Bearer <token>
```

#### 更新病历夹

```http
PUT /medical-folders/{folder_id}
Authorization: Bearer <token>
```

#### 删除病历夹

```http
DELETE /medical-folders/{folder_id}
Authorization: Bearer <token>
```

---

### 病历记录管理 (`/medical-records`)

#### 创建病历记录

```http
POST /medical-records
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "folder_id": "uuid-string",
  "title": "皮肤过敏记录",
  "record_date": "2024-01-01",
  "description": "患者出现皮肤过敏症状"
}
```

**响应：**
```json
{
  "id": "uuid-string",
  "folder_id": "uuid-string",
  "user_id": 1,
  "title": "皮肤过敏记录",
  "record_date": "2024-01-01",
  "description": "患者出现皮肤过敏症状",
  "file_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 获取病历记录列表

```http
GET /medical-records?folder_id={folder_id}
Authorization: Bearer <token>
```

#### 获取病历记录详情

```http
GET /medical-records/{record_id}
Authorization: Bearer <token>
```

#### 更新病历记录

```http
PUT /medical-records/{record_id}
Authorization: Bearer <token>
```

#### 删除病历记录

```http
DELETE /medical-records/{record_id}
Authorization: Bearer <token>
```

---

### 医疗文件管理 (`/medical-files`)

#### 上传文件

```http
POST /medical-files
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**表单参数：**
- `file`: 文件（支持图片、PDF、视频、音频、文档）
- `record_id`: 病历记录 ID
- `description`: 文件描述（可选）

**支持的文件类型：**
- 图片：`.jpg`, `.jpeg`, `.png`, `.gif`, `.heic`, `.webp`
- PDF：`.pdf`
- 视频：`.mp4`, `.mov`, `.avi`, `.mkv`
- 音频：`.mp3`, `.m4a`, `.wav`, `.aac`
- 文档：`.doc`, `.docx`, `.txt`, `.xls`, `.xlsx`

**响应：**
```json
{
  "id": "uuid-string",
  "record_id": "uuid-string",
  "file_name": "photo.jpg",
  "file_type": "image",
  "file_size": 102400,
  "url": "/static/uploads/medical_files/1/record/photo.jpg",
  "thumbnail_url": "/static/uploads/medical_files/1/record/.thumbnails/photo.jpg",
  "description": "皮肤照片",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 获取文件列表

```http
GET /medical-files?record_id={record_id}
Authorization: Bearer <token>
```

#### 获取文件详情

```http
GET /medical-files/{file_id}
Authorization: Bearer <token>
```

#### 重命名文件

```http
PUT /medical-files/{file_id}
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "file_name": "new_name.jpg"
}
```

#### 删除文件

```http
DELETE /medical-files/{file_id}
Authorization: Bearer <token>
```

---

### 健康检查端点

#### 基础健康检查

```http
GET /
```

**响应：**
```json
{
  "message": "灵犀健康 AI分身系统 API 服务运行中",
  "version": "2.0.0"
}
```

#### 详细健康检查

```http
GET /health/detailed
```

**响应：**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0",
  "checks": {
    "database": {"status": "healthy"},
    "llm": {"status": "configured", "provider": "qwen"}
  },
  "environment": {
    "debug": true,
    "test_mode": true,
    "production": false
  },
  "response_time_ms": 45.2
}
```

#### 就绪检查

```http
GET /health/ready
```

用于 Kubernetes 等容器编排系统。

#### 存活检查

```http
GET /health/live
```

用于 Kubernetes 等容器编排系统。

---

## 医生工作台 API

> 医生工作台 API 需要医生角色认证，使用前缀 `/api/doctor`

### 医生信息 (`/api/doctor`)

#### 获取当前医生信息

```http
GET /api/doctor/me
Authorization: Bearer <doctor_token>
```

**响应：**
```json
{
  "id": 1,
  "username": "doctor001",
  "email": "doctor@example.com",
  "role": "doctor",
  "department_id": 1,
  "department_name": "皮肤科",
  "managed_doctors": [
    {
      "id": 1,
      "name": "AI助手-皮肤科",
      "title": "主治医师",
      "department": "皮肤科"
    }
  ]
}
```

### 患者管理 (`/api/doctor/patients`)

#### 获取患者列表

```http
GET /api/doctor/patients?search=张三
Authorization: Bearer <doctor_token>
```

**查询参数：**
- `search` - 搜索关键词（姓名/手机号）

**响应：**
```json
[
  {
    "id": 1,
    "nickname": "张三",
    "phone": "138****1234",
    "gender": "male",
    "age": 35,
    "last_consultation_at": "2024-01-01T10:00:00Z",
    "active_orders_count": 2,
    "completion_rate": 0.85
  }
]
```

#### 获取患者详情

```http
GET /api/doctor/patients/{patient_id}
Authorization: Bearer <doctor_token>
```

**响应：**
```json
{
  "id": 1,
  "nickname": "张三",
  "phone": "138****1234",
  "gender": "male",
  "age": 35,
  "avatar_url": null,
  "is_profile_completed": true,
  "last_consultation_at": "2024-01-01T10:00:00Z",
  "active_orders_count": 2,
  "completion_rate": 0.85,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 对话记录 (`/api/doctor`)

#### 获取患者对话列表

```http
GET /api/doctor/patients/{patient_id}/consultations?limit=10
Authorization: Bearer <doctor_token>
```

**响应：**
```json
[
  {
    "id": "uuid-string",
    "user_id": 1,
    "doctor_id": 1,
    "agent_type": "derma",
    "last_message": "患者主诉皮肤瘙痒",
    "message_count": 15,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
]
```

#### 获取对话详情

```http
GET /api/doctor/consultations/{session_id}
Authorization: Bearer <doctor_token>
```

**响应：**
```json
{
  "session": {
    "id": "uuid-string",
    "user_id": 1,
    "doctor_id": 1,
    "agent_type": "derma",
    "last_message": "患者主诉皮肤瘙痒",
    "message_count": 15,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "messages": [
    {
      "id": 1,
      "sender": "user",
      "content": "你好，我最近皮肤有点痒",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 医嘱管理 (`/api/doctor`)

#### 创建医嘱

```http
POST /api/doctor/orders
Authorization: Bearer <doctor_token>
```

**请求体：**
```json
{
  "patient_id": 1,
  "title": "每日测量血压",
  "order_type": "medication",
  "description": "每天早晚各测量一次血压",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "frequency": "daily"
}
```

#### 获取患者医嘱列表

```http
GET /api/doctor/patients/{patient_id}/orders?status_filter=active
Authorization: Bearer <doctor_token>
```

**查询参数：**
- `status_filter` - 状态筛选 (draft/active/stopped/completed)

#### 更新医嘱

```http
PUT /api/doctor/orders/{order_id}
Authorization: Bearer <doctor_token>
```

**请求体：**
```json
{
  "title": "更新后的医嘱标题",
  "description": "更新后的描述",
  "end_date": "2024-02-01"
}
```

#### 停用医嘱

```http
DELETE /api/doctor/orders/{order_id}
Authorization: Bearer <doctor_token>
```

### 任务执行情况 (`/api/doctor`)

#### 获取患者指定日期的任务

```http
GET /api/doctor/patients/{patient_id}/tasks?task_date=2024-01-01
Authorization: Bearer <doctor_token>
```

**响应：**
```json
{
  "date": "2024-01-01",
  "pending": [...],
  "completed": [...],
  "overdue": [...],
  "summary": {
    "date": "2024-01-01",
    "total": 5,
    "completed": 3,
    "overdue": 1,
    "pending": 1,
    "rate": 0.6
  }
}
```

---

## 管理后台 API

### 管理员认证 (`/admin/auth`)

#### 管理员登录

```http
POST /admin/auth/login
```

**请求体：**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  }
}
```

#### 获取当前管理员信息

```http
GET /admin/auth/me
Authorization: Bearer <admin_token>
```

#### 管理员登出

```http
POST /admin/auth/logout
Authorization: Bearer <admin_token>
```

#### 创建管理员用户

```http
POST /admin/auth/users
Authorization: Bearer <admin_token>
```

**请求体：**
```json
{
  "username": "editor",
  "password": "editor123",
  "email": "editor@example.com",
  "role": "editor"
}
```

#### 获取管理员用户列表

```http
GET /admin/auth/users
Authorization: Bearer <admin_token>
```

#### 更新管理员用户

```http
PUT /admin/auth/users/{user_id}
Authorization: Bearer <admin_token>
```

---

### 疾病管理 (`/admin/diseases`)

#### 获取疾病列表

```http
GET /admin/diseases?department_id=1&is_active=true&is_hot=true&search=感冒
Authorization: Bearer <admin_token>
```

#### 获取疾病详情

```http
GET /admin/diseases/{disease_id}
Authorization: Bearer <admin_token>
```

#### 创建疾病

```http
POST /admin/diseases
Authorization: Bearer <admin_token>
```

**请求体：**
```json
{
  "name": "感冒",
  "department_id": 1,
  "recommended_department": "内科",
  "overview": "感冒是一种常见的呼吸道疾病...",
  "symptoms": "鼻塞,流涕,咳嗽",
  "causes": "病毒感染",
  "diagnosis": "根据症状诊断",
  "treatment": "休息,多喝水",
  "prevention": "注意保暖",
  "care": "保持室内通风",
  "author_name": "张医生",
  "author_title": "主治医师",
  "is_hot": true,
  "sort_order": 1,
  "is_active": true
}
```

#### 更新疾病

```http
PUT /admin/diseases/{disease_id}
Authorization: Bearer <admin_token>
```

#### 删除疾病

```http
DELETE /admin/diseases/{disease_id}
Authorization: Bearer <admin_token>
```

#### 切换热门状态

```http
PUT /admin/diseases/{disease_id}/toggle-hot?is_hot=true
Authorization: Bearer <admin_token>
```

#### 切换启用状态

```http
PUT /admin/diseases/{disease_id}/toggle-active?is_active=true
Authorization: Bearer <admin_token>
```

---

## 数据模型

### 通用响应结构

#### 成功响应

```json
{
  "data": {...}
}
```

#### 错误响应

```json
{
  "detail": "错误描述信息"
}
```

### 用户模型

```json
{
  "id": 1,
  "phone": "13800138000",
  "nickname": "用户昵称",
  "avatar_url": "https://example.com/avatar.jpg",
  "gender": "male",
  "birthday": "1990-01-01",
  "emergency_contact_name": "紧急联系人",
  "emergency_contact_phone": "13900139000",
  "emergency_contact_relation": "配偶",
  "is_profile_completed": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 会话模型

```json
{
  "session_id": "uuid-string",
  "doctor_id": 1,
  "doctor_name": "AI助手",
  "agent_type": "general",
  "last_message": "最后一条消息摘要",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 消息模型

```json
{
  "id": 123,
  "session_id": "uuid-string",
  "sender": "user",
  "content": "消息内容",
  "message_type": "text",
  "attachments": null,
  "structured_data": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## 错误码

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 200 | 成功 | 请求成功 |
| 201 | 创建成功 | 资源创建成功 |
| 204 | 无内容 | 删除成功 |
| 400 | 请求错误 | 请求参数错误或验证失败 |
| 401 | 未授权 | Token 无效或已过期 |
| 403 | 禁止访问 | 无权限访问该资源 |
| 404 | 未找到 | 资源不存在 |
| 429 | 请求过多 | 超过速率限制 |
| 500 | 服务器错误 | 服务器内部错误 |

### 常见错误响应

**Token 无效：**
```json
{
  "detail": "无效的认证凭证"
}
```

**验证码错误：**
```json
{
  "detail": "验证码错误或已过期"
}
```

**速率限制：**
```json
{
  "detail": "发送过于频繁，请稍后再试"
}
```

---

## API 文档（Swagger）

访问 `http://localhost:8100/docs` 查看自动生成的交互式 API 文档（Swagger UI）。

访问 `http://localhost:8100/redoc` 查看备用的文档格式（ReDoc）。

---

## 测试示例

### 使用 curl 测试

```bash
# 1. 发送验证码
curl -X POST http://localhost:8100/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'

# 2. 登录获取 Token
curl -X POST http://localhost:8100/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "code": "000000"}'

# 3. 使用 Token 访问受保护接口
curl -X GET http://localhost:8100/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 4. 创建会话
curl -X POST http://localhost:8100/sessions \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "general"}'

# 5. 发送消息
curl -X POST http://localhost:8100/sessions/SESSION_ID/messages \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"content": "你好，我头疼"}'
```
