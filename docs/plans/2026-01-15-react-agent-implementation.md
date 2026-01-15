# ReAct Agent 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将皮肤科智能体从状态机模式重构为 LangGraph ReAct Agent 模式，实现自然对话、渐进式诊断和动态快捷选项。

**Architecture:** 使用 LangGraph 的 ReAct 循环：agent → should_continue → tools → agent。LLM 通过 bind_tools 绑定医疗工具，自主决策何时调用。

**Tech Stack:** LangGraph 0.2+, LangChain Core 0.3+, Pydantic, Python 3.12

**Design Doc:** `docs/plans/2026-01-15-intelligent-agent-redesign.md`

---

## Task 1: 创建 ReAct Agent 状态定义

**Files:**
- Create: `backend/app/services/dermatology/react_state.py`
- Test: `backend/test/test_react_agent.py`

**Step 1: 创建状态文件**

```python
# backend/app/services/dermatology/react_state.py
"""
ReAct Agent 状态定义

基于 LangGraph ReAct 模式的皮肤科智能体状态
"""
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class DermaReActState(TypedDict):
    """皮肤科 ReAct Agent 状态"""
    # === 会话标识 ===
    session_id: str
    user_id: int
    
    # === 对话历史（LangGraph 自动管理）===
    messages: Annotated[List[BaseMessage], add_messages]
    
    # === 医学信息（LLM 提取并累积）===
    chief_complaint: str
    skin_location: str
    symptoms: List[str]
    duration: str
    
    # === 分析结果 ===
    skin_analyses: List[dict]
    knowledge_refs: List[dict]
    possible_conditions: List[dict]
    
    # === 输出控制 ===
    current_response: str
    quick_options: List[dict]
    
    # === 待处理附件 ===
    pending_attachments: List[dict]
    
    # === 诊断相关 ===
    risk_level: str
    care_advice: str
    need_offline_visit: bool


def create_react_initial_state(session_id: str, user_id: int) -> DermaReActState:
    """创建 ReAct Agent 初始状态"""
    return DermaReActState(
        session_id=session_id,
        user_id=user_id,
        messages=[],
        chief_complaint="",
        skin_location="",
        symptoms=[],
        duration="",
        skin_analyses=[],
        knowledge_refs=[],
        possible_conditions=[],
        current_response="",
        quick_options=[],
        pending_attachments=[],
        risk_level="low",
        care_advice="",
        need_offline_visit=False
    )
```

**Step 2: 编写测试文件骨架**

```python
# backend/test/test_react_agent.py
"""ReAct Agent 单元测试"""
import pytest
from app.services.dermatology.react_state import (
    DermaReActState,
    create_react_initial_state
)


class TestReActState:
    """状态定义测试"""
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        state = create_react_initial_state("test-session", 123)
        
        assert state["session_id"] == "test-session"
        assert state["user_id"] == 123
        assert state["messages"] == []
        assert state["chief_complaint"] == ""
        assert state["symptoms"] == []
        assert state["risk_level"] == "low"
```

**Step 3: 运行测试**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_agent.py::TestReActState::test_create_initial_state -v`

Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/dermatology/react_state.py backend/test/test_react_agent.py
git commit -m "feat(derma): add ReAct agent state definition"
```

---

## Task 2: 创建医疗工具定义

**Files:**
- Create: `backend/app/services/dermatology/react_tools.py`
- Modify: `backend/test/test_react_agent.py`

**Step 1: 创建工具定义文件**

