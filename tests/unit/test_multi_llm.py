"""Tests for MultiLLMManager."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from papergen.ai.multi_llm import LLMConfig, LLMResponse, MultiLLMManager


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = LLMConfig(provider="openai", model="gpt-4")

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key is None
        assert config.base_url is None
        assert config.enabled is True

    def test_custom_values(self):
        """Test custom values."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3",
            api_key="test-key",
            base_url="https://custom.url",
            enabled=False
        )

        assert config.provider == "anthropic"
        assert config.model == "claude-3"
        assert config.api_key == "test-key"
        assert config.base_url == "https://custom.url"
        assert config.enabled is False


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_success_response(self):
        """Test successful response."""
        response = LLMResponse(
            provider="openai",
            model="gpt-4",
            content="Generated text",
            success=True
        )

        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert response.content == "Generated text"
        assert response.success is True
        assert response.error is None

    def test_error_response(self):
        """Test error response."""
        response = LLMResponse(
            provider="anthropic",
            model="claude-3",
            content="",
            success=False,
            error="API Error"
        )

        assert response.success is False
        assert response.error == "API Error"
        assert response.content == ""


class TestMultiLLMManagerInit:
    """Tests for MultiLLMManager initialization."""

    def test_init(self):
        """Test initialization."""
        manager = MultiLLMManager()

        assert manager.llm_configs == []
        assert manager._clients == {}


class TestMultiLLMManagerAddLLM:
    """Tests for add_llm method."""

    def test_add_enabled_llm(self):
        """Test adding enabled LLM."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="openai", model="gpt-4", enabled=True)

        manager.add_llm(config)

        assert len(manager.llm_configs) == 1
        assert manager.llm_configs[0] == config

    def test_add_disabled_llm(self):
        """Test adding disabled LLM."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="openai", model="gpt-4", enabled=False)

        manager.add_llm(config)

        assert len(manager.llm_configs) == 0

    def test_add_multiple_llms(self):
        """Test adding multiple LLMs."""
        manager = MultiLLMManager()
        config1 = LLMConfig(provider="openai", model="gpt-4")
        config2 = LLMConfig(provider="anthropic", model="claude-3")

        manager.add_llm(config1)
        manager.add_llm(config2)

        assert len(manager.llm_configs) == 2


