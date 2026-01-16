"""
测试 V2 统一会话接口

注意：这些测试需要数据库和认证，可能需要模拟或跳过
"""
import pytest
from app.services.agent_router_v2 import AgentRouterV2
from app.schemas.agent_response import AgentResponse


def test_agent_router_v2_get_dermatology():
    """测试获取皮肤科智能体"""
    agent = AgentRouterV2.get_agent("dermatology")
    assert agent is not None


def test_agent_router_v2_get_general():
    """测试获取通用智能体"""
    agent = AgentRouterV2.get_agent("general")
    assert agent is not None


@pytest.mark.asyncio
async def test_dermatology_agent_returns_agent_response():
    """测试皮肤科智能体返回 AgentResponse 格式"""
    agent = AgentRouterV2.get_agent("dermatology")
    response = await agent.run(
        state={},
        user_input="我手臂有红疹"
    )
    assert isinstance(response, AgentResponse)
    assert hasattr(response, 'message')
    assert hasattr(response, 'stage')
    assert hasattr(response, 'progress')
    assert hasattr(response, 'next_state')


@pytest.mark.asyncio
async def test_general_agent_returns_agent_response():
    """测试通用智能体返回 AgentResponse 格式"""
    agent = AgentRouterV2.get_agent("general")
    response = await agent.run(
        state={},
        user_input="你好"
    )
    assert isinstance(response, AgentResponse)
    assert response.message is not None
    assert response.stage in ['greeting', 'collecting', 'analyzing', 'diagnosing', 'completed']
