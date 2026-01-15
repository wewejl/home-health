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
