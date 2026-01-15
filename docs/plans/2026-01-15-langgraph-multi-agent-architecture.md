# LangGraph 多智能体架构设计

> 替换 CrewAI，实现高性能、可扩展的医疗问诊多智能体系统

## 1. 背景与目标

### 1.1 当前问题

| 问题 | 影响 |
|------|------|
| CrewAI 每次创建 Crew 实例开销大 | 响应时间 30-60 秒 |
| 超长 Prompt（500+ 行）每次解析 | Token 消耗高 |
| 单 Agent 场景过度设计 | 浪费编排能力 |
| 扩展困难 | 新增 Agent 需重构 |

### 1.2 目标

- **响应速度**：普通对话 1-3 秒，复杂分析 5-10 秒
- **可扩展性**：轻松添加新科室、新能力
- **推理深度**：保持专业医学推理质量
- **兼容性**：现有 API 接口完全兼容

## 2. 技术选型

### 2.1 为什么选择 LangGraph

| 维度 | CrewAI | LangGraph |
|------|--------|-----------|
| 性能 | 每次创建 Crew 开销大 | 图结构复用，状态流转快 |
| 灵活性 | 固定编排模式 | 自定义状态图，完全控制 |
| 可扩展性 | 添加 Agent 需重构 | 动态添加节点和边 |
| 调试 | 黑盒，难追踪 | 状态可视化，易调试 |
| 流式输出 | 有限支持 | 原生支持 |
| 并行执行 | 有限 | 原生支持并行节点 |

### 2.2 依赖版本

```
langgraph>=0.2.0
langchain-core>=0.3.0
langchain-openai>=0.2.0  # 或 langchain-community for DashScope
```

## 3. 核心架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (routes/)                       │
│                    POST /sessions/{id}/messages                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      AgentRouter (不变)                          │
│                   根据 agent_type 路由到科室                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ DermaLangGraph  │  │ CardioLangGraph │  │ OrthoLangGraph  │
│    Agent        │  │     Agent       │  │     Agent       │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraphAgentBase (新增)                      │
│              统一的图构建、状态管理、流式输出                       │
└─────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                        LLM Provider                              │
│              DashScope (Qwen) / OpenAI / Ollama                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 类层次结构

```
BaseAgent (ABC)                    # 现有抽象基类，保持不变
    │
    ├── LangGraphAgentBase         # 新增：LangGraph 实现基类
    │       │
    │       ├── DermaLangGraphAgent    # 皮肤科
    │       ├── CardioLangGraphAgent   # 心血管科
    │       ├── OrthoLangGraphAgent    # 骨科
    │       └── GeneralLangGraphAgent  # 通用
    │
    └── (Future) AutoGenAgentBase  # 未来可扩展其他框架
```

## 4. 状态设计

### 4.1 基础状态（所有科室共享）

```python
from typing import TypedDict, List, Literal, Annotated, Optional
from langgraph.graph.message import add_messages

class BaseAgentState(TypedDict):
    """统一的 Agent 状态基类"""
    # === 会话标识 ===
    session_id: str
    user_id: int
    agent_type: str
    
    # === 对话历史（LangGraph 自动管理追加）===
    messages: Annotated[List[dict], add_messages]
    
    # === 问诊进度 ===
    stage: Literal["greeting", "collecting", "analyzing", "diagnosis", "completed"]
    questions_asked: int
    
    # === 核心医学信息 ===
    chief_complaint: str          # 主诉
    symptoms: List[str]           # 症状列表
    duration: str                 # 持续时间
    
    # === AI 输出 ===
    current_response: str         # 当前回复
    quick_options: List[dict]     # 快捷选项
    
    # === 流程控制 ===
    next_node: str                # 下一个节点
    should_stream: bool           # 是否流式输出
    
    # === 附件处理 ===
    pending_attachments: List[dict]    # 待处理附件
    processed_results: List[dict]      # 处理结果
    
    # === 错误处理 ===
    error: Optional[str]
```

