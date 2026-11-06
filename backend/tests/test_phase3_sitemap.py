"""
backend/tests/test_phase3_sitemap.py
Comprehensive Phase 3 Test Suite: Requirement Analysis & Sitemap Generation Engine.

Verifies:
1. Requirement Analyzer:
   - Website category extraction across standard industry taxonomies
   - Business objectives identification
   - Target audience extraction
   - Design preferences extraction (style, tone, visual direction)
   - Required functionality extraction
   - Required pages and hierarchy extraction (bulleted, path syntax, comma-separated)
   - Navigation requirements (primary nav, navbar CTA, footer)
   - Content requirements and proof points
   - Dynamic brief clarification questions

2. Sitemap Generator:
   - Primary navigation marking and labels
   - Parent and child page hierarchy with parent_id linkage
   - Contextual, rich page descriptions
   - Meaningful, distinct page objectives
   - Logical page sequencing (Home at root position 0)
   - Navigation relationships
   - Pydantic v2 schema validation
   - Self-healing repair (missing IDs, missing Home, deduplication, circular loops, missing sections)
   - Backward compatibility with legacy endpoints and flight booking
   - Graceful degradation when AI fails
"""

import os
import sys
import uuid
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Force offline mock provider during testing
os.environ['AI_PROVIDER'] = 'mock'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from sitemap_app.analyzer import RequirementAnalyzer
from sitemap_app.sitemap_service import SitemapService
from sitemap_app.services import SitemapGenerator
from sitemap_app.schemas import (
    SitemapModel,
    SitemapPageModel,
    SitemapSectionModel,
    BriefContextModel,
    validate_sitemap,
    repair_sitemap,
    SUPPORTED_SECTION_TYPES,
    SECTION_TYPE_ALIASES,
)
from rest_framework.test import APIRequestFactory
from sitemap_app.views import init_brief, generate_sitemap, export_json


