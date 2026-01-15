"""
CrewAI 1.x 骨科问诊智能体
支持：骨科症状问诊、X光片解读
"""
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from crewai import Agent, Task, LLM

from ...config import get_settings

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


class OrthoConversationOutput(BaseModel):
    """骨科问诊对话输出 Schema"""
    message: str = Field(description="回复消息")
    next_action: str = Field(description="下一步动作: continue 或 complete")
    stage: str = Field(default="collecting", description="当前阶段: greeting, collecting, summary")
    quick_options: List[Dict[str, str]] = Field(default_factory=list, description="快捷选项")
    extracted_info: Dict[str, Any] = Field(default_factory=dict, description="从用户输入提取的信息")
    risk_level: str = Field(default="low", description="风险等级: low, medium, high, emergency")


class XRayInterpretationOutput(BaseModel):
    """X光片解读输出 Schema"""
    interpretation: str = Field(description="X光片解读结果")
    findings: List[str] = Field(default_factory=list, description="主要发现")
    abnormalities: List[str] = Field(default_factory=list, description="异常项")
    risk_level: str = Field(default="low", description="风险等级")
    recommendations: List[str] = Field(default_factory=list, description="建议")
    need_urgent_care: bool = Field(default=False, description="是否需要紧急就医")


ORTHO_CONVERSATION_BACKSTORY = """你是一位经验丰富的骨科问诊协调员，专注于骨骼、关节和肌肉骨骼系统疾病的初步问诊。
目标：通过多轮对话了解患者骨科相关症状，进行初步风险评估，并给出专业、温和的建议。

【最高优先级：紧急情况识别】
当识别到以下紧急症状时，必须立即提醒患者就医：
1. 明显骨折体征（畸形、异常活动、骨擦音）
2. 开放性外伤/开放性骨折
3. 脊柱损伤伴肢体麻木或无力
4. 关节脱位
5. 严重肿胀伴剧烈疼痛（骨筋膜室综合征风险）
6. 肢体苍白、发凉、脉搏减弱（血管损伤）
此时输出 risk_level: "emergency"，并在 message 中强调立即就医。

【及时总结条件】
当满足以下任一条件时，进入总结阶段（stage: "summary", next_action: "complete"）：
1. 已连续追问 ≥5 轮
2. 已掌握 ≥3 项关键信息（主诉、疼痛部位、持续时间、外伤史、活动受限等）
3. 用户明确请求分析/总结

【核心原则：症状导向追问】
首先识别患者描述中的主要症状类别，然后围绕该症状进行系统性追问：
- **关节疼痛** → 追问：具体关节（膝/髋/肩/腕/踝等）、疼痛性质（酸痛/刺痛/胀痛）、活动时是否加重、有无晨僵、有无肿胀发热
- **腰背痛** → 追问：疼痛部位（腰部/背部/骶尾部）、是否放射到腿部、久坐/弯腰是否加重、有无下肢麻木
- **骨折/外伤** → 追问：受伤机制、受伤时间、是否能活动、有无肿胀畸形、是否已处理
- **颈椎不适** → 追问：是否有上肢麻木、头晕、活动受限、与姿势的关系
- **肢体麻木** → 追问：麻木范围、持续还是间歇、有无无力感、与体位的关系

【骨科风险因素评估】
在问诊过程中关注以下因素：
1. 年龄（老年人骨折风险高、骨质疏松）
2. 外伤史（跌倒、车祸、运动损伤）
3. 既往骨科病史（骨折史、关节手术史）
4. 职业因素（久坐、重体力劳动、运动员）
5. 骨质疏松风险因素（绝经后女性、长期激素使用）
6. 类风湿/痛风等代谢性关节病史

【沟通规范】
1. 每次只提出一个最重要的问题
2. 对紧急症状保持高度警觉，及时提醒就医
3. 每次回复附带 3-5 个可点击的快捷选项
4. 不做确定性诊断，只提供初步分析和建议
5. 免责声明由前端统一展示，模型输出无需包含
"""


ORTHO_XRAY_INTERPRETER_BACKSTORY = """你是一位专业的骨科影像分析专家，能够解读X光片图像或报告。
你的任务是：
1. 识别X光片中的正常和异常表现
2. 对发现的问题进行分类（骨折、关节退变、骨质改变等）
3. 评估紧急程度
4. 给出专业但易懂的解释
5. 提供后续建议

【重点关注】
- 骨折：骨折线、移位、粉碎情况
- 关节：关节间隙、骨赘、软骨下硬化
- 脊柱：椎体高度、椎间隙、侧弯/后凸
- 骨质：骨密度变化、骨质疏松征象
- 软组织：肿胀、钙化

注意：这是辅助分析，最终诊断需由专业医生确认。
"""


def create_ortho_conversation_agent(llm: LLM = None) -> Agent:
    """创建骨科问诊对话 Agent"""
    if llm is None:
        llm = create_llm()
    return Agent(
        role="骨科问诊协调员",
        goal="通过文本问诊收集骨科相关症状信息，识别紧急情况，并给出初步评估",
        backstory=ORTHO_CONVERSATION_BACKSTORY,
        verbose=False,
        allow_delegation=False,
        llm=llm,
        max_iter=10,
        max_retry_limit=2,
    )


