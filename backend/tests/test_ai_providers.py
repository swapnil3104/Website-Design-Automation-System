"""
backend/tests/test_ai_providers.py
Unit and integration tests for AI Provider Subsystem (Phase 2).
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Configure minimal Django settings if not configured
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

import unittest
from core.config import config
from sitemap_app.providers import (
    BaseAIProvider,
    CompletionRequest,
    CompletionResponse,
    TokenUsage,
    OllamaProvider,
    OpenRouterProvider,
    MockFallbackProvider,
    get_ai_provider,
    execute_completion_with_fallback
)


class TestProviderDataClasses(unittest.TestCase):
    """Test data structures and JSON parsing helpers."""

    def test_completion_request_messages(self):
        req = CompletionRequest(
            prompt="Create a portfolio site",
            system_instruction="You are an expert designer."
        )
        msgs = req.get_messages()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[0]["content"], "You are an expert designer.")
        self.assertEqual(msgs[1]["role"], "user")
        self.assertEqual(msgs[1]["content"], "Create a portfolio site")

    def test_completion_response_json_clean(self):
        resp = CompletionResponse(
            success=True,
            content='{"key": "value", "items": [1, 2, 3]}'
        )
        data = resp.parse_as_json()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("key"), "value")

    def test_completion_response_json_fenced(self):
        resp = CompletionResponse(
            success=True,
            content='Here is the requested output:\n```json\n{"status": "ok", "count": 42}\n```\nHope this helps!'
        )
        data = resp.parse_as_json()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("count"), 42)

    def test_completion_response_bracket_recovery(self):
        resp = CompletionResponse(
            success=True,
            content='Certainly! Below is the array:\n[{"id": "sec-1", "type": "hero"}, {"id": "sec-2", "type": "features"}]\nLet me know if you need more.'
        )
        data = resp.parse_as_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["type"], "hero")


class TestMockProvider(unittest.TestCase):
    """Test deterministic mock fallback provider."""

    def setUp(self):
        self.provider = MockFallbackProvider()

    def test_availability(self):
        self.assertTrue(self.provider.is_available())

    def test_sitemap_mock_generation(self):
        req = CompletionRequest(
            prompt="Generate a sitemap for an e-commerce coffee brand",
            response_format={"type": "json_object"}
        )
        resp = self.provider.complete(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.provider_name, "mock")
        data = resp.parse_as_json()
        self.assertIn("pages", data)
        self.assertTrue(len(data["pages"]) > 0)

    def test_wireframe_mock_generation(self):
        req = CompletionRequest(
            prompt="Generate wireframe sections for the Home page",
            response_format={"type": "json_object"}
        )
        resp = self.provider.complete(req)
        self.assertTrue(resp.success)
        data = resp.parse_as_json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 3)


class TestOllamaProviderIntegration(unittest.TestCase):
    """Integration test for local Ollama instance."""

    def setUp(self):
        self.provider = OllamaProvider(model="qwen2.5:3b")

    def test_connection_and_availability(self):
        available = self.provider.is_available()
        if not available:
            self.skipTest("Ollama is not running on localhost:11434")
        self.assertTrue(available, "Ollama should be accessible on localhost:11434")

    def test_qwen_structured_json_generation(self):
        if not self.provider.is_available():
            self.skipTest("Ollama is not running")

        req = CompletionRequest(
            prompt="Generate a JSON object with keys 'site_title', 'industry', and 'primary_color'. Return JSON only.",
            system_instruction="You are a JSON-only generator.",
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=150,
            timeout_seconds=30
        )
        resp = self.provider.complete(req)
        self.assertTrue(resp.success, f"Ollama generation failed: {resp.error_message}")
        data = resp.parse_as_json()
        self.assertIsInstance(data, dict, f"Expected dict, got {data}")
        self.assertIn("site_title", data)
        self.assertIn("industry", data)


class TestOpenRouterProviderIntegration(unittest.TestCase):
    """Integration test for OpenRouter cloud provider."""

    def setUp(self):
        self.provider = OpenRouterProvider()

    def test_availability(self):
        # Checks if key is configured
        self.assertTrue(self.provider.is_available())

    def test_secret_protection(self):
        # Ensure API key is masked in error responses
        fake_provider = OpenRouterProvider(
            api_key="sk-or-v1-fakekey1234567890",
            base_url="http://invalid-domain-xyz-1234.com",
            fallback_models=[],
            max_retries=1
        )
        req = CompletionRequest(prompt="Hello", timeout_seconds=2)
        resp = fake_provider.complete(req)
        self.assertFalse(resp.success)
        self.assertNotIn("sk-or-v1-fakekey1234567890", str(resp.error_message))


class TestProviderFactoryAndFailover(unittest.TestCase):
    """Test provider resolution and automated failover."""

    def test_provider_resolution(self):
        p_mock = get_ai_provider("mock")
        self.assertIsInstance(p_mock, MockFallbackProvider)

        p_ollama = get_ai_provider("ollama")
        self.assertIsInstance(p_ollama, OllamaProvider)

        p_openrouter = get_ai_provider("openrouter")
        self.assertIsInstance(p_openrouter, OpenRouterProvider)

    def test_failover_to_mock_on_invalid_endpoint(self):
        # Configure an unreachable provider and verify it falls back smoothly without exception
        unreachable_ollama = OllamaProvider(base_url="http://localhost:9999", max_retries=1)
        req = CompletionRequest(prompt="Generate sitemap for tech startup")
        
        # Test execute_completion_with_fallback directly
        resp = execute_completion_with_fallback(req, preferred_provider="mock")
        self.assertTrue(resp.success)
        self.assertIsNotNone(resp.parse_as_json())


if __name__ == "__main__":
    unittest.main()
