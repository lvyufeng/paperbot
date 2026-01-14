"""Configuration management for PaperGen."""

from pathlib import Path
from typing import Any, Dict, Optional
import os

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for PaperGen."""

    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """Singleton pattern for configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from files and environment."""
        # Load environment variables
        load_dotenv()

        # Load default config
        default_config_path = Path(__file__).parent.parent.parent.parent / "config" / "default_config.yaml"
        if default_config_path.exists():
            with open(default_config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation).

        Args:
            key: Configuration key (e.g., "api.model")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_api_key(self) -> str:
        """
        Get Anthropic API key from environment.

        Returns:
            API key

        Raises:
            ValueError: If API key not found
        """
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables.\n"
                "Please set it with: export ANTHROPIC_API_KEY='your-key-here'"
            )
        return api_key

    def get_api_base_url(self) -> Optional[str]:
        """
        Get custom API base URL from environment or config.

        Supports self-hosted Anthropic API and third-party providers
        like LiteLLM, OpenRouter, etc.

        Returns:
            Custom base URL if configured, None for default Anthropic API
        """
        # Check environment variable first (highest priority)
        base_url = os.getenv('ANTHROPIC_BASE_URL')
        if base_url:
            return base_url

        # Check config file
        base_url = self.get('api.base_url', None)
        return base_url

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        config = {
            'provider': self.get('api.provider', 'anthropic'),
            'model': self.get('api.model', 'claude-opus-4-5'),
            'max_tokens': self.get('api.max_tokens', 4096),
            'temperature': self.get('api.temperature', 0.7),
            'timeout': self.get('api.timeout', 120),
        }

        # Add base_url if configured (for self-hosted or third-party APIs)
        base_url = self.get_api_base_url()
        if base_url:
            config['base_url'] = base_url

        return config

    def get_word_count_targets(self) -> Dict[str, int]:
        """Get default word count targets for sections."""
        return self.get('content.default_word_counts', {
            'abstract': 250,
            'introduction': 1500,
            'methods': 1500,
            'results': 1500,
            'discussion': 1000,
            'conclusion': 500,
        })

    def get_citation_style(self) -> str:
        """Get citation style."""
        return self.get('content.citation_style', 'apa')

    def load_project_config(self, project_path: Path) -> None:
        """
        Load and merge project-specific configuration.

        Args:
            project_path: Path to project root
        """
        config_file = project_path / ".papergen" / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                project_config = yaml.safe_load(f) or {}
                # Merge with existing config (project config takes precedence)
                self._merge_config(self._config, project_config)

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value


# Global configuration instance
config = Config()
