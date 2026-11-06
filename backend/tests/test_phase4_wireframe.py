"""
backend/tests/test_phase4_wireframe.py
Comprehensive Unit & Integration Test Suite for Phase 4 — AI Wireframe Generation Engine.
Tests Pydantic v2 schemas, auto-repair, page planning, AI generation, JSON self-healing,
deterministic fallbacks, multi-page wireframes, and REST API endpoints.
"""

import os
import sys
import json
import uuid
from typing import Dict, Any, List
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

os.environ['AI_PROVIDER'] = 'mock'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status

from core.config import config
from sitemap_app.views import generate_wireframe, regenerate_section
from sitemap_app.page_planner import (
    PagePlanner,
    PagePlan,
    PlannedSectionBlueprint,
)
from sitemap_app.providers.base import (
    BaseAIProvider,
    CompletionRequest,
    CompletionResponse,
)
from sitemap_app.providers.mock_provider import MockFallbackProvider
from sitemap_app.schemas.wireframe import (
    SectionItemModel,
    SectionStylesModel,
    ResponsiveSettingsModel,
    WireframeSectionModel,
    PageWireframeModel,
    WireframeContainerModel,
    SUPPORTED_LAYOUT_VARIANTS,
    LAYOUT_VARIANT_ALIASES,
    DEFAULT_ITEMS_BY_SECTION_TYPE,
    repair_wireframe_item,
    repair_wireframe_section,
    repair_page_wireframe,
    repair_wireframe_container,
    validate_wireframe,
    validate_page_wireframe,
)
from sitemap_app.wireframe_service import (
    WireframeService,
    _attempt_json_repair,
)
from sitemap_app.services import WireframeGenerator


class WireframePydanticSchemaTests(TestCase):
    """Tests Pydantic v2 validation models and auto-repair pipelines for wireframes."""

    def test_section_item_model_and_icon_normalization(self):
        """Test item fields, fallback titles, and Lucide icon normalization."""
        # Emoji icon conversion to Lucide token
        item = SectionItemModel.model_validate({
            'title': 'Fast Performance',
            'desc': 'Instant query latency across billions of records.',
            'icon': '⚡'
        })
        self.assertEqual(item.title, 'Fast Performance')
        self.assertEqual(item.desc, 'Instant query latency across billions of records.')
        self.assertEqual(item.icon, 'Zap')

        # Testimonial author title fallback
        review_item = SectionItemModel.model_validate({
            'name': 'Sarah Connor',
            'role': 'Director of Security',
            'quote': 'This system prevents all critical vulnerabilities.',
            'icon': '⭐'
        })
        self.assertEqual(review_item.title, 'Sarah Connor')
        self.assertEqual(review_item.quote, 'This system prevents all critical vulnerabilities.')
        self.assertEqual(review_item.icon, 'Star')

        # Pricing features list
        pricing_item = SectionItemModel.model_validate({
            'title': 'Enterprise Plan',
            'price': '$199/mo',
            'tag': 'Popular',
            'features': ['Dedicated Support', 'Custom SLA', 'SSO']
        })
        self.assertEqual(pricing_item.price, '$199/mo')
        self.assertEqual(len(pricing_item.features), 3)

    def test_section_styles_and_responsive_bounds(self):
        """Test style constraints and responsive breakpoint models."""
        styles = SectionStylesModel.model_validate({
            'padding': 64,
            'margin': 24,
            'fontSize': 18,
            'align': 'center',
            'theme': 'dark'
        })
        self.assertEqual(styles.padding, 64)
        self.assertEqual(styles.align, 'center')

        responsive = ResponsiveSettingsModel.model_validate({
            'columns_desktop': 4,
            'columns_tablet': 2,
            'columns_mobile': 1,
            'stack_on_mobile': True
        })
        self.assertEqual(responsive.columns_desktop, 4)
        self.assertTrue(responsive.stack_on_mobile)

    def test_wireframe_section_type_and_layout_aliasing(self):
        """Test section type aliasing and layout variant normalization."""
        sec = WireframeSectionModel.model_validate({
            'type': 'nav',  # alias for navbar
            'title': 'Main Nav',
            'layoutVariant': 'split-right',  # alias for layout-split-right
            'menuItems': ['Home', 'Features', 'Pricing', 'Contact']
        })
        self.assertEqual(sec.type, 'navbar')
        self.assertEqual(sec.layoutVariant, 'layout-split-right')
        self.assertIsNotNone(sec.id)
        self.assertEqual(len(sec.menuItems), 4)

    def test_repair_wireframe_section_empty_items_infilling(self):
        """Test that itemized sections (features, pricing, stats) automatically infill default items."""
        # Empty features section
        repaired_features = repair_wireframe_section({
            'type': 'features',
            'title': 'Key Highlights'
        })
        self.assertEqual(repaired_features['type'], 'features')
        self.assertEqual(repaired_features['layoutVariant'], 'layout-grid-3')
        self.assertTrue(len(repaired_features['items']) >= 3)
        self.assertIn('title', repaired_features['items'][0])
        self.assertIn('icon', repaired_features['items'][0])

        # Empty pricing section
        repaired_pricing = repair_wireframe_section({
            'type': 'pricing',
            'title': 'Subscription Tiers'
        })
        self.assertEqual(repaired_pricing['type'], 'pricing')
        self.assertTrue(len(repaired_pricing['items']) >= 3)
        self.assertIsNotNone(repaired_pricing['items'][0].get('price'))

        # Empty footer section
        repaired_footer = repair_wireframe_section({
            'type': 'footer'
        })
        self.assertEqual(repaired_footer['type'], 'footer')
        self.assertEqual(repaired_footer['layoutVariant'], 'layout-multi-column')
        self.assertTrue(len(repaired_footer['items']) >= 4)

    def test_repair_page_wireframe_mandatory_framing(self):
        """Test that every page gets a navbar at the top and footer at the bottom."""
        raw_page = {
            'page_name': 'About Us',
            'sections': [
                {'type': 'content', 'title': 'Our Team'}
            ]
        }
        repaired = repair_page_wireframe(raw_page, sitemap_menu_items=['Home', 'About', 'Contact'])
        sections = repaired['sections']
        self.assertTrue(len(sections) >= 3)
        self.assertEqual(sections[0]['type'], 'navbar')
        self.assertEqual(sections[-1]['type'], 'footer')
        self.assertEqual(repaired['page_name'], 'About Us')

    def test_repair_wireframe_container_hierarchy(self):
        """Test repairing a full wireframe container with nested sitemap pages."""
        sitemap = {
            'website_type': 'SaaS Platform',
            'brief': {'client': 'PulseMetrics', 'type': 'SaaS'},
            'pages': [
                {
                    'id': 'p1',
                    'name': 'Home',
                    'children': [
                        {'id': 'p2', 'name': 'Features', 'children': []},
                        {'id': 'p3', 'name': 'Pricing', 'children': []}
                    ]
                }
            ]
        }
        repaired_container = repair_wireframe_container({}, sitemap)
        self.assertEqual(repaired_container['website_type'], 'SaaS Platform')
        self.assertIn('p1', repaired_container['wireframes'])
        self.assertIn('p2', repaired_container['wireframes'])
        self.assertIn('p3', repaired_container['wireframes'])
        self.assertEqual(repaired_container['wireframes']['p2']['page_path'], 'Home/Features')

        # Validate with Pydantic
        is_valid, model, errors = validate_wireframe(repaired_container)
        self.assertTrue(is_valid, f"Validation errors: {errors}")


