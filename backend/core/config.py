"""
Secure configuration loader for environment variables.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Config:
    """
    Centralized configuration management for the application.
    Loads environment variables from .env file and provides
    secure access to sensitive configuration values.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_environment()
            self._validate_required_vars()
            Config._initialized = True

    def _load_environment(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        env_path = base_dir / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

    def _validate_required_vars(self) -> None:
        provider = os.getenv('AI_PROVIDER', 'auto').strip().lower()
        if provider == 'openrouter':
            key = os.getenv('OPENROUTER_API_KEY') or os.getenv('AI_API_KEY') or os.getenv('PRIVATE_KEY')
            if not key or 'xxxx' in key.lower():
                logger.warning(
                    "AI_PROVIDER is set to 'openrouter' but no valid OPENROUTER_API_KEY or AI_API_KEY was found."
                )

    # ---------------- Provider & Model Configurations ----------------

    @property
    def ai_provider(self) -> str:
        """Active AI provider: 'ollama', 'openrouter', 'mock', or 'auto'."""
        return os.getenv('AI_PROVIDER', 'auto').strip().lower()

    @property
    def ollama_base_url(self) -> str:
        """Base endpoint for Ollama instance (default: http://localhost:11434)."""
        raw = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').strip()
        return raw.rstrip('/')

    @property
    def ollama_model(self) -> str:
        """Target model tag for Ollama execution (default: qwen2.5:3b)."""
        return os.getenv('OLLAMA_MODEL', 'qwen2.5:3b').strip()

    @property
    def openrouter_api_key(self) -> str:
        """API key for OpenRouter."""
        for env_name in ('OPENROUTER_API_KEY', 'AI_API_KEY', 'PRIVATE_KEY'):
            val = os.getenv(env_name, '').strip()
            if val and 'xxxx' not in val.lower():
                return val
        return ''

    @property
    def openrouter_model(self) -> str:
        """Target model for OpenRouter."""
        return (
            os.getenv('OPENROUTER_MODEL')
            or os.getenv('AI_MODEL')
            or os.getenv('CHAT_AI_MODEL')
            or 'anthropic/claude-3.7-sonnet'
        ).strip()

    @property
    def openrouter_base_url(self) -> str:
        """Base API URL for OpenRouter completions."""
        return os.getenv(
            'OPENROUTER_BASE_URL',
            os.getenv('AI_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions')
        ).strip()

    @property
    def openrouter_fallback_models(self) -> List[str]:
        """Ordered list of fallback models when OpenRouter primary model fails."""
        raw = os.getenv('OPENROUTER_FALLBACK_MODELS') or os.getenv('CHAT_AI_FALLBACK_MODELS', '')
        if not raw:
            return ['anthropic/claude-3.5-sonnet', 'openai/gpt-4.1', 'deepseek/deepseek-v3.2']
        return [m.strip() for m in raw.split(',') if m.strip()]

    # ---------------- Execution & Timeout Settings ----------------

    @property
    def ai_timeout_seconds(self) -> int:
        """Timeout for AI completion requests in seconds."""
        try:
            return int(os.getenv('AI_TIMEOUT_SECONDS', '45'))
        except (ValueError, TypeError):
            return 45

    @property
    def ai_max_retries(self) -> int:
        """Maximum retry attempts for transient AI provider errors."""
        try:
            return int(os.getenv('AI_MAX_RETRIES', '3'))
        except (ValueError, TypeError):
            return 3

    @property
    def ai_retry_delay(self) -> float:
        """Initial retry delay in seconds (exponential backoff base)."""
        try:
            return float(os.getenv('AI_RETRY_DELAY', '1.5'))
        except (ValueError, TypeError):
            return 1.5

    @property
    def ai_temperature(self) -> float:
        """Default temperature for AI generation."""
        try:
            return float(os.getenv('AI_TEMPERATURE', '0.2'))
        except (ValueError, TypeError):
            return 0.2

    @property
    def ai_max_tokens(self) -> int:
        """Default maximum token generation length."""
        try:
            return int(os.getenv('AI_MAX_TOKENS', '4096'))
        except (ValueError, TypeError):
            return 4096

    # ---------------- Legacy Compatibility Properties ----------------

    @property
    def private_key(self) -> str:
        """Legacy accessor. Always returns openrouter_api_key."""
        return self.openrouter_api_key

    @property
    def ai_api_key(self) -> str:
        """Legacy accessor for API key."""
        return self.openrouter_api_key

    @property
    def ai_base_url(self) -> str:
        return self.openrouter_base_url

    @property
    def ai_http_referer(self) -> str:
        return os.getenv('AI_HTTP_REFERER', 'http://localhost:8000')

    @property
    def ai_app_name(self) -> str:
        return os.getenv('AI_APP_NAME', 'Website Design Automation')

    @property
    def chat_ai_base_url(self) -> str:
        return os.getenv('CHAT_AI_BASE_URL', self.openrouter_base_url)

    @property
    def wireframe_ai_base_url(self) -> str:
        return os.getenv('WIREFRAME_AI_BASE_URL', self.openrouter_base_url)

    @property
    def chat_ai_model(self) -> str:
        return self.openrouter_model

    @property
    def chat_ai_fallback_models(self) -> List[str]:
        return self.openrouter_fallback_models

    @property
    def wireframe_ai_model(self) -> str:
        return (
            os.getenv('WIREFRAME_AI_MODEL')
            or os.getenv('AI_MODEL_WIREFRAME')
            or self.openrouter_model
        )

    @property
    def chat_ai_enabled(self) -> bool:
        value = os.getenv('CHAT_AI_ENABLED')
        if value is None:
            return True
        return value.lower() in ('true', '1', 'yes')

    # ---------------- Django App Settings ----------------

    @property
    def secret_key(self) -> str:
        return os.getenv(
            'SECRET_KEY',
            'django-insecure-your-secret-key-here-change-in-production'
        )

    @property
    def debug(self) -> bool:
        return os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

    @property
    def allowed_hosts(self) -> list:
        hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
        return [host.strip() for host in hosts.split(',')]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)


# Singleton instance
config = Config()


def get_private_key() -> str:
    return config.private_key

