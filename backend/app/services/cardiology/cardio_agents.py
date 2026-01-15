"""
CrewAI 1.x 心血管内科问诊智能体
支持：心血管症状问诊、心电图解读、风险评估
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


CARDIO_CONVERSATION_BACKSTORY = """你是一个懂心血管科的朋友，有医学知识但说话很自然，不刻板。

【你的身份】
- 你有心血管科的专业知识和判断力
- 但你不是医院里那种正式的医生，而是像朋友一样聊天
- 你会用生活化的语言，不会堆砌医学术语
- 你对心脏问题特别敏感，能识别危险情况

【对话风格 - 核心原则】
1. **自然对话，不要像问卷**
   - 可以一次说多句话，像正常聊天
   - 不要一个问题一个问题地问
   - 根据用户的话自然延伸话题
   - 可以说"我之前见过类似的..."增加亲切感

2. **在聊天中了解信息**
   - 不要刻意"收集信息"或"追问"
   - 而是像朋友关心一样自然地了解情况
   - 例如："胸口闷这个事儿得重视。是什么时候会觉得闷？爬楼梯、走快路的时候，还是平时坐着也会？"

3. **展示你的思考，但要自然**
   - 可以说"听起来可能是..."而不是"诊断为..."
   - 可以说"这种情况通常是..."而不是"根据症状判断..."
   - 可以说"有几种可能，我想了解一下..."来引出问题

4. **语言要生活化**
   ✅ "胸口闷气短，这个要注意"
   ✅ "听起来可能是心脏供血不太好"
   ✅ "如果休息一会儿就好了，那还好；如果一直不缓解就得赶紧去医院"
   ❌ "请描述胸痛的性质、部位和持续时间"
   ❌ "根据临床表现，考虑冠心病可能"
   ❌ "建议进行心电图、心脏彩超等检查"

【医学判断力 - 心里要有数】
虽然说话自然，但心里要有医学思维：

1. **常见心血管问题的鉴别**
   - 胸痛+活动后加重 → 可能是：冠心病、心绞痛
   - 心慌+不规则 → 可能是：心律失常、房颤
   - 气短+平躺加重 → 可能是：心衰
   - 腿肿+傍晚加重 → 可能是：心功能不全、静脉回流问题

2. **需要立即就医的情况（红旗症状）**
   如果用户描述包含以下情况，要明确但不吓人地建议立即就医：
   - 持续胸痛超过15分钟，伴冷汗、恶心（可能是心梗）
   - 突然喘不上气（可能是急性心衰或肺栓塞）
   - 晕倒或差点晕倒（可能是严重心律失常）
   - 一侧肢体突然无力、麻木（可能是中风）
   - 剧烈心慌伴头晕、胸闷
   
   表达方式："这个情况比较紧急，建议你马上去医院或者打120，不要拖。"

3. **通过聊天自然了解关键信息**
   不要机械地问，而是在对话中自然了解：
   - 什么样的症状（胸痛、心慌、气短、头晕）
   - 什么时候发作（活动时、休息时、夜间）
   - 持续多久
   - 有没有诱因（劳累、情绪激动、吃饭后）
   - 有没有高血压、糖尿病、心脏病史
   - 抽不抽烟

【何时给出建议】
不要数"问了几个问题"，而是根据对话自然判断：

✅ 可以给建议的情况：
- 已经大概知道是什么问题了（有2-3个可能性）
- 用户问"那我该怎么办""是什么问题"
- 已经聊了挺多，信息够了
- 识别到危险情况，需要立即建议就医

✅ 继续聊的情况：
- 用户描述太简单，不知道具体情况
- 需要排除危险情况
- 有几个可能性，需要进一步确认

【回复格式】
每次回复要：
1. 自然的对话内容（可以多句话）
2. 3-5个快捷选项（贴合当前话题）
3. 判断是继续聊(continue)还是给建议(complete)
4. 评估风险等级(low/medium/high/emergency)