```python
# backend/app/services/dermatology/react_tools.py
"""
皮肤科 ReAct Agent 工具定义

LLM 可调用的医疗工具集
"""
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..llm_provider import LLMProvider


class SkinAnalysisResult(BaseModel):
    """图片分析结果"""
    description: str = Field(description="皮损描述")
    morphology: str = Field(description="形态特征")
    color: str = Field(description="颜色特征")
    distribution: str = Field(description="分布特征")
    suggested_conditions: List[str] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    """诊断结果"""
    conditions: List[dict] = Field(default_factory=list)
    risk_level: str = Field(default="low")
    care_advice: str = Field(default="")
    need_offline_visit: bool = Field(default=False)


@tool
def analyze_skin_image(image_base64: str, chief_complaint: str = "") -> dict:
    """
    分析皮肤图片，识别皮损特征。
    
    Args:
        image_base64: 图片的 base64 编码（带 data:image 前缀）
        chief_complaint: 患者主诉，帮助分析
    
    Returns:
        包含皮损描述、形态、颜色、分布特征的分析结果
    """
    llm = LLMProvider.get_multimodal_llm()
    
    prompt = """你是皮肤科影像专家。分析皮肤照片，描述皮损特征。

分析要点：
- 形态：斑、丘疹、水疱、结节等
- 颜色：红、褐、紫、白等
- 分布：局限性、泛发性、对称性
- 边界：清楚或模糊

用简洁专业的语言描述。"""
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": image_base64}},
            {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{chief_complaint or '未说明'}"}
        ])
    ]
    
    response = llm.invoke(messages)
    
    return {
        "description": response.content,
        "type": "skin_analysis"
    }


@tool
def generate_diagnosis(
    symptoms: List[str],
    location: str,
    duration: str,
    additional_info: str = ""
) -> dict:
    """
    综合问诊信息生成初步诊断建议。
    
    Args:
        symptoms: 症状列表，如 ["瘙痒", "红斑", "脱皮"]
        location: 皮损部位，如 "面部" "手臂"
        duration: 持续时间，如 "三天" "一周"
        additional_info: 其他信息，如图片分析结果
    
    Returns:
        包含鉴别诊断、风险等级、护理建议的诊断结果
    """
    llm = LLMProvider.get_llm()
    
    prompt = f"""作为皮肤科专家，根据以下信息给出初步诊断建议：

症状：{', '.join(symptoms) if symptoms else '未明确'}
部位：{location or '未明确'}
持续时间：{duration or '未明确'}
{f'补充信息：{additional_info}' if additional_info else ''}

请给出：
1. 1-3个可能的诊断（按可能性排序）
2. 风险等级（low/medium/high/emergency）
3. 护理建议
4. 是否需要线下就诊

用自然语言回复，不要输出 JSON。"""
    
    response = llm.invoke(prompt)
    
    return {
        "diagnosis_text": response.content,
        "type": "diagnosis"
    }


def get_derma_tools():
    """获取皮肤科工具列表"""
    return [analyze_skin_image, generate_diagnosis]
```

**Step 2: 添加工具测试**

```python
# 在 backend/test/test_react_agent.py 中添加

class TestReActTools:
    """工具定义测试"""
    
    def test_tools_are_callable(self):
        """测试工具可调用"""
        from app.services.dermatology.react_tools import get_derma_tools
        
        tools = get_derma_tools()
        assert len(tools) == 2
        assert tools[0].name == "analyze_skin_image"
        assert tools[1].name == "generate_diagnosis"
    
    def test_tool_schemas(self):
        """测试工具 schema 正确"""
        from app.services.dermatology.react_tools import get_derma_tools
        
        tools = get_derma_tools()
        
        # 图片分析工具
        img_tool = tools[0]
        assert "image_base64" in str(img_tool.args_schema.schema())
        
        # 诊断工具
        diag_tool = tools[1]
        assert "symptoms" in str(diag_tool.args_schema.schema())
```

**Step 3: 运行测试**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_agent.py::TestReActTools -v`

Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/dermatology/react_tools.py backend/test/test_react_agent.py
git commit -m "feat(derma): add ReAct agent tools definition"
```

---

## Task 3: 创建 ReAct Agent 核心实现

**Files:**
- Create: `backend/app/services/dermatology/react_agent.py`
- Modify: `backend/test/test_react_agent.py`

**Step 1: 创建 Agent 核心文件**

