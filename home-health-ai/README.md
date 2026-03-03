# 🏥 全科医生智能体 - General Practitioner Agent

基于 Microsoft AutoGen 0.7.5 官方 API 的单一全科医生智能体，支持对话历史持久化、医疗合规审计。

官方文档: https://github.com/microsoft/autogen

## 🎯 项目概述

### 核心功能
- ✅ **智能问诊** - 全科医疗咨询
- ✅ **对话记忆** - 跨会话持久化（基于 save_state/load_state）
- ✅ **医疗合规** - 审计日志、数据导出、访问控制
- ✅ **REST API** - 可集成到现有 HIS 系统

### 技术栈
- **框架**: Microsoft AutoGen 0.7.5
- **模型**: DeepSeek Chat / OpenAI 兼容
- **数据库**: PostgreSQL 17
- **API**: FastAPI
- **Python**: 3.10+

## 📁 项目结构

```
home-health-ai/
├── src/
│   ├── agents/              # 智能体定义
│   │   ├── __init__.py
│   │   └── general_practitioner.py  # 全科医生智能体
│   ├── services/            # 服务层
│   │   ├── chat_service.py  # 对话服务
│   │   └── ...
│   ├── db/                  # 数据库管理
│   │   ├── session_manager.py  # 会话管理
│   │   └── audit_logger.py     # 审计日志
│   ├── api/                 # REST API
│   └── tools/               # 工具函数
├── db/                      # 数据库脚本
├── config/                  # 配置文件
├── tests/                   # 测试
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖
└── README.md               # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd home-health-ai
pip install -r requirements.txt
```

### 2. 配置环境

编辑 `config/settings.py`：

```python
DEEPSEEK_API_KEY = "sk-your-api-key"
POSTGRESQL_URL = "postgresql://user:password@localhost/home_health_ai"
```

### 3. 启动服务

```bash
# 方式 1: 交互式命令行
python main.py

# 方式 2: REST API 服务
uvicorn src.api.app:app --reload --port 8300
```

## 📖 使用示例

### 命令行模式

```bash
python main.py

# 输入示例
> 你好
> 我头痛头晕三天了
> 高血压患者需要注意什么？
> /save   # 保存会话
> /history  # 查看历史
> /quit   # 退出
```

### API 模式

```bash
# 创建会话
curl -X POST http://localhost:8300/api/sessions

# 发送消息
curl -X POST http://localhost:8300/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "我头痛头晕三天了"}'

# 获取历史
curl http://localhost:8300/api/sessions/{session_id}/history
```

## 🏗️ 架构设计

### 单一全科医生智能体

```
用户请求
    ↓
全科医生智能体 (General Practitioner)
    ├── search_disease_info  (查询疾病信息)
    └── search_medication    (查询药物信息)
```

### 代码结构

```python
# 使用 AutoGen 0.7.5 官方 API
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 创建智能体
agent = AssistantAgent(
    name="general_practitioner",
    model_client=model_client,
    tools=[search_disease_info, search_medication],
    system_message=system_message,
)

# 运行
response = await agent.run(task="患者描述...")
```

### 状态持久化

```python
# AutoGen 官方推荐方式
state = await agent.save_state()  # 保存状态
await db.save_state(session_id, state)  # 存入 PostgreSQL

# 恢复会话
state = await db.load_state(session_id)  # 从 PostgreSQL 读取
await agent.load_state(state)  # 恢复状态
```

## 🔐 安全与合规

### 审计日志
- ✅ 所有对话记录
- ✅ 操作日志（创建、更新、删除）
- ✅ 用户访问记录
- ✅ 数据导出功能

### 数据安全
- ✅ 会话隔离
- ✅ 敏感信息脱敏
- ✅ 定期备份
- ✅ 访问控制

## 📊 性能指标

- ⚡ 响应时间: < 3秒
- 💾 数据库查询: < 100ms
- 🔄 状态保存/恢复: < 500ms
- 👥 支持并发: 100+ 会话

## ⚠️ 免责声明

本系统提供的医疗建议仅供参考，不能替代专业医师的临床判断。