class PagePlanningTests(TestCase):
    """Tests PagePlanner category detection, section blueprints, ordering, and navigation consistency."""

    def setUp(self):
        self.planner = PagePlanner()
        self.sample_sitemap = {
            'website_type': 'FinTech Platform',
            'brief': {
                'client': 'AuraPay',
                'type': 'FinTech Payment Platform',
                'style': 'Clean, Minimalist',
                'tone': 'Authoritative'
            },
            'pages': [
                {'id': 'p1', 'name': 'Home'},
                {'id': 'p2', 'name': 'Services'},
                {'id': 'p3', 'name': 'Pricing'},
                {'id': 'p4', 'name': 'About'},
                {'id': 'p5', 'name': 'Contact'}
            ]
        }

    def test_page_category_detection(self):
        """Verify 10+ page category matchers."""
        test_cases = [
            ('Home Page', 'home'),
            ('About Our Company', 'about'),
            ('Consulting Services', 'services'),
            ('Cloud Migration Service Detail', 'service-detail'),
            ('Product Catalog', 'products'),
            ('Subscription Pricing', 'pricing'),
            ('Contact & Support', 'contact'),
            ('Client Portfolio & Work', 'portfolio'),
            ('Engineering Blog & News', 'blog'),
            ('Frequently Asked Questions', 'faq'),
            ('Search Flights & Bookings', 'booking-search'),
        ]
        for name, expected_cat in test_cases:
            cat = self.planner.detect_page_category(name)
            self.assertEqual(cat, expected_cat, f"Failed for name '{name}': got {cat}, expected {expected_cat}")

    def test_global_navigation_extraction(self):
        """Verify that top navigation links are extracted cleanly and deduplicated."""
        nav = self.planner.extract_global_navigation(self.sample_sitemap)
        self.assertIn('Home', nav)
        self.assertIn('Services', nav)
        self.assertIn('Pricing', nav)
        self.assertTrue(len(nav) <= 6)

    def test_plan_page_section_ordering(self):
        """Verify that sections are strictly ordered: navbar (0) first, hero (10) second, footer (100) last."""
        home_page = {'id': 'p1', 'name': 'Home', 'description': 'Main landing page'}
        plan = self.planner.plan_page(home_page, 'Home', self.sample_sitemap)

        self.assertEqual(plan.page_category, 'home')
        self.assertEqual(plan.page_name, 'Home')
        self.assertTrue(len(plan.conversion_goals) > 0)
        self.assertNotEqual(plan.primary_cta, '')

        section_types = [s.type for s in plan.sections]
        self.assertEqual(section_types[0], 'navbar')
        self.assertEqual(section_types[1], 'hero')
        self.assertEqual(section_types[-1], 'footer')

        # Check weights are monotonic
        weights = [self.planner.SECTION_ORDER_WEIGHTS.get(st, 50) for st in section_types]
        for i in range(len(weights) - 1):
            self.assertLessEqual(weights[i], weights[i + 1])


