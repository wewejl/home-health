"""
测试 ReAct Agent 状态定义

验证 DermaReActState 包含所有必需字段
"""
import pytest
from app.services.dermatology.react_state import (
    DermaReActState,
    create_react_initial_state
)


class TestDermaReActState:
    """测试 DermaReActState 类型定义"""
    
    def test_create_initial_state_has_advice_history(self):
        """初始状态应包含 advice_history 字段"""
        state = create_react_initial_state("test-session", 1)
        assert "advice_history" in state
        assert isinstance(state["advice_history"], list)
        assert len(state["advice_history"]) == 0
    
    def test_create_initial_state_has_diagnosis_card(self):
        """初始状态应包含 diagnosis_card 字段"""
        state = create_react_initial_state("test-session", 1)
        assert "diagnosis_card" in state
        assert state["diagnosis_card"] is None
    
    def test_create_initial_state_has_reasoning_steps(self):
        """初始状态应包含 reasoning_steps 字段"""
        state = create_react_initial_state("test-session", 1)
        assert "reasoning_steps" in state
        assert isinstance(state["reasoning_steps"], list)
        assert len(state["reasoning_steps"]) == 0
    
    def test_state_can_store_advice_history(self):
        """状态应能存储中间建议历史"""
        state = create_react_initial_state("test-session", 1)
        advice = {
            "id": "adv-001",
            "title": "初步建议",
            "content": "保持皮肤清洁",
            "evidence": ["湿疹护理指南"],
            "timestamp": "2026-01-16T10:00:00"
        }
        state["advice_history"].append(advice)
        assert len(state["advice_history"]) == 1
        assert state["advice_history"][0]["title"] == "初步建议"
    
    def test_state_can_store_diagnosis_card(self):
        """状态应能存储诊断卡"""
        state = create_react_initial_state("test-session", 1)
        diagnosis_card = {
            "summary": "皮肤出现红疹，伴有瘙痒",
            "conditions": [
                {"name": "湿疹", "confidence": 0.8, "rationale": ["红疹", "瘙痒"]}
            ],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": ["保持清洁", "避免抓挠"]
        }
        state["diagnosis_card"] = diagnosis_card
        assert state["diagnosis_card"]["summary"] == "皮肤出现红疹，伴有瘙痒"
        assert len(state["diagnosis_card"]["conditions"]) == 1
    
    def test_state_can_store_reasoning_steps(self):
        """状态应能存储推理步骤"""
        state = create_react_initial_state("test-session", 1)
        steps = ["收集症状信息", "检索医学文献", "生成鉴别诊断"]
        state["reasoning_steps"] = steps
        assert len(state["reasoning_steps"]) == 3
        assert "检索医学文献" in state["reasoning_steps"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
