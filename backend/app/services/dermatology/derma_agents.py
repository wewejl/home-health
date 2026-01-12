"""
CrewAI 1.x 皮肤科问诊单智能体
仅保留对话编排能力，移除图像/报告相关逻辑
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


class ConversationOutput(BaseModel):
    """对话编排器输出 Schema"""
    message: str = Field(description="回复消息")
    next_action: str = Field(description="下一步动作: continue 或 complete")
    stage: str = Field(default="collecting", description="当前阶段")
    quick_options: List[Dict[str, str]] = Field(default_factory=list, description="快捷选项")
    extracted_info: Dict[str, Any] = Field(default_factory=dict, description="从用户输入提取的信息")


CONVERSATION_ORCHESTRATOR_BACKSTORY = """你是一位经验丰富的皮肤科问诊协调员，只负责文字问诊。
目标：通过多轮对话了解患者皮肤问题，并给出温和、专业的建议。

【最高优先级：及时总结】
当满足以下任一条件时，你必须立即进入总结阶段（stage: "summary", next_action: "complete"）：
1. 已连续追问 ≥5 轮
2. 已掌握 ≥3 项关键信息（主诉、部位、持续时间、症状特征、诱因等）
3. 用户明确请求分析/总结（如"是什么问题""你分析一下""都问了好几个问题了"）
总结时直接给出症状归纳、可能原因、建议，避免再次追问。

【核心原则：症状导向追问】
首先识别患者描述中的主要症状类别（红肿、瘙痒、疼痛、渗液、异味、排尿困难等），然后优先围绕该症状的关键特征进行追问。
示例：
- 红肿 → 追问是否伴随瘙痒、灼痛、渗液、局部发热
- 灼痛 → 追问排尿是否困难、是否伴随异味、疼痛程度
- 瘙痒 → 追问瘙痒程度（轻微/中度/剧烈）、是否抓破、是否有渗液或结痂

【表达技巧】
1. 追问前先复述用户提供的部位和症状（如"你提到阴茎皮肤红肿…"），展现已充分理解，避免泛泛的"能否详细描述"。
2. 若用户描述含糊（例如"有点问题"），结合已知部位，列出 2-3 个常见表现供其确认（如"主要是瘙痒、疼痛还是出现渗液？"）。
3. 对隐私部位使用尊重而具体的措辞，可将口语转化为医学但自然的表达（"私密部位/阴茎/外阴"），同时保持同理心。
4. 当用户提到非皮肤症状（如腹痛）或跨专业问题，先表达理解，再温和说明自己聚焦皮肤表现，并引导其描述皮肤相关线索。

【问诊推进原则】
1. 当主要症状的核心特征已明确时，转向询问相关并发症/风险信号（如感染迹象、排尿问题、性行为史）或对生活的影响，而非重复基础字段。
2. 若症状特征基本清楚，再补齐未覆盖的基础信息（部位范围、持续时间、诱因、既往史、护理措施等）。

【沟通规范】
1. 每次只提出一个最重要的问题，语气有同理心但避免过度礼貌套话（如"感谢你说明情况"）。
2. 不要求上传任何图片或报告，所有判断基于文字描述。
3. 每次回复附带 3-5 个可点击的快捷选项，选项需与当前追问紧密相关，并覆盖常见回答区间。
4. 敏感或私密部位要主动表达尊重和理解，复述用户诉求后再提出问题。
5. 如用户描述与皮肤无关，先回应关切，再引导回皮肤表现。
6. 每次追问需附带简短依据说明（如"灼烧感常与刺激或感染相关，因此需要确认是否伴随排尿疼痛"），帮助患者理解追问逻辑。
7. 免责声明由前端统一展示，模型输出无需包含。
"""


def create_conversation_orchestrator(llm: LLM = None) -> Agent:
    """创建单一对话编排 Agent"""
    if llm is None:
        llm = create_llm()
    return Agent(
        role="皮肤科问诊协调员",
        goal="通过纯文本问诊收集症状信息并给出初步建议",
        backstory=CONVERSATION_ORCHESTRATOR_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=10,
        max_retry_limit=2,
    )


def create_conversation_task(
    agent: Agent,
    state: Dict[str, Any],
    user_input: str,
) -> Task:
    """创建对话任务"""
    state_snapshot = _format_state_snapshot(state)
    questions_asked = state.get("questions_asked", 0)
    context = f"""
最近对话：
{_format_recent_messages(state.get('messages', []))}

结构化关键信息：
{state_snapshot}

用户最新输入：{user_input}
"""

    # 检查是否应该强制总结
    should_summarize = (
        questions_asked >= 5 or  # 已问5轮以上
        sum([bool(state.get(k)) for k in ["chief_complaint", "skin_location", "duration", "symptoms"]]) >= 3 or  # 已有3项关键信息
        any(keyword in user_input.lower() for keyword in ["分析", "总结", "是什么问题", "怎么办", "好几个问题", "接下来"])  # 用户请求总结
    )
    
    summary_instruction = ""
    if should_summarize:
        summary_instruction = f"""
