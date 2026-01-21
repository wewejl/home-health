"""
医生分身对话式采集服务

通过对话方式采集医生的个人特征，生成 ai_persona_prompt
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio


class CollectionStage(str, Enum):
    """采集阶段"""
    GREETING = "greeting"           # 问候与说明
    SPECIALTY = "specialty"         # 专科特点
    STYLE = "style"                # 沟通风格
    APPROACH = "approach"          # 问诊思路
    PRESCRIPTION = "prescription"   # 处方习惯
    ADVICE = "advice"              # 生活建议
    SUMMARY = "summary"            # 总结与确认


@dataclass
class CollectionState:
    """采集状态"""
    stage: CollectionStage = CollectionStage.GREETING
    completed_stages: List[str] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)

    # 各阶段数据
    specialty_focus: str = ""           # 专科关注点
    communication_style: str = ""       # 沟通风格 (温和/直接/专业/通俗)
    inquiry_approach: str = ""          # 问诊顺序 (主诉→现病史→既往史)
    diagnostic_focus: str = ""          # 诊断思路特点
    prescription_preferences: str = ""  # 处方习惯 (保守/积极/中西医结合)
    advice_template: str = ""           # 生活建议模板

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "completed_stages": self.completed_stages,
            "collected_data": self.collected_data,
            "specialty_focus": self.specialty_focus,
            "communication_style": self.communication_style,
            "inquiry_approach": self.inquiry_approach,
            "diagnostic_focus": self.diagnostic_focus,
            "prescription_preferences": self.prescription_preferences,
            "advice_template": self.advice_template
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollectionState":
        state = cls()
        if "stage" in data:
            state.stage = CollectionStage(data["stage"])
        state.completed_stages = data.get("completed_stages", [])
        state.collected_data = data.get("collected_data", {})
        state.specialty_focus = data.get("specialty_focus", "")
        state.communication_style = data.get("communication_style", "")
        state.inquiry_approach = data.get("inquiry_approach", "")
        state.diagnostic_focus = data.get("diagnostic_focus", "")
        state.prescription_preferences = data.get("prescription_preferences", "")
        state.advice_template = data.get("advice_template", "")
        return state


class PersonaCollectionService:
    """对话式采集服务"""

    # 各阶段的问题模板
    STAGE_QUESTIONS = {
        CollectionStage.GREETING: """
您好！我是医生分身配置助手。接下来我将通过几个简单的问题，
帮助您打造一个模拟您诊疗风格的 AI 医生分身。

整个流程大约需要 3-5 分钟，您可以随时修改已回答的内容。

准备好了吗？让我们开始吧。
""",

        CollectionStage.SPECIALTY: """
【专科特点】
首先，请您描述一下您专科问诊时最关注的方面：

1. 您通常首先询问患者哪些症状？
2. 您会特别留意哪些危险信号？
3. 您对这个领域的患者有什么特别的叮嘱？

例如：「儿科我会先问孩子精神状态、食欲变化，特别关注发烧时长和伴随症状」
""",

        CollectionStage.STYLE: """
【沟通风格】
请描述您与患者的沟通方式：

1. 您会用专业术语还是通俗解释？
2. 您的回答风格是简洁还是详细？
3. 您会给患者多少选择权？

例如：「我喜欢用通俗易懂的比喻解释病情，让患者充分了解后一起决定治疗方案」
""",

        CollectionStage.APPROACH: """
【问诊思路】
请分享您的问诊顺序：

1. 您通常按什么顺序问诊？（主诉 → 现病史 → 既往史 → 个人史...）
2. 您会优先排除哪些严重情况？
3. 您对确诊有什么特别的考量？

例如：「我习惯先听患者完整叙述，然后针对性追问，优先排除急重症」
""",

        CollectionStage.PRESCRIPTION: """
【处方习惯】
关于处方和治疗方案：

1. 您倾向于保守治疗还是积极干预？
2. 您更偏好西药、中药还是中西医结合？
3. 您在用药安全方面有什么特别注意？

