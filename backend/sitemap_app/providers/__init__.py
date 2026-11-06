"""
backend/sitemap_app/providers/__init__.py
Unified exports for AI provider subsystem.
"""

from .base import (
    BaseAIProvider,
    CompletionRequest,
    CompletionResponse,
    TokenUsage
)
from .ollama_provider import OllamaProvider
from .openrouter_provider import OpenRouterProvider
from .mock_provider import MockFallbackProvider
from .factory import (
    get_ai_provider,
    execute_completion_with_fallback
)

__all__ = [
    "BaseAIProvider",
    "CompletionRequest",
    "CompletionResponse",
    "TokenUsage",
    "OllamaProvider",
    "OpenRouterProvider",
    "MockFallbackProvider",
    "get_ai_provider",
    "execute_completion_with_fallback"
]