⚠️ 重要：当前已满足总结条件（已追问 {questions_asked} 轮 / 用户请求总结），你必须立即进入总结阶段。
请输出 stage: "summary", next_action: "complete"，并在 message 中直接给出症状归纳、可能原因和建议，不要再追问新问题。
"""
    
    return Task(
        description=f"""根据用户文本输入继续皮肤科问诊。

{context}
{summary_instruction}

任务要求：
1. 根据最近对话和用户最新输入，自由判断下一步最有价值的追问方向，优先关注用户提到的症状特征。
2. 若对话刚开始或信息较少，先围绕用户描述的核心症状（如红肿、瘙痒、疼痛等）展开追问。
3. 若已有一定信息积累，可转向相关并发症、风险信号、生活影响或其他临床关注点。
4. 根据对话进展决定下一步：continue（继续问诊）或 complete（信息充足，可总结）
5. 生成自然、有同理心的回复，避免过度礼貌套话（如"感谢你说明情况"），若继续问诊需明确提出下一个问题
6. 【追问依据】每次追问需附带简短依据说明（如"灼烧感常与刺激或感染相关，因此需要确认是否伴随排尿疼痛"）
7. 【快捷选项要求】给出 3-5 个快捷选项，选项需与当前追问紧密相关，覆盖常见回答（如"有瘙痒/无瘙痒/伴随灼痛"、"轻微/中度/剧烈"、"有渗液/无渗液"等）
8. 【总结阶段要求】当问诊信息充足时，必须输出 stage: "summary" 且 next_action: "complete"，总结内容需：
   - 简洁实用：直接归纳症状要点、可能原因和建议/下一步（如是否需线下就诊）
   - 说明关键判断依据（示例："持续灼烧感通常提示刺激或感染，因此建议…"）
   - 避免冗长礼貌语，聚焦临床价值
   - 触发条件（满足任一即可进入总结）：已掌握≥3项关键字段（主诉/部位/持续时间/症状/诱因等）、已连续追问≥5轮（当前累计 {questions_asked} 轮）、用户明确请求分析/总结/判断下一步（如"是什么问题""你分析一下""接下来怎么办"等）
9. 免责声明由前端统一展示，模型输出无需包含

输出 JSON：
{{
    "message": "回复消息（信息收集阶段：包含针对当前症状的追问+简短依据；总结阶段：简洁归纳症状要点、可能原因、建议及判断依据）",
    "next_action": "continue/complete",
    "stage": "collecting|summary",
    "quick_options": [{{"text": "选项文本", "value": "选项值", "category": "症状类别"}}],
    "extracted_info": {{"chief_complaint": "", "skin_location": "", "duration": "", "symptoms": []}}
}}
""",
        expected_output="JSON格式的对话输出",
        agent=agent,
        output_pydantic=ConversationOutput
    )


def create_safety_check_task(
    agent: Agent,
    content: str,
    risk_level: str = "medium"
) -> Task:
    """创建安全审查任务"""
    return Task(
        description=f"""审查以下AI生成内容的安全性和合规性。

待审查内容：
{content}

风险等级：{risk_level}

任务要求：
1. 检查内容是否包含适当的免责声明
2. 检查是否有过度诊断或不当建议
3. 对于高风险情况，确保有就医提醒
4. 如需修改，提供修改后的内容

输出 JSON 格式：
{{
    "is_safe": true/false,
    "warnings": ["警告1", "警告2"],
    "disclaimer": "免责声明",
    "modified_message": "修改后的消息（如无需修改则为null）"
}}
""",
        expected_output="JSON格式的安全审查结果",
        agent=agent
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


def _format_state_snapshot(state: Dict[str, Any]) -> str:
    """汇总结构化问诊信息，帮助 Agent 判断进展"""
    if not state:
        return "暂无结构化信息（尚未明确主诉、部位或持续时间）"

    snapshot = []
    chief = state.get("chief_complaint", "")
    location = state.get("skin_location", "")
    duration = state.get("duration", "")
    symptoms = state.get("symptoms") or []

    # 显示已收集的信息
    if chief:
        snapshot.append(f"- 主诉: {chief}")
    else:
        snapshot.append(f"- 主诉: 未明确")
    
    if location:
        snapshot.append(f"- 部位: {location}")
    else:
        snapshot.append(f"- 部位: 未明确")
    
    if duration:
        snapshot.append(f"- 持续时间: {duration}")
    else:
        snapshot.append(f"- 持续时间: 未明确")
    
    if symptoms:
        symptom_list = ", ".join(symptoms[:5])
        if len(symptoms) > 5:
            symptom_list += " 等"
        snapshot.append(f"- 记录症状: {symptom_list}")
    else:
        snapshot.append(f"- 记录症状: 未明确")

    # 计算已填充的关键字段数量
    filled_fields = [
        bool(chief),
        bool(location),
        bool(duration),
        bool(symptoms),
        bool(state.get("symptom_details")),
    ]
    completeness = sum(1 for filled in filled_fields if filled)
    snapshot.append(f"- 关键信息收集进度: {completeness}/{len(filled_fields)}")
    snapshot.append(f"- 已追问轮次: {state.get('questions_asked', 0)}")

    return "\n".join(snapshot)


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
