"""
backend/sitemap_app/providers/ollama_provider.py
Provider implementation for local LLMs via Ollama HTTP API.
"""

import time
import logging
from typing import Any, Dict, List, Optional
import requests

from .base import BaseAIProvider, CompletionRequest, CompletionResponse, TokenUsage
from core.config import config

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Executes AI completions against a local or remote Ollama server."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None
    ):
        super().__init__(name="ollama")
        self.base_url = (base_url or config.ollama_base_url).rstrip('/')
        self.model = model or config.ollama_model
        self.timeout = timeout or config.ai_timeout_seconds
        self.max_retries = max_retries or config.ai_max_retries
        self.retry_delay = retry_delay or config.ai_retry_delay

    def is_available(self) -> bool:
        """
        Pings Ollama server version endpoint with a short timeout to check availability.
        """
        try:
            url = f"{self.base_url}/api/version"
            res = requests.get(url, timeout=3.0)
            return res.status_code == 200
        except Exception:
            return False

    def get_installed_models(self) -> List[str]:
        """Returns list of models installed on this Ollama instance."""
        try:
            url = f"{self.base_url}/api/tags"
            res = requests.get(url, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception as e:
            logger.warning(f"[ollama] Error fetching installed models: {e}")
        return []

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executes completion against Ollama with retries and timeout protection.
        """
        def _call() -> CompletionResponse:
            start_time = time.time()
            url = f"{self.base_url}/api/chat"
            
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": request.get_messages(),
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens
                }
            }

            if request.stop_sequences:
                payload["options"]["stop"] = request.stop_sequences

            # Ollama native JSON mode
            if request.response_format and request.response_format.get("type") == "json_object":
                payload["format"] = "json"

            effective_timeout = request.timeout_seconds or self.timeout

            try:
                res = requests.post(
                    url,
                    json=payload,
                    timeout=effective_timeout,
                    headers={"Content-Type": "application/json"}
                )
            except requests.exceptions.Timeout:
                return CompletionResponse(
                    success=False,
                    provider_name=self.name,
                    model=self.model,
                    error_message=f"Ollama request timed out after {effective_timeout}s",
                    status_code=504,
                    duration_ms=(time.time() - start_time) * 1000
                )
            except requests.exceptions.ConnectionError:
                return CompletionResponse(
                    success=False,
                    provider_name=self.name,
                    model=self.model,
                    error_message=f"Failed to connect to Ollama at {self.base_url}. Ensure Ollama is running.",
                    status_code=503,
                    duration_ms=(time.time() - start_time) * 1000
                )
            except requests.exceptions.RequestException as e:
                return CompletionResponse(
                    success=False,
                    provider_name=self.name,
                    model=self.model,
                    error_message=f"Ollama request failed: {str(e)}",
                    status_code=500,
                    duration_ms=(time.time() - start_time) * 1000
                )

            duration_ms = (time.time() - start_time) * 1000

            if res.status_code != 200:
                return CompletionResponse(
                    success=False,
                    provider_name=self.name,
                    model=self.model,
                    error_message=f"Ollama HTTP error {res.status_code}: {res.text}",
                    status_code=res.status_code,
                    duration_ms=duration_ms
                )

            try:
                body = res.json()
            except Exception as e:
                return CompletionResponse(
                    success=False,
                    provider_name=self.name,
                    model=self.model,
                    error_message=f"Failed to parse Ollama JSON response: {str(e)}",
                    status_code=res.status_code,
                    duration_ms=duration_ms
                )

            msg = body.get("message", {})
            content = msg.get("content", "")

            # Token usage extraction
            prompt_tokens = body.get("prompt_eval_count", 0)
            completion_tokens = body.get("eval_count", 0)
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )

            resp = CompletionResponse(
                success=True,
                content=content,
                model=body.get("model", self.model),
                provider_name=self.name,
                raw_response=body,
                status_code=200,
                usage=usage,
                duration_ms=duration_ms
            )

            if payload.get("format") == "json" or request.response_format:
                resp.parse_as_json()

            return resp

        return self._execute_with_retry(
            _call,
            max_retries=self.max_retries,
            initial_delay=self.retry_delay
        )

