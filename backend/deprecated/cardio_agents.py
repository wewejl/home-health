"""
CrewAI 1.x 心血管内科问诊智能体
支持：心血管症状问诊、心电图解读、风险评估
"""
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from crewai import Agent, Task, LLM

from ..config import get_settings

settings = get_settings()


def create_llm() -> LLM:
    """创建 LLM 实例 - 使用 DashScope OpenAI 兼容接口"""
    return LLM(
        model=f"openai/{settings.LLM_MODEL}",
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.6,
        max_tokens=2000,
        timeout=90,
        max_retries=2,
    )


class CardioConversationOutput(BaseModel):
    """心血管问诊对话输出 Schema"""
    message: str = Field(description="回复消息")
    next_action: str = Field(description="下一步动作: continue 或 complete")
    stage: str = Field(default="collecting", description="当前阶段: greeting, collecting, risk_assessment, summary")
    quick_options: List[Dict[str, str]] = Field(default_factory=list, description="快捷选项")
    extracted_info: Dict[str, Any] = Field(default_factory=dict, description="从用户输入提取的信息")
    risk_level: str = Field(default="low", description="风险等级: low, medium, high, emergency")


class ECGInterpretationOutput(BaseModel):
    """心电图解读输出 Schema"""
    interpretation: str = Field(description="心电图解读结果")
    findings: List[str] = Field(default_factory=list, description="主要发现")
    abnormalities: List[str] = Field(default_factory=list, description="异常项")
    risk_level: str = Field(default="low", description="风险等级")
    recommendations: List[str] = Field(default_factory=list, description="建议")
    need_urgent_care: bool = Field(default=False, description="是否需要紧急就医")


class RiskAssessmentOutput(BaseModel):
    """心血管风险评估输出 Schema"""
    overall_risk: str = Field(description="综合风险等级: low, medium, high, very_high")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")
    protective_factors: List[str] = Field(default_factory=list, description="保护因素")
    score: int = Field(default=0, description="风险评分 0-100")
    recommendations: List[str] = Field(default_factory=list, description="建议措施")
    follow_up: str = Field(default="", description="随访建议")


CARDIO_CONVERSATION_BACKSTORY = """你是一位经验丰富的心血管内科问诊协调员，专注于心脏和血管系统疾病的初步问诊。
目标：通过多轮对话了解患者心血管相关症状，进行初步风险评估，并给出专业、温和的建议。

【最高优先级：紧急情况识别】
当识别到以下紧急症状时，必须立即提醒患者就医：
1. 持续性胸痛、胸闷，尤其是伴随冷汗、恶心
2. 突发性呼吸困难
3. 晕厥或濒临晕厥
4. 严重心悸伴随头晕
5. 肢体突然无力或麻木（可能为卒中）
此时输出 risk_level: "emergency"，并在 message 中强调立即拨打急救电话。

【及时总结条件】
当满足以下任一条件时，进入总结阶段（stage: "summary", next_action: "complete"）：
1. 已连续追问 ≥5 轮
2. 已掌握 ≥3 项关键信息（主诉、症状特征、持续时间、诱因、既往史等）
3. 用户明确请求分析/总结

【核心原则：症状导向追问】
首先识别患者描述中的主要症状类别，然后围绕该症状进行系统性追问：
- **胸痛/胸闷** → 追问：部位（前胸/后背/左侧）、性质（压榨/刺痛/闷胀）、持续时间、诱因（活动/情绪/进食）、缓解因素、是否放射到其他部位
- **心悸** → 追问：发作频率、持续时间、是否规则、伴随症状（头晕/乏力/胸闷）、诱因
- **呼吸困难** → 追问：发作时机（活动时/平卧时/夜间）、程度、伴随症状
- **水肿** → 追问：部位、时间规律（晨起/傍晚）、程度
- **头晕/乏力** → 追问：发作频率、与体位变化的关系、是否有黑朦

【心血管风险因素评估】
在问诊过程中关注以下风险因素：
1. 年龄和性别（男性>45岁，女性>55岁风险增加）
2. 高血压、糖尿病、高血脂病史
3. 吸烟史、饮酒史
4. 家族心血管病史（一级亲属早发冠心病）
5. 肥胖、缺乏运动
6. 既往心脏病史

【沟通规范】
1. 每次只提出一个最重要的问题
2. 对紧急症状保持高度警觉，及时提醒就医
3. 每次回复附带 3-5 个可点击的快捷选项
4. 不做确定性诊断，只提供初步分析和建议
5. 免责声明由前端统一展示，模型输出无需包含
"""


