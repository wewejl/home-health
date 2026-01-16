"""
测试 build_response 函数

验证新增的 advice_history, diagnosis_card, knowledge_refs, reasoning_steps 字段
"""
import pytest
from app.routes.derma import build_response
from app.services.dermatology.derma_agent import DermaTaskType


class TestBuildResponse:
    """测试 build_response 函数"""
    
    def get_base_state(self):
        """获取基础状态"""
        return {
            "session_id": "test-session-001",
            "user_id": 1,
            "current_response": "您好，请描述您的皮肤问题",
            "progress": 50,
            "stage": "collecting",
            "current_task": DermaTaskType.CONVERSATION,
            "awaiting_image": False,
            "quick_options": [],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_advice": ""
        }
    
    def test_build_response_with_advice_history(self):
        """响应应包含 advice_history"""
        state = self.get_base_state()
        state["advice_history"] = [
            {
                "id": "adv-001",
                "title": "初步建议",
                "content": "保持皮肤清洁",
                "evidence": ["湿疹护理指南"],
                "timestamp": "2026-01-16T10:00:00"
            }
        ]
        
        response = build_response(state)
        
        assert response.advice_history is not None
        assert len(response.advice_history) == 1
        assert response.advice_history[0].title == "初步建议"
    
    def test_build_response_with_diagnosis_card(self):
        """响应应包含 diagnosis_card"""
        state = self.get_base_state()
        state["diagnosis_card"] = {
            "summary": "手臂出现红疹，伴有瘙痒",
            "conditions": [
                {"name": "湿疹", "confidence": 0.8, "rationale": ["红疹", "瘙痒"]}
            ],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": ["保持清洁"],
            "reasoning_steps": ["收集症状", "分析特征"]
        }
        
        response = build_response(state)
        
        assert response.diagnosis_card is not None
        assert response.diagnosis_card.summary == "手臂出现红疹，伴有瘙痒"
        assert len(response.diagnosis_card.conditions) == 1
    
    def test_build_response_with_knowledge_refs(self):
        """响应应包含 knowledge_refs"""
        state = self.get_base_state()
        state["knowledge_refs"] = [
            {
                "id": "ref-001",
                "title": "湿疹诊疗指南",
                "snippet": "湿疹是一种常见的皮肤炎症...",
                "source": "中华皮肤科杂志"
            }
        ]
        
        response = build_response(state)
        
        assert response.knowledge_refs is not None
        assert len(response.knowledge_refs) == 1
        assert response.knowledge_refs[0].title == "湿疹诊疗指南"
    
    def test_build_response_with_reasoning_steps(self):
        """响应应包含 reasoning_steps"""
        state = self.get_base_state()
        state["reasoning_steps"] = ["收集症状", "检索文献", "生成诊断"]
        
        response = build_response(state)
        
        assert response.reasoning_steps is not None
        assert len(response.reasoning_steps) == 3
        assert "检索文献" in response.reasoning_steps
    
    def test_build_response_without_new_fields(self):
        """没有新字段时响应也应正常"""
        state = self.get_base_state()
        
        response = build_response(state)
        
        assert response.advice_history is None
        assert response.diagnosis_card is None
        assert response.knowledge_refs is None
        assert response.reasoning_steps is None
    
    def test_build_response_with_all_new_fields(self):
        """同时包含所有新字段"""
        state = self.get_base_state()
        state["advice_history"] = [
            {"id": "adv-001", "title": "建议1", "content": "内容1", "evidence": [], "timestamp": "2026-01-16T10:00:00"}
        ]
        state["diagnosis_card"] = {
            "summary": "诊断总结",
            "conditions": [{"name": "湿疹", "confidence": 0.8, "rationale": []}],
            "risk_level": "low",
            "need_offline_visit": False
        }
        state["knowledge_refs"] = [
            {"id": "ref-001", "title": "参考1", "snippet": "内容..."}
        ]
        state["reasoning_steps"] = ["步骤1", "步骤2"]
        
        response = build_response(state)
        
        assert response.advice_history is not None
        assert response.diagnosis_card is not None
        assert response.knowledge_refs is not None
        assert response.reasoning_steps is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
