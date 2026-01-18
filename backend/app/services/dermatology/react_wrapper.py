"""
ReAct Agent API 适配层

实现 BaseAgent 接口，保持与现有 API 兼容
"""
import re
from typing import Dict, Any, Optional, Callable, Awaitable, List
from langchain_core.messages import HumanMessage, AIMessage

from ..base import BaseAgent
from .react_state import create_react_initial_state
from .react_agent import get_derma_react_graph
from .quick_options import generate_quick_options


# JSON 特征关键词列表（诊断相关）
_JSON_FIELD_KEYWORDS = {
    '"care_plan"', '"conditions"', '"summary"', '"risk_level"',
    '"confidence"', '"rationale"', '"need_offline_visit"', '"urgency"',
    '"reasoning_steps"', '"references"', '"evidence"', '"title":', '"content":',
    '"name":', '"id":', '"timestamp"'
}


def _is_json_content(text: str) -> bool:
    """检测文本是否为 JSON 格式"""
    if not text:
        return False
    stripped = text.strip()
    # 检测是否以 { 或 [ 开头
    if stripped.startswith('{') or stripped.startswith('['):
        # 检测是否包含 JSON 键名特征
        for keyword in _JSON_FIELD_KEYWORDS:
            if keyword in stripped:
                return True
        # 检测通用 JSON 模式："key": value
        if re.search(r'"[a-z_]+"\s*:', stripped):
            return True
    return False


def _looks_like_json_start(text: str) -> bool:
    """检测文本是否像是 JSON 块的开始"""
    stripped = text.strip()
    # 以 { 开头且紧跟 " 或换行后 "
    if stripped.startswith('{'):
        rest = stripped[1:].lstrip()
        if rest.startswith('"') or rest.startswith('\n'):
            return True
    return False


def _contains_json_field_keyword(text: str) -> bool:
    """检测文本是否包含 JSON 字段关键词"""
    for keyword in _JSON_FIELD_KEYWORDS:
        if keyword in text:
            return True
    return False


def _filter_json_from_response(text: str) -> str:
    """从 AI 回复中过滤掉 JSON 内容"""
    if not text:
        return text
    
    # 如果整个内容都是 JSON，返回空字符串
    if _is_json_content(text):
        return ""
    
    # 尝试移除文本中嵌入的 JSON 块（支持嵌套）
    # 使用更健壮的方法：追踪括号层级
    result = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '{':
            # 尝试找到匹配的 }
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                j += 1
            # 检查这个块是否包含 JSON 特征
            block = text[i:j]
            if _contains_json_field_keyword(block) or re.search(r'"[a-z_]+"\s*:', block):
                # 跳过整个 JSON 块
                i = j
                continue
            else:
                # 不是 JSON，保留
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    
    cleaned = ''.join(result)
    # 清理多余的空行
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