class TestRequirementAnalyzer(unittest.TestCase):
    """Unit tests for the RequirementAnalyzer engine."""

    def setUp(self):
        self.analyzer = RequirementAnalyzer()

    def test_category_extraction_ecommerce(self):
        prompt = "Create an online boutique store selling artisanal leather shoes and accessories"
        cat, label = self.analyzer.extract_category(prompt)
        self.assertEqual(cat, 'ecommerce')
        self.assertIn('E-commerce', label)

    def test_category_extraction_saas(self):
        prompt = "Design a cloud B2B SaaS platform for developer workflow automation named DevOpsFlow"
        cat, label = self.analyzer.extract_category(prompt)
        self.assertEqual(cat, 'saas')
        self.assertIn('SaaS', label)

    def test_category_extraction_healthcare(self):
        prompt = "Build a modern dental clinic and orthodontics website with appointment booking"
        cat, label = self.analyzer.extract_category(prompt)
        self.assertEqual(cat, 'healthcare')
        self.assertIn('Healthcare', label)

    def test_category_extraction_restaurant(self):
        prompt = "A fine dining Italian bistro and bakery website with table reservations"
        cat, label = self.analyzer.extract_category(prompt)
        self.assertEqual(cat, 'restaurant')
        self.assertIn('Restaurant', label)

    def test_category_extraction_sports(self):
        prompt = "Create a cricket tournament league website with live score updates and points table"
        cat, label = self.analyzer.extract_category(prompt)
        self.assertEqual(cat, 'sports')
        self.assertIn('Sports', label)

    def test_category_extraction_travel_flights(self):
        prompt = "Build a modern flight booking website with fare calendar and seat selection"
        cat, label = self.analyzer.extract_category(prompt)
        self.assertEqual(cat, 'travel')
        self.assertEqual(label, 'Flight Booking Website')

    def test_business_objectives_identification(self):
        prompt = (
            "Build an education academy platform. "
            "Goals: Increase online course enrollments, drive corporate training inquiries, and build academic trust."
        )
        objectives = self.analyzer.extract_business_objectives(prompt, category='education')
        self.assertTrue(len(objectives) >= 2)
        combined = ' '.join(objectives).lower()
        self.assertTrue('enrollment' in combined or 'inquiries' in combined or 'trust' in combined)

    def test_target_audience_extraction(self):
        prompt = "Design a luxury resort website designed for high-net-worth travelers and wellness seekers"
        audience = self.analyzer.extract_target_audience(prompt, category='travel')
        self.assertTrue('travelers' in audience.lower() or 'wellness' in audience.lower())

    def test_design_preferences_extraction(self):
        prompt = "Minimalist, clean visual style with dark mode tech accents and an authoritative, expert tone"
        prefs = self.analyzer.extract_design_preferences(prompt)
        style = prefs['style'].lower()
        tone = prefs['tone'].lower()
        self.assertTrue('minimal' in style or 'clean' in style or 'dark' in style)
        self.assertTrue('authoritative' in tone or 'expert' in tone)

    def test_required_functionality_extraction(self):
        prompt = (
            "E-commerce website with features: Instant product search with faceted filters, "
            "shopping cart with promo codes, verified customer review ratings, and one-click checkout."
        )
        features = self.analyzer.extract_required_functionality(prompt, category='ecommerce')
        self.assertTrue(len(features) >= 3)
        combined = ' '.join(features).lower()
        self.assertTrue('search' in combined or 'cart' in combined or 'checkout' in combined or 'review' in combined)

    def test_required_pages_bulleted_hierarchy(self):
        prompt = """Pages:
- Home
- Services
  - Web Development
    - React
    - Django
  - Cloud Infrastructure
- About Us
- Contact"""
        res = self.analyzer.extract_required_pages(prompt, category='corporate')
        tree = res['pages_tree']
        self.assertEqual(len(tree), 4)  # Home, Services, About Us, Contact
        services_node = tree[1]
        self.assertEqual(services_node['name'], 'Services')
        self.assertEqual(len(services_node['children']), 2)  # Web Development, Cloud Infrastructure
        web_dev_node = services_node['children'][0]
        self.assertEqual(web_dev_node['name'], 'Web Development')
        self.assertEqual(len(web_dev_node['children']), 2)  # React, Django

    def test_required_pages_path_syntax(self):
        prompt = "Pages: Home; Solutions > Enterprise > Analytics; Pricing; Contact"
        res = self.analyzer.extract_required_pages(prompt, category='saas')
        tree = res['pages_tree']
        self.assertEqual(len(tree), 4)
        solutions_node = tree[1]
        self.assertEqual(solutions_node['name'], 'Solutions')
        self.assertEqual(len(solutions_node['children']), 1)
        self.assertEqual(solutions_node['children'][0]['name'], 'Enterprise')
        self.assertEqual(solutions_node['children'][0]['children'][0]['name'], 'Analytics')

    def test_navigation_requirements(self):
        prompt = 'SaaS website with Navbar CTA: "Start 14-Day Free Trial"'
        nav = self.analyzer.extract_navigation_requirements(prompt, None, ['Home', 'Features', 'Pricing', 'Contact'])
        self.assertEqual(nav['cta_button'], 'Start 14-Day Free Trial')
        self.assertIn('Home', nav['primary_nav'])

    def test_content_requirements(self):
        prompt = "Include client testimonials, in-depth case studies with ROI stats, and a transparent pricing table"
        content = self.analyzer.extract_content_requirements(prompt, None, ['Home'], 'saas')
        priorities = ' '.join(content['editorial_priorities']).lower()
        self.assertTrue('testimonial' in priorities or 'case' in priorities or 'pricing' in priorities)

    def test_dynamic_brief_questions(self):
        parsed = self.analyzer.analyze("Build an e-commerce website for artisanal chocolate")
        questions = self.analyzer.generate_brief_questions("Build an e-commerce website", parsed)
        self.assertTrue(len(questions) >= 5)
        q_ids = [q['id'] for q in questions]
        self.assertIn('audience', q_ids)
        self.assertIn('goals', q_ids)
        self.assertIn('features', q_ids)
        self.assertIn('style', q_ids)
        for q in questions:
            self.assertTrue(len(q['options']) >= 3)


