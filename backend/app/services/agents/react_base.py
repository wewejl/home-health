"""
ReAct Agent 基类

实现 Observe → Think → Act 循环的智能体基类
所有科室智能体继承此类，实现完全自主的 AI 决策
"""
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, List
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from ..qwen_service import QwenService
from ...schemas.agent_response import AgentResponse
from .tools import TOOL_REGISTRY, ALL_TOOL_SCHEMAS, execute_tools_parallel


class ReActAgentState(TypedDict, total=False):
    """ReAct Agent 状态"""
    # 会话标识
    session_id: str
    user_id: int
    agent_type: str
    
    # 对话历史（LangGraph 管理追加）
    messages: Annotated[List[dict], add_messages]
    
    # AI 决策（结构化 JSON）
    agent_decision: dict
    
    # 工具调用
    pending_tool_calls: List[dict]
    tool_results: List[dict]
    
    # 医学上下文（AI 自己维护）
    medical_context: dict
    
    # 响应输出
    current_response: str
    quick_options: List[str]
    
    # 进度追踪
    stage: str  # greeting, collecting, analyzing, diagnosing, completed
    progress: int
    risk_level: str
    
    # 附件
    attachments: List[dict]
    
    # 专科数据
    specialty_data: dict
    
    # 控制标记
    should_continue: bool
    iteration_count: int
    max_iterations: int
    
    # 错误处理
    error: Optional[str]


def create_react_initial_state(
    session_id: str, 
    user_id: int, 
    agent_type: str
) -> Dict[str, Any]:
    """创建 ReAct Agent 初始状态"""
    return {
        "session_id": session_id,
        "user_id": user_id,
        "agent_type": agent_type,
        "messages": [],
        "agent_decision": {},
        "pending_tool_calls": [],
        "tool_results": [],
        "medical_context": {
            "symptoms": [],
            "duration": "",
            "severity": "",
            "affected_area": "",
            "triggers": [],
            "medical_history": [],
            "allergies": [],
            "current_medications": [],
            "collected_info": [],
            "missing_info": []
        },
        "current_response": "",
        "quick_options": [],
        "stage": "greeting",
        "progress": 0,
        "risk_level": "low",
        "attachments": [],
        "specialty_data": {},
        "should_continue": True,
        "iteration_count": 0,
        "max_iterations": 10,
        "error": None,
    }


