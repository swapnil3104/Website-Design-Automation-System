"""
backend/tests/test_phase9_stabilization.py
Phase 9 — Final Stabilization & Documentation Test Suite

Validates:
1. Dead code removal & dependency cleanliness (no openai requirement, no obsolete imports)
2. All 8 REST API endpoints return robust standard JSON envelopes with try/except protection
3. Database model definitions and schemas (Sitemap and Page models, initial migration)
4. Environment configuration safety & secret sanitization
5. Frontend asset integrity & script hierarchy consistency
6. Django core system check validation
"""

import os
import sys
import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from rest_framework.test import APIRequestFactory

from core.config import config
from sitemap_app.models import Sitemap, Page
from sitemap_app.schemas import (
    SitemapModel,
    WireframeContainerModel,
    SUPPORTED_SECTION_TYPES,
)
from sitemap_app.views import (
    get_config,
    init_brief,
    generate_sitemap,
    update_sitemap,
    export_json,
    generate_wireframe,
    regenerate_section,
    evaluate_quality,
)


class TestPhase9Stabilization(unittest.TestCase):
    """System-wide stabilization, security, and integrity verification suite."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.prev_provider = os.environ.get('AI_PROVIDER')
        os.environ['AI_PROVIDER'] = 'mock'

    def tearDown(self):
        if self.prev_provider is not None:
            os.environ['AI_PROVIDER'] = self.prev_provider
        else:
            os.environ.pop('AI_PROVIDER', None)

    # -------------------------------------------------------------------------
    # 1. Dependency and Dead Code Verification
    # -------------------------------------------------------------------------
    def test_requirements_file_cleanliness(self):
        """Verify requirements.txt contains only necessary packages (no unused openai)."""
        req_path = self.base_dir / "backend" / "requirements.txt"
        self.assertTrue(req_path.exists(), "backend/requirements.txt must exist")
        
        content = req_path.read_text(encoding='utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
        
        # Check essential dependencies
        self.assertTrue(any(line.startswith('Django') for line in lines))
        self.assertTrue(any(line.startswith('djangorestframework') for line in lines))
        self.assertTrue(any(line.startswith('pydantic') for line in lines))
        self.assertTrue(any(line.startswith('requests') for line in lines))
        self.assertTrue(any(line.startswith('django-cors-headers') for line in lines))
        
        # Verify unused openai is eliminated
        self.assertFalse(any(line.startswith('openai') for line in lines), "openai is obsolete and should not be in requirements.txt")

    def test_services_py_clean_imports(self):
        """Verify backend/sitemap_app/services.py does not import openai."""
        services_path = self.base_dir / "backend" / "sitemap_app" / "services.py"
        self.assertTrue(services_path.exists())
        content = services_path.read_text(encoding='utf-8')
        self.assertNotIn("from openai import", content)
        self.assertNotIn("import openai", content)

    def test_patch_html_archived(self):
        """Verify patch_html.py is archived and contains no executable code."""
        patch_path = self.base_dir / "patch_html.py"
        if patch_path.exists():
            content = patch_path.read_text(encoding='utf-8')
            self.assertIn("Archived", content)
            self.assertNotIn("with open('frontend/wireframe.html'", content)

    # -------------------------------------------------------------------------
    # 2. Database Models and Persistence Schema
    # -------------------------------------------------------------------------
    def test_sitemap_model_instantiation_and_str(self):
        """Verify Sitemap model fields, attributes, and __str__ representation."""
        test_payload = {
            "website_type": "Healthcare Clinic",
            "pages": [{"id": "p1", "name": "Home", "sections": []}]
        }
        sitemap = Sitemap(
            prompt="A modern dental clinic in Seattle",
            website_type="Healthcare",
            sitemap_data=test_payload
        )
        sitemap.created_at = datetime(2026, 11, 4)
        self.assertEqual(sitemap.website_type, "Healthcare")
        self.assertEqual(sitemap.sitemap_data["website_type"], "Healthcare Clinic")
        self.assertEqual(str(sitemap), "Healthcare - 2026-11-04")

    def test_page_model_instantiation_and_hierarchy(self):
        """Verify Page model fields, relationships, and __str__ representation."""
        sitemap = Sitemap(
            prompt="Test Site",
            website_type="Agency",
            sitemap_data={"website_type": "Agency", "pages": []}
        )
        parent_page = Page(
            sitemap=sitemap,
            page_id="p-services",
            name="Services",
            description="Our primary services list",
            order=1
        )
        child_page = Page(
            sitemap=sitemap,
            page_id="p-seo",
            name="SEO Optimization",
            description="Detailed SEO service description",
            parent=parent_page,
            order=2
        )
        self.assertEqual(child_page.parent, parent_page)
        self.assertEqual(child_page.sitemap, sitemap)
        self.assertEqual(str(parent_page), "Services")
        self.assertEqual(str(child_page), "SEO Optimization")

    def test_migration_files_present(self):
        """Verify initial migration exists for sitemap_app."""
        mig_path = self.base_dir / "backend" / "sitemap_app" / "migrations" / "0001_initial.py"
        self.assertTrue(mig_path.exists(), "0001_initial.py migration must exist")
        content = mig_path.read_text(encoding='utf-8')
        self.assertIn("CreateModel", content)
        self.assertIn("Sitemap", content)
        self.assertIn("Page", content)

    # -------------------------------------------------------------------------
    # 3. Environment & Configuration Safety
    # -------------------------------------------------------------------------
    def test_env_example_completeness_and_safety(self):
        """Verify .env.example contains configuration keys without real secret values."""
        example_path = self.base_dir / "backend" / ".env.example"
        self.assertTrue(example_path.exists())
        content = example_path.read_text(encoding='utf-8')
        
        required_keys = [
            "AI_PROVIDER",
            "OLLAMA_BASE_URL",
            "OLLAMA_MODEL",
            "OPENROUTER_API_KEY",
            "OPENROUTER_MODEL",
            "DEBUG"
        ]
        for key in required_keys:
            self.assertIn(key, content)

        # Ensure no real production key was placed in example
        self.assertNotIn("sk-or-v1-real", content)

    def test_api_config_endpoint_sanitization(self):
        """Verify GET /api/config/ returns sanitized configuration without secrets."""
        req = self.factory.get('/api/config/')
        resp = get_config(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIsNone(data.get('private_key'), "Private key must be sanitized to None")
        self.assertIn('provider', data)
        self.assertIn('ai', data)

    # -------------------------------------------------------------------------
    # 4. REST API Endpoint Robustness & Exception Envelopes
    # -------------------------------------------------------------------------
    def test_init_brief_endpoint(self):
        """Verify POST /api/init-brief/ returns structured response."""
        req = self.factory.post('/api/init-brief/', {"prompt": "A modern boutique coffee roaster"}, format="json")
        resp = init_brief(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('questions', data)
        self.assertIn('parsed', data)

    def test_generate_sitemap_endpoint(self):
        """Verify POST /api/generate-sitemap/ returns valid sitemap."""
        req = self.factory.post(
            '/api/generate-sitemap/',
            {"prompt": "SaaS analytics platform with pricing and docs"},
            format="json"
        )
        resp = generate_sitemap(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('sitemap', data)
        self.assertIn('pages', data['sitemap'])

    def test_update_sitemap_endpoint(self):
        """Verify POST /api/update-sitemap/ validates schema and returns standard response."""
        valid_sitemap = {
            "sitemap_data": {
                "website_type": "Corporate",
                "brief": {"category": "business"},
                "pages": [
                    {
                        "id": "p-home",
                        "name": "Home",
                        "sections": [{"id": "s-nav", "type": "navbar", "title": "Navbar"}]
                    }
                ]
            }
        }
        req = self.factory.post('/api/update-sitemap/', valid_sitemap, format="json")
        resp = update_sitemap(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertEqual(data['sitemap']['website_type'], "Corporate")

    def test_update_sitemap_invalid_payload(self):
        """Verify POST /api/update-sitemap/ rejects invalid data with HTTP 400."""
        req = self.factory.post('/api/update-sitemap/', {"sitemap_data": "not a dictionary"}, format="json")
        resp = update_sitemap(req)
        self.assertEqual(resp.status_code, 400)
        data = resp.data
        self.assertFalse(data.get('success'))
        self.assertIn('errors', data)

    def test_export_json_endpoint(self):
        """Verify POST /api/export-json/ delivers valid downloadable JSON attachment."""
        sample_data = {"website_type": "Agency", "pages": []}
        req = self.factory.post('/api/export-json/', {"sitemap_data": sample_data}, format="json")
        resp = export_json(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertIn('attachment; filename="sitemap.json"', resp['Content-Disposition'])

    def test_generate_wireframe_endpoint(self):
        """Verify POST /api/generate-wireframe/ generates complete wireframes."""
        sample_sitemap = {
            "website_type": "SaaS Platform",
            "brief": {"category": "saas"},
            "pages": [
                {
                    "id": "p-home",
                    "name": "Home",
                    "sections": [
                        {"id": "s1", "type": "navbar", "title": "Navigation"},
                        {"id": "s2", "type": "hero", "title": "Hero Section"},
                        {"id": "s3", "type": "pricing", "title": "Pricing Plans"},
                        {"id": "s4", "type": "footer", "title": "Footer"}
                    ]
                }
            ]
        }
        req = self.factory.post('/api/generate-wireframe/', {"sitemap_data": sample_sitemap}, format="json")
        resp = generate_wireframe(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('wireframes', data)
        self.assertIn('wireframes', data['wireframes'])
        self.assertIn('p-home', data['wireframes']['wireframes'])

    def test_generate_wireframe_missing_payload(self):
        """Verify POST /api/generate-wireframe/ returns HTTP 400 when missing payload."""
        req = self.factory.post('/api/generate-wireframe/', {}, format="json")
        resp = generate_wireframe(req)
        self.assertEqual(resp.status_code, 400)
        data = resp.data
        self.assertFalse(data.get('success'))

    def test_regenerate_section_endpoint(self):
        """Verify POST /api/regenerate-section/ returns regenerated section."""
        payload = {
            "title": "Interactive Features Grid",
            "type": "features",
            "page_context": {"name": "Home", "category": "saas"}
        }
        req = self.factory.post('/api/regenerate-section/', payload, format="json")
        resp = regenerate_section(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('section', data)
        self.assertEqual(data['section']['type'], 'features')

    def test_evaluate_quality_endpoint(self):
        """Verify POST /api/evaluate-quality/ returns 8-dimension report."""
        sample_wireframe = {
            "website_type": "Agency",
            "pages": [
                {
                    "id": "p-home",
                    "name": "Home",
                    "sections": [
                        {"id": "s1", "type": "navbar", "title": "Navigation"},
                        {"id": "s2", "type": "hero", "title": "Hero Section", "layoutVariant": "layout-split"},
                        {"id": "s3", "type": "features", "title": "Services", "layoutVariant": "layout-cards"},
                        {"id": "s4", "type": "footer", "title": "Footer"}
                    ]
                }
            ]
        }
        req = self.factory.post('/api/evaluate-quality/', {"wireframe_data": sample_wireframe}, format="json")
        resp = evaluate_quality(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('report', data)
        self.assertIn('overall_score', data['report'])
        self.assertIn('grade', data['report'])

    # -------------------------------------------------------------------------
    # 5. Frontend Asset & Hierarchy Consistency
    # -------------------------------------------------------------------------
    def test_frontend_files_and_scripts_presence(self):
        """Verify all HTML and JS core assets exist."""
        expected_files = [
            "frontend/index.html",
            "frontend/chat.html",
            "frontend/wireframe.html",
            "frontend/css/style.css",
            "frontend/css/wireframe.css",
            "frontend/css/chat.css",
            "frontend/js/app.js",
            "frontend/js/chat.js",
            "frontend/js/state-manager.js",
            "frontend/js/wireframe-icons.js",
            "frontend/js/wireframe-components.js",
            "frontend/js/wireframe-editor.js",
            "frontend/js/wireframe.js",
        ]
        for f in expected_files:
            file_path = self.base_dir / f
            self.assertTrue(file_path.exists(), f"Frontend asset {f} must exist")

    def test_html_script_tag_hierarchies(self):
        """Verify wireframe.html and index.html include state-manager and wireframe-components."""
        wf_html = (self.base_dir / "frontend" / "wireframe.html").read_text(encoding='utf-8')
        idx_html = (self.base_dir / "frontend" / "index.html").read_text(encoding='utf-8')

        for script in ["state-manager.js", "wireframe-icons.js", "wireframe-components.js", "wireframe-editor.js"]:
            self.assertIn(script, wf_html, f"wireframe.html must include {script}")
            self.assertIn(script, idx_html, f"index.html must include {script}")

    # -------------------------------------------------------------------------
    # 6. Django Core System Check
    # -------------------------------------------------------------------------
    def test_django_system_check_zero_errors(self):
        """Run standard Django check to verify zero model, url, or setting errors."""
        try:
            call_command('check')
        except Exception as e:
            self.fail(f"Django system check failed: {e}")


if __name__ == '__main__':
    unittest.main()
