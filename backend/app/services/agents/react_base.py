"""
ReAct Agent 基类

实现 Observe → Think → Act 循环的智能体基类
所有科室智能体继承此类，实现完全自主的 AI 决策
"""
import json
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from ..qwen_service import QwenService
from ...schemas.agent_response import AgentResponse
from .tools import TOOL_REGISTRY, ALL_TOOL_SCHEMAS, execute_tools_parallel

logger = logging.getLogger(__name__)

# 🆕 CRITICAL FIX: 限制消息历史大小，防止内存泄漏
MAX_MESSAGE_HISTORY = 50
MAX_REASONING_HISTORY = 100
SUPPORTED_KNOWLEDGE_SPECIALTIES = {
    "dermatology",
    "cardiology",
    "orthopedics",
    "neurology",
    "respiratory",
    "gastroenterology",
    "endocrinology",
    "ophthalmology",
    "otorhinolaryngology",
    "stomatology",
    "obstetrics_gynecology",
    "pediatrics",
    "general",
}


class ThoughtEntry(TypedDict, total=False):
    """单条思考记录"""
    step: int
    timestamp: str
    thought: str
    intent_analysis: str
    state_assessment: str
    decision: str
    action: str
    tool_used: Optional[str]



class ReActAgentState(TypedDict, total=False):
    """ReAct Agent 状态"""
    # 会话标识
    session_id: str
    user_id: int
    agent_type: str

    # 🆕 对话历史（使用字典列表，避免序列化问题）
    messages: List[dict]  # [{"type": "human", "content": "..."}, {"type": "ai", "content": "..."}]

    # AI 决策（结构化 JSON）
    agent_decision: dict
    
    # 工具调用
    pending_tool_calls: List[dict]
    tool_results: List[dict]

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

    # 🆕 思考追踪（不放入 messages，单独持久化）
    current_thought: str
    reasoning_history: List[ThoughtEntry]
    show_thinking: bool

    # 🆕 已问问题追踪（防止重复提问）
    asked_questions: List[str]


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
        # 🆕 思考追踪初始化
        "current_thought": "",
        "reasoning_history": [],
        "show_thinking": False,
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

        # 新用户输入优先触发知识检索，避免“只在疑难问题才查知识库”
        if self._should_prefetch_knowledge(state):
            query = self._build_knowledge_query(state)
            if query:
                specialty = self._get_knowledge_specialty(state)
                tool_call = {
                    "function": {
                        "name": "search_medical_knowledge",
                        "arguments": json.dumps(
                            {"query": query, "specialty": specialty, "top_k": 5},
                            ensure_ascii=False
                        )
                    }
                }

                state["pending_tool_calls"] = [tool_call]
                state["current_thought"] = "先检索相关医学知识，再进行问诊推理。"
                self._save_thought_to_history(
                    state,
                    state["iteration_count"],
                    state["current_thought"],
                    "use_tool",
                    "search_medical_knowledge",
                )
                state["agent_decision"] = {
                    "action": "use_tool",
                    "tool_calls": [tool_call],
                    "thought": state["current_thought"],
                }
                return state
        
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

                # 提取并保存思考
                thought_content = result.get("content", "")
                state["current_thought"] = thought_content
                self._save_thought_to_history(
                    state, state["iteration_count"], thought_content, "use_tool",
                    tool_calls[0].get("function", {}).get("name") if tool_calls else None
                )

                state["agent_decision"] = {
                    "action": "use_tool",
                    "tool_calls": tool_calls,
                    "thought": thought_content
                }
            else:
                # AI 决定直接回复
                content = result.get("content", "")
                decision = self._parse_decision(content)

                # 提取并保存思考
                thought = decision.get("thought", "")
                if not thought:
                    thought = self._extract_thought_from_response(content)
                state["current_thought"] = thought

                self._save_thought_to_history(
                    state, state["iteration_count"], thought,
                    decision.get("action", "respond")
                )

                state["agent_decision"] = decision

        except Exception as e:
            state["error"] = str(e)
            state["agent_decision"] = {
                "action": "respond",
                "response": "抱歉，处理时出现了问题，请稍后重试。"
            }
        
        return state

    def _get_human_messages(self, state: Dict[str, Any]) -> List[dict]:
        """获取人类消息列表（按时间顺序）"""
        return [
            m for m in state.get("messages", [])
            if isinstance(m, dict) and m.get("type") == "human"
        ]

    def _build_knowledge_query(self, state: Dict[str, Any]) -> str:
        """构建知识检索查询"""
        human_messages = self._get_human_messages(state)
        if not human_messages:
            return ""
        latest = (human_messages[-1].get("content") or "").strip()
        return latest[:300]

    def _get_knowledge_specialty(self, state: Dict[str, Any]) -> str:
        """根据 agent_type 推断知识库 specialty"""
        agent_type = (state.get("agent_type") or "general").strip().lower()
        if agent_type in SUPPORTED_KNOWLEDGE_SPECIALTIES:
            return agent_type
        return "general"

    def _should_prefetch_knowledge(self, state: Dict[str, Any]) -> bool:
        """
        判断是否需要预检索知识库

        规则：
        1. 当前智能体支持 search_medical_knowledge 工具
        2. 至少有一条用户消息
        3. 针对“当前最新用户消息”尚未做过知识检索
        """
        if "search_medical_knowledge" not in self._tools:
            return False

        human_messages = self._get_human_messages(state)
        if not human_messages:
            return False

        latest_human_index = len(human_messages) - 1
        specialty_data = state.get("specialty_data") or {}
        last_prefetch_index = specialty_data.get("_kb_prefetch_human_index")

        if last_prefetch_index == latest_human_index:
            return False

        return True
    
    def _build_reasoning_messages(self, state: Dict[str, Any]) -> List[dict]:
        """构建推理所需的消息列表"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]

        # 添加对话历史（现在 messages 是字典列表）
        for msg in state.get("messages", [])[-10:]:  # 最近10条
            if isinstance(msg, dict):
                msg_type = msg.get("type", "")
                if msg_type == "human":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg_type == "ai":
                    messages.append({"role": "assistant", "content": msg.get("content", "")})
                else:
                    # 兼容旧格式 role
                    role = msg.get("role", "user")
                    messages.append({"role": role, "content": msg.get("content", "")})

        # 添加工具调用结果
        for result in state.get("tool_results", []):
            messages.append({
                "role": "assistant",
                "content": f"[工具调用结果] {result.get('tool')}: {json.dumps(result.get('result'), ensure_ascii=False)}"
            })

        # 添加思考历史（让 AI 看到自己之前的思考过程）
        reasoning_history = state.get("reasoning_history", [])
        if reasoning_history:
            history_summary = self._format_reasoning_history(reasoning_history)
            messages.append({
                "role": "system",
                "content": f"[之前的思考过程]\n{history_summary}"
            })

        return messages

    def _format_reasoning_history(self, history: List[ThoughtEntry]) -> str:
        """格式化思考历史为文本"""
        if not history:
            return "暂无"

        parts = []
        for entry in history[-5:]:  # 只显示最近5条
            parts.append(f"步骤{entry.get('step')}: {entry.get('thought', '')[:50]}...")

        return "\n".join(parts)

    def _save_thought_to_history(
        self,
        state: Dict[str, Any],
        step: int,
        thought: str,
        action: str,
        tool_used: Optional[str] = None
    ):
        """
        保存思考到历史记录

        CRITICAL FIX: 限制 reasoning_history 大小，防止内存泄漏
        """
        history = state.get("reasoning_history", [])
        if not isinstance(history, list):
            history = []

        thought_entry: ThoughtEntry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "action": action,
        }

        if tool_used:
            thought_entry["tool_used"] = tool_used

        history.append(thought_entry)

        # CRITICAL FIX: 限制历史大小
        if len(history) > MAX_REASONING_HISTORY:
            history = history[-MAX_REASONING_HISTORY:]

        state["reasoning_history"] = history

        logger.debug(f"[ReAct] Step {step}: {action} | Thought: {thought[:100]}...")

    def _extract_thought_from_response(self, content: str) -> str:
        """
        从 AI 响应中提取思考内容

        支持多种格式：
        1. JSON 中的 thought 字段
        2. ```thinking ... ``` 代码块
        3. ## 思考 ... 标题下的内容
        """
        import re

        # 尝试提取 JSON 中的 thought 字段
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if parsed.get("thought"):
                    return parsed["thought"]
            except:
                pass

        # 尝试提取 ```thinking ... ``` 代码块
        thinking_match = re.search(r'```thinking\s*(.*?)\s*```', content, re.DOTALL)
        if thinking_match:
            return thinking_match.group(1).strip()

        # 尝试提取 ## 思考 下的内容
        thinking_section = re.search(r'## 思考\s*\n+(.*?)(?=##|```json|$)', content, re.DOTALL)
        if thinking_section:
            return thinking_section.group(1).strip()

        # 如果都没找到，返回前 500 字符作为思考
        lines = content.split('\n')
        thought_lines = []
        for line in lines:
            line = line.strip()
            # 跳过明显的决策部分
            if line.startswith('```json') or line.startswith('"action"') or line.startswith('"tool_calls"'):
                break
            if line:
                thought_lines.append(line)

        result = '\n'.join(thought_lines[:10])  # 最多 10 行
        return result[:500] if result else "思考过程未详细记录"

    def _get_decision_instruction(self, state: Dict[str, Any]) -> str:
        """
        获取决策指令

        设计理念：
        1. 阶段框架是参考，不是硬性限制
        2. AI 自主判断何时信息充分
        3. 每次追问提供快速选项，降低用户输入门槛
        """
        attachments = state.get("attachments", [])
        has_image = any(
            att.get("type") == "image" or "image" in att.get("mime_type", "")
            for att in attachments
        )

        messages = state.get("messages", [])

        # 计算对话轮数（用户消息数量）
        conversation_rounds = len([
            m for m in messages
            if isinstance(m, dict) and m.get("type") == "human"
        ])

        instruction = f"""# AI 医生助手指令