def create_ortho_xray_interpreter(llm: LLM = None) -> Agent:
    """创建X光片解读 Agent"""
    if llm is None:
        llm = create_llm()
    return Agent(
        role="骨科影像分析专家",
        goal="解读X光片图像或报告，识别异常，评估风险",
        backstory=ORTHO_XRAY_INTERPRETER_BACKSTORY,
        verbose=False,
        allow_delegation=False,
        llm=llm,
        max_iter=5,
        max_retry_limit=2,
    )


def create_ortho_conversation_task(
    agent: Agent,
    state: Dict[str, Any],
    user_input: str,
) -> Task:
    """创建骨科问诊对话任务"""
    state_snapshot = _format_ortho_state_snapshot(state)
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
        sum([bool(state.get(k)) for k in ["chief_complaint", "pain_location", "duration", "symptoms", "injury_history"]]) >= 3 or
        any(keyword in user_input.lower() for keyword in ["分析", "总结", "是什么问题", "怎么办", "评估"])
    )
    
    summary_instruction = ""
    if should_summarize:
        summary_instruction = f"""
⚠️ 重要：当前已满足总结条件（已追问 {questions_asked} 轮），你必须立即进入总结阶段。
请输出 stage: "summary", next_action: "complete"，并在 message 中给出症状归纳、初步分析和建议。
"""
    
    return Task(
        description=f"""根据用户文本输入继续骨科问诊。

{context}
{summary_instruction}

任务要求：
1. 首先检查是否存在紧急症状（明显骨折体征、开放性外伤、脊柱损伤伴麻木等），如有则立即提醒就医
2. 根据用户描述的核心症状（关节痛/腰背痛/外伤/麻木等）进行针对性追问
3. 关注骨科相关风险因素（年龄、外伤史、职业、骨质疏松等）
4. 根据对话进展决定下一步：continue（继续问诊）或 complete（信息充足，可总结）
5. 生成专业、有同理心的回复
6. 给出 3-5 个快捷选项
7. 评估当前风险等级：low/medium/high/emergency

【风险等级判断标准】
- emergency: 明显骨折体征、开放性外伤、脊柱损伤伴肢体症状、疑似骨筋膜室综合征
- high: 关节脱位可能、严重肿胀无法活动、持续剧烈疼痛
- medium: 活动受限、中度疼痛、慢性关节退变
- low: 轻度不适、肌肉酸痛、无明显外伤

输出 JSON：
{{
    "message": "回复消息",
    "next_action": "continue/complete",
    "stage": "collecting|summary",
    "quick_options": [{{"text": "选项文本", "value": "选项值", "category": "类别"}}],
    "extracted_info": {{"chief_complaint": "", "pain_location": "", "duration": "", "symptoms": [], "injury_history": ""}},
    "risk_level": "low/medium/high/emergency"
}}
""",
        expected_output="JSON格式的对话输出",
        agent=agent,
        output_pydantic=OrthoConversationOutput
    )


def create_xray_interpretation_task(
    agent: Agent,
    xray_description: str,
    patient_context: str = ""
) -> Task:
    """创建X光片解读任务"""
    return Task(
        description=f"""解读以下X光片信息。

X光片描述/报告内容：
{xray_description}

患者背景信息：
{patient_context if patient_context else "无额外背景信息"}

任务要求：
1. 识别X光片中的正常和异常表现
2. 对异常进行分类（骨折、关节退变、骨质改变等）
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
        expected_output="JSON格式的X光片解读结果",
        agent=agent,
        output_pydantic=XRayInterpretationOutput
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


def _format_ortho_state_snapshot(state: Dict[str, Any]) -> str:
    """汇总骨科问诊结构化信息"""
    if not state:
        return "暂无结构化信息"

    snapshot = []
    
    # 基本症状信息
    chief = state.get("chief_complaint")
    location = state.get("pain_location")
    duration = state.get("duration")
    symptoms = state.get("symptoms") or []
    symptom_details = state.get("symptom_details") or {}
    injury = state.get("injury_history")
    
    if chief:
        snapshot.append(f"- 主诉: {chief}")
    if location:
        snapshot.append(f"- 疼痛部位: {location}")
    if duration:
        snapshot.append(f"- 持续时间: {duration}")
    if symptoms:
        snapshot.append(f"- 症状: {', '.join(symptoms[:5])}")
    if symptom_details:
        for k, v in list(symptom_details.items())[:3]:
            snapshot.append(f"- {k}: {v}")
    if injury:
        snapshot.append(f"- 外伤史: {injury}")
    
    # 既往史
    medical_history = state.get("medical_history") or []
    if medical_history:
        snapshot.append(f"- 既往史: {', '.join(medical_history)}")
    
    # 活动受限
    mobility = state.get("mobility_limitation")
    if mobility:
        snapshot.append(f"- 活动受限: {mobility}")
    
    # 进度统计
    filled_fields = [
        bool(chief), bool(location), bool(duration),
        bool(symptoms), bool(injury), bool(medical_history)
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
