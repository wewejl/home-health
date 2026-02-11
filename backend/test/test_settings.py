"""
配置管理测试
"""
import pytest
import os
from backend.app.config import Settings, get_settings, reset_settings


class TestSettings:
    """配置管理测试"""

    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        assert settings.APP_NAME == "灵犀健康 API"
        assert settings.PORT == 8100
        assert settings.DEBUG is True

    def test_get_settings_singleton(self):
        """测试单例模式"""
        reset_settings()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reset_settings(self):
        """测试重置配置"""
        reset_settings()
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        assert settings1 is not settings2

    def test_cors_origins_list_debug(self):
        """测试开发环境 CORS 配置"""
        settings = Settings(DEBUG=True)
        origins = settings.cors_origins_list
        assert "http://localhost:8150" in origins
        assert "http://localhost:5173" in origins

    def test_cors_origins_list_production(self):
        """测试生产环境 CORS 配置"""
        settings = Settings(DEBUG=False, CORS_ALLOWED_ORIGINS="")
        origins = settings.cors_origins_list
        assert origins == []

    def test_is_production(self):
        """测试生产环境判断"""
        settings_debug = Settings(DEBUG=True)
        assert settings_debug.is_production is False

        settings_prod = Settings(DEBUG=False)
        assert settings_prod.is_production is True
