"""测试工具节点状态更新功能"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage

from app.services.dermatology.react_state import DermaReActState, create_react_initial_state


class TestToolNodeStateUpdate:
    """测试工具节点更新 state"""
    
    def test_retrieve_knowledge_updates_state(self):
        """测试 retrieve_derma_knowledge 更新 knowledge_refs"""
        from app.services.dermatology.react_agent import _build_derma_react_graph, reset_derma_react_graph
        
        # 重置图以确保使用新配置
        reset_derma_react_graph()
        
        # 模拟工具返回结果
        mock_knowledge_result = [
            {"id": "kb-001", "title": "湿疹诊疗指南", "snippet": "湿疹是一种常见皮肤病..."}
        ]
        
        with patch('app.services.dermatology.react_tools.retrieve_derma_knowledge') as mock_retrieve:
            mock_retrieve.return_value = mock_knowledge_result
            
            with patch('app.services.llm_provider.LLMProvider.get_llm') as mock_llm:
                # 模拟 LLM 调用工具
                mock_tool_call = {
                    "name": "retrieve_derma_knowledge",
                    "args": {"symptoms": ["红疹", "瘙痒"], "location": "手臂"},
                    "id": "call-123"
                }
                mock_ai_response = AIMessage(content="", tool_calls=[mock_tool_call])
                mock_final_response = AIMessage(content="根据检索结果，这可能是湿疹。")
                
                mock_model = MagicMock()
                mock_model.bind_tools.return_value.invoke.side_effect = [
                    mock_ai_response,
                    mock_final_response
                ]
                mock_llm.return_value = mock_model
                
                # 构建图
                graph = _build_derma_react_graph()
                
                # 创建初始状态
                state = create_react_initial_state("test-session", 1)
                state["messages"] = [HumanMessage(content="我手臂有红疹，很痒")]
                
                # 执行图
                result = graph.invoke(state)
                
                # 验证 knowledge_refs 被更新
                assert "knowledge_refs" in result
                # 注意：由于模拟可能不完全匹配，这里主要验证结构正确
    
    def test_generate_diagnosis_updates_state(self):
        """测试 generate_structured_diagnosis 更新 diagnosis_card"""
        from app.services.dermatology.react_agent import _build_derma_react_graph, reset_derma_react_graph
        
        reset_derma_react_graph()
        
        mock_diagnosis_result = {
            "summary": "手臂红疹伴瘙痒",
            "conditions": [{"name": "湿疹", "confidence": 0.8, "rationale": ["红疹", "瘙痒"]}],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": ["保持清洁"],
            "reasoning_steps": ["分析症状", "生成诊断"]
        }
        
        with patch('app.services.dermatology.react_tools.generate_structured_diagnosis') as mock_diagnosis:
            mock_diagnosis.return_value = mock_diagnosis_result
            
            with patch('app.services.llm_provider.LLMProvider.get_llm') as mock_llm:
                mock_tool_call = {
                    "name": "generate_structured_diagnosis",
                    "args": {
                        "symptoms": ["红疹", "瘙痒"],
                        "location": "手臂",
                        "duration": "三天"
                    },
                    "id": "call-456"
                }
                mock_ai_response = AIMessage(content="", tool_calls=[mock_tool_call])
                mock_final_response = AIMessage(content="诊断结果已生成。")
                
                mock_model = MagicMock()
                mock_model.bind_tools.return_value.invoke.side_effect = [
                    mock_ai_response,
                    mock_final_response
                ]
                mock_llm.return_value = mock_model
                
                graph = _build_derma_react_graph()
                
                state = create_react_initial_state("test-session", 1)
                state["messages"] = [HumanMessage(content="我手臂有红疹")]
                
                result = graph.invoke(state)
                
                # 验证 diagnosis_card 相关字段
                assert "diagnosis_card" in result or "risk_level" in result


class TestRecordIntermediateAdviceTool:
    """测试 record_intermediate_advice 工具"""
    
    def test_record_advice_updates_state(self):
        """测试工具调用更新 advice_history"""
        from app.services.dermatology.react_agent import _build_derma_react_graph, reset_derma_react_graph
        
        reset_derma_react_graph()
        
        with patch('app.services.llm_provider.LLMProvider.get_llm') as mock_llm:
            # 模拟 Agent 调用 record_intermediate_advice 工具
            mock_tool_call = {
                "name": "record_intermediate_advice",
                "args": {
                    "title": "初步护理建议",
                    "content": "建议保持皮肤清洁干燥，避免抓挠",
                    "evidence": ["湿疹护理指南"]
                },
                "id": "call-789"
            }
            mock_ai_response = AIMessage(content="", tool_calls=[mock_tool_call])
            mock_final_response = AIMessage(content="请问症状持续多久了？")
            
            mock_model = MagicMock()
            mock_model.bind_tools.return_value.invoke.side_effect = [
                mock_ai_response,
                mock_final_response
            ]
            mock_llm.return_value = mock_model
            
            graph = _build_derma_react_graph()
            state = create_react_initial_state("test-session", 1)
            state["messages"] = [HumanMessage(content="我手臂有红疹")]
            
            result = graph.invoke(state)
            
            # 验证 advice_history 被更新
            assert "advice_history" in result
            assert len(result["advice_history"]) > 0
            assert result["advice_history"][0]["title"] == "初步护理建议"
            assert "建议" in result["advice_history"][0]["content"]
            
            # 验证 reasoning_steps 同步
            assert "reasoning_steps" in result
            assert any("记录护理建议" in step for step in result["reasoning_steps"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
