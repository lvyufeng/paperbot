"""Tests for OpenAIClient."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestOpenAIClientInit:
    """Tests for OpenAIClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        mock_client = Mock()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.dict('sys.modules', {'openai': MagicMock()}):
                import sys
                sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

                # Need to reimport to pick up the mock
                import importlib
                import papergen.ai.openai_client as openai_module
                importlib.reload(openai_module)

                client = openai_module.OpenAIClient()

                assert client.provider == "openai"
                assert client.model == "gpt-4o"

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        mock_client = Mock()

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

            import importlib
            import papergen.ai.openai_client as openai_module
            importlib.reload(openai_module)

            client = openai_module.OpenAIClient(
                api_key="custom-key",
                model="gpt-3.5-turbo",
                base_url="https://custom.api.com",
                provider="custom"
            )

            assert client.api_key == "custom-key"
            assert client.model == "gpt-3.5-turbo"
            assert client.base_url == "https://custom.api.com"
            assert client.provider == "custom"


class TestOpenAIClientGenerate:
    """Tests for generate method."""

    @pytest.fixture
    def mock_openai_module(self):
        """Set up mock OpenAI module."""
        mock_client = Mock()

        # Set up response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

            import importlib
            import papergen.ai.openai_client as openai_module
            importlib.reload(openai_module)

            yield openai_module, mock_client

    def test_generate_basic(self, mock_openai_module):
        """Test basic generation."""
        openai_module, mock_client = mock_openai_module

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = openai_module.OpenAIClient()
            result = client.generate("Test prompt")

            assert result == "Generated response"
            mock_client.chat.completions.create.assert_called_once()

    def test_generate_with_system_prompt(self, mock_openai_module):
        """Test generation with system prompt."""
        openai_module, mock_client = mock_openai_module

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = openai_module.OpenAIClient()
            result = client.generate("Test prompt", system="You are helpful")

            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']

            assert messages[0]['role'] == 'system'
            assert messages[0]['content'] == 'You are helpful'

    def test_generate_with_context(self, mock_openai_module):
        """Test generation with context."""
        openai_module, mock_client = mock_openai_module

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = openai_module.OpenAIClient()
            context = {"topic": "AI", "sources": ["Source 1", "Source 2"]}
            result = client.generate("Test prompt", context=context)

            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']

            # Context should be in the message
            assert "Context:" in messages[0]['content']

    def test_generate_with_parameters(self, mock_openai_module):
        """Test generation with custom parameters."""
        openai_module, mock_client = mock_openai_module

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = openai_module.OpenAIClient()
            result = client.generate(
                "Test prompt",
                max_tokens=2000,
                temperature=0.5
            )

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs['max_tokens'] == 2000
            assert call_args.kwargs['temperature'] == 0.5

    def test_generate_api_error(self, mock_openai_module):
        """Test generation handles API errors."""
        openai_module, mock_client = mock_openai_module
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = openai_module.OpenAIClient()

            with pytest.raises(RuntimeError) as exc_info:
                client.generate("Test prompt")

            assert "API error" in str(exc_info.value)


class TestOpenAIClientFormatContext:
    """Tests for _format_context method."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        mock_client = Mock()

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

            import importlib
            import papergen.ai.openai_client as openai_module
            importlib.reload(openai_module)

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                return openai_module.OpenAIClient()

    def test_format_simple_context(self, client):
        """Test formatting simple context."""
        context = {"topic": "AI", "author": "Test"}

        result = client._format_context(context)

        assert "topic" in result.lower() or "AI" in result
        assert "author" in result.lower() or "Test" in result

    def test_format_dict_context(self, client):
        """Test formatting nested dict context."""
        context = {"metadata": {"title": "Paper Title", "year": "2024"}}

        result = client._format_context(context)

        assert "metadata" in result.lower()
        assert "title" in result.lower() or "Paper Title" in result

    def test_format_list_context(self, client):
        """Test formatting list context."""
        context = {"sources": ["Source 1", "Source 2", "Source 3"]}

        result = client._format_context(context)

        assert "Source 1" in result
        assert "Source 2" in result


class TestOpenAIClientHelpers:
    """Tests for helper methods."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        mock_client = Mock()

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

            import importlib
            import papergen.ai.openai_client as openai_module
            importlib.reload(openai_module)

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                return openai_module.OpenAIClient(provider="openai", model="gpt-4")

    def test_get_provider_name(self, client):
        """Test getting provider name."""
        result = client.get_provider_name()

        assert result == "openai"

    def test_get_model_name(self, client):
        """Test getting model name."""
        result = client.get_model_name()

        assert result == "gpt-4"


class TestOpenAIClientDefaultValues:
    """Tests for default value methods."""

    def test_default_models(self):
        """Test default models for different providers."""
        mock_client = Mock()

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

            import importlib
            import papergen.ai.openai_client as openai_module
            importlib.reload(openai_module)

            # Test different providers
            with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}):
                client = openai_module.OpenAIClient(provider="openai")
                assert client.model == "gpt-4o"

            with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}):
                client = openai_module.OpenAIClient(provider="gemini")
                assert client.model == "gemini-2.0-flash"

            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "key"}):
                client = openai_module.OpenAIClient(provider="deepseek")
                assert client.model == "deepseek-chat"

    def test_default_base_urls(self):
        """Test default base URLs for different providers."""
        mock_client = Mock()

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            sys.modules['openai'].OpenAI = Mock(return_value=mock_client)

            import importlib
            import papergen.ai.openai_client as openai_module
            importlib.reload(openai_module)

            with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}):
                client = openai_module.OpenAIClient(provider="openai")
                assert client.base_url is None

            with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}):
                client = openai_module.OpenAIClient(provider="gemini")
                assert "googleapis.com" in client.base_url

            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "key"}):
                client = openai_module.OpenAIClient(provider="deepseek")
                assert "deepseek.com" in client.base_url