```python
# backend/app/services/dermatology/react_agent.py
"""
皮肤科 ReAct Agent 核心实现

基于 LangGraph ReAct 模式：agent → should_continue → tools → agent
"""
import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage

from ..llm_provider import LLMProvider
from .react_state import DermaReActState, create_react_initial_state
from .react_tools import get_derma_tools


# System Prompt
DERMA_REACT_PROMPT = """你是一位经验丰富的皮肤科专家医生，正在与患者进行问诊对话。

## 角色定位
- 专业但亲和，用通俗易懂的语言
- 像真人医生一样自然对话

## 对话原则
1. 直接响应用户问题，不使用固定模板
2. 渐进式诊断：边问诊边给初步建议
3. 每次回复后追问 1-2 个关键问题
4. 需要时主动调用工具

## 信息收集要点
- 主诉：什么问题
- 部位：身体哪个位置
- 症状：红肿、瘙痒、疼痛、脱皮等
- 持续时间

## 可用工具
- analyze_skin_image: 分析皮肤图片
- generate_diagnosis: 生成诊断建议

## 输出要求
- 回复简洁自然（2-4句话）
- 识别危急情况立即建议就医"""


def _build_derma_react_graph():
    """构建皮肤科 ReAct Agent 状态图"""
    
    # 获取工具
    tools = get_derma_tools()
    tools_by_name = {tool.name: tool for tool in tools}
    
    # 绑定工具到 LLM
    llm = LLMProvider.get_llm()
    model_with_tools = llm.bind_tools(tools)
    
    def call_model(state: DermaReActState) -> Dict[str, Any]:
        """Agent 节点：调用 LLM"""
        system_message = SystemMessage(content=DERMA_REACT_PROMPT)
        
        # 构建消息列表
        messages = [system_message] + list(state["messages"])
        
        # 调用 LLM
        response = model_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    def tool_node(state: DermaReActState) -> Dict[str, Any]:
        """工具节点：执行工具调用"""
        outputs = []
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # 执行工具
                if tool_name in tools_by_name:
                    result = tools_by_name[tool_name].invoke(tool_args)
                    outputs.append(
                        ToolMessage(
                            content=json.dumps(result, ensure_ascii=False),
                            name=tool_name,
                            tool_call_id=tool_call["id"]
                        )
                    )
        
        return {"messages": outputs}
    
    def should_continue(state: DermaReActState) -> str:
        """判断是否继续执行工具"""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"
    
    # 构建状态图
    workflow = StateGraph(DermaReActState)
    
    # 添加节点
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # 设置入口
    workflow.add_edge(START, "agent")
    
    # 条件边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    # 工具执行后回到 agent
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


# 单例模式
_derma_react_graph = None


def get_derma_react_graph():
    """获取编译后的状态图（单例）"""
    global _derma_react_graph
    if _derma_react_graph is None:
        _derma_react_graph = _build_derma_react_graph()
    return _derma_react_graph


def reset_derma_react_graph():
    """重置状态图（用于测试）"""
    global _derma_react_graph
    _derma_react_graph = None
```

**Step 2: 添加 Agent 测试**

```python
# 在 backend/test/test_react_agent.py 中添加

class TestReActAgent:
    """Agent 核心测试"""
    
    def test_graph_builds(self):
        """测试图可以构建"""
        from app.services.dermatology.react_agent import (
            get_derma_react_graph,
            reset_derma_react_graph
        )
        
        reset_derma_react_graph()
        graph = get_derma_react_graph()
        
        assert graph is not None
    
    def test_graph_singleton(self):
        """测试图是单例"""
        from app.services.dermatology.react_agent import get_derma_react_graph
        
        graph1 = get_derma_react_graph()
        graph2 = get_derma_react_graph()
        
        assert graph1 is graph2
```

**Step 3: 运行测试**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_agent.py::TestReActAgent -v`

Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/dermatology/react_agent.py backend/test/test_react_agent.py
git commit -m "feat(derma): add ReAct agent core implementation"
```

---

## Task 4: 创建快捷选项生成器

**Files:**
- Create: `backend/app/services/dermatology/quick_options.py`
- Modify: `backend/test/test_react_agent.py`

**Step 1: 创建快捷选项生成器**

```python
# backend/app/services/dermatology/quick_options.py
"""
动态快捷选项生成器

根据 AI 回复生成相关的快捷回复选项
"""
from typing import List
from pydantic import BaseModel, Field

from ..llm_provider import LLMProvider


class QuickOptionsOutput(BaseModel):
    """快捷选项输出"""
    options: List[str] = Field(
        description="3-4个快捷回复选项，每个2-6个字",
        default_factory=list
    )


QUICK_OPTIONS_PROMPT = """根据医生的回复，生成 3-4 个快捷回复选项供患者选择。

医生回复：
{response}

要求：
- 每个选项 2-6 个字
- 与当前问题相关
- 覆盖常见回答
- 符合口语表达

示例：
- 医生问"症状持续多久了" → ["刚开始", "几天了", "一周以上", "很久了"]
- 医生问"有其他症状吗" → ["有瘙痒", "有疼痛", "有脱皮", "没有了"]

直接输出选项列表，不要解释。"""


def generate_quick_options(response: str) -> List[dict]:
    """
    根据 AI 回复生成快捷选项
    
    Args:
        response: AI 的回复文本
    
    Returns:
        快捷选项列表 [{"text": "选项", "value": "选项", "category": "reply"}]
    """
    if not response or len(response) < 10:
        return []
    
    try:
        llm = LLMProvider.get_llm()
        
        # 使用结构化输出
        structured_llm = llm.with_structured_output(QuickOptionsOutput)
        
        prompt = QUICK_OPTIONS_PROMPT.format(response=response)
        result = structured_llm.invoke(prompt)
        
        return [
            {"text": opt, "value": opt, "category": "reply"}
            for opt in result.options[:4]  # 最多4个
        ]
    except Exception:
        # 降级：返回默认选项
        return [
            {"text": "好的", "value": "好的", "category": "reply"},
            {"text": "还有问题", "value": "我还有问题", "category": "reply"},
        ]
```