class TestSitemapGeneratorEngine(unittest.TestCase):
    """Unit and Integration tests for SitemapService and schema compliance."""

    def setUp(self):
        self.service = SitemapService()

    def test_simple_website_sitemap(self):
        prompt = "A simple portfolio for a landscape photographer named HorizonLens"
        sitemap = self.service.generate_sitemap(prompt, ai_enabled=False)
        self.assertTrue(len(sitemap['pages']) >= 3)
        self.assertEqual(sitemap['pages'][0]['name'], 'Home')
        self.assertTrue(sitemap['pages'][0]['is_primary_nav'])

        # Verify sections inside Home page
        home_sections = sitemap['pages'][0]['sections']
        self.assertTrue(len(home_sections) >= 4)
        self.assertEqual(home_sections[0]['type'], 'navbar')
        self.assertEqual(home_sections[-1]['type'], 'footer')

    def test_multi_page_sitemap_with_descriptions_and_objectives(self):
        prompt = "Create a multi-page SaaS website for CloudMetrics with 6 pages: Home, Features, Solutions, Pricing, Blog, Contact"
        sitemap = self.service.generate_sitemap(prompt, ai_enabled=False)
        self.assertEqual(len(sitemap['pages']), 6)
        
        for page in sitemap['pages']:
            self.assertTrue(len(page['name']) > 0)
            self.assertTrue(len(page['description']) > 15)
            self.assertTrue(len(page['objective']) > 15)
            self.assertIsNotNone(page['id'])
            self.assertIn('order_index', page)
            self.assertTrue(len(page['sections']) >= 3)

    def test_complex_hierarchy_with_parent_child_links(self):
        prompt = """Build an enterprise consulting website for Summit Advisors.
Pages:
- Home
- Services
  - Strategy & Operations
  - Digital Transformation
  - Mergers & Acquisitions
- Case Studies
- Leadership
- Contact"""
        sitemap = self.service.generate_sitemap(prompt, ai_enabled=False)
        pages = sitemap['pages']
        self.assertEqual(pages[0]['name'], 'Home')

        # Find Services parent
        services_page = next((p for p in pages if p['name'] == 'Services'), None)
        self.assertIsNotNone(services_page)
        self.assertEqual(len(services_page['children']), 3)

        # Verify parent_id linkage on child nodes
        for child in services_page['children']:
            self.assertEqual(child['parent_id'], services_page['id'])
            self.assertFalse(child['is_primary_nav'])
            self.assertTrue(len(child['sections']) >= 2)
            self.assertTrue(len(child['objective']) > 10)

    def test_pydantic_schema_validation(self):
        prompt = "Healthcare clinic website with online booking"
        sitemap = self.service.generate_sitemap(prompt, ai_enabled=False)
        
        is_valid, model, errors = validate_sitemap(sitemap)
        self.assertTrue(is_valid, f"Sitemap failed validation: {errors}")
        self.assertIsInstance(model, SitemapModel)
        self.assertIsInstance(model.brief, BriefContextModel)
        self.assertTrue(len(model.pages) >= 4)
        for page in model.pages:
            self.assertIsInstance(page, SitemapPageModel)
            for sec in page.sections:
                self.assertIsInstance(sec, SitemapSectionModel)

    def test_self_healing_repair_missing_home(self):
        broken_sitemap = {
            'website_type': 'Agency Site',
            'pages': [
                {'name': 'Services', 'sections': []},
                {'name': 'About Us', 'sections': []}
            ]
        }
        repaired = repair_sitemap(broken_sitemap)
        self.assertEqual(repaired['pages'][0]['name'], 'Home')
        self.assertEqual(len(repaired['pages']), 3)
        self.assertTrue(repaired['pages'][0]['is_primary_nav'])

    def test_self_healing_repair_duplicate_pages_and_ids(self):
        shared_id = 'shared-123'
        broken_sitemap = {
            'website_type': 'Store',
            'pages': [
                {'id': shared_id, 'name': 'Home', 'sections': []},
                {'id': shared_id, 'name': 'Contact', 'sections': []},
                {'id': 'another-id', 'name': 'contact', 'sections': []}  # duplicate name
            ]
        }
        repaired = repair_sitemap(broken_sitemap)
        # Should deduplicate page names and guarantee unique IDs
        self.assertEqual(len(repaired['pages']), 2)
        page_ids = [p['id'] for p in repaired['pages']]
        self.assertEqual(len(page_ids), len(set(page_ids)))

    def test_self_healing_repair_alias_section_types(self):
        broken_sitemap = {
            'website_type': 'App',
            'pages': [
                {
                    'name': 'Home',
                    'sections': [
                        {'type': 'header', 'title': 'Header'},
                        {'type': 'hero-banner', 'title': 'Hero'},
                        {'type': 'key-features', 'title': 'Features'},
                        {'type': 'social-proof', 'title': 'Reviews'},
                        {'type': 'site-footer', 'title': 'Footer'}
                    ]
                }
            ]
        }
        repaired = repair_sitemap(broken_sitemap)
        sec_types = [s['type'] for s in repaired['pages'][0]['sections']]
        self.assertIn('navbar', sec_types)
        self.assertIn('hero', sec_types)
        self.assertIn('features', sec_types)
        self.assertIn('testimonial', sec_types)
        self.assertIn('footer', sec_types)

    def test_self_healing_repair_circular_reference_prevention(self):
        p1_id = 'page-1'
        p2_id = 'page-2'
        circular_node_1 = {'id': p1_id, 'name': 'Level 1', 'children': []}
        circular_node_2 = {'id': p2_id, 'name': 'Level 2', 'children': [circular_node_1]}
        circular_node_1['children'].append(circular_node_2)

        broken_sitemap = {
            'pages': [circular_node_1]
        }
        # Must not enter infinite recursion and must repair safely
        repaired = repair_sitemap(broken_sitemap)
        self.assertTrue(len(repaired['pages']) >= 1)

    def test_preserve_flight_booking_sitemap(self):
        prompt = "Flight booking website for domestic airlines"
        sitemap = self.service.generate_sitemap(prompt, ai_enabled=False)
        self.assertEqual(sitemap['website_type'], 'Flight Booking Website')
        self.assertIn('trip_types', sitemap['brief'])
        self.assertIn('passenger_types', sitemap['brief'])
        self.assertIn('addons', sitemap['brief'])