CARDIO_ECG_INTERPRETER_BACKSTORY = """你是一位专业的心电图分析专家，能够解读心电图图像或报告。
你的任务是：
1. 识别心电图中的正常和异常表现
2. 对发现的问题进行分类（心律失常、缺血、传导异常等）
3. 评估紧急程度
4. 给出专业但易懂的解释
5. 提供后续建议

注意：这是辅助分析，最终诊断需由专业医生确认。
"""


CARDIO_RISK_ASSESSOR_BACKSTORY = """你是一位心血管风险评估专家，基于收集的信息进行综合风险评估。
评估维度包括：
1. Framingham 风险评分参考
2. 中国心血管病风险评估模型参考
3. 生活方式因素
4. 既往病史
5. 家族史

输出需包含：综合风险等级、主要风险因素、保护因素、具体建议。
"""


def create_cardio_conversation_agent(llm: LLM = None) -> Agent:
    """创建心血管问诊对话 Agent"""
    if llm is None:
        llm = create_llm()
    return Agent(
        role="心血管内科问诊协调员",
        goal="通过文本问诊收集心血管相关症状信息，识别紧急情况，并给出初步评估",
        backstory=CARDIO_CONVERSATION_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=10,
        max_retry_limit=2,
    )


def create_cardio_ecg_interpreter(llm: LLM = None) -> Agent:
    """创建心电图解读 Agent"""
    if llm is None:
        llm = create_llm()
    return Agent(
        role="心电图分析专家",
        goal="解读心电图图像或报告，识别异常，评估风险",
        backstory=CARDIO_ECG_INTERPRETER_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=5,
        max_retry_limit=2,
    )


def create_cardio_risk_assessor(llm: LLM = None) -> Agent:
    """创建心血管风险评估 Agent"""
    if llm is None:
        llm = create_llm()
    return Agent(
        role="心血管风险评估专家",
        goal="基于收集的信息进行心血管风险综合评估",
        backstory=CARDIO_RISK_ASSESSOR_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=5,
        max_retry_limit=2,
    )


def create_cardio_conversation_task(
    agent: Agent,
    state: Dict[str, Any],
    user_input: str,
) -> Task:
    """创建心血管问诊对话任务"""
    state_snapshot = _format_cardio_state_snapshot(state)
    questions_asked = state.get("questions_asked", 0)
    context = f"""
最近对话：
{_format_recent_messages(state.get('messages', []))}

结构化关键信息：
{state_snapshot}

用户最新输入：{user_input}
"""

    should_summarize = (
        questions_asked >= 5 or
        sum([bool(state.get(k)) for k in ["chief_complaint", "symptom_location", "duration", "symptoms", "risk_factors"]]) >= 3 or
        any(keyword in user_input.lower() for keyword in ["分析", "总结", "是什么问题", "怎么办", "评估"])
    )
    
    summary_instruction = ""
    if should_summarize:
        summary_instruction = f"""
⚠️ 重要：当前已满足总结条件（已追问 {questions_asked} 轮），你必须立即进入总结阶段。
请输出 stage: "summary", next_action: "complete"，并在 message 中给出症状归纳、风险评估和建议。
"""
    
    return Task(
        description=f"""根据用户文本输入继续心血管内科问诊。

{context}
{summary_instruction}

任务要求：
1. 首先检查是否存在紧急症状（持续胸痛、呼吸困难、晕厥等），如有则立即提醒就医
2. 根据用户描述的核心症状（胸痛/心悸/呼吸困难/水肿等）进行针对性追问
3. 关注心血管风险因素（高血压、糖尿病、吸烟、家族史等）
4. 根据对话进展决定下一步：continue（继续问诊）或 complete（信息充足，可总结）
5. 生成专业、有同理心的回复
6. 给出 3-5 个快捷选项
7. 评估当前风险等级：low/medium/high/emergency

【风险等级判断标准】
- emergency: 持续胸痛>15分钟、突发呼吸困难、晕厥、疑似急性心梗/卒中
- high: 活动时胸闷、新发心悸、夜间阵发性呼吸困难
- medium: 偶发心悸、轻度胸闷、多个风险因素
- low: 偶发不适、无明显风险因素

输出 JSON：
{{
    "message": "回复消息",
    "next_action": "continue/complete",
    "stage": "collecting|risk_assessment|summary",
    "quick_options": [{{"text": "选项文本", "value": "选项值", "category": "类别"}}],
    "extracted_info": {{"chief_complaint": "", "symptom_location": "", "duration": "", "symptoms": [], "risk_factors": []}},
    "risk_level": "low/medium/high/emergency"
}}
""",
        expected_output="JSON格式的对话输出",
        agent=agent,
        output_pydantic=CardioConversationOutput
    )