## ⚠️ 输出格式要求

**你必须严格按照以下 JSON 格式输出：**

```json
{{
  "thought": "你的深度思考过程",
  "action": "respond",
  "response": "给患者的回复内容",
  "quick_options": ["选项1", "选项2"],
  "ready_to_diagnose": false,
  "stage": "collecting"
}}
```

## 🎯 你的角色

你是一位经验丰富的 AI 医生助手。通过渐进式问诊收集信息，然后给出专业建议。

## 📋 渐进式问诊流程

**按以下顺序逐步收集信息，每次只问 1-2 个问题：**

1. **时间线** - 什么时候开始的？突然还是逐渐？
2. **症状性质** - 具体什么感觉？
3. **伴随症状** - 还有其他不适吗？
4. **环境关联** - 什么情况下加重/缓解？
5. **干预史** - 做过什么检查吗？
6. **个人史** - 相关病史

**重要：问完 4-6 个问题后应该给出综合分析，不要一直问下去！**

## 💬 回复格式

### A. 信息收集阶段

**结构：**
```
[先给一点初步分析，让用户感觉被理解]

[然后提1-2个具体问题]
```

**示例：**
```
装修后的环境因素确实可能对呼吸道产生刺激，比如甲醛等挥发性物质在温度升高时释放量增加。不过喉咙疼痛的原因也需要结合其他症状来综合判断，比如感染或过敏等。

您提到症状是在过年后回来且天气暖和后出现的，具体是从哪一天开始喉咙明显疼痛或不适的？是突然发生的还是逐渐加重的？
```