class StreamingJsonFilter:
    """
    流式 JSON 过滤器
    
    用于在流式输出时检测并过滤 JSON 块，避免用户看到 "先闪 JSON，再被覆盖" 的现象。
    """
    
    def __init__(self):
        self._buffer = ""  # 累积缓冲区
        self._in_json_block = False  # 是否正在 JSON 块内
        self._brace_depth = 0  # 花括号深度
        self._pending_output = ""  # 待输出内容
    
    def process_chunk(self, chunk: str) -> str:
        """
        处理一个流式 chunk，返回应该输出的内容
        
        Returns:
            应该发送给前端的内容，可能为空字符串
        """
        if not chunk:
            return ""
        
        output = []
        
        for char in chunk:
            if self._in_json_block:
                # 正在 JSON 块内，追踪括号
                self._buffer += char
                if char == '{':
                    self._brace_depth += 1
                elif char == '}':
                    self._brace_depth -= 1
                    if self._brace_depth == 0:
                        # JSON 块结束，检查是否确实是 JSON
                        if _contains_json_field_keyword(self._buffer) or re.search(r'"[a-z_]+"\s*:', self._buffer):
                            # 确认是 JSON，丢弃整个块
                            pass
                        else:
                            # 不是 JSON，输出缓冲区内容
                            output.append(self._buffer)
                        self._buffer = ""
                        self._in_json_block = False
            else:
                # 不在 JSON 块内
                if char == '{':
                    # 可能是 JSON 块开始
                    # 先输出之前累积的待输出内容
                    if self._pending_output:
                        output.append(self._pending_output)
                        self._pending_output = ""
                    # 开始追踪
                    self._in_json_block = True
                    self._brace_depth = 1
                    self._buffer = char
                else:
                    # 普通字符，累积到待输出
                    self._pending_output += char
                    # 如果累积了足够内容且不以 JSON 相关字符结尾，可以输出
                    if len(self._pending_output) > 20 and not self._pending_output.rstrip().endswith(('"', ':')):
                        output.append(self._pending_output)
                        self._pending_output = ""
        
        return ''.join(output)
    
    def flush(self) -> str:
        """
        刷新剩余内容
        
        Returns:
            剩余的待输出内容
        """
        result = self._pending_output
        # 如果还在 JSON 块内但未闭合，也尝试输出（可能不是 JSON）
        if self._in_json_block and self._buffer:
            if not _contains_json_field_keyword(self._buffer):
                result += self._buffer
        self._pending_output = ""
        self._buffer = ""
        self._in_json_block = False
        self._brace_depth = 0
        return result


def _serialize_messages(messages: list) -> List[dict]:
    """序列化消息为 JSON 格式"""
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        elif hasattr(msg, "content"):
            role = "assistant" if getattr(msg, "type", "") == "ai" else "user"
            if hasattr(msg, "type") and msg.type == "system":
                continue  # 跳过 system 消息
            if hasattr(msg, "type") and msg.type == "tool":
                continue  # 跳过 tool 消息
            serialized.append({
                "role": role,
                "content": msg.content
            })
    return serialized