### 4.2 皮肤科扩展状态

```python
class DermaState(BaseAgentState):
    """皮肤科专用状态"""
    # === 皮肤科特有字段 ===
    skin_location: str            # 皮损部位
    skin_analyses: List[dict]     # 图片分析历史
    latest_analysis: Optional[dict]
    
    # === 诊断相关 ===
    possible_conditions: List[dict]  # 可能的诊断
    risk_level: Literal["low", "medium", "high", "emergency"]
    care_advice: str
    need_offline_visit: bool
```

### 4.3 心血管科扩展状态

```python
class CardioState(BaseAgentState):
    """心血管科专用状态"""
    # === 心血管科特有字段 ===
    chest_pain_type: str          # 胸痛类型
    ecg_analyses: List[dict]      # 心电图分析历史
    risk_factors: List[str]       # 危险因素
    
    # === 风险评估 ===
    cardiovascular_risk_score: int
    recommended_tests: List[str]
```

## 5. 节点设计

### 5.1 皮肤科状态图

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   router    │◄──────────────────┐
                    └──────┬──────┘                   │
                           │                          │
          ┌────────────────┼────────────────┐         │
          │                │                │         │
    ┌─────▼─────┐   ┌──────▼──────┐  ┌──────▼─────┐   │
    │ greeting  │   │conversation │  │image_analysis│  │
    └─────┬─────┘   └──────┬──────┘  └──────┬──────┘  │
          │                │                │         │
          └────────────────┴────────────────┴─────────┘
                           │
                    ┌──────▼──────┐
                    │  diagnosis  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    END      │
                    └─────────────┘
```

### 5.2 节点函数实现

```python
# === 路由节点 ===
def route_node(state: DermaState) -> DermaState:
    """决定下一个执行节点"""
    # 新会话 -> 问候
    if state["stage"] == "greeting" and state["questions_asked"] == 0:
        state["next_node"] = "greeting"
        return state
    
    # 有待处理图片 -> 图片分析
    if state["pending_attachments"]:
        state["next_node"] = "image_analysis"
        return state
    
    # 信息足够 + 用户请求诊断 -> 诊断
    if should_give_diagnosis(state):
        state["next_node"] = "diagnosis"
        return state
    
    # 默认 -> 继续对话
    state["next_node"] = "conversation"
    return state

def route_decision(state: DermaState) -> str:
    """返回下一个节点名称"""
    return state["next_node"]


# === 问候节点 ===
async def greeting_node(state: DermaState) -> DermaState:
    """问候节点 - 快速响应，无需 LLM"""
    greeting = """你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。"""
    
    state["current_response"] = greeting
    state["stage"] = "collecting"
    state["quick_options"] = [
        {"text": "描述位置", "value": "出现在身体哪个部位", "category": "症状"},
        {"text": "持续时间", "value": "大概持续了多久", "category": "症状"},
        {"text": "伴随感觉", "value": "是否有瘙痒或疼痛", "category": "症状"},
    ]
    state["next_node"] = "end"
    return state


# === 对话节点（核心）===
async def conversation_node(state: DermaState) -> DermaState:
    """问诊对话节点 - 轻量化，快速响应"""
    from langchain_core.prompts import ChatPromptTemplate
    
    # 获取最新用户输入
    user_input = get_last_user_message(state["messages"])
    
    # 构建精简 Prompt（<200 tokens）
    prompt = ChatPromptTemplate.from_messages([
        ("system", DERMA_SYSTEM_PROMPT),  # 精简版系统提示
        ("human", """
当前问诊信息：
- 主诉: {chief_complaint}
- 部位: {skin_location}
- 症状: {symptoms}
- 已问诊 {questions_asked} 轮

用户说: {user_input}

请继续问诊或给出建议。输出 JSON 格式。
""")
    ])
    
    # 使用 with_structured_output 保证格式
    chain = prompt | llm.with_structured_output(ConversationOutput)
    
    result = await chain.ainvoke({
        "chief_complaint": state.get("chief_complaint", "未明确"),
        "skin_location": state.get("skin_location", "未明确"),
        "symptoms": ", ".join(state.get("symptoms", [])) or "未明确",
        "questions_asked": state["questions_asked"],
        "user_input": user_input
    })
    
    # 更新状态
    state["current_response"] = result.message
    state["quick_options"] = result.quick_options
    state["questions_asked"] += 1
    
    # 更新提取的医学信息
    if result.extracted_info:
        update_medical_info(state, result.extracted_info)
    
    # 判断下一步
    if result.next_action == "complete":
        state["next_node"] = "diagnosis"
        state["stage"] = "diagnosis"
    else:
        state["next_node"] = "end"
    
    return state


