# AI 算法服务设计文档

## 1. 概述

本文档描述病历资料夹系统中 AI 算法服务的设计与实现，包含三大核心功能：

1. **AI 摘要服务** - 智能生成病历摘要和结构化分析
2. **智能事件聚合** - 自动识别并聚合相关病历事件
3. **语音转写服务** - 将语音录音转换为文本

---

## 2. 技术架构

### 2.1 服务层结构

```
backend/app/services/ai/
├── __init__.py
├── base_ai_service.py      # AI 服务基类
├── summary_service.py      # AI 摘要服务
├── aggregation_service.py  # 智能事件聚合服务
├── transcription_service.py # 语音转写服务
└── prompts/
    ├── __init__.py
    ├── summary_prompts.py   # 摘要相关提示词
    └── aggregation_prompts.py # 聚合相关提示词
```

### 2.2 技术选型

| 功能 | 技术方案 | 备选方案 |
|------|----------|----------|
| AI 摘要 | 阿里千问 (qwen-plus) | GPT-4, Claude |
| 事件聚合 | 千问 + 规则引擎 | 向量相似度匹配 |
| 语音转写 | 阿里 Paraformer | Whisper, 讯飞 |

---

## 3. AI 摘要服务

### 3.1 功能描述

从病历事件的对话记录、附件、AI 分析结果中生成结构化摘要。

### 3.2 输入数据

```python
class SummaryInput:
    event_id: str
    chief_complaint: str        # 主诉
    sessions: List[dict]        # 会话记录
    attachments: List[dict]     # 附件信息
    notes: List[dict]           # 用户备注
    existing_analysis: dict     # 现有 AI 分析
```

### 3.3 输出结构

```python
class SummaryOutput:
    summary: str                    # 摘要文本（100-200字）
    key_points: List[str]           # 关键要点（3-5条）
    symptoms: List[str]             # 症状列表
    possible_diagnosis: List[str]   # 可能诊断
    risk_level: str                 # 风险等级
    recommendations: List[str]      # 建议
    follow_up_reminders: List[str]  # 随访提醒
    timeline: List[TimelineEvent]   # 时间轴事件
    confidence: float               # 置信度 0-1
```

### 3.4 核心算法

1. **信息提取**：从对话记录中提取症状、时间、严重程度
2. **结构化生成**：使用 LLM 生成结构化 JSON
3. **后处理验证**：校验输出格式，补充缺失字段

### 3.5 API 接口

```
POST /api/medical-events/{event_id}/ai-summary
GET  /api/medical-events/{event_id}/ai-summary
```

---

## 4. 智能事件聚合服务

### 4.1 功能描述

自动识别同一病情的多次对话，建议合并相关事件，生成病程演变时间轴。

### 4.2 聚合策略

#### 4.2.1 规则引擎（快速匹配）

- **时间维度**：同一天内同科室对话自动归入同一事件
- **科室维度**：7 天内同一科室的对话建议合并
- **主诉维度**：相似主诉的事件建议关联

#### 4.2.2 语义匹配（AI 驱动）

- 使用 LLM 判断两个事件是否属于同一病情
- 计算症状相似度和时间关联性
- 生成合并建议和置信度

### 4.3 聚合结果

```python
class AggregationResult:
    should_merge: bool              # 是否建议合并
    confidence: float               # 置信度
    related_events: List[str]       # 相关事件 ID
    merge_reason: str               # 合并原因
    timeline: List[TimelineEvent]   # 合并后时间轴
```

### 4.4 API 接口

```
POST /api/medical-events/smart-aggregate  # 智能聚合分析
POST /api/medical-events/merge            # 合并事件
GET  /api/medical-events/{id}/related     # 获取相关事件
```

---

## 5. 语音转写服务

### 5.1 功能描述

将用户上传的语音录音转换为文本，并提取关键症状信息。

### 5.2 技术实现

#### 5.2.1 阿里 Paraformer 方案

- 模型：paraformer-v2
- 支持：中文普通话、方言
- 特性：实时/离线转写、标点恢复

#### 5.2.2 处理流程

```
音频上传 → 格式转换 → ASR 转写 → 文本后处理 → 症状提取
```

### 5.3 输出结构

```python
class TranscriptionResult:
    text: str                       # 转写文本
    duration: float                 # 音频时长（秒）
    confidence: float               # 转写置信度
    segments: List[Segment]         # 分段时间戳
    extracted_symptoms: List[str]   # 提取的症状
    language: str                   # 识别的语言
```

### 5.4 API 接口

```
POST /api/ai/transcribe              # 语音转写
GET  /api/ai/transcribe/{task_id}    # 获取转写结果
```

---

## 6. 配置参数

```python
# .env 配置
AI_SUMMARY_MODEL=qwen-plus
AI_SUMMARY_MAX_TOKENS=2000
AI_SUMMARY_TEMPERATURE=0.3

AI_AGGREGATION_TIME_WINDOW_DAYS=7
AI_AGGREGATION_SIMILARITY_THRESHOLD=0.7

ASR_PROVIDER=aliyun
ASR_MODEL=paraformer-v2
ASR_SAMPLE_RATE=16000
```

---

## 7. 性能指标

| 指标 | 目标值 |
|------|--------|
| AI 摘要生成时间 | < 3秒 |
| 事件聚合分析时间 | < 2秒 |
| 语音转写延迟 | < 5秒/分钟音频 |
| 摘要准确率 | > 85% |
| 聚合准确率 | > 80% |
| 语音转写准确率 | > 90% |

---

## 8. 错误处理

- API 调用失败：重试 3 次，间隔指数退避
- JSON 解析失败：使用默认结构 + 原始文本
- 超时处理：异步任务 + 状态轮询
- 降级策略：AI 服务不可用时使用规则引擎

---

## 9. 安全考虑

- 敏感数据脱敏：不将真实姓名、手机号传入 AI
- 请求限流：每用户每分钟最多 10 次 AI 调用
- 结果缓存：相同输入 1 小时内使用缓存

---

**文档版本**：V1.0
**创建日期**：2026-01-14
**作者**：AI 算法工程师