### B. 综合分析阶段

**必须包含：**

```
### 最可能的原因：**[病名]**
[简要解释，用通俗语言]

其他可能性较小的原因包括：
- **[病名2]**：[解释]
- **[病名3]**：[解释]

### 下一步建议
1. [具体建议1]
2. [具体建议2]

### 何时需要就医？
- [就医指征1]
- [就医指征2]

[同理心结尾]
```

**示例：**
```
### 最可能的原因：**环境刺激或过敏反应**
装修两年多的房子，虽然已经过了初期高浓度释放期，但温度升高时，家具、板材中的甲醛等挥发性有机物释放量会增加。这些物质会刺激咽喉黏膜，引发灼烧感、疼痛。卧室通常空间封闭，空气流通差，污染物容易积聚，所以夜间症状更明显。

其他可能性较小的原因包括：
- **病毒感染**：比如普通感冒，但通常伴有低烧、乏力等
- **胃酸反流**：夜间平躺时胃酸可能刺激咽喉，但通常会有反酸、烧心感

### 下一步建议：从环境改善入手
1. 加强通风 - 每天至少开窗通风两次，每次30分钟以上
2. 降低卧室污染物浓度 - 使用空气净化器，睡前开窗通风
3. 临时缓解症状 - 温盐水漱口、多喝温水

### 何时需要就医？
如果经过上述调整3-5天，症状没有缓解或继续加重，建议到耳鼻喉科就诊。

喉咙的疼痛和不适通过环境调整和适当护理大多可以缓解，不用太焦虑。
```

