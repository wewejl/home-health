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

## 可用工具及使用时机

### 1. analyze_skin_image
- **用途**: 分析皮肤图片
- **时机**: 用户上传皮肤照片时

### 2. retrieve_derma_knowledge
- **用途**: 检索皮肤科医学知识库
- **时机**: 收集到症状后，生成诊断前
- **参数**: symptoms（症状列表）, location（部位）, query（补充查询词）
- **返回**: 相关医学知识引用列表

### 3. generate_structured_diagnosis
- **用途**: 生成结构化诊断卡
- **时机**: 收集完主要信息（主诉、部位、症状、持续时间）后
- **参数**: symptoms, location, duration, knowledge_refs（来自步骤2）, additional_info
- **返回**: 包含鉴别诊断、风险等级、护理建议的结构化诊断卡

### 4. generate_diagnosis (旧工具，保留兼容)
- **用途**: 生成文本诊断建议
- **时机**: 快速给出初步建议时使用

## 诊断工作流（重要）

当收集完以下信息后，按顺序调用工具：
1. 主诉（chief_complaint）
2. 部位（skin_location）
3. 症状列表（symptoms，至少2个）
4. 持续时间（duration）

**标准流程**:
```
步骤1: 调用 retrieve_derma_knowledge(symptoms=症状列表, location=部位)
步骤2: 调用 generate_structured_diagnosis(
    symptoms=症状列表,
    location=部位,
    duration=持续时间,
    knowledge_refs=步骤1的结果
)
```

## 输出要求
- 回复简洁自然（2-4句话）
- 识别危急情况立即建议就医
- 调用工具后，基于结果给出专业建议"""


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
        import uuid
        from datetime import datetime
        
        system_message = SystemMessage(content=DERMA_REACT_PROMPT)
        
        # 构建消息列表
        messages = [system_message] + list(state["messages"])
        
        # 调用 LLM
        response = model_with_tools.invoke(messages)
        
        updates = {"messages": [response]}
        
        # 如果 Agent 给出了建议（没有调用工具），提取为中间建议
        if isinstance(response, AIMessage) and not response.tool_calls:
            content = response.content
            # 简单判断：如果回复包含建议关键词
            if any(keyword in content for keyword in ["建议", "可以", "应该", "注意", "避免", "推荐"]):
                advice_entry = {
                    "id": str(uuid.uuid4()),
                    "title": "护理建议",
                    "content": content,
                    "evidence": [],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                advice_history = state.get("advice_history", [])
                updates["advice_history"] = advice_history + [advice_entry]
        
        return updates
    
    def tool_node(state: DermaReActState) -> Dict[str, Any]:
        """工具节点：执行工具调用并更新状态"""
        outputs = []
        updates = {}  # 用于收集 state 更新
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # 执行工具
                if tool_name in tools_by_name:
                    result = tools_by_name[tool_name].invoke(tool_args)
                    
                    # 根据工具类型更新 state
                    if tool_name == "retrieve_derma_knowledge":
                        # 更新知识引用
                        if isinstance(result, list):
                            updates["knowledge_refs"] = result
                            # 同时添加到推理步骤
                            current_steps = state.get("reasoning_steps", [])
                            updates["reasoning_steps"] = current_steps + [
                                f"检索到 {len(result)} 条相关医学知识"
                            ]
                    
                    elif tool_name == "generate_structured_diagnosis":
                        # 更新诊断卡
                        if isinstance(result, dict):
                            updates["diagnosis_card"] = result
                            # 更新推理步骤
                            if "reasoning_steps" in result:
                                current_steps = state.get("reasoning_steps", [])
                                updates["reasoning_steps"] = current_steps + result["reasoning_steps"]
                            # 更新风险等级和就诊建议
                            if "risk_level" in result:
                                updates["risk_level"] = result["risk_level"]
                            if "need_offline_visit" in result:
                                updates["need_offline_visit"] = result["need_offline_visit"]
                    
                    elif tool_name == "analyze_skin_image":
                        # 保持原有逻辑
                        if isinstance(result, dict) and "analysis" in result:
                            skin_analyses = state.get("skin_analyses", [])
                            updates["skin_analyses"] = skin_analyses + [result]
                    
                    # 添加工具消息
                    outputs.append(
                        ToolMessage(
                            content=json.dumps(result, ensure_ascii=False),
                            name=tool_name,
                            tool_call_id=tool_call["id"]
                        )
                    )
        
        # 返回消息和状态更新
        return {"messages": outputs, **updates}
    
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
