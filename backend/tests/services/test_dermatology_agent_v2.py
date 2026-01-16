import pytest
from app.services.dermatology.agent_v2 import DermatologyAgentV2
from app.schemas.agent_response import AgentResponse


@pytest.mark.asyncio
async def test_dermatology_agent_greeting():
    """测试初次问候"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={},
        user_input="你好"
    )
    assert isinstance(response, AgentResponse)
    assert response.stage == "greeting"
    assert response.progress >= 0


@pytest.mark.asyncio
async def test_dermatology_agent_collecting():
    """测试症状收集"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={"stage": "greeting", "symptoms": []},
        user_input="我手臂有红疹，很痒"
    )
    assert response.stage in ["collecting", "diagnosing"]
    assert response.next_state.get("symptoms") is not None


@pytest.mark.asyncio
async def test_dermatology_agent_specialty_data():
    """测试专科数据返回"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={"stage": "diagnosing", "symptoms": ["红疹", "瘙痒", "脱皮"]},
        user_input="症状持续3天了"
    )
    # 当症状足够时应该返回诊断卡
    if response.stage == "diagnosing":
        assert response.specialty_data is not None


@pytest.mark.asyncio
async def test_dermatology_agent_symptom_extraction():
    """测试症状提取"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={},
        user_input="皮肤很痒，有红疹，还有点肿"
    )
    symptoms = response.next_state.get("symptoms", [])
    assert len(symptoms) > 0


@pytest.mark.asyncio
async def test_dermatology_agent_quick_options():
    """测试快捷选项"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={"stage": "diagnosing", "symptoms": ["红疹", "瘙痒", "脱皮"]},
        user_input="还有什么需要了解的吗"
    )
    assert len(response.quick_options) > 0
    assert "上传照片" in response.quick_options or "继续描述" in response.quick_options