class ReActAgent(ABC):
    """
    ReAct Agent 基类

    实现 Observe → Think → Act 循环
    AI 自主决策，无硬编码规则

    新增功能：
    - 支持并行工具执行
    - 支持 Corrective RAG
    """

    _compiled_graph = None

    def __init__(self, enable_parallel_tools: bool = True):
        self._tools = self.get_tools()
        self._tool_schemas = self.get_tool_schemas()
        self._enable_parallel_tools = enable_parallel_tools
    
    @property
    def graph(self):
        """获取编译后的图（懒加载）"""
        if self.__class__._compiled_graph is None:
            self.__class__._compiled_graph = self._build_graph()
        return self.__class__._compiled_graph
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词 - 子类必须实现
        
        定义智能体的角色、能力和行为准则
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[str]:
        """
        获取智能体可用的工具列表 - 子类必须实现
        
        Returns:
            工具名称列表，如 ["search_medical_knowledge", "analyze_skin_image"]
        """
        pass
    
    def get_tool_schemas(self) -> List[dict]:
        """获取工具 Schema（用于 Function Calling）"""
        from .tools import ALL_TOOL_SCHEMAS
        return [
            schema for schema in ALL_TOOL_SCHEMAS 
            if schema["function"]["name"] in self._tools
        ]
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取智能体能力配置"""
        pass
    
    def _build_graph(self) -> StateGraph:
        """构建 ReAct 状态图"""
        graph = StateGraph(ReActAgentState)
        
        # 添加节点
        graph.add_node("reasoning", self._reasoning_node)
        graph.add_node("tool_executor", self._tool_executor_node)
        graph.add_node("response_generator", self._response_generator_node)
        
        # 设置入口
        graph.set_entry_point("reasoning")
        
        # 条件边：根据 AI 决策路由
        graph.add_conditional_edges(
            "reasoning",
            self._route_decision,
            {
                "use_tool": "tool_executor",
                "respond": "response_generator",
                "diagnose": "response_generator",
                "end": END,
            }
        )
        
        # 工具执行后回到推理
        graph.add_edge("tool_executor", "reasoning")
        
        # 响应生成后结束
        graph.add_edge("response_generator", END)
        
        return graph.compile()
    
    def _route_decision(self, state: Dict[str, Any]) -> str:
        """根据 AI 决策路由到下一个节点"""
        decision = state.get("agent_decision", {})
        action = decision.get("action", "respond")
        
        # 检查迭代次数
        if state.get("iteration_count", 0) >= state.get("max_iterations", 10):
            return "respond"
        
        # 检查是否有错误
        if state.get("error"):
            return "respond"
        
        if action == "use_tool":
            return "use_tool"
        elif action == "diagnose":
            return "diagnose"
        elif action == "respond":
            return "respond"
        else:
            return "respond"
    
    async def _reasoning_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        推理节点 - AI 分析状态并决定下一步
        
        这是 ReAct 的核心：AI 自主决策
        """
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        # 构建消息
        messages = self._build_reasoning_messages(state)
        
        # 添加决策指令
        decision_instruction = self._get_decision_instruction(state)
        messages.append({"role": "user", "content": decision_instruction})
        
        try:
            # 调用 LLM（带 Function Calling）
            result = await QwenService.chat_with_tools(
                messages=messages,
                tools=self._tool_schemas,
                tool_choice="auto",
                max_tokens=2000
            )
            
            # 解析决策
            if result.get("tool_calls"):
                # AI 决定调用工具
                tool_calls = result["tool_calls"]
                state["pending_tool_calls"] = tool_calls
                state["agent_decision"] = {
                    "action": "use_tool",
                    "tool_calls": tool_calls,
                    "thought": result.get("content", "")
                }
            else:
                # AI 决定直接回复
                content = result.get("content", "")
                decision = self._parse_decision(content)
                state["agent_decision"] = decision
                
                # 更新医学上下文（如果 AI 提供了）
                if decision.get("medical_context_update"):
                    self._update_medical_context(state, decision["medical_context_update"])
                
        except Exception as e:
            state["error"] = str(e)
            state["agent_decision"] = {
                "action": "respond",
                "response": "抱歉，处理时出现了问题，请稍后重试。"
            }
        
        return state
    
    def _build_reasoning_messages(self, state: Dict[str, Any]) -> List[dict]:
        """构建推理所需的消息列表"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]

        # 添加对话历史
        for msg in state.get("messages", [])[-10:]:  # 最近10条
            if isinstance(msg, dict):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            elif hasattr(msg, "type"):  # LangChain Message 对象
                role = "user" if msg.type == "human" else "assistant"
                messages.append({
                    "role": role,
                    "content": getattr(msg, "content", "")
                })

        # 添加工具调用结果
        for result in state.get("tool_results", []):
            messages.append({
                "role": "assistant",
                "content": f"[工具调用结果] {result.get('tool')}: {json.dumps(result.get('result'), ensure_ascii=False)}"
            })

        # 添加当前医学上下文
        ctx = state.get("medical_context", {})
        if ctx.get("symptoms") or ctx.get("collected_info"):
            context_summary = self._format_medical_context(ctx)
            messages.append({
                "role": "system",
                "content": f"[当前收集的信息]\n{context_summary}"
            })

        return messages
    
    def _get_decision_instruction(self, state: Dict[str, Any]) -> str:
        """获取决策指令"""
        attachments = state.get("attachments", [])
        has_image = any(
            att.get("type") == "image" or "image" in att.get("mime_type", "")
            for att in attachments
        )

        # 获取已收集的信息
        medical_context = state.get("medical_context", {})
        collected_info = medical_context.get("collected_info", [])
        symptoms = medical_context.get("symptoms", [])
        messages = state.get("messages", [])

        # 计算对话轮数（用户消息数量）
        conversation_rounds = len([
            m for m in messages
            if (isinstance(m, dict) and m.get("role") == "user") or getattr(m, "type", None) == "human"
        ])

        instruction = f"""# 决策指令

## 当前状态
- 对话轮数：{conversation_rounds}
- 已收集症状：{symptoms if symptoms else '暂无'}
- 已收集信息项：{len(collected_info)} 项

## 核心原则：先问诊，后诊断

**你必须先通过提问收集足够信息，然后才能给出诊断建议。**

### 信息充分性判断标准

