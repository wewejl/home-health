import httpx
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