**Step 2: 添加测试**

```python
# 在 backend/test/test_react_agent.py 中添加

class TestQuickOptions:
    """快捷选项测试"""
    
    def test_empty_response(self):
        """测试空回复返回空列表"""
        from app.services.dermatology.quick_options import generate_quick_options
        
        result = generate_quick_options("")
        assert result == []
    
    def test_short_response(self):
        """测试过短回复返回空列表"""
        from app.services.dermatology.quick_options import generate_quick_options
        
        result = generate_quick_options("你好")
        assert result == []
```

**Step 3: 运行测试**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_agent.py::TestQuickOptions -v`

Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/dermatology/quick_options.py backend/test/test_react_agent.py
git commit -m "feat(derma): add dynamic quick options generator"
```

---

## Task 5: 创建 API 适配层

**Files:**
- Create: `backend/app/services/dermatology/react_wrapper.py`
- Modify: `backend/test/test_react_agent.py`

**Step 1: 创建适配器**

```python
# backend/app/services/dermatology/react_wrapper.py
"""
ReAct Agent API 适配层

实现 BaseAgent 接口，保持与现有 API 兼容
"""
from typing import Dict, Any, Optional, Callable, Awaitable, List
from langchain_core.messages import HumanMessage, AIMessage

from ..base import BaseAgent
from .react_state import create_react_initial_state
from .react_agent import get_derma_react_graph
from .quick_options import generate_quick_options


def _serialize_messages(messages: list) -> List[dict]:
    """序列化消息为 JSON 格式"""
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        elif hasattr(msg, "content"):
            role = "assistant" if getattr(msg, "type", "") == "ai" else "user"
            if hasattr(msg, "type") and msg.type == "system":
                continue  # 跳过 system 消息
            if hasattr(msg, "type") and msg.type == "tool":
                continue  # 跳过 tool 消息
            serialized.append({
                "role": role,
                "content": msg.content
            })
    return serialized


class DermaReActWrapper(BaseAgent):
    """
    皮肤科 ReAct Agent 适配器
    
    实现 BaseAgent 接口，内部使用 ReAct 模式
    """
    
    def __init__(self):
        self._graph = get_derma_react_graph()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        state = create_react_initial_state(session_id, user_id)
        # 转换为普通 dict
        return dict(state)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        
        # 添加用户消息
        if user_input:
            state["messages"].append(HumanMessage(content=user_input))
        
        # 处理附件（图片）
        if attachments:
            for att in attachments:
                att_type = att.get("type", "")
                if att_type == "image" or att_type.startswith("image/"):
                    state["pending_attachments"].append(att)
        
        # 运行状态图
        if on_chunk:
            final_state = await self._run_with_stream(state, on_chunk)
        else:
            final_state = await self._graph.ainvoke(state)
        
        # 提取最后的 AI 回复
        ai_response = ""
        for msg in reversed(final_state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                ai_response = msg.content
                break
            elif isinstance(msg, AIMessage):
                ai_response = msg.content
                break
        
        final_state["current_response"] = ai_response
        
        # 生成快捷选项
        if ai_response:
            final_state["quick_options"] = generate_quick_options(ai_response)
        
        # 序列化消息
        final_state["messages"] = _serialize_messages(final_state.get("messages", []))
        
        return final_state
    
    async def _run_with_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Callable[[str], Awaitable[None]]
    ) -> Dict[str, Any]:
        """流式输出运行"""
        final_state = state.copy()
        
        async for event in self._graph.astream_events(state, version="v2"):
            if event.get("event") == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    await on_chunk(chunk.content)
            elif event.get("event") == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict):
                    final_state = output
        
        return final_state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return {
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png"],
            "ui_components": ["TextBubble", "SkinAnalysisCard"],
            "description": "皮肤科 ReAct AI 智能体"
        }
```

**Step 2: 添加适配器测试**

```python
# 在 backend/test/test_react_agent.py 中添加
import pytest

class TestReActWrapper:
    """适配器测试"""
    
    @pytest.mark.asyncio
    async def test_create_initial_state(self):
        """测试创建初始状态"""
        from app.services.dermatology.react_wrapper import DermaReActWrapper
        
        wrapper = DermaReActWrapper()
        state = await wrapper.create_initial_state("test-session", 123)
        
        assert state["session_id"] == "test-session"
        assert state["user_id"] == 123
        assert isinstance(state["messages"], list)
    
    def test_get_capabilities(self):
        """测试获取能力"""
        from app.services.dermatology.react_wrapper import DermaReActWrapper
        
        wrapper = DermaReActWrapper()
        caps = wrapper.get_capabilities()
        
        assert "conversation" in caps["actions"]
        assert "image/jpeg" in caps["accepts_media"]
```