def create_ecg_interpretation_task(
    agent: Agent,
    ecg_description: str,
    patient_context: str = ""
) -> Task:
    """创建心电图解读任务"""
    return Task(
        description=f"""解读以下心电图信息。

心电图描述/报告内容：
{ecg_description}

患者背景信息：
{patient_context if patient_context else "无额外背景信息"}

任务要求：
1. 识别心电图中的正常和异常表现
2. 对异常进行分类（心律失常、ST-T改变、传导异常等）
3. 评估紧急程度
4. 用通俗易懂的语言解释发现
5. 给出后续建议

输出 JSON：
{{
    "interpretation": "整体解读结果",
    "findings": ["发现1", "发现2"],
    "abnormalities": ["异常1", "异常2"],
    "risk_level": "low/medium/high/emergency",
    "recommendations": ["建议1", "建议2"],
    "need_urgent_care": true/false
}}
""",
        expected_output="JSON格式的心电图解读结果",
        agent=agent,
        output_pydantic=ECGInterpretationOutput
    )


def create_risk_assessment_task(
    agent: Agent,
    state: Dict[str, Any]
) -> Task:
    """创建心血管风险评估任务"""
    state_info = _format_cardio_state_snapshot(state)
    
    return Task(
        description=f"""基于以下信息进行心血管风险综合评估。

收集的信息：
{state_info}

对话历史摘要：
{_format_recent_messages(state.get('messages', []), limit=15)}

任务要求：
1. 综合评估心血管风险等级（low/medium/high/very_high）
2. 列出主要风险因素
3. 列出保护因素（如有）
4. 给出风险评分（0-100）
5. 提供具体的生活方式和医疗建议
6. 给出随访建议

输出 JSON：
{{
    "overall_risk": "low/medium/high/very_high",
    "risk_factors": ["风险因素1", "风险因素2"],
    "protective_factors": ["保护因素1"],
    "score": 35,
    "recommendations": ["建议1", "建议2"],
    "follow_up": "随访建议"
}}
""",
        expected_output="JSON格式的风险评估结果",
        agent=agent,
        output_pydantic=RiskAssessmentOutput
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _format_recent_messages(messages: List[Dict], limit: int = 10) -> str:
    """格式化最近的对话消息"""
    recent = messages[-limit:] if len(messages) > limit else messages
    formatted = []
    for msg in recent:
        role = "患者" if msg.get("role") == "user" else "医生"
        formatted.append(f"{role}: {msg.get('content', '')}")
    return "\n".join(formatted) if formatted else "无历史对话"


def _format_cardio_state_snapshot(state: Dict[str, Any]) -> str:
    """汇总心血管问诊结构化信息"""
    if not state:
        return "暂无结构化信息"

    snapshot = []
    
    # 基本症状信息
    chief = state.get("chief_complaint")
    location = state.get("symptom_location")
    duration = state.get("duration")
    symptoms = state.get("symptoms") or []
    symptom_details = state.get("symptom_details") or {}
    
    if chief:
        snapshot.append(f"- 主诉: {chief}")
    if location:
        snapshot.append(f"- 症状部位: {location}")
    if duration:
        snapshot.append(f"- 持续时间: {duration}")
    if symptoms:
        snapshot.append(f"- 症状: {', '.join(symptoms[:5])}")
    if symptom_details:
        for k, v in list(symptom_details.items())[:3]:
            snapshot.append(f"- {k}: {v}")
    
    # 风险因素
    risk_factors = state.get("risk_factors") or []
    if risk_factors:
        snapshot.append(f"- 风险因素: {', '.join(risk_factors)}")
    
    # 既往史
    medical_history = state.get("medical_history") or []
    if medical_history:
        snapshot.append(f"- 既往史: {', '.join(medical_history)}")
    
    # 家族史
    family_history = state.get("family_history")
    if family_history:
        snapshot.append(f"- 家族史: {family_history}")
    
    # 生活方式
    lifestyle = state.get("lifestyle") or {}
    if lifestyle:
        for k, v in lifestyle.items():
            snapshot.append(f"- {k}: {v}")
    
    # 进度统计
    filled_fields = [
        bool(chief), bool(location), bool(duration),
        bool(symptoms), bool(risk_factors), bool(medical_history)
    ]
    completeness = sum(1 for filled in filled_fields if filled)
    snapshot.append(f"- 关键信息收集进度: {completeness}/{len(filled_fields)}")
    snapshot.append(f"- 已追问轮次: {state.get('questions_asked', 0)}")
    snapshot.append(f"- 当前风险等级: {state.get('risk_level', 'low')}")

    return "\n".join(snapshot) if snapshot else "暂无结构化信息"


def parse_json_output(output: str) -> Dict[str, Any]:
    """解析 Agent 输出的 JSON"""
    try:
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0]
        elif "```" in output:
            output = output.split("```")[1].split("```")[0]
        return json.loads(output.strip())
    except (json.JSONDecodeError, IndexError):
        return {}
