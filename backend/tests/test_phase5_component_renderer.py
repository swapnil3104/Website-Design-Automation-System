"""
backend/tests/test_phase5_component_renderer.py
Comprehensive Verification Suite for Phase 5: Wireframe Component Library & Renderer.
Tests component dispatch, layout engines, graceful fallbacks, and React export fidelity.
"""

import os
import sys
import re
import json
import unittest
import subprocess

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django
django.setup()

from django.test import SimpleTestCase
from django.conf import settings

from sitemap_app.schemas.sitemap import SUPPORTED_SECTION_TYPES, SECTION_TYPE_ALIASES
from sitemap_app.schemas.wireframe import (
    SUPPORTED_LAYOUT_VARIANTS,
    LAYOUT_VARIANT_ALIASES,
    WireframeSectionModel,
    PageWireframeModel,
    repair_wireframe_section
)


class TestPhase5ComponentRenderer(SimpleTestCase):
    """Test suite verifying component coverage, layout engine, and visual rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cls.components_js_path = os.path.join(cls.repo_root, 'frontend', 'js', 'wireframe-components.js')
        cls.editor_js_path = os.path.join(cls.repo_root, 'frontend', 'js', 'wireframe-editor.js')
        cls.wireframe_js_path = os.path.join(cls.repo_root, 'frontend', 'js', 'wireframe.js')
        cls.wireframe_css_path = os.path.join(cls.repo_root, 'frontend', 'css', 'wireframe.css')
        cls.wireframe_html_path = os.path.join(cls.repo_root, 'frontend', 'wireframe.html')

    def test_01_component_library_file_exists(self):
        """Verify frontend/js/wireframe-components.js exists and has non-trivial size."""
        self.assertTrue(os.path.isfile(self.components_js_path), "wireframe-components.js must exist")
        size = os.path.getsize(self.components_js_path)
        self.assertGreater(size, 5000, f"wireframe-components.js is unexpectedly small ({size} bytes)")

    def test_02_wireframe_html_includes_component_library(self):
        """Verify wireframe.html loads wireframe-components.js before wireframe-editor.js."""
        with open(self.wireframe_html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        self.assertIn('wireframe-components.js', html, "wireframe.html must script-load wireframe-components.js")
        pos_comp = html.find('wireframe-components.js')
        pos_editor = html.find('wireframe-editor.js')
        self.assertLess(pos_comp, pos_editor, "wireframe-components.js must be loaded before wireframe-editor.js")

    def test_03_wireframe_editor_delegates_to_components_library(self):
        """Verify wireframe-editor.js createSectionContent invokes WireframeComponents."""
        with open(self.editor_js_path, 'r', encoding='utf-8') as f:
            editor_code = f.read()
        self.assertIn('window.WireframeComponents', editor_code)
        self.assertIn('renderComponent(section)', editor_code)

    def test_04_travel_section_no_longer_hijacks_pricing_or_stats(self):
        """Verify isTravelSection in wireframe-editor.js does not contain pricing or stats."""
        with open(self.editor_js_path, 'r', encoding='utf-8') as f:
            editor_code = f.read()
        # Find isTravelSection definition
        match = re.search(r'isTravelSection\s*\([^)]*\)\s*\{(.*?)\}', editor_code, re.DOTALL)
        self.assertTrue(match, "isTravelSection function must exist in editor")
        body = match.group(1)
        self.assertNotIn("'pricing'", body, "isTravelSection must not hijack generic pricing sections")
        self.assertNotIn("'stats'", body, "isTravelSection must not hijack generic stats sections")

    def test_05_css_contains_all_phase5_component_classes(self):
        """Verify wireframe.css contains complete styling for all Phase 5 components."""
        with open(self.wireframe_css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        required_classes = [
            'wf-section-header', 'wf-pill-badge', 'wf-mockup-placeholder',
            'wf-nav-standard-layout', 'wf-nav-dropdown-layout', 'wf-nav-mega-layout',
            'wf-dropdown-menu', 'wf-mega-menu-flyout', 'wf-mobile-drawer',
            'wf-hero-product', 'wf-hero-cta', 'wf-hero-full-bg', 'wf-hero-asymmetric',
            'wf-grid-2', 'wf-grid-3', 'wf-grid-4', 'wf-grid-bento',
            'wf-about-section', 'wf-image-text-section', 'wf-checklist',
            'wf-feature-card', 'wf-service-card', 'wf-product-card', 'wf-product-grid-section',
            'wf-stat-card', 'wf-testimonial-card', 'wf-team-card', 'wf-gallery-section',
            'wf-pricing-section', 'wf-pricing-card', 'wf-popular-ribbon', 'wf-billing-toggle',
            'wf-faq-section', 'wf-faq-accordion-container', 'wf-faq-item',
            'wf-blog-section', 'wf-blog-card', 'wf-contact-section', 'wf-process-section',
            'wf-cta-banner', 'wf-footer-section', 'wf-sidebar-layout-container'
        ]

        for cls_name in required_classes:
            self.assertIn(cls_name, css, f"wireframe.css must define class .{cls_name}")

    def test_06_nodejs_executes_component_library_for_all_supported_types(self):
        """Run Node.js to verify WireframeComponents.renderComponent renders all 32 section types without error."""
        test_script = f"""
        const fs = require('fs');
        const code = fs.readFileSync({json.dumps(self.components_js_path)}, 'utf8');

        // Mock browser window and DOM environment
        global.window = {{}};
        eval(code);

        const components = global.window.WireframeComponents;
        if (!components) {{
            console.error('WireframeComponents not defined');
            process.exit(1);
        }}

        const testTypes = {json.dumps(list(SUPPORTED_SECTION_TYPES))};
        let passed = 0;

        for (const type of testTypes) {{
            const section = {{
                id: 'sec-' + type,
                type: type,
                title: 'Test ' + type.toUpperCase(),
                description: 'Comprehensive test description for ' + type + ' section.',
                buttonText: 'Action Button',
                layoutVariant: 'layout-default',
                items: [
                    {{ title: 'Item 1', desc: 'Item 1 description', icon: 'Zap', price: '$29' }},
                    {{ title: 'Item 2', desc: 'Item 2 description', icon: 'Shield', price: '$59' }},
                    {{ title: 'Item 3', desc: 'Item 3 description', icon: 'Star', price: '$99' }}
                ]
            }};

            const html = components.renderComponent(section);
            if (!html || typeof html !== 'string' || html.length < 50) {{
                console.error('Failed rendering section type:', type, 'Output length:', html ? html.length : 0);
                process.exit(2);
            }}

            // Verify editable-text class exists for two-way editor synchronization
            if (!html.includes('editable-text')) {{
                console.error('Section type missing editable-text markers:', type);
                process.exit(3);
            }}

            passed++;
        }}

        console.log('SUCCESS_NODE_RENDER:' + passed);
        """

        result = subprocess.run(
            ['node', '-e', test_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        self.assertEqual(result.returncode, 0, f"Node.js rendering test failed: {result.stderr}")
        self.assertIn(f"SUCCESS_NODE_RENDER:{len(SUPPORTED_SECTION_TYPES)}", result.stdout)

    def test_07_nodejs_verifies_all_canonical_layouts(self):
        """Run Node.js to verify that all 8 canonical layout engine options render appropriately."""
        canonical_layouts = [
            'layout-full-width',
            'layout-grid-2',
            'layout-grid-3',
            'layout-grid-4',
            'layout-split',
            'layout-sidebar',
            'layout-centered',
            'layout-asymmetric'
        ]

        test_script = f"""
        const fs = require('fs');
        const code = fs.readFileSync({json.dumps(self.components_js_path)}, 'utf8');
        global.window = {{}};
        eval(code);

        const components = global.window.WireframeComponents;
        const layouts = {json.dumps(canonical_layouts)};
        let passed = 0;

        for (const layout of layouts) {{
            const heroSection = {{
                type: 'hero',
                title: 'Hero with ' + layout,
                description: 'Layout testing description.',
                layoutVariant: layout
            }};
            const html = components.renderComponent(heroSection);
            if (!html || html.length < 50) {{
                process.exit(1);
            }}
            passed++;
        }}

        console.log('SUCCESS_LAYOUT_RENDER:' + passed);
        """

        result = subprocess.run(
            ['node', '-e', test_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        self.assertEqual(result.returncode, 0, f"Node layout test failed: {result.stderr}")
        self.assertIn(f"SUCCESS_LAYOUT_RENDER:{len(canonical_layouts)}", result.stdout)

    def test_08_graceful_handling_of_empty_and_corrupt_sections(self):
        """Verify that minimal, empty, or un-typed sections render gracefully without crashes."""
        test_script = f"""
        const fs = require('fs');
        const code = fs.readFileSync({json.dumps(self.components_js_path)}, 'utf8');
        global.window = {{}};
        eval(code);

        const components = global.window.WireframeComponents;
        const corruptPayloads = [
            {{}},
            {{ type: null }},
            {{ type: 'unknown-alien-section-xyz' }},
            {{ type: 'features', items: [] }},
            {{ type: 'pricing', items: null, title: '' }},
            {{ type: 'faq', items: undefined }},
            {{ type: 'navbar', menuItems: [] }}
        ];

        let passed = 0;
        for (const bad of corruptPayloads) {{
            const html = components.renderComponent(bad);
            if (!html || typeof html !== 'string' || html.length < 20) {{
                process.exit(1);
            }}
            passed++;
        }}
        console.log('SUCCESS_CORRUPT_RENDER:' + passed);
        """

        result = subprocess.run(
            ['node', '-e', test_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        self.assertEqual(result.returncode, 0, f"Graceful error handling failed: {result.stderr}")
        self.assertIn("SUCCESS_CORRUPT_RENDER:7", result.stdout)

    def test_09_react_export_templates_and_home_routing_complete(self):
        """Verify wireframe.js contains complete JSX templates and routing for all section types."""
        with open(self.wireframe_js_path, 'r', encoding='utf-8') as f:
            code = f.read()

        expected_jsx_files = [
            "Navbar.jsx",
            "HeroSection.jsx",
            "AboutSection.jsx",
            "ImageTextSection.jsx",
            "FeaturesGrid.jsx",
            "ServicesGrid.jsx",
            "ProductGrid.jsx",
            "StatsSection.jsx",
            "Testimonials.jsx",
            "TeamSection.jsx",
            "GallerySection.jsx",
            "PricingSection.jsx",
            "FAQSection.jsx",
            "BlogSection.jsx",
            "ContactSection.jsx",
            "ProcessSection.jsx",
            "SidebarSection.jsx",
            "CTASection.jsx",
            "Footer.jsx",
            "Section.jsx"
        ]

        for jsx in expected_jsx_files:
            self.assertIn(f'sectionsFolder.file("{jsx}"', code, f"React export must bundle {jsx}")
            self.assertIn(f"import {jsx.replace('.jsx', '')} from './sections/{jsx}';", code,
                          f"Home.jsx must import {jsx}")

    def test_10_react_component_translation_covers_canonical_types(self):
        """Verify translateToReactComponent routes specialized section types accurately."""
        with open(self.wireframe_js_path, 'r', encoding='utf-8') as f:
            code = f.read()

        self.assertIn("lowType === 'faq'", code)
        self.assertIn("return 'FAQSection'", code)
        self.assertIn("lowType === 'product-grid'", code)
        self.assertIn("return 'ProductGrid'", code)
        self.assertIn("lowType === 'services'", code)
        self.assertIn("return 'ServicesGrid'", code)
        self.assertIn("lowType === 'team'", code)
        self.assertIn("return 'TeamSection'", code)
        self.assertIn("lowType === 'about'", code)
        self.assertIn("return 'AboutSection'", code)
        self.assertIn("lowType === 'process'", code)
        self.assertIn("return 'ProcessSection'", code)


if __name__ == '__main__':
    unittest.main()
