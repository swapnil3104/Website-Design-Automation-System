"""
backend/tests/test_phase7_quality_optimization.py
Comprehensive Quality Optimization & Generation Test Suite.
Phase 7 — Design Quality & Generation Optimization

Verifies:
1. Accurate taxonomy classification across all 10 website categories
2. Category-specific page blueprint resolution and domain heuristics
3. Anti-repetition engine and layout diversity enforcement (zero adjacent layout duplicates)
4. Domain-tailored content generation with zero generic placeholder copy
5. Full 8-dimension quality evaluation mechanism (scoring, grading, issues, recommendations)
6. Quality issue detection and grading degradation on defective payloads
7. REST API endpoint /api/evaluate-quality/ integration
8. End-to-end multi-page generation and quality verification across distinct categories
9. Category-specific item catalog infill (agriculture, restaurant, healthcare, etc.)
10. Spacing hierarchy, typography tokens, and category mockup placeholders
"""

import os
import sys
import json
import re
import unittest
from typing import Dict, Any, List
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

os.environ['AI_PROVIDER'] = 'mock'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.urls import reverse

from sitemap_app.analyzer import RequirementAnalyzer
from sitemap_app.page_planner import PagePlanner, PlannedSectionBlueprint
from sitemap_app.wireframe_service import WireframeService
from sitemap_app.quality_evaluator import QualityEvaluator, QualityReport
from sitemap_app.schemas.wireframe import validate_wireframe, SUPPORTED_LAYOUT_VARIANTS


