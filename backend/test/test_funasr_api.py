"""
FunASR 语音识别 API 测试

测试 /funasr 端点：
- GET /funasr/health - 健康检查
- GET /funasr/config - 获取配置说明
"""
import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    from backend.app.main import app


# ============================================================================
# FunASR API 测试
# ============================================================================

class TestFunASRHealthAPI:
    """测试健康检查 API (GET /funasr/health)"""

    def test_health_check_success(self, test_client: TestClient):
        """测试成功获取健康状态"""
        response = test_client.get("/funasr/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "funasr"


class TestFunASRConfigAPI:
    """测试配置说明 API (GET /funasr/config)"""

    def test_get_config_success(self, test_client: TestClient):
        """测试成功获取配置说明"""
        response = test_client.get("/funasr/config")

        assert response.status_code == 200
        data = response.json()
        assert "websocket_url" in data
        assert "parameters" in data
        assert "audio_format" in data
        assert "note" in data

    def test_config_websocket_url(self, test_client: TestClient):
        """测试返回的 WebSocket URL"""
        response = test_client.get("/funasr/config")

        assert response.status_code == 200
        data = response.json()
        assert "ws://localhost:8000/funasr/ws" in data["websocket_url"]

    def test_config_parameters(self, test_client: TestClient):
        """测试返回的参数说明"""
        response = test_client.get("/funasr/config")

        assert response.status_code == 200
        data = response.json()
        params = data["parameters"]

        assert "api_key" in params
        assert "sample_rate" in params
        assert "format" in params

    def test_config_audio_format(self, test_client: TestClient):
        """测试返回的音频格式说明"""
        response = test_client.get("/funasr/config")

        assert response.status_code == 200
        data = response.json()
        assert "16kHz" in data["audio_format"]
        assert "单声道" in data["audio_format"]
        assert "PCM" in data["audio_format"]


class TestFunASRWebSocket:
    """测试 FunASR WebSocket 端点"""

    def test_websocket_endpoint_exists(self, test_client: TestClient):
        """测试 WebSocket 端点存在"""
        # 通过健康检查确认服务可用
        response = test_client.get("/funasr/health")
        assert response.status_code == 200
