"""
DermaCrewService - CrewAI 1.x 文本问诊服务
仅保留单 Agent 对话编排能力
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime

from crewai import Crew, Process

from ..config import get_settings
from .crewai_agents import (
    create_conversation_orchestrator,
    create_conversation_task,
    create_llm,
)

settings = get_settings()


class DermaCrewService:
    """
    皮肤科 CrewAI 1.x 编排服务（文本问诊版）
    
    负责：
    1. 初始化单一对话 Agent
    2. 调用 Crew 执行问诊任务
    3. 管理状态与流式输出
    """
    
    def __init__(self):
        self.llm = self._build_llm()
        self._conversation_agent = None
    
    def _build_llm(self):
        """构建 LLM 实例 - 使用 CrewAI 1.x LLM 类 + DashScope OpenAI 兼容接口"""
        return create_llm()
    
    @property
    def conversation_agent(self):
        if self._conversation_agent is None:
            self._conversation_agent = create_conversation_orchestrator(self.llm)
        return self._conversation_agent
    
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
        运行文本问诊任务
        """
        # 新会话问候
        has_assistant_history = any(msg.get("role") == "assistant" for msg in state.get("messages", []))
        if state.get("stage") == "greeting" and not has_assistant_history:
            return await self._handle_greeting(state, on_chunk)
        
        # 如果 stage 还是 greeting 但已有历史，切换到 collecting
        if state.get("stage") == "greeting":
            state["stage"] = "collecting"
        
        # 处理文本输入
        if user_input:
            return await self._handle_conversation(state, user_input, on_chunk)
        
        return state
    
    async def _handle_greeting(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理问候"""
        greeting = """你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。"""
        
        state["current_response"] = greeting
        state["stage"] = "collecting"
        state["messages"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "描述位置", "value": "出现在身体哪个部位", "category": "症状"},
            {"text": "持续时间", "value": "大概持续了多久", "category": "症状"},
            {"text": "伴随感觉", "value": "是否有瘙痒或疼痛", "category": "症状"},
            {"text": "日常护理", "value": "我做过哪些护理措施", "category": "其他"}
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
            raise ValueError("CrewAI 未返回有效的 message 字段，请检查 Agent 配置或模型输出")
        
        # 流式输出
        if on_chunk:
            for char in response:
                await on_chunk(char)
        
        # 更新提取的信息
        extracted = result.get("extracted_info", {})
        if extracted.get("chief_complaint") and not state.get("chief_complaint"):
            state["chief_complaint"] = extracted["chief_complaint"]
        if extracted.get("skin_location"):
            state["skin_location"] = extracted["skin_location"]
        if extracted.get("duration"):
            state["duration"] = extracted["duration"]
        if extracted.get("symptoms"):
            for symptom in extracted["symptoms"]:
                if symptom not in state.get("symptoms", []):
                    state.setdefault("symptoms", []).append(symptom)
        
        state["current_response"] = response
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        state["quick_options"] = result.get("quick_options", self._default_quick_options(state))
        state["questions_asked"] = state.get("questions_asked", 0) + 1
        state["stage"] = result.get("stage", state.get("stage", "collecting"))
        
        return state
    
    async def _run_conversation_crew(
        self,
        state: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """运行对话 Crew - CrewAI 1.x 原生异步支持"""
        task = create_conversation_task(
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
        
        # CrewAI 1.x 支持原生 async
        try:
            result = await crew.kickoff_async()
        except AttributeError:
            # 如果 kickoff_async 不可用，回退到线程池执行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
        
        # 使用 CrewAI 官方结构化输出，直接返回字典
        # result 是 CrewOutput 对象，支持 .to_dict() 或 .pydantic 访问
        return result.to_dict()
    
    
    def _default_quick_options(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """默认快捷选项"""
        return [
            {"text": "是的", "value": "是的", "category": "确认"},
            {"text": "没有", "value": "没有", "category": "否定"},
            {"text": "不确定", "value": "不确定", "category": "不确定"},
            {"text": "换个问法", "value": "能换一个角度问吗", "category": "其他"}
        ]


# 全局实例
derma_crew_service = DermaCrewService()
