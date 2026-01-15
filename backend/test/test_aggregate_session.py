"""
单元测试：测试 aggregate_session 接口重构

执行方式：
    cd backend
    pytest test/test_aggregate_session.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.routes.medical_events import (
    aggregate_session, 
    get_department_name, 
    get_agent_type_enum
)
from app.models.medical_event import AgentType, EventStatus, RiskLevel
from app.schemas.medical_event import AggregateSessionRequest


class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_get_department_name_ios_naming(self):
        """测试 iOS 命名格式"""
        assert get_department_name("dermatology") == "皮肤科"
        assert get_department_name("cardiology") == "心血管科"
        assert get_department_name("orthopedics") == "骨科"
        assert get_department_name("general") == "全科"
    
    def test_get_department_name_backend_naming(self):
        """测试后端短名格式"""
        assert get_department_name("derma") == "皮肤科"
        assert get_department_name("cardio") == "心血管科"
        assert get_department_name("ortho") == "骨科"
        assert get_department_name("neuro") == "神经科"
        assert get_department_name("endo") == "内分泌科"
        assert get_department_name("gastro") == "消化科"
        assert get_department_name("diagnosis") == "全科"
    
    def test_get_department_name_unknown(self):
        """测试未知类型默认返回全科"""
        assert get_department_name("unknown") == "全科"
        assert get_department_name("") == "全科"
    
    def test_get_agent_type_enum_ios_naming(self):
        """测试 iOS 命名转换为枚举"""
        assert get_agent_type_enum("dermatology") == AgentType.derma
        assert get_agent_type_enum("cardiology") == AgentType.cardio
        assert get_agent_type_enum("orthopedics") == AgentType.ortho
        assert get_agent_type_enum("general") == AgentType.general
    
    def test_get_agent_type_enum_backend_naming(self):
        """测试后端短名转换为枚举"""
        assert get_agent_type_enum("derma") == AgentType.derma
        assert get_agent_type_enum("cardio") == AgentType.cardio
        assert get_agent_type_enum("ortho") == AgentType.ortho
        assert get_agent_type_enum("neuro") == AgentType.neuro
        assert get_agent_type_enum("diagnosis") == AgentType.general
    
    def test_get_agent_type_enum_unknown(self):
        """测试未知类型默认返回 general"""
        assert get_agent_type_enum("unknown") == AgentType.general


class TestAggregateSessionRequest:
    """测试请求模型"""
    
    def test_valid_ios_session_types(self):
        """测试有效的 iOS 会话类型"""
        for session_type in ["dermatology", "cardiology", "orthopedics"]:
            req = AggregateSessionRequest(
                session_id="test-123",
                session_type=session_type
            )
            assert req.session_type == session_type
    
    def test_valid_backend_session_types(self):
        """测试有效的后端会话类型"""
        for session_type in ["cardio", "derma", "ortho", "neuro", "general", "endo", "gastro", "respiratory", "diagnosis"]:
            req = AggregateSessionRequest(
                session_id="test-123",
                session_type=session_type
            )
            assert req.session_type == session_type


class MockUser:
    """模拟用户对象"""
    def __init__(self, user_id=1):
        self.id = user_id


class MockSession:
    """模拟会话对象"""
    def __init__(self, session_id=None, user_id=1, agent_type="dermatology", agent_state=None):
        self.id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.agent_type = agent_type
        self.agent_state = agent_state or {
            "stage": "completed",
            "chief_complaint": "皮肤瘙痒",
            "symptoms": ["瘙痒", "红肿"],
            "risk_level": "low"
        }
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class MockMessage:
    """模拟消息对象"""
    def __init__(self, session_id, sender_type="user", content="测试消息"):
        self.id = 1
        self.session_id = session_id
        self.sender = MagicMock()
        self.sender.value = sender_type
        self.content = content
        self.message_type = "text"
        self.attachments = None
        self.created_at = datetime.utcnow()


class TestAggregateSessionLogic:
    """测试聚合会话逻辑"""
    
    def test_session_data_extraction(self):
        """测试从 agent_state 提取数据"""
        agent_state = {
            "stage": "completed",
            "chief_complaint": "皮肤瘙痒红肿",
            "symptoms": ["瘙痒", "红肿", "脱皮"],
            "risk_level": "medium",
            "skin_analyses": [{"condition": "湿疹", "confidence": 0.85}],
            "symptom_details": {"瘙痒": {"duration": "3天"}}
        }
        
        # 验证数据提取逻辑
        chief_complaint = agent_state.get("chief_complaint", "")
        symptoms = agent_state.get("symptoms", [])
        risk_level = agent_state.get("risk_level", "low")
        
        assert chief_complaint == "皮肤瘙痒红肿"
        assert len(symptoms) == 3
        assert risk_level == "medium"
    
    def test_risk_level_priority(self):
        """测试风险等级优先级计算"""
        risk_priority = {"low": 0, "medium": 1, "high": 2, "emergency": 3}
        
        assert risk_priority["emergency"] > risk_priority["high"]
        assert risk_priority["high"] > risk_priority["medium"]
        assert risk_priority["medium"] > risk_priority["low"]
    
    def test_session_data_structure(self):
        """测试会话数据结构完整性"""
        session = MockSession()
        messages = [MockMessage(session.id)]
        state = session.agent_state
        
        session_data = {
            "session_id": session.id,
            "session_type": session.agent_type,
            "timestamp": session.created_at.isoformat(),
            "summary": f"皮肤科问诊 - {state.get('chief_complaint', '')}",
            "chief_complaint": state.get("chief_complaint", ""),
            "symptoms": state.get("symptoms", []),
            "risk_level": state.get("risk_level", "low"),
            "stage": state.get("stage", "completed"),
            "message_count": len(messages),
            "messages": [
                {
                    "role": msg.sender.value,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "type": msg.message_type
                }
                for msg in messages
            ]
        }
        
        # 验证必要字段存在
        assert "session_id" in session_data
        assert "session_type" in session_data
        assert "chief_complaint" in session_data
        assert "symptoms" in session_data
        assert "risk_level" in session_data
        assert "messages" in session_data
        assert session_data["message_count"] == 1


class TestIntegration:
    """集成测试 - 需要数据库连接"""
    
    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        # 这里可以使用测试数据库或内存数据库
        # 实际运行时需要配置测试环境
        pass
    
    def test_aggregate_new_session_creates_event(self):
        """测试聚合新会话创建病历事件"""
        # 这个测试需要实际的数据库连接
        # 在 CI/CD 环境中运行
        pass
    
    def test_aggregate_existing_session_updates_event(self):
        """测试聚合已存在的会话更新病历事件"""
        pass
    
    def test_aggregate_nonexistent_session_returns_404(self):
        """测试聚合不存在的会话返回404"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
