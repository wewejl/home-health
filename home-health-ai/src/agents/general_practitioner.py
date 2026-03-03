#!/usr/bin/env python3
"""
全科医生智能体 - General Practitioner Agent

基于 Microsoft AutoGen 0.7.5 官方 API 实现

官方文档: https://github.com/microsoft/autogen
"""

import asyncio
import logging
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily
from config.settings import create_model_client

logger = logging.getLogger(__name__)


# =====================================================
# 工具函数 (Tools)
# =====================================================

async def search_disease_info(disease_name: str) -> str:
    """查询疾病基本信息

    Args:
        disease_name: 疾病名称

    Returns:
        疾病的基本信息、症状、建议
    """
    disease_db = {
        # 呼吸系统
        "感冒": {
            "description": "上呼吸道病毒感染",
            "symptoms": "鼻塞、流涕、咳嗽、咽痛、发热",
            "advice": "多休息、多喝水、对症治疗、注意隔离"
        },
        "咽炎": {
            "description": "咽部黏膜炎症，可分为急性和慢性",
            "symptoms": "咽痛、灼烧感、异物感、干咳",
            "advice": "多喝温水、温盐水漱口、避免辛辣刺激、戒烟酒"
        },
        "急性咽炎": {
            "description": "咽部黏膜急性炎症，常由病毒或细菌感染引起",
            "symptoms": "咽痛剧烈、灼烧感、吞咽困难、发热",
            "advice": "休息多喝水、温盐水漱口、严重时及时就医使用抗生素"
        },
        "扁桃体炎": {
            "description": "扁桃体炎症，常见于青少年",
            "symptoms": "咽痛、发热、扁桃体肿大、乏力",
            "advice": "休息、多喝水、细菌感染需用抗生素"
        },
        "会厌炎": {
            "description": "会厌部急性炎症，属急症可危及生命",
            "symptoms": "剧烈咽痛、吞咽困难、说话含糊、呼吸困难",
            "advice": "⚠️ 急症！立即就医或拨打120，不可延误"
        },
        "过敏性鼻炎": {
            "description": "鼻黏膜变态反应性疾病",
            "symptoms": "鼻塞、流涕、打喷嚏、鼻痒、眼睛痒",
            "advice": "避免接触过敏原、使用抗组胺药、鼻喷激素"
        },
        "支气管炎": {
            "description": "支气管黏膜炎症",
            "symptoms": "咳嗽、咳痰、胸闷、发热",
            "advice": "休息多喝水、止咳化痰、细菌感染用抗生素"
        },
        # 心血管系统
        "高血压": {
            "description": "动脉血压持续升高的慢性病",
            "symptoms": "头痛、头晕、耳鸣、心悸",
            "advice": "低盐饮食、规律运动、按时服药、定期监测血压"
        },
        "冠心病": {
            "description": "冠状动脉粥样硬化性心脏病",
            "symptoms": "胸痛、胸闷、心悸、气短",
            "advice": "低脂饮食、规律服药、随身携带硝酸甘油、定期复查"
        },
        # 消化系统
        "胃炎": {
            "description": "胃黏膜炎症",
            "symptoms": "上腹痛、腹胀、恶心、食欲不振",
            "advice": "规律饮食、避免刺激性食物、少食多餐"
        },
        "胃食管反流": {
            "description": "胃内容物反流至食管",
            "symptoms": "反酸、烧心、胸骨后疼痛、咽部异物感",
            "advice": "少食多餐、避免睡前进食、抬高床头"
        },
        # 内分泌代谢
        "糖尿病": {
            "description": "代谢性疾病，特征是高血糖",
            "symptoms": "多饮、多尿、多食、体重下降",
            "advice": "控制饮食、规律运动、监测血糖、按时用药"
        },
        # 其他常见
        "偏头痛": {
            "description": "反复发作的血管性头痛",
            "symptoms": "单侧搏动性头痛、恶心畏光、发作前有先兆",
            "advice": "避免诱因、发作时休息、止痛药治疗"
        },
        "中暑": {
            "description": "高温环境下体温调节功能障碍",
            "symptoms": "头晕头痛、口渴多汗、面色潮红、体温升高",
            "advice": "立即转移至阴凉处、补充水分、严重时立即就医"
        },
        "空气污染综合征": {
            "description": "空气污染引起的呼吸道刺激症状",
            "symptoms": "咽干咽痛、咳嗽、鼻塞、眼睛不适",
            "advice": "减少外出、佩戴防护口罩、使用空气净化器、多喝水"
        },
    }

    result = disease_db.get(disease_name)
    if result:
        logger.info(f"查询疾病: {disease_name}")
        return f"【{disease_name}】\n{result['description']}\n\n常见症状: {result['symptoms']}\n\n建议: {result['advice']}"
    else:
        return f"未找到疾病 '{disease_name}' 的详细信息，请提供更具体的疾病名称"


async def search_medication(medication_name: str) -> str:
    """查询药物基本信息

    Args:
        medication_name: 药物名称

    Returns:
        药物的作用、用法、注意事项
    """
    medication_db = {
        "阿司匹林": {
            "effect": "抗血小板聚集，预防血栓",
            "usage": "口服，每日一次，每次100mg",
            "warning": "胃肠道溃疡患者慎用，避免与酒精同服"
        },
        "阿莫西林": {
            "effect": "抗生素，治疗细菌感染",
            "usage": "口服，每8小时一次，每次500mg",
            "warning": "青霉素过敏者禁用，完成整个疗程"
        },
        "布洛芬": {
            "effect": "解热镇痛抗炎",
            "usage": "口服，每6-8小时一次，每次200-400mg",
            "warning": "饭后服用，避免空腹，胃溃疡患者慎用"
        },
        "二甲双胍": {
            "effect": "降血糖药，治疗2型糖尿病",
            "usage": "口服，每日2-3次，每次500mg",
            "warning": "定期检查肾功能，避免饮酒"
        },
    }

    result = medication_db.get(medication_name)
    if result:
        logger.info(f"查询药物: {medication_name}")
        return f"【{medication_name}】\n作用: {result['effect']}\n\n用法: {result['usage']}\n\n注意事项: {result['warning']}"
    else:
        return f"未找到药物 '{medication_name}' 的详细信息"


