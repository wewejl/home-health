"""
LangGraphAgentBase - LangGraph 实现的智能体基类

基于 LangGraph 1.x 构建，提供：
- 状态图构建和复用
- 流式输出支持
- 统一的状态管理
"""
from abc import abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, List, Literal, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages

from .base_agent import BaseAgent


def _serialize_messages(messages: List[dict]) -> List[dict]:
    """
    将消息列表序列化为可 JSON 保存的格式
    
    LangGraph 的 add_messages 会将 dict 转换为 LangChain Message 对象，
    但数据库存储需要 JSON 格式，因此需要转换回 dict
    """
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        elif hasattr(msg, "content"):
            # LangChain Message 对象
            role = "assistant" if getattr(msg, "type", "") == "ai" else "user"
            if hasattr(msg, "type") and msg.type == "system":
                role = "system"
            serialized.append({
                "role": role,
                "content": msg.content
            })
        else:
            serialized.append({"role": "user", "content": str(msg)})
    return serialized


class BaseAgentState(TypedDict):
    """
    统一的 Agent 状态基类
    
    所有 LangGraph 智能体状态都应继承此类
    """
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
    chief_complaint: str
    symptoms: List[str]
    duration: str
    
    # === AI 输出 ===
    current_response: str
    quick_options: List[dict]
    
    # === 流程控制 ===
    next_node: str
    should_stream: bool
    
    # === 附件处理 ===
    pending_attachments: List[dict]
    processed_results: List[dict]
    
    # === 错误处理 ===
    error: Optional[str]


class LangGraphAgentBase(BaseAgent):
    """
    LangGraph 实现的 Agent 基类
    
    提供：
    - 图结构复用（编译后缓存）
    - 流式输出支持
    - 统一的运行接口
    
    子类需要实现：
    - _build_graph(): 构建状态图
    - _create_initial_state(): 创建初始状态
    - get_capabilities(): 返回能力配置
    """
    
    # 类级别缓存编译后的图
    _compiled_graph = None
    
    def __init__(self):
        self._graph = None
    
    @property
    def graph(self):
        """获取编译后的图（懒加载，类级别缓存）"""
        if self.__class__._compiled_graph is None:
            self.__class__._compiled_graph = self._build_graph()
        return self.__class__._compiled_graph
    
    @abstractmethod
    def _build_graph(self) -> StateGraph:
        """
        构建状态图 - 子类必须实现
        
        Returns:
            编译后的 StateGraph
        """
        pass
    
    @abstractmethod
    def _create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """
        创建初始状态 - 子类必须实现
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            
        Returns:
            初始状态字典
        """
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
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表
            action: 动作类型
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
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
        
        try:
            # 运行状态图
            if on_chunk:
                final_state = await self._run_with_stream(state, on_chunk)
            else:
                final_state = await self.graph.ainvoke(state)
            
            # 添加 AI 回复到消息历史
            if final_state.get("current_response"):
                final_state["messages"].append({
                    "role": "assistant",
                    "content": final_state["current_response"]
                })
            
            # 序列化消息以便数据库存储
            final_state["messages"] = _serialize_messages(final_state.get("messages", []))
            
            return final_state
            
        except Exception as e:
            # 错误处理
            state["error"] = str(e)
            state["current_response"] = f"抱歉，处理您的请求时出现了问题。请稍后重试。"
            return state
    
    async def _run_with_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Callable[[str], Awaitable[None]]
    ) -> Dict[str, Any]:
        """
        流式输出运行
        
        使用 LangGraph 的 astream_events API
        """
        final_state = state.copy()
        streamed_content = ""
        
        try:
            async for event in self.graph.astream_events(state, version="v2"):
                event_type = event.get("event", "")
                
                # 处理 LLM 流式输出
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        await on_chunk(chunk.content)
                        streamed_content += chunk.content
                
                # 获取最终状态
                elif event_type == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict) and "current_response" in output:
                        final_state = output
            
            # 如果流式内容被收集，更新到状态
            if streamed_content and not final_state.get("current_response"):
                final_state["current_response"] = streamed_content
                
        except Exception as e:
            final_state["error"] = str(e)
            if streamed_content:
                final_state["current_response"] = streamed_content
        
        # 序列化消息以便数据库存储
        final_state["messages"] = _serialize_messages(final_state.get("messages", []))
        
        return final_state
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置 - 子类必须实现"""
        pass
    
    @classmethod
    def reset_graph(cls):
        """重置编译后的图（用于测试或配置变更）"""
        cls._compiled_graph = None
