import pytest
from app.services.agent_router_v2 import AgentRouterV2
from app.services.base.base_agent_v2 import BaseAgentV2


def test_get_capabilities():
    """测试获取智能体能力配置"""
    caps = AgentRouterV2.get_capabilities("general")
    assert caps is not None
    assert "display_name" in caps
    assert "actions" in caps


def test_list_agents():
    """测试列出所有智能体"""
    agents = AgentRouterV2.list_agents()
    assert "general" in agents
    assert isinstance(agents["general"], dict)


def test_infer_agent_type():
    """测试科室推断"""
    assert AgentRouterV2.infer_agent_type("皮肤科") == "dermatology"
    assert AgentRouterV2.infer_agent_type("心内科") == "cardiology"
    assert AgentRouterV2.infer_agent_type("未知科室") == "general"


def test_get_agent_invalid():
    """测试获取不存在的智能体"""
    with pytest.raises(ValueError, match="未知智能体类型"):
        AgentRouterV2.get_agent("invalid_type")


def test_get_agent_general():
    """测试获取通用智能体"""
    agent = AgentRouterV2.get_agent("general")
    assert isinstance(agent, BaseAgentV2)


def test_is_valid_agent_type():
    """测试有效智能体类型检查"""
    assert AgentRouterV2.is_valid_agent_type("general") is True
    assert AgentRouterV2.is_valid_agent_type("invalid") is False
