"""
backend/sitemap_app/providers/openrouter_provider.py
Provider implementation for OpenRouter cloud LLM API with model failover.
"""

import time
import logging
from typing import Any, Dict, List, Optional
import requests

from .base import BaseAIProvider, CompletionRequest, CompletionResponse, TokenUsage
from core.config import config

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseAIProvider):
    """Executes AI completions against OpenRouter API with multi-model fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None
    ):
        super().__init__(name="openrouter")
        self.api_key = api_key or config.openrouter_api_key
        raw_url = base_url or config.openrouter_base_url
        # Normalize endpoint: ensure ends with /chat/completions
        clean_url = raw_url.rstrip('/')
        if not clean_url.endswith('/chat/completions'):
            clean_url = f"{clean_url}/chat/completions"
        self.base_url = clean_url

        self.model = model or config.openrouter_model
        self.fallback_models = fallback_models or config.openrouter_fallback_models
        self.timeout = timeout or config.ai_timeout_seconds
        self.max_retries = max_retries or config.ai_max_retries
        self.retry_delay = retry_delay or config.ai_retry_delay

    def is_available(self) -> bool:
        """
        Validates presence and basic format of API key.
        """
        if not self.api_key or "xxxx" in self.api_key.lower():
            return False
        return True

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executes completion against OpenRouter with automatic model fallback and retries.
        """
        if not self.is_available():
            return CompletionResponse(
                success=False,
                provider_name=self.name,
                model=self.model,
                error_message="OpenRouter API key is missing or invalid. Set OPENROUTER_API_KEY in .env.",
                status_code=401
            )

        candidate_models = [self.model]
        for fb in self.fallback_models:
            if fb and fb not in candidate_models:
                candidate_models.append(fb)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": config.ai_http_referer,
            "X-Title": config.ai_app_name,
            "Content-Type": "application/json"
        }

        effective_timeout = request.timeout_seconds or self.timeout
        last_error_resp = None

        for model_to_try in candidate_models:
            def _call_model() -> CompletionResponse:
                start_time = time.time()
                payload: Dict[str, Any] = {
                    "model": model_to_try,
                    "messages": request.get_messages(),
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                }
                if request.response_format:
                    payload["response_format"] = request.response_format
                if request.stop_sequences:
                    payload["stop"] = request.stop_sequences

                try:
                    res = requests.post(
                        self.base_url,
                        json=payload,
                        headers=headers,
                        timeout=effective_timeout
                    )
                except requests.exceptions.Timeout:
                    return CompletionResponse(
                        success=False,
                        provider_name=self.name,
                        model=model_to_try,
                        error_message=f"OpenRouter timed out after {effective_timeout}s with model {model_to_try}",
                        status_code=504,
                        duration_ms=(time.time() - start_time) * 1000
                    )
                except requests.exceptions.RequestException as e:
                    return CompletionResponse(
                        success=False,
                        provider_name=self.name,
                        model=model_to_try,
                        error_message=f"OpenRouter request error: {str(e)}",
                        status_code=500,
                        duration_ms=(time.time() - start_time) * 1000
                    )

                duration_ms = (time.time() - start_time) * 1000

                if res.status_code != 200:
                    # Sanitize error message to prevent accidental key leakage
                    err_text = res.text
                    if self.api_key and self.api_key in err_text:
                        err_text = err_text.replace(self.api_key, "[REDACTED]")

                    return CompletionResponse(
                        success=False,
                        provider_name=self.name,
                        model=model_to_try,
                        error_message=f"OpenRouter HTTP error {res.status_code}: {err_text}",
                        status_code=res.status_code,
                        duration_ms=duration_ms
                    )

                try:
                    data = res.json()
                except Exception as e:
                    return CompletionResponse(
                        success=False,
                        provider_name=self.name,
                        model=model_to_try,
                        error_message=f"Failed to parse OpenRouter response: {str(e)}",
                        status_code=res.status_code,
                        duration_ms=duration_ms
                    )

                choices = data.get("choices", [])
                if not choices:
                    return CompletionResponse(
                        success=False,
                        provider_name=self.name,
                        model=model_to_try,
                        error_message="OpenRouter returned empty choices list",
                        raw_response=data,
                        status_code=200,
                        duration_ms=duration_ms
                    )

                message = choices[0].get("message", {})
                content = message.get("content", "")

                raw_usage = data.get("usage", {})
                usage = TokenUsage(
                    prompt_tokens=raw_usage.get("prompt_tokens", 0),
                    completion_tokens=raw_usage.get("completion_tokens", 0),
                    total_tokens=raw_usage.get("total_tokens", 0)
                )

                resp = CompletionResponse(
                    success=True,
                    content=content,
                    model=data.get("model", model_to_try),
                    provider_name=self.name,
                    raw_response=data,
                    status_code=200,
                    usage=usage,
                    duration_ms=duration_ms
                )

                if request.response_format:
                    resp.parse_as_json()

                return resp

            attempt_result = self._execute_with_retry(
                _call_model,
                max_retries=self.max_retries,
                initial_delay=self.retry_delay
            )

            if attempt_result.success:
                return attempt_result

            last_error_resp = attempt_result
            logger.warning(
                f"[openrouter] Model '{model_to_try}' failed ({attempt_result.error_message}). "
                f"Attempting fallback model if available..."
            )

        return last_error_resp or CompletionResponse(
            success=False,
            provider_name=self.name,
            model=self.model,
            error_message="All OpenRouter models failed."
        )

