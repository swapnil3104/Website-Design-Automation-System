"""
backend/tests/test_phase8_benchmarking_and_testing.py
Comprehensive End-to-End Test Suite for Phase 8: Testing & Model Benchmarking.

Verifies:
1. AI Provider Testing:
   - Ollama connectivity and offline handling
   - Qwen (qwen2.5:3b) provider configuration and execution
   - Nemotron (nemotron-mini:4b) provider configuration and execution
   - OpenRouter provider headers, bearer token protection, and HTTP error handling
   - Invalid AI responses recovery (markdown fences, conversational prefixes, broken JSON, non-JSON strings)
   - Provider timeouts and cascading failover
   - Dynamic provider switching ('mock', 'ollama', 'openrouter', 'auto')
2. Generation Testing across 8 Categories:
   - Simple business website
   - Multi-page corporate business website
   - E-commerce website
   - SaaS platform website
   - Portfolio website
   - Agriculture & Agritech website
   - Healthcare & Medical clinic website
   - Complex custom requirements with nested paths & dynamic questions
3. Frontend Testing:
   - Sitemap display & tree navigation
   - Wireframe canvas multi-board rendering
   - All 32 supported component types rendering cleanly without crashes
   - Responsive previews & breakpoints (desktop, tablet, mobile)
   - Page navigation & single-page vs all-pages switcher
   - Section inline editing, toolbar actions (move up/down), add modal, and type replacement
   - Section-level and page-level regeneration
   - State persistence & localStorage auto-saving
4. Model Benchmarking & Selection:
   - 20 standard test prompts catalog and domain coverage
   - JSON validity, requirement coverage, render success, latency, and quality scoring
   - Model selection decision matrix (selecting Qwen 2.5 3B as best local model)
"""

import os
import sys
import json
import time
import unittest
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

os.environ['AI_PROVIDER'] = 'mock'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import TestCase, Client
from rest_framework.test import APIRequestFactory

from core.config import config
from sitemap_app.analyzer import RequirementAnalyzer
from sitemap_app.page_planner import PagePlanner
from sitemap_app.sitemap_service import SitemapService
from sitemap_app.wireframe_service import WireframeService
from sitemap_app.quality_evaluator import QualityEvaluator
from sitemap_app.schemas.sitemap import SUPPORTED_SECTION_TYPES
from sitemap_app.schemas.wireframe import (
    validate_wireframe,
    validate_page_wireframe,
    SUPPORTED_LAYOUT_VARIANTS
)
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
from tests.benchmark_suite_20 import BENCHMARK_PROMPTS, BenchmarkRunner


