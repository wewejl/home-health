"""智能事件聚合服务提示词"""

AGGREGATION_PROMPTS = {
    "system": """你是一位医疗数据分析专家，负责分析病历事件之间的关联性。

你的任务：
1. 判断多个病历事件是否属于同一病情
2. 分析病情演变趋势
3. 生成合并建议
4. 输出必须是有效的 JSON 格式

判断标准：
- 症状相似度
- 时间关联性（7天内高度相关）
- 科室一致性
- 病程连续性""",

    "analyze_relation": """请分析以下两个病历事件是否属于同一病情。

【事件 A】
标题：{event_a_title}
科室：{event_a_department}
主诉：{event_a_complaint}
症状：{event_a_symptoms}
时间：{event_a_time}
摘要：{event_a_summary}

【事件 B】
标题：{event_b_title}
科室：{event_b_department}
主诉：{event_b_complaint}
症状：{event_b_symptoms}
时间：{event_b_time}
摘要：{event_b_summary}

请分析并输出 JSON：
{{
    "is_related": true/false,
    "relation_type": "same_condition/follow_up/complication/unrelated",
    "confidence": 0.85,
    "reasoning": "分析理由",
    "should_merge": true/false,
    "merge_suggestion": "合并建议描述"
}}

请直接输出 JSON：""",

    "find_related_events": """请从以下事件列表中找出与目标事件相关的病历。

【目标事件】
标题：{target_title}
科室：{target_department}
主诉：{target_complaint}
症状：{target_symptoms}
时间：{target_time}

【候选事件列表】
{candidate_events}

请输出 JSON：
{{
    "related_events": [
        {{
            "event_id": "事件ID",
            "relation_type": "same_condition/follow_up/complication",
            "confidence": 0.85,
            "reasoning": "关联理由"
        }}
    ],
    "merge_candidates": ["建议合并的事件ID列表"],
    "timeline_order": ["按时间排序的事件ID"]
}}

请直接输出 JSON：""",

    "generate_merged_summary": """请为以下合并的病历事件生成综合摘要。

【事件列表】
{events}

请输出 JSON：
{{
    "merged_title": "合并后的标题",
    "summary": "综合摘要（200-300字）",
    "disease_progression": "病情演变描述",
    "key_milestones": [
        {{
            "time": "时间",
            "event": "里程碑事件"
        }}
    ],
    "current_status": "当前状态",
    "overall_risk_level": "low/medium/high/emergency",
    "recommendations": ["综合建议"]
}}

请直接输出 JSON：""",

    "smart_aggregate": """分析用户的会话记录，判断应该归入哪个现有事件或创建新事件。

【新会话信息】
科室：{session_department}
主诉：{session_complaint}
时间：{session_time}
对话摘要：{session_summary}

【现有事件列表】
{existing_events}

请输出 JSON：
{{
    "action": "add_to_existing/create_new",
    "target_event_id": "目标事件ID（如适用）",
    "confidence": 0.85,
    "reasoning": "决策理由",
    "suggested_title": "建议的事件标题（如创建新事件）"
}}

请直接输出 JSON："""
}
