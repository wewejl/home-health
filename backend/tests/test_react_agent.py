"""
ReAct Agent 测试

测试 ReAct 架构的核心功能
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.agents.react_base import ReActAgent, create_react_initial_state, ReActAgentState
from app.services.agents.dermatology.react_agent import DermatologyReActAgent, create_dermatology_react_state
from app.services.agents.tools import (
    search_medical_knowledge,
    assess_risk,
    search_medication,
    TOOL_REGISTRY
)
from app.services.agents.router import AgentRouter


class TestTools:
    """测试工具函数"""
    
    @pytest.mark.asyncio
    async def test_search_medical_knowledge_found(self):
        """测试医学知识查询 - 找到结果"""
        result = await search_medical_knowledge("湿疹的症状", "dermatology")
        
        assert result["found"] is True
        assert len(result["results"]) > 0
        assert "湿疹" in result["results"][0]
    
    @pytest.mark.asyncio
    async def test_search_medical_knowledge_not_found(self):
        """测试医学知识查询 - 未找到"""
        result = await search_medical_knowledge("不存在的疾病xyz", "dermatology")
        
        assert result["found"] is False
    
    @pytest.mark.asyncio
    async def test_assess_risk_low(self):
        """测试风险评估 - 低风险"""
        result = await assess_risk(
            symptoms=["轻微瘙痒"],
            patient_info={"age": 30},
            specialty="dermatology"
        )
        
        assert result["risk_level"] in ["low", "medium"]
        assert "score" in result
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_assess_risk_emergency(self):
        """测试风险评估 - 紧急"""
        result = await assess_risk(
            symptoms=["呼吸困难", "喉头水肿", "全身红斑"],
            patient_info={"age": 30},
            specialty="dermatology"
        )
        
        assert result["risk_level"] in ["high", "emergency"]
        assert result["score"] >= 60
    
    @pytest.mark.asyncio
    async def test_search_medication(self):
        """测试药物查询"""
        result = await search_medication(
            condition="湿疹",
            severity="mild"
        )
        
        assert result["found"] is True
        assert "medications" in result
        assert "disclaimer" in result


class TestDermatologyReActAgent:
    """测试皮肤科 ReAct 智能体"""
    
    def test_agent_creation(self):
        """测试智能体创建"""
        agent = DermatologyReActAgent()
        
        assert agent is not None
        assert "search_medical_knowledge" in agent.get_tools()
        assert "analyze_skin_image" in agent.get_tools()
    
    def test_get_system_prompt(self):
        """测试系统提示词"""
        agent = DermatologyReActAgent()
        prompt = agent.get_system_prompt()
        
        assert "皮肤科" in prompt
        assert "问诊要点" in prompt
        assert "工具" in prompt
    
    def test_get_capabilities(self):
        """测试能力配置"""
        agent = DermatologyReActAgent()
        caps = agent.get_capabilities()
        
        assert "actions" in caps
        assert "accepts_media" in caps
        assert "version" in caps
        assert "react" in caps["version"]
    
    def test_initial_state_creation(self):
        """测试初始状态创建"""
        state = create_dermatology_react_state("test-session", 1)
        
        assert state["session_id"] == "test-session"
        assert state["user_id"] == 1
        assert state["agent_type"] == "dermatology_react"
        assert state["stage"] == "greeting"
        assert state["progress"] == 0
        assert "medical_context" in state
        assert "symptoms" in state["medical_context"]


class TestAgentRouter:
    """测试智能体路由器"""
    
    def test_get_dermatology_agent(self):
        """测试获取皮肤科智能体"""
        AgentRouter.reset()
        agent = AgentRouter.get_agent("dermatology")
        
        assert agent is not None
        assert isinstance(agent, DermatologyReActAgent)
    
    def test_get_legacy_agent(self):
        """测试获取旧版智能体"""
        AgentRouter.reset()
        agent = AgentRouter.get_agent("dermatology_legacy")
        
        assert agent is not None
        # 应该是旧版的 DermatologyAgent
        assert agent.__class__.__name__ == "DermatologyAgent"
    
    def test_infer_agent_type(self):
        """测试科室名称推断"""
        assert AgentRouter.infer_agent_type("皮肤科") == "dermatology"
        assert AgentRouter.infer_agent_type("心血管内科") == "cardiology"
        assert AgentRouter.infer_agent_type("骨科") == "orthopedics"
        assert AgentRouter.infer_agent_type("未知科室") == "general"
    
    def test_list_agents(self):
        """测试列出所有智能体"""
        AgentRouter.reset()
        agents = AgentRouter.list_agents()
        
        assert "dermatology" in agents
        assert "dermatology_legacy" in agents
        assert "general" in agents
        assert "cardiology" in agents


class TestReActAgentIntegration:
    """ReAct 智能体集成测试"""
    
    @pytest.mark.asyncio
    async def test_agent_run_basic(self):
        """测试基本运行流程（需要 mock LLM）"""
        agent = DermatologyReActAgent()
        state = create_dermatology_react_state("test-session", 1)
        
        # Mock LLM 响应
        mock_response = {
            "content": """```json
{
  "thought": "用户首次咨询，需要了解症状",
  "action": "respond",
  "response": "您好，我是皮肤科AI医生。请问您有什么皮肤问题需要咨询？",
  "quick_options": ["皮肤瘙痒", "长了疹子", "皮肤变色"],
  "stage": "collecting",
  "progress": 10
}
```""",
            "tool_calls": [],
            "finish_reason": "stop"
        }
        
        with patch('app.services.agents.react_base.QwenService.chat_with_tools', 
                   new_callable=AsyncMock, return_value=mock_response):
            response = await agent.run(state, user_input="你好")
        
        assert response is not None
        assert response.message != ""
        assert response.stage in ["greeting", "collecting", "diagnosing", "completed"]


class TestToolRegistry:
    """测试工具注册表"""
    
    def test_tool_registry_completeness(self):
        """测试工具注册表完整性"""
        expected_tools = [
            "search_medical_knowledge",
            "assess_risk",
            "analyze_skin_image",
            "generate_medical_dossier",
            "search_medication"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in TOOL_REGISTRY, f"工具 {tool_name} 未注册"
            assert callable(TOOL_REGISTRY[tool_name]), f"工具 {tool_name} 不可调用"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