**Step 3: 运行测试**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_agent.py::TestReActWrapper -v`

Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/dermatology/react_wrapper.py backend/test/test_react_agent.py
git commit -m "feat(derma): add ReAct agent API wrapper"
```

---

## Task 6: 更新模块导出

**Files:**
- Modify: `backend/app/services/dermatology/__init__.py`

**Step 1: 更新 __init__.py**

```python
# backend/app/services/dermatology/__init__.py
"""
皮肤科智能体模块

提供多种实现：
- DermaAgentWrapper: CrewAI 实现（旧）
- DermaLangGraphWrapper: LangGraph 状态机实现（过渡）
- DermaReActWrapper: LangGraph ReAct 实现（新）
"""
from .derma_wrapper import DermaAgentWrapper
from .derma_langgraph_wrapper import DermaLangGraphWrapper
from .react_wrapper import DermaReActWrapper
from .derma_agent import DermaTaskType, create_derma_initial_state

# 默认使用 ReAct 实现
DermaAgent = DermaReActWrapper

__all__ = [
    "DermaAgent",
    "DermaAgentWrapper",
    "DermaLangGraphWrapper",
    "DermaReActWrapper",
    "DermaTaskType",
    "create_derma_initial_state"
]
```

**Step 2: 运行所有测试确认不破坏现有功能**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_agent.py -v`

Expected: All PASS

**Step 3: Commit**

```bash
git add backend/app/services/dermatology/__init__.py
git commit -m "feat(derma): export ReAct agent as default"
```

---

## Task 7: 端到端集成测试

**Files:**
- Create: `backend/test/test_react_e2e.py`

**Step 1: 创建端到端测试**

```python
# backend/test/test_react_e2e.py
"""ReAct Agent 端到端测试"""
import pytest
from app.services.dermatology import DermaAgent


class TestReActE2E:
    """端到端测试"""
    
    @pytest.mark.asyncio
    async def test_simple_conversation(self):
        """测试简单对话"""
        agent = DermaAgent()
        
        # 创建初始状态
        state = await agent.create_initial_state("e2e-test", 1)
        
        # 发送第一条消息
        state = await agent.run(
            state=state,
            user_input="我脸上长痘痘了"
        )
        
        # 验证有回复
        assert state["current_response"]
        assert len(state["current_response"]) > 10
        
        # 验证有快捷选项
        assert isinstance(state["quick_options"], list)
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """测试多轮对话"""
        agent = DermaAgent()
        
        state = await agent.create_initial_state("e2e-test-2", 1)
        
        # 第一轮
        state = await agent.run(state=state, user_input="皮肤很痒")
        assert state["current_response"]
        
        # 第二轮
        state = await agent.run(state=state, user_input="手臂上")
        assert state["current_response"]
        
        # 验证消息历史
        assert len(state["messages"]) >= 4  # user + ai + user + ai
```

**Step 2: 运行端到端测试**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && python -m pytest test/test_react_e2e.py -v --timeout=60`

Expected: PASS（需要 LLM API 连接）

**Step 3: Commit**

```bash
git add backend/test/test_react_e2e.py
git commit -m "test(derma): add ReAct agent e2e tests"
```

---

## 实施清单

| Task | 描述 | 预估时间 |
|------|------|----------|
| Task 1 | 创建状态定义 | 15 min |
| Task 2 | 创建工具定义 | 30 min |
| Task 3 | 创建 Agent 核心 | 45 min |
| Task 4 | 创建快捷选项生成器 | 20 min |
| Task 5 | 创建 API 适配层 | 30 min |
| Task 6 | 更新模块导出 | 10 min |
| Task 7 | 端到端测试 | 20 min |

**总预估时间**: ~3 小时

---

## 后续扩展（Phase 2）

完成核心实现后，可以继续：

1. **RAG 知识库集成**
   - 添加 `search_medical_knowledge` 工具
   - 集成向量数据库（Chroma/Pinecone）
   - 实现"院士团队解读"卡片格式

2. **图片处理优化**
   - 自动从 pending_attachments 触发图片分析
   - 多图片批量处理

3. **性能优化**
   - Prompt 缓存
   - 并行工具调用
