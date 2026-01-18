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

## 核心原则
- **像真实医生一样直接**：不要过度礼貌，直接追问病情
- **不要使用"请问"等礼貌用语**：直接问问题
- **用通俗易懂的语言**：避免过于专业的术语

## 问诊流程

### 第一步：直接追问症状细节（前2-3轮）
- **不要**：请问您的症状是什么？
- **要**：这个瘙痒是从什么时候开始的？有没有出现红肿、皮疹、脱皮或其他异常表现？
- **风格**：直接问问题，每次1-2个问题，不要一次问太多

### 第二步：给出医学分析 + 继续追问（收集到关键信息后）
- **先给分析**：根据您的描述，龟头部位有长期瘙痒并伴有白色分泌物，这种情况可能与真菌感染（如念珠菌性龟头炎）、细菌感染或其他皮肤问题有关。
- **再追问**：这些分泌物是否有异味？是否有红斑、糜烂或皮肤破损？您是否有过不洁的性接触史，或近期使用抗生素、激素类药物？

### 第三步：最终诊断（收集完整信息后）
- **触发条件**：用户主动要求总结，或已收集完整信息（部位、症状、持续时间、诱因等）
- **使用工具**：调用 generate_structured_diagnosis 生成结构化诊断

## 必须收集的信息
1. 症状：具体是什么不适（瘙痒、疼痛、红肿等）
2. 部位：身体哪个位置
3. 持续时间：多久了
4. 伴随症状：有没有分泌物、异味、破损等
5. 诱因：接触过什么、用过什么药、性接触史等

## 可用工具

### 1. analyze_skin_image
- **用途**: 分析皮肤图片
- **时机**: 用户上传皮肤照片时

### 2. retrieve_derma_knowledge
- **用途**: 检索皮肤科医学知识库
- **时机**: 需要医学知识支持时（可选）

### 3. generate_structured_diagnosis
- **用途**: 生成最终结构化诊断报告
- **时机**: **仅在用户明确要求总结/生成诊断报告时调用**
- **重要**: 信息收集阶段不要调用

## 输出格式要求
- **不要使用 Markdown 格式**：不要用 ###、**、- 等符号
- **直接用自然语言**：用换行和空行分段即可
- **分段清晰**：医学分析一段，追问问题另起一段
- 识别危急情况立即建议就医
- 不要透露自己使用的底层模型或服务提供商"""


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
        """工具节点：执行工具调用并更新状态"""
        outputs = []
        updates = {}  # 用于收集 state 更新
        last_message = state["messages"][-1]
        
        # === 调试日志：工具调用 ===
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print(f"[DEBUG] tool_node 收到工具调用: {len(last_message.tool_calls)} 个")
            for tc in last_message.tool_calls:
                print(f"[DEBUG] - 工具名称: {tc['name']}")
                print(f"[DEBUG] - 工具参数: {tc['args']}")
        else:
            print(f"[DEBUG] tool_node: 没有工具调用")
        # === 日志结束 ===
        
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
                            # === 调试日志：诊断工具结果 ===
                            summary_preview = result.get('summary', 'N/A')[:50] if result.get('summary') else 'N/A'
                            print(f"[DEBUG] generate_structured_diagnosis 返回:")
                            print(f"[DEBUG] - summary: {summary_preview}...")
                            print(f"[DEBUG] - conditions: {len(result.get('conditions', []))} 个")
                            print(f"[DEBUG] - risk_level: {result.get('risk_level', 'N/A')}")
                            # === 日志结束 ===
                            
                            updates["diagnosis_card"] = result
                            
                            # === 调试日志：state 更新 ===
                            print(f"[DEBUG] 已更新 state['diagnosis_card']")
                            print(f"[DEBUG] - 包含字段: {list(result.keys())}")
                            # === 日志结束 ===
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
                    
                    elif tool_name == "record_intermediate_advice":
                        # 记录中间建议
                        if isinstance(result, dict):
                            # === 调试日志：中间建议 ===
                            content_preview = result.get('content', 'N/A')[:50] if result.get('content') else 'N/A'
                            print(f"[DEBUG] record_intermediate_advice 返回:")
                            print(f"[DEBUG] - title: {result.get('title', 'N/A')}")
                            print(f"[DEBUG] - content: {content_preview}...")
                            # === 日志结束 ===
                            
                            advice_history = state.get("advice_history", [])
                            updates["advice_history"] = advice_history + [result]
                            
                            # === 调试日志：state 更新 ===
                            print(f"[DEBUG] 已更新 state['advice_history'], 当前数量: {len(updates['advice_history'])}")
                            # === 日志结束 ===
                            # 同步推理步骤
                            current_steps = state.get("reasoning_steps", [])
                            updates["reasoning_steps"] = current_steps + [
                                f"记录护理建议: {result.get('title', '未命名')}"
                            ]
                    
                    # 添加工具消息
                    # 针对不同工具类型，返回简短确认消息（避免 JSON 被流式输出给前端）
                    if tool_name == "generate_structured_diagnosis":
                        # 诊断工具：只返回简短确认，避免 AI 输出完整 JSON
                        tool_message_content = "已生成结构化诊断报告，包含鉴别诊断、风险评估和护理建议。请用自然语言向患者解释诊断结果和建议。"
                    elif tool_name == "record_intermediate_advice":
                        # 中间建议：简短确认
                        tool_message_content = f"已记录护理建议：{result.get('title', '未命名')}"
                    elif tool_name == "analyze_skin_image":
                        # 图片分析：返回分析描述文本，不是 JSON
                        description = result.get('description', '图片分析完成')
                        tool_message_content = f"皮肤图片分析完成。分析结果：{description}"
                    elif tool_name == "retrieve_derma_knowledge":
                        # 知识检索：返回简短摘要
                        if isinstance(result, list) and len(result) > 0:
                            titles = [ref.get('title', '') for ref in result[:3] if ref.get('title')]
                            tool_message_content = f"已检索到 {len(result)} 条相关医学知识：{', '.join(titles)}"
                        else:
                            tool_message_content = "未找到相关医学知识。"
                    elif tool_name == "generate_diagnosis":
                        # 普通诊断：返回诊断文本
                        diagnosis_text = result.get('diagnosis_text', '诊断生成完成')
                        tool_message_content = diagnosis_text
                    else:
                        # 其他未知工具：返回简短确认而非 JSON
                        tool_message_content = f"工具 {tool_name} 执行完成。"
                    
                    outputs.append(
                        ToolMessage(
                            content=tool_message_content,
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
