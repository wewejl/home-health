"""
OrthoCrewService - CrewAI 1.x 骨科问诊服务
支持：症状问诊、X光片解读
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime

from crewai import Crew, Process

from ...config import get_settings
from .ortho_agents import (
    create_ortho_conversation_agent,
    create_ortho_xray_interpreter,
    create_ortho_conversation_task,
    create_xray_interpretation_task,
    create_llm,
)

settings = get_settings()


class OrthoCrewService:
    """
    骨科 CrewAI 1.x 编排服务
    
    负责：
    1. 初始化骨科专业 Agents
    2. 调用 Crew 执行问诊、X光解读任务
    3. 管理状态与流式输出
    """
    
    def __init__(self):
        self.llm = self._build_llm()
        self._conversation_agent = None
        self._xray_interpreter = None
        print("[OrthoCrewService] Initialized with CrewAI multi-agent architecture")
    
    def _build_llm(self):
        """构建 LLM 实例"""
        return create_llm()
    
    @property
    def conversation_agent(self):
        if self._conversation_agent is None:
            self._conversation_agent = create_ortho_conversation_agent(self.llm)
        return self._conversation_agent
    
    @property
    def xray_interpreter(self):
        if self._xray_interpreter is None:
            self._xray_interpreter = create_ortho_xray_interpreter(self.llm)
        return self._xray_interpreter
    
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
        运行骨科问诊任务
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            image_url: X光片图片 URL
            image_base64: X光片图片 Base64
            task_type: 任务类型 (conversation, interpret_xray)
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
        if task_type == "interpret_xray" and (image_url or image_base64 or user_input):
            return await self._handle_xray_interpretation(state, user_input, image_url, image_base64, on_chunk)
        
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
        greeting = """你好~我是你的骨科AI助手。我可以帮助你：
• 了解骨骼和关节相关症状（关节疼痛、腰背痛、骨折等）
• 解读X光片报告

请告诉我你目前的症状或想咨询的问题，我会一步步和你沟通。

⚠️ 提醒：如果你有明显外伤、骨折体征（畸形、异常活动）、或脊柱损伤伴肢体麻木，请立即就医。"""
        
        state["current_response"] = greeting
        state["stage"] = "collecting"
        state["messages"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "关节疼痛", "value": "我有关节疼痛的症状", "category": "症状"},
            {"text": "腰背痛", "value": "我有腰背疼痛", "category": "症状"},
            {"text": "颈椎不适", "value": "我有颈椎不舒服", "category": "症状"},
            {"text": "扭伤/外伤", "value": "我有扭伤或外伤", "category": "症状"},
            {"text": "解读X光片", "value": "我想解读一下X光片", "category": "功能"}
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
        if extracted.get("pain_location"):
            state["pain_location"] = extracted["pain_location"]
        if extracted.get("duration"):
            state["duration"] = extracted["duration"]
        if extracted.get("symptoms"):
            for symptom in extracted["symptoms"]:
                if symptom not in state.get("symptoms", []):
                    state.setdefault("symptoms", []).append(symptom)
        if extracted.get("injury_history"):
            state["injury_history"] = extracted["injury_history"]
        
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
    
    async def _handle_xray_interpretation(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理X光片解读"""
        # 构建X光片描述
        xray_description = user_input or "用户上传了X光片图片"
        if image_url:
            xray_description += f"\n[图片URL: {image_url}]"
        
        # 患者背景
        patient_context = self._format_patient_context(state)
        
        # 运行解读 Crew
        result = await self._run_xray_interpretation_crew(xray_description, patient_context)
        
        # 构建响应
        interpretation = result.get("interpretation", "无法解读X光片")
        findings = result.get("findings", [])
        abnormalities = result.get("abnormalities", [])
        recommendations = result.get("recommendations", [])
        need_urgent_care = result.get("need_urgent_care", False)
        
        response_parts = [f"**X光片解读结果**\n\n{interpretation}"]
        
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
        state["latest_xray_interpretation"] = result
        state.setdefault("xray_interpretations", []).append(result)
        state["messages"].append({
            "role": "user",
            "content": xray_description,
            "timestamp": datetime.now().isoformat()
        })
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "继续咨询", "value": "我还有其他问题想问", "category": "继续"},
            {"text": "了解更多", "value": "能详细解释一下吗", "category": "详情"},
            {"text": "结束咨询", "value": "谢谢，我了解了", "category": "结束"}
        ]
        
        return state
    
    async def _run_conversation_crew(
        self,
        state: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """运行对话 Crew"""
        task = create_ortho_conversation_task(
            self.conversation_agent,
            state,
            user_input
        )
        
        crew = Crew(
            agents=[self.conversation_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )
        
        try:
            result = await crew.kickoff_async()
        except AttributeError:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
        
        return result.to_dict()
    
    async def _run_xray_interpretation_crew(
        self,
        xray_description: str,
        patient_context: str
    ) -> Dict[str, Any]:
        """运行X光片解读 Crew"""
        task = create_xray_interpretation_task(
            self.xray_interpreter,
            xray_description,
            patient_context
        )
        
        crew = Crew(
            agents=[self.xray_interpreter],
            tasks=[task],
            process=Process.sequential,
            verbose=False
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
        if state.get("pain_location"):
            parts.append(f"疼痛部位: {state['pain_location']}")
        if state.get("injury_history"):
            parts.append(f"外伤史: {state['injury_history']}")
        if state.get("medical_history"):
            parts.append(f"既往史: {', '.join(state['medical_history'])}")
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
ortho_crew_service = OrthoCrewService()