class TestMultiLLMManagerGetClient:
    """Tests for _get_client method."""

    def test_get_anthropic_client(self):
        """Test getting Anthropic client."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="anthropic", model="claude-3", api_key="test")

        mock_client = Mock()
        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client):
            client = manager._get_client(config)

            assert client == mock_client
            assert "anthropic_claude-3" in manager._clients

    def test_get_openai_client(self):
        """Test getting OpenAI client."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="openai", model="gpt-4", api_key="test")

        mock_client = Mock()
        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=Mock())

            with patch('papergen.ai.openai_client.OpenAIClient', return_value=mock_client):
                client = manager._get_client(config)

                assert client == mock_client
                assert "openai_gpt-4" in manager._clients

    def test_get_cached_client(self):
        """Test getting cached client."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="anthropic", model="claude-3", api_key="test")

        mock_client = Mock()
        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client) as mock_class:
            # First call creates client
            client1 = manager._get_client(config)
            # Second call returns cached
            client2 = manager._get_client(config)

            assert client1 == client2
            mock_class.assert_called_once()


class TestMultiLLMManagerGenerateSingle:
    """Tests for _generate_single method."""

    def test_generate_single_success(self):
        """Test successful single generation."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="anthropic", model="claude-3", api_key="test")

        mock_client = Mock()
        mock_client.generate.return_value = "Generated content"

        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client):
            response = manager._generate_single(
                config,
                prompt="Test prompt",
                system="System message"
            )

            assert response.success is True
            assert response.content == "Generated content"
            assert response.provider == "anthropic"
            assert response.model == "claude-3"

    def test_generate_single_error(self):
        """Test single generation with error."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="anthropic", model="claude-3", api_key="test")

        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")

        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client):
            response = manager._generate_single(config, prompt="Test")

            assert response.success is False
            assert response.error == "API Error"
            assert response.content == ""


class TestMultiLLMManagerGenerateParallel:
    """Tests for generate_parallel method."""

    def test_generate_parallel_no_llms(self):
        """Test parallel generation with no LLMs configured."""
        manager = MultiLLMManager()

        with pytest.raises(ValueError, match="No LLMs configured"):
            manager.generate_parallel("Test prompt")

    def test_generate_parallel_single_llm(self):
        """Test parallel generation with single LLM."""
        manager = MultiLLMManager()
        config = LLMConfig(provider="anthropic", model="claude-3", api_key="test")
        manager.add_llm(config)

        mock_client = Mock()
        mock_client.generate.return_value = "Generated"

        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client):
            responses = manager.generate_parallel("Test prompt")

            assert len(responses) == 1
            assert responses[0].success is True

    def test_generate_parallel_multiple_llms(self):
        """Test parallel generation with multiple LLMs."""
        manager = MultiLLMManager()
        manager.add_llm(LLMConfig(provider="anthropic", model="claude-3", api_key="test1"))
        manager.add_llm(LLMConfig(provider="anthropic", model="claude-2", api_key="test2"))

        mock_client = Mock()
        mock_client.generate.return_value = "Claude response"

        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client):
            responses = manager.generate_parallel("Test prompt")

            assert len(responses) == 2
            # All should succeed
            assert all(r.success for r in responses)


class TestMultiLLMManagerFromEnv:
    """Tests for from_env class method."""

    def test_from_env_no_keys(self):
        """Test from_env with no API keys."""
        with patch.dict(os.environ, {}, clear=True):
            manager = MultiLLMManager.from_env()

            assert len(manager.llm_configs) == 0

    def test_from_env_anthropic_only(self):
        """Test from_env with Anthropic key only."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            manager = MultiLLMManager.from_env()

            assert len(manager.llm_configs) == 1
            assert manager.llm_configs[0].provider == "anthropic"

    def test_from_env_openai_only(self):
        """Test from_env with OpenAI key only."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            manager = MultiLLMManager.from_env()

            assert len(manager.llm_configs) == 1
            assert manager.llm_configs[0].provider == "openai"

    def test_from_env_gemini_only(self):
        """Test from_env with Gemini key only."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
            manager = MultiLLMManager.from_env()

            assert len(manager.llm_configs) == 1
            assert manager.llm_configs[0].provider == "gemini"

    def test_from_env_multiple_keys(self):
        """Test from_env with multiple API keys."""
        env = {
            "ANTHROPIC_API_KEY": "anthropic-key",
            "OPENAI_API_KEY": "openai-key",
            "GEMINI_API_KEY": "gemini-key"
        }
        with patch.dict(os.environ, env, clear=True):
            manager = MultiLLMManager.from_env()

            assert len(manager.llm_configs) == 3
            providers = {c.provider for c in manager.llm_configs}
            assert providers == {"anthropic", "openai", "gemini"}

    def test_from_env_custom_models(self):
        """Test from_env with custom model names."""
        env = {
            "ANTHROPIC_API_KEY": "key",
            "ANTHROPIC_MODEL": "claude-opus",
            "OPENAI_API_KEY": "key",
            "OPENAI_MODEL": "gpt-4-turbo"
        }
        with patch.dict(os.environ, env, clear=True):
            manager = MultiLLMManager.from_env()

            anthropic_config = next(c for c in manager.llm_configs if c.provider == "anthropic")
            openai_config = next(c for c in manager.llm_configs if c.provider == "openai")

            assert anthropic_config.model == "claude-opus"
            assert openai_config.model == "gpt-4-turbo"

    def test_from_env_with_base_url(self):
        """Test from_env with custom base URL."""
        env = {
            "ANTHROPIC_API_KEY": "key",
            "ANTHROPIC_BASE_URL": "https://custom.api.com"
        }
        with patch.dict(os.environ, env, clear=True):
            manager = MultiLLMManager.from_env()

            assert manager.llm_configs[0].base_url == "https://custom.api.com"