class WireframeServiceTests(TestCase):
    """Tests WireframeService generation, failover, JSON repair, and deterministic fallback."""

    def setUp(self):
        self.service = WireframeService()
        self.sitemap_data = {
            'website_type': 'SaaS Analytics',
            'brief': {
                'client': 'DataMesh',
                'type': 'B2B Data Platform',
                'services': ['Stream Ingestion', 'AI Dashboards'],
                'style': 'Technical, Modern',
                'tone': 'Developer-first'
            },
            'pages': [
                {
                    'id': 'home-01',
                    'name': 'Home',
                    'description': 'Main platform overview',
                    'sections': [
                        {'id': 's1', 'type': 'navbar', 'title': 'DataMesh'},
                        {'id': 's2', 'type': 'hero', 'title': 'Stream Data at Scale'},
                        {'id': 's3', 'type': 'features', 'title': 'Core Capabilities'},
                        {'id': 's4', 'type': 'cta', 'title': 'Deploy in 60s'},
                        {'id': 's5', 'type': 'footer', 'title': 'Footer'}
                    ]
                },
                {
                    'id': 'pricing-01',
                    'name': 'Pricing',
                    'description': 'Predictable tiers',
                    'sections': [
                        {'id': 's6', 'type': 'navbar', 'title': 'DataMesh'},
                        {'id': 's7', 'type': 'hero', 'title': 'Simple Pricing'},
                        {'id': 's8', 'type': 'pricing', 'title': 'Tiers'},
                        {'id': 's9', 'type': 'footer', 'title': 'Footer'}
                    ]
                }
            ]
        }

    def test_json_repair_heuristics(self):
        """Test heuristic repair on malformed, fenced, or truncated JSON responses."""
        # 1. Code fence removal
        fenced = "```json\n[{\"type\": \"hero\", \"title\": \"Welcome\"}]\n```"
        self.assertIsNotNone(_attempt_json_repair(fenced))

        # 2. Conversational prefix and suffix
        conversational = "Here is the wireframe structure you requested:\n[{\"type\": \"hero\", \"title\": \"Welcome\"}]\nHope this helps!"
        parsed = _attempt_json_repair(conversational)
        self.assertIsInstance(parsed, list)
        self.assertEqual(parsed[0]['title'], 'Welcome')

        # 3. Trailing commas
        trailing_comma = '[{"type": "features", "items": [{"title": "Fast",},],},]'
        parsed_tc = _attempt_json_repair(trailing_comma)
        self.assertIsInstance(parsed_tc, list)
        self.assertEqual(parsed_tc[0]['type'], 'features')

        # 4. Truncated closing brackets
        truncated = '[{"type": "hero", "title": "Welcome to DataMesh"'
        parsed_tr = _attempt_json_repair(truncated)
        self.assertIsInstance(parsed_tr, list)

    def test_ai_provider_mock_generation(self):
        """Test WireframeService using MockFallbackProvider."""
        mock_provider = MockFallbackProvider()
        service_with_mock = WireframeService(ai_provider=mock_provider)

        result = service_with_mock.generate_wireframes(self.sitemap_data)
        self.assertIn('wireframes', result)
        self.assertIn('home-01', result['wireframes'])
        self.assertIn('pricing-01', result['wireframes'])

        home_wf = result['wireframes']['home-01']
        self.assertEqual(home_wf['page_name'], 'Home')
        self.assertTrue(len(home_wf['sections']) >= 3)

        # Check navbar and footer framing
        self.assertEqual(home_wf['sections'][0]['type'], 'navbar')
        self.assertEqual(home_wf['sections'][-1]['type'], 'footer')

    def test_deterministic_fallback_when_ai_disabled(self):
        """Test deterministic fallback synthesis when config.chat_ai_enabled is False."""
        prev_enabled = os.environ.get('CHAT_AI_ENABLED')
        try:
            os.environ['CHAT_AI_ENABLED'] = 'false'
            result = self.service.generate_wireframes(self.sitemap_data)

            self.assertIn('wireframes', result)
            home_wf = result['wireframes']['home-01']
            self.assertEqual(home_wf['page_name'], 'Home')
            self.assertTrue(len(home_wf['sections']) >= 4)

            # Check that sections are customized with client name
            sec_titles = [s['title'] for s in home_wf['sections']]
            self.assertTrue(any('DataMesh' in t for t in sec_titles))
        finally:
            if prev_enabled is not None:
                os.environ['CHAT_AI_ENABLED'] = prev_enabled
            else:
                os.environ.pop('CHAT_AI_ENABLED', None)

    def test_single_page_on_demand_generation(self):
        """Test on-demand generation for a single page ID in a multi-page site."""
        result = self.service.generate_wireframes(self.sitemap_data, page_id='pricing-01')
        self.assertIn('wireframes', result)
        # Should have generated pricing-01 wireframe
        self.assertIn('pricing-01', result['wireframes'])
        pricing_wf = result['wireframes']['pricing-01']
        self.assertEqual(pricing_wf['page_name'], 'Pricing')

    def test_regenerate_section_and_description(self):
        """Test single section copy and structure regeneration."""
        desc = self.service.regenerate_section_description(
            'Core Features', 'features', 'Home', {'client': 'DataMesh'}
        )
        self.assertIsInstance(desc, str)
        self.assertTrue(len(desc) > 10)

        section_obj = self.service.regenerate_section(
            'Pricing Options', 'pricing', {'name': 'Pricing'}, {'client': 'DataMesh'}
        )
        self.assertEqual(section_obj['type'], 'pricing')
        self.assertEqual(section_obj['title'], 'Pricing Options')
        self.assertTrue(len(section_obj['items']) >= 3)


