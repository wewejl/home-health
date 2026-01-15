"""
皮肤科 LangGraph Agent

基于 LangGraph 1.x 实现的高性能皮肤科智能体
- 图结构复用，避免重复编译
- 精简 Prompt，降低 Token 消耗
- 流式输出支持
"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from ..base.langgraph_base import LangGraphAgentBase
from ..llm_provider import LLMProvider
from .derma_state import DermaState, create_derma_initial_state
from .output_models import ConversationOutput, DiagnosisOutput
from .prompts import (
    DERMA_CONVERSATION_PROMPT,
    DERMA_IMAGE_ANALYSIS_PROMPT,
    DERMA_DIAGNOSIS_PROMPT,
    DERMA_GREETING_TEMPLATE,
    DERMA_QUICK_OPTIONS_GREETING,
    DERMA_QUICK_OPTIONS_COLLECTING,
    DERMA_QUICK_OPTIONS_DIAGNOSIS,
)


def _get_message_content(msg) -> str:
    """安全提取消息内容，兼容 dict 和 LangChain Message 对象"""
    if isinstance(msg, dict):
        return msg.get("content", "")
    elif hasattr(msg, "content"):
        return msg.content
    return str(msg)


def _get_message_role(msg) -> str:
    """安全提取消息角色，兼容 dict 和 LangChain Message 对象"""
    if isinstance(msg, dict):
        return msg.get("role", "")
    elif hasattr(msg, "type"):
        # LangChain message types: human, ai, system
        return "assistant" if msg.type == "ai" else msg.type
    return ""


class DermaLangGraphAgent(LangGraphAgentBase):
    """
    皮肤科 LangGraph Agent
    
    状态图结构：
        START -> router -> greeting/conversation/image_analysis/diagnosis -> END
    
    性能优化：
        - 问候节点无需 LLM 调用
        - 图结构类级别缓存
        - LLM 实例复用
    """
    
    def _create_initial_state(self, session_id: str, user_id: int) -> DermaState:
        """创建皮肤科初始状态"""
        return create_derma_initial_state(session_id, user_id)
    
    def _build_graph(self) -> StateGraph:
        """构建皮肤科状态图"""
        graph = StateGraph(DermaState)
        
        # 添加节点
        graph.add_node("router", self._route_node)
        graph.add_node("greeting", self._greeting_node)
        graph.add_node("conversation", self._conversation_node)
        graph.add_node("image_analysis", self._image_analysis_node)
        graph.add_node("diagnosis", self._diagnosis_node)
        
        # 设置入口点
        graph.add_edge(START, "router")
        
        # 路由条件边
        graph.add_conditional_edges(
            "router",
            self._get_next_node,
            {
                "greeting": "greeting",
                "conversation": "conversation",
                "image_analysis": "image_analysis",
                "diagnosis": "diagnosis",
                "end": END
            }
        )
        
        # 节点后续流转 - 都回到 END
        graph.add_edge("greeting", END)
        graph.add_edge("conversation", END)
        graph.add_edge("image_analysis", END)
        graph.add_edge("diagnosis", END)
        
        return graph.compile()
    
    # === 路由逻辑 ===
    
    def _route_node(self, state: DermaState) -> DermaState:
        """路由决策节点"""
        # 新会话 -> 问候
        if state["stage"] == "greeting" and state["questions_asked"] == 0:
            has_history = any(_get_message_role(m) == "assistant" for m in state["messages"])
            if not has_history:
                state["next_node"] = "greeting"
                return state
        
        # 有待处理图片 -> 图片分析
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
    
    def _get_next_node(self, state: DermaState) -> str:
        """返回下一个节点名称"""
        return state.get("next_node", "conversation")
    
    def _should_diagnose(self, state: DermaState) -> bool:
        """判断是否应该给出诊断"""
        if not state["messages"]:
            return False
            
        last_msg = _get_message_content(state["messages"][-1]) if state["messages"] else ""
        
        # 用户明确请求诊断
        diagnosis_keywords = ["怎么办", "是什么", "什么病", "建议", "严重吗", "需要治疗", "用什么药"]
        user_wants_diagnosis = any(kw in last_msg for kw in diagnosis_keywords)
        
        # 信息足够
        has_enough_info = (
            bool(state.get("chief_complaint")) and
            bool(state.get("skin_location")) and
            len(state.get("symptoms", [])) >= 1
        )
        
        # 对话足够长
        enough_rounds = state["questions_asked"] >= 3
        
        return user_wants_diagnosis or (has_enough_info and enough_rounds)
    
    # === 节点实现 ===
    
    async def _greeting_node(self, state: DermaState) -> DermaState:
        """问候节点 - 无需 LLM 调用，快速响应"""
        state["current_response"] = DERMA_GREETING_TEMPLATE
        state["stage"] = "collecting"
        state["quick_options"] = DERMA_QUICK_OPTIONS_GREETING
        state["next_node"] = "end"
        return state
    
    async def _conversation_node(self, state: DermaState) -> DermaState:
        """对话节点 - 问诊收集信息"""
        llm = LLMProvider.get_llm()
        
        # 获取最新用户输入
        user_input = ""
        if state["messages"]:
            user_input = _get_message_content(state["messages"][-1])
        
        # 构建 Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", DERMA_CONVERSATION_PROMPT),
            ("human", """问诊信息：
