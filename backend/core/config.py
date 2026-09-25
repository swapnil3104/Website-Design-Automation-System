"""
Secure configuration loader for environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


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
        if not (os.getenv('PRIVATE_KEY') or os.getenv('AI_API_KEY')):
            raise ConfigurationError(
                "Missing required environment variables: PRIVATE_KEY or AI_API_KEY. "
                "Please ensure one is set in your .env file or environment."
            )

    @property
    def private_key(self) -> str:
        def _valid_key(val: str) -> bool:
            if not val:
                return False
            return 'xxxx' not in val.lower()

        key = os.getenv('PRIVATE_KEY') if _valid_key(os.getenv('PRIVATE_KEY', '')) else ''
        if not key:
            key = os.getenv('AI_API_KEY') if _valid_key(os.getenv('AI_API_KEY', '')) else ''
        if not key:
            raise ConfigurationError(
                "PRIVATE_KEY is not configured. Please set it in your .env file."
            )
        return key

    @property
    def ai_api_key(self) -> str:
        def _valid_key(val: str) -> bool:
            if not val:
                return False
            return 'xxxx' not in val.lower()

        ai_key = os.getenv('AI_API_KEY', '')
        if _valid_key(ai_key):
            return ai_key
        private_key = os.getenv('PRIVATE_KEY', '')
        if _valid_key(private_key):
            return private_key
        return ai_key or private_key

    @property
    def ai_base_url(self) -> str:
        return os.getenv('AI_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions')

    @property
    def ai_http_referer(self) -> str:
        return os.getenv('AI_HTTP_REFERER', 'http://localhost:8000')

    @property
    def ai_app_name(self) -> str:
        return os.getenv('AI_APP_NAME', 'Website Design Automation')

    @property
    def chat_ai_base_url(self) -> str:
        return os.getenv('CHAT_AI_BASE_URL', self.ai_base_url)

    @property
    def wireframe_ai_base_url(self) -> str:
        return os.getenv('WIREFRAME_AI_BASE_URL', self.ai_base_url)

    @property
    def chat_ai_model(self) -> str:
        return (
            os.getenv('CHAT_AI_MODEL')
            or os.getenv('AI_MODEL_CHAT')
            or os.getenv('AI_MODEL')
            or 'meta-llama/llama-3.2-3b-instruct:free'
        )

    @property
    def chat_ai_fallback_models(self) -> list:
        raw = os.getenv('CHAT_AI_FALLBACK_MODELS', '')
        if not raw:
            return ['google/gemini-2.0-flash-lite-preview-02-05:free', 'qwen/qwen-2.5-72b-instruct:free']
        return [m.strip() for m in raw.split(',') if m.strip()]

    @property
    def wireframe_ai_model(self) -> str:
        return (
            os.getenv('WIREFRAME_AI_MODEL')
            or os.getenv('AI_MODEL_WIREFRAME')
            or os.getenv('AI_MODEL')
            or 'meta-llama/llama-3.2-3b-instruct:free'
        )

    @property
    def chat_ai_enabled(self) -> bool:
        value = os.getenv('CHAT_AI_ENABLED')
        if value is None:
            return bool(self.ai_api_key)
        return value.lower() in ('true', '1', 'yes')

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