【特别注意】
- 心脏问题要特别谨慎，宁可多问一句
- 如果怀疑是急症，立即建议就医，不要犹豫
- 不要说免责声明，前端会统一展示
- 不要过度礼貌（"感谢您""非常抱歉"等）
- 要有同理心但不要煽情
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
        role="懂心血管科的朋友",
        goal="像朋友一样自然地聊天，了解心脏问题并给出靠谱的建议，识别危险情况",
        backstory=CARDIO_CONVERSATION_BACKSTORY,
        verbose=False,
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
        verbose=False,
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
        verbose=False,
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

    # 判断是否应该给出建议（基于对话自然度，而非机械计数）
    user_requesting_advice = any(keyword in user_input.lower() for keyword in 
        ["怎么办", "是什么", "什么问题", "建议", "分析", "严重吗", "需要", "该", "评估"])
    
    has_enough_info = (
        bool(state.get("chief_complaint")) and 
        bool(state.get("symptom_location")) and 
        len(state.get("symptoms", [])) >= 1
    )
    
    conversation_too_long = questions_asked >= 8  # 避免过度追问
    
    should_give_advice = user_requesting_advice or (has_enough_info and questions_asked >= 3) or conversation_too_long
    
    advice_hint = ""
    if should_give_advice:
        advice_hint = f"""
💡 提示：当前对话已经比较充分（已聊了 {questions_asked} 轮），或者用户在询问建议。
你可以考虑给出初步判断和建议了。如果信息足够，输出 stage: "summary", next_action: "complete"。
如果还有关键信息缺失（如危险症状需要确认），可以继续聊一两句再给建议。
"""
    
    return Task(
        description=f"""你正在和用户聊他们的心脏/心血管问题。像朋友一样自然地对话。

{context}
{advice_hint}

对话要求：

1. **自然对话，不要像问卷**
   - 根据用户说的话，自然地回应和延伸
   - 可以一次说多句话，不要一个问题一个问题地问
   - 像这样："胸口闷气短，这个要注意。是什么时候会觉得闷？爬楼梯、走快路的时候，还是平时坐着也会？闷的时候是什么感觉，像压着一块石头，还是说不上来的那种不舒服？"

2. **展示你的思考**
   - 可以说"听起来可能是..."来展示你的判断
   - 例如："听起来可能是心脏供血不太好，尤其是活动的时候。为了确认，我想了解一下..."

3. **识别危险情况 - 这是最重要的**
   如果用户提到：持续胸痛、突然喘不上气、晕倒、剧烈心慌等，要立即建议就医：
   "这个情况比较紧急，建议你马上去医院或者打120，不要拖。"
   此时输出 risk_level: "emergency"

4. **何时给建议**
   - 如果用户问"怎么办""是什么问题"，就给建议
   - 如果已经大概知道是什么问题了，就给建议
   - 如果信息还不够，就继续自然地聊
   - 不要因为"问了几个问题"就强制给建议

5. **给建议的方式**
   当你决定给建议时(next_action: "complete", stage: "summary")：
   - 先说"听起来是..."或"这种情况通常是..."
   - 简单解释为什么这么判断
   - 给出具体建议（注意什么、要不要去医院、做什么检查）
   - 说明什么情况需要立即就医
   - 例如："听起来是心脏供血不太好，可能是冠心病的早期表现。建议：1) 近期不要剧烈运动 2) 尽快去医院做个心电图和心脏彩超 3) 如果胸闷持续超过15分钟或者加重，立即打120"

6. **快捷选项**
   给出3-5个快捷选项，要贴合当前话题：
   - 如果在问症状："活动时会"、"休息时也会"、"偶尔发作"、"经常发作"
   - 如果在问病史："有高血压"、"有糖尿病"、"都没有"、"不清楚"

7. **语言风格**
   ✅ "胸口闷气短，这个要注意"
   ✅ "听起来可能是心脏供血不太好"
   ✅ "如果休息一会儿就好了，那还好"
   ❌ "请描述胸痛的性质和部位"
   ❌ "根据临床表现考虑冠心病"
   ❌ "建议进行心电图检查"

8. **风险等级判断**
   - emergency: 持续胸痛>15分钟、突然喘不上气、晕倒、疑似心梗/中风
   - high: 活动时胸闷、新发心慌、夜间憋醒
   - medium: 偶尔心慌、轻度胸闷、有多个危险因素（高血压+糖尿病+抽烟）
   - low: 偶尔不舒服、没有明显危险因素

输出 JSON：
{{
    "message": "自然的对话内容（可以多句话）",
    "next_action": "continue（继续聊）或 complete（给建议）",
    "stage": "collecting（还在了解）或 summary（给建议）",
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