# === 图片分析节点 ===
async def image_analysis_node(state: DermaState) -> DermaState:
    """图片分析节点 - 多模态 LLM"""
    attachment = state["pending_attachments"].pop(0)
    
    # 构建多模态消息
    messages = [
        {
            "role": "system",
            "content": DERMA_IMAGE_ANALYSIS_PROMPT  # 精简版图片分析提示
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": attachment["base64"]}},
                {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{state.get('chief_complaint', '未说明')}"}
            ]
        }
    ]
    
    result = await multimodal_llm.ainvoke(messages)
    
    # 解析结果
    analysis = parse_image_analysis(result.content)
    
    # 更新状态
    state["skin_analyses"].append(analysis)
    state["latest_analysis"] = analysis
    state["current_response"] = analysis["message"]
    state["processed_results"].append({
        "type": "image_analysis",
        "result": analysis
    })
    
    # 根据图片分析更新医学信息
    if analysis.get("extracted_info"):
        update_medical_info(state, analysis["extracted_info"])
    
    state["next_node"] = "end"
    return state


# === 诊断节点 ===
async def diagnosis_node(state: DermaState) -> DermaState:
    """诊断节点 - 综合分析，给出建议"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", DERMA_DIAGNOSIS_PROMPT),
        ("human", """
请根据以下信息给出诊断建议：

主诉: {chief_complaint}
部位: {skin_location}
持续时间: {duration}
症状: {symptoms}
图片分析: {image_analysis}

要求：
1. 给出 1-3 个鉴别诊断
2. 说明诊断依据
3. 给出具体治疗建议
4. 说明何时需要就医
""")
    ])
    
    chain = prompt | llm.with_structured_output(DiagnosisOutput)
    
    result = await chain.ainvoke({
        "chief_complaint": state.get("chief_complaint", ""),
        "skin_location": state.get("skin_location", ""),
        "duration": state.get("duration", ""),
        "symptoms": ", ".join(state.get("symptoms", [])),
        "image_analysis": format_image_analyses(state.get("skin_analyses", []))
    })
    
    # 更新状态
    state["current_response"] = result.diagnosis_message
    state["possible_conditions"] = result.conditions
    state["risk_level"] = result.risk_level
    state["care_advice"] = result.care_advice
    state["need_offline_visit"] = result.need_offline_visit
    state["stage"] = "completed"
    state["next_node"] = "end"
    
    return state
```

## 6. Prompt 优化策略

### 6.1 精简 System Prompt

**原则：专注单一职责，每个节点独立 Prompt**

```python
# 对话节点 Prompt（<150 tokens）
DERMA_CONVERSATION_PROMPT = """你是皮肤科专家医生。

任务：根据患者描述进行问诊。

规则：
1. 专业但通俗的语言
2. 系统收集：主诉、部位、持续时间、症状
3. 识别危急情况立即建议就医
4. 信息足够时给出诊断

输出 JSON：
{"message": "回复", "next_action": "continue/complete", "extracted_info": {...}, "quick_options": [...]}
"""

# 图片分析 Prompt（<100 tokens）
DERMA_IMAGE_ANALYSIS_PROMPT = """你是皮肤科影像专家。

