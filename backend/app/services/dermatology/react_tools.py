"""
皮肤科 ReAct Agent 工具定义

LLM 可调用的医疗工具集
"""
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..llm_provider import LLMProvider


class SkinAnalysisResult(BaseModel):
    """图片分析结果"""
    description: str = Field(description="皮损描述")
    morphology: str = Field(description="形态特征")
    color: str = Field(description="颜色特征")
    distribution: str = Field(description="分布特征")
    suggested_conditions: List[str] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    """诊断结果"""
    conditions: List[dict] = Field(default_factory=list)
    risk_level: str = Field(default="low")
    care_advice: str = Field(default="")
    need_offline_visit: bool = Field(default=False)


class ConditionOutput(BaseModel):
    """鉴别诊断条目输出"""
    name: str = Field(description="诊断名称")
    confidence: float = Field(description="置信度 0-1")
    rationale: List[str] = Field(default_factory=list, description="诊断依据")


class DiagnosisOutput(BaseModel):
    """结构化诊断输出"""
    summary: str = Field(description="症状总结")
    conditions: List[ConditionOutput] = Field(default_factory=list, description="鉴别诊断列表")
    risk_level: str = Field(default="low", description="风险等级: low/medium/high/emergency")
    need_offline_visit: bool = Field(default=False, description="是否需要线下就诊")
    urgency: Optional[str] = Field(default=None, description="就诊紧急程度说明")
    care_plan: List[str] = Field(default_factory=list, description="护理建议列表")
    reasoning_steps: List[str] = Field(default_factory=list, description="推理步骤")


# === 本地知识库（模拟，实际可用向量数据库） ===
DERMA_KNOWLEDGE_BASE = [
    {
        "id": "kb-001",
        "title": "湿疹诊疗指南",
        "snippet": "湿疹是一种常见的皮肤炎症，表现为红斑、丘疹、水疱，伴有剧烈瘙痒。治疗以保湿、抗炎为主，避免刺激物接触。",
        "source": "中华皮肤科杂志",
        "keywords": ["湿疹", "红斑", "瘙痒", "炎症", "保湿"]
    },
    {
        "id": "kb-002",
        "title": "接触性皮炎诊断要点",
        "snippet": "接触性皮炎由外界物质接触引起，分为刺激性和变应性两类。皮损局限于接触部位，边界清楚，去除致敏原后可自愈。",
        "source": "皮肤病学教材",
        "keywords": ["接触性皮炎", "过敏", "刺激", "局限", "致敏原"]
    },
    {
        "id": "kb-003",
        "title": "银屑病临床特征",
        "snippet": "银屑病表现为红色斑块覆盖银白色鳞屑，刮除鳞屑可见薄膜现象和点状出血。好发于头皮、肘膝伸侧。",
        "source": "皮肤科临床实践",
        "keywords": ["银屑病", "鳞屑", "红斑", "银白色", "点状出血"]
    },
    {
        "id": "kb-004",
        "title": "汗疱疹护理指南",
        "snippet": "汗疱疹多发于手指侧面、手掌，表现为深在性小水疱，伴有瘙痒。保持干燥、避免刺激是关键护理措施。",
        "source": "皮肤病护理手册",
        "keywords": ["汗疱疹", "水疱", "手指", "手掌", "瘙痒"]
    },
    {
        "id": "kb-005",
        "title": "荨麻疹鉴别诊断",
        "snippet": "荨麻疹表现为一过性风团，大小不等，消退后不留痕迹。急性荨麻疹多与食物、药物过敏相关。",
        "source": "过敏性皮肤病诊疗",
        "keywords": ["荨麻疹", "风团", "过敏", "瘙痒", "一过性"]
    }
]


@tool
def retrieve_derma_knowledge(
    symptoms: List[str],
    location: str,
    query: str = ""
) -> List[dict]:
    """
    检索皮肤科医学知识库
    
    Args:
        symptoms: 症状列表，如 ["红疹", "瘙痒"]
        location: 皮损部位，如 "手臂"
        query: 补充查询词（可选）
    
    Returns:
        [{id, title, snippet, source, link}] 相关知识条目列表
    """
    # 构建搜索关键词
    search_terms = set()
    for s in symptoms:
        search_terms.add(s.lower())
    if location:
        search_terms.add(location.lower())
    if query:
        search_terms.add(query.lower())
    
    # 简单关键词匹配（实际可用向量检索）
    results = []
    for kb in DERMA_KNOWLEDGE_BASE:
        score = 0
        keywords = [k.lower() for k in kb.get("keywords", [])]
        title_lower = kb["title"].lower()
        snippet_lower = kb["snippet"].lower()
        
        for term in search_terms:
            if term in keywords:
                score += 3
            elif term in title_lower:
                score += 2
            elif term in snippet_lower:
                score += 1
        
        if score > 0:
            results.append({
                "id": kb["id"],
                "title": kb["title"],
                "snippet": kb["snippet"],
                "source": kb.get("source"),
                "link": kb.get("link"),
                "_score": score
            })
    
    # 按相关度排序，返回 top 3
    results.sort(key=lambda x: x["_score"], reverse=True)
    for r in results:
        del r["_score"]
    
    return results[:3] if results else [{
        "id": "kb-default",
        "title": "皮肤科基础知识",
        "snippet": "建议保持皮肤清洁干燥，避免刺激物接触，如症状持续或加重请及时就医。",
        "source": "通用护理指南"
    }]


