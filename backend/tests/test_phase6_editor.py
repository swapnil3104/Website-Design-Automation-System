"""
backend/tests/test_phase6_editor.py
Comprehensive Verification Suite for Phase 6: Responsive Design & Wireframe Editor.
Tests responsive preview breakpoints, grid collapsing, mobile navigation,
page switching, section CRUD & reordering, inline & sidebar editing,
component replacement, section/page regeneration, and state persistence.
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

from rest_framework.test import APIRequestFactory
from sitemap_app.views import generate_wireframe, regenerate_section
from sitemap_app.schemas.sitemap import SUPPORTED_SECTION_TYPES


class TestPhase6Editor(unittest.TestCase):
    """Test suite verifying responsive preview and wireframe editor capabilities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = APIRequestFactory()
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cls.editor_js_path = os.path.join(cls.repo_root, 'frontend', 'js', 'wireframe-editor.js')
        cls.wireframe_js_path = os.path.join(cls.repo_root, 'frontend', 'js', 'wireframe.js')
        cls.state_manager_path = os.path.join(cls.repo_root, 'frontend', 'js', 'state-manager.js')
        cls.wireframe_css_path = os.path.join(cls.repo_root, 'frontend', 'css', 'wireframe.css')
        cls.wireframe_html_path = os.path.join(cls.repo_root, 'frontend', 'wireframe.html')

    def setUp(self):
        self.prev_provider = os.environ.get('AI_PROVIDER')
        os.environ['AI_PROVIDER'] = 'mock'

    def tearDown(self):
        if self.prev_provider is not None:
            os.environ['AI_PROVIDER'] = self.prev_provider
        else:
            os.environ.pop('AI_PROVIDER', None)

    def _run_node_script(self, script_body: str) -> dict:
        """Helper to run a Node.js snippet and return parsed JSON result."""
        wrapped_script = f"""
        function createMockEl(props = {{}}) {{
            return Object.assign({{
                addEventListener: () => {{}},
                removeEventListener: () => {{}},
                classList: {{ add: () => {{}}, remove: () => {{}}, toggle: () => {{}}, contains: () => false }},
                style: {{}},
                dataset: {{}},
                value: '',
                textContent: '',
                innerHTML: '',
                querySelector: () => null,
                querySelectorAll: () => [],
                appendChild: () => {{}},
                setAttribute: () => {{}},
                getAttribute: () => null
            }}, props);
        }}

        global.Event = class Event {{
            constructor(type) {{ this.type = type; }}
        }};

        global.document = {{
            getElementById: () => createMockEl(),
            querySelector: () => createMockEl(),
            querySelectorAll: () => [],
            addEventListener: () => {{}},
            removeEventListener: () => {{}},
            createElement: () => createMockEl()
        }};

        const storageMock = {{}};
        global.localStorage = {{
            getItem: (k) => storageMock[k] || null,
            setItem: (k, v) => {{ storageMock[k] = v; }},
            removeItem: (k) => {{ delete storageMock[k]; }}
        }};

        const {{ StateManager }} = require('{self.state_manager_path.replace(os.sep, "/")}');
        const realStateManager = new StateManager();
        realStateManager.setSitemap({{ pages: [{{ id: 'home', name: 'Home', sections: [] }}] }});

        global.window = {{
            addEventListener: () => {{}},
            removeEventListener: () => {{}},
            dispatchEvent: () => {{}},
            location: {{ origin: 'http://localhost' }},
            stateManager: realStateManager
        }};

        const {{ WireframeEditor }} = require('{self.editor_js_path.replace(os.sep, "/")}');
        {script_body}
        """
        proc = subprocess.run(
            ['node', '-e', wrapped_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Node execution failed: {proc.stderr}\nScript:\n{wrapped_script}")

        stdout = proc.stdout.strip()
        lines = [l.strip() for l in stdout.split('\n') if l.strip().startswith('{') and l.strip().endswith('}')]
        if lines:
            return json.loads(lines[-1])
        return json.loads(stdout)

    # -------------------------------------------------------------------------
    # Responsive Preview Verification
    # -------------------------------------------------------------------------

    def test_01_responsive_preview_css_breakpoints(self):
        """Verify CSS contains viewport breakpoint classes for Desktop, Tablet, and Mobile."""
        with open(self.wireframe_css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        # Desktop: 1024px+
        self.assertIn('.bp-desktop', css, "CSS must define .bp-desktop class")
        self.assertTrue(
            re.search(r'\.bp-desktop\s+\.wireframe-page-column[^{]*\{[^}]*width:\s*1024px', css),
            "Desktop breakpoint column must be 1024px wide"
        )

        # Tablet: 768px
        self.assertIn('.bp-tablet', css, "CSS must define .bp-tablet class")
        self.assertTrue(
            re.search(r'\.bp-tablet\s+\.wireframe-page-column[^{]*\{[^}]*width:\s*768px', css),
            "Tablet breakpoint column must be 768px wide"
        )

        # Mobile: 375px
        self.assertIn('.bp-mobile', css, "CSS must define .bp-mobile class")
        self.assertTrue(
            re.search(r'\.bp-mobile\s+\.wireframe-page-column[^{]*\{[^}]*width:\s*375px', css),
            "Mobile breakpoint column must be 375px wide"
        )

    def test_02_responsive_grid_collapsing_rules(self):
        """Verify grid containers collapse gracefully on tablet (2-col) and mobile (1-col)."""
        with open(self.wireframe_css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        # Mobile 1-col collapsing
        self.assertTrue(
            re.search(r'\.bp-mobile[^{]*grid-template-columns:\s*1fr', css, re.DOTALL) or
            '.bp-mobile [style*="grid-template-columns"]' in css or
            '.bp-mobile .features-wireframe .features-grid' in css,
            "CSS must include 1-column grid collapsing for mobile"
        )

        # Tablet 2-col collapsing
        self.assertTrue(
            re.search(r'\.bp-tablet[^{]*grid-template-columns:\s*repeat\(2,\s*1fr\)', css, re.DOTALL) or
            '.bp-tablet .features-wireframe .features-grid' in css,
            "CSS must include 2-column grid collapsing for tablet"
        )

    def test_03_responsive_spacing_rules(self):
        """Verify responsive container and section padding scales across devices."""
        with open(self.wireframe_css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        # Verify desktop padding (72px 32px or 60px 32px)
        self.assertTrue(
            re.search(r'\.bp-desktop\s+\.wireframe-section[^{]*\{[^}]*padding:\s*(?:72px|60px)\s+32px', css),
            "Desktop section padding must be 72px 32px (or 60px 32px)"
        )
        # Verify tablet padding (48px 24px)
        self.assertTrue(
            re.search(r'\.bp-tablet\s+\.wireframe-section[^{]*\{[^}]*padding:\s*48px\s+24px', css),
            "Tablet section padding must be 48px 24px"
        )
        # Verify mobile padding (32px 16px)
        self.assertTrue(
            re.search(r'\.bp-mobile\s+\.wireframe-section[^{]*\{[^}]*padding:\s*32px\s+16px', css),
            "Mobile section padding must be 32px 16px"
        )

    def test_04_responsive_image_placeholders(self):
        """Verify image placeholders maintain aspect ratio and scale to container width."""
        with open(self.wireframe_css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        self.assertIn('.wf-mockup-placeholder', css, "CSS must define .wf-mockup-placeholder")
        self.assertTrue(
            'aspect-ratio: 16 / 9' in css or 'aspect-ratio: 16/9' in css,
            "Placeholder must maintain 16/9 aspect ratio"
        )
        self.assertTrue(
            re.search(r'\.wf-mockup-placeholder[^{]*\{[^}]*max-width:\s*100%', css) or
            '.bp-mobile .wf-mockup-placeholder' in css,
            "Placeholder must specify max-width: 100%"
        )

    def test_05_mobile_navigation_behavior(self):
        """Verify mobile navigation hamburger and drawer toggle styling."""
        with open(self.wireframe_css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        self.assertIn('.wf-hamburger-btn', css, "CSS must style hamburger toggle button")
        self.assertTrue(
            '.wf-mobile-drawer' in css or '.wf-drawer-expanded' in css,
            "CSS must define mobile navigation drawer and toggle classes"
        )
        self.assertIn('.wf-drawer-expanded', css, "CSS must define expanded drawer state")

    # -------------------------------------------------------------------------
    # HTML Controls & Modal Structure
    # -------------------------------------------------------------------------

    def test_06_wireframe_html_phase6_elements(self):
        """Verify wireframe.html contains Page Switcher, Device Toggles, Save Status, and Add Section Modal."""
        with open(self.wireframe_html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Device Toggle Group
        self.assertIn('id="deviceToggleGroup"', html, "wireframe.html must contain #deviceToggleGroup")
        self.assertIn('data-bp="desktop"', html, "Device toggle must have desktop option")
        self.assertIn('data-bp="tablet"', html, "Device toggle must have tablet option")
        self.assertIn('data-bp="mobile"', html, "Device toggle must have mobile option")

        # Page Switcher
        self.assertIn('id="pageSwitcherBar"', html, "wireframe.html must contain #pageSwitcherBar")
        self.assertIn('id="pageSelectDropdown"', html, "wireframe.html must contain #pageSelectDropdown")

        # Save Status Indicator
        self.assertIn('id="saveStatusIndicator"', html, "wireframe.html must contain #saveStatusIndicator")

        # Add Section Modal
        self.assertIn('id="addSectionModal"', html, "wireframe.html must contain #addSectionModal")
        self.assertIn('id="addSectionSearchInput"', html, "Modal must contain search input")
        self.assertIn('id="addSectionGrid"', html, "Modal must contain section grid")
        self.assertIn('id="generateAllBtn"', html, "wireframe.html must contain #generateAllBtn")

    # -------------------------------------------------------------------------
    # State Manager & Section CRUD Verification (Node.js)
    # -------------------------------------------------------------------------

    def test_07_state_manager_section_reordering(self):
        """Verify StateManager.reorderSections correctly reorders sections and handles boundaries."""
        script = """
        const sm = new StateManager();
        const testSitemap = {
            pages: [
                {
                    id: 'home',
                    name: 'Home',
                    sections: [
                        { type: 'navbar', title: 'Nav' },
                        { type: 'hero', title: 'Hero' },
                        { type: 'features', title: 'Features' },
                        { type: 'footer', title: 'Footer' }
                    ]
                }
            ]
        };
        sm.setSitemap(testSitemap);

        // Move hero (index 1) up to index 0
        const moveUpOk = sm.reorderSections('home', 1, 0);
        const orderAfterUp = sm.findPageById('home').sections.map(s => s.type);

        // Move navbar (now index 1) down to index 2
        const moveDownOk = sm.reorderSections('home', 1, 2);
        const orderAfterDown = sm.findPageById('home').sections.map(s => s.type);

        // Out of bounds tests
        const invalidNegative = sm.reorderSections('home', -1, 0);
        const invalidHigh = sm.reorderSections('home', 0, 99);

        console.log(JSON.stringify({
            moveUpOk,
            orderAfterUp,
            moveDownOk,
            orderAfterDown,
            invalidNegative,
            invalidHigh
        }));
        """
        res = self._run_node_script(script)
        self.assertTrue(res['moveUpOk'])
        self.assertEqual(res['orderAfterUp'], ['hero', 'navbar', 'features', 'footer'])
        self.assertTrue(res['moveDownOk'])
        self.assertEqual(res['orderAfterDown'], ['hero', 'features', 'navbar', 'footer'])
        self.assertFalse(res['invalidNegative'])
        self.assertFalse(res['invalidHigh'])

    def test_08_state_manager_add_section_at_index(self):
        """Verify StateManager.addSection supports inserting at specific index positions."""
        script = """
        const sm = new StateManager();
        const testSitemap = {
            pages: [
                {
                    id: 'home',
                    name: 'Home',
                    sections: [
                        { type: 'navbar', title: 'Nav' },
                        { type: 'footer', title: 'Footer' }
                    ]
                }
            ]
        };
        sm.setSitemap(testSitemap);

        // Insert hero at index 1 (between navbar and footer)
        sm.addSection('home', { type: 'hero', title: 'Inserted Hero' }, 1);
        const order1 = sm.findPageById('home').sections.map(s => s.type);

        // Append cta at end (atIndex = null)
        sm.addSection('home', { type: 'cta', title: 'End CTA' }, null);
        const order2 = sm.findPageById('home').sections.map(s => s.type);

        console.log(JSON.stringify({ order1, order2 }));
        """
        res = self._run_node_script(script)
        self.assertEqual(res['order1'], ['navbar', 'hero', 'footer'])
        self.assertEqual(res['order2'], ['navbar', 'hero', 'footer', 'cta'])

    def test_09_state_manager_localstorage_persistence(self):
        """Verify state mutations automatically persist to localStorage."""
        script = """
        const storage = {};
        global.localStorage = {
            getItem: (k) => storage[k] || null,
            setItem: (k, v) => { storage[k] = v; },
            removeItem: (k) => { delete storage[k]; }
        };

        const sm = new StateManager();
        const testSitemap = {
            pages: [
                {
                    id: 'page1',
                    name: 'Page 1',
                    sections: [{ type: 'hero', title: 'Initial' }]
                }
            ]
        };
        sm.setSitemap(testSitemap);

        const saved1 = JSON.parse(storage['currentSitemap'] || '{}');
        const hasSet = saved1.pages && saved1.pages.length === 1;

        // Mutation: Update section
        sm.updateSection('page1', 0, { title: 'Updated Title' });
        const saved2 = JSON.parse(storage['currentSitemap'] || '{}');
        const updatedTitle = saved2.pages[0].sections[0].title;

        // Mutation: Add section
        sm.addSection('page1', { type: 'features', title: 'Features' });
        const saved3 = JSON.parse(storage['currentSitemap'] || '{}');
        const countAfterAdd = saved3.pages[0].sections.length;

        // Mutation: Delete section
        sm.deleteSection('page1', 0);
        const saved4 = JSON.parse(storage['currentSitemap'] || '{}');
        const countAfterDel = saved4.pages[0].sections.length;

        console.log(JSON.stringify({
            hasSet,
            updatedTitle,
            countAfterAdd,
            countAfterDel
        }));
        """
        res = self._run_node_script(script)
        self.assertTrue(res['hasSet'])
        self.assertEqual(res['updatedTitle'], 'Updated Title')
        self.assertEqual(res['countAfterAdd'], 2)
        self.assertEqual(res['countAfterDel'], 1)

    # -------------------------------------------------------------------------
    # Wireframe Editor Logic Verification
    # -------------------------------------------------------------------------

    def test_10_wireframe_editor_section_types_coverage(self):
        """Verify WireframeEditor.getAllSectionTypes covers all 32 canonical section types."""
        script = """
        const editor = new WireframeEditor();
        const types = editor.getAllSectionTypes();
        console.log(JSON.stringify({
            count: types.length,
            types: types.map(t => t.type || t.id)
        }));
        """
        res = self._run_node_script(script)
        self.assertGreaterEqual(res['count'], 32, "Editor must provide at least 32 section types")
        canonical_keys = [
            'navbar', 'hero', 'features', 'services', 'pricing', 'testimonials',
            'faq', 'about', 'contact', 'footer', 'cta', 'stats', 'team', 'gallery',
            'process', 'products', 'quote', 'timeline', 'partners', 'newsletter',
            'login', 'sidebar', 'divider', 'banner'
        ]
        editor_keys = set(res['types'])
        for key in canonical_keys:
            self.assertIn(key, editor_keys, f"Section type '{key}' must be present in getAllSectionTypes()")

    def test_11_wireframe_editor_create_default_section(self):
        """Verify createDefaultSection returns valid data schemas for various section types."""
        script = """
        const editor = new WireframeEditor();
        const hero = editor.createDefaultSection('hero', 'page_1');
        const pricing = editor.createDefaultSection('pricing', 'page_1');
        const features = editor.createDefaultSection('features', 'page_1');
        const contact = editor.createDefaultSection('contact', 'page_1');

        console.log(JSON.stringify({
            heroValid: Boolean(hero.title && hero.description && hero.buttonText),
            pricingItems: Array.isArray(pricing.items) && pricing.items.length >= 3,
            featuresItems: Array.isArray(features.items) && features.items.length >= 3,
            contactItems: Array.isArray(contact.items) && contact.items.length >= 2
        }));
        """
        res = self._run_node_script(script)
        self.assertTrue(res['heroValid'])
        self.assertTrue(res['pricingItems'])
        self.assertTrue(res['featuresItems'])
        self.assertTrue(res['contactItems'])

    def test_12_wireframe_editor_breakpoint_switching_logic(self):
        """Verify setBreakpoint updates currentBreakpoint and coordinates board classes."""
        script = """
        let boardClasses = ['wireframe-board'];
        let dropdownValue = '';
        let activeDevice = '';

        const mockBoard = createMockEl({
            classList: {
                remove: (...cls) => { boardClasses = boardClasses.filter(c => !cls.includes(c)); },
                add: (c) => { boardClasses.push(c); },
                toggle: () => {},
                contains: (c) => boardClasses.includes(c)
            }
        });

        const mockScreenSize = createMockEl({
            value: dropdownValue,
            set value(v) { dropdownValue = v; }
        });

        document.getElementById = (id) => {
            if (id === 'wireframeBoard') return mockBoard;
            if (id === 'screenSizeSelect') return mockScreenSize;
            return createMockEl();
        };

        document.querySelectorAll = (sel) => {
            if (sel === '.device-toggle-btn') {
                return [
                    createMockEl({
                        dataset: { bp: 'desktop' },
                        classList: { toggle: (c, active) => { if (active) activeDevice = 'desktop'; } }
                    }),
                    createMockEl({
                        dataset: { bp: 'tablet' },
                        classList: { toggle: (c, active) => { if (active) activeDevice = 'tablet'; } }
                    }),
                    createMockEl({
                        dataset: { bp: 'mobile' },
                        classList: { toggle: (c, active) => { if (active) activeDevice = 'mobile'; } }
                    })
                ];
            }
            return [];
        };

        const editor = new WireframeEditor();
        editor.setBreakpoint('tablet');
        const tabletBp = editor.currentBreakpoint;
        const tabletHasClass = boardClasses.includes('bp-tablet');
        const tabletActive = activeDevice;

        editor.setBreakpoint('mobile');
        const mobileBp = editor.currentBreakpoint;
        const mobileHasClass = boardClasses.includes('bp-mobile');
        const mobileActive = activeDevice;

        console.log(JSON.stringify({
            tabletBp,
            tabletHasClass,
            tabletActive,
            mobileBp,
            mobileHasClass,
            mobileActive
        }));
        """
        res = self._run_node_script(script)
        self.assertEqual(res['tabletBp'], 'tablet')
        self.assertTrue(res['tabletHasClass'])
        self.assertEqual(res['tabletActive'], 'tablet')
        self.assertEqual(res['mobileBp'], 'mobile')
        self.assertTrue(res['mobileHasClass'])
        self.assertEqual(res['mobileActive'], 'mobile')

    def test_13_text_editing_and_sidebar_sync(self):
        """Verify handleContentChange updates local section object, DOM elements, and state manager."""
        script = """
        let updatedState = null;
        global.window.stateManager.updateSection = (pId, idx, updates) => {
            updatedState = { pId, idx, updates };
        };

        const domTitle = { textContent: 'Old Title' };
        const domDesc = { textContent: 'Old Desc' };
        const domBtn = { textContent: 'Old Btn' };

        const element = createMockEl({
            querySelector: (sel) => {
                if (sel === '[data-field="title"]') return domTitle;
                if (sel === '[data-field="description"]') return domDesc;
                if (sel === '.cta-button, .btn') return domBtn;
                return null;
            }
        });

        const editor = new WireframeEditor();
        editor.activeSection = {
            section: { title: 'Old Title', description: 'Old Desc', buttonText: 'Old Btn' },
            index: 2,
            pageId: 'home',
            element: element
        };

        // Test updating title
        editor.handleContentChange('title', 'Brand New Heading');
        const titleSyncOk = domTitle.textContent === 'Brand New Heading' &&
                            editor.activeSection.section.title === 'Brand New Heading' &&
                            updatedState.updates.title === 'Brand New Heading';

        // Test updating buttonText
        editor.handleContentChange('buttonText', 'Get Started Now');
        const btnSyncOk = domBtn.textContent === 'Get Started Now' &&
                          editor.activeSection.section.buttonText === 'Get Started Now' &&
                          updatedState.updates.buttonText === 'Get Started Now';

        console.log(JSON.stringify({ titleSyncOk, btnSyncOk }));
        """
        res = self._run_node_script(script)
        self.assertTrue(res['titleSyncOk'], "Title edit must sync to DOM, section, and StateManager")
        self.assertTrue(res['btnSyncOk'], "Button edit must sync to DOM, section, and StateManager")

    def test_14_component_replacement_workflow(self):
        """Verify replaceComponent updates type, re-renders content, and notifies StateManager."""
        script = """
        let stateUpdated = false;
        let toastMessage = '';

        global.window.stateManager.updateSection = (pId, idx, sec) => {
            stateUpdated = (sec.type === 'pricing');
        };

        let replacedContent = null;
        const mockContentContainer = {
            replaceWith: (newEl) => { replacedContent = newEl; }
        };
        const mockLabelEl = { textContent: 'features' };
        const mockNameEl = { textContent: '' };

        const mockSectionEl = createMockEl({
            className: 'wireframe-section features edit-mode',
            querySelector: (sel) => {
                if (sel === '.section-content') return mockContentContainer;
                if (sel === '.section-label') return mockLabelEl;
                return null;
            }
        });

        document.getElementById = (id) => {
            if (id === 'sidebarComponentName') return mockNameEl;
            return createMockEl();
        };

        const editor = new WireframeEditor();
        editor.showNotification = (msg) => { toastMessage = msg; };
        editor.createSectionContent = (sec, idx, pId) => ({ type: sec.type, tag: 'div' });
        editor.bindSectionEvents = () => {};
        editor.closeReplaceView = () => {};

        editor.activeSection = {
            section: { type: 'features', title: 'Old Features' },
            index: 1,
            pageId: 'home',
            element: mockSectionEl
        };

        editor.replaceComponent('pricing');

        console.log(JSON.stringify({
            newType: editor.activeSection.section.type,
            stateUpdated,
            labelUpdated: mockLabelEl.textContent === 'pricing',
            sidebarUpdated: mockNameEl.textContent === 'Pricing',
            toastMessage
        }));
        """
        res = self._run_node_script(script)
        self.assertEqual(res['newType'], 'pricing')
        self.assertTrue(res['stateUpdated'])
        self.assertTrue(res['labelUpdated'])
        self.assertTrue(res['sidebarUpdated'])
        self.assertIn('pricing', res['toastMessage'])

    # -------------------------------------------------------------------------
    # Backend Regeneration APIs & Isolation Verification
    # -------------------------------------------------------------------------

    def test_15_backend_regenerate_section_api(self):
        """Verify /api/regenerate-section/ regenerates a single section preserving other properties."""
        payload = {
            "title": "Features Grid",
            "type": "features",
            "page_context": {
                "name": "Home Page",
                "purpose": "Showcase SaaS product"
            },
            "brief": {
                "client": "Acme SaaS",
                "industry": "Software"
            }
        }

        req = self.factory.post('/api/regenerate-section/', payload, format='json')
        resp = regenerate_section(req)

        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('section', data)
        sec = data['section']
        self.assertEqual(sec['type'], 'features')
        self.assertTrue('title' in sec and len(sec['title']) > 0)

    def test_16_backend_generate_wireframe_page_id_filtering(self):
        """Verify /api/generate-wireframe/ with page_id regenerates ONLY the requested page."""
        sitemap_payload = {
            "sitemap_data": {
                "website_type": "SaaS Platform",
                "brief": {"client": "Acme Cloud", "goals": "Streamline operations"},
                "pages": [
                    {
                        "id": "page_home",
                        "name": "Home",
                        "sections": [{"id": "s1", "type": "hero", "title": "Home Hero"}]
                    },
                    {
                        "id": "page_about",
                        "name": "About Us",
                        "sections": [{"id": "s2", "type": "about", "title": "About Story"}]
                    }
                ]
            },
            "page_id": "page_about"
        }

        req = self.factory.post('/api/generate-wireframe/', sitemap_payload, format='json')
        resp = generate_wireframe(req)

        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertTrue(data.get('success'))
        self.assertIn('wireframes', data)
        wireframes = data['wireframes'].get('wireframes', {})
        # Only page_about should be generated/returned
        self.assertIn('page_about', wireframes)
        self.assertNotIn('page_home', wireframes)

    def test_17_wireframe_app_generate_all_integration(self):
        """Verify WireframeApp binds generateAllBtn and provides generateAllPages with fallback."""
        with open(self.wireframe_js_path, 'r', encoding='utf-8') as f:
            js = f.read()

        self.assertIn('generateAllBtn', js, "wireframe.js must reference generateAllBtn")
        self.assertIn('generateAllPages()', js, "wireframe.js must define generateAllPages()")
        self.assertIn('/api/generate-wireframe/', js, "generateAllPages must call /api/generate-wireframe/")
        self.assertIn('generateFallbackWireframesForAllPages', js, "generateAllPages must include fallback handler")


if __name__ == '__main__':
    unittest.main()
