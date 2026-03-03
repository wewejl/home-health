# HIS 门诊 AI 助手 - 前端使用说明

## 🚀 快速启动

### 1. 启动后端服务

```bash
# 确保在项目根目录
cd /Users/zhuxinye/Desktop/project/AutoGen/his_outpatient

# 启动后端（已在后台运行）
PYTHONPATH=. ../venv/bin/python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# 或使用启动脚本
./start_api.sh
```

### 2. 打开前端页面

**方式 1: 直接打开（推荐）**
```bash
# macOS
open frontend/chat.html

# Linux
xdg-open frontend/chat.html

# Windows
start frontend/chat.html
```

**方式 2: 使用本地服务器（推荐用于开发）**
```bash
# Python 3
cd frontend
python3 -m http.server 8080

# 然后访问: http://localhost:8080/chat.html
```

**方式 3: 使用 Live Server（VSCode）**
1. 安装 Live Server 扩展
2. 右键点击 `chat.html`
3. 选择 "Open with Live Server"

## 📋 功能说明

### 主要功能

1. **智能对话**
   - 支持多轮对话，AI 会记住上下文
   - 可以询问患者信息、用药建议、疾病编码等

2. **快捷操作**
   - 查询患者信息
   - 用药咨询
   - 复杂用药建议

3. **实时状态**
   - 显示后端服务连接状态
   - 显示当前会话 ID
   - 打字指示器（AI 思考时）

4. **操作按钮**
   - 发送消息（或按 Enter 键）
   - 清空对话

### 使用示例

**示例 1: 查询患者信息**
```
你: 你好，我正在看一位叫李明的患者
AI: 您好！我是HIS医院的智能医疗助手。请问您需要了解患者李明的哪些信息？
```

**示例 2: 用药咨询（简单）**
```
你: 阿司匹林是治疗什么的？
AI: 阿司匹林主要用于治疗以下情况：...
```

**示例 3: 复杂用药（调用用药专家）**
```
你: 患者同时服用阿司匹林和华法林，需要注意什么？
AI: ⚠️ 重要提醒：此联用风险极高...（用药专家子 Agent 回复）
```

## 🔧 技术特点

### 前端特性
- ✅ 纯 HTML/CSS/JavaScript，无需构建
- ✅ 响应式设计，支持移动端
- ✅ 流畅的动画效果
- ✅ 自动滚动到最新消息
- ✅ 支持多行输入（Shift+Enter）
- ✅ 后端服务健康检查

### 后端特性
- ✅ FastAPI REST API
- ✅ PostgreSQL 持久化
- ✅ 跨会话记忆
- ✅ 用药专家子 Agent
- ✅ 审计日志

## 📊 系统架构

```
┌─────────────┐      HTTP       ┌─────────────┐
│             │  ────────────>  │             │
│   前端页面   │                  │  FastAPI    │
│  chat.html  │  < ───────────  │   后端      │
│             │      JSON       │             │
└─────────────┘                  └──────┬──────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │  ChatService  │
                                └───────┬───────┘
                                        │
                        ┌───────────────┴───────────────┐
                        ▼                               ▼
                ┌───────────────┐               ┌─────────────┐
                │  Doctor Agent │               │ PostgreSQL  │
                │  + 子 Agent   │               │  数据库      │
                └───────────────┘               └─────────────┘
```

## 🎨 界面预览

页面特点：
- 🎨 渐变紫色主题
- 💬 现代化聊天界面
- 📱 完全响应式
- ✨ 流畅动画
- 🟢 实时状态指示

## ⚠️ 注意事项

1. **CORS 限制**: 当前后端允许所有来源（`allow_origins=["*"]`），生产环境需限制
2. **会话管理**: 每次刷新页面会生成新的会话 ID
3. **数据持久化**: 对话历史保存在 PostgreSQL 数据库中
4. **网络要求**: 需要保持后端服务运行

## 🐛 常见问题

**Q: 页面显示"离线"状态**
```
A: 检查后端服务是否启动：
   curl http://localhost:8000/health

   如果未启动，运行：
   PYTHONPATH=. ../venv/bin/python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

**Q: 发送消息后没有响应**
```
A: 1. 检查浏览器控制台是否有错误
   2. 检查后端日志: tail -f api_server.log
   3. 确认数据库连接正常
```

**Q: AI 不记住之前的对话**
```
A: 确认使用同一个 session_id。当前实现每次刷新页面会生成新会话。
```

## 📞 技术支持

- 查看 API 文档: http://localhost:8000/docs
- 查看后端日志: `tail -f api_server.log`
- 数据库测试: `PYTHONPATH=. ../venv/bin/python src/db/connection.py`

## 🎯 下一步

可以扩展的功能：
- 添加用户登录
- 历史会话切换
- 导出对话记录
- 语音输入
- 多语言支持
- 暗黑模式