class WireframeAPIRoutesTests(TestCase):
    """Tests REST API endpoints /api/generate-wireframe/ and /api/regenerate-section/."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.valid_sitemap = {
            'website_type': 'Agency Website',
            'brief': {'client': 'HyperCreative', 'type': 'Design Agency'},
            'pages': [
                {
                    'id': 'pg-1',
                    'name': 'Home',
                    'sections': [
                        {'id': 's1', 'type': 'navbar', 'title': 'HyperCreative'},
                        {'id': 's2', 'type': 'hero', 'title': 'Design That Inspires'},
                        {'id': 's3', 'type': 'features', 'title': 'What We Do'},
                        {'id': 's4', 'type': 'footer', 'title': 'Footer'}
                    ]
                }
            ]
        }

    def test_generate_wireframe_endpoint_success(self):
        """Verify POST /api/generate-wireframe/ returns HTTP 200 with standard wireframe envelope."""
        req = self.factory.post(
            '/api/generate-wireframe/',
            data={'sitemap_data': self.valid_sitemap},
            format='json'
        )
        response = generate_wireframe(req)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.data
        self.assertTrue(res_data.get('success'))
        self.assertIn('wireframes', res_data)
        self.assertIn('wireframes', res_data['wireframes'])
        self.assertIn('pg-1', res_data['wireframes']['wireframes'])

        sections = res_data['wireframes']['wireframes']['pg-1']['sections']
        self.assertTrue(len(sections) >= 3)
        self.assertEqual(sections[0]['type'], 'navbar')
        self.assertEqual(sections[-1]['type'], 'footer')

    def test_generate_wireframe_endpoint_missing_payload(self):
        """Verify POST /api/generate-wireframe/ returns HTTP 400 when sitemap_data is missing."""
        req = self.factory.post(
            '/api/generate-wireframe/',
            data={},
            format='json'
        )
        response = generate_wireframe(req)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        res_data = response.data
        self.assertFalse(res_data.get('success'))

    def test_regenerate_section_endpoint(self):
        """Verify POST /api/regenerate-section/ returns HTTP 200 with new description and section."""
        req = self.factory.post(
            '/api/regenerate-section/',
            data={'title': 'Key Benefits', 'type': 'features'},
            format='json'
        )
        response = regenerate_section(req)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.data
        self.assertTrue(res_data.get('success'))
        self.assertTrue(len(res_data.get('description', '')) > 5)
        self.assertIn('section', res_data)
        self.assertEqual(res_data['section']['type'], 'features')