## 🤔 思考过程要求

每次都要思考：
1. **用户说了什么新信息**
2. **现在已经知道什么**（汇总之前的对话）
3. **还缺什么关键信息**
4. **下一步问什么**（不要重复已问的）

**示例：**
```
用户已经说明喉咙不适是天气转暖后逐渐加重的，这可能与环境因素有关。已知：天气转暖后出现、前天开始、逐渐加重。还缺：疼痛性质、伴随症状。下一步应该问疼痛的具体特征。
```

## 🎯 快速选项设计

每次提问提供 2-3 个常见选项，让用户快速选择：

| 问题类型 | 快速选项 |
|---------|---------|
| 疼痛性质 | "刀割样疼痛", "灼烧感", "胀痛/隐痛" |
| 时间 | "1-2天", "3-7天", "一周以上" |
| 程度 | "轻微", "中等", "严重" |
| 是/否 | "是", "否", "不确定" |

## ⚠️ 注意事项

1. **仔细阅读上面的对话历史** - 不要重复问已经了解的信息
2. **每次只问 1-2 个问题** - 不要贪多
3. **先给分析再提问** - 让用户感觉被理解
4. **问完 4-6 个问题后应该给分析** - 不要一直问下去
5. **用通俗语言** - "环境刺激"比"上呼吸道刺激因素"更易懂"""

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

    def _extract_symptoms_from_messages(self, messages: List) -> List[str]:
        """从对话历史中提取症状关键词"""
        symptoms = []
        # 常见症状关键词
        symptom_keywords = [
            "头痛", "发热", "咳嗽", "喉咙痛", "咽痛", "胸痛", "腹痛",
            "恶心", "呕吐", "腹泻", "便秘", "尿频", "尿急",
            "皮疹", "瘙痒", "红肿", "疼痛", "麻木", "乏力"
        ]

        for msg in messages:
            if isinstance(msg, dict) and msg.get("type") == "human":
                content = msg.get("content", "")
                for keyword in symptom_keywords:
                    if keyword in content and keyword not in symptoms:
                        symptoms.append(keyword)

        return symptoms

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
                        # 从对话历史中提取症状作为上下文
                        args["context"] = self._extract_symptoms_from_messages(state.get("messages", []))
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
        elif tool_name == "search_medical_knowledge":
            specialty_data["_kb_prefetch_human_index"] = len(self._get_human_messages(state)) - 1
            specialty_data["knowledge_context"] = result
        
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

        # 🆕 将 AI 的回复加入消息历史（使用 AIMessage + add_messages reducer）
        # CRITICAL FIX: 追加而不是替换，避免丢失历史消息
        current_messages = state.get("messages", [])
        updated_messages = current_messages + [{"type": "ai", "content": response}]

        # 限制消息历史大小
        if len(updated_messages) > MAX_MESSAGE_HISTORY:
            updated_messages = updated_messages[-MAX_MESSAGE_HISTORY:]

        state["messages"] = updated_messages

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
        messages = state.get("messages", [])[-10:]
        specialty_data = state.get("specialty_data", {})

        # 构建对话历史文本
        conversation_text = "\n".join([
            f"{'患者' if m.get('type') == 'human' else 'AI'}: {m.get('content', '')}"
            for m in messages
        ])

        diagnosis_prompt = f"""基于以下对话历史，请给出专业的初步诊断意见：

{conversation_text}

