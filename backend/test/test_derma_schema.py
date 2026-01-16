"""
测试皮肤科 Schema 定义

验证新增的 Advice、KnowledgeRef、Condition、DiagnosisCard Schema
"""
import pytest
from pydantic import ValidationError


class TestDermaAdviceSchema:
    """测试 DermaAdviceSchema"""
    
    def test_valid_advice(self):
        """有效的建议数据应通过验证"""
        from app.schemas.derma import DermaAdviceSchema
        advice = DermaAdviceSchema(
            id="adv-001",
            title="初步建议",
            content="保持皮肤清洁干燥",
            evidence=["湿疹护理指南"],
            timestamp="2026-01-16T10:00:00"
        )
        assert advice.id == "adv-001"
        assert advice.title == "初步建议"
        assert len(advice.evidence) == 1
    
    def test_advice_without_evidence(self):
        """没有证据的建议也应有效（evidence 默认空列表）"""
        from app.schemas.derma import DermaAdviceSchema
        advice = DermaAdviceSchema(
            id="adv-002",
            title="护理提醒",
            content="避免抓挠",
            timestamp="2026-01-16T10:05:00"
        )
        assert advice.evidence == []


class TestDermaKnowledgeRefSchema:
    """测试 DermaKnowledgeRefSchema"""
    
    def test_valid_knowledge_ref(self):
        """有效的知识引用应通过验证"""
        from app.schemas.derma import DermaKnowledgeRefSchema
        ref = DermaKnowledgeRefSchema(
            id="ref-001",
            title="湿疹诊疗指南",
            snippet="湿疹是一种常见的皮肤炎症...",
            source="中华皮肤科杂志",
            link="https://example.com/eczema"
        )
        assert ref.id == "ref-001"
        assert ref.source == "中华皮肤科杂志"
    
    def test_knowledge_ref_optional_fields(self):
        """source 和 link 是可选字段"""
        from app.schemas.derma import DermaKnowledgeRefSchema
        ref = DermaKnowledgeRefSchema(
            id="ref-002",
            title="皮肤护理基础",
            snippet="皮肤是人体最大的器官..."
        )
        assert ref.source is None
        assert ref.link is None


class TestDermaConditionSchema:
    """测试 DermaConditionSchema"""
    
    def test_valid_condition(self):
        """有效的鉴别诊断条目"""
        from app.schemas.derma import DermaConditionSchema
        condition = DermaConditionSchema(
            name="湿疹",
            confidence=0.85,
            rationale=["红疹", "瘙痒", "对称分布"]
        )
        assert condition.name == "湿疹"
        assert condition.confidence == 0.85
        assert len(condition.rationale) == 3
    
    def test_condition_without_rationale(self):
        """没有依据的诊断条目也有效"""
        from app.schemas.derma import DermaConditionSchema
        condition = DermaConditionSchema(
            name="接触性皮炎",
            confidence=0.6
        )
        assert condition.rationale == []


class TestDermaDiagnosisCardSchema:
    """测试 DermaDiagnosisCardSchema"""
    
    def test_valid_diagnosis_card(self):
        """有效的诊断卡"""
        from app.schemas.derma import (
            DermaDiagnosisCardSchema,
            DermaConditionSchema,
            DermaKnowledgeRefSchema
        )
        card = DermaDiagnosisCardSchema(
            summary="手臂出现红疹，伴有瘙痒，已持续3天",
            conditions=[
                DermaConditionSchema(name="湿疹", confidence=0.8, rationale=["红疹", "瘙痒"]),
                DermaConditionSchema(name="接触性皮炎", confidence=0.5, rationale=["外露部位"])
            ],
            risk_level="low",
            need_offline_visit=False,
            care_plan=["保持清洁", "避免刺激"],
            reasoning_steps=["收集症状", "分析特征", "鉴别诊断"]
        )
        assert card.summary.startswith("手臂出现红疹")
        assert len(card.conditions) == 2
        assert card.risk_level == "low"
        assert not card.need_offline_visit
    
    def test_diagnosis_card_with_urgency(self):
        """带有紧急程度的诊断卡"""
        from app.schemas.derma import DermaDiagnosisCardSchema, DermaConditionSchema
        card = DermaDiagnosisCardSchema(
            summary="面部出现急性肿胀",
            conditions=[DermaConditionSchema(name="血管性水肿", confidence=0.9)],
            risk_level="high",
            need_offline_visit=True,
            urgency="建议24小时内就诊"
        )
        assert card.urgency == "建议24小时内就诊"
        assert card.need_offline_visit


class TestDermaResponseExtension:
    """测试 DermaResponse 新增字段"""
    
    def test_response_with_advice_history(self):
        """响应应支持 advice_history 字段"""
        from app.schemas.derma import DermaResponse, DermaAdviceSchema
        response = DermaResponse(
            type="conversation",
            session_id="test-session",
            message="请告诉我更多症状",
            progress=50,
            stage="collecting",
            advice_history=[
                DermaAdviceSchema(
                    id="adv-001",
                    title="初步建议",
                    content="先保持清洁",
                    timestamp="2026-01-16T10:00:00"
                )
            ]
        )
        assert response.advice_history is not None
        assert len(response.advice_history) == 1
    
    def test_response_with_diagnosis_card(self):
        """响应应支持 diagnosis_card 字段"""
        from app.schemas.derma import (
            DermaResponse,
            DermaDiagnosisCardSchema,
            DermaConditionSchema
        )
        card = DermaDiagnosisCardSchema(
            summary="诊断总结",
            conditions=[DermaConditionSchema(name="湿疹", confidence=0.8)],
            risk_level="low",
            need_offline_visit=False
        )
        response = DermaResponse(
            type="conversation",
            session_id="test-session",
            message="根据您描述的症状...",
            progress=100,
            stage="diagnosis",
            diagnosis_card=card
        )
        assert response.diagnosis_card is not None
        assert response.diagnosis_card.conditions[0].name == "湿疹"
    
    def test_response_with_knowledge_refs(self):
        """响应应支持 knowledge_refs 字段"""
        from app.schemas.derma import DermaResponse, DermaKnowledgeRefSchema
        response = DermaResponse(
            type="conversation",
            session_id="test-session",
            message="参考相关文献...",
            progress=80,
            stage="analyzing",
            knowledge_refs=[
                DermaKnowledgeRefSchema(
                    id="ref-001",
                    title="湿疹诊疗指南",
                    snippet="湿疹的诊断要点..."
                )
            ]
        )
        assert response.knowledge_refs is not None
        assert len(response.knowledge_refs) == 1
    
    def test_response_with_reasoning_steps(self):
        """响应应支持 reasoning_steps 字段"""
        from app.schemas.derma import DermaResponse
        response = DermaResponse(
            type="conversation",
            session_id="test-session",
            message="正在分析...",
            progress=70,
            stage="reasoning",
            reasoning_steps=["收集症状", "检索文献", "生成诊断"]
        )
        assert response.reasoning_steps is not None
        assert len(response.reasoning_steps) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
