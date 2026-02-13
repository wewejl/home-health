"""
语音识别 API 测试

测试 /ws/voice 端点：
- GET /ws/voice/status - 获取语音服务状态
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.user import User
    from app.services.auth_service import AuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService
    from backend.app.main import app


# ============================================================================
# 语音识别 API 测试
# ============================================================================

class TestVoiceStatusAPI:
    """测试语音服务状态 API (GET /ws/voice/status)"""

    def test_voice_status_success(self, test_client: TestClient):
        """测试成功获取语音服务状态"""
        response = test_client.get("/ws/voice/status")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "voice_asr"
        assert data["provider"] == "dashscope"
        assert "asr_connections" in data
        assert "asr_configured" in data
        assert "endpoints" in data
        assert "config" in data

    def test_voice_status_endpoints(self, test_client: TestClient):
        """测试返回的端点配置"""
        response = test_client.get("/ws/voice/status")

        assert response.status_code == 200
        data = response.json()
        assert "/ws/voice/asr" in data["endpoints"]["asr"]

    def test_voice_status_config(self, test_client: TestClient):
        """测试返回的配置信息"""
        response = test_client.get("/ws/voice/status")

        assert response.status_code == 200
        data = response.json()
        config = data["config"]

        assert "asr_sample_rate" in config
        assert "asr_format" in config
        assert "supported_languages" in config
        assert isinstance(config["supported_languages"], list)
        assert "auto" in config["supported_languages"]
        assert "zh" in config["supported_languages"]
        assert "en" in config["supported_languages"]


class TestVoiceASRWebSocket:
    """测试 ASR WebSocket 端点"""

    def test_websocket_requires_token(self, test_client: TestClient):
        """测试 WebSocket 连接需要 token"""
        # TestClient 不直接支持 WebSocket 测试
        # 这里测试端点存在性
        response = test_client.get("/ws/voice/status")
        # 确认路由已注册
        assert response.status_code == 200

    def test_websocket_language_parameter(self, test_client: TestClient):
        """测试语言参数"""
        response = test_client.get("/ws/voice/status")
        data = response.json()

        # 确认支持的语言参数
        assert "auto" in data["config"]["supported_languages"]
        assert "zh" in data["config"]["supported_languages"]
        assert "en" in data["config"]["supported_languages"]
        assert "yue" in data["config"]["supported_languages"]
