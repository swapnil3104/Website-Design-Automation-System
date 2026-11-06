"""
backend/sitemap_app/providers/base.py
Core abstraction and dataclasses for all AI model providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
import json
import re
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompletionRequest:
    """Standardized input request for any AI model completion."""
    prompt: str
    system_instruction: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    temperature: float = 0.2
    max_tokens: int = 4096
    response_format: Optional[Dict[str, str]] = None  # e.g., {"type": "json_object"}
    stop_sequences: Optional[List[str]] = None
    timeout_seconds: int = 45

    def get_messages(self) -> List[Dict[str, str]]:
        """Returns normalized messages list containing system instruction and user prompt."""
        if self.messages:
            return list(self.messages)

        msgs: List[Dict[str, str]] = []
        if self.system_instruction:
            msgs.append({"role": "system", "content": self.system_instruction})
        msgs.append({"role": "user", "content": self.prompt})
        return msgs


@dataclass
class TokenUsage:
    """Token consumption statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class CompletionResponse:
    """Standardized response returned by any AI model provider."""
    success: bool
    content: str = ""
    parsed_json: Optional[Union[Dict[str, Any], List[Any]]] = None
    model: str = ""
    provider_name: str = ""
    raw_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    duration_ms: float = 0.0

    def parse_as_json(self) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Attempts to safely parse content as JSON with code fence removal
        and balanced bracket recovery if conversational text surrounds it.
        """
        if self.parsed_json is not None:
            return self.parsed_json

        if not self.content:
            return None

        cleaned = self.content.strip()

        # 1. Direct parse attempt
        try:
            self.parsed_json = json.loads(cleaned)
            return self.parsed_json
        except Exception:
            pass

        # 2. Markdown fence removal
        if "```" in cleaned:
            # Extract content inside code block
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
            if match:
                fenced = match.group(1).strip()
                try:
                    self.parsed_json = json.loads(fenced)
                    return self.parsed_json
                except Exception:
                    cleaned = fenced

        # 3. Balanced bracket heuristic for JSON object {...} or array [...]
        for open_ch, close_ch in [('{', '}'), ('[', ']')]:
            start_idx = cleaned.find(open_ch)
            end_idx = cleaned.rfind(close_ch)
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                candidate = cleaned[start_idx:end_idx + 1].strip()
                try:
                    self.parsed_json = json.loads(candidate)
                    return self.parsed_json
                except Exception:
                    # Trailing comma recovery
                    try:
                        repaired = re.sub(r',\s*([\]\}])', r'\1', candidate)
                        self.parsed_json = json.loads(repaired)
                        return self.parsed_json
                    except Exception:
                        continue

        return None


class BaseAIProvider(ABC):
    """Abstract base class that all AI execution engines must implement."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider endpoint is healthy and reachable."""
        pass

    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a synchronous completion against the model."""
        pass

    def _execute_with_retry(
        self,
        call_fn: Callable[[], CompletionResponse],
        max_retries: int = 3,
        initial_delay: float = 1.5
    ) -> CompletionResponse:
        """
        Executes a network call with exponential backoff and error normalization.
        """
        delay = initial_delay
        last_response = None

        for attempt in range(1, max_retries + 1):
            try:
                response = call_fn()
                if response.success:
                    return response
                
                # Check if the failure is retryable (e.g., 429 rate limit or 5xx server error)
                if response.status_code and response.status_code not in (429, 500, 502, 503, 504):
                    # Non-retryable error (e.g. 400 Bad Request, 401 Unauthorized)
                    return response

                last_response = response
                logger.warning(
                    f"[{self.name}] Attempt {attempt}/{max_retries} failed: "
                    f"{response.error_message}. Retrying in {delay:.1f}s..."
                )
            except Exception as e:
                logger.warning(
                    f"[{self.name}] Attempt {attempt}/{max_retries} exception: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                last_response = CompletionResponse(
                    success=False,
                    provider_name=self.name,
                    error_message=str(e)
                )

            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0

        return last_response or CompletionResponse(
            success=False,
            provider_name=self.name,
            error_message="Exceeded maximum retries."
        )

