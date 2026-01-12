"""
Qwen-VL 多模态服务 - 支持图像理解与分析
用于皮肤科图像识别、报告解读等场景
"""
import base64
import httpx
import json
from typing import Optional, List, Dict, Any
from ..config import get_settings

settings = get_settings()


class QwenVLService:
    """
    Qwen-VL 多模态服务
    支持 Qwen-VL-Plus API 和开源 Qwen-VL 模型
    """
    
    def __init__(self):
        self.api_url = f"{settings.LLM_BASE_URL}/chat/completions"
        self.api_key = settings.LLM_API_KEY
        # 使用 Qwen-VL-Plus 或 Qwen-VL-Max 进行多模态推理
        self.vl_model = getattr(settings, 'QWEN_VL_MODEL', 'qwen-vl-plus')
    
    async def analyze_image(
        self,
        image_url: str = None,
        image_base64: str = None,
        prompt: str = "请描述这张图片",
        system_prompt: str = None,
        temperature: float = 0.5,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        分析图像内容
        
        Args:
            image_url: 图像URL（与image_base64二选一）
            image_base64: 图像Base64编码
            prompt: 分析提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大输出token数
            
        Returns:
            包含分析结果的字典
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API密钥未配置",
                "content": None
            }
        
        if not image_url and not image_base64:
            return {
                "success": False,
                "error": "未提供图像",
                "content": None
            }
        
        # 构建图像内容
        if image_base64:
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            }
        else:
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            }
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                image_content,
                {"type": "text", "text": prompt}
            ]
        })
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.vl_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return {
                            "success": True,
                            "content": content,
                            "usage": data.get("usage", {})
                        }
                    return {
                        "success": False,
                        "error": "无有效响应",
                        "content": None
                    }
                else:
                    print(f"Qwen-VL API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API请求失败: {response.status_code}",
                        "content": None
                    }
                    
        except Exception as e:
            print(f"Qwen-VL API exception: {e}")
            return {
                "success": False,
                "error": f"请求异常: {str(e)}",
                "content": None
            }
    
    async def analyze_skin_image(
        self,
        image_url: str = None,
        image_base64: str = None,
        additional_info: str = ""
    ) -> Dict[str, Any]:
        """
        皮肤影像分析专用方法
        
        Args:
            image_url: 皮肤图像URL
            image_base64: 皮肤图像Base64
            additional_info: 用户补充的症状信息
            
        Returns:
            结构化的皮肤分析结果
        """
        system_prompt = """你是一位专业的皮肤科AI助手，具备丰富的皮肤病学知识。
你的任务是分析用户上传的皮肤图像，识别可能的皮肤问题，并给出专业建议。

分析原则：
1. 仔细观察皮损的形态、颜色、分布、边界等特征
2. 结合常见皮肤病的临床表现进行鉴别
3. 评估病情的严重程度和就医紧迫性
4. 给出合理的护理建议和就医指导
5. 对于不确定的情况，诚实说明并建议线下就医

重要提示：你的分析仅供参考，不能替代专业医生的诊断。"""

        analysis_prompt = f"""请仔细分析这张皮肤图像，并按照以下JSON格式返回结果：

{{
    "lesion_description": "皮损特征描述（形态、颜色、大小、分布等）",
    "possible_conditions": [
        {{"name": "疾病名称1", "confidence": 0.8, "description": "简要说明"}},
        {{"name": "疾病名称2", "confidence": 0.5, "description": "简要说明"}}
    ],
    "risk_level": "low/medium/high/emergency",
    "care_advice": "日常护理建议",
    "need_offline_visit": true或false,
    "visit_urgency": "紧急程度说明",
    "additional_questions": ["需要进一步了解的问题1", "问题2"]
}}

{f"用户补充信息：{additional_info}" if additional_info else ""}

请确保返回有效的JSON格式。如果图像质量不佳或无法识别，请在lesion_description中说明，并将confidence设为较低值。"""

        result = await self.analyze_image(
            image_url=image_url,
            image_base64=image_base64,
            prompt=analysis_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000
        )
        
        if not result["success"]:
            return result
        
        # 解析JSON结果
        try:
            content = result["content"]
            # 处理可能的markdown代码块
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            analysis = json.loads(content.strip())
            return {
                "success": True,
                "analysis": analysis,
                "raw_content": result["content"]
            }
        except json.JSONDecodeError:
            # 如果无法解析JSON，返回原始文本
            return {
                "success": True,
                "analysis": {
                    "lesion_description": result["content"],
                    "possible_conditions": [],
                    "risk_level": "medium",
                    "care_advice": "建议线下就医获取专业诊断",
                    "need_offline_visit": True,
                    "visit_urgency": "建议尽快就诊",
                    "additional_questions": []
                },
                "raw_content": result["content"],
                "parse_error": True
            }
    
    async def interpret_medical_report(
        self,
        image_url: str = None,
        image_base64: str = None,
        report_type: str = "皮肤科检查报告"
    ) -> Dict[str, Any]:
        """
        医学报告解读
        
        Args:
            image_url: 报告图像URL
            image_base64: 报告图像Base64
            report_type: 报告类型
            
        Returns:
            结构化的报告解读结果
        """
        system_prompt = """你是一位专业的医学报告解读助手，擅长解读各类医学检查报告。
你的任务是帮助用户理解报告内容，解释各项指标的含义，并给出健康建议。

解读原则：
1. 准确识别报告中的各项指标和数值
2. 用通俗易懂的语言解释专业术语
3. 标注异常指标并解释其临床意义
4. 给出合理的健康建议
5. 对于严重异常，提醒及时就医

重要提示：报告解读仅供参考，具体诊疗请遵医嘱。"""

        interpret_prompt = f"""请仔细阅读这份{report_type}，并按照以下JSON格式返回解读结果：

{{
    "report_type": "报告类型",
    "report_date": "报告日期（如能识别）",
    "indicators": [
        {{
            "name": "指标名称",
            "value": "检测值",
            "reference_range": "参考范围",
            "status": "normal/high/low/abnormal",
            "explanation": "该指标的含义和临床意义"
        }}
    ],
    "summary": "报告整体解读总结",
    "abnormal_findings": ["异常发现1", "异常发现2"],
    "health_advice": ["健康建议1", "建议2"],
    "need_follow_up": true或false,
    "follow_up_suggestion": "复查建议"
}}

请确保返回有效的JSON格式。如果图像模糊或无法完整识别，请在summary中说明。"""

        result = await self.analyze_image(
            image_url=image_url,
            image_base64=image_base64,
            prompt=interpret_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2500
        )
        
        if not result["success"]:
            return result
        
        # 解析JSON结果
        try:
            content = result["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            interpretation = json.loads(content.strip())
            return {
                "success": True,
                "interpretation": interpretation,
                "raw_content": result["content"]
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "interpretation": {
                    "report_type": report_type,
                    "summary": result["content"],
                    "indicators": [],
                    "abnormal_findings": [],
                    "health_advice": ["建议携带报告咨询专业医生"],
                    "need_follow_up": True,
                    "follow_up_suggestion": "建议线下就医获取专业解读"
                },
                "raw_content": result["content"],
                "parse_error": True
            }


# 单例实例
qwen_vl_service = QwenVLService()
