# AI 算法服务 API 文档

## 概述

本文档描述病历资料夹系统中 AI 算法服务的 API 接口。

**Base URL**: `/api/ai`

**认证**: 所有接口需要 Bearer Token 认证

---

## 1. AI 摘要接口

### 1.1 生成 AI 摘要

生成病历事件的 AI 摘要和结构化分析。

```
POST /ai/summary
```

**请求体**:
```json
{
    "event_id": "uuid-string",
    "force_regenerate": false
}
```

**响应**:
```json
{
    "event_id": "uuid-string",
    "summary": "患者主诉头痛2天，伴有轻微恶心...",
    "key_points": ["持续性头痛", "伴有恶心", "无发热"],
    "symptoms": ["头痛", "恶心"],
    "symptom_details": {
        "头痛": {
            "duration": "2天",
            "severity": "中度",
            "location": "太阳穴"
        }
    },
    "possible_diagnosis": ["紧张性头痛", "偏头痛"],
    "risk_level": "low",
    "risk_warning": null,
    "recommendations": ["注意休息", "避免强光刺激"],
    "follow_up_reminders": ["3天后复诊"],
    "timeline": [
        {"time": "2026-01-12", "event": "症状开始", "type": "symptom_onset"}
    ],
    "confidence": 0.85,
    "message": "摘要生成成功"
}
```

### 1.2 获取 AI 摘要

获取已生成的 AI 摘要。

```
GET /ai/summary/{event_id}
```

---

## 2. 智能聚合接口

### 2.1 分析事件关联性

分析两个病历事件是否属于同一病情。

```
POST /ai/analyze-relation
```

**请求体**:
```json
{
    "event_id_a": "uuid-string-1",
    "event_id_b": "uuid-string-2"
}
```

**响应**:
```json
{
    "is_related": true,
    "relation_type": "same_condition",
    "confidence": 0.92,
    "reasoning": "两个事件都是关于皮肤红疹，时间间隔2天，属于同一病情的发展",
    "should_merge": true,
    "merge_suggestion": "建议合并为一个病历事件"
}
```

**relation_type 枚举**:
- `same_condition`: 同一病情
- `follow_up`: 随访/复诊
- `complication`: 并发症
- `unrelated`: 不相关

### 2.2 智能聚合分析

判断新会话应归入哪个现有事件或创建新事件。

```
POST /ai/smart-aggregate
```

**请求体**:
```json
{
    "session_id": "session-uuid",
    "session_type": "derma",
    "department": "皮肤科",
    "chief_complaint": "皮肤红疹"
}
```

**响应**:
```json
{
    "action": "add_to_existing",
    "target_event_id": "event-uuid",
    "confidence": 0.95,
    "reasoning": "同一天同一科室的问诊，自动归入现有事件",
    "should_merge": true
}
```

### 2.3 查找相关事件

从用户的所有事件中找出与目标事件相关的病历。

```
POST /ai/find-related
```

**请求体**:
```json
{
    "event_id": "target-event-uuid",
    "max_results": 5
}
```

**响应**:
```json
{
    "target_event_id": "target-event-uuid",
    "related_events": [
        {
            "event_id": "related-event-uuid",
            "relation_type": "follow_up",
            "confidence": 0.88,
            "reasoning": "7天前的同科室问诊，症状相似"
        }
    ]
}
```

### 2.4 合并事件

将多个相关事件合并为一个。

```
POST /ai/merge-events
```

**请求体**:
```json
{
    "event_ids": ["event-uuid-1", "event-uuid-2"],
    "new_title": "皮肤红疹治疗记录"
}
```

**响应**:
```json
{
    "merged_event_id": "merged-event-uuid",
    "merged_title": "皮肤红疹治疗记录",
    "summary": "患者1月10日首次出现皮肤红疹，经过3天治疗...",
    "disease_progression": "红疹从局部扩散到全身，用药后逐渐缓解",
    "current_status": "症状缓解中",
    "overall_risk_level": "medium",
    "recommendations": ["继续用药", "避免接触过敏原"],
    "message": "成功合并 2 个事件"
}
```

---

## 3. 语音转写接口

### 3.1 转写音频（URL/Base64）

将语音录音转换为文本。

```
POST /ai/transcribe
```

**请求体**:
```json
{
    "audio_url": "https://example.com/audio.mp3",
    "language": "zh",
    "extract_symptoms": true
}
```

或使用 Base64:
```json
{
    "audio_base64": "SGVsbG8gV29ybGQ=...",
    "language": "zh",
    "extract_symptoms": true
}
```

**响应**:
```json
{
    "task_id": "task-uuid",
    "status": "completed",
    "text": "我最近头痛得厉害，已经持续3天了，还有点恶心。",
    "duration": 5.2,
    "confidence": 0.92,
    "segments": [
        {
            "start_time": 0.0,
            "end_time": 2.5,
            "text": "我最近头痛得厉害",
            "confidence": 0.95
        }
    ],
    "extracted_symptoms": ["头痛", "恶心"],
    "language": "zh",
    "error_message": null
}
```

### 3.2 上传音频文件转写

```
POST /ai/transcribe/upload
Content-Type: multipart/form-data
```

**表单参数**:
- `file`: 音频文件（支持 mp3, wav, m4a, aac, ogg, flac, webm）
- `language`: 语言代码（默认 "zh"）
- `extract_symptoms`: 是否提取症状（默认 true）

### 3.3 获取转写状态

```
GET /ai/transcribe/{task_id}
```

**响应**:
```json
{
    "task_id": "task-uuid",
    "status": "completed",
    "text": "转写文本...",
    "error_message": null
}
```

**status 枚举**:
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 完成
- `failed`: 失败

---

## 4. 错误响应

所有接口的错误响应格式：

```json
{
    "detail": "错误描述信息"
}
```

**常见错误码**:
- `400`: 请求参数错误
- `401`: 未认证或认证过期
- `403`: 无权访问
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 5. 使用示例

### Python 示例

```python
import httpx

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# 生成 AI 摘要
async def generate_summary(event_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ai/summary",
            headers=headers,
            json={"event_id": event_id, "force_regenerate": False}
        )
        return response.json()

# 智能聚合
async def smart_aggregate(session_id: str, department: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ai/smart-aggregate",
            headers=headers,
            json={
                "session_id": session_id,
                "session_type": "diagnosis",
                "department": department
            }
        )
        return response.json()

# 语音转写
async def transcribe(audio_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ai/transcribe",
            headers=headers,
            json={"audio_url": audio_url, "language": "zh"}
        )
        return response.json()
```

### cURL 示例

```bash
# 生成 AI 摘要
curl -X POST "http://localhost:8000/api/ai/summary" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "your-event-id", "force_regenerate": false}'

# 语音转写（文件上传）
curl -X POST "http://localhost:8000/api/ai/transcribe/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/audio.mp3" \
  -F "language=zh"
```

---

## 6. 性能说明

| 接口 | 预期响应时间 | 备注 |
|------|-------------|------|
| AI 摘要 | 2-5秒 | 首次生成较慢，有缓存 |
| 关联分析 | 1-3秒 | 规则匹配更快 |
| 智能聚合 | 0.5-2秒 | 同天同科室秒级响应 |
| 语音转写 | 视音频长度 | 约 1秒/分钟音频 |

---

**文档版本**: V1.0  
**更新日期**: 2026-01-14
