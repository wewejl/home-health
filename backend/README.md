# 鑫琳医生后端 API

## 快速开始

### 1. 安装依赖
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 初始化数据库
```bash
python -m app.seed
```

### 4. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试登录
测试阶段验证码固定为 `000000`

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "code": "000000"}'
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /auth/login | POST | 登录 |
| /auth/me | GET | 获取当前用户 |
| /departments | GET | 科室列表 |
| /departments/{id}/doctors | GET | 科室医生列表 |
| /sessions | GET | 我的问诊列表 |
| /sessions | POST | 创建问诊会话 |
| /sessions/{id}/messages | GET | 获取消息历史 |
| /sessions/{id}/messages | POST | 发送消息 |

### AI诊室统一请求结构

为了方便前端携带完整上下文，AI诊室**要求**使用单一请求体（用于开始/继续问诊）：

```json
{
  "consultation_id": "9e141b61-ddbf-45cd-bd4a-b3e1173799ea",
  "force_conclude": false,
  "history": [
    {
      "role": "assistant",
      "message": "你好，我是AI医生，请描述病情。",
      "timestamp": "2025-12-29T11:35:12Z"
    },
    {
      "role": "user",
      "message": "最近总是左下腹疼，午后更明显。",
      "timestamp": "2025-12-29T11:35:32Z"
    }
  ],
  "current_input": {
    "message": "over_week"
  }
}
```

- `consultation_id`：问诊会话 ID，新会话时可提前创建再传入。
- `force_conclude`：为 `true` 时表示点击“直接出结论”，默认 `false`。
- `history`：按时间顺序提供最近 5-10 条问答，字段包含 `role`（user/assistant）、`message`、`timestamp`。**此字段必填**，后端将基于它重建状态。
- `current_input.message`：本次提交的内容（快捷选项或自由输入均以纯文本形式传递）。**此字段必填**，替代旧版的 `user_message`。

> ⚠️ 自 2025-12-30 起，`/diagnosis/{id}/continue` 不再接受仅包含 `user_message` 的旧请求体，所有客户端必须携带 `history + current_input`。

### AI 评估进度与诊断触发

问诊进度和诊断触发逻辑由 AI 动态评估，不再使用硬编码阈值。后端返回的状态包含以下 AI 评估字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `progress` | int (0-100) | 问诊完成度百分比 |
| `should_diagnose` | bool | AI 判断是否应进入诊断阶段 |
| `can_conclude` | bool | 当前信息是否足够出诊断 |
| `confidence` | int (0-100) | 诊断置信度 |
| `missing_info` | string[] | 缺失的关键信息列表 |
| `reasoning` | string | AI 评估理由 |

**诊断触发逻辑**：
1. 若 `force_conclude=true`（用户点击"直接出结论"），立即进入诊断
2. 若 AI 返回 `should_diagnose=true`，进入诊断
3. 否则继续问诊

### 首轮快捷选项

首轮快捷选项由 AI 根据主诉或常见就诊场景动态生成，每次可能不同。若 AI 生成失败，将 fallback 到默认选项（头痛头晕、咳嗽发烧、胃痛腹泻、皮肤问题、其他症状）。

### 响应示例

```json
{
  "consultation_id": "9e141b61-ddbf-45cd-bd4a-b3e1173799ea",
  "stage": "collecting",
  "progress": 45,
  "should_diagnose": false,
  "confidence": 40,
  "missing_info": ["症状持续时间", "是否有伴随症状"],
  "current_question": "您的症状持续多长时间了？",
  "quick_options": [
    {"text": "1-3天", "value": "1-3天", "category": "时间"},
    {"text": "一周左右", "value": "一周左右", "category": "时间"},
    {"text": "超过两周", "value": "超过两周", "category": "时间"},
    {"text": "不确定", "value": "不确定", "category": "其他"}
  ]
}
```