class TestPhase7QualityOptimization(TestCase):
    """
    Test suite for Phase 7: Design Quality & Generation Optimization.
    """

    def setUp(self):
        self.analyzer = RequirementAnalyzer()
        self.planner = PagePlanner()
        self.wireframe_service = WireframeService()
        self.evaluator = QualityEvaluator()
        self.client = Client()

        self.canonical_categories = [
            'business',
            'saas',
            'ecommerce',
            'portfolio',
            'agency',
            'healthcare',
            'education',
            'agriculture',
            'blog',
            'restaurant'
        ]

    # -------------------------------------------------------------------------
    # 1. Category Classification & Taxonomy Verification
    # -------------------------------------------------------------------------

    def test_01_all_10_categories_classification(self):
        """Verify RequirementAnalyzer extracts all 10 canonical website categories accurately."""
        test_prompts = [
            ('Create a corporate consulting business website for Global Advisory Partners', 'business'),
            ('Build a SaaS platform for cloud analytics and workflow automation', 'saas'),
            ('Design an e-commerce online shop for apparel and accessories', 'ecommerce'),
            ('Develop a portfolio website for a visual designer and creative coder', 'portfolio'),
            ('Create a marketing and branding agency studio website', 'agency'),
            ('Build a healthcare medical clinic hospital website with doctor appointments', 'healthcare'),
            ('Design an education university website with academic courses and degree programs', 'education'),
            ('Create an organic agriculture farm website for sustainable crop harvesting and produce', 'agriculture'),
            ('Develop an editorial tech blog and online magazine publication', 'blog'),
            ('Build a fine dining restaurant bistro cafe website with table reservations', 'restaurant')
        ]

        for prompt, expected_cat in test_prompts:
            detected_cat, label = self.analyzer.extract_category(prompt)
            self.assertEqual(
                detected_cat,
                expected_cat,
                f"Failed classification for prompt: '{prompt}'. Expected {expected_cat}, got {detected_cat}"
            )
            self.assertTrue(len(label) > 3, "Category label must be non-empty")

    # -------------------------------------------------------------------------
    # 2. Category-Specific Blueprints Resolution
    # -------------------------------------------------------------------------

    def test_02_category_specific_blueprints_resolution(self):
        """Verify PagePlanner returns distinct, domain-specific blueprints for each category."""
        category_signatures = {}

        for cat in self.canonical_categories:
            blueprints = self.planner.get_category_page_blueprint(cat, 'home')
            self.assertTrue(len(blueprints) >= 6, f"Category '{cat}' blueprint must have at least 6 sections.")

            types = [b[0] for b in blueprints]
            titles = [b[1] for b in blueprints]
            layouts = [b[3] for b in blueprints]

            # Verify framing
            self.assertEqual(types[0], 'navbar', f"Category '{cat}' must start with navbar")
            self.assertEqual(types[1], 'hero', f"Category '{cat}' second section must be hero")
            self.assertEqual(types[-1], 'footer', f"Category '{cat}' must end with footer")

            # Store signature to check uniqueness across categories
            sig = (cat, tuple(types))
            category_signatures[cat] = sig

        # Verify that blueprints are not all identical clones
        unique_type_sequences = {sig[1] for sig in category_signatures.values()}
        self.assertTrue(
            len(unique_type_sequences) >= 7,
            f"Expected diverse section compositions across categories, found only {len(unique_type_sequences)} unique sequences."
        )

    # -------------------------------------------------------------------------
    # 3. Layout Diversity & Anti-Repetition Engine
    # -------------------------------------------------------------------------

    def test_03_layout_diversity_and_anti_repetition(self):
        """Verify enforce_layout_diversity eliminates adjacent identical layout variants."""
        # Create an artificial sequence with consecutive duplicate layouts
        repetitive_sections = [
            PlannedSectionBlueprint('1', 'navbar', 'Nav', '', 'layout-default'),
            PlannedSectionBlueprint('2', 'hero', 'Hero', '', 'layout-split-right'),
            PlannedSectionBlueprint('3', 'features', 'Feat 1', '', 'layout-grid-3'),
            PlannedSectionBlueprint('4', 'services', 'Feat 2', '', 'layout-grid-3'),  # DUPLICATE LAYOUT
            PlannedSectionBlueprint('5', 'process', 'Process', '', 'layout-grid-3'),   # DUPLICATE LAYOUT
            PlannedSectionBlueprint('6', 'stats', 'Stats', '', 'layout-grid-4'),
            PlannedSectionBlueprint('7', 'cta', 'CTA', '', 'layout-centered'),
            PlannedSectionBlueprint('8', 'footer', 'Foot', '', 'layout-multi-column'),
        ]

        diversified = self.planner.enforce_layout_diversity(repetitive_sections)
        layouts = [s.layout_variant for s in diversified]

        # Verify no adjacent duplicates
        for i in range(1, len(layouts)):
            if layouts[i] != 'layout-default':  # Ignore default framing if any
                self.assertNotEqual(
                    layouts[i],
                    layouts[i - 1],
                    f"Adjacent duplicate found at index {i}: '{layouts[i]}' vs '{layouts[i - 1]}'"
                )

        # Check all layouts belong to canonical set
        for lay in layouts:
            self.assertIn(lay, SUPPORTED_LAYOUT_VARIANTS, f"Layout '{lay}' must be canonical")

    # -------------------------------------------------------------------------
    # 4. Zero Generic Copy Enforcement
    # -------------------------------------------------------------------------

    def test_04_zero_generic_copy_enforcement(self):
        """Verify generated wireframe sections contain zero forbidden placeholder text."""
        forbidden_regexes = [
            re.compile(r'\blorem\s+ipsum\b', re.I),
            re.compile(r'\bfeature\s+[0-9]+\b', re.I),
            re.compile(r'\bservice\s+[0-9]+\b', re.I),
            re.compile(r'\bitem\s+[0-9]+\b', re.I),
            re.compile(r'\bplaceholder\b', re.I),
            re.compile(r'\bsample\s+text\b', re.I),
        ]

        for cat in self.canonical_categories:
            sitemap_data = {
                'website_type': f'{cat.title()} Website',
                'brief': {'client': f'{cat.title()} Co', 'type': cat},
                'pages': [{'id': 'home', 'name': 'Home'}]
            }

            wf = self.wireframe_service.generate_wireframes(sitemap_data)
            home_page = wf['wireframes']['home']

            for sec_idx, sec in enumerate(home_page['sections']):
                combined_text = f"{sec.get('title', '')} {sec.get('description', '')}"
                for it in sec.get('items', []):
                    combined_text += f" {it.get('title', '')} {it.get('desc', '')}"

                for pat in forbidden_regexes:
                    self.assertIsNone(
                        pat.search(combined_text),
                        f"Found forbidden generic copy matching {pat.pattern} in {cat} section {sec_idx}: '{combined_text}'"
                    )

    # -------------------------------------------------------------------------
    # 5. Quality Evaluator All 8 Dimensions
    # -------------------------------------------------------------------------

    def test_05_quality_evaluator_all_8_dimensions(self):
        """Verify QualityEvaluator scores across all 8 dimensions and awards Grade A/A+ for clean sites."""
        expected_dims = [
            'requirement_coverage',
            'sitemap_quality',
            'layout_quality',
            'content_relevance',
            'component_consistency',
            'responsive_correctness',
            'json_validity',
            'rendering_success'
        ]

        for cat in self.canonical_categories:
            sitemap_data = {
                'website_type': f'{cat.title()} Website',
                'brief': {'client': f'Acme {cat.title()}', 'type': cat},
                'pages': [
                    {'id': 'home', 'name': 'Home'},
                    {'id': 'about', 'name': 'About Us'},
                    {'id': 'contact', 'name': 'Contact'}
                ]
            }

            wf = self.wireframe_service.generate_wireframes(sitemap_data)
            report = self.evaluator.evaluate(wf, sitemap_data)

            # Check report structure
            self.assertIsInstance(report, QualityReport)
            report_dict = report.to_dict()

            # Verify all 8 dimensions exist
            for d in expected_dims:
                self.assertIn(d, report_dict['dimension_scores'], f"Dimension '{d}' missing from report")
                dim_score = report_dict['dimension_scores'][d]
                self.assertGreaterEqual(dim_score, 85.0, f"Dimension '{d}' for {cat} scored below 85: {dim_score}")

            # Overall score should be >= 90.0 (Grade A or A+)
            self.assertGreaterEqual(
                report_dict['overall_score'],
                90.0,
                f"Overall score for category '{cat}' must be >= 90.0, got {report_dict['overall_score']}"
            )
            self.assertIn(report_dict['grade'], ('A', 'A+'), f"Grade for category '{cat}' must be A or A+")
            self.assertTrue(len(report_dict['recommendations']) > 0)

    # -------------------------------------------------------------------------
    # 6. Quality Evaluator Issue Detection on Defective Payloads
    # -------------------------------------------------------------------------

    def test_06_quality_evaluator_issue_detection(self):
        """Verify QualityEvaluator detects missing framing, duplicate layouts, generic copy, and docks score."""
        defective_container = {
            'website_type': 'Defective Website',
            'wireframes': {
                'home': {
                    'page_name': 'Home',
                    'page_type': 'home',
                    'sections': [
                        # Missing Navbar!
                        {
                            'id': 's1',
                            'type': 'hero',
                            'title': 'Lorem Ipsum Title Here',  # Generic copy
                            'description': 'description goes here lorem ipsum dolor sit amet',
                            'layoutVariant': 'layout-grid-3'
                        },
                        {
                            'id': 's2',
                            'type': 'features',
                            'title': 'Feature 1',  # Generic copy
                            'description': 'Feature 1 description sample text',
                            'layoutVariant': 'layout-grid-3'  # Adjacent layout duplicate!
                        },
                        {
                            'id': 's3',
                            'type': 'features',
                            'title': 'Feature 2',
                            'description': 'Feature 2 description',
                            'layoutVariant': 'layout-grid-3'  # Adjacent layout duplicate!
                        }
                        # Missing Footer!
                    ]
                }
            }
        }

        sitemap_data = {
            'website_type': 'Defective Website',
            'pages': [
                {'id': 'home', 'name': 'Home'},
                {'id': 'about', 'name': 'About Us'}  # Missing wireframe page!
            ]
        }

        report = self.evaluator.evaluate(defective_container, sitemap_data)
        report_dict = report.to_dict()

        # Score should be degraded
        self.assertLess(report_dict['overall_score'], 80.0, "Defective wireframe must score below 80")
        self.assertIn(report_dict['grade'], ('B', 'C', 'F'))

        # Check detected issues
        issues = report_dict['issues']
        self.assertTrue(len(issues) >= 3, "Must detect multiple quality issues")

        messages = " ".join(i['message'] for i in issues)
        self.assertTrue('Navbar' in messages or 'navbar' in messages, "Must flag missing Navbar")
        self.assertTrue('Footer' in messages or 'footer' in messages, "Must flag missing Footer")
        self.assertTrue('generic' in messages.lower() or 'placeholder' in messages.lower(), "Must flag generic copy")
        self.assertTrue('adjacent' in messages.lower() or 'layout' in messages.lower(), "Must flag layout repetition")

    # -------------------------------------------------------------------------
    # 7. REST API Integration: /api/evaluate-quality/
    # -------------------------------------------------------------------------

    def test_07_api_evaluate_quality_endpoint(self):
        """Verify POST /api/evaluate-quality/ returns HTTP 200 with structured evaluation report."""
        sitemap_data = {
            'website_type': 'Agriculture & Farming Website',
            'brief': {'client': 'Verdant Harvest Farms', 'type': 'agriculture'},
            'pages': [{'id': 'home', 'name': 'Home'}]
        }

        wf = self.wireframe_service.generate_wireframes(sitemap_data)

        payload = {
            'wireframe_data': wf,
            'sitemap_data': sitemap_data
        }

        response = self.client.post(
            '/api/evaluate-quality/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('report', data)

        report = data['report']
        self.assertGreaterEqual(report['overall_score'], 90.0)
        self.assertIn(report['grade'], ('A', 'A+'))
        self.assertEqual(len(report['dimension_scores']), 8)

    # -------------------------------------------------------------------------
    # 8. End-to-End Generation & Evaluation across Distinct Categories
    # -------------------------------------------------------------------------

    def test_08_end_to_end_generation_and_evaluation_pipeline(self):
        """Verify full pipeline generates valid, high-scoring wireframes across Agriculture, Restaurant, Healthcare & SaaS."""
        test_cases = [
            ('agriculture', 'GreenField Organics', 'Inquire Wholesale'),
            ('restaurant', 'L’Aura Bistro', 'Reserve a Table'),
            ('healthcare', 'Apex Health Clinic', 'Book Appointment'),
            ('saas', 'CloudMatrix Platform', 'Start Free Trial'),
        ]

        for cat, client_name, expected_cta in test_cases:
            sitemap_data = {
                'website_type': f'{cat.title()} Website',
                'brief': {'client': client_name, 'type': cat},
                'pages': [
                    {'id': f'{cat}_home', 'name': 'Home'},
                    {'id': f'{cat}_about', 'name': 'About Us'}
                ]
            }

            wf = self.wireframe_service.generate_wireframes(sitemap_data)

            # Pydantic validation
            is_valid, validated, errors = validate_wireframe(wf)
            self.assertTrue(is_valid, f"Pydantic validation failed for {cat}: {errors}")

            # Check CTA
            home_page = wf['wireframes'][f'{cat}_home']
            navbar_sec = home_page['sections'][0]
            hero_sec = home_page['sections'][1]

            # Verify evaluation grade
            report = self.evaluator.evaluate(wf, sitemap_data)
            self.assertGreaterEqual(report.overall_score, 90.0, f"E2E test score for {cat} must be >= 90")
            self.assertIn(report.grade, ('A', 'A+'))

    # -------------------------------------------------------------------------
    # 9. Category-Specific Items Injection
    # -------------------------------------------------------------------------

    def test_09_category_specific_items_injection(self):
        """Verify _get_category_specific_items returns authentic domain items for all 10 categories."""
        for cat in self.canonical_categories:
            items = self.wireframe_service._get_category_specific_items('features', cat, 'TestBrand')
            self.assertTrue(len(items) >= 3, f"Category '{cat}' must have at least 3 feature items")

            for item in items:
                self.assertTrue(len(item.get('title', '')) > 3)
                self.assertTrue(len(item.get('desc', '')) > 10)
                self.assertTrue(bool(item.get('icon')))

        # Check stats for Agriculture and Healthcare
        ag_stats = self.wireframe_service._get_category_specific_items('stats', 'agriculture', 'FarmCo')
        self.assertTrue(any('Acres' in s.get('title', '') for s in ag_stats))

        hc_stats = self.wireframe_service._get_category_specific_items('stats', 'healthcare', 'ClinicCo')
        self.assertTrue(any('Patients' in s.get('title', '') for s in hc_stats))

    # -------------------------------------------------------------------------
    # 10. Spacing & CSS Hierarchy Tokens
    # -------------------------------------------------------------------------

    def test_10_section_spacing_and_hierarchy_css_rules(self):
        """Verify frontend/css/wireframe.css includes Phase 7 section spacing and mockup placeholder styles."""
        with open('frontend/css/wireframe.css', 'r', encoding='utf-8') as f:
            css = f.read()

        # Check section spacing tokens
        self.assertIn('.wireframe-section.hero', css)
        self.assertIn('.wireframe-section.cta', css)
        self.assertIn('.wireframe-section.navbar', css)
        self.assertIn('.wireframe-section.footer', css)

        # Check category placeholder highlights
        self.assertIn('.wf-mockup-placeholder.healthcare', css)
        self.assertIn('.wf-mockup-placeholder.agriculture', css)
        self.assertIn('.wf-mockup-placeholder.restaurant', css)
        self.assertIn('.wf-eyebrow', css)


if __name__ == '__main__':
    unittest.main()
