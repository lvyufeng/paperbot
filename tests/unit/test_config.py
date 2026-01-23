"""Tests for configuration management."""

import pytest
from unittest.mock import patch, mock_open, Mock
from pathlib import Path
import os

from papergen.core.config import Config


class TestConfigSingleton:
    """Tests for Config singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Test that Config is a singleton."""
        # Reset singleton for test
        Config._instance = None

        with patch.object(Config, '_load_config'):
            config1 = Config()
            config2 = Config()

        assert config1 is config2

    def test_singleton_initializes_once(self):
        """Test that _load_config is only called once."""
        Config._instance = None

        with patch.object(Config, '_load_config') as mock_load:
            Config()
            Config()
            Config()

        assert mock_load.call_count == 1


class TestConfigGet:
    """Tests for Config.get method."""

    @pytest.fixture
    def config(self):
        """Create a config instance with test data."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {
                'api': {
                    'model': 'claude-sonnet-4-5',
                    'temperature': 0.7,
                    'nested': {
                        'deep_value': 'found'
                    }
                },
                'content': {
                    'citation_style': 'apa'
                }
            }
            yield conf

    def test_get_simple_key(self, config):
        """Test getting a top-level key."""
        assert config.get('api') == {
            'model': 'claude-sonnet-4-5',
            'temperature': 0.7,
            'nested': {'deep_value': 'found'}
        }

    def test_get_nested_key(self, config):
        """Test getting a nested key with dot notation."""
        assert config.get('api.model') == 'claude-sonnet-4-5'
        assert config.get('api.temperature') == 0.7

    def test_get_deeply_nested_key(self, config):
        """Test getting deeply nested keys."""
        assert config.get('api.nested.deep_value') == 'found'

    def test_get_missing_key_returns_default(self, config):
        """Test that missing keys return the default value."""
        assert config.get('missing.key', 'default') == 'default'
        assert config.get('api.missing', 42) == 42

    def test_get_missing_key_returns_none(self, config):
        """Test that missing keys return None when no default."""
        assert config.get('nonexistent') is None
        assert config.get('api.nonexistent.deep') is None


class TestConfigSet:
    """Tests for Config.set method."""

    @pytest.fixture
    def config(self):
        """Create a fresh config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {}
            yield conf

    def test_set_simple_key(self, config):
        """Test setting a simple key."""
        config.set('model', 'claude-opus')
        assert config._config['model'] == 'claude-opus'

    def test_set_nested_key(self, config):
        """Test setting a nested key creates intermediate dicts."""
        config.set('api.model', 'claude-sonnet')

        assert config._config['api']['model'] == 'claude-sonnet'

    def test_set_deeply_nested_key(self, config):
        """Test setting deeply nested keys."""
        config.set('api.nested.deep.value', 'test')

        assert config._config['api']['nested']['deep']['value'] == 'test'

    def test_set_overwrites_existing(self, config):
        """Test that set overwrites existing values."""
        config.set('key', 'original')
        config.set('key', 'updated')

        assert config.get('key') == 'updated'


class TestConfigApiKey:
    """Tests for Config.get_api_key method."""

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            yield Config()

    def test_get_api_key_from_anthropic_api_key(self, config):
        """Test getting API key from ANTHROPIC_API_KEY env var."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'}, clear=True):
            assert config.get_api_key() == 'test-key-123'

    def test_get_api_key_from_auth_token(self, config):
        """Test getting API key from ANTHROPIC_AUTH_TOKEN env var."""
        with patch.dict(os.environ, {'ANTHROPIC_AUTH_TOKEN': 'auth-token-456'}, clear=True):
            assert config.get_api_key() == 'auth-token-456'

    def test_get_api_key_prefers_api_key(self, config):
        """Test that ANTHROPIC_API_KEY takes precedence."""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'api-key',
            'ANTHROPIC_AUTH_TOKEN': 'auth-token'
        }, clear=True):
            assert config.get_api_key() == 'api-key'

    def test_get_api_key_raises_when_missing(self, config):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove both possible env vars
            os.environ.pop('ANTHROPIC_API_KEY', None)
            os.environ.pop('ANTHROPIC_AUTH_TOKEN', None)

            with pytest.raises(ValueError) as exc_info:
                config.get_api_key()

            assert "ANTHROPIC_API_KEY" in str(exc_info.value)


class TestConfigBaseUrl:
    """Tests for Config.get_api_base_url method."""

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {}
            yield conf

    def test_get_base_url_from_env(self, config):
        """Test getting base URL from environment variable."""
        with patch.dict(os.environ, {'ANTHROPIC_BASE_URL': 'https://proxy.example.com'}):
            assert config.get_api_base_url() == 'https://proxy.example.com'

    def test_get_base_url_from_config(self, config):
        """Test getting base URL from config file."""
        config._config = {'api': {'base_url': 'https://config.example.com'}}

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ANTHROPIC_BASE_URL', None)
            assert config.get_api_base_url() == 'https://config.example.com'

    def test_get_base_url_env_takes_precedence(self, config):
        """Test that environment variable takes precedence over config."""
        config._config = {'api': {'base_url': 'https://config.example.com'}}

        with patch.dict(os.environ, {'ANTHROPIC_BASE_URL': 'https://env.example.com'}):
            assert config.get_api_base_url() == 'https://env.example.com'

    def test_get_base_url_returns_none_when_not_configured(self, config):
        """Test that None is returned when no base URL configured."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ANTHROPIC_BASE_URL', None)
            assert config.get_api_base_url() is None


