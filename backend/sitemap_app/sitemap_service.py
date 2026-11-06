"""
backend/sitemap_app/sitemap_service.py
Core Sitemap Generation & Hierarchy Engine.
Phase 3 — Requirement Analysis & Sitemap Generation

Implements:
1. Primary navigation generation & relationship mapping
2. Parent & child page hierarchy construction
3. Rich contextual page descriptions & explicit page objectives
4. Logical page sequencing & deduplication
5. Pydantic v2 schema validation & self-healing repair
"""

from __future__ import annotations
import uuid
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from core.config import config
from .analyzer import RequirementAnalyzer
from .schemas import (
    SitemapModel,
    SitemapPageModel,
    SitemapSectionModel,
    BriefContextModel,
    validate_sitemap,
    repair_sitemap,
    SUPPORTED_SECTION_TYPES,
    SECTION_TYPE_ALIASES,
)
from .providers import CompletionRequest, execute_completion_with_fallback


class SitemapService:
    """
    Robust Sitemap Generation Service.
    Converts unstructured prompts or briefs into fully validated, multi-level sitemaps.
    """

    def __init__(self, analyzer: Optional[RequirementAnalyzer] = None):
        self.analyzer = analyzer or RequirementAnalyzer()
        self.last_ai_error: Optional[str] = None

    def generate_sitemap(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None, ai_enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Generates a complete, validated sitemap object:
        {
          "website_type": "...",
          "brief": { ... },
          "pages": [ ... ]
        }
        """
        self.last_ai_error = None
        
        # 1. Analyze requirements & extract structured brief
        brief = self.analyzer.analyze(prompt, brief_data, ai_enabled=ai_enabled)
        website_type = brief.get('type') or 'Business Website'
        client_name = brief.get('client') or 'the company'
        category = brief.get('category') or 'business'

        # 2. Build page tree hierarchy
        raw_pages_tree = brief.get('pages_tree')
        raw_pages_list = brief.get('pages_list')

        if raw_pages_tree and len(raw_pages_tree) > 0:
            pages = self._build_tree_nodes(raw_pages_tree, brief, parent_id=None)
        elif raw_pages_list and len(raw_pages_list) > 0:
            pages = self._build_flat_nodes(raw_pages_list, brief)
        else:
            cat_defaults = self.analyzer.CATEGORIES.get(category, {}).get(
                'default_pages', ['Home', 'Services', 'About', 'Contact']
            )
            pages = self._build_flat_nodes(cat_defaults, brief)

        # 3. Ensure Home page is present at root position 0
        self._ensure_home_root(pages, brief)

        # 4. Generate section outlines for each page (AI or template heuristic)
        self._populate_sections_for_all_pages(pages, prompt, brief, ai_enabled=ai_enabled)

        # 5. Establish primary navigation flags and relationships
        self._assign_navigation_relationships(pages, brief)

        # 6. Assemble candidate sitemap dict
        candidate_sitemap = {
            'website_type': website_type,
            'brief': brief,
            'pages': pages
        }

        # 7. Self-healing repair & Pydantic v2 schema validation
        repaired_dict = repair_sitemap(candidate_sitemap)
        is_valid, validated_model, validation_errors = validate_sitemap(repaired_dict)

        if not is_valid:
            # Secondary fallback if validation found edge-case violations
            repaired_dict = repair_sitemap(repaired_dict)

        return repaired_dict

    def _build_tree_nodes(self, tree: List[Dict[str, Any]], brief: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recursively converts raw tree nodes into fully enriched SitemapPage nodes."""
        nodes: List[Dict[str, Any]] = []
        for idx, item in enumerate(tree):
            name = str(item.get('name') or 'Page').strip()
            if not name:
                continue

            node_id = str(item.get('id') or str(uuid.uuid4())[:8])
            raw_children = item.get('children', [])
            
            # Recurse for children
            children_nodes = self._build_tree_nodes(raw_children, brief, parent_id=node_id) if raw_children else []

            desc = self._generate_page_description(name, brief, is_child=(parent_id is not None))
            obj = self._generate_page_objective(name, brief, is_child=(parent_id is not None))

            nodes.append({
                'id': node_id,
                'name': name,
                'description': desc,
                'objective': obj,
                'is_primary_nav': (parent_id is None and idx < 6),
                'nav_label': name,
                'parent_id': parent_id,
                'order_index': idx,
                'sections': [],
                'children': children_nodes
            })
        return nodes

    def _build_flat_nodes(self, page_names: List[str], brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Builds a primary page list and automatically identifies common child subpages."""
        nodes: List[Dict[str, Any]] = []
        seen_names = set()

        for idx, name in enumerate(page_names):
            clean_name = str(name).strip()
            if not clean_name:
                continue
            name_key = clean_name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            node_id = str(uuid.uuid4())[:8]
            desc = self._generate_page_description(clean_name, brief, is_child=False)
            obj = self._generate_page_objective(clean_name, brief, is_child=False)

            # Check if domain-specific child pages should be nested
            children = self._generate_domain_child_pages(clean_name, brief, parent_id=node_id)

            nodes.append({
                'id': node_id,
                'name': clean_name,
                'description': desc,
                'objective': obj,
                'is_primary_nav': (idx < 6),
                'nav_label': clean_name,
                'parent_id': None,
                'order_index': idx,
                'sections': [],
                'children': children
            })
        return nodes

    def _ensure_home_root(self, pages: List[Dict[str, Any]], brief: Dict[str, Any]) -> None:
        """Guarantees a Home landing page is present at index 0."""
        home_idx = next((i for i, p in enumerate(pages) if p['name'].lower() in ('home', 'homepage')), None)
        if home_idx is not None and home_idx > 0:
            home_page = pages.pop(home_idx)
            pages.insert(0, home_page)
        elif home_idx is None:
            client = brief.get('client') or 'our company'
            home_id = str(uuid.uuid4())[:8]
            pages.insert(0, {
                'id': home_id,
                'name': 'Home',
                'description': f'Main landing page showcasing core value proposition and key services for {client}.',
                'objective': 'Welcome visitors, communicate primary value proposition, and drive key conversion actions.',
                'is_primary_nav': True,
                'nav_label': 'Home',
                'parent_id': None,
                'order_index': 0,
                'sections': [],
                'children': []
            })

        # Re-index
        for i, p in enumerate(pages):
            p['order_index'] = i

    def _generate_page_description(self, page_name: str, brief: Dict[str, Any], is_child: bool = False) -> str:
        """Produces contextual, rich, purpose-driven descriptions for each page."""
        lower = page_name.lower()
        client = brief.get('client') or 'the company'
        web_type = brief.get('type') or 'website'
        category = brief.get('category') or 'business'

        if 'home' in lower:
            return f"Comprehensive landing page introducing {client}, highlighting core solutions, and driving primary user conversion."
        if 'about' in lower or 'story' in lower:
            return f"Founding history, corporate mission, core values, leadership team, and credentials of {client}."
        if 'services' in lower:
            return f"Detailed overview of commercial solutions, deliverables, and service engagement tiers offered by {client}."
        if 'product' in lower or 'shop' in lower or 'catalog' in lower:
            return f"Interactive product catalog with category filters, item specifications, customer ratings, and purchase actions."
        if 'pricing' in lower or 'plans' in lower:
            return f"Transparent pricing tiers, feature comparison matrix, billing options, and money-back guarantee details."
        if 'contact' in lower:
            return f"Direct inquiry form, office location map, direct phone/email contact details, and customer support channels."
        if 'portfolio' in lower or 'work' in lower or 'case' in lower:
            return f"Curated showcase of completed client deliverables, creative work, measurable results, and client testimonials."
        if 'blog' in lower or 'news' in lower or 'insights' in lower or 'articles' in lower:
            return f"Industry articles, thought leadership publications, news announcements, and customer guides."
        if 'team' in lower or 'doctors' in lower or 'attorneys' in lower or 'faculty' in lower:
            return f"Profiles of key practitioners, leadership bios, areas of specialization, and professional achievements."
        if 'faq' in lower or 'help' in lower:
            return f"Frequently asked questions, troubleshooting guidelines, customer onboarding steps, and support routes."
        if 'cart' in lower or 'checkout' in lower:
            return f"Secure order review, billing and shipping address inputs, payment method selection, and order confirmation."
        if 'flight' in lower or 'booking' in lower:
            return f"Interactive reservation engine with departure/arrival search, fare calendar, seat selection, and checkout."
        if 'fixture' in lower or 'schedule' in lower:
            return f"Tournament match schedules, upcoming fixtures, venue details, and ticket reservation links."
        if 'standing' in lower or 'points table' in lower:
            return f"Live tournament rankings, points table, goal differences, and qualification status."

        if is_child:
            return f"Specialized subpage providing in-depth information, technical details, and direct actions for {page_name}."
        return f"Dedicated {page_name} page for {client} supporting user exploration and conversion within the {web_type}."

    def _generate_page_objective(self, page_name: str, brief: Dict[str, Any], is_child: bool = False) -> str:
        """Synthesizes explicit, conversion-focused page objectives."""
        lower = page_name.lower()
        if 'home' in lower:
            return "Capture visitor interest immediately, establish brand credibility, and route traffic to key conversion funnels."
        if 'about' in lower:
            return "Establish authentic trust and authority by presenting team credentials and institutional values."
        if 'services' in lower:
            return "Demonstrate capability, articulate clear business value, and prompt visitors to request service quotes."
        if 'product' in lower or 'shop' in lower:
            return "Facilitate effortless browsing, display transparent product benefits, and maximize add-to-cart conversions."
        if 'pricing' in lower:
            return "Eliminate buyer hesitation with transparent plan comparisons and guide visitors to the optimal subscription."
        if 'contact' in lower:
            return "Capture high-intent inquiries with minimal friction and provide immediate communication reassurance."
        if 'portfolio' in lower or 'case' in lower:
            return "Prove execution capability through verifiable case studies and quantifiable client outcomes."
        if 'faq' in lower:
            return "Deflect common customer objections, resolve pre-purchase doubts, and empower self-service resolution."
        if 'checkout' in lower or 'booking' in lower:
            return "Provide a trustworthy, distraction-free environment to complete payment or reservation smoothly."
        
        return f"Inform visitors regarding {page_name} and drive engagement toward core project goals."

    def _generate_domain_child_pages(self, page_name: str, brief: Dict[str, Any], parent_id: str) -> List[Dict[str, Any]]:
        """Intelligently generates subpages for parent categories if appropriate."""
        lower = page_name.lower()
        category = brief.get('category', 'business')
        children: List[Dict[str, Any]] = []

        subpage_specs: Dict[str, List[str]] = {
            'services': {
                'agency': ['Brand Identity', 'Digital Marketing', 'Web & App Design'],
                'corporate': ['Strategic Consulting', 'Operations & Logistics', 'Risk Management'],
                'healthcare': ['General Practice', 'Specialized Care', 'Preventative Diagnostics'],
                'default': ['Consulting', 'Implementation', 'Support & Maintenance']
            }.get(category, ['Consulting', 'Custom Solutions', 'Support & Training']),

            'products': {
                'ecommerce': ['New Arrivals', 'Best Sellers', 'Collections'],
                'saas': ['Core Platform', 'Integrations Hub', 'Mobile Suite'],
                'default': ['Featured Products', 'Accessories', 'Special Offers']
            }.get(category, ['Featured Items', 'Catalog Archive']),

            'about': ['Our Story', 'Leadership & Team', 'Mission & Values'],
            'destinations': ['Popular Getaways', 'Luxury Villas', 'Adventure Tours']
        }

        # Match parent page
        target_subpages: Optional[List[str]] = None
        for key, subs in subpage_specs.items():
            if key in lower:
                target_subpages = subs
                break

        if target_subpages and brief.get('page_count', 5) > 4:
            for s_idx, s_name in enumerate(target_subpages[:3]):
                s_id = str(uuid.uuid4())[:8]
                children.append({
                    'id': s_id,
                    'name': s_name,
                    'description': self._generate_page_description(s_name, brief, is_child=True),
                    'objective': self._generate_page_objective(s_name, brief, is_child=True),
                    'is_primary_nav': False,
                    'nav_label': s_name,
                    'parent_id': parent_id,
                    'order_index': s_idx,
                    'sections': [],
                    'children': []
                })

        return children

    def _assign_navigation_relationships(self, pages: List[Dict[str, Any]], brief: Dict[str, Any]) -> None:
        """Sets primary navigation flags and menu relationships."""
        nav_reqs = brief.get('navigation_requirements', {})
        preferred_nav = [p.lower() for p in nav_reqs.get('primary_nav', [])]

        primary_count = 0
        for page in pages:
            # Home is always in primary navigation
            if page['name'].lower() == 'home':
                page['is_primary_nav'] = True
                page['nav_label'] = 'Home'
                continue

            if preferred_nav and page['name'].lower() in preferred_nav:
                page['is_primary_nav'] = True
                primary_count += 1
            elif not preferred_nav and primary_count < 5:
                # Top 5 root pages default to primary navigation
                page['is_primary_nav'] = True
                primary_count += 1
            else:
                page['is_primary_nav'] = False

    def _populate_sections_for_all_pages(self, pages: List[Dict[str, Any]], prompt: str, brief: Dict[str, Any], ai_enabled: Optional[bool] = None) -> None:
        """Generates section outlines for each page, leveraging AI when available with heuristic fallback."""
        should_use_ai = ai_enabled if ai_enabled is not None else config.chat_ai_enabled
        ai_sections_map: Dict[str, List[Dict[str, Any]]] = {}

        if should_use_ai:
            ai_sections_map = self._ai_generate_section_stubs(prompt, brief, pages)

        def apply_sections_recursive(nodes: List[Dict[str, Any]]):
            for node in nodes:
                name = node['name']
                name_lower = name.lower()
                
                if name in ai_sections_map:
                    raw_ai_secs = ai_sections_map[name]
                    node['sections'] = self._normalize_sections(raw_ai_secs, name, brief)
                else:
                    node['sections'] = self._build_heuristic_sections(name_lower, brief)

                if node.get('children'):
                    apply_sections_recursive(node['children'])

        apply_sections_recursive(pages)

    def _normalize_sections(self, raw_sections: List[Dict[str, Any]], page_name: str, brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ensures AI generated sections follow the schema and maintain navbar/footer anchors."""
        cleaned: List[Dict[str, Any]] = []
        for s in raw_sections:
            if not isinstance(s, dict):
                continue
            title = str(s.get('title') or '').strip()
            raw_type = str(s.get('type') or 'content').strip().lower()
            canon_type = SECTION_TYPE_ALIASES.get(raw_type, raw_type)
            if not title:
                title = canon_type.capitalize()
            cleaned.append({
                'id': str(uuid.uuid4())[:8],
                'type': canon_type,
                'title': title,
                'description': str(s.get('description') or f'{title} section for {page_name}').strip(),
                'layoutVariant': 'layout-default'
            })

        # Ensure navbar at top and footer at bottom
        if not any(s['type'] == 'navbar' for s in cleaned):
            cleaned.insert(0, {'id': str(uuid.uuid4())[:8], 'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation bar', 'layoutVariant': 'layout-default'})
        if not any(s['type'] == 'footer' for s in cleaned):
            cleaned.append({'id': str(uuid.uuid4())[:8], 'type': 'footer', 'title': 'Footer', 'description': 'Global footer and legal links', 'layoutVariant': 'layout-default'})

        return cleaned

    def _build_heuristic_sections(self, page_name_lower: str, brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Constructs industry-specific, semantic section outlines for each page."""
        client = brief.get('client') or 'our company'
        category = brief.get('category') or 'business'
        objectives = brief.get('business_objectives', [])
        primary_obj = objectives[0] if objectives else f'Deliver value for {client}'
        features = brief.get('required_functionality', [])

        sections: List[Dict[str, Any]] = []

        def add(type_: str, title: str, desc: str, layout: str = 'layout-default'):
            canon = SECTION_TYPE_ALIASES.get(type_, type_)
            sections.append({
                'id': str(uuid.uuid4())[:8],
                'type': canon,
                'title': title,
                'description': desc,
                'layoutVariant': layout
            })

        # Global Header
        add('navbar', 'Navbar', f'Main navigation bar for {client}', 'layout-default')

        if 'home' in page_name_lower:
            add('hero', f'Welcome to {client}', f'High-impact hero banner communicating {primary_obj}', 'layout-split-right')
            add('features', 'Core Capabilities', 'Grid showcasing key competitive advantages and platform capabilities', 'layout-grid-3')
            add('main-info', 'How It Works', 'Step-by-step breakdown of how visitors achieve success with our service', 'layout-default')
            add('testimonial', 'What Our Clients Say', 'Verified customer reviews and industry trust badges', 'layout-default')
            add('cta', 'Take the Next Step', f'Compelling call to action to {brief.get("navigation_requirements", {}).get("cta_button", "Get Started")}', 'layout-centered')

        elif 'about' in page_name_lower:
            add('hero', f'About {client}', f'Our mission, vision, and the founding story behind {client}', 'layout-centered')
            add('story', 'Our Journey', 'Timeline tracing our growth, values, and milestone achievements', 'layout-default')
            add('team', 'Leadership Team', 'Meet the experienced specialists leading our mission', 'layout-grid-3')
            add('values', 'Our Core Principles', 'Integrity, innovation, and client commitment standards', 'layout-grid-3')
            add('cta', 'Join Our Journey', 'Connect with our leadership or explore career opportunities', 'layout-centered')

        elif 'services' in page_name_lower:
            add('hero', 'Our Services & Solutions', f'Tailored commercial solutions engineered for {brief.get("target_audience", "clients")}', 'layout-split-right')
            add('services-grid', 'Featured Service Offerings', 'Comprehensive catalog of primary service deliverables and packages', 'layout-grid-3')
            add('process', 'Engagement Process', 'Transparent roadmap from initial consultation to final delivery', 'layout-default')
            add('pricing', 'Service Tiers & Plans', 'Clear, transparent pricing and retainer engagement models', 'layout-default')
            add('cta', 'Request a Proposal', 'Submit project specifications for a customized timeline and quote', 'layout-centered')

        elif 'product' in page_name_lower or 'shop' in page_name_lower:
            add('hero', 'Shop Our Collection', f'Discover top-rated products curated by {client}', 'layout-default')
            add('filters', 'Filter & Refine', 'Instant filter controls for categories, price ranges, and ratings', 'layout-default')
            add('product-grid', 'All Products', 'Product cards with high-res imagery, pricing badges, and quick-add actions', 'layout-grid-3')
            add('promo', 'Special Offers', 'Seasonal discounts and bundled product savings', 'layout-default')

        elif 'pricing' in page_name_lower or 'plans' in page_name_lower:
            add('hero', 'Simple, Transparent Pricing', 'Select the tier that best accelerates your growth with zero hidden fees', 'layout-centered')
            add('pricing-table', 'Choose Your Plan', 'Multi-tier pricing comparison with monthly/annual toggle and feature checks', 'layout-grid-3')
            add('faq', 'Pricing FAQ', 'Answers to billing cycles, upgrade paths, cancellations, and refunds', 'layout-default')
            add('trust', 'Enterprise Security & Guarantee', '30-day money-back guarantee, SLA commitments, and payment badges', 'layout-default')

        elif 'contact' in page_name_lower:
            add('hero', 'Get in Touch', f'We would love to hear from you. Reach out to the {client} team today.', 'layout-centered')
            add('contact-form', 'Send a Message', 'Direct inquiry form with validation, department routing, and file attachment', 'layout-split-left')
            add('contact-details', 'Direct Contact Routes', 'Office address, direct telephone, email addresses, and support hours', 'layout-default')
            add('location', 'Find Our Office', 'Interactive map and visitor transportation guidance', 'layout-default')

        elif 'portfolio' in page_name_lower or 'work' in page_name_lower or 'case' in page_name_lower:
            add('hero', 'Featured Work & Case Studies', f'Explore our track record of measurable business impact for clients', 'layout-centered')
            add('gallery', 'Project Showcase', 'Interactive portfolio grid with live filtering by category and industry', 'layout-grid-3')
            add('stats', 'Impact by the Numbers', 'Quantifiable performance statistics and ROI results', 'layout-grid-4')
            add('cta', 'Let Us Build Your Next Success', 'Partner with our creative team on your upcoming initiative', 'layout-centered')

        elif 'flight' in page_name_lower or 'booking' in page_name_lower:
            add('search-form', 'Find Flights & Bookings', 'Origin, destination, dates, passengers, and cabin class selector', 'layout-default')
            add('offers', 'Featured Fares', 'Curated discounts and special seasonal destination packages', 'layout-grid-3')
            add('trust', 'Why Book With Us', 'Zero change fees, 24/7 customer assistance, and airline partners', 'layout-default')

        elif 'fixtures' in page_name_lower or 'schedule' in page_name_lower:
            add('hero', 'Tournament Fixtures', 'Full calendar of upcoming matches, venues, and timings', 'layout-default')
            add('main-info', 'Match Schedule', 'Categorized fixture list with date filters and team rosters', 'layout-default')
            add('cta', 'Get Match Tickets', 'Reserve passes for upcoming marquee matches', 'layout-centered')

        elif 'standing' in page_name_lower or 'points table' in page_name_lower:
            add('hero', 'Points Table & Standings', 'Current tournament standings, points, net run rates, and rankings', 'layout-default')
            add('main-info', 'League Table', 'Interactive ranking table updated in real-time', 'layout-default')

        else:
            # Universal tailored page fallback
            add('hero', f'{page_name_lower.capitalize()}', f'Key information and resources regarding {page_name_lower}', 'layout-split-right')
            add('main-info', f'Overview of {page_name_lower.capitalize()}', f'Detailed insights and core details supporting {client}', 'layout-default')
            add('supporting-info', 'Key Considerations', 'Supporting data, guidelines, and related documentation', 'layout-default')
            add('cta', 'Ready to Learn More?', f'Connect with {client} for additional information and next steps', 'layout-centered')

        # Global Footer
        add('footer', 'Footer', f'Global footer with navigation links, policies, and contact information for {client}', 'layout-default')

        return sections

    def _ai_generate_section_stubs(self, prompt: str, brief: Dict[str, Any], pages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Calls AI provider to generate tailored section arrays for each page."""
        page_names = [p['name'] for p in pages]
        system_instruction = "You are a professional UX architect. Generate semantic section lists for website pages in JSON."
        user_message = (
            f"Generate section outlines for these website pages: {json.dumps(page_names)}\n"
            f"Website Category: {brief.get('category')}\n"
            f"Website Type: {brief.get('type')}\n"
            f"Client Name: {brief.get('client')}\n"
            f"Business Objectives: {brief.get('goals')}\n"
            f"User Prompt: {prompt}\n\n"
            "Return a JSON object where each key is a page name, and the value is an array of section objects with: {type, title, description}.\n"
            "Include 'navbar' as the first section and 'footer' as the last section of each page."
        )

        req = CompletionRequest(
            prompt=user_message,
            system_instruction=system_instruction,
            temperature=0.2,
            max_tokens=1200,
            response_format={"type": "json_object"},
            timeout_seconds=25
        )
        resp = execute_completion_with_fallback(req)
        if not resp.success:
            self.last_ai_error = resp.error_message
            return {}

        parsed = resp.parse_as_json()
        if isinstance(parsed, dict):
            return parsed
        return {}