**最低要求（必须全部满足才能进入诊断阶段）：**
1. ✅ 了解主诉症状（皮疹形态、皮肤问题描述）
2. ✅ 了解发病部位
3. ✅ 了解持续时间
4. ✅ 了解至少1个伴随症状或诱因

### 决策流程

```
如果 对话轮数 < 2 或 已收集信息项 < 4：
    → 进入信息收集模式，提问收集缺失信息
否则 如果 信息收集充分：
    → 可以给出初步诊断建议
```

### 信息收集模式（信息不足时）

你的回复应该是**向患者提问**，格式：
- "[提问] 请问您皮肤上的皮疹是什么样子的？"
- "[提问] 皮疹出现在身体的哪个部位？"
- "[提问] 这个问题出现多久了？"

每次只问 **1-2 个问题**，针对最缺失的信息。

### 诊断模式（信息充分后）

当收集到足够信息后，你可以：
- 调用工具：`search_medical_knowledge` 查询专业知识
- 调用工具：`assess_risk` 评估风险等级
- 给出初步诊断建议

---

## 可用工具
1. `search_medical_knowledge` - 查询医学知识库
2. `assess_risk` - 评估病情风险
3. `analyze_skin_image` - 分析皮肤照片
4. `search_medication` - 查询用药信息
5. `generate_medical_dossier` - 生成病历

## 回复格式（JSON）

```json
{{
  "thought": "你的思考过程：当前信息是否充分，还需要收集什么",
  "action": "respond",
  "response": "给患者的回复内容（提问时使用问句）",
  "quick_options": ["快速回复选项1", "选项2"],
  "medical_context_update": {{
    "symptoms": ["新提取的症状"],
    "collected_info": ["部位", "时间", "症状类型"],
    "missing_info": ["还需了解的信息"]
  }},
  "ready_to_diagnose": {True if len(collected_info) >= 4 else False},
  "stage": "collecting",
  "progress": {min(len(collected_info) * 15, 80)}
}}
```

**记住**：你的回复主要是**向患者提问**，直到收集足够信息。"""

        if has_image:
            instruction += """

## 📸 患者上传了图片

