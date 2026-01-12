"""
通用智能体 - 包装现有的 QwenService
"""
from typing import Dict, Any, Optional, Callable, Awaitable
from .agent_router import BaseAgent
from .qwen_service import QwenService


class GeneralAgent(BaseAgent):
    """通用医生问诊智能体"""
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        return {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_response": "",
            "quick_options": []
        }
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        doctor_info: Dict[str, Any] = None,
        history: list = None,
        rag_context: str = ""
    ) -> Dict[str, Any]:
        """
        运行通用问诊
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表（通用智能体暂不支持）
            action: 动作类型（通用智能体只支持 conversation）
            on_chunk: 流式输出回调
            doctor_info: 医生信息 {name, title, specialty, persona_prompt, model, temperature, max_tokens}
            history: 对话历史
            rag_context: RAG 上下文
            
        Returns:
            更新后的状态
        """
        if not user_input:
            return state
        
        # 提取医生信息
        doctor_name = "AI助手"
        doctor_title = "主治医师"
        specialty = "全科医学"
        persona_prompt = None
        model = None
        temperature = None
        max_tokens = None
        
        if doctor_info:
            doctor_name = doctor_info.get("name", doctor_name)
            doctor_title = doctor_info.get("title", doctor_title)
            specialty = doctor_info.get("specialty", specialty)
            persona_prompt = doctor_info.get("persona_prompt")
            model = doctor_info.get("model")
            temperature = doctor_info.get("temperature")
            max_tokens = doctor_info.get("max_tokens")
        
        # 格式化历史记录
        formatted_history = history or []
        
        # 调用 QwenService 获取 AI 响应
        ai_response = await QwenService.get_ai_response(
            user_message=user_input,
            doctor_name=doctor_name,
            doctor_title=doctor_title,
            specialty=specialty,
            history=formatted_history,
            persona_prompt=persona_prompt,
            rag_context=rag_context,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 流式输出
        if on_chunk:
            for char in ai_response:
                await on_chunk(char)
        
        # 更新状态
        state["current_response"] = ai_response
        state["messages"].append({
            "role": "user",
            "content": user_input
        })
        state["messages"].append({
            "role": "assistant",
            "content": ai_response
        })
        
        return state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return {
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble"],
            "description": "通用医生问诊AI"
        }