@tool
def analyze_skin_image(image_base64: str, chief_complaint: str = "") -> dict:
    """
    分析皮肤图片，识别皮损特征。
    
    Args:
        image_base64: 图片的 base64 编码（带 data:image 前缀）
        chief_complaint: 患者主诉，帮助分析
    
    Returns:
        包含皮损描述、形态、颜色、分布特征的分析结果
    """
    llm = LLMProvider.get_multimodal_llm()
    
    prompt = """你是皮肤科影像专家。分析皮肤照片，描述皮损特征。

分析要点：
- 形态：斑、丘疹、水疱、结节等
- 颜色：红、褐、紫、白等
- 分布：局限性、泛发性、对称性
- 边界：清楚或模糊

用简洁专业的语言描述。"""
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": image_base64}},
            {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{chief_complaint or '未说明'}"}
        ])
    ]
    
    response = llm.invoke(messages)
    
    return {
        "description": response.content,
        "type": "skin_analysis"
    }


@tool
def generate_diagnosis(
    symptoms: List[str],
    location: str,
    duration: str,
    additional_info: str = ""
) -> dict:
    """
    综合问诊信息生成初步诊断建议。
    
    Args:
        symptoms: 症状列表，如 ["瘙痒", "红斑", "脱皮"]
        location: 皮损部位，如 "面部" "手臂"
        duration: 持续时间，如 "三天" "一周"
        additional_info: 其他信息，如图片分析结果
    
    Returns:
        包含鉴别诊断、风险等级、护理建议的诊断结果
    """
    llm = LLMProvider.get_llm()
    
    prompt = f"""作为皮肤科专家，根据以下信息给出初步诊断建议：

症状：{', '.join(symptoms) if symptoms else '未明确'}
部位：{location or '未明确'}
持续时间：{duration or '未明确'}
{f'补充信息：{additional_info}' if additional_info else ''}

请给出：
1. 1-3个可能的诊断（按可能性排序）
2. 风险等级（low/medium/high/emergency）
3. 护理建议
4. 是否需要线下就诊

用自然语言回复，不要输出 JSON。"""
    
    response = llm.invoke(prompt)
    
    return {
        "diagnosis_text": response.content,
        "type": "diagnosis"
    }


@tool
def generate_structured_diagnosis(
    symptoms: List[str],
    location: str,
    duration: str,
    knowledge_refs: List[dict] = [],
    additional_info: str = ""
) -> dict:
    """
    生成结构化诊断卡，包含鉴别诊断、风险等级、护理建议等。
    
    Args:
        symptoms: 症状列表，如 ["红疹", "瘙痒", "脱皮"]
        location: 皮损部位，如 "手臂"
        duration: 持续时间，如 "三天"
        knowledge_refs: 检索到的知识引用列表
        additional_info: 其他信息，如图片分析结果
    
    Returns:
        结构化诊断卡，包含 summary, conditions, risk_level, care_plan 等
    """
    llm = LLMProvider.get_llm()
    structured_llm = llm.with_structured_output(DiagnosisOutput)
    
    # 构建参考资料文本
    refs_text = ""
    if knowledge_refs:
        refs_text = "\n参考资料：\n" + "\n".join([
            f"- {ref.get('title', '')}: {ref.get('snippet', '')}"
            for ref in knowledge_refs
        ])
    
    prompt = f"""作为皮肤科专家，根据以下信息生成结构化诊断：

症状：{', '.join(symptoms) if symptoms else '未明确'}
部位：{location or '未明确'}
持续时间：{duration or '未明确'}
{f'补充信息：{additional_info}' if additional_info else ''}
{refs_text}

请输出：
1. summary: 症状总结（一句话）
2. conditions: 鉴别诊断列表，每个包含 name（诊断名）、confidence（0-1置信度）、rationale（依据列表）
3. risk_level: 风险等级（low/medium/high/emergency）
4. need_offline_visit: 是否建议线下就诊
5. urgency: 如需就诊，紧急程度说明
6. care_plan: 护理建议列表
7. reasoning_steps: 你的推理步骤"""
    
    try:
        result = structured_llm.invoke(prompt)
        return result.model_dump()
    except Exception as e:
        # fallback：返回默认结构
        return {
            "summary": f"症状：{', '.join(symptoms) if symptoms else '待进一步了解'}",
            "conditions": [],
            "risk_level": "low",
            "need_offline_visit": False,
            "urgency": None,
            "care_plan": ["建议保持皮肤清洁", "避免刺激"],
            "reasoning_steps": ["信息收集", "生成建议"]
        }


@tool
def record_intermediate_advice(
    title: str,
    content: str,
    evidence: List[str] = []
) -> dict:
    """
    记录中间护理建议
    
    在问诊过程中，当你给出护理建议或风险提示时调用此工具。
    例如：建议保持清洁、避免抓挠等初步护理措施。
    
    Args:
        title: 建议标题，如"初步护理建议"、"风险提示"
        content: 建议内容，清晰具体的护理指导
        evidence: 依据列表（可选），如 ["湿疹护理指南"]
    
    Returns:
        结构化建议对象，包含 id、timestamp 等字段
    """
    import uuid
    from datetime import datetime
    
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "evidence": evidence,
        "timestamp": datetime.utcnow().isoformat()
    }


def get_derma_tools():
    """获取皮肤科工具列表"""
    return [
        analyze_skin_image, 
        generate_diagnosis, 
        retrieve_derma_knowledge, 
        generate_structured_diagnosis,
        record_intermediate_advice
    ]
