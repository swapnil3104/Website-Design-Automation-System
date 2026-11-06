"""
backend/tests/test_api_integration.py
Integration tests for Django REST API endpoints with the AI provider subsystem.
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import unittest
from rest_framework.test import APIRequestFactory
from sitemap_app.views import get_config, init_brief, generate_sitemap, generate_wireframe, regenerate_section
from core.config import config


class TestAPIEndpointsIntegration(unittest.TestCase):
    """Verifies that API views function seamlessly with providers and never expose secrets."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.prev_provider = os.environ.get('AI_PROVIDER')
        os.environ['AI_PROVIDER'] = 'mock'

    def tearDown(self):
        if self.prev_provider is not None:
            os.environ['AI_PROVIDER'] = self.prev_provider
        else:
            os.environ.pop('AI_PROVIDER', None)

    def test_get_config_does_not_expose_secrets(self):
        req = self.factory.get('/api/config/')
        resp = get_config(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        # Key assertions for secret protection:
        self.assertIsNone(data.get('private_key'))
        self.assertNotIn('sk-or-v1', str(data))
        self.assertIn('provider', data)
        self.assertIn('active_provider', data)
        self.assertIn('ai', data)

    def test_init_brief_generation(self):
        payload = {
            "prompt": "Create an e-commerce website for bespoke handmade leather goods",
            "ai_enabled": True
        }
        req = self.factory.post('/api/init-brief/', payload, format='json')
        resp = init_brief(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('questions', data)
        self.assertTrue(len(data['questions']) > 0)
        self.assertIn('parsed', data)
        self.assertIn(data['parsed'].get('type'), ['Ecommerce Website', 'E-commerce Website'])

    def test_generate_sitemap(self):
        payload = {
            "prompt": "A modern portfolio for a freelance 3D motion designer",
            "brief_data": {
                "type": "Portfolio Website",
                "client": "Nova Studios"
            }
        }
        req = self.factory.post('/api/generate-sitemap/', payload, format='json')
        resp = generate_sitemap(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        sitemap = data.get('sitemap')
        self.assertIsNotNone(sitemap)
        self.assertIn('pages', sitemap)
        self.assertTrue(len(sitemap['pages']) >= 3)

    def test_generate_wireframe(self):
        sitemap_payload = {
            "sitemap_data": {
                "website_type": "SaaS Platform",
                "brief": {"client": "CloudSync", "goals": "Streamline devops"},
                "pages": [
                    {
                        "id": "p-home",
                        "name": "Home",
                        "path": "/",
                        "description": "Main landing page",
                        "sections": [
                            {"id": "sec-1", "type": "navbar", "title": "Navbar"},
                            {"id": "sec-2", "type": "hero", "title": "Hero Banner"},
                            {"id": "sec-3", "type": "features", "title": "Features Grid"},
                            {"id": "sec-4", "type": "footer", "title": "Footer"}
                        ]
                    }
                ]
            }
        }
        req = self.factory.post('/api/generate-wireframe/', sitemap_payload, format='json')
        resp = generate_wireframe(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('wireframes', data)
        wireframes = data['wireframes']
        self.assertIn('wireframes', wireframes)
        self.assertTrue('p-home' in wireframes['wireframes'] or 'Home' in wireframes['wireframes'])
        home_key = 'p-home' if 'p-home' in wireframes['wireframes'] else 'Home'
        home_wireframe = wireframes['wireframes'][home_key]
        self.assertIn('sections', home_wireframe)
        self.assertTrue(len(home_wireframe['sections']) >= 3)


if __name__ == "__main__":
    unittest.main()