class DermaReActWrapper(BaseAgent):
    """
    皮肤科 ReAct Agent 适配器
    
    实现 BaseAgent 接口，内部使用 ReAct 模式
    """
    
    def __init__(self):
        self._graph = get_derma_react_graph()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        state = create_react_initial_state(session_id, user_id)
        # 转换为普通 dict
        return dict(state)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        
        # 添加用户消息
        if user_input:
            state["messages"].append(HumanMessage(content=user_input))
        
        # 处理附件（图片）
        if attachments:
            for att in attachments:
                att_type = att.get("type", "")
                if att_type == "image" or att_type.startswith("image/"):
                    state["pending_attachments"].append(att)
        
        # 运行状态图
        if on_chunk:
            final_state = await self._run_with_stream(state, on_chunk)
        else:
            final_state = await self._graph.ainvoke(state)
        
        # 提取最后的 AI 回复
        ai_response = ""
        for msg in reversed(final_state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                ai_response = msg.content
                break
            elif isinstance(msg, AIMessage):
                ai_response = msg.content
                break
        
        # 过滤 JSON 内容
        ai_response = _filter_json_from_response(ai_response)
        
        # 如果过滤后为空，且有诊断卡，生成默认的自然语言回复
        if not ai_response and final_state.get("diagnosis_card"):
            diagnosis_card = final_state["diagnosis_card"]
            summary = diagnosis_card.get("summary", "")
            risk_level = diagnosis_card.get("risk_level", "low")
            need_visit = diagnosis_card.get("need_offline_visit", False)
            care_plan = diagnosis_card.get("care_plan", [])
            
            # 生成自然语言回复
            risk_text = {"low": "低", "medium": "中等", "high": "较高", "emergency": "紧急"}.get(risk_level, "")
            ai_response = f"根据您的症状描述，{summary}\n\n"
            if risk_text:
                ai_response += f"风险等级：{risk_text}\n\n"
            if care_plan:
                ai_response += "护理建议：\n"
                for i, advice in enumerate(care_plan[:5], 1):
                    ai_response += f"{i}. {advice}\n"
            if need_visit:
                urgency = diagnosis_card.get("urgency", "")
                ai_response += f"\n建议就医：{urgency if urgency else '建议尽早到医院皮肤科就诊确认诊断。'}"
        
        final_state["current_response"] = ai_response
        
        # 生成快捷选项
        if ai_response:
            final_state["quick_options"] = generate_quick_options(ai_response)
        
        # 序列化消息
        final_state["messages"] = _serialize_messages(final_state.get("messages", []))
        
        return final_state
    
    async def _run_with_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Callable[[str], Awaitable[None]]
    ) -> Dict[str, Any]:
        """流式输出运行"""
        final_state = state.copy()
        
        # 使用流式 JSON 过滤器，避免用户看到"先闪 JSON 再被覆盖"的现象
        json_filter = StreamingJsonFilter()
        
        async for event in self._graph.astream_events(state, version="v2"):
            if event.get("event") == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    # 过滤掉工具调用相关的内容
                    if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                        continue
                    
                    # 使用流式 JSON 过滤器处理
                    content = chunk.content
                    
                    # 快速检查：如果整个 chunk 明显是 JSON，直接跳过
                    if _is_json_content(content):
                        continue
                    
                    # 通过流式过滤器处理（处理跨 chunk 的 JSON 块）
                    filtered_content = json_filter.process_chunk(content)
                    if filtered_content:
                        await on_chunk(filtered_content)
            elif event.get("event") == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict):
                    # 合并状态更新，特殊处理关键字段避免被空值覆盖
                    list_fields = ("advice_history", "knowledge_refs", "reasoning_steps", "skin_analyses")
                    dict_fields = ("diagnosis_card", "latest_analysis", "latest_interpretation")
                    for key, value in output.items():
                        if value is not None:
                            # 对于列表字段，只有当新值非空时才更新
                            if key in list_fields:
                                if value and len(value) > 0:
                                    existing = final_state.get(key, [])
                                    # 如果新值包含更多或相同数量的数据，使用新值
                                    if len(value) >= len(existing):
                                        final_state[key] = value
                            # 对于字典字段，只有当新值是有效字典时才更新
                            elif key in dict_fields:
                                if isinstance(value, dict) and len(value) > 0:
                                    final_state[key] = value
                            else:
                                final_state[key] = value
                    # === 调试日志 ===
                    if "advice_history" in output:
                        adv_val = output.get('advice_history')
                        print(f"[DEBUG] _run_with_stream: 捕获到 advice_history 更新")
                        print(f"[DEBUG]   - 值类型: {type(adv_val).__name__}")
                        print(f"[DEBUG]   - 值是否为None: {adv_val is None}")
                        print(f"[DEBUG]   - 数量: {len(adv_val) if adv_val else 0}")
                    if "diagnosis_card" in output:
                        diag_val = output.get('diagnosis_card')
                        print(f"[DEBUG] _run_with_stream: 捕获到 diagnosis_card 更新")
                        print(f"[DEBUG]   - 值类型: {type(diag_val).__name__}")
                        print(f"[DEBUG]   - 值是否为None: {diag_val is None}")
                    # === 日志结束 ===
        
        # 刷新流式过滤器中剩余的内容
        remaining = json_filter.flush()
        if remaining:
            await on_chunk(remaining)
        
        # === 调试日志：最终状态 ===
        print(f"[DEBUG] _run_with_stream 最终状态:")
        adv_final = final_state.get('advice_history')
        diag_final = final_state.get('diagnosis_card')
        print(f"[DEBUG] - advice_history: 类型={type(adv_final).__name__}, 是None={adv_final is None}, 数量={len(adv_final) if adv_final else 0}")
        print(f"[DEBUG] - diagnosis_card: 类型={type(diag_final).__name__}, 是None={diag_final is None}")
        if adv_final:
            for i, adv in enumerate(adv_final):
                print(f"[DEBUG]   - [{i}] {adv.get('title', 'N/A')}")
        # === 日志结束 ===
        
        return final_state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return {
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png"],
            "ui_components": ["TextBubble", "SkinAnalysisCard"],
            "description": "皮肤科 ReAct AI 智能体"
        }
