import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from ..config import get_settings

settings = get_settings()


class QwenService:
    """使用 OpenAI 兼容接口调用阿里千问"""

    @staticmethod
    def build_system_prompt(
        doctor_name: str, 
        doctor_title: str, 
        specialty: str,
        persona_prompt: str = None,
        rag_context: str = None
    ) -> str:
        if persona_prompt:
            base_prompt = persona_prompt
        else:
            base_prompt = f"""你是{doctor_name}医生的AI分身，职称是{doctor_title}。
擅长领域：{specialty}

你的职责是：
1. 以专业、温和、耐心的态度回答患者的健康咨询
2. 根据患者描述的症状，给出初步的分析和建议
3. 必要时建议患者进行相关检查或线下就医
4. 不做确定性诊断，只提供参考建议

注意事项：
- 回复要简洁明了，控制在200字以内
- 如果问题超出你的专业范围，请诚实告知并建议咨询相关科室
- 遇到紧急情况，请建议患者立即就医或拨打急救电话"""
        
        if rag_context:
            base_prompt += f"\n\n{rag_context}\n\n请结合以上参考资料回答患者问题。"
        
        return base_prompt

    @classmethod
    async def get_ai_response(
        cls,
        user_message: str,
        doctor_name: str = "AI助手",
        doctor_title: str = "主治医师",
        specialty: str = "全科医学",
        history: list[dict] = None,
        persona_prompt: str = None,
        rag_context: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        if not settings.LLM_API_KEY:
            return f"您好，我是{doctor_name}医生AI分身。感谢您的咨询，根据您描述的情况，建议您注意休息，保持良好的生活习惯。如果症状持续，建议到医院进行详细检查。"

        system_prompt = cls.build_system_prompt(
            doctor_name, doctor_title, specialty, 
            persona_prompt=persona_prompt, 
            rag_context=rag_context
        )

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history[-6:]:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        # 使用传入的参数或默认配置
        use_model = model or settings.LLM_MODEL
        use_temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        use_max_tokens = max_tokens or 500

        try:
            api_url = f"{settings.LLM_BASE_URL}/chat/completions"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": use_model,
                        "messages": messages,
                        "temperature": use_temperature,
                        "max_tokens": use_max_tokens
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and len(choices) > 0:
                        return choices[0].get("message", {}).get("content", "抱歉，暂时无法回复，请稍后再试。")
                    return "抱歉，暂时无法回复，请稍后再试。"
                else:
                    print(f"LLM API error: {response.status_code} - {response.text}")
                    return "医生繁忙，请稍后再试。"

        except Exception as e:
            print(f"LLM API exception: {e}")
            return "网络繁忙，请稍后再试。"

    @classmethod
    async def chat_with_tools(
        cls,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        tool_choice: str = "auto",
        max_tokens: int = 2000,
        temperature: float = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        调用 LLM with Function Calling 支持

        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI Function Calling 格式）
            tool_choice: 工具选择模式 ("auto", "none", "required")
            max_tokens: 最大 token 数
            temperature: 温度参数
            model: 模型名称

        Returns:
            {
                "content": str,           # AI 回复内容
                "tool_calls": list,       # 工具调用列表
                "finish_reason": str      # 结束原因
            }
        """
        if not settings.LLM_API_KEY:
            return {
                "content": "API Key 未配置",
                "tool_calls": [],
                "finish_reason": "stop"
            }

        use_model = model or settings.LLM_MODEL
        use_temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE

        # 构建请求体
        request_body = {
            "model": use_model,
            "messages": messages,
            "temperature": use_temperature,
            "max_tokens": max_tokens,
        }

        # 添加工具定义
        if tools:
            request_body["tools"] = cls._convert_tools_to_openai_format(tools)
            if tool_choice:
                request_body["tool_choice"] = tool_choice

        try:
            api_url = f"{settings.LLM_BASE_URL}/chat/completions"

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )

                if response.status_code == 200:
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {})

                    # 解析工具调用
                    tool_calls = []
                    if "tool_calls" in message:
                        for tc in message["tool_calls"]:
                            tool_calls.append({
                                "id": tc.get("id", ""),
                                "type": tc.get("type", "function"),
                                "function": {
                                    "name": tc.get("function", {}).get("name", ""),
                                    "arguments": tc.get("function", {}).get("arguments", "{}")
                                }
                            })

                    return {
                        "content": message.get("content", ""),
                        "tool_calls": tool_calls,
                        "finish_reason": choice.get("finish_reason", "stop")
                    }
                else:
                    print(f"LLM API error: {response.status_code} - {response.text}")
                    return {
                        "content": "调用 LLM 失败",
                        "tool_calls": [],
                        "finish_reason": "error"
                    }

        except Exception as e:
            print(f"LLM API exception in chat_with_tools: {e}")
            import traceback
            traceback.print_exc()
            return {
                "content": f"系统错误: {str(e)}",
                "tool_calls": [],
                "finish_reason": "error"
            }

    @classmethod
    async def chat_with_tools_stream(
        cls,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        tool_choice: str = "auto",
        max_tokens: int = 2000,
        temperature: float = None,
        model: str = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式调用 LLM with Function Calling 支持

        Args:
            messages: 消息列表
            tools: 工具定义列表
            tool_choice: 工具选择模式
            max_tokens: 最大 token 数
            temperature: 温度参数
            model: 模型名称

        Yields:
            {
                "type": "content" | "tool_call",
                "delta": str,              # 内容增量（type=content 时）
                "tool_call": dict,         # 工具调用（type=tool_call 时）
                "done": bool               # 是否结束
            }
        """
        if not settings.LLM_API_KEY:
            yield {"type": "error", "content": "API Key 未配置", "done": True}
            return

        use_model = model or settings.LLM_MODEL
        use_temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE

        # 构建请求体
        request_body = {
            "model": use_model,
            "messages": messages,
            "temperature": use_temperature,
            "max_tokens": max_tokens,
            "stream": True,  # 启用流式
        }

        # 添加工具定义
        if tools:
            request_body["tools"] = cls._convert_tools_to_openai_format(tools)
            if tool_choice:
                request_body["tool_choice"] = tool_choice

        try:
            api_url = f"{settings.LLM_BASE_URL}/chat/completions"

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"LLM API error: {response.status_code} - {error_text}")
                        yield {"type": "error", "content": "调用 LLM 失败", "done": True}
                        return

                    # 解析 SSE 流
                    tool_calls_buffer = {}
                    pending_tool_calls = []

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                # 发送所有待处理的工具调用
                                for tc in pending_tool_calls:
                                    yield {"type": "tool_call", "tool_call": tc, "done": False}
                                yield {"type": "done", "done": True}
                                return

                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if not choices:
                                    continue

                                delta = choices[0].get("delta", {})

                                # 处理内容
                                if "content" in delta and delta["content"]:
                                    yield {
                                        "type": "content",
                                        "delta": delta["content"],
                                        "done": False
                                    }

                                # 处理工具调用
                                if "tool_calls" in delta:
                                    for tc_delta in delta["tool_calls"]:
                                        index = tc_delta.get("index", 0)
                                        tc_id = tc_delta.get("id", "")

                                        if tc_id:
                                            tool_calls_buffer[index] = {
                                                "id": tc_id,
                                                "type": tc_delta.get("type", "function"),
                                                "function": {
                                                    "name": "",
                                                    "arguments": ""
                                                }
                                            }

                                        if "function" in tc_delta:
                                            func_delta = tc_delta["function"]

                                            # 更新函数名
                                            if "name" in func_delta:
                                                tool_calls_buffer[index]["function"]["name"] = func_delta["name"]

                                            # 追加参数
                                            if "arguments" in func_delta:
                                                tool_calls_buffer[index]["function"]["arguments"] += func_delta["arguments"]

                                        # 检查工具调用是否完成
                                        tc = tool_calls_buffer[index]
                                        if tc_delta.get("arguments") is None or choices[0].get("finish_reason") == "tool_calls":
                                            # 工具调用完成
                                            # 尝试解析参数
                                            try:
                                                arguments = json.loads(tc["function"]["arguments"])
                                            except json.JSONDecodeError:
                                                arguments = tc["function"]["arguments"]

                                            complete_tc = {
                                                "id": tc["id"],
                                                "type": "function",
                                                "function": {
                                                    "name": tc["function"]["name"],
                                                    "arguments": json.dumps(arguments) if isinstance(arguments, dict) else arguments
                                                }
                                            }

                                            if index < len(pending_tool_calls):
                                                pending_tool_calls[index] = complete_tc
                                            else:
                                                pending_tool_calls.append(complete_tc)
                                                yield {"type": "tool_call", "tool_call": complete_tc, "done": False}

                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                print(f"Error parsing SSE data: {e}")
                                continue

                    # 最终确认
                    yield {"type": "done", "done": True}

        except Exception as e:
            print(f"LLM API exception in chat_with_tools_stream: {e}")
            import traceback
            traceback.print_exc()
            yield {"type": "error", "content": f"系统错误: {str(e)}", "done": True}

    @staticmethod
    def _convert_tools_to_openai_format(tools: List[Dict[str, Any]]) -> List[Dict]:
        """
        将内部工具格式转换为 OpenAI Function Calling 格式

        Args:
            tools: [{"function": {"name": "xxx", "description": "xxx", "parameters": {...}}}]

        Returns:
            OpenAI 格式的工具列表
        """
        openai_tools = []
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {
                            "type": "object",
                            "properties": {},
                            "required": []
                        })
                    }
                })
        return openai_tools