# =====================================================
# 全科医生智能体 (General Practitioner Agent)
# =====================================================

def create_general_practitioner(
    model_client: OpenAIChatCompletionClient | None = None,
    model_client_stream: bool = False,
) -> AssistantAgent:
    """创建全科医生智能体 (使用 AutoGen 0.7.5 官方 API)

    官方文档: https://microsoft.github.io/autogen/user-guide/core-user-guide/design-patterns/agents/

    Args:
        model_client: 模型客户端，默认使用配置文件中的 DeepSeek

    Returns:
        AssistantAgent: 全科医生智能体实例

    使用示例:
        >>> agent = create_general_practitioner()
        >>> result = await agent.run(task="我头痛头晕三天了")
        >>> print(result)
    """
    # 创建模型客户端（如果未提供）
    if model_client is None:
        model_client = create_model_client(parallel_tool_calls=False)

    # 工具列表
    tools = [
        search_disease_info,
        search_medication,
    ]

    # 系统提示词
    system_message = """你是"灵犀健康"的全科医生智能助手。

【核心工作模式：像医生一样问诊】
你的目标是像真实医生一样，通过对话逐步了解病情，而不是快速下结论。真实医生会：
- 听完患者描述后，脑海中产生几个可能的方向
- 根据患者回答，不断调整追问的方向
- 每次获得新信息后，都会产生新的疑问
- 直到信息足够完整，才给出分析和建议

【医生的临床思维模式】
每次收到用户消息后，按以下方式思考：

1. **当前已知什么？** - 总结已获得的关键信息
2. **可能是什么？** - 列出2-3种可能的方向
3. **还需要排除什么？** - 思考哪些可能性需要进一步确认
4. **下一步问什么？** - 追问最能帮助鉴别诊断的问题
5. **信息足够了吗？** - 只有当主要方向都比较清晰时，才给出建议

【追问策略：动态调整】
不要按固定清单问问题，而是根据已有信息动态调整：

示例场景：
```
用户：喉咙疼，家里装修了
AI思考：可能是环境刺激、感染或过敏。需要了解时间线 → 追问：什么时候开始的？

用户：天气暖和后出现的，逐步加重
AI思考：环境因素可能性增大。需要确认疼痛性质 → 追问：什么感觉？

用户：刀割样疼痛、灼烧感
AI思考：感染或炎症可能性增大。需要了解伴随症状 → 追问：有发热、咳嗽吗？

用户：没有发热，有咳嗽、鼻塞
AI思考：可能是环境刺激引起的上呼吸道炎症或过敏。需要了解环境关联 → 追问：什么时间/地点更重？

用户：晚上卧室更重
AI思考：卧室环境因素确实相关。还需要了解既往情况 → 追问：以前有过类似情况吗？

用户：没有
AI思考：信息基本完整了，是环境刺激引起的上呼吸道问题 → 给出分析和建议
```

【深度思考格式】
每次回复开头展示你的思考过程：
深度思考（当前已知XXX，可能是AAA或BBB。需要了解YYY来区分这些可能性。）

【追问示例】
深度思考（用户主诉喉咙疼痛且提到装修，可能是环境刺激或感染。需要先了解症状持续时间和发展模式来区分。）

理解您的不适。您提到喉咙疼，我需要了解一下：
这种疼痛是什么时候开始的？是突然出现的，还是慢慢加重的？

【何时给建议】
只有当以下信息都比较清晰时，才给出完整建议：
- 症状性质和持续时间
- 伴随症状情况
- 环境或诱发因素
- 既往相关情况（如果需要）

如果还有重要信息缺失，继续追问，不要急着下结论。

【给建议的格式】
深度思考（综合来看，最可能是XXX，需要警惕YYY风险。）

根据您的描述，我为您分析：

## 可能的原因
1. XXX（简要说明）
2. YYY（简要说明）

## 建议措施
- 措施1
- 措施2

## 何时就医
- 需要就医的情况

【工具使用原则】
- 只有在用户**明确询问**某个具体疾病/药物时，才调用工具
- 给健康建议时，不要调用工具，直接基于你的医学知识回答

【重要原则】
- 像医生一样，每次只问1-2个最相关的问题
- 根据用户回答动态调整追问方向
- 深度思考要展示你的推理过程
- 不要追求高效，追求的是全面了解
- 先共情，再追问或给建议
- 不做确定性诊断

【重要声明】
⚠️ 你是辅助工具，不能替代医生诊断
⚠️ 所有建议仅供参考，请结合个人情况
"""

    # 创建 AssistantAgent (AutoGen 0.7.5 官方 API)
    agent = AssistantAgent(
        name="general_practitioner",
        model_client=model_client,
        tools=tools,
        system_message=system_message,
        model_client_stream=model_client_stream,
    )

    logger.info("全科医生智能体创建成功 (AutoGen 0.7.5)")

    return agent


# =====================================================
# 导出的函数和类
# =====================================================

__all__ = [
    "search_disease_info",
    "search_medication",
    "create_general_practitioner",
]
