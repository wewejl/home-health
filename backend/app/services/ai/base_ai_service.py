"""
AI 服务基类

提供 LLM 调用、JSON 解析、错误处理等通用功能
"""
import json
import httpx
from typing import Optional, Any, Dict
from ...config import get_settings

settings = get_settings()


class BaseAIService:
    """AI 服务基类"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: float = 60.0
    ):
        self.api_url = f"{settings.LLM_BASE_URL}/chat/completions"
        self.api_key = settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
    
    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_count: int = 3
    ) -> str:
        """
        调用 LLM API
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大 token 数
            retry_count: 重试次数
        
        Returns:
            LLM 响应文本
        """
        if not self.api_key:
            raise ValueError("LLM API Key 未配置")
        
        use_temperature = temperature if temperature is not None else self.temperature
        use_max_tokens = max_tokens or self.max_tokens
        
        last_error = None
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.api_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": use_temperature,
                            "max_tokens": use_max_tokens
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "")
                    else:
                        last_error = f"API error: {response.status_code} - {response.text}"
                        
            except Exception as e:
                last_error = str(e)
                if attempt < retry_count - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # 指数退避
        
        raise Exception(f"LLM 调用失败: {last_error}")
    
    def _parse_json(self, text: str, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        解析 JSON 响应
        
        处理可能的 markdown 代码块包装
        """
        if not text:
            return default or {}
        
        # 尝试提取 JSON 内容
        content = text.strip()
        
        # 处理 markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
        
        content = content.strip()
        
        # 尝试解析 JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试修复常见问题
            try:
                # 尝试找到 JSON 对象的开始和结束
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except:
                pass
            
            return default or {}
    
    def _clean_text(self, text: str) -> str:
        """清理文本，去除多余空白"""
        if not text:
            return ""
        return " ".join(text.split())
    
    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
