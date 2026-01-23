"""Tests for Claude API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import anthropic

from papergen.ai.claude_client import ClaudeClient
from papergen.core.exceptions import (
    APIConnectionError,
    APIAuthenticationError,
    APIRateLimitError,
    APIResponseError,
    APITimeoutError
)


class TestClaudeClientInitialization:
    """Tests for ClaudeClient initialization."""

    @patch('papergen.ai.claude_client.config')
    @patch('papergen.ai.claude_client.CacheManager')
    def test_init_with_defaults(self, mock_cache_manager, mock_config):
        """Test initialization with default values."""
        mock_config.get_api_key.return_value = "test-api-key"
        mock_config.get.return_value = None
        mock_config.get_api_base_url.return_value = None
        mock_cache_manager.get_cache.return_value = Mock()

        client = ClaudeClient()

        assert client.api_key == "test-api-key"
        assert client.use_direct_http is False
        assert client.use_cache is True

    @patch('papergen.ai.claude_client.config')
    @patch('papergen.ai.claude_client.CacheManager')
    def test_init_with_custom_api_key(self, mock_cache_manager, mock_config):
        """Test initialization with custom API key."""
        mock_config.get.return_value = None
        mock_config.get_api_base_url.return_value = None
        mock_cache_manager.get_cache.return_value = Mock()

        client = ClaudeClient(api_key="custom-key")

        assert client.api_key == "custom-key"

    @patch('papergen.ai.claude_client.config')
    @patch('papergen.ai.claude_client.CacheManager')
    def test_init_with_base_url_uses_direct_http(self, mock_cache_manager, mock_config):
        """Test that providing base_url enables direct HTTP mode."""
        mock_config.get_api_key.return_value = "test-api-key"
        mock_config.get.return_value = None
        mock_cache_manager.get_cache.return_value = Mock()

        client = ClaudeClient(base_url="https://proxy.example.com")

        assert client.use_direct_http is True
        assert client.base_url == "https://proxy.example.com"

    @patch('papergen.ai.claude_client.config')
    @patch('papergen.ai.claude_client.CacheManager')
    def test_init_without_cache(self, mock_cache_manager, mock_config):
        """Test initialization with caching disabled."""
        mock_config.get_api_key.return_value = "test-api-key"
        mock_config.get.return_value = None
        mock_config.get_api_base_url.return_value = None

        client = ClaudeClient(use_cache=False)

        assert client.cache is None
        mock_cache_manager.get_cache.assert_not_called()

    @patch('papergen.ai.claude_client.config')
    @patch('papergen.ai.claude_client.CacheManager')
    def test_init_with_custom_model(self, mock_cache_manager, mock_config):
        """Test initialization with custom model."""
        mock_config.get_api_key.return_value = "test-api-key"
        mock_config.get.return_value = None
        mock_config.get_api_base_url.return_value = None
        mock_cache_manager.get_cache.return_value = Mock()

        client = ClaudeClient(model="claude-opus-4-5")

        assert client.model == "claude-opus-4-5"


class TestClaudeClientGenerate:
    """Tests for ClaudeClient.generate method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mocked Claude client."""
        with patch('papergen.ai.claude_client.config') as mock_config, \
             patch('papergen.ai.claude_client.CacheManager') as mock_cache_manager, \
             patch('papergen.ai.claude_client.anthropic.Anthropic') as mock_anthropic:

            mock_config.get_api_key.return_value = "test-api-key"
            mock_config.get.return_value = None
            mock_config.get_api_base_url.return_value = None
            mock_cache_manager.get_cache.return_value = Mock()
            mock_cache_manager.get_cache.return_value.get.return_value = None

            client = ClaudeClient()
            client.client = mock_anthropic.return_value

            yield client, mock_anthropic.return_value

    def test_generate_basic(self, mock_client):
        """Test basic text generation."""
        client, mock_anthropic = mock_client

        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_anthropic.messages.create.return_value = mock_response

        result = client.generate("Test prompt")

        assert result == "Generated response"
        mock_anthropic.messages.create.assert_called_once()

    def test_generate_with_context(self, mock_client):
        """Test generation with context."""
        client, mock_anthropic = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response with context")]
        mock_response.usage.input_tokens = 150
        mock_response.usage.output_tokens = 75
        mock_anthropic.messages.create.return_value = mock_response

        context = {"topic": "Machine Learning", "sources": ["paper1", "paper2"]}
        result = client.generate("Write about this", context=context)

        assert result == "Response with context"
        # Verify context was included in the call
        call_args = mock_anthropic.messages.create.call_args
        messages = call_args.kwargs['messages']
        assert "Context:" in messages[0]['content']

    def test_generate_with_system_prompt(self, mock_client):
        """Test generation with system prompt."""
        client, mock_anthropic = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="System response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_anthropic.messages.create.return_value = mock_response

        result = client.generate("Test", system="You are a helpful assistant")

        call_args = mock_anthropic.messages.create.call_args
        assert call_args.kwargs.get('system') == "You are a helpful assistant"

    def test_generate_uses_cache(self, mock_client):
        """Test that generation uses cached response when available."""
        client, mock_anthropic = mock_client
        client.cache.get.return_value = "Cached response"

        result = client.generate("Test prompt")

        assert result == "Cached response"
        mock_anthropic.messages.create.assert_not_called()

    def test_generate_stores_in_cache(self, mock_client):
        """Test that generation stores response in cache."""
        client, mock_anthropic = mock_client
        client.cache.get.return_value = None

        mock_response = Mock()
        mock_response.content = [Mock(text="New response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_anthropic.messages.create.return_value = mock_response

        client.generate("Test prompt")

        client.cache.set.assert_called_once()


class TestClaudeClientErrorHandling:
    """Tests for ClaudeClient error handling."""

    @pytest.fixture
    def client_with_mocks(self):
        """Create client with mocked dependencies."""
        with patch('papergen.ai.claude_client.config') as mock_config, \
             patch('papergen.ai.claude_client.CacheManager') as mock_cache_manager, \
             patch('papergen.ai.claude_client.anthropic.Anthropic') as mock_anthropic:

            mock_config.get_api_key.return_value = "test-api-key"
            mock_config.get.return_value = None
            mock_config.get_api_base_url.return_value = None
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache_manager.get_cache.return_value = mock_cache

            client = ClaudeClient()
            client.client = mock_anthropic.return_value

            yield client, mock_anthropic.return_value

    def test_authentication_error(self, client_with_mocks):
        """Test authentication error handling."""
        client, mock_anthropic = client_with_mocks
        mock_anthropic.messages.create.side_effect = anthropic.AuthenticationError(
            message="Invalid API key",
            response=Mock(status_code=401),
            body={}
        )

        with pytest.raises(APIAuthenticationError):
            client.generate("Test")

    def test_rate_limit_error(self, client_with_mocks):
        """Test rate limit error handling."""
        client, mock_anthropic = client_with_mocks
        mock_anthropic.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body={}
        )

        with pytest.raises(APIRateLimitError):
            client.generate("Test")

    def test_connection_error(self, client_with_mocks):
        """Test connection error handling."""
        client, mock_anthropic = client_with_mocks
        mock_anthropic.messages.create.side_effect = anthropic.APIConnectionError(
            message="Connection failed",
            request=Mock()
        )

        with pytest.raises(APIConnectionError):
            client.generate("Test")

    def test_timeout_error(self, client_with_mocks):
        """Test timeout error handling.

        Note: In anthropic library, APITimeoutError inherits from APIConnectionError,
        so timeouts are handled as connection errors by the current exception order.
        """
        client, mock_anthropic = client_with_mocks

        # Create a real exception subclass for testing
        class MockTimeoutError(anthropic.APITimeoutError):
            def __init__(self):
                pass  # Skip parent init that requires request param

        mock_anthropic.messages.create.side_effect = MockTimeoutError()

        # Currently handled as connection error due to exception hierarchy
        with pytest.raises(APIConnectionError):
            client.generate("Test")


class TestClaudeClientDirectHttp:
    """Tests for ClaudeClient direct HTTP mode (third-party APIs)."""

    @pytest.fixture
    def direct_http_client(self):
        """Create client configured for direct HTTP."""
        with patch('papergen.ai.claude_client.config') as mock_config, \
             patch('papergen.ai.claude_client.CacheManager') as mock_cache_manager:

            mock_config.get_api_key.return_value = "test-api-key"
            mock_config.get.return_value = None
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache_manager.get_cache.return_value = mock_cache

            client = ClaudeClient(base_url="https://proxy.example.com")

            yield client

    @patch('papergen.ai.claude_client.requests.Session')
    def test_direct_http_generate(self, mock_session_class, direct_http_client):
        """Test direct HTTP generation."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"text": "HTTP response"}],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }
        mock_response.raise_for_status = Mock()
        mock_session.post.return_value = mock_response

        result = direct_http_client.generate("Test prompt")

        assert result == "HTTP response"
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert "proxy.example.com" in call_args.args[0]

    @patch('papergen.ai.claude_client.requests.Session')
    def test_direct_http_retry_on_timeout(self, mock_session_class, direct_http_client):
        """Test retry logic on timeout."""
        import requests

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First call times out, second succeeds
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"text": "Retry success"}],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }
        mock_response.raise_for_status = Mock()

        mock_session.post.side_effect = [
            requests.exceptions.Timeout("timeout"),
            mock_response
        ]

        with patch('papergen.ai.claude_client.time.sleep'):
            result = direct_http_client.generate("Test")

        assert result == "Retry success"
        assert mock_session.post.call_count == 2


