# 智能体架构设计

**版本**: V1.0  
**设计日期**: 2026-01-20  
**状态**: 生产就绪

---

## 一、架构概览

### 1.1 设计原则

- ✅ **统一架构** - 只有一个版本，没有 v1/v2 混乱
- ✅ **基于 LangGraph** - 所有智能体使用 LangGraph 状态图
- ✅ **简单清晰** - 硬编码注册表，无复杂的装饰器或自动发现
- ✅ **易于扩展** - 新增科室只需创建目录并注册

### 1.2 系统分层

```
┌─────────────────────────────────────────────────────────┐
│                   客户端层 (iOS/Web)                      │
│  - SwiftUI 视图                                          │
│  - ConversationViewModel                                 │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────┐
│                   路由层 (sessions.py)                    │
│  - POST /sessions (创建会话)                             │
│  - POST /sessions/{id}/messages (发送消息)               │
│  - GET /sessions/{id}/messages (获取历史)                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              智能体路由器 (agents/router.py)              │
│  - 硬编码注册表: agent_type → Agent 类                    │
│  - 能力配置: actions, accepts_media                      │
│  - 科室映射: 科室名 → agent_type                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              智能体层 (LangGraph Agents)                  │
│  LangGraphAgent (抽象基类)                                │
│  ├── GeneralAgent (全科)                                 │
│  ├── DermatologyAgent (皮肤科)                           │
│  ├── CardiologyAgent (心血管科)                          │
│  └── OrthopedicsAgent (骨科)                             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   数据持久化层                            │
│  - Session (会话表, agent_state JSON)                    │
│  - Message (消息表)                                      │
│  - MedicalEvent (病历事件表)                              │
└─────────────────────────────────────────────────────────┘
```

---

## 二、目录结构

```
backend/app/services/agents/
├── __init__.py           # 模块入口，导出主要接口
├── base.py               # LangGraphAgent 基类 + AgentState
├── router.py             # AgentRouter 路由器
├── general/              # 全科智能体
│   ├── __init__.py
│   └── agent.py
├── dermatology/          # 皮肤科智能体
│   ├── __init__.py
│   └── agent.py
├── cardiology/           # 心血管科智能体
│   ├── __init__.py
│   └── agent.py
└── orthopedics/          # 骨科智能体
    ├── __init__.py
    └── agent.py
```

---

## 三、核心组件

### 3.1 AgentState - 统一状态结构

```python
class AgentState(TypedDict, total=False):
    # 会话标识
    session_id: str
    user_id: int
    agent_type: str
    
    # 对话历史（LangGraph 自动管理）
    messages: Annotated[List[dict], add_messages]
    
    # 问诊进度
    stage: Literal["greeting", "collecting", "analyzing", "diagnosing", "completed"]
    progress: int
    questions_asked: int
    
    # 医学信息
    chief_complaint: str
    symptoms: List[str]
    duration: str
    
    # AI 输出
    current_response: str
    quick_options: List[str]
    risk_level: str
    
    # 专科数据
    specialty_data: Dict[str, Any]
    
    # 附件和流程控制
    attachments: List[dict]
    action: str
    should_stream: bool
    error: Optional[str]
```

### 3.2 LangGraphAgent - 基类

```python
class LangGraphAgent(ABC):
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """构建状态图 - 子类必须实现"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        pass
    
    async def run(self, state, user_input, attachments, action, on_chunk) -> AgentResponse:
        """运行智能体（默认实现）"""
        pass
```

### 3.3 AgentResponse - 统一响应格式

```python
class AgentResponse(BaseModel):
    message: str              # AI 回复
    stage: str                # 当前阶段
    progress: int             # 进度 0-100
    quick_options: List[str]  # 快捷选项
    risk_level: Optional[str] # 风险等级
    specialty_data: Optional[Dict]  # 专科数据
    next_state: Dict          # 下次调用的状态
```

### 3.4 AgentRouter - 路由器

```python
class AgentRouter:
    @classmethod
    def register(cls, agent_type, agent_class, capabilities):
        """注册智能体"""
    
    @classmethod
    def get_agent(cls, agent_type) -> LangGraphAgent:
        """获取智能体实例"""
    
    @classmethod
    def infer_agent_type(cls, department_name) -> str:
        """根据科室名推断智能体类型"""
```

---

## 四、已实现的智能体

| 类型 | 类名 | 功能 | 支持的动作 |
|------|------|------|-----------|
| `general` | GeneralAgent | 全科问诊 | conversation |
| `dermatology` | DermatologyAgent | 皮肤科问诊、图像分析 | conversation, analyze_skin |
| `cardiology` | CardiologyAgent | 心血管问诊、心电图解读 | conversation, interpret_ecg, risk_assessment |
| `orthopedics` | OrthopedicsAgent | 骨科问诊、X光解读 | conversation, interpret_xray |

---

## 五、新增科室流程

1. **创建目录**: `backend/app/services/agents/{科室名}/`

2. **实现智能体**:
```python
# agents/{科室名}/agent.py
from ..base import LangGraphAgent, AgentState
from langgraph.graph import StateGraph, END

class NewAgent(LangGraphAgent):
    def build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)
        # 添加节点和边
        return graph.compile()
    
    def get_capabilities(self):
        return {"actions": [...], "accepts_media": [...]}
```

3. **注册到路由器**: 在 `router.py` 的 `_initialize_agents()` 中添加:
```python
from .{科室名} import NewAgent
AgentRouter.register(
    agent_type="{科室名}",
    agent_class=NewAgent,
    capabilities={...}
)
```

4. **添加科室映射**: 在 `router.py` 的 `infer_agent_type()` 中添加映射

---

## 六、API 接口

### 创建会话
```
POST /sessions
Body: { "doctor_id": 1, "agent_type": "dermatology" }
```

### 发送消息
```
POST /sessions/{session_id}/messages
Body: { 
    "content": "皮肤很痒",
    "attachments": [{"type": "image", "base64": "..."}],
    "action": "analyze_skin"
}
Headers: Accept: text/event-stream (可选，启用流式响应)
```

### 获取智能体列表
```
GET /sessions/agents
```

---

## 七、相关文档

- [API 契约文档](../API_CONTRACT.md)
- [开发规范](../DEVELOPMENT_GUIDELINES.md)
- [iOS 开发指南](../IOS_DEVELOPMENT_GUIDE.md)

---

**文档维护者**: 项目团队  
**最后更新**: 2026-01-20
