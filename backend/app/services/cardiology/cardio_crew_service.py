"""
CardioCrewService - CrewAI 1.x 心血管内科问诊服务
支持：症状问诊、心电图解读、风险评估
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime

from crewai import Crew, Process

from ...config import get_settings
from .cardio_agents import (
    create_cardio_conversation_agent,
    create_cardio_ecg_interpreter,
    create_cardio_risk_assessor,
    create_cardio_conversation_task,
    create_ecg_interpretation_task,
    create_risk_assessment_task,
    create_llm,
)

settings = get_settings()


class CardioCrewService:
    """
    心血管内科 CrewAI 1.x 编排服务
    
    负责：
    1. 初始化心血管内科专业 Agents
    2. 调用 Crew 执行问诊、解读、评估任务
    3. 管理状态与流式输出
    """
    
    def __init__(self):
        self.llm = self._build_llm()
        self._conversation_agent = None
        self._ecg_interpreter = None
        self._risk_assessor = None
        print("[CardioCrewService] Initialized with CrewAI multi-agent architecture")
    
    def _build_llm(self):
        """构建 LLM 实例"""
        return create_llm()
    
    @property
    def conversation_agent(self):
        if self._conversation_agent is None:
            self._conversation_agent = create_cardio_conversation_agent(self.llm)
        return self._conversation_agent
    
    @property
    def ecg_interpreter(self):
        if self._ecg_interpreter is None:
            self._ecg_interpreter = create_cardio_ecg_interpreter(self.llm)
        return self._ecg_interpreter
    
    @property
    def risk_assessor(self):
        if self._risk_assessor is None:
            self._risk_assessor = create_cardio_risk_assessor(self.llm)
        return self._risk_assessor
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        task_type: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行心血管问诊任务
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            image_url: 心电图图片 URL
            image_base64: 心电图图片 Base64
            task_type: 任务类型 (conversation, interpret_ecg, risk_assessment)
            on_chunk: 流式输出回调
        """
        # 新会话问候
        has_assistant_history = any(msg.get("role") == "assistant" for msg in state.get("messages", []))
        if state.get("stage") == "greeting" and not has_assistant_history:
            return await self._handle_greeting(state, on_chunk)
        
        # 如果 stage 还是 greeting 但已有历史，切换到 collecting
        if state.get("stage") == "greeting":
            state["stage"] = "collecting"
        
        # 根据任务类型分发
        if task_type == "interpret_ecg" and (image_url or image_base64 or user_input):
            return await self._handle_ecg_interpretation(state, user_input, image_url, image_base64, on_chunk)
        
        if task_type == "risk_assessment":
            return await self._handle_risk_assessment(state, on_chunk)
        
        # 默认处理文本对话
        if user_input:
            return await self._handle_conversation(state, user_input, on_chunk)
        
        return state
    
    async def _handle_greeting(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理问候"""
        greeting = """你好~我是你的心血管内科AI助手。我可以帮助你：
• 了解心脏相关症状（胸痛、心悸、呼吸困难等）
• 解读心电图报告
• 评估心血管风险

请告诉我你目前的症状或想咨询的问题，我会一步步和你沟通。

⚠️ 提醒：如果你正在经历持续性胸痛、严重呼吸困难或晕厥，请立即拨打120急救电话。"""
        
        state["current_response"] = greeting
        state["stage"] = "collecting"
        state["messages"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "胸痛/胸闷", "value": "我有胸痛或胸闷的症状", "category": "症状"},
            {"text": "心悸心慌", "value": "我经常感到心跳加快或心慌", "category": "症状"},
            {"text": "呼吸困难", "value": "我有时感到呼吸困难", "category": "症状"},
            {"text": "解读心电图", "value": "我想解读一下心电图报告", "category": "功能"},
            {"text": "风险评估", "value": "我想评估一下心血管风险", "category": "功能"}
        ]
        
        if on_chunk:
            for char in greeting:
                await on_chunk(char)
        
        return state
    
    async def _handle_conversation(
        self,
        state: Dict[str, Any],
        user_input: str,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理对话"""
        # 记录用户消息
        state["messages"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 使用 CrewAI 处理对话
        result = await self._run_conversation_crew(state, user_input)
        
        # 更新状态
        response = result.get("message", "")
        if not response:
            response = "抱歉，我暂时无法理解你的问题，请换一种方式描述。"
        
        # 流式输出
        if on_chunk:
            for char in response:
                await on_chunk(char)
        
        # 更新提取的信息
        extracted = result.get("extracted_info", {})
        if extracted.get("chief_complaint") and not state.get("chief_complaint"):
            state["chief_complaint"] = extracted["chief_complaint"]
        if extracted.get("symptom_location"):
            state["symptom_location"] = extracted["symptom_location"]
        if extracted.get("duration"):
            state["duration"] = extracted["duration"]
        if extracted.get("symptoms"):
            for symptom in extracted["symptoms"]:
                if symptom not in state.get("symptoms", []):
                    state.setdefault("symptoms", []).append(symptom)
        if extracted.get("risk_factors"):
            for factor in extracted["risk_factors"]:
                if factor not in state.get("risk_factors", []):
                    state.setdefault("risk_factors", []).append(factor)
        
        # 更新风险等级
        risk_level = result.get("risk_level", state.get("risk_level", "low"))
        state["risk_level"] = risk_level
        
        state["current_response"] = response
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        state["quick_options"] = result.get("quick_options", self._default_quick_options(state))
        state["questions_asked"] = state.get("questions_asked", 0) + 1
        state["stage"] = result.get("stage", state.get("stage", "collecting"))
        
        # 检查是否需要紧急就医提醒
        if risk_level == "emergency":
            state["need_urgent_care"] = True
        
        return state
    
    async def _handle_ecg_interpretation(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理心电图解读"""
        # 构建心电图描述
        ecg_description = user_input or "用户上传了心电图图片"
        if image_url:
            ecg_description += f"\n[图片URL: {image_url}]"
        
        # 患者背景
        patient_context = self._format_patient_context(state)
        
        # 运行解读 Crew
        result = await self._run_ecg_interpretation_crew(ecg_description, patient_context)
        
        # 构建响应
        interpretation = result.get("interpretation", "无法解读心电图")
        findings = result.get("findings", [])
        abnormalities = result.get("abnormalities", [])
        recommendations = result.get("recommendations", [])
        need_urgent_care = result.get("need_urgent_care", False)
        
        response_parts = [f"**心电图解读结果**\n\n{interpretation}"]
        
        if findings:
            response_parts.append(f"\n\n**主要发现：**\n" + "\n".join([f"• {f}" for f in findings]))
        
        if abnormalities:
            response_parts.append(f"\n\n**异常项：**\n" + "\n".join([f"⚠️ {a}" for a in abnormalities]))
        
        if recommendations:
            response_parts.append(f"\n\n**建议：**\n" + "\n".join([f"• {r}" for r in recommendations]))
        
        if need_urgent_care:
            response_parts.append("\n\n🚨 **请注意：建议尽快就医进一步检查！**")
        
        response = "".join(response_parts)
        
        # 流式输出
        if on_chunk:
            for char in response:
                await on_chunk(char)
        
        # 更新状态
        state["current_response"] = response
        state["latest_ecg_interpretation"] = result
        state["messages"].append({
            "role": "user",
            "content": ecg_description,
            "timestamp": datetime.now().isoformat()
        })
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "继续咨询", "value": "我还有其他问题想问", "category": "继续"},
            {"text": "风险评估", "value": "帮我做个心血管风险评估", "category": "功能"},
            {"text": "结束咨询", "value": "谢谢，我了解了", "category": "结束"}
        ]
        
        return state
    
    async def _handle_risk_assessment(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理心血管风险评估"""
        # 运行评估 Crew
        result = await self._run_risk_assessment_crew(state)
        
        # 构建响应
        overall_risk = result.get("overall_risk", "unknown")
        risk_factors = result.get("risk_factors", [])
        protective_factors = result.get("protective_factors", [])
        score = result.get("score", 0)
        recommendations = result.get("recommendations", [])
        follow_up = result.get("follow_up", "")
        
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "very_high": "🔴"
        }.get(overall_risk, "⚪")
        
        risk_label = {
            "low": "低风险",
            "medium": "中等风险",
            "high": "高风险",
            "very_high": "极高风险"
        }.get(overall_risk, "未知")
        
        response_parts = [
            f"**心血管风险评估结果**\n\n",
            f"{risk_emoji} **综合风险等级：{risk_label}**\n",
            f"风险评分：{score}/100\n"
        ]
        
        if risk_factors:
            response_parts.append(f"\n**风险因素：**\n" + "\n".join([f"⚠️ {f}" for f in risk_factors]))
        
        if protective_factors:
            response_parts.append(f"\n\n**保护因素：**\n" + "\n".join([f"✅ {f}" for f in protective_factors]))
        
        if recommendations:
            response_parts.append(f"\n\n**建议：**\n" + "\n".join([f"• {r}" for r in recommendations]))
        
        if follow_up:
            response_parts.append(f"\n\n**随访建议：**\n{follow_up}")
        
        response = "".join(response_parts)
        
        # 流式输出
        if on_chunk:
            for char in response:
                await on_chunk(char)
        
        # 更新状态
        state["current_response"] = response
        state["latest_risk_assessment"] = result
        state["risk_level"] = overall_risk
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "继续咨询", "value": "我还有其他问题", "category": "继续"},
            {"text": "了解更多", "value": "能详细说说建议吗", "category": "详情"},
            {"text": "结束咨询", "value": "谢谢，我了解了", "category": "结束"}
        ]
        
        return state
    
    async def _run_conversation_crew(
        self,
        state: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """运行对话 Crew"""
        task = create_cardio_conversation_task(
            self.conversation_agent,
            state,
            user_input
        )
        
        crew = Crew(
            agents=[self.conversation_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            result = await crew.kickoff_async()
        except AttributeError:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
        
        return result.to_dict()
    
    async def _run_ecg_interpretation_crew(
        self,
        ecg_description: str,
        patient_context: str
    ) -> Dict[str, Any]:
        """运行心电图解读 Crew"""
        task = create_ecg_interpretation_task(
            self.ecg_interpreter,
            ecg_description,
            patient_context
        )
        
        crew = Crew(
            agents=[self.ecg_interpreter],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            result = await crew.kickoff_async()
        except AttributeError:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
        
        return result.to_dict()
    
    async def _run_risk_assessment_crew(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行风险评估 Crew"""
        task = create_risk_assessment_task(
            self.risk_assessor,
            state
        )
        
        crew = Crew(
            agents=[self.risk_assessor],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            result = await crew.kickoff_async()
        except AttributeError:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
        
        return result.to_dict()
    
    def _format_patient_context(self, state: Dict[str, Any]) -> str:
        """格式化患者背景信息"""
        parts = []
        if state.get("chief_complaint"):
            parts.append(f"主诉: {state['chief_complaint']}")
        if state.get("symptoms"):
            parts.append(f"症状: {', '.join(state['symptoms'])}")
        if state.get("medical_history"):
            parts.append(f"既往史: {', '.join(state['medical_history'])}")
        if state.get("risk_factors"):
            parts.append(f"风险因素: {', '.join(state['risk_factors'])}")
        return "\n".join(parts) if parts else "无额外背景信息"
    
    def _default_quick_options(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """默认快捷选项"""
        risk_level = state.get("risk_level", "low")
        if risk_level in ["high", "emergency"]:
            return [
                {"text": "我会去医院", "value": "我会尽快去医院检查", "category": "确认"},
                {"text": "还有问题", "value": "我还有其他问题", "category": "继续"},
            ]
        return [
            {"text": "是的", "value": "是的", "category": "确认"},
            {"text": "没有", "value": "没有", "category": "否定"},
            {"text": "不确定", "value": "不确定", "category": "不确定"},
            {"text": "换个问题", "value": "能换一个角度问吗", "category": "其他"}
        ]


# 全局实例
cardio_crew_service = CardioCrewService()
