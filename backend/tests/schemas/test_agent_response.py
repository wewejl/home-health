import pytest
from app.schemas.agent_response import AgentResponse


def test_agent_response_minimal():
    """测试最小必填字段"""
    response = AgentResponse(
        message="测试消息",
        stage="greeting",
        progress=0
    )
    assert response.message == "测试消息"
    assert response.stage == "greeting"
    assert response.progress == 0
    assert response.quick_options == []
    assert response.specialty_data is None


def test_agent_response_with_specialty_data():
    """测试包含专科数据"""
    response = AgentResponse(
        message="诊断完成",
        stage="diagnosing",
        progress=80,
        specialty_data={
            "diagnosis_card": {
                "summary": "湿疹",
                "conditions": [{"name": "湿疹", "confidence": 0.85}]
            }
        }
    )
    assert response.specialty_data is not None
    assert "diagnosis_card" in response.specialty_data


def test_agent_response_validation():
    """测试字段验证"""
    with pytest.raises(ValueError):
        AgentResponse(
            message="测试",
            stage="invalid_stage",
            progress=150  # 超出范围
        )


def test_agent_response_with_next_state():
    """测试 next_state 字段"""
    response = AgentResponse(
        message="测试",
        stage="collecting",
        progress=40,
        next_state={
            "stage": "collecting",
            "symptoms": ["瘙痒", "红疹"],
            "questions_asked": 2
        }
    )
    assert response.next_state["symptoms"] == ["瘙痒", "红疹"]
    assert response.next_state["questions_asked"] == 2


def test_agent_response_all_fields():
    """测试所有字段"""
    response = AgentResponse(
        message="根据您的描述，可能是湿疹",
        stage="diagnosing",
        progress=80,
        quick_options=["继续描述", "上传照片", "生成病历"],
        risk_level="low",
        event_id="uuid-123",
        is_new_event=True,
        should_show_dossier_prompt=True,
        specialty_data={
            "diagnosis_card": {"summary": "湿疹"}
        },
        next_state={"stage": "diagnosing"}
    )
    assert response.risk_level == "low"
    assert response.event_id == "uuid-123"
    assert response.is_new_event is True
    assert response.should_show_dossier_prompt is True
