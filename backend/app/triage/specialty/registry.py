"""Specialty pack registry."""
from typing import Dict

from .base_pack import SpecialtyPack


_PACKS: Dict[str, SpecialtyPack] = {
    "general": SpecialtyPack(
        code="general",
        display_name="全科导诊",
        required_slots=["symptoms", "duration", "severity", "accompanying_symptoms"],
        followup_questions=["症状持续多久", "有没有伴随症状", "目前严重程度如何"],
        min_evidence_count=1,
        min_avg_score=0.15,
        rewrite_terms=["症状", "病程", "诱因", "处理建议"],
        emergency_signs=["剧烈胸痛", "呼吸困难", "昏迷", "晕厥", "大出血", "抽搐"],
        high_risk_signs=["持续高热", "症状加重", "影响进食", "明显乏力"],
        warning_signals=["胸痛加重", "呼吸困难", "意识异常", "持续高热"],
        disposition_advice={
            "home": "可先居家观察并进行基础对症处理",
            "clinic": "建议尽快线下门诊就医",
            "urgent_clinic": "建议今日内尽快线下就医",
            "er": "请立即前往急诊或拨打120",
        },
    ),
    "cardiology": SpecialtyPack(
        code="cardiology",
        display_name="心血管导诊",
        required_slots=[
            "symptoms",
            "duration",
            "chest_pain_character",
            "activity_relation",
            "accompanying_symptoms",
        ],
        followup_questions=["胸痛持续多久", "胸痛是压榨样还是刺痛", "活动后是否加重，是否伴大汗或气短"],
        min_evidence_count=2,
        min_avg_score=0.20,
        rewrite_terms=["胸痛性质", "持续时间", "活动相关", "心肌缺血", "危险分层"],
        emergency_signs=["持续胸痛", "呼吸困难", "大汗", "晕厥", "濒死感"],
        high_risk_signs=["活动后胸闷", "心悸加重", "夜间憋醒", "下肢水肿"],
        warning_signals=["持续胸痛超过20分钟", "突发呼吸困难", "晕厥", "冷汗伴胸痛"],
        disposition_advice={
            "home": "如症状轻且短暂，可短时观察并避免剧烈活动",
            "clinic": "建议尽快心内科门诊评估",
            "urgent_clinic": "建议今日内前往心内科/胸痛门诊",
            "er": "疑似急性心血管事件，请立即急诊或拨打120",
        },
    ),
    "respiratory": SpecialtyPack(
        code="respiratory",
        display_name="呼吸导诊",
        required_slots=["symptoms", "duration", "temperature", "sputum", "accompanying_symptoms"],
        followup_questions=["有没有发热，最高体温多少", "咳嗽多久、是否有痰", "是否有胸闷气短或呼吸费力"],
        min_evidence_count=1,
        min_avg_score=0.15,
        rewrite_terms=["发热", "咳嗽病程", "痰性状", "气促", "肺部感染"],
        emergency_signs=["呼吸困难", "不能平卧", "紫绀", "喘憋", "意识模糊"],
        high_risk_signs=["咳喘加重", "胸闷", "痰中带血", "高热不退"],
        warning_signals=["静息气促", "口唇紫绀", "持续高热", "痰中带血"],
        disposition_advice={
            "home": "如症状轻，可先补液休息并观察",
            "clinic": "建议呼吸科门诊评估",
            "urgent_clinic": "建议今日内呼吸科就诊",
            "er": "出现呼吸衰竭风险信号，请立即急诊",
        },
    ),
    "dermatology": SpecialtyPack(
        code="dermatology",
        display_name="皮肤导诊",
        required_slots=["symptoms", "duration", "skin_location", "itch_or_pain"],
        followup_questions=["皮疹分布位置", "持续多久", "以瘙痒还是疼痛为主"],
        min_evidence_count=1,
        min_avg_score=0.10,
        rewrite_terms=["皮疹形态", "分布", "瘙痒", "诱因"],
        emergency_signs=["全身水疱", "喉头水肿", "发热伴皮疹"],
        high_risk_signs=["皮疹扩散", "破溃", "继发感染"],
        warning_signals=["皮疹迅速扩散", "发热", "喉头紧缩或呼吸困难"],
        disposition_advice={
            "home": "轻症可先避免刺激并观察",
            "clinic": "建议皮肤科门诊就诊",
            "urgent_clinic": "建议今日内皮肤科就诊",
            "er": "出现严重过敏或全身症状，请立即急诊",
        },
    ),
}


def get_specialty_pack(code: str) -> SpecialtyPack:
    """Return pack by specialty code; fallback to general."""
    if not code:
        return _PACKS["general"]
    return _PACKS.get(code, _PACKS["general"])
