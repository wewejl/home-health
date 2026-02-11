"""
LLM Factory 单元测试

测试 LLM 工厂的所有方法：
- get_qwen_client() 单例模式
- create_llm() 创建配置
- 环境变量缺失错误处理
"""
import pytest
from unittest.mock import patch, MagicMock
import os

# 导入 LLM 工厂
try:
    from app.services.base.llm_factory import get_qwen_client, create_llm
except ImportError:
    from backend.app.services.base.llm_factory import get_qwen_client, create_llm


class TestGetQwenClient:
    """测试 Qwen 客户端获取"""

    @patch('app.services.base.llm_factory.OpenAI')
    def test_get_qwen_client_with_api_key(self, mock_openai):
        """测试有 API key 时创建客户端"""
        # 设置环境变量
        with patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'test_api_key_123'}):
            # 清除缓存以确保获取新实例
            get_qwen_client.cache_clear()

            client = get_qwen_client()

            # 验证 OpenAI 被正确调用
            mock_openai.assert_called_once_with(
                api_key='test_api_key_123',
                base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
            )
            assert client is not None

    @patch('app.services.base.llm_factory.OpenAI')
    def test_get_qwen_client_singleton(self, mock_openai):
        """测试单例模式 - 多次调用返回同一实例"""
        with patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'test_api_key'}):
            # 清除缓存
            get_qwen_client.cache_clear()

            client1 = get_qwen_client()
            client2 = get_qwen_client()

            # 应该是同一个实例
            assert client1 is client2
            # OpenAI 应该只被调用一次
            assert mock_openai.call_count == 1

    @patch.dict(os.environ, {}, clear=False)
    def test_get_qwen_client_missing_api_key(self):
        """测试缺少 API key 时抛出错误"""
        # 清除环境变量
        os.environ.pop('DASHSCOPE_API_KEY', None)
        # 清除缓存
        get_qwen_client.cache_clear()

        with pytest.raises(ValueError) as exc_info:
            get_qwen_client()

        assert "DASHSCOPE_API_KEY" in str(exc_info.value)


class TestCreateLLM:
    """测试 LLM 配置创建"""

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_create_llm_default_params(self, mock_get_client):
        """测试使用默认参数创建 LLM 配置"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm()

        assert config["model"] == "qwen-plus"
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 2000
        assert config["client"] == mock_client

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_create_llm_custom_params(self, mock_get_client):
        """测试使用自定义参数创建 LLM 配置"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm(
            model="qwen-turbo",
            temperature=0.5,
            max_tokens=1000
        )

        assert config["model"] == "qwen-turbo"
        assert config["temperature"] == 0.5
        assert config["max_tokens"] == 1000
        assert config["client"] == mock_client

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_create_llm_zero_temperature(self, mock_get_client):
        """测试零温度参数（确定性输出）"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm(temperature=0)

        assert config["temperature"] == 0

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_create_llm_high_max_tokens(self, mock_get_client):
        """测试高 token 限制"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm(max_tokens=8000)

        assert config["max_tokens"] == 8000


class TestLLMConfigStructure:
    """测试 LLM 配置结构"""

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_config_has_required_keys(self, mock_get_client):
        """测试配置包含所有必需的键"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm()

        required_keys = ["model", "temperature", "max_tokens", "client"]
        for key in required_keys:
            assert key in config, f"配置缺少必需的键: {key}"

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_config_values_are_correct_types(self, mock_get_client):
        """测试配置值是正确的类型"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm()

        assert isinstance(config["model"], str)
        assert isinstance(config["temperature"], (int, float))
        assert isinstance(config["max_tokens"], int)
        assert isinstance(config["client"], MagicMock)


class TestEdgeCases:
    """测试边界情况"""

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_negative_temperature(self, mock_get_client):
        """测试负温度参数（虽然不推荐，但不应该报错）"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm(temperature=-0.1)

        assert config["temperature"] == -0.1

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_very_high_temperature(self, mock_get_client):
        """测试极高温度参数"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm(temperature=2.0)

        assert config["temperature"] == 2.0

    @patch('app.services.base.llm_factory.get_qwen_client')
    def test_minimal_max_tokens(self, mock_get_client):
        """测试最小 token 限制"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        config = create_llm(max_tokens=1)

        assert config["max_tokens"] == 1