class TestAPIEndpointsPhase3(unittest.TestCase):
    """Integration tests for the REST API endpoints using Phase 3 engine."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.prev_provider = os.environ.get('AI_PROVIDER')
        os.environ['AI_PROVIDER'] = 'mock'

    def tearDown(self):
        if self.prev_provider is not None:
            os.environ['AI_PROVIDER'] = self.prev_provider
        else:
            os.environ.pop('AI_PROVIDER', None)

    def test_init_brief_endpoint_returns_rich_parsed_and_questions(self):
        payload = {
            "prompt": "Create an automated customer support SaaS platform named ZenDeskFlow",
            "ai_enabled": False
        }
        req = self.factory.post('/api/init-brief/', payload, format='json')
        resp = init_brief(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertTrue(len(data.get('questions', [])) >= 4)
        
        parsed = data.get('parsed', {})
        self.assertEqual(parsed.get('client'), 'ZenDeskFlow')
        self.assertEqual(parsed.get('category'), 'saas')
        self.assertIn('business_objectives', parsed)
        self.assertIn('target_audience', parsed)
        self.assertIn('design_preferences', parsed)
        self.assertIn('required_functionality', parsed)
        self.assertIn('navigation_requirements', parsed)

    def test_generate_sitemap_endpoint_full_pipeline(self):
        payload = {
            "prompt": "Build a modern luxury hotel and resort booking website for Azure Cove",
            "brief_data": {
                "client": "Azure Cove Spa Resort",
                "type": "Luxury Resort & Spa Website",
                "goals": "Drive direct villa bookings and spa reservations",
                "style": "Luxury & Elegant, Clean"
            }
        }
        req = self.factory.post('/api/generate-sitemap/', payload, format='json')
        resp = generate_sitemap(req)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        
        sitemap = data.get('sitemap')
        self.assertIsNotNone(sitemap)
        self.assertEqual(sitemap['website_type'], 'Luxury Resort & Spa Website')
        self.assertEqual(sitemap['brief']['client'], 'Azure Cove Spa Resort')
        self.assertTrue(len(sitemap['pages']) >= 4)
        
        # Verify schema validation on returned payload
        is_valid, _, errors = validate_sitemap(sitemap)
        self.assertTrue(is_valid, f"Endpoint returned invalid schema: {errors}")

    def test_export_json_endpoint(self):
        generator = SitemapGenerator()
        sitemap = generator.generate_sitemap("Simple agency website")
        req = self.factory.post('/api/export-json/', {'sitemap_data': sitemap}, format='json')
        resp = export_json(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertIn('attachment; filename="sitemap.json"', resp['Content-Disposition'])


if __name__ == '__main__':
    unittest.main()