- 主诉: {chief_complaint}
- 部位: {skin_location}
- 症状: {symptoms}
- 已问诊 {questions_asked} 轮

用户说：{user_input}

请继续问诊或给出建议。输出 JSON 格式：
{{"message": "你的回复", "next_action": "continue或complete", "extracted_info": {{"chief_complaint": "", "skin_location": "", "duration": "", "symptoms": []}}, "quick_options": [{{"text": "选项文本", "value": "选项值", "category": "类别"}}]}}""")
        ])
        
        try:
            # 使用结构化输出
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
            state["quick_options"] = result.quick_options or DERMA_QUICK_OPTIONS_COLLECTING
            state["questions_asked"] += 1
            
            # 更新医学信息
            if result.extracted_info:
                self._update_medical_info(state, result.extracted_info)
            
            # 下一步
            if result.next_action == "complete":
                state["next_node"] = "diagnosis"
                state["stage"] = "diagnosis"
            else:
                state["next_node"] = "end"
                
        except Exception as e:
            # 降级处理：直接使用 LLM
            state["current_response"] = "请继续描述您的症状，我会帮您分析。"
            state["quick_options"] = DERMA_QUICK_OPTIONS_COLLECTING
            state["questions_asked"] += 1
            state["next_node"] = "end"
        
        return state
    
    async def _image_analysis_node(self, state: DermaState) -> DermaState:
        """图片分析节点 - 多模态 LLM"""
        llm = LLMProvider.get_multimodal_llm()
        
        # 获取待处理图片
        if not state["pending_attachments"]:
            state["current_response"] = "没有检测到图片，请上传皮肤问题的照片。"
            state["next_node"] = "end"
            return state
        
        attachment = state["pending_attachments"].pop(0)
        image_base64 = attachment.get("base64", "")
        
        # 确保 base64 格式正确
        if image_base64 and not image_base64.startswith("data:"):
            image_base64 = f"data:image/jpeg;base64,{image_base64}"
        
        try:
            # 构建多模态消息
            messages = [
                SystemMessage(content=DERMA_IMAGE_ANALYSIS_PROMPT),
                HumanMessage(content=[
                    {"type": "image_url", "image_url": {"url": image_base64}},
                    {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{state.get('chief_complaint') or '未说明'}"}
                ])
            ]
            
            response = await llm.ainvoke(messages)
            
            # 解析结果
            analysis = {
                "message": response.content,
                "type": "image_analysis",
                "attachment_id": attachment.get("id", "")
            }
            
            # 更新状态
            state["skin_analyses"].append(analysis)
            state["latest_analysis"] = analysis
            state["current_response"] = response.content
            state["processed_results"].append({
                "type": "image_analysis",
                "result": analysis
            })
            state["stage"] = "analyzing"
            
        except Exception as e:
            state["current_response"] = f"图片分析时出现问题，请尝试重新上传清晰的照片。"
            state["error"] = str(e)
        
        state["next_node"] = "end"
        return state
    
    async def _diagnosis_node(self, state: DermaState) -> DermaState:
        """诊断节点 - 综合分析给出建议"""
        llm = LLMProvider.get_llm()
        
        # 获取图片分析结果
        image_analysis_text = ""
        if state.get("skin_analyses"):
            image_analysis_text = state["skin_analyses"][-1].get("message", "")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", DERMA_DIAGNOSIS_PROMPT),
            ("human", """请根据以下信息给出诊断建议：