请立即调用 `analyze_skin_image` 工具分析图片，然后基于分析结果继续提问或给出建议。"""

        return instruction
    
    def _parse_decision(self, content: str) -> dict:
        """解析 AI 的决策输出"""
        # 尝试提取 JSON
        try:
            # 查找 JSON 块
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 尝试直接解析
            if content.strip().startswith('{'):
                return json.loads(content)
            
        except json.JSONDecodeError:
            pass
        
        # 解析失败，返回默认决策
        return {
            "action": "respond",
            "response": content,
            "thought": "",
            "quick_options": []
        }
    
    def _update_medical_context(self, state: Dict[str, Any], update: dict):
        """更新医学上下文"""
        ctx = state.get("medical_context", {})
        
        for key, value in update.items():
            if key in ctx:
                if isinstance(ctx[key], list) and isinstance(value, list):
                    # 合并列表，去重
                    ctx[key] = list(set(ctx[key] + value))
                else:
                    ctx[key] = value
        
        state["medical_context"] = ctx
    
    def _format_medical_context(self, ctx: dict) -> str:
        """格式化医学上下文为文本"""
        parts = []
        
        if ctx.get("symptoms"):
            parts.append(f"症状: {', '.join(ctx['symptoms'])}")
        if ctx.get("duration"):
            parts.append(f"病程: {ctx['duration']}")
        if ctx.get("severity"):
            parts.append(f"严重程度: {ctx['severity']}")
        if ctx.get("affected_area"):
            parts.append(f"部位: {ctx['affected_area']}")
        if ctx.get("triggers"):
            parts.append(f"诱因: {', '.join(ctx['triggers'])}")
        if ctx.get("allergies"):
            parts.append(f"过敏史: {', '.join(ctx['allergies'])}")
        if ctx.get("missing_info"):
            parts.append(f"待收集: {', '.join(ctx['missing_info'])}")
        
        return "\n".join(parts) if parts else "暂无"
    
    async def _tool_executor_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        工具执行节点

        支持并行执行多个独立工具，提升响应速度
        """
        pending_calls = state.get("pending_tool_calls", [])

        if not pending_calls:
            return state

        # 预处理：注入附件数据到图像分析工具
        processed_calls = self._prepare_tool_calls(state, pending_calls)

        # 执行工具（并行或串行）
        if self._enable_parallel_tools and len(processed_calls) > 1:
            # 并行执行多个工具
            execution_results = await execute_tools_parallel(
                processed_calls,
                TOOL_REGISTRY,
                enable_parallel=True
            )
        else:
            # 串行执行（兼容模式或单个工具）
            execution_results = await self._execute_tools_serial(processed_calls)

        # 处理结果并更新状态
        results = state.get("tool_results", [])
        for result_item in execution_results:
            tool_name = result_item.get("tool")
            tool_result = result_item.get("result")
            success = result_item.get("success", False)

            results.append(result_item)

            # 特殊处理：更新状态
            if success and tool_result:
                self._process_tool_result(state, tool_name, tool_result)

        state["tool_results"] = results
        state["pending_tool_calls"] = []
        state["attachments"] = []  # 清空已处理的附件

        return state

    def _prepare_tool_calls(
        self,
        state: Dict[str, Any],
        pending_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        预处理工具调用，注入必要的上下文数据

        例如：将附件数据注入到图像分析工具
        """
        processed_calls = []
        attachments = state.get("attachments", [])
        medical_context = state.get("medical_context", {})

        for call in pending_calls:
            tool_name = call.get("function", {}).get("name", "")
            args_str = call.get("function", {}).get("arguments", "{}")

            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}

            # 特殊处理图像分析工具：注入附件数据
            if tool_name == "analyze_skin_image" and not args.get("image_base64"):
                for att in attachments:
                    if att.get("type") == "image" or "image" in att.get("mime_type", ""):
                        args["image_base64"] = att.get("base64") or att.get("url", "")
                        args["context"] = medical_context.get("symptoms", [])
                        break

            # 重新构造工具调用
            processed_calls.append({
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(args, ensure_ascii=False)
                }
            })

        return processed_calls

    async def _execute_tools_serial(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        串行执行工具（兼容模式）
        """
        results = []

        for call in tool_calls:
            tool_name = call.get("function", {}).get("name", "")
            args_str = call.get("function", {}).get("arguments", "{}")

            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}

            tool_func = TOOL_REGISTRY.get(tool_name)
            if tool_func:
                try:
                    result = await tool_func(**args)
                    results.append({
                        "tool": tool_name,
                        "args": args,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "args": args,
                        "result": {"error": str(e)},
                        "success": False,
                        "error": str(e)
                    })
            else:
                results.append({
                    "tool": tool_name,
                    "args": args,
                    "result": {"error": f"工具 {tool_name} 不存在"},
                    "success": False,
                    "error": f"Tool {tool_name} not found"
                })

        return results
    
    def _process_tool_result(self, state: Dict[str, Any], tool_name: str, result: dict):
        """处理工具结果，更新状态"""
        specialty_data = state.get("specialty_data", {})
        
        if tool_name == "analyze_skin_image" and result.get("success"):
            specialty_data["skin_analysis"] = result
            state["progress"] = max(state.get("progress", 0), 50)
            
        elif tool_name == "assess_risk":
            state["risk_level"] = result.get("risk_level", "low")
            specialty_data["risk_assessment"] = result
            
        elif tool_name == "generate_medical_dossier":
            specialty_data["dossier"] = result
            state["stage"] = "completed"
            state["progress"] = 100
            
        elif tool_name == "search_medication":
            specialty_data["medication_info"] = result
        
        state["specialty_data"] = specialty_data
    
    async def _response_generator_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """响应生成节点"""
        decision = state.get("agent_decision", {})
        
        # 获取响应内容
        response = decision.get("response", "")
        
        if not response:
            # 如果没有预设响应，根据行动类型生成
            action = decision.get("action", "respond")
            if action == "diagnose":
                response = await self._generate_diagnosis(state)
            else:
                response = "请问还有什么需要了解的吗？"
        
        state["current_response"] = response
        state["quick_options"] = decision.get("quick_options", [])
        
        # 更新阶段和进度
        if decision.get("stage"):
            state["stage"] = decision["stage"]
        if decision.get("progress"):
            state["progress"] = decision["progress"]
        
        # 如果准备诊断
        if decision.get("ready_to_diagnose") or decision.get("action") == "diagnose":
            state["stage"] = "diagnosing"
            state["progress"] = max(state.get("progress", 0), 80)
        
        return state
    
    async def _generate_diagnosis(self, state: Dict[str, Any]) -> str:
        """生成诊断（由 AI 完成）"""
        ctx = state.get("medical_context", {})
        specialty_data = state.get("specialty_data", {})

        diagnosis_prompt = f"""基于以下收集的信息，请给出专业的初步诊断意见：

{self._format_medical_context(ctx)}

图像分析结果：{specialty_data.get('skin_analysis', {}).get('findings', '无')}
风险评估：{specialty_data.get('risk_assessment', {}).get('risk_level', '未评估')}

请包含：
1. 可能的诊断（按可能性排序）
2. 诊断依据
3. 建议的处理方式
4. 是否需要线下就医
5. 日常护理建议
6. 注意事项和警示信号

请用专业但通俗易懂的语言回复。"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": diagnosis_prompt}
        ]

        try:
            result = await QwenService.chat_with_tools(
                messages=messages,
                tools=[],
                max_tokens=1500
            )
            return result.get("content", "无法生成诊断，请稍后重试。")
        except Exception as e:
            return f"生成诊断时出现问题：{str(e)}"

    async def _handle_response_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]]
    ):
        """处理响应生成节点的流式输出"""
        decision = state.get("agent_decision", {})
        response = decision.get("response", "")

        if not response:
            action = decision.get("action", "respond")
            if action == "diagnose":
                # 流式生成诊断
                response = await self._generate_diagnosis_stream(state, on_chunk)
            else:
                response = "请问还有什么需要了解的吗？"

        # 流式输出响应（阶段 4: 优化为分块发送，提高性能）
        if on_chunk and response:
            await self._stream_chunked(response, on_chunk, chunk_size=10)

        state["current_response"] = response
        state["quick_options"] = decision.get("quick_options", [])

        if decision.get("stage"):
            state["stage"] = decision["stage"]
        if decision.get("progress"):
            state["progress"] = decision["progress"]

    async def _stream_chunked(
        self,
        text: str,
        on_chunk: Callable[[str], Awaitable[None]],
        chunk_size: int = 10,
        delay: float = 0.005
    ):
        """
        阶段 4 性能优化: 分块流式发送文本

        将文本分成多个块发送，而不是逐字符发送，这样可以:
        - 减少网络请求次数
        - 降低 CPU 开销
        - 保持流式输出的视觉效果

        Args:
            text: 要发送的文本
            on_chunk: 回调函数
            chunk_size: 每块字符数（默认 10）
            delay: 每块之间的延迟（秒，默认 0.005）
        """
        import asyncio

        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            await on_chunk(chunk)
            # 只在块之间添加小延迟，保持流式效果
            if delay > 0:
                await asyncio.sleep(delay)

    async def _handle_reasoning_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]],
        show_thinking: bool
    ):
        """
        处理推理节点的流式输出

        使用流式 LLM 进行推理，实时输出 AI 的思考过程
        """
        # 发送思考状态
        if show_thinking and on_chunk:
            await on_chunk({"type": "thinking", "data": "🤔 正在分析..."})

        # 增加迭代计数
        state["iteration_count"] = state.get("iteration_count", 0) + 1

        # 构建消息
        messages = self._build_reasoning_messages(state)

        # 添加决策指令
        decision_instruction = self._get_decision_instruction(state)
        messages.append({"role": "user", "content": decision_instruction})

        try:
            # 使用流式 LLM 调用
            full_response = ""
            pending_tool_calls = []
            tool_calls_buffer = {}

            async for chunk in QwenService.chat_with_tools_stream(
                messages=messages,
                tools=self._tool_schemas,
                tool_choice="auto",
                max_tokens=2000
            ):
                chunk_type = chunk.get("type")

                if chunk_type == "content":
                    delta = chunk.get("delta", "")
                    full_response += delta
                    # 如果显示思考过程，实时发送给前端
                    if show_thinking and on_chunk:
                        await on_chunk({"type": "thinking", "data": delta})

                elif chunk_type == "tool_call":
                    # AI 决定调用工具
                    tool_call = chunk.get("tool_call", {})
                    pending_tool_calls.append(tool_call)

                    # 发送工具调用事件
                    if on_chunk:
                        tool_name = tool_call.get("function", {}).get("name", "")
                        await on_chunk({
                            "type": "tool_call",
                            "data": {
                                "tool": tool_name,
                                "status": "calling"
                            }
                        })

                elif chunk_type == "done":
                    break

            # 处理决策结果
            if pending_tool_calls:
                # AI 决定调用工具
                state["pending_tool_calls"] = pending_tool_calls
                state["agent_decision"] = {
                    "action": "use_tool",
                    "tool_calls": pending_tool_calls,
                    "thought": full_response
                }
            else:
                # AI 决定直接回复
                decision = self._parse_decision(full_response)
                state["agent_decision"] = decision

                # 更新医学上下文（如果 AI 提供了）
                if decision.get("medical_context_update"):
                    self._update_medical_context(state, decision["medical_context_update"])

        except Exception as e:
            state["error"] = str(e)
            state["agent_decision"] = {
                "action": "respond",
                "response": "抱歉，处理时出现了问题，请稍后重试。"
            }

            # 发送错误事件
            if on_chunk:
                await on_chunk({
                    "type": "thinking",
                    "data": f"❌ 出现错误: {str(e)}"
                })

    async def _generate_diagnosis_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]]
    ) -> str:
        """流式生成诊断"""
        ctx = state.get("medical_context", {})
        specialty_data = state.get("specialty_data", {})

        diagnosis_prompt = f"""基于以下收集的信息，请给出专业的初步诊断意见：

