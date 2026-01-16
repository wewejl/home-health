"""
皮肤科智能体 V2 - 基于新架构

设计原则：返回统一 AgentResponse 格式
"""
from ..base.base_agent_v2 import BaseAgentV2
from ...schemas.agent_response import AgentResponse
from typing import Dict, Any, List, Optional, Callable, Awaitable


class DermatologyAgentV2(BaseAgentV2):
    """皮肤科智能体 V2"""
    
    def __init__(self):
        pass
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> AgentResponse:
        """执行皮肤科问诊流程"""
        
        # 根据 action 分发
        if action == "analyze_skin":
            return await self._analyze_skin_image(state, attachments, on_chunk)
        else:
            return await self._conversation(state, user_input, on_chunk)
    
    async def _conversation(
        self,
        state: Dict[str, Any],
        user_input: str,
        on_chunk: Optional[Callable] = None
    ) -> AgentResponse:
        """对话问诊流程"""
        
        # 1. 从 state 恢复上下文
        stage = state.get("stage", "greeting")
        symptoms = state.get("symptoms", [])
        
        # 2. 提取症状（简化版 - 关键词匹配）
        if user_input:
            new_symptoms = self._extract_symptoms_simple(user_input)
            # 去重添加
            for s in new_symptoms:
                if s not in symptoms:
                    symptoms.append(s)
        
        # 3. 判断阶段
        if stage == "greeting" and not symptoms:
            new_stage = "greeting"
            progress = 0
        elif len(symptoms) < 3:
            new_stage = "collecting"
            progress = len(symptoms) * 20
        else:
            new_stage = "diagnosing"
            progress = 80
        
        # 4. 生成回复（模板方式）
        message = self._generate_response_template(new_stage, symptoms, user_input)
        
        # 5. 流式输出
        if on_chunk:
            await on_chunk(message)
        
        # 6. 构建专科数据
        specialty_data = None
        if new_stage == "diagnosing" and len(symptoms) >= 3:
            specialty_data = {
                "diagnosis_card": {
                    "summary": f"收集到 {len(symptoms)} 个症状",
                    "conditions": [
                        {"name": "待诊断", "confidence": 0.5}
                    ]
                },
                "symptoms": symptoms
            }
        
        return AgentResponse(
            message=message,
            stage=new_stage,
            progress=progress,
            quick_options=self._get_quick_options(new_stage),
            risk_level="low",
            specialty_data=specialty_data,
            next_state={
                "stage": new_stage,
                "symptoms": symptoms,
                "questions_asked": state.get("questions_asked", 0) + 1
            }
        )
    
    def _extract_symptoms_simple(self, text: str) -> List[str]:
        """简化的症状提取（关键词匹配）"""
        symptom_keywords = {
            "痒": "瘙痒",
            "红": "红疹",
            "肿": "肿胀",
            "痛": "疼痛",
            "脱皮": "脱皮",
            "水泡": "水泡",
            "干燥": "皮肤干燥",
            "起皮": "脱皮",
            "发红": "红疹",
            "刺痛": "刺痛",
            "灼热": "灼热感",
        }
        
        found_symptoms = []
        for keyword, symptom in symptom_keywords.items():
            if keyword in text and symptom not in found_symptoms:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def _generate_response_template(self, stage: str, symptoms: List[str], user_input: str = None) -> str:
        """生成回复（模板方式）"""
        if stage == "greeting":
            return "您好，我是皮肤科AI医生。请描述您的皮肤问题，例如：哪个部位？有什么症状？持续多久了？"
        elif stage == "collecting":
            if symptoms:
                return f"我了解到您有 {', '.join(symptoms)} 的症状。请继续描述其他症状，或者上传患处照片帮助我更准确地判断。"
            else:
                return "请描述您的皮肤症状，例如：是否有红疹、瘙痒、脱皮等情况？"
        else:
            return f"根据您描述的 {', '.join(symptoms)} 等症状，我将为您进行初步分析。您可以继续补充信息或上传照片。"
    
    def _get_quick_options(self, stage: str) -> List[str]:
        """获取快捷选项"""
        if stage == "diagnosing":
            return ["继续描述", "上传照片", "生成病历"]
        else:
            return ["继续描述", "上传照片"]
    
    async def _analyze_skin_image(
        self,
        state: Dict[str, Any],
        attachments: List[Dict[str, Any]],
        on_chunk: Optional[Callable] = None
    ) -> AgentResponse:
        """皮肤图像分析（占位实现）"""
        message = "图像分析功能开发中，请先通过文字描述您的症状。"
        
        if on_chunk:
            await on_chunk(message)
        
        return AgentResponse(
            message=message,
            stage="analyzing",
            progress=50,
            quick_options=["继续描述"],
            next_state=state
        )