- 主诉: {chief_complaint}
- 部位: {skin_location}
- 持续时间: {duration}
- 症状: {symptoms}
- 图片分析: {image_analysis}

输出 JSON 格式：
{{"diagnosis_message": "诊断说明", "conditions": [{{"name": "疾病名", "probability": "likely/possible/unlikely", "basis": "依据"}}], "risk_level": "low/medium/high/emergency", "care_advice": "护理建议", "treatment_suggestions": ["建议1"], "need_offline_visit": false, "follow_up_days": 7}}""")
        ])
        
        try:
            chain = prompt | llm.with_structured_output(DiagnosisOutput)
            
            result = await chain.ainvoke({
                "chief_complaint": state.get("chief_complaint", "") or "未明确",
                "skin_location": state.get("skin_location", "") or "未明确",
                "duration": state.get("duration", "") or "未明确",
                "symptoms": ", ".join(state.get("symptoms", [])) or "未明确",
                "image_analysis": image_analysis_text or "无图片分析"
            })
            
            # 格式化诊断信息为用户友好的文本
            formatted_response = self._format_diagnosis_response(result)
            
            # 更新状态
            state["current_response"] = formatted_response
            state["possible_conditions"] = [c.model_dump() for c in result.conditions]
            state["risk_level"] = result.risk_level
            state["care_advice"] = result.care_advice
            state["need_offline_visit"] = result.need_offline_visit
            state["stage"] = "completed"
            state["quick_options"] = DERMA_QUICK_OPTIONS_DIAGNOSIS
            
        except Exception as e:
            state["current_response"] = "根据您提供的信息，建议您到皮肤科就诊获得更准确的诊断。"
            state["stage"] = "completed"
            state["error"] = str(e)
        
        state["next_node"] = "end"
        return state
    
    # === 辅助方法 ===
    
    def _format_diagnosis_response(self, result: DiagnosisOutput) -> str:
        """
        将结构化诊断结果格式化为用户友好的文本
        
        避免直接显示 JSON 格式，提供清晰的诊断说明
        """
        lines = []
        
        # 诊断说明
        if result.diagnosis_message:
            lines.append(result.diagnosis_message)
            lines.append("")
        
        # 可能的诊断
        if result.conditions:
            lines.append("**可能的诊断：**")
            for condition in result.conditions:
                probability_text = {
                    "likely": "较可能",
                    "possible": "可能",
                    "unlikely": "不太可能"
                }.get(condition.probability, condition.probability)
                
                lines.append(f"\n• **{condition.name}**（{probability_text}）")
                lines.append(f"  依据：{condition.basis}")
            lines.append("")
        
        # 护理建议
        if result.care_advice:
            lines.append("**护理建议：**")
            lines.append(result.care_advice)
            lines.append("")
        
        # 治疗建议
        if result.treatment_suggestions:
            lines.append("**治疗建议：**")
            for suggestion in result.treatment_suggestions:
                lines.append(f"• {suggestion}")
            lines.append("")
        
        # 就医提醒
        if result.need_offline_visit:
            risk_emoji = {
                "emergency": "🚨",
                "high": "⚠️",
                "medium": "ℹ️",
                "low": "💡"
            }.get(result.risk_level, "ℹ️")
            
            lines.append(f"{risk_emoji} **重要提醒：**")
            lines.append("建议您尽快到皮肤科就诊，获得专业医生的面诊和确诊。")
            
            if result.follow_up_days:
                lines.append(f"建议 {result.follow_up_days} 天内复诊。")
        
        return "\n".join(lines)
    
    def _update_medical_info(self, state: DermaState, extracted_info: Dict[str, Any]):
        """更新医学信息"""
        if extracted_info.get("chief_complaint"):
            state["chief_complaint"] = extracted_info["chief_complaint"]
        
        if extracted_info.get("skin_location"):
            state["skin_location"] = extracted_info["skin_location"]
        
        if extracted_info.get("duration"):
            state["duration"] = extracted_info["duration"]
        
        if extracted_info.get("symptoms"):
            for symptom in extracted_info["symptoms"]:
                if symptom and symptom not in state["symptoms"]:
                    state["symptoms"].append(symptom)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return {
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "SkinAnalysisCard", "ReportInterpretationCard"],
            "description": "皮肤科AI智能体（LangGraph），支持皮肤影像分析和报告解读"
        }