任务：分析皮肤照片，描述皮损特征。

要点：形态、颜色、分布、边界、大小。

输出 JSON：
{"message": "分析描述", "extracted_info": {"skin_location": "", "symptoms": []}}
"""

# 诊断 Prompt（<100 tokens）
DERMA_DIAGNOSIS_PROMPT = """你是皮肤科诊断专家。

任务：综合问诊信息给出诊断建议。

要求：鉴别诊断、依据、治疗方案、就医指征。
"""
```

### 6.2 Prompt 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def get_compiled_prompt(prompt_name: str):
    """缓存编译后的 Prompt 模板"""
    prompts = {
        "conversation": ChatPromptTemplate.from_messages([...]),
        "image_analysis": ChatPromptTemplate.from_messages([...]),
        "diagnosis": ChatPromptTemplate.from_messages([...]),
    }
    return prompts[prompt_name]
```

## 7. 性能优化策略

### 7.1 图实例复用

```python
class DermaLangGraphAgent(LangGraphAgentBase):
    """皮肤科 LangGraph Agent"""
    
    # 类级别缓存编译后的图
    _compiled_graph = None
    
    @classmethod
    def get_graph(cls):
        """获取编译后的图（单例模式）"""
        if cls._compiled_graph is None:
            cls._compiled_graph = cls._build_graph()
        return cls._compiled_graph
    
    @classmethod
    def _build_graph(cls):
        """构建并编译状态图（只执行一次）"""
        graph = StateGraph(DermaState)
        
        graph.add_node("router", route_node)
        graph.add_node("greeting", greeting_node)
        graph.add_node("conversation", conversation_node)
        graph.add_node("image_analysis", image_analysis_node)
        graph.add_node("diagnosis", diagnosis_node)
        
        graph.set_entry_point("router")
        
        graph.add_conditional_edges(
            "router",
            route_decision,
            {
                "greeting": "greeting",
                "conversation": "conversation",
                "image_analysis": "image_analysis",
                "diagnosis": "diagnosis",
                "end": END
            }
        )
        
        # 所有节点执行后回到 router 或结束
        for node in ["greeting", "conversation", "image_analysis"]:
            graph.add_conditional_edges(
                node,
                lambda s: s["next_node"],
                {"end": END, "diagnosis": "diagnosis"}
            )
        
        graph.add_edge("diagnosis", END)
        
        return graph.compile()
```

### 7.2 LLM 实例复用

```python
from langchain_openai import ChatOpenAI

class LLMProvider:
    """LLM 提供者（单例）"""
    _instance = None
    _llm = None
    _multimodal_llm = None
    
    @classmethod
    def get_llm(cls):
        """获取普通 LLM"""
        if cls._llm is None:
            cls._llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=0.6,
                max_tokens=1500,
                timeout=30,  # 缩短超时
                max_retries=1,
            )
        return cls._llm
    
    @classmethod
    def get_multimodal_llm(cls):
        """获取多模态 LLM"""
        if cls._multimodal_llm is None:
            cls._multimodal_llm = ChatOpenAI(
                model=settings.QWEN_VL_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=0.6,
                max_tokens=2000,
                timeout=60,
            )
        return cls._multimodal_llm
```

### 7.3 流式输出

```python
async def run_with_stream(
    self,
    state: DermaState,
    on_chunk: Callable[[str], Awaitable[None]]
) -> DermaState:
    """支持流式输出的运行方法"""
    graph = self.get_graph()
    
    # LangGraph 原生流式支持
    async for event in graph.astream_events(state, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                await on_chunk(chunk.content)
    
    # 获取最终状态
    final_state = await graph.ainvoke(state)
    return final_state
```

### 7.4 并行处理

```python
# 在状态图中定义并行节点
from langgraph.graph import StateGraph

def build_parallel_graph():
    """构建支持并行的状态图"""
    graph = StateGraph(DermaState)
    
    # 并行分支：同时进行图片分析和症状提取
    graph.add_node("parallel_analysis", parallel_analysis_node)
    
    # 使用 fan-out/fan-in 模式
    graph.add_node("image_branch", image_analysis_node)
    graph.add_node("symptom_branch", symptom_extraction_node)
    graph.add_node("merge", merge_results_node)
    
    # 并行边
    graph.add_edge("parallel_analysis", "image_branch")
    graph.add_edge("parallel_analysis", "symptom_branch")
    graph.add_edge("image_branch", "merge")
    graph.add_edge("symptom_branch", "merge")
    
    return graph.compile()
```

## 8. LangGraphAgentBase 实现

```python
from abc import abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
from langgraph.graph import StateGraph, END

from .base import BaseAgent


class LangGraphAgentBase(BaseAgent):
    """LangGraph 实现的 Agent 基类"""
    
    # 子类需要定义的类属性
    STATE_CLASS = BaseAgentState  # 状态类
    
    def __init__(self):
        self._graph = None
    
    @property
    def graph(self):
        """获取编译后的图（懒加载）"""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph
    
    @abstractmethod
    def _build_graph(self) -> StateGraph:
        """构建状态图 - 子类必须实现"""
        pass
    
    @abstractmethod
    def _create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态 - 子类必须实现"""
        pass
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """实现 BaseAgent 接口"""
        return self._create_initial_state(session_id, user_id)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行 Agent
        
        实现 BaseAgent 接口，内部使用 LangGraph 状态图
        """
        # 添加用户消息到状态
        if user_input:
            state["messages"].append({
                "role": "user",
                "content": user_input
            })
        
        # 处理附件
        if attachments:
            for att in attachments:
                state["pending_attachments"].append(att)
        
        # 标记是否需要流式输出
        state["should_stream"] = on_chunk is not None
        
        # 运行状态图
        if on_chunk:
            # 流式输出模式
            final_state = await self._run_with_stream(state, on_chunk)
        else:
            # 普通模式
            final_state = await self.graph.ainvoke(state)
        
        # 添加 AI 回复到消息历史
        if final_state.get("current_response"):
            final_state["messages"].append({
                "role": "assistant",
                "content": final_state["current_response"]
            })
        
        return final_state
    
    async def _run_with_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Callable[[str], Awaitable[None]]
    ) -> Dict[str, Any]:
        """流式输出运行"""
        final_state = state
        streamed_content = ""
        
        async for event in self.graph.astream_events(state, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    await on_chunk(chunk.content)
                    streamed_content += chunk.content
            elif event["event"] == "on_chain_end":
                if "output" in event["data"]:
                    final_state = event["data"]["output"]
        
        # 如果流式内容被收集，更新到状态
        if streamed_content and not final_state.get("current_response"):
            final_state["current_response"] = streamed_content
        
        return final_state
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置 - 子类必须实现"""
        pass
