import pytest
from app.services.base.base_agent_v2 import BaseAgentV2
from app.schemas.agent_response import AgentResponse


class MockAgent(BaseAgentV2):
    """测试用的 Mock 智能体"""
    
    async def run(self, state, user_input, attachments=None, action="conversation", on_chunk=None):
        return AgentResponse(
            message="Mock response",
            stage="greeting",
            progress=0,
            next_state={"test": "state"}
        )


@pytest.mark.asyncio
async def test_base_agent_run():
    """测试基类 run 方法"""
    agent = MockAgent()
    response = await agent.run(
        state={},
        user_input="测试输入"
    )
    assert isinstance(response, AgentResponse)
    assert response.message == "Mock response"
    assert response.next_state == {"test": "state"}


@pytest.mark.asyncio
async def test_base_agent_abstract():
    """测试基类不能直接实例化"""
    with pytest.raises(TypeError):
        BaseAgentV2()


@pytest.mark.asyncio
async def test_base_agent_with_attachments():
    """测试带附件的调用"""
    agent = MockAgent()
    response = await agent.run(
        state={"stage": "collecting"},
        user_input="看看这张图片",
        attachments=[{"type": "image", "base64": "abc123"}],
        action="analyze_skin"
    )
    assert isinstance(response, AgentResponse)


@pytest.mark.asyncio
async def test_base_agent_with_callback():
    """测试带回调的调用"""
    chunks = []
    
    async def on_chunk(chunk):
        chunks.append(chunk)
    
    agent = MockAgent()
    response = await agent.run(
        state={},
        user_input="测试",
        on_chunk=on_chunk
    )
    assert isinstance(response, AgentResponse)
