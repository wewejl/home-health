# LangGraph 智能体架构统一重构计划

> **状态:** ✅ 已完成
> **完成日期:** 2026-01-20
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 统一使用 LangGraph 重构所有智能体，删除 v1/v2 双版本混乱，建立清晰的单一架构。

**Architecture:** 
- 使用 LangGraph StateGraph 构建所有智能体的状态图
- 统一的 AgentState 基类和 AgentResponse 响应格式
- 每个科室一个独立目录，继承统一基类
- 单一路由器 AgentRouter，硬编码注册表

**Tech Stack:** LangGraph 1.x, FastAPI, Pydantic, SQLAlchemy, 通义千问 API

---

## 阶段概览

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| 1 | 清理废弃代码和文件 | 15分钟 |
| 2 | 创建统一 LangGraph 基础架构 | 30分钟 |
| 3 | 实现智能体路由器 | 15分钟 |
| 4 | 实现各科室智能体 | 1小时 |
| 5 | 统一路由层和测试 | 30分钟 |

---

## 阶段 1: 清理废弃代码和文件

### Task 1.1: 删除 v2 相关文件

**需要删除的文件:**
- `backend/app/routes/sessions_v2.py`
- `backend/app/services/agent_router_v2.py`
- `backend/app/services/general_v2/` (整个目录)
- `backend/app/services/base/base_agent_v2.py` (如果存在)

**需要删除的文档:**
- `docs/architecture/multi-agent-architecture-v2.md`

### Task 1.2: 清理 main.py 中的 v2 路由注册

**修改文件:** `backend/app/main.py`
- 移除 `sessions_v2` 路由导入和注册

### Task 1.3: 清理 routes/__init__.py 中的 v2 导出

**修改文件:** `backend/app/routes/__init__.py`
- 移除 v2 相关导出

### Task 1.4: 删除旧的智能体目录结构

**需要清理的目录:**
- `backend/app/services/base/` - 保留但重构
- `backend/app/services/general/` - 保留但重构
- `backend/app/services/cardiology/` - 保留但重构
- `backend/app/services/orthopedics/` - 保留但重构

---

## 阶段 2: 创建统一 LangGraph 基础架构

### Task 2.1: 创建 AgentResponse Schema

**创建文件:** `backend/app/schemas/agent_response.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AgentResponse(BaseModel):
    """统一智能体响应格式"""
    
    # 基础字段（必填）
    message: str = Field(..., description="AI 回复内容")
    stage: str = Field(..., description="当前阶段: greeting, collecting, analyzing, diagnosis, completed")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    
    # 可选字段
    quick_options: List[str] = Field(default=[], description="快捷回复选项")
    risk_level: Optional[str] = Field(None, description="风险等级: low, medium, high, emergency")
    
    # 病历相关
    event_id: Optional[str] = Field(None, description="关联的病历事件ID")
    should_show_dossier_prompt: bool = Field(False, description="是否提示生成病历")
    
    # 专科扩展数据
    specialty_data: Optional[Dict[str, Any]] = Field(
        None,
        description="专科特有数据，如: {'diagnosis_card': {...}, 'skin_analysis': {...}}"
    )
    
    # 状态持久化
    next_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="下次调用需要的状态（保存到 Session.agent_state）"
    )
```

### Task 2.2: 创建统一的 LangGraph 基类

**创建文件:** `backend/app/services/agents/base.py`

定义:
- `AgentState` TypedDict - 统一状态结构
- `LangGraphAgent` ABC - 所有智能体的基类
- 提供 `run()` 方法的默认实现
- 提供流式输出支持

### Task 2.3: 创建智能体目录结构

```
backend/app/services/agents/
├── __init__.py
├── base.py              # LangGraph 基类
├── router.py            # 统一路由器
├── general/
│   ├── __init__.py
│   └── agent.py
├── dermatology/
│   ├── __init__.py
│   ├── agent.py
│   └── tools.py
├── cardiology/
│   ├── __init__.py
│   ├── agent.py
│   └── tools.py
└── orthopedics/
    ├── __init__.py
    └── agent.py
```

---

## 阶段 3: 实现智能体路由器

### Task 3.1: 创建统一路由器

**创建文件:** `backend/app/services/agents/router.py`

```python
from typing import Dict, Type
from .base import LangGraphAgent

class AgentRouter:
    """统一智能体路由器"""
    
    _agents: Dict[str, Type[LangGraphAgent]] = {}
    _capabilities: Dict[str, Dict] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, agent_type: str, agent_class: Type[LangGraphAgent], capabilities: Dict):
        """注册智能体"""
        pass
    
    @classmethod
    def get_agent(cls, agent_type: str) -> LangGraphAgent:
        """获取智能体实例"""
        pass
    
    @classmethod
    def infer_agent_type(cls, department_name: str) -> str:
        """根据科室名推断智能体类型"""
        pass
```

---

## 阶段 4: 实现各科室智能体

### Task 4.1: 实现 GeneralAgent

**文件:** `backend/app/services/agents/general/agent.py`

简单的对话流程:
- greeting → collecting → completed
- 使用 QwenService 生成回复

### Task 4.2: 实现 DermatologyAgent

**文件:** `backend/app/services/agents/dermatology/agent.py`

完整的皮肤科流程:
- greeting → collecting → analyzing (如有图片) → diagnosis → completed
- 支持图像分析 (QwenVLService)
- 生成诊断卡和建议

### Task 4.3: 实现 CardiologyAgent

**文件:** `backend/app/services/agents/cardiology/agent.py`

心血管科流程:
- 支持心电图解读
- 风险评估

### Task 4.4: 实现 OrthopedicsAgent

**文件:** `backend/app/services/agents/orthopedics/agent.py`

骨科流程:
- 支持 X 光片解读

---

## 阶段 5: 统一路由层和测试

### Task 5.1: 重构 sessions.py

**修改文件:** `backend/app/routes/sessions.py`

- 使用新的 `AgentRouter`
- 返回 `AgentResponse` 格式
- 保持 SSE 流式响应

### Task 5.2: 更新 services/__init__.py

**修改文件:** `backend/app/services/__init__.py`

- 导出新的 `AgentRouter`
- 移除旧的导出

### Task 5.3: 编写基础测试

**创建文件:** `backend/tests/test_agents.py`

测试:
- AgentRouter 注册和获取
- GeneralAgent 基本对话
- AgentResponse 格式验证

### Task 5.4: 清理数据库会话数据

```bash
# SQLite 清理脚本
sqlite3 backend/app.db "DELETE FROM messages; DELETE FROM sessions;"
```

### Task 5.5: 更新架构文档

**创建文件:** `docs/architecture/agent-architecture.md`

- 删除旧的 v2 文档
- 创建新的统一架构文档

---

## 验收标准

- [ ] 没有任何 `_v2` 后缀的文件
- [ ] 所有智能体继承 `LangGraphAgent` 基类
- [ ] 统一使用 `AgentResponse` 响应格式
- [ ] `/sessions` 路由正常工作
- [ ] 皮肤科图像分析功能正常
- [ ] 基础测试通过

---

**计划完成。立即开始执行阶段 1: 清理废弃代码。**