```

## 9. 皮肤科完整实现

```python
# app/services/dermatology/derma_langgraph_agent.py

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..base import LangGraphAgentBase
from .prompts import (
    DERMA_CONVERSATION_PROMPT,
    DERMA_IMAGE_ANALYSIS_PROMPT,
    DERMA_DIAGNOSIS_PROMPT
)
from ..llm_provider import LLMProvider


# === Pydantic 输出模型 ===
class ConversationOutput(BaseModel):
    message: str = Field(description="回复消息")
    next_action: str = Field(description="continue 或 complete")
    extracted_info: Dict[str, Any] = Field(default_factory=dict)
    quick_options: List[Dict[str, str]] = Field(default_factory=list)

class DiagnosisOutput(BaseModel):
    diagnosis_message: str
    conditions: List[Dict[str, Any]]
    risk_level: str
    care_advice: str
    need_offline_visit: bool


# === 状态定义 ===
class DermaState(BaseAgentState):
    skin_location: str
    skin_analyses: List[dict]
    latest_analysis: dict | None
    possible_conditions: List[dict]
    risk_level: str
    care_advice: str
    need_offline_visit: bool


# === Agent 实现 ===
class DermaLangGraphAgent(LangGraphAgentBase):
    """皮肤科 LangGraph Agent"""
    
    STATE_CLASS = DermaState
    
    def _create_initial_state(self, session_id: str, user_id: int) -> DermaState:
        return DermaState(
            session_id=session_id,
            user_id=user_id,
            agent_type="dermatology",
            messages=[],
            stage="greeting",
            questions_asked=0,
            chief_complaint="",
            symptoms=[],
            duration="",
            current_response="",
            quick_options=[],
            next_node="router",
            should_stream=False,
            pending_attachments=[],
            processed_results=[],
            error=None,
            # 皮肤科特有
            skin_location="",
            skin_analyses=[],
            latest_analysis=None,
            possible_conditions=[],
            risk_level="low",
            care_advice="",
            need_offline_visit=False
        )
    
    def _build_graph(self) -> StateGraph:
        """构建皮肤科状态图"""
        graph = StateGraph(DermaState)
        
        # 添加节点
        graph.add_node("router", self._route_node)
        graph.add_node("greeting", self._greeting_node)
        graph.add_node("conversation", self._conversation_node)
        graph.add_node("image_analysis", self._image_analysis_node)
        graph.add_node("diagnosis", self._diagnosis_node)
        
        # 设置入口
        graph.set_entry_point("router")
        
        # 路由条件边
        graph.add_conditional_edges(
            "router",
            lambda s: s["next_node"],
            {
                "greeting": "greeting",
                "conversation": "conversation",
                "image_analysis": "image_analysis",
                "diagnosis": "diagnosis",
                "end": END
            }
        )
        
        # 节点后续流转
        for node in ["greeting", "conversation", "image_analysis"]:
            graph.add_conditional_edges(
                node,
                lambda s: s["next_node"],
                {"end": END, "diagnosis": "diagnosis", "conversation": "conversation"}
            )
        
        graph.add_edge("diagnosis", END)
        
        return graph.compile()
    
    # === 节点实现 ===
    
    def _route_node(self, state: DermaState) -> DermaState:
        """路由决策"""
        # 新会话
        if state["stage"] == "greeting" and state["questions_asked"] == 0:
            has_history = any(m.get("role") == "assistant" for m in state["messages"])
            if not has_history:
                state["next_node"] = "greeting"
                return state
        
        # 有待处理图片
        if state["pending_attachments"]:
            state["next_node"] = "image_analysis"
            return state
        
        # 判断是否应该诊断
        if self._should_diagnose(state):
            state["next_node"] = "diagnosis"
            return state
        
        # 默认继续对话
        state["next_node"] = "conversation"
        return state
    
    def _should_diagnose(self, state: DermaState) -> bool:
        """判断是否应该给出诊断"""
        # 用户请求
        last_msg = state["messages"][-1]["content"] if state["messages"] else ""
        user_wants_diagnosis = any(kw in last_msg for kw in ["怎么办", "是什么", "建议", "严重吗"])
        
        # 信息足够
        has_enough_info = (
            bool(state.get("chief_complaint")) and
            bool(state.get("skin_location")) and
            len(state.get("symptoms", [])) >= 1
        )
        
        # 对话足够长
        enough_rounds = state["questions_asked"] >= 3
        
        return user_wants_diagnosis or (has_enough_info and enough_rounds)
    
    async def _greeting_node(self, state: DermaState) -> DermaState:
        """问候节点"""
        greeting = """你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。"""
        
        state["current_response"] = greeting
        state["stage"] = "collecting"
        state["quick_options"] = [
            {"text": "描述位置", "value": "出现在身体哪个部位", "category": "症状"},
            {"text": "持续时间", "value": "大概持续了多久", "category": "症状"},
            {"text": "伴随感觉", "value": "是否有瘙痒或疼痛", "category": "症状"},
        ]
        state["next_node"] = "end"
        return state
    
    async def _conversation_node(self, state: DermaState) -> DermaState:
        """对话节点"""
        llm = LLMProvider.get_llm()
        
        user_input = state["messages"][-1]["content"] if state["messages"] else ""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", DERMA_CONVERSATION_PROMPT),
            ("human", """
问诊信息：主诉={chief_complaint}，部位={skin_location}，症状={symptoms}，已问诊{questions_asked}轮

用户说：{user_input}

请继续问诊或给出建议。
""")
        ])
        
        chain = prompt | llm.with_structured_output(ConversationOutput)
        
        result = await chain.ainvoke({
            "chief_complaint": state.get("chief_complaint") or "未明确",
            "skin_location": state.get("skin_location") or "未明确",
            "symptoms": ", ".join(state.get("symptoms", [])) or "未明确",
            "questions_asked": state["questions_asked"],
            "user_input": user_input
        })
        
        # 更新状态
        state["current_response"] = result.message
        state["quick_options"] = result.quick_options
        state["questions_asked"] += 1
        
        # 更新医学信息
        if result.extracted_info:
            if result.extracted_info.get("chief_complaint"):
                state["chief_complaint"] = result.extracted_info["chief_complaint"]
            if result.extracted_info.get("skin_location"):
                state["skin_location"] = result.extracted_info["skin_location"]
            if result.extracted_info.get("duration"):
                state["duration"] = result.extracted_info["duration"]
            if result.extracted_info.get("symptoms"):
                for s in result.extracted_info["symptoms"]:
                    if s not in state["symptoms"]:
                        state["symptoms"].append(s)
        
        # 下一步
        if result.next_action == "complete":
            state["next_node"] = "diagnosis"
            state["stage"] = "diagnosis"
        else:
            state["next_node"] = "end"
        
        return state
    
    async def _image_analysis_node(self, state: DermaState) -> DermaState:
        """图片分析节点"""
        llm = LLMProvider.get_multimodal_llm()
        
        attachment = state["pending_attachments"].pop(0)
        image_base64 = attachment.get("base64", "")
        
        if not image_base64.startswith("data:"):
            image_base64 = f"data:image/jpeg;base64,{image_base64}"
        
        messages = [
            {"role": "system", "content": DERMA_IMAGE_ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_base64}},
                    {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{state.get('chief_complaint', '未说明')}"}
                ]
            }
        ]
        
        response = await llm.ainvoke(messages)
        
        # 解析结果（简化处理）
        analysis = {
            "message": response.content,
            "type": "image_analysis"
        }
        
        state["skin_analyses"].append(analysis)
        state["latest_analysis"] = analysis
        state["current_response"] = response.content
        state["processed_results"].append(attachment)
        state["next_node"] = "end"
        
        return state
    
    async def _diagnosis_node(self, state: DermaState) -> DermaState:
        """诊断节点"""
        llm = LLMProvider.get_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", DERMA_DIAGNOSIS_PROMPT),
            ("human", """
请根据以下信息给出诊断：
- 主诉: {chief_complaint}
- 部位: {skin_location}
- 持续时间: {duration}
- 症状: {symptoms}
- 图片分析: {image_analysis}
""")
        ])
        
        chain = prompt | llm.with_structured_output(DiagnosisOutput)
        
        image_analysis_text = ""
        if state.get("skin_analyses"):
            image_analysis_text = state["skin_analyses"][-1].get("message", "")
        
        result = await chain.ainvoke({
            "chief_complaint": state.get("chief_complaint", ""),
            "skin_location": state.get("skin_location", ""),
            "duration": state.get("duration", ""),
            "symptoms": ", ".join(state.get("symptoms", [])),
            "image_analysis": image_analysis_text or "无图片分析"
        })
        
        state["current_response"] = result.diagnosis_message
        state["possible_conditions"] = result.conditions
        state["risk_level"] = result.risk_level
        state["care_advice"] = result.care_advice
        state["need_offline_visit"] = result.need_offline_visit
        state["stage"] = "completed"
        state["next_node"] = "end"
        
        return state
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "SkinAnalysisCard", "ReportInterpretationCard"],
            "description": "皮肤科AI智能体（LangGraph），支持皮肤影像分析和报告解读"
        }