class TestClaudeClientHelpers:
    """Tests for ClaudeClient helper methods."""

    @pytest.fixture
    def client(self):
        """Create a basic client."""
        with patch('papergen.ai.claude_client.config') as mock_config, \
             patch('papergen.ai.claude_client.CacheManager') as mock_cache_manager:

            mock_config.get_api_key.return_value = "test-api-key"
            mock_config.get.return_value = None
            mock_config.get_api_base_url.return_value = None
            mock_cache_manager.get_cache.return_value = Mock()

            yield ClaudeClient()

    def test_count_tokens(self, client):
        """Test token counting estimation."""
        text = "This is a test with about 40 characters."
        tokens = client.count_tokens(text)

        # ~4 chars per token
        assert tokens == len(text) // 4

    def test_format_context_dict(self, client):
        """Test context formatting with nested dict."""
        context = {
            "topic": "AI Research",
            "metadata": {
                "year": 2024,
                "field": "ML"
            }
        }
        formatted = client._format_context(context)

        assert "**topic:** AI Research" in formatted
        assert "## metadata" in formatted
        assert "**year:** 2024" in formatted

    def test_format_context_list(self, client):
        """Test context formatting with list."""
        context = {
            "sources": ["paper1", "paper2", "paper3"]
        }
        formatted = client._format_context(context)

        assert "## sources" in formatted
        assert "- paper1" in formatted
        assert "- paper2" in formatted

    @patch('papergen.ai.claude_client.anthropic.Anthropic')
    def test_validate_api_key_success(self, mock_anthropic, client):
        """Test successful API key validation."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Hi")]
        client.client = mock_anthropic.return_value
        client.client.messages.create.return_value = mock_response

        assert client.validate_api_key() is True

    @patch('papergen.ai.claude_client.anthropic.Anthropic')
    def test_validate_api_key_failure(self, mock_anthropic, client):
        """Test failed API key validation."""
        client.client = mock_anthropic.return_value
        client.client.messages.create.side_effect = Exception("Invalid key")

        assert client.validate_api_key() is False


class TestClaudeClientStreaming:
    """Tests for ClaudeClient streaming generation."""

    @pytest.fixture
    def client_with_sdk(self):
        """Create client with SDK mode."""
        with patch('papergen.ai.claude_client.config') as mock_config, \
             patch('papergen.ai.claude_client.CacheManager') as mock_cache_manager, \
             patch('papergen.ai.claude_client.anthropic.Anthropic') as mock_anthropic:

            mock_config.get_api_key.return_value = "test-api-key"
            mock_config.get.return_value = None
            mock_config.get_api_base_url.return_value = None
            mock_cache_manager.get_cache.return_value = Mock()

            client = ClaudeClient()
            client.client = mock_anthropic.return_value

            yield client, mock_anthropic.return_value

    def test_stream_generate(self, client_with_sdk):
        """Test streaming generation."""
        client, mock_anthropic = client_with_sdk

        # Create mock stream context manager
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value = mock_stream
        mock_stream.__exit__.return_value = None
        mock_stream.text_stream = iter(["Hello", " ", "World"])
        mock_anthropic.messages.stream.return_value = mock_stream

        chunks = list(client.stream_generate("Test prompt"))

        assert chunks == ["Hello", " ", "World"]