{self._format_medical_context(ctx)}

图像分析结果：{specialty_data.get('skin_analysis', {}).get('findings', '无')}
风险评估：{specialty_data.get('risk_assessment', {}).get('risk_level', '未评估')}

请包含：
1. 可能的诊断（按可能性排序）
2. 诊断依据
3. 建议的处理方式
4. 是否需要线下就医
5. 日常护理建议
6. 注意事项和警示信号

请用专业但通俗易懂的语言回复。"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": diagnosis_prompt}
        ]

        full_response = ""
        async for chunk in QwenService.chat_with_tools_stream(
            messages=messages,
            tools=[],
            max_tokens=2000
        ):
            chunk_type = chunk.get("type")

            if chunk_type == "content":
                delta = chunk.get("delta", "")
                full_response += delta
                if on_chunk:
                    await on_chunk(delta)
            elif chunk_type == "done":
                break
            elif chunk_type == "error":
                full_response = "生成诊断时出现问题，请稍后重试。"
                break

        return full_response or "无法生成诊断，请稍后重试。"
    
    async def run_stream(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        show_thinking: bool = False,
        **kwargs
    ) -> AgentResponse:
        """
        流式运行 ReAct Agent

        Args:
            state: 当前会话状态
            user_input: 用户输入
            attachments: 附件列表
            action: 动作类型
            on_chunk: 流式输出回调
            show_thinking: 是否显示 AI 思考过程

        Returns:
            AgentResponse
        """
        # 重置迭代计数
        state["iteration_count"] = 0
        state["tool_results"] = []
        state["pending_tool_calls"] = []

        # 添加用户消息
        if user_input:
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append({"role": "user", "content": user_input})

        # 处理附件
        if attachments:
            state["attachments"] = attachments

        try:
            # 使用 astream 而不是 ainvoke
            async for event in self.graph.astream(state):
                # LangGraph astream 返回的是 (node_name, node_state) 元组
                # 或者直接返回状态更新
                if isinstance(event, tuple):
                    node_name, node_state = event
                else:
                    # 如果是字典，检查是否有 __metadata__ 或其他标识
                    if isinstance(event, dict):
                        # 检查是否是 LangGraph 的流式事件格式
                        metadata = event.get("__metadata__", {})
                        node_name = metadata.get("name", "") if metadata else ""
                        node_state = event
                    else:
                        node_name = ""
                        node_state = event

                # 处理不同节点的流式输出
                if node_name == "reasoning":
                    await self._handle_reasoning_stream(
                        node_state, on_chunk, show_thinking
                    )
                elif node_name == "tool_executor":
                    # 发送工具执行状态
                    if on_chunk:
                        pending_calls = node_state.get("pending_tool_calls", [])
                        for call in pending_calls:
                            tool_name = call.get("function", {}).get("name", "")
                            # 发送工具执行状态
                            await on_chunk({
                                "type": "tool_call",
                                "data": {
                                    "tool": tool_name,
                                    "status": "executing"
                                }
                            })
                        # 发送工具执行完成状态
                        results = node_state.get("tool_results", [])
                        if results:
                            for result in results:
                                if result.get("success"):
                                    await on_chunk({
                                        "type": "tool_result",
                                        "data": {
                                            "tool": result.get("tool"),
                                            "status": "success"
                                        }
                                    })
                elif node_name == "response_generator":
                    await self._handle_response_stream(
                        node_state, on_chunk
                    )

            # 获取最终状态（node_state 是最后的状态）
            final_state = node_state if 'node_state' in locals() else state

            # 序列化状态以便保存到数据库
            serialized_state = self._serialize_state_for_db(final_state)

            # 构建响应
            return AgentResponse(
                message=final_state.get("current_response", ""),
                stage=final_state.get("stage", "collecting"),
                progress=final_state.get("progress", 0),
                quick_options=final_state.get("quick_options", []),
                risk_level=final_state.get("risk_level"),
                specialty_data=final_state.get("specialty_data"),
                next_state=serialized_state
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return AgentResponse(
                message=f"抱歉，处理您的请求时出现了问题: {str(e)}",
                stage=state.get("stage", "collecting"),
                progress=state.get("progress", 0),
                quick_options=[],
                next_state=state
            )

    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs  # 兼容额外参数
    ) -> AgentResponse:
        """
        运行 ReAct Agent
        
        Args:
            state: 当前会话状态
            user_input: 用户输入
            attachments: 附件列表
            action: 动作类型
            on_chunk: 流式输出回调
            
        Returns:
            AgentResponse
        """
        # 重置迭代计数
        state["iteration_count"] = 0
        state["tool_results"] = []
        state["pending_tool_calls"] = []
        
        # 添加用户消息
        if user_input:
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append({"role": "user", "content": user_input})
        
        # 处理附件
        if attachments:
            state["attachments"] = attachments
        
        try:
            # 运行状态图
            final_state = await self.graph.ainvoke(state)

            # 序列化状态以便保存到数据库
            serialized_state = self._serialize_state_for_db(final_state)

            # 构建响应
            return AgentResponse(
                message=final_state.get("current_response", ""),
                stage=final_state.get("stage", "collecting"),
                progress=final_state.get("progress", 0),
                quick_options=final_state.get("quick_options", []),
                risk_level=final_state.get("risk_level"),
                specialty_data=final_state.get("specialty_data"),
                next_state=serialized_state
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return AgentResponse(
                message=f"抱歉，处理您的请求时出现了问题: {str(e)}",
                stage=state.get("stage", "collecting"),
                progress=state.get("progress", 0),
                quick_options=[],
                next_state=state
            )
    
    @classmethod
    def reset_graph(cls):
        """重置编译后的图"""
        cls._compiled_graph = None

    def _serialize_state_for_db(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        将状态序列化为 JSON 可序列化的格式

        LangGraph 的 add_messages 会在状态中添加 LangChain Message 对象，
        这些对象无法直接序列化到 JSON，需要转换为普通字典
        """
        serialized = {}
        for key, value in state.items():
            # 跳过特定字段
            if key.startswith("_"):
                continue

            # 处理 LangChain Message 对象列表
            if isinstance(value, list) and value:
                if all(isinstance(item, BaseMessage) for item in value):
                    # 全是 Message 对象，转换为字典
                    serialized[key] = [
                        {"type": msg.type, "content": msg.content}
                        for msg in value
                    ]
                    continue
                elif all(isinstance(item, (dict, str, int, float, bool, type(None))) for item in value):
                    # 基本类型列表，直接保留
                    serialized[key] = value
                    continue
                else:
                    # 混合类型，逐个处理
                    serialized[key] = []
                    for item in value:
                        if isinstance(item, BaseMessage):
                            serialized[key].append({"type": item.type, "content": item.content})
                        elif isinstance(item, dict):
                            serialized[key].append(self._serialize_dict(item))
                        else:
                            serialized[key].append(item)
                    continue

            # 处理字典
            if isinstance(value, dict):
                serialized[key] = self._serialize_dict(value)
            else:
                # 基本类型直接保留
                serialized[key] = value

        return serialized

    def _serialize_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """递归序列化字典中的非 JSON 类型"""
        result = {}
        for k, v in d.items():
            if isinstance(v, BaseMessage):
                result[k] = {"type": v.type, "content": v.content}
            elif isinstance(v, dict):
                result[k] = self._serialize_dict(v)
            elif isinstance(v, list):
                result[k] = [
                    {"type": item.type, "content": item.content} if isinstance(item, BaseMessage) else item
                    for item in v
                ]
            else:
                result[k] = v
        return result


# 兼容旧版导入 - 别名
create_initial_state = create_react_initial_state
LangGraphAgent = ReActAgent
AgentState = ReActAgentState
