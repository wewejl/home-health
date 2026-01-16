"""
测试 generate_structured_diagnosis 工具

验证结构化诊断输出功能
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.dermatology.react_tools import generate_structured_diagnosis


class TestGenerateStructuredDiagnosis:
    """测试 generate_structured_diagnosis 工具"""
    
    @patch('app.services.dermatology.react_tools.LLMProvider')
    def test_returns_diagnosis_card_structure(self, mock_llm_provider):
        """应返回诊断卡结构"""
        # Mock LLM 响应
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_llm_provider.get_llm.return_value = mock_llm
        
        mock_response = MagicMock()
        mock_response.summary = "手臂出现红疹"
        mock_response.conditions = [
            {"name": "湿疹", "confidence": 0.8, "rationale": ["红疹", "瘙痒"]}
        ]
        mock_response.risk_level = "low"
        mock_response.need_offline_visit = False
        mock_response.care_plan = ["保持清洁"]
        mock_response.reasoning_steps = ["收集症状", "分析特征"]
        mock_response.model_dump.return_value = {
            "summary": "手臂出现红疹",
            "conditions": [{"name": "湿疹", "confidence": 0.8, "rationale": ["红疹", "瘙痒"]}],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": ["保持清洁"],
            "reasoning_steps": ["收集症状", "分析特征"]
        }
        mock_structured_llm.invoke.return_value = mock_response
        
        result = generate_structured_diagnosis.invoke({
            "symptoms": ["红疹", "瘙痒"],
            "location": "手臂",
            "duration": "三天"
        })
        
        assert "summary" in result
        assert "conditions" in result
        assert "risk_level" in result
    
    @patch('app.services.dermatology.react_tools.LLMProvider')
    def test_includes_knowledge_refs(self, mock_llm_provider):
        """应能包含知识引用"""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_llm_provider.get_llm.return_value = mock_llm
        
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "summary": "诊断总结",
            "conditions": [],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": [],
            "reasoning_steps": []
        }
        mock_structured_llm.invoke.return_value = mock_response
        
        knowledge_refs = [
            {"id": "ref-001", "title": "湿疹指南", "snippet": "..."}
        ]
        
        result = generate_structured_diagnosis.invoke({
            "symptoms": ["红疹"],
            "location": "手臂",
            "duration": "一周",
            "knowledge_refs": knowledge_refs
        })
        
        assert isinstance(result, dict)
    
    @patch('app.services.dermatology.react_tools.LLMProvider')
    def test_handles_empty_symptoms(self, mock_llm_provider):
        """应能处理空症状"""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_llm_provider.get_llm.return_value = mock_llm
        
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "summary": "信息不足",
            "conditions": [],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": [],
            "reasoning_steps": []
        }
        mock_structured_llm.invoke.return_value = mock_response
        
        result = generate_structured_diagnosis.invoke({
            "symptoms": [],
            "location": "",
            "duration": ""
        })
        
        assert isinstance(result, dict)
        assert "summary" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
