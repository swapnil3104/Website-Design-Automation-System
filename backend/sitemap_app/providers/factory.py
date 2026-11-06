"""
backend/sitemap_app/providers/factory.py
Factory and resolver for AI model providers with automatic failover.
"""

import logging
from typing import Dict, Optional

from .base import BaseAIProvider, CompletionRequest, CompletionResponse
from .ollama_provider import OllamaProvider
from .openrouter_provider import OpenRouterProvider
from .mock_provider import MockFallbackProvider
from core.config import config

logger = logging.getLogger(__name__)

# Cached provider singleton instances
_instances: Dict[str, BaseAIProvider] = {}


def get_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """
    Resolves and returns the appropriate AI provider instance.
    
    Resolution hierarchy:
    1. Explicit provider_name if provided ('ollama', 'openrouter', 'mock', 'auto').
    2. config.ai_provider ('ollama', 'openrouter', 'mock', 'auto').
    3. In 'auto' mode:
       - If Ollama is available -> OllamaProvider
       - Else if OpenRouter key is configured -> OpenRouterProvider
       - Else -> MockFallbackProvider
    """
    target = (provider_name or config.ai_provider or "auto").strip().lower()

    if target == "ollama":
        if "ollama" not in _instances:
            _instances["ollama"] = OllamaProvider()
        return _instances["ollama"]

    if target == "openrouter":
        if "openrouter" not in _instances:
            _instances["openrouter"] = OpenRouterProvider()
        return _instances["openrouter"]

    if target == "mock":
        if "mock" not in _instances:
            _instances["mock"] = MockFallbackProvider()
        return _instances["mock"]

    # 'auto' mode: probe availability in priority order
    if "ollama" not in _instances:
        _instances["ollama"] = OllamaProvider()
    if _instances["ollama"].is_available():
        logger.info("[AI Provider] Auto-selected healthy local Ollama provider.")
        return _instances["ollama"]

    if "openrouter" not in _instances:
        _instances["openrouter"] = OpenRouterProvider()
    if _instances["openrouter"].is_available():
        logger.info("[AI Provider] Auto-selected cloud OpenRouter provider.")
        return _instances["openrouter"]

    logger.warning("[AI Provider] Neither Ollama nor OpenRouter is available. Using MockFallbackProvider.")
    if "mock" not in _instances:
        _instances["mock"] = MockFallbackProvider()
    return _instances["mock"]


def execute_completion_with_fallback(
    request: CompletionRequest,
    preferred_provider: Optional[str] = None
) -> CompletionResponse:
    """
    Executes completion with multi-level provider fallback:
    Primary -> Alternative Provider -> Mock Fallback.
    Guarantees the system never crashes on external provider network failures.
    """
    primary = get_ai_provider(preferred_provider)
    resp = primary.complete(request)

    if resp.success:
        return resp

    logger.warning(
        f"[Provider Failover] Primary provider '{primary.name}' failed: "
        f"{resp.error_message}. Attempting secondary provider..."
    )

    # Determine secondary provider
    fallback_chain = []
    if primary.name == "ollama":
        fallback_chain = [get_ai_provider("openrouter"), get_ai_provider("mock")]
    elif primary.name == "openrouter":
        fallback_chain = [get_ai_provider("ollama"), get_ai_provider("mock")]
    else:
        fallback_chain = [get_ai_provider("mock")]

    for fallback in fallback_chain:
        if fallback.name == primary.name:
            continue
        if not fallback.is_available():
            continue

        logger.info(f"[Provider Failover] Trying fallback provider '{fallback.name}'...")
        fb_resp = fallback.complete(request)
        if fb_resp.success:
            logger.info(f"[Provider Failover] Fallback provider '{fallback.name}' succeeded.")
            return fb_resp

    return resp