```

## 10. 迁移方案

### 10.1 迁移策略：渐进式替换

```
阶段1: 新增 LangGraph 实现，与 CrewAI 并存
阶段2: 通过配置切换，A/B 测试验证性能
阶段3: 确认稳定后，移除 CrewAI 实现
```

### 10.2 Wrapper 兼容层

```python
# app/services/dermatology/__init__.py

from ...config import get_settings

settings = get_settings()

# 根据配置选择实现
if settings.USE_LANGGRAPH:
    from .derma_langgraph_agent import DermaLangGraphAgent as DermaAgentWrapper
else:
    from .derma_wrapper import DermaAgentWrapper

__all__ = ["DermaAgentWrapper"]
```

### 10.3 配置开关

```python
# app/config.py

class Settings:
    # ... 现有配置 ...
    
    # LangGraph 开关
    USE_LANGGRAPH: bool = True  # 默认启用
    
    # 性能配置
    LLM_TIMEOUT: int = 30       # 缩短超时
    LLM_MAX_RETRIES: int = 1    # 减少重试
```

### 10.4 文件结构变更

```
app/services/
├── base/
│   ├── __init__.py
│   ├── base_agent.py           # 现有，不变
│   └── langgraph_base.py       # 新增：LangGraph 基类
├── dermatology/
│   ├── __init__.py             # 修改：添加切换逻辑
│   ├── derma_agent.py          # 保留（兼容）
│   ├── derma_agents.py         # 保留（兼容）
│   ├── derma_crew_service.py   # 保留（兼容）
│   ├── derma_wrapper.py        # 保留（兼容）
│   ├── derma_langgraph_agent.py  # 新增：LangGraph 实现
│   └── prompts.py              # 新增：精简 Prompt
├── cardiology/
│   └── ... (同上)
├── orthopedics/
│   └── ... (同上)
└── llm_provider.py             # 新增：LLM 单例提供者
```

## 11. 实施计划

### Phase 1: 基础设施（1天）

- [ ] 安装 `langgraph` 依赖
- [ ] 创建 `LangGraphAgentBase` 基类
- [ ] 创建 `LLMProvider` 单例
- [ ] 添加配置开关

### Phase 2: 皮肤科迁移（2天）

- [ ] 创建 `DermaLangGraphAgent`
- [ ] 实现所有节点函数
- [ ] 编写精简 Prompts
- [ ] 集成测试

### Phase 3: 验证与优化（1天）

- [ ] A/B 测试对比性能
- [ ] 调优 Prompt 和超时
- [ ] 确认流式输出正常
- [ ] 确认状态持久化兼容

### Phase 4: 其他科室迁移（2天）

- [ ] 心血管科迁移
- [ ] 骨科迁移
- [ ] 通用科迁移

### Phase 5: 清理（1天）

- [ ] 移除 CrewAI 依赖
- [ ] 清理废弃代码
- [ ] 更新文档

## 12. 预期收益

| 指标 | 当前（CrewAI） | 目标（LangGraph） |
|------|----------------|-------------------|
| 普通对话响应 | 30-60 秒 | 1-3 秒 |
| 图片分析响应 | 60-90 秒 | 5-10 秒 |
| Token 消耗/轮 | ~2000 | ~500 |
| 代码可维护性 | 低（黑盒） | 高（状态图可视化） |
| 新增科室成本 | 3-5 天 | 1 天 |

## 13. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| LangGraph 版本不稳定 | 锁定版本，充分测试 |
| 流式输出兼容性 | 保留非流式回退方案 |
| 状态序列化问题 | 使用 TypedDict + Pydantic |
| 推理质量下降 | A/B 测试，逐步优化 Prompt |