class TestConfigApiConfig:
    """Tests for Config.get_api_config method."""

    @pytest.fixture
    def config(self):
        """Create a config instance with API settings."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {
                'api': {
                    'provider': 'anthropic',
                    'model': 'claude-sonnet-4-5',
                    'max_tokens': 8192,
                    'temperature': 0.5,
                    'timeout': 300
                }
            }
            yield conf

    def test_get_api_config_returns_all_settings(self, config):
        """Test that get_api_config returns all API settings."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ANTHROPIC_BASE_URL', None)

            api_config = config.get_api_config()

            assert api_config['provider'] == 'anthropic'
            assert api_config['model'] == 'claude-sonnet-4-5'
            assert api_config['max_tokens'] == 8192
            assert api_config['temperature'] == 0.5
            assert api_config['timeout'] == 300

    def test_get_api_config_includes_base_url(self, config):
        """Test that base_url is included when configured."""
        with patch.dict(os.environ, {'ANTHROPIC_BASE_URL': 'https://proxy.example.com'}):
            api_config = config.get_api_config()

            assert api_config['base_url'] == 'https://proxy.example.com'

    def test_get_api_config_uses_defaults(self):
        """Test that defaults are used when config is empty."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            config = Config()
            config._config = {}

            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop('ANTHROPIC_BASE_URL', None)

                api_config = config.get_api_config()

                assert api_config['provider'] == 'anthropic'
                assert api_config['model'] == 'claude-opus-4-5'
                assert api_config['max_tokens'] == 4096
                assert api_config['temperature'] == 0.7


class TestConfigWordCounts:
    """Tests for Config.get_word_count_targets method."""

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {}
            yield conf

    def test_get_word_count_targets_returns_defaults(self, config):
        """Test that default word counts are returned."""
        targets = config.get_word_count_targets()

        assert targets['abstract'] == 250
        assert targets['introduction'] == 1500
        assert targets['methods'] == 1500
        assert targets['results'] == 1500
        assert targets['discussion'] == 1000
        assert targets['conclusion'] == 500

    def test_get_word_count_targets_from_config(self, config):
        """Test that configured word counts are used."""
        config._config = {
            'content': {
                'default_word_counts': {
                    'abstract': 300,
                    'introduction': 2000
                }
            }
        }

        targets = config.get_word_count_targets()

        assert targets['abstract'] == 300
        assert targets['introduction'] == 2000


class TestConfigCitationStyle:
    """Tests for Config.get_citation_style method."""

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {}
            yield conf

    def test_get_citation_style_default(self, config):
        """Test default citation style."""
        assert config.get_citation_style() == 'apa'

    def test_get_citation_style_from_config(self, config):
        """Test configured citation style."""
        config._config = {'content': {'citation_style': 'mla'}}

        assert config.get_citation_style() == 'mla'


class TestConfigProjectConfig:
    """Tests for Config.load_project_config method."""

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            conf = Config()
            conf._config = {
                'api': {'model': 'claude-sonnet'},
                'content': {'citation_style': 'apa'}
            }
            yield conf

    def test_load_project_config_merges(self, config, tmp_path):
        """Test that project config is merged with base config."""
        # Create project config file
        project_config_dir = tmp_path / ".papergen"
        project_config_dir.mkdir()
        project_config_file = project_config_dir / "config.yaml"
        project_config_file.write_text("api:\n  model: claude-opus\ncontent:\n  citation_style: chicago\n")

        config.load_project_config(tmp_path)

        # Project config should override
        assert config.get('api.model') == 'claude-opus'
        assert config.get('content.citation_style') == 'chicago'

    def test_load_project_config_missing_file(self, config, tmp_path):
        """Test that missing project config is handled."""
        # Should not raise, just do nothing
        config.load_project_config(tmp_path)

        # Original config unchanged
        assert config.get('api.model') == 'claude-sonnet'


class TestConfigMerge:
    """Tests for Config._merge_config method."""

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        Config._instance = None

        with patch.object(Config, '_load_config'):
            yield Config()

    def test_merge_overwrites_simple_values(self, config):
        """Test that simple values are overwritten."""
        base = {'key': 'original'}
        override = {'key': 'new'}

        config._merge_config(base, override)

        assert base['key'] == 'new'

    def test_merge_adds_new_keys(self, config):
        """Test that new keys are added."""
        base = {'existing': 'value'}
        override = {'new_key': 'new_value'}

        config._merge_config(base, override)

        assert base['existing'] == 'value'
        assert base['new_key'] == 'new_value'

    def test_merge_recursively_merges_dicts(self, config):
        """Test that nested dicts are merged recursively."""
        base = {
            'api': {
                'model': 'original',
                'temperature': 0.7
            }
        }
        override = {
            'api': {
                'model': 'new'
            }
        }

        config._merge_config(base, override)

        # Model overwritten, temperature preserved
        assert base['api']['model'] == 'new'
        assert base['api']['temperature'] == 0.7