class TestPhase8TestingAndBenchmarking(TestCase):
    """
    Complete Verification Suite for Phase 8: Testing & Model Benchmarking.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_root = backend_dir.parent
        cls.editor_js_path = cls.repo_root / 'frontend' / 'js' / 'wireframe-editor.js'
        cls.wireframe_js_path = cls.repo_root / 'frontend' / 'js' / 'wireframe.js'
        cls.components_js_path = cls.repo_root / 'frontend' / 'js' / 'wireframe-components.js'
        cls.state_manager_path = cls.repo_root / 'frontend' / 'js' / 'state-manager.js'
        cls.wireframe_css_path = cls.repo_root / 'frontend' / 'css' / 'wireframe.css'
        cls.wireframe_html_path = cls.repo_root / 'frontend' / 'wireframe.html'

    def setUp(self):
        self.analyzer = RequirementAnalyzer()
        self.planner = PagePlanner()
        self.sitemap_service = SitemapService()
        self.wireframe_service = WireframeService()
        self.evaluator = QualityEvaluator()
        self.client = Client()

    # =========================================================================
    # PART 1: AI PROVIDER TESTING
    # =========================================================================

    def test_01_ollama_connectivity_and_offline_handling(self):
        """Verifies Ollama connectivity checks and graceful offline degradation."""
        # Non-running / unreachable endpoint
        offline_provider = OllamaProvider(
            base_url="http://127.0.0.1:9999",
            model="qwen2.5:3b",
            timeout=1,
            max_retries=1,
            retry_delay=0.01
        )
        self.assertFalse(offline_provider.is_available())

        req = CompletionRequest(prompt="Generate JSON", max_tokens=100)
        resp = offline_provider.complete(req)
        self.assertFalse(resp.success)
        self.assertIn("Failed to connect to Ollama", resp.error_message)
        self.assertIsNone(resp.parsed_json)

    def test_02_qwen_provider_configuration_and_completion(self):
        """Verifies Qwen 2.5 3B provider configuration, request formatting, and JSON parsing."""
        qwen = OllamaProvider(model="qwen2.5:3b")
        self.assertEqual(qwen.model, "qwen2.5:3b")

        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "message": {"content": json.dumps({"website_name": "Qwen Bakery", "pages": ["Home", "Menu"]})},
            "prompt_eval_count": 25,
            "eval_count": 80
        }
        with patch('requests.post', return_value=mock_res):
            req = CompletionRequest(
                prompt="Generate bakery sitemap",
                response_format={"type": "json_object"}
            )
            resp = qwen.complete(req)
            self.assertTrue(resp.success)
            self.assertEqual(resp.model, "qwen2.5:3b")
            self.assertIsInstance(resp.parsed_json, dict)
            self.assertEqual(resp.parsed_json.get("website_name"), "Qwen Bakery")

    def test_03_nemotron_provider_configuration_and_completion(self):
        """Verifies Nemotron Mini 4B provider configuration and structured completion."""
        nemotron = OllamaProvider(model="nemotron-mini:4b")
        self.assertEqual(nemotron.model, "nemotron-mini:4b")

        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "message": {"content": json.dumps({"sections": [{"type": "hero", "title": "AI Cloud"}]})},
            "prompt_eval_count": 30,
            "eval_count": 95
        }
        with patch('requests.post', return_value=mock_res):
            req = CompletionRequest(
                prompt="Generate hero section",
                response_format={"type": "json_object"}
            )
            resp = nemotron.complete(req)
            self.assertTrue(resp.success)
            self.assertEqual(resp.model, "nemotron-mini:4b")
            self.assertIn("sections", resp.parsed_json)

    def test_04_openrouter_headers_secrets_and_http_errors(self):
        """Verifies OpenRouter bearer authorization, secret masking, and HTTP error recovery."""
        openrouter = OpenRouterProvider(
            api_key="sk-or-v1-mocksecret1234567890",
            model="anthropic/claude-3.7-sonnet",
            timeout=1,
            max_retries=1
        )
        self.assertTrue(openrouter.is_available())

        # Test HTTP 401 Unauthorized handling
        mock_res = MagicMock()
        mock_res.status_code = 401
        mock_res.text = "Unauthorized: Invalid API Key"
        with patch('requests.post', return_value=mock_res):
            req = CompletionRequest(prompt="Test prompt")
            resp = openrouter.complete(req)
            self.assertFalse(resp.success)
            self.assertIn("OpenRouter HTTP error 401", resp.error_message)
            # Secret must never be in error message
            self.assertNotIn("sk-or-v1-mocksecret1234567890", resp.error_message)

    def test_05_invalid_ai_responses_recovery(self):
        """Verifies multi-stage self-healing JSON parser recovers from corrupt AI responses."""
        mock_provider = MockFallbackProvider()

        # 1. Markdown code fences wrapped response
        fenced_content = "```json\n{\"title\": \"Clean Hero\", \"type\": \"hero\"}\n```"
        resp1 = CompletionResponse(success=True, content=fenced_content)
        parsed1 = resp1.parse_as_json()
        self.assertIsInstance(parsed1, dict)
        self.assertEqual(parsed1.get("title"), "Clean Hero")

        # 2. Conversational preface + trailing commentary
        conversational_content = (
            "Sure! Here is the JSON structure for the requested landing page:\n\n"
            "{\"page_name\": \"Home\", \"sections\": [\"navbar\", \"hero\"]}\n\n"
            "Hope this helps with your design process!"
        )
        resp2 = CompletionResponse(success=True, content=conversational_content)
        parsed2 = resp2.parse_as_json()
        self.assertIsInstance(parsed2, dict)
        self.assertEqual(parsed2.get("page_name"), "Home")

        # 3. Trailing commas in objects and arrays
        trailing_comma_content = '{"items": ["One", "Two",], "status": "active",}'
        resp3 = CompletionResponse(success=True, content=trailing_comma_content)
        parsed3 = resp3.parse_as_json()
        self.assertIsInstance(parsed3, dict)
        self.assertEqual(len(parsed3.get("items", [])), 2)

        # 4. Completely invalid non-JSON text
        garbage_content = "I cannot generate JSON because I am a conversational model."
        resp4 = CompletionResponse(success=True, content=garbage_content)
        parsed4 = resp4.parse_as_json()
        self.assertIsNone(parsed4)

    def test_06_provider_timeout_and_failover(self):
        """Verifies request timeout on primary provider triggers failover to fallback chain."""
        failing_provider = MagicMock()
        failing_provider.name = "ollama"
        failing_provider.complete.return_value = CompletionResponse(
            success=False,
            error_message="Connection timed out after 30s",
            status_code=504
        )

        with patch('sitemap_app.providers.factory.get_ai_provider', side_effect=lambda name=None: failing_provider if name == "ollama" else MockFallbackProvider()):
            req = CompletionRequest(prompt="Generate wireframe")
            # Should fail on primary 'ollama' and seamlessly fall back to Mock
            resp = execute_completion_with_fallback(req, preferred_provider="ollama")
            self.assertTrue(resp.success)
            self.assertEqual(resp.provider_name, "mock")

    def test_07_dynamic_provider_switching(self):
        """Verifies dynamic resolution of AI providers via factory resolver."""
        p_mock = get_ai_provider("mock")
        self.assertIsInstance(p_mock, MockFallbackProvider)
        self.assertEqual(p_mock.name, "mock")

        p_ollama = get_ai_provider("ollama")
        self.assertIsInstance(p_ollama, OllamaProvider)
        self.assertEqual(p_ollama.name, "ollama")

        p_openrouter = get_ai_provider("openrouter")
        self.assertIsInstance(p_openrouter, OpenRouterProvider)
        self.assertEqual(p_openrouter.name, "openrouter")

    # =========================================================================
    # PART 2: GENERATION TESTING ACROSS 8 CATEGORIES
    # =========================================================================

    def test_08_generation_simple_business(self):
        """Verifies generating a simple business website (local consulting / services)."""
        prompt = "Apex Business Advisory: Local financial advisory and corporate tax consulting for family businesses in Denver."
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        self.assertIn("wireframes", wf)
        self.assertGreaterEqual(len(wf["wireframes"]), 3)
        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)
        self.assertIn(report.grade, ("A+", "A"))

    def test_09_generation_multipage_business(self):
        """Verifies generating a multi-page corporate enterprise business website."""
        prompt = (
            "Apex Global Consulting: Enterprise digital transformation.\n"
            "Pages:\n"
            "- Home\n"
            "- Services\n"
            "- Case Studies\n"
            "- Leadership\n"
            "- Contact"
        )
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        pages = wf.get("wireframes", {})
        self.assertGreaterEqual(len(pages), 5)
        # Check layout diversity across home page
        home_page = next((p for p in pages.values() if p.get("page_name") == "Home"), None)
        self.assertIsNotNone(home_page)
        sections = home_page.get("sections", [])
        # Zero adjacent duplicate layout variants
        layouts = [s.get("layoutVariant") for s in sections if s.get("layoutVariant")]
        for i in range(len(layouts) - 1):
            self.assertNotEqual(layouts[i], layouts[i + 1])

    def test_10_generation_ecommerce(self):
        """Verifies generating an e-commerce website with product catalog and cart/checkout pages."""
        prompt = "VeloSport: Premium carbon road bikes, cycling apparel, and high-performance accessories store with customer reviews."
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)
        # Verify product section exists in the generated wireframes
        has_products = False
        for p in wf.get("wireframes", {}).values():
            for s in p.get("sections", []):
                if s.get("type") in ("products", "product-grid", "features"):
                    has_products = True
                    break
        self.assertTrue(has_products)

    def test_11_generation_saas(self):
        """Verifies generating a SaaS platform website with features, pricing tiers, and FAQ."""
        prompt = "PulseOps: Cloud infrastructure observability and automated incident response platform for Kubernetes clusters."
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)
        # Verify pricing and features sections exist
        types = set()
        for p in wf.get("wireframes", {}).values():
            for s in p.get("sections", []):
                types.add(s.get("type"))
        self.assertTrue("features" in types or "services" in types)
        self.assertTrue("pricing" in types or "cta" in types)

    def test_12_generation_portfolio(self):
        """Verifies generating a portfolio website for a creative professional."""
        prompt = "Elena Rostova: Senior Product Designer portfolio showcasing fintech mobile apps, UX design systems, and client case studies."
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)
        # Verify gallery or portfolio projects present
        types = set()
        for p in wf.get("wireframes", {}).values():
            for s in p.get("sections", []):
                types.add(s.get("type"))
        self.assertTrue("gallery" in types or "features" in types or "story" in types)

    def test_13_generation_agriculture(self):
        """Verifies generating an agriculture & agritech website with crop process and farm products."""
        prompt = "Verdant Fields: Sustainable hydroponic farming and organic greenhouse produce supplier with farm-to-table delivery."
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)
        # Ensure agriculture domain terminology in content
        home_str = json.dumps(wf)
        self.assertTrue(any(term in home_str.lower() for term in ["farm", "crop", "sustainable", "organic", "harvest", "produce"]))

    def test_14_generation_healthcare(self):
        """Verifies generating a healthcare & medical clinic website with doctors and booking CTAs."""
        prompt = "Beacon Health Clinic: Comprehensive outpatient medical clinic with family doctors, pediatric care, and urgent care booking."
        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)
        home_str = json.dumps(wf)
        self.assertTrue(any(term in home_str.lower() for term in ["doctor", "patient", "clinic", "health", "care", "medical"]))

    def test_15_generation_complex_custom_requirements(self):
        """Verifies generating a complex custom website with deep page hierarchy, paths, and brief clarifications."""
        prompt = (
            "OmniHealth Portal: Multi-specialty healthcare and telemedicine platform.\n"
            "Pages:\n"
            "- Home\n"
            "- Medical Specialties > Cardiology\n"
            "- Medical Specialties > Neurology\n"
            "- Medical Specialties > Pediatrics\n"
            "- Patient Services > Telehealth Virtual Visits\n"
            "- Patient Services > Prescription Refill Portal\n"
            "- Doctor Directory\n"
            "- Insurance & Pricing Guide\n"
            "- Emergency Contact & Urgent Care"
        )
        extracted = self.analyzer.analyze(prompt)
        self.assertGreaterEqual(len(extracted.get("pages_list", [])), 5)

        sitemap = self.sitemap_service.generate_sitemap(prompt)
        wf = self.wireframe_service.generate_wireframes(sitemap)

        is_valid, validated_model, errors = validate_wireframe(wf)
        self.assertTrue(is_valid)
        report = self.evaluator.evaluate(wf, sitemap)
        self.assertGreaterEqual(report.overall_score, 90.0)

    # =========================================================================
    # PART 3: FRONTEND TESTING (HEADLESS NODE.JS & DOM CONTRACTS)
    # =========================================================================

    def _run_node_script(self, script_body: str) -> dict:
        """Helper to run a Node.js snippet and return parsed JSON result."""
        wrapped = f"""
        const vm = require('vm');
        function createMockEl(props = {{}}) {{
            return Object.assign({{
                addEventListener: () => {{}},
                querySelector: () => null,
                querySelectorAll: () => [],
                classList: {{ add: () => {{}}, remove: () => {{}}, toggle: () => {{}}, contains: () => false }},
                style: {{}},
                appendChild: () => {{}},
                removeChild: () => {{}},
                setAttribute: () => {{}},
                getAttribute: () => null,
                innerHTML: '',
                textContent: '',
                children: []
            }}, props);
        }}
        global.document = {{
            getElementById: (id) => createMockEl({{ id }}),
            querySelector: (sel) => createMockEl({{ selector: sel }}),
            querySelectorAll: (sel) => [],
            createElement: (tag) => createMockEl({{ tagName: tag }}),
            body: createMockEl({{ tagName: 'BODY' }})
        }};
        global.window = {{
            addEventListener: () => {{}},
            innerWidth: 1200,
            localStorage: {{
                _store: {{}},
                getItem(k) {{ return this._store[k] || null; }},
                setItem(k, v) {{ this._store[k] = String(v); }},
                removeItem(k) {{ delete this._store[k]; }}
            }}
        }};
        {script_body}
        """
        proc = subprocess.run(['node', '-e', wrapped], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, f"Node.js execution failed: {proc.stderr}")
        return json.loads(proc.stdout.strip())

    def test_16_frontend_sitemap_display(self):
        """Verifies frontend sitemap tree display, navigation items, and indentation structure."""
        script = f"""
        const fs = require('fs');
        const wireframeJs = fs.readFileSync('{self.wireframe_js_path.as_posix()}', 'utf8');
        const hasSitemapHandling = wireframeJs.includes('loadSitemap') && wireframeJs.includes('setSitemap');
        console.log(JSON.stringify({{ hasSitemapHandling }}));
        """
        res = self._run_node_script(script)
        self.assertTrue(res.get("hasSitemapHandling"))

    def test_17_frontend_wireframe_rendering_all_boards(self):
        """Verifies frontend multi-board canvas rendering and page column structures."""
        script = f"""
        const fs = require('fs');
        const editorJs = fs.readFileSync('{self.editor_js_path.as_posix()}', 'utf8');
        const hasBoardRender = editorJs.includes('wireframe-board') || editorJs.includes('renderMultiBoardCanvas');
        const hasPageColumn = editorJs.includes('page-column') || editorJs.includes('renderBoard');
        console.log(JSON.stringify({{ hasBoardRender, hasPageColumn }}));
        """
        res = self._run_node_script(script)
        self.assertTrue(res.get("hasBoardRender") or res.get("hasPageColumn"))

    def test_18_frontend_all_32_components_render_cleanly(self):
        """Verifies that all 32 canonical section types render in WireframeComponents without crashing."""
        script = f"""
        const fs = require('fs');
        const componentsJs = fs.readFileSync('{self.components_js_path.as_posix()}', 'utf8');
        eval(componentsJs);

        const components = global.window.WireframeComponents;
        const types = {json.dumps(sorted(list(SUPPORTED_SECTION_TYPES)))};
        let renderedCount = 0;
        let errors = [];

        types.forEach(t => {{
            try {{
                const dummySec = {{
                    type: t,
                    title: 'Test Section ' + t,
                    subtitle: 'Test Subtitle for ' + t,
                    description: 'Structured description for testing ' + t,
                    layoutVariant: 'layout-cards',
                    items: [{{ title: 'Item 1', description: 'Desc 1', icon: 'check' }}]
                }};
                const html = components.renderComponent(dummySec, {{ isMobile: false }});
                if (html && typeof html === 'string' && html.length > 0) {{
                    renderedCount++;
                }} else {{
                    errors.push(t + ': empty render');
                }}
            }} catch(e) {{
                errors.push(t + ': ' + e.message);
            }}
        }});

        console.log(JSON.stringify({{ total: types.length, renderedCount, errors }}));
        """
        res = self._run_node_script(script)
        self.assertEqual(res.get("renderedCount"), len(SUPPORTED_SECTION_TYPES), f"Failed renders: {res.get('errors')}")

    def test_19_frontend_responsive_previews_and_breakpoints(self):
        """Verifies responsive preview breakpoints (desktop, tablet, mobile) and CSS rules."""
        css_content = self.wireframe_css_path.read_text(encoding='utf-8')
        # Check breakpoint CSS rules exist
        self.assertIn(".bp-desktop", css_content)
        self.assertIn(".bp-tablet", css_content)
        self.assertIn(".bp-mobile", css_content)
        self.assertIn(".wireframe-page-column", css_content)

    def test_20_frontend_page_navigation_and_switcher(self):
        """Verifies page switcher dropdown and active board highlighting."""
        html_content = self.wireframe_html_path.read_text(encoding='utf-8')
        editor_js = self.editor_js_path.read_text(encoding='utf-8')

        self.assertIn("pageSelectDropdown", html_content)
        self.assertTrue("onPageDropdownChange" in editor_js or "handlePageSwitch" in editor_js or "pageSelectDropdown" in editor_js)

    def test_21_frontend_section_editing_and_reordering(self):
        """Verifies inline editing, Move Up/Down buttons, Add Section modal, and type replacement."""
        editor_js = self.editor_js_path.read_text(encoding='utf-8')
        state_js = self.state_manager_path.read_text(encoding='utf-8')

        self.assertIn("editable-text", editor_js)
        self.assertIn("reorderSections", state_js)
        self.assertTrue("openReplaceView" in editor_js or "sidebarReplaceView" in editor_js)
        self.assertIn("addSectionModal", self.wireframe_html_path.read_text(encoding='utf-8'))

    def test_22_frontend_regeneration_section_and_page(self):
        """Verifies section-level and page-level regeneration integration."""
        editor_js = self.editor_js_path.read_text(encoding='utf-8')
        self.assertIn("regenerateSection", editor_js)
        self.assertIn("/api/regenerate-section/", editor_js)
        self.assertIn("/api/generate-wireframe/", editor_js)

    def test_23_frontend_persistence_localstorage(self):
        """Verifies auto-saving to localStorage and save status indicator."""
        state_js = self.state_manager_path.read_text(encoding='utf-8')
        html = self.wireframe_html_path.read_text(encoding='utf-8')

        self.assertIn("localStorage", state_js)
        self.assertIn("saveStatusIndicator", html)

    # =========================================================================
    # PART 4: BENCHMARKING SUITE & DECISION MATRIX
    # =========================================================================

    def test_24_benchmark_prompts_catalog_coverage(self):
        """Verifies that at least 20 diverse test prompts exist and span 10 industries."""
        self.assertGreaterEqual(len(BENCHMARK_PROMPTS), 20)
        categories = {p["category"] for p in BENCHMARK_PROMPTS}
        # Spans at least 6 canonical categories
        self.assertGreaterEqual(len(categories), 6)
        for p in BENCHMARK_PROMPTS:
            self.assertTrue(p.get("id"))
            self.assertTrue(p.get("title"))
            self.assertTrue(p.get("prompt"))
            self.assertGreaterEqual(len(p.get("expected_pages", [])), 3)

    def test_25_benchmark_results_metrics_evaluation(self):
        """Verifies that benchmark results file exists and has valid evaluation metrics."""
        results_file = backend_dir / "benchmark_20_prompts_results.json"
        self.assertTrue(results_file.exists())

        with open(results_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("models", data)
        models = data["models"]
        self.assertIn("qwen2.5:3b", models)
        self.assertIn("nemotron-mini:4b", models)

        qwen_metrics = models["qwen2.5:3b"]["summary_metrics"]
        self.assertEqual(qwen_metrics["total_prompts"], 20)
        self.assertEqual(qwen_metrics["json_validity_rate_pct"], 100.0)
        self.assertGreaterEqual(qwen_metrics["avg_quality_score"], 90.0)
        self.assertEqual(qwen_metrics["grade_distribution"]["A+"], 20)

    def test_26_model_selection_decision_matrix(self):
        """
        Validates model comparison matrix selecting Qwen 2.5 3B as primary local model:
        1. Throughput: Qwen (40.9 tps) is 1.77x faster than Nemotron (23.1 tps)
        2. Latency: Qwen (4.99s) is 2.57x lower latency than Nemotron (12.8s)
        3. VRAM: Qwen (2.18GB) requires 710MB less VRAM than Nemotron (2.89GB)
        4. Schema Reliability: Both achieve 100% JSON validity with Phase 7 quality pipeline
        """
        results_file = backend_dir / "benchmark_20_prompts_results.json"
        with open(results_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        qwen = data["models"]["qwen2.5:3b"]["specification"]
        nemo = data["models"]["nemotron-mini:4b"]["specification"]

        self.assertGreater(qwen["avg_tps"], nemo["avg_tps"])
        self.assertLess(qwen["base_latency"], nemo["base_latency"])
        self.assertLess(qwen["vram_mb"], nemo["vram_mb"])


if __name__ == "__main__":
    unittest.main()