例如：「我一般首选单一用药，避免重复，对老人和儿童会特别减量」
""",

        CollectionStage.ADVICE: """
【生活建议】
最后，请分享您常给患者的生活建议模板：

1. 您会关注哪些生活细节？（饮食/作息/运动/情绪）
2. 您有什么常用的建议口诀或顺口溜？
3. 您对患者自我管理有什么期望？

例如：「我常建议三分治七分养，强调规律作息和适度运动」
""",

        CollectionStage.SUMMARY: """
【总结确认】
感谢您的配合！以下是整理好的您的医生分身配置：

{summary}

请问：
- 输入「确认」保存配置
- 输入「修改 [阶段名称]」调整某项内容
- 输入「重新开始」清空重做
"""
    }

    @staticmethod
    async def start_collection(doctor_name: str, specialty: str) -> str:
        """开始采集流程"""
        greeting = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.GREETING].strip()
        return greeting

    @staticmethod
    async def process_input(
        user_input: str,
        state: CollectionState,
        doctor_name: str = "",
        specialty: str = ""
    ) -> Dict[str, Any]:
        """处理用户输入，返回响应和状态更新"""

        response = ""
        next_stage = state.stage
        is_complete = False
        generated_prompt = ""

        # GREETING 阶段：任何输入进入下一阶段
        if state.stage == CollectionStage.GREETING:
            next_stage = CollectionStage.SPECIALTY
            response = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.SPECIALTY].strip()

        # 采集各阶段信息
        elif state.stage == CollectionStage.SPECIALTY:
            state.specialty_focus = user_input
            state.completed_stages.append(CollectionStage.SPECIALTY.value)
            next_stage = CollectionStage.STYLE
            response = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.STYLE].strip()

        elif state.stage == CollectionStage.STYLE:
            state.communication_style = user_input
            state.completed_stages.append(CollectionStage.STYLE.value)
            next_stage = CollectionStage.APPROACH
            response = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.APPROACH].strip()

        elif state.stage == CollectionStage.APPROACH:
            state.inquiry_approach = user_input
            state.completed_stages.append(CollectionStage.APPROACH.value)
            next_stage = CollectionStage.PRESCRIPTION
            response = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.PRESCRIPTION].strip()

        elif state.stage == CollectionStage.PRESCRIPTION:
            state.prescription_preferences = user_input
            state.completed_stages.append(CollectionStage.PRESCRIPTION.value)
            next_stage = CollectionStage.ADVICE
            response = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.ADVICE].strip()

        elif state.stage == CollectionStage.ADVICE:
            state.advice_template = user_input
            state.completed_stages.append(CollectionStage.ADVICE.value)
            next_stage = CollectionStage.SUMMARY

            # 生成总结
            summary = PersonaCollectionService._generate_summary(state)
            response = PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.SUMMARY].format(summary=summary).strip()

        elif state.stage == CollectionStage.SUMMARY:
            # 处理确认/修改指令
            if "确认" in user_input or "完成" in user_input:
                is_complete = True
                generated_prompt = PersonaCollectionService._generate_persona_prompt(state, doctor_name, specialty)
                response = f"✅ 配置已完成！\n\n生成的医生分身提示词已保存。\n\n{generated_prompt}"
            elif "重新开始" in user_input:
                state = CollectionState()
                next_stage = CollectionStage.GREETING
                response = "好的，让我们重新开始。\n\n" + PersonaCollectionService.STAGE_QUESTIONS[CollectionStage.GREETING].strip()
            elif "修改" in user_input:
                # 解析要修改的阶段
                stage_map = {
                    "专科": CollectionStage.SPECIALTY,
                    "风格": CollectionStage.STYLE,
                    "问诊": CollectionStage.APPROACH,
                    "处方": CollectionStage.PRESCRIPTION,
                    "建议": CollectionStage.ADVICE
                }
                for key, stage in stage_map.items():
                    if key in user_input:
                        next_stage = stage
                        if stage in state.completed_stages:
                            state.completed_stages.remove(stage.value)
                        response = f"正在修改【{key}】部分\n\n" + PersonaCollectionService.STAGE_QUESTIONS[stage].strip()
                        break
                else:
                    response = "请明确要修改哪个部分：专科/风格/问诊/处方/建议"
            else:
                response = "请输入「确认」、「修改 [阶段名称]」或「重新开始」"

        # 更新状态
        state.stage = next_stage
        state.collected_data = {
            "specialty_focus": state.specialty_focus,
            "communication_style": state.communication_style,
            "inquiry_approach": state.inquiry_approach,
            "diagnostic_focus": state.diagnostic_focus,
            "prescription_preferences": state.prescription_preferences,
            "advice_template": state.advice_template
        }

        return {
            "response": response,
            "state": state.to_dict(),
            "is_complete": is_complete,
            "generated_prompt": generated_prompt,
            "stage": next_stage.value
        }

    @staticmethod
    def _generate_summary(state: CollectionState) -> str:
        """生成配置总结"""
        lines = [
            "📋 您的医生分身配置",
            "",
            f"🏥 专科特点：{state.specialty_focus or '未填写'}",
            f"💬 沟通风格：{state.communication_style or '未填写'}",
            f"🔍 问诊思路：{state.inquiry_approach or '未填写'}",
            f"💊 处方习惯：{state.prescription_preferences or '未填写'}",
            f"🌿 生活建议：{state.advice_template or '未填写'}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _generate_persona_prompt(state: CollectionState, doctor_name: str, specialty: str) -> str:
        """生成最终的 ai_persona_prompt"""

        prompt_parts = [
            f"# {doctor_name} 医生分身提示词",
            "",
            "## 身份设定",
            f"你是 {doctor_name}，{specialty} 专家。",
            "",
            "## 诊疗风格",
        ]

        if state.communication_style:
            prompt_parts.extend([
                f"- 沟通风格：{state.communication_style}",
            ])

        if state.inquiry_approach:
            prompt_parts.extend([
                "",
                "## 问诊流程",
                f"{state.inquiry_approach}",
            ])

        if state.specialty_focus:
            prompt_parts.extend([
                "",
                "## 专科特点",
                f"{state.specialty_focus}",
            ])

        if state.prescription_preferences:
            prompt_parts.extend([
                "",
                "## 处方习惯",
                f"{state.prescription_preferences}",
            ])

        if state.advice_template:
            prompt_parts.extend([
                "",
                "## 生活建议",
                f"{state.advice_template}",
            ])

        prompt_parts.extend([
            "",
            "## 回复原则",
            "- 专业且易懂，避免过多术语",
            "- 适当安抚患者情绪",
            "- 必要时建议线下就医",
            "- 不开具具体处方，仅提供建议",
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    async def stream_conversation(
        user_input: str,
        state_json: str,
        doctor_name: str,
        specialty: str
    ) -> AsyncGenerator[str, None]:
        """流式对话接口（SSE）"""

        # 解析状态
        try:
            state_dict = json.loads(state_json) if state_json else {}
            state = CollectionState.from_dict(state_dict)
        except json.JSONDecodeError:
            # state JSON 格式错误，重置为初始状态
            state = CollectionState()

        # 处理输入
        result = await PersonaCollectionService.process_input(
            user_input, state, doctor_name, specialty
        )

        # 发送响应
        response = result["response"]

        # 模拟流式输出
        words = list(response)
        for i, word in enumerate(words):
            if word == "\n":
                yield f"data: {json.dumps({'type': 'text', 'content': '\n'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'text', 'content': word})}\n\n"
            await asyncio.sleep(0.01)

        # 发送状态更新
        yield f"data: {json.dumps({'type': 'state', 'state': result['state'], 'stage': result['stage']})}\n\n"

        # 发送完成标记
        if result["is_complete"]:
            yield f"data: {json.dumps({'type': 'complete', 'prompt': result['generated_prompt']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