图像分析结果：{specialty_data.get('skin_analysis', {}).get('findings', '无')}
风险评估：{specialty_data.get('risk_assessment', {}).get('risk_level', '未评估')}
知识库参考：{json.dumps(specialty_data.get('knowledge_context', {}), ensure_ascii=False)}

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

        # 🆕 将 AI 的回复加入消息历史（使用 AIMessage + add_messages reducer）
        # CRITICAL FIX: 追加而不是替换，避免丢失历史消息
        current_messages = state.get("messages", [])
        updated_messages = current_messages + [{"type": "ai", "content": response}]

        # 限制消息历史大小
        if len(updated_messages) > MAX_MESSAGE_HISTORY:
            updated_messages = updated_messages[-MAX_MESSAGE_HISTORY:]

        state["messages"] = updated_messages

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
        messages = state.get("messages", [])[-10:]
        specialty_data = state.get("specialty_data", {})

        # 构建对话历史文本
        conversation_text = "\n".join([
            f"{'患者' if m.get('type') == 'human' else 'AI'}: {m.get('content', '')}"
            for m in messages
        ])

        diagnosis_prompt = f"""基于以下对话历史，请给出专业的初步诊断意见：

{conversation_text}

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
        # CRITICAL FIX: 反序列化状态 - 将字典格式的 messages 转换为 BaseMessage 对象

        # 重置迭代计数
        state["iteration_count"] = 0
        state["tool_results"] = []
        state["pending_tool_calls"] = []

        # 🆕 添加用户消息（保留之前的对话历史）
        # CRITICAL FIX: 限制消息历史大小
        if user_input:
            existing_messages = state.get("messages", [])
            new_message = {"type": "human", "content": user_input}
            updated_messages = existing_messages + [new_message] if existing_messages else [new_message]

            # 限制消息历史大小
            if len(updated_messages) > MAX_MESSAGE_HISTORY:
                updated_messages = updated_messages[-MAX_MESSAGE_HISTORY:]

            state["messages"] = updated_messages

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

            # 🆕 提取思考历史
            reasoning_history = final_state.get("reasoning_history", [])

            # 构建响应
            return AgentResponse(
                message=final_state.get("current_response", ""),
                stage=final_state.get("stage", "collecting"),
                progress=final_state.get("progress", 0),
                quick_options=final_state.get("quick_options", []),
                risk_level=final_state.get("risk_level"),
                specialty_data=final_state.get("specialty_data"),
                next_state=serialized_state,
                # 🆕 思考相关字段
                current_thought=final_state.get("current_thought"),
                reasoning_history=reasoning_history,
                show_thinking=final_state.get("show_thinking", False)
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

        # 🆕 添加用户消息（保留之前的对话历史）
        if user_input:
            existing_messages = state.get("messages", [])
            new_message = {"type": "human", "content": user_input}
            updated_messages = existing_messages + [new_message] if existing_messages else [new_message]

            # 限制消息历史大小
            if len(updated_messages) > MAX_MESSAGE_HISTORY:
                updated_messages = updated_messages[-MAX_MESSAGE_HISTORY:]

            state["messages"] = updated_messages

        # 处理附件
        if attachments:
            state["attachments"] = attachments
        
        try:
            # 运行状态图
            final_state = await self.graph.ainvoke(state)

            # 序列化状态以便保存到数据库
            serialized_state = self._serialize_state_for_db(final_state)

            # 🆕 提取思考历史
            reasoning_history = final_state.get("reasoning_history", [])

            # 构建响应
            return AgentResponse(
                message=final_state.get("current_response", ""),
                stage=final_state.get("stage", "collecting"),
                progress=final_state.get("progress", 0),
                quick_options=final_state.get("quick_options", []),
                risk_level=final_state.get("risk_level"),
                specialty_data=final_state.get("specialty_data"),
                next_state=serialized_state,
                # 🆕 思考相关字段
                current_thought=final_state.get("current_thought"),
                reasoning_history=reasoning_history,
                show_thinking=final_state.get("show_thinking", False)
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
            if isinstance(value, list):
                # 检查是否包含 BaseMessage 对象
                has_base_message = any(isinstance(item, BaseMessage) for item in value)
                if has_base_message:
                    # 转换所有 Message 对象为字典
                    serialized[key] = []
                    for item in value:
                        if isinstance(item, BaseMessage):
                            serialized[key].append({"type": item.type, "content": item.content})
                        elif isinstance(item, dict):
                            serialized[key].append(self._serialize_dict(item))
                        else:
                            serialized[key].append(item)
                    continue
                else:
                    # 基本类型列表，直接保留（但需要检查嵌套的字典）
                    serialized[key] = self._serialize_list(value)
                    continue

            # 处理字典
            if isinstance(value, dict):
                serialized[key] = self._serialize_dict(value)
            else:
                # 基本类型直接保留
                serialized[key] = value

        return serialized

    def _serialize_list(self, lst: List) -> List:
        """递归序列化列表中的非 JSON 类型"""
        result = []
        for item in lst:
            if isinstance(item, BaseMessage):
                result.append({"type": item.type, "content": item.content})
            elif isinstance(item, dict):
                result.append(self._serialize_dict(item))
            elif isinstance(item, list):
                result.append(self._serialize_list(item))
            else:
                result.append(item)
        return result

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
