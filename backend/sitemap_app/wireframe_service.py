"""
backend/sitemap_app/wireframe_service.py
Core Wireframe Generation Service for Website Design Automation System.
Phase 4 — AI Wireframe Generation Engine

Orchestrates page planning, AI layout generation with failover, deterministic fallback
synthesis, Pydantic v2 validation, self-healing repairs, and consistent multi-page structures.
"""

from __future__ import annotations
import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional

from core.config import config
from .page_planner import PagePlanner, PagePlan, PlannedSectionBlueprint
from .providers import (
    CompletionRequest,
    CompletionResponse,
    execute_completion_with_fallback,
    get_ai_provider
)
from .schemas.wireframe import (
    WireframeContainerModel,
    PageWireframeModel,
    WireframeSectionModel,
    SectionItemModel,
    SUPPORTED_LAYOUT_VARIANTS,
    LAYOUT_VARIANT_ALIASES,
    DEFAULT_ITEMS_BY_SECTION_TYPE,
    repair_wireframe_item,
    repair_wireframe_section,
    repair_page_wireframe,
    repair_wireframe_container,
    validate_wireframe,
    validate_page_wireframe
)
from .schemas.sitemap import (
    repair_sitemap,
    SECTION_TYPE_ALIASES,
    SUPPORTED_SECTION_TYPES
)

logger = logging.getLogger('sitemap_app')


def _attempt_json_repair(raw: str) -> Optional[Any]:
    """
    Attempts heuristic repair on malformed or truncated JSON strings:
    - Removes unescaped control characters
    - Cleans up trailing commas before ']' or '}'
    - Balances unclosed brackets and braces
    """
    if not raw or not isinstance(raw, str):
        return None

    cleaned = raw.strip()

    # Strip markdown fences
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Find candidate array or object
    start_arr = cleaned.find('[')
    start_obj = cleaned.find('{')

    target_start = -1
    is_array = False

    if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
        target_start = start_arr
        is_array = True
    elif start_obj != -1:
        target_start = start_obj
        is_array = False

    if target_start == -1:
        return None

    # Check for complete matching array or object
    if is_array:
        end_arr = cleaned.rfind(']')
        if end_arr > target_start:
            candidate = cleaned[target_start:end_arr + 1]
            candidate = re.sub(r',\s*([\]}])', r'\1', candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass
    else:
        end_obj = cleaned.rfind('}')
        if end_obj > target_start:
            candidate = cleaned[target_start:end_obj + 1]
            candidate = re.sub(r',\s*([\]}])', r'\1', candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass

    substring = cleaned[target_start:]

    # Remove trailing commas: e.g. , ] or , }
    substring = re.sub(r',\s*([\]}])', r'\1', substring)

    # Try parsing substring
    try:
        return json.loads(substring)
    except Exception:
        pass

    # Try balancing braces/brackets if truncated by token limit
    open_brackets = substring.count('[') - substring.count(']')
    open_braces = substring.count('{') - substring.count('}')

    balanced = substring
    # Close any open string quote
    if balanced.count('"') % 2 != 0:
        balanced += '"'

    # Remove trailing comma if string ended right after comma
    balanced = balanced.rstrip()
    if balanced.endswith(','):
        balanced = balanced[:-1]

    for _ in range(max(0, open_braces)):
        balanced += '}'
    for _ in range(max(0, open_brackets)):
        balanced += ']'

    try:
        return json.loads(balanced)
    except Exception:
        return None


class WireframeService:
    """
    Comprehensive Wireframe Generation and Validation Service.
    Supports multi-page wireframe generation, single-page on-demand generation,
    AI provider execution with graceful degradation, and Pydantic validation.
    """

    def __init__(self, ai_provider=None, page_planner: Optional[PagePlanner] = None):
        self.ai_provider = ai_provider
        self.page_planner = page_planner or PagePlanner()

    def generate_wireframes(
        self,
        sitemap_data: Dict[str, Any],
        page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate wireframes for all pages (or a single page) in the provided sitemap.
        Preserves shared project context across all pages.
        """
        if not isinstance(sitemap_data, dict):
            sitemap_data = {}

        # 1. Clean and normalize sitemap data
        repaired_sitemap = repair_sitemap(sitemap_data)
        website_type = repaired_sitemap.get('website_type', 'Website')
        brief = repaired_sitemap.get('brief', {})

        pages = repaired_sitemap.get('pages', [])
        wireframes_map: Dict[str, Any] = {}

        # 2. Collect flattened page list with paths
        flat_pages: List[Dict[str, Any]] = []

        def flatten(nodes: List[Dict[str, Any]], parent_path: str = ""):
            for p in nodes:
                if not isinstance(p, dict):
                    continue
                p_name = str(p.get('name') or 'Page').strip()
                p_path = f"{parent_path}/{p_name}" if parent_path else p_name
                flat_pages.append({
                    'page': p,
                    'path': p_path,
                    'id': str(p.get('id') or '').strip()
                })
                children = p.get('children')
                if isinstance(children, list) and children:
                    flatten(children, p_path)

        flatten(pages)

        # 3. Filter for specific page if requested
        if page_id:
            targets = [item for item in flat_pages if item['id'] == page_id]
            if not targets and flat_pages:
                targets = [flat_pages[0]]
        else:
            targets = flat_pages

        # 4. Generate wireframe for each target page
        for item in targets:
            p_obj = item['page']
            p_path = item['path']
            p_id = item['id'] or str(uuid.uuid4())[:8]

            page_wireframe = self.generate_page_wireframe(p_obj, p_path, repaired_sitemap)
            wireframes_map[p_id] = page_wireframe

        # 5. Assemble and repair complete container
        container_payload = {
            'website_type': website_type,
            'brief': brief,
            'wireframes': wireframes_map
        }

        sitemap_for_repair = repaired_sitemap
        if page_id and targets:
            sitemap_for_repair = dict(repaired_sitemap)
            sitemap_for_repair['pages'] = [t['page'] for t in targets]

        repaired_container = repair_wireframe_container(container_payload, sitemap_for_repair)

        # 6. Validate with Pydantic v2
        is_valid, validated_model, errors = validate_wireframe(repaired_container)
        if is_valid and validated_model:
            return validated_model.model_dump()

        logger.warning(f"Wireframe container validation fallback: {errors}")
        return repaired_container

    def generate_page_wireframe(
        self,
        page: Dict[str, Any],
        page_path: str,
        sitemap_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate wireframe structure for a single page using PagePlanner,
        AI completion with fallback, and deterministic validation.
        """
        if not isinstance(page, dict):
            page = {}

        # 1. Page Planning
        page_plan = self.page_planner.plan_page(page, page_path, sitemap_data)

        # 2. Try AI generation if enabled
        ai_sections = None
        if config.chat_ai_enabled:
            ai_sections = self._ai_generate_page(page_plan, sitemap_data)

        # 3. If AI generation failed or returned empty, use deterministic fallback
        if not ai_sections:
            sections = self._fallback_generate_page(page_plan, sitemap_data)
        else:
            sections = ai_sections

        # 4. Repair and structure single page wireframe
        raw_page_payload = {
            'page_name': page_plan.page_name,
            'page_path': page_plan.page_path,
            'page_id': page_plan.page_id,
            'objective': page_plan.purpose,
            'page_type': page_plan.page_category,
            'sections': sections
        }

        repaired_page = repair_page_wireframe(
            raw_page_payload,
            sitemap_menu_items=page_plan.global_navigation,
            brief=page_plan.branding,
            page_name_override=page_plan.page_name
        )

        # 5. Validate with Pydantic
        is_valid, validated_model, errors = validate_page_wireframe(repaired_page)
        if is_valid and validated_model:
            return validated_model.model_dump()

        return repaired_page

    def _ai_generate_page(
        self,
        page_plan: PagePlan,
        sitemap_data: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Dispatches structured AI generation for a page wireframe using the active AI provider.
        """
        system_instruction = (
            "You are an elite website UX/UI architect and conversion copywriting specialist. "
            "Generate production-grade wireframe sections tailored specifically to the given industry category and client brief. "
            "Strictly avoid placeholder copy such as 'Lorem ipsum', 'Feature 1', 'Item 1', 'Title here'. "
            "Every headline and body copy must be realistic, compelling, domain-specific, and conversion-focused. "
            "Ensure adjacent sections feature diverse, alternating layout variants (e.g. split -> grid -> cards -> centered). "
            "Return only a valid JSON array of section objects. Do not include markdown fences, "
            "explanations, or conversational prose."
        )

        # Prepare section blueprints representation for AI prompt
        blueprints_summary = []
        for s in page_plan.sections:
            blueprints_summary.append({
                'id': s.id,
                'type': s.type,
                'title': s.title,
                'description': s.description,
                'layoutVariant': s.layout_variant,
                'buttonText': s.button_text,
                'requires_items': s.requires_items
            })

        user_prompt = (
            f"Generate a complete wireframe section layout for the following website page:\n"
            f"- Industry Category: '{page_plan.website_category.upper()}'\n"
            f"- Page Name: '{page_plan.page_name}'\n"
            f"- Page Category: {page_plan.page_category}\n"
            f"- Page Path: {page_plan.page_path}\n"
            f"- Page Purpose: {page_plan.purpose}\n"
            f"- Primary Conversion Goal: {', '.join(page_plan.conversion_goals)}\n"
            f"- Primary CTA Button: '{page_plan.primary_cta}'\n"
            f"- Global Navigation Items: {json.dumps(page_plan.global_navigation)}\n"
            f"- Client / Brand Context: {json.dumps(page_plan.branding)}\n\n"
            f"Required Section Blueprints:\n{json.dumps(blueprints_summary, indent=2)}\n\n"
            "INSTRUCTIONS:\n"
            "1. Output a JSON array containing one object for each section in the required blueprints above.\n"
            "2. Preserve the same order and section types.\n"
            "3. For each section object, include:\n"
            "   - \"id\": string matching blueprint ID\n"
            "   - \"type\": canonical section type (e.g. navbar, hero, features, main-info, pricing, testimonial, cta, footer)\n"
            "   - \"title\": compelling, realistic headline refined for this industry\n"
            "   - \"description\": specific, professional body copy explaining value (2-3 sentences)\n"
            "   - \"layoutVariant\": layout string (e.g. layout-split-right, layout-grid-3, layout-cards, layout-centered, layout-multi-column)\n"
            "   - \"buttonText\": action label for hero, cta, pricing, contact, or navbar\n"
            "   - \"menuItems\": array of page names for navbar sections\n"
            "   - \"items\": array of item objects for features, services, pricing, stats, testimonials, faq, or footer\n"
            "4. For \"items\", provide objects with: {\"title\": \"...\", \"desc\": \"...\", \"icon\": \"LucideIconName\"}\n"
            "   - For testimonials, provide: {\"name\": \"...\", \"role\": \"...\", \"quote\": \"...\"}\n"
            "   - For pricing, provide: {\"title\": \"...\", \"price\": \"...\", \"tag\": \"...\", \"features\": [...]}\n"
            "   - For stats, provide: {\"value\": \"...\", \"title\": \"...\", \"desc\": \"...\"}\n"
            "   - For footer, provide: {\"title\": \"Column Header\", \"items\": [\"Link 1\", \"Link 2\", ...]}\n"
            "5. NO generic filler text like 'Lorem ipsum' or 'Feature 1'. Use high-quality, domain-tailored copy."
        )

        try:
            req = CompletionRequest(
                prompt=user_prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_tokens=2500,
                response_format={"type": "json_object"},
                timeout_seconds=config.ai_timeout_seconds
            )

            if isinstance(self.ai_provider, str):
                resp = execute_completion_with_fallback(req, preferred_provider=self.ai_provider)
            elif hasattr(self.ai_provider, 'complete'):
                resp = self.ai_provider.complete(req)
                if not resp.success:
                    resp = execute_completion_with_fallback(req)
            else:
                resp = execute_completion_with_fallback(req)

            if not resp.success or not resp.content:
                logger.warning(f"Wireframe AI generation failed: {resp.error_message}")
                return None

            # Multi-stage parsing & repair
            parsed = resp.parse_as_json()
            if parsed is None:
                parsed = _attempt_json_repair(resp.content)

            # If wrapped in a container object: {"sections": [...]}
            if isinstance(parsed, dict):
                if 'sections' in parsed and isinstance(parsed['sections'], list):
                    parsed = parsed['sections']
                elif 'wireframe' in parsed and isinstance(parsed['wireframe'], list):
                    parsed = parsed['wireframe']
                elif 'wireframes' in parsed and isinstance(parsed['wireframes'], list):
                    parsed = parsed['wireframes']

            if not isinstance(parsed, list) or len(parsed) == 0:
                logger.warning("AI response did not parse into a list of section objects")
                return None

            # Normalize sections against blueprints
            cleaned_sections = []
            for idx, raw_sec in enumerate(parsed):
                if not isinstance(raw_sec, dict):
                    continue
                blueprint = page_plan.sections[idx] if idx < len(page_plan.sections) else None
                fallback_type = blueprint.type if blueprint else 'content'
                fallback_id = blueprint.id if blueprint else str(uuid.uuid4())[:8]

                cleaned_sections.append({
                    'id': str(raw_sec.get('id') or fallback_id).strip(),
                    'type': str(raw_sec.get('type') or fallback_type).strip(),
                    'title': str(raw_sec.get('title') or (blueprint.title if blueprint else 'Section')).strip(),
                    'description': str(raw_sec.get('description') or (blueprint.description if blueprint else '')).strip(),
                    'layoutVariant': str(raw_sec.get('layoutVariant') or (blueprint.layout_variant if blueprint else 'layout-default')).strip(),
                    'buttonText': str(raw_sec.get('buttonText') or (blueprint.button_text if blueprint else '')).strip(),
                    'secondaryButtonText': str(raw_sec.get('secondaryButtonText') or (blueprint.secondary_button_text if blueprint else '')).strip(),
                    'menuItems': raw_sec.get('menuItems') or page_plan.global_navigation,
                    'items': raw_sec.get('items') or []
                })

            return cleaned_sections

        except Exception as e:
            logger.error(f"Error in _ai_generate_page: {e}", exc_info=True)
            return None

    def _get_category_specific_items(self, section_type: str, website_category: str, client: str) -> List[Dict[str, Any]]:
        """
        Returns rich, domain-adapted section items tailored to the website category
        to eliminate generic placeholder copy ('Feature 1', 'Lorem ipsum', etc.).
        """
        stype = (section_type or '').lower()
        wcat = (website_category or 'business').lower()

        catalog = {
            'agriculture': {
                'features': [
                    {'title': 'Certified Organic Harvests', 'desc': '100% Non-GMO verified produce grown with regenerative soil practices.', 'icon': 'leaf'},
                    {'title': 'Precision Agronomy & Irrigation', 'desc': 'Smart sensor water management preserving regional freshwater aquifers.', 'icon': 'droplet'},
                    {'title': 'Cold-Chain Supply Network', 'desc': 'Rapid 48-hour farm-to-distributor climate controlled shipping logistics.', 'icon': 'truck'}
                ],
                'process': [
                    {'title': 'Soil Remediation & Seeding', 'desc': 'Natural compost enrichment and certified organic seed selection.', 'icon': 'sprout'},
                    {'title': 'Autonomous Crop Monitoring', 'desc': 'Continuous multispectral drone inspection tracking crop health and vigor.', 'icon': 'shieldCheck'},
                    {'title': 'Wholesale Cold Packing', 'desc': 'Immediate sorting, sanitizing, and cold-pack shipping from on-site packing hubs.', 'icon': 'box'}
                ],
                'stats': [
                    {'value': '50,000+', 'title': 'Acres Cultivated', 'desc': 'Dedicated regenerative organic farmland'},
                    {'value': '100%', 'title': 'Certified Non-GMO', 'desc': 'Full origin verification across all harvests'},
                    {'value': '12,000', 'title': 'Tons Annual Yield', 'desc': 'Consistent high-yield fresh seasonal supply'},
                    {'value': '48 hrs', 'title': 'Farm to Distributor', 'desc': 'Guaranteed peak freshness delivery window'}
                ],
                'gallery': [
                    {'title': 'Greenhouse Hydroponics', 'desc': 'Automated indoor arrays producing fresh leafy greens year-round.'},
                    {'title': 'Heirloom Orchard Harvest', 'desc': 'Sun-ripened organic fruit orchards during peak autumn harvest.'},
                    {'title': 'Distribution Fleet Logistics', 'desc': 'Climate-controlled delivery fleet preparing for daily commercial dispatches.'}
                ],
                'testimonial': [
                    {'name': 'Marcus Vance', 'role': 'Supply Chain Director, OrganicMarket Co.', 'quote': 'Their consistency in crop quality and cold-chain reliability is the gold standard for regional produce distribution.'},
                    {'name': 'Dr. Sarah Lin', 'role': 'Head Agronomist, Sustainable Ag Alliance', 'quote': 'The soil carbon sequestration metrics achieved on their farmland serve as a benchmark for modern commercial agriculture.'},
                    {'name': 'Thomas Keller', 'role': 'Executive Chef, Heritage Dining Group', 'quote': 'The flavor profile and freshness of their heirloom crops have elevated our seasonal tasting menus year after year.'}
                ]
            },
            'restaurant': {
                'features': [
                    {'title': 'Seasonal Tasting Menus', 'desc': 'Seven-course culinary narratives inspired by regional micro-climates and farmers.', 'icon': 'utensils'},
                    {'title': 'Artisan Cellar Pairings', 'desc': 'Rare biodynamic wines and bespoke non-alcoholic infusions curated by our sommelier.', 'icon': 'wine'},
                    {'title': 'Zero-Waste Kitchen', 'desc': 'Whole-ingredient gastronomy turning every element into exquisite sauces and ferments.', 'icon': 'sparkles'}
                ],
                'story': [
                    {'title': 'Culinary Heritage', 'desc': 'Founded on time-honored open-fire cooking techniques refined over two decades.', 'icon': 'flame'},
                    {'title': 'Direct Farm Partnerships', 'desc': 'Daily morning deliveries from independent regional growers and coastal day-boats.', 'icon': 'heart'},
                    {'title': 'Private Dining Salon', 'desc': 'Intimate dining space accommodating up to 24 guests with customized menus.', 'icon': 'users'}
                ],
                'stats': [
                    {'value': 'Michelin', 'title': 'Recommended Guide 2024', 'desc': 'Celebrated for inventive regional cuisine'},
                    {'value': '100%', 'title': 'Organic Farm Partners', 'desc': 'Sourced entirely from independent local growers'},
                    {'value': '4.9 / 5', 'title': 'Guest Review Rating', 'desc': 'Consistently praised for service and ambiance'},
                    {'value': '15+', 'title': 'Culinary Awards Won', 'desc': 'Recognized across leading gastronomy publications'}
                ],
                'testimonial': [
                    {'name': 'Julian Moreau', 'role': 'Senior Food Critic, Le Guide Gastronomique', 'quote': 'An unforgettable sensory journey. The mastery of texture and balance in their seasonal menu is unmatched.'},
                    {'name': 'Sophia Sterling', 'role': 'Private Event Host', 'quote': 'Hosting our corporate celebration in their private salon was effortless. The wine pairings and service were sublime.'},
                    {'name': 'David Thorne', 'role': 'Verified Diner', 'quote': 'Easily one of the top five dining experiences of my life. The smoked duck and honey glaze was pure art.'}
                ]
            },
            'healthcare': {
                'services': [
                    {'title': 'Cardiovascular Medicine', 'desc': 'Advanced diagnostics, preventative cardiac care, and non-invasive surgical treatments.', 'icon': 'activity'},
                    {'title': 'Neurology & Brain Health', 'desc': 'Comprehensive clinical neurological evaluations and cutting-edge rehabilitation protocols.', 'icon': 'brain'},
                    {'title': 'Pediatric Healthcare', 'desc': 'Compassionate, gentle developmental healthcare for infants, children, and adolescents.', 'icon': 'users'},
                    {'title': '24/7 Emergency Trauma', 'desc': 'Accredited acute emergency response team equipped with modern diagnostic imaging.', 'icon': 'shieldAlert'}
                ],
                'features': [
                    {'title': 'Board-Certified Faculty', 'desc': 'Over 120 leading medical doctors with decades of university hospital experience.', 'icon': 'award'},
                    {'title': 'Rapid Lab Diagnostics', 'desc': 'On-site pathology and radiology delivering accurate clinical results in hours.', 'icon': 'microscope'},
                    {'title': 'Digital Patient Portal', 'desc': 'Instant telehealth appointments, secure medical records, and prescription refills.', 'icon': 'smartphone'}
                ],
                'team': [
                    {'name': 'Dr. Eleanor Vance, MD', 'role': 'Chief of Cardiology', 'desc': 'Harvard Medical School graduate with 18 years in non-invasive coronary interventions.'},
                    {'name': 'Dr. Robert Chen, MD, PhD', 'role': 'Director of Neurology', 'desc': 'Pioneering clinical researcher specializing in neurodegenerative care and brain imaging.'},
                    {'name': 'Dr. Sarah Patel, MD', 'role': 'Head of Pediatric Care', 'desc': 'Passionate advocate for holistic child wellness and early developmental medicine.'}
                ],
                'stats': [
                    {'value': '50,000+', 'title': 'Patients Treated', 'desc': 'Delivering compassionate clinical care annually'},
                    {'value': '99.2%', 'title': 'Clinical Satisfaction', 'desc': 'Consistently ranked highest in regional patient care'},
                    {'value': '120+', 'title': 'Board Specialists', 'desc': 'Comprehensive expertise across 28 specialties'},
                    {'value': '24/7', 'title': 'Emergency Response', 'desc': 'Always open with zero waiting room triage delays'}
                ],
                'testimonial': [
                    {'name': 'Margaret Holloway', 'role': 'Cardiac Patient', 'quote': 'The cardiology team saved my life. Their attentiveness, clear communication, and modern facility gave me total peace of mind.'},
                    {'name': 'James Sullivan', 'role': 'Emergency Care Patient', 'quote': 'I was admitted and treated within 15 minutes of arriving. The clinical staff was compassionate and remarkably thorough.'},
                    {'name': 'Rebecca Diaz', 'role': 'Parent of Pediatric Patient', 'quote': 'Dr. Patel made my daughter feel calm and cared for. We will never go anywhere else for family healthcare.'}
                ]
            },
            'education': {
                'services': [
                    {'title': 'Computer Science & AI', 'desc': 'Accredited undergraduate and graduate programs covering machine learning, systems, and security.', 'icon': 'cpu'},
                    {'title': 'Business Administration', 'desc': 'Executive leadership, venture finance, and global market strategy degrees.', 'icon': 'briefcase'},
                    {'title': 'Bioengineering & Health', 'desc': 'Translational research laboratory programs bridging biology and medical devices.', 'icon': 'dna'},
                    {'title': 'Liberal Arts & Design', 'desc': 'Interdisciplinary curricula in digital ethics, interactive design, and communication.', 'icon': 'bookOpen'}
                ],
                'features': [
                    {'title': 'World-Renowned Faculty', 'desc': 'Learn from MacArthur Fellows, Nobel laureates, and industry pioneers.', 'icon': 'award'},
                    {'title': 'Modern Research Labs', 'desc': 'Over $40M invested in campus supercomputing, robotics, and biology facilities.', 'icon': 'flaskConical'},
                    {'title': 'Global Study Programs', 'desc': 'Semester abroad exchange partnerships across 35 countries worldwide.', 'icon': 'globe'}
                ],
                'stats': [
                    {'value': '94%', 'title': 'Graduate Placement', 'desc': 'Employed or in graduate study within 6 months'},
                    {'value': '15 : 1', 'title': 'Student-to-Faculty', 'desc': 'Intimate seminar learning and direct research access'},
                    {'value': '$12M+', 'title': 'Annual Research Grants', 'desc': 'Funding breakthrough student and faculty discoveries'},
                    {'value': '45+', 'title': 'Global Partner Hubs', 'desc': 'International campus study and exchange programs'}
                ],
                'testimonial': [
                    {'name': 'Elena Rostova', 'role': 'Class of 2024 (Now Software Engineer at Google)', 'quote': 'The rigor of the curriculum and the mentorship from professors prepared me for the highest levels of tech engineering.'},
                    {'name': 'Marcus Vance', 'role': 'Alumni & Biotech Founder', 'quote': 'My company began as a senior capstone project in the university lab. The entrepreneurial support was unmatched.'},
                    {'name': 'Dr. Catherine Hayes', 'role': 'Visiting Professor, Oxford', 'quote': 'The intellectual curiosity of students here creates one of the most vibrant seminar environments in the world.'}
                ]
            },
            'ecommerce': {
                'product-grid': [
                    {'title': 'Minimalist Ergonomic Chair', 'desc': 'Breathable mesh with 4D armrest adjustment and dynamic lumbar contour.', 'price': '$349', 'tag': 'BEST SELLER', 'icon': 'shoppingBag'},
                    {'title': 'Precision Studio Headphones', 'desc': 'Lossless acoustic drivers, active noise cancellation, and 40hr battery life.', 'price': '$199', 'tag': 'NEW', 'icon': 'headphones'},
                    {'title': 'Anodized Aluminum Desk Lamp', 'desc': 'Warm circadian dimming with built-in wireless charging pad.', 'price': '$89', 'tag': 'POPULAR', 'icon': 'sparkles'}
                ],
                'features': [
                    {'title': 'Carbon-Neutral Delivery', 'desc': 'Free express shipping on all domestic orders over $50 with eco-friendly packaging.', 'icon': 'truck'},
                    {'title': '30-Day Hassle-Free Returns', 'desc': 'Prepaid return labels and instant refunds with zero restocking fees.', 'icon': 'rotateCcw'},
                    {'title': '256-Bit Encrypted Checkout', 'desc': 'Seamless payment support for Apple Pay, Google Pay, cards, and installment plans.', 'icon': 'shieldCheck'},
                    {'title': 'Dedicated Concierge Support', 'desc': 'Friendly 24/7 product specialists ready to assist via live chat and phone.', 'icon': 'headphones'}
                ],
                'stats': [
                    {'value': '500,000+', 'title': 'Orders Delivered', 'desc': 'Trusted by satisfied customers worldwide'},
                    {'value': '4.9 / 5', 'title': 'Customer Review Score', 'desc': 'Over 25,000 verified five-star product ratings'},
                    {'value': '99.8%', 'title': 'On-Time Dispatch', 'desc': 'Same-day warehouse fulfillment on stock items'},
                    {'value': '100%', 'title': 'Guaranteed Satisfaction', 'desc': 'Full money-back promise on every purchase'}
                ],
                'testimonial': [
                    {'name': 'Chloe Bennett', 'role': 'Verified Customer', 'quote': 'The build quality exceeded my expectations. Shipping was lightning-fast and the customer support was incredible.'},
                    {'name': 'Liam Henderson', 'role': 'Verified Customer', 'quote': 'Returning an incorrect size was completely painless. New size arrived two days later. Customer for life!'},
                    {'name': 'Maya Patel', 'role': 'Verified Customer', 'quote': 'Beautiful minimalist design and durable materials. Definitely worth every dollar.'}
                ]
            },
            'saas': {
                'features': [
                    {'title': 'Automated Deployment Pipelines', 'desc': 'Zero-configuration CI/CD with automatic branch previews and instant rollbacks.', 'icon': 'zap'},
                    {'title': 'Enterprise End-to-End Security', 'desc': 'SOC2 Type II, HIPAA, and GDPR compliance with role-based team permissions.', 'icon': 'lock'},
                    {'title': 'Unified Real-Time Telemetry', 'desc': 'High-cardinality distributed tracing and actionable performance alerts in one dashboard.', 'icon': 'barChart'},
                    {'title': 'Comprehensive REST & GraphQL APIs', 'desc': 'Build custom automations with strongly typed SDKs for TypeScript, Python, and Go.', 'icon': 'terminal'}
                ],
                'pricing': [
                    {'title': 'Starter', 'price': '$29', 'tag': 'ESSENTIALS', 'features': ['Up to 5 team seats', '10,000 API requests/day', 'Community Discord support', 'Standard metrics dashboard']},
                    {'title': 'Pro', 'price': '$89', 'tag': 'MOST POPULAR', 'features': ['Up to 25 team seats', '1M API requests/day', 'Priority 24/7 email & chat', 'Advanced telemetry & alerts', 'Custom webhooks']},
                    {'title': 'Enterprise', 'price': '$299', 'tag': 'DEDICATED', 'features': ['Unlimited team members', 'Unlimited API throughput', 'Dedicated technical account manager', 'Custom 99.99% SLA', 'SOC2 compliance exports']}
                ],
                'stats': [
                    {'value': '99.99%', 'title': 'Guaranteed SLA', 'desc': 'Multi-region redundancy with automatic failover'},
                    {'value': '500M+', 'title': 'API Calls Handled Daily', 'desc': 'Proven high-throughput production resilience'},
                    {'value': '< 15 ms', 'title': 'Global Edge Latency', 'desc': 'Distributed nodes across 45 worldwide datacenters'},
                    {'value': '10,000+', 'title': 'Engineering Teams', 'desc': 'From high-growth startups to Fortune 500 enterprises'}
                ],
                'testimonial': [
                    {'name': 'Alex Rivera', 'role': 'VP of Engineering, CloudScale Systems', 'quote': 'This platform reduced our deployment cycle time by 70%. It paid for itself in engineering productivity within two weeks.'},
                    {'name': 'Samantha Wu', 'role': 'Head of Product, FinFlow', 'quote': 'The reliability and API documentation are top notch. Easily the best developer tooling decision we made this year.'},
                    {'name': 'David Thorne', 'role': 'Lead DevOps Architect, NextGen Media', 'quote': 'Our team handles hundreds of millions of requests with zero latency jitter. An indispensable tool.'}
                ]
            },
            'portfolio': {
                'features': [
                    {'title': 'Design Systems & Architecture', 'desc': 'Scalable design tokens, accessible component libraries, and Figma-to-code pipelines.', 'icon': 'layers'},
                    {'title': 'Interactive Motion & 3D Web', 'desc': 'WebGL, Three.js, and fluid shader animations optimized for 60fps performance.', 'icon': 'sparkles'},
                    {'title': 'User Research & Product Strategy', 'desc': 'Qualitative user interviews, rapid prototypes, and data-driven usability testing.', 'icon': 'compass'}
                ],
                'gallery': [
                    {'title': 'AI Workflow Canvas', 'desc': 'End-to-end UX/UI and node architecture for an enterprise generative AI builder.'},
                    {'title': 'NeoBank Mobile App', 'desc': 'Global consumer banking app with real-time currency conversions and savings vaults.'},
                    {'title': 'Design Tokens Studio', 'desc': 'Open-source design system tooling syncing styles between Figma and React.'}
                ],
                'stats': [
                    {'value': '12+', 'title': 'Years Experience', 'desc': 'Designing high-impact digital products'},
                    {'value': '40+', 'title': 'Products Shipped', 'desc': 'Across FinTech, AI, and Consumer Tech'},
                    {'value': '8', 'title': 'Awwwards & FWA Honors', 'desc': 'Recognized for interactive digital design'},
                    {'value': '100%', 'title': 'Independent Ownership', 'desc': 'Dedicated end-to-end craft on every engagement'}
                ],
                'testimonial': [
                    {'name': 'Marcus Vance', 'role': 'Creative Director, Studio Hyper', 'quote': 'A rare hybrid talent who understands pixel perfection and production code equally well.'},
                    {'name': 'Elena Rostova', 'role': 'Founder, Nova Labs', 'quote': 'Delivered our flagship product design on an impossible timeline. Our seed investors were blown away.'}
                ]
            },
            'agency': {
                'features': [
                    {'title': 'Brand Strategy & Identity', 'desc': 'Distinct brand positioning, naming, and visual identity systems that command market authority.', 'icon': 'sparkles'},
                    {'title': 'High-Conversion Web Platforms', 'desc': 'Modern responsive digital experiences engineered for maximum conversion velocity.', 'icon': 'monitor'},
                    {'title': 'Full-Funnel Growth Marketing', 'desc': 'Strategic paid acquisition, content production, and conversion rate optimization sprints.', 'icon': 'trendingUp'}
                ],
                'process': [
                    {'title': 'Discovery & Market Intelligence', 'desc': 'In-depth stakeholder immersion, competitor analysis, and audience research.', 'icon': 'search'},
                    {'title': 'Strategic Prototyping', 'desc': 'Interactive design prototypes validated with target customers before engineering.', 'icon': 'layout'},
                    {'title': 'Full-Stack Execution & Launch', 'desc': 'Production-ready headless web implementation with global CDN optimization.', 'icon': 'rocket'}
                ],
                'stats': [
                    {'value': '45+', 'title': 'Global Design Awards', 'desc': 'Recognized across Cannes Lions, D&AD, and Awwwards'},
                    {'value': '3.8x', 'title': 'Average Client ROI', 'desc': 'Measurable revenue uplift across client launches'},
                    {'value': '$250M+', 'title': 'Client Funding Raised', 'desc': 'Helped 30+ startups successfully close capital rounds'},
                    {'value': '100%', 'title': 'On-Time Sprint Delivery', 'desc': 'Disciplined agile execution with zero scope creep'}
                ],
                'testimonial': [
                    {'name': 'Rachel Chen', 'role': 'CMO, Apex Systems', 'quote': 'They transformed our market positioning completely. Our inbound enterprise sales inquiries increased by 240%.'},
                    {'name': 'Julian Moreau', 'role': 'Founder & CEO, Veloce Mobility', 'quote': 'The strategic clarity and design execution they brought to our launch was worth tenfold our investment.'}
                ]
            },
            'blog': {
                'features': [
                    {'title': 'Investigative Technical Essays', 'desc': 'Deep dives into distributed systems, generative AI ethics, and product design craft.', 'icon': 'newspaper'},
                    {'title': 'Weekly Curated Briefing', 'desc': 'Hand-filtered signals without noise, delivered directly to your inbox every Tuesday morning.', 'icon': 'mail'},
                    {'title': 'Audio Article Narrations', 'desc': 'Professionally narrated studio recordings for every published longform essay.', 'icon': 'headphones'}
                ],
                'team': [
                    {'name': 'Sarah Jenkins', 'role': 'Editor-in-Chief', 'desc': 'Former technology correspondent at MIT Technology Review with 14 years reporting.'},
                    {'name': 'Dr. Aris Thorne', 'role': 'Senior Technical Editor', 'desc': 'Distributed systems researcher focusing on cloud infrastructure and database internals.'},
                    {'name': 'Maya Lin', 'role': 'Design & Culture Critic', 'desc': 'Investigating the cultural implications of synthetic media, interfaces, and architecture.'}
                ],
                'stats': [
                    {'value': '75,000+', 'title': 'Active Subscribers', 'desc': 'Engineers, founders, and technical designers'},
                    {'value': '250+', 'title': 'Longform Publications', 'desc': 'Thoroughly researched, cited technical essays'},
                    {'value': '45', 'title': 'Industry Contributors', 'desc': 'Writers from leading research labs and universities'},
                    {'value': '1.2M', 'title': 'Monthly Pageviews', 'desc': 'Read by practitioners across 120 countries'}
                ],
                'testimonial': [
                    {'name': 'Dr. Aris Thorne', 'role': 'Research Fellow, AI Safety Institute', 'quote': 'Their publications consistently provide the most rigorous and nuanced perspectives in modern tech journalism.'},
                    {'name': 'Sophie Martin', 'role': 'Staff Engineer, Stripe', 'quote': 'The only technical newsletter that never ends up in my archive unread. Essential reading.'}
                ]
            },
            'business': {
                'services': [
                    {'title': 'Management Consulting', 'desc': 'Executive advisory on corporate restructuring, capital allocation, and performance turnaround.', 'icon': 'briefcase'},
                    {'title': 'Enterprise Cloud Architecture', 'desc': 'Modernizing legacy architectures with secure cloud-native platforms and microservices.', 'icon': 'cloud'},
                    {'title': 'Regulatory Compliance & Risk', 'desc': 'Governance frameworks ensuring compliance across global regulatory jurisdictions.', 'icon': 'shieldCheck'},
                    {'title': 'Supply Chain Optimization', 'desc': 'Data-driven logistics planning reducing procurement cycle times and overhead.', 'icon': 'truck'}
                ],
                'features': [
                    {'title': 'Enterprise Strategic Advisory', 'desc': 'Guiding corporate executives through market entry, M&A integration, and capital allocation.', 'icon': 'briefcase'},
                    {'title': 'Digital Transformation & Cloud', 'desc': 'Modernizing legacy ERP and data architectures with scalable cloud-native microservices.', 'icon': 'cloud'},
                    {'title': 'Operational Risk & Compliance', 'desc': 'Comprehensive governance frameworks safeguarding institutional assets and regulatory alignment.', 'icon': 'shieldCheck'}
                ],
                'stats': [
                    {'value': '$1.2B+', 'title': 'Client Value Generated', 'desc': 'Audited cost efficiencies and new revenue unlocked'},
                    {'value': '500+', 'title': 'Enterprise Engagements', 'desc': 'Partnering with leading Fortune 1000 organizations'},
                    {'value': '98%', 'title': 'Client Retention Rate', 'desc': 'Long-standing multi-year advisory relationships'},
                    {'value': '35', 'title': 'Global Office Hubs', 'desc': 'Advisors operating across North America, Europe, and Asia'}
                ],
                'testimonial': [
                    {'name': 'Robert Sterling', 'role': 'Managing Director, Global Logistics Partners', 'quote': 'Their advisory team identified over $14M in supply chain redundancies within six months. Extraordinary ROI.'},
                    {'name': 'Claire Dupont', 'role': 'Chief Financial Officer, Aegis Financial Group', 'quote': 'A trusted strategic partner. Their institutional rigor and market insights have been invaluable.'}
                ]
            }
        }

        cat_data = catalog.get(wcat, catalog['business'])
        if stype in cat_data:
            return [dict(item) for item in cat_data[stype]]

        return []

    def _fallback_generate_page(
        self,
        page_plan: PagePlan,
        sitemap_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        High-quality deterministic fallback generator that produces tailored,
        domain-adapted wireframe sections directly from the PagePlan and Brief.
        """
        client = page_plan.branding.get('client') or 'Our Company'
        sections: List[Dict[str, Any]] = []

        for blueprint in page_plan.sections:
            stype = blueprint.type
            stitle = blueprint.title
            sdesc = blueprint.description
            slayout = blueprint.layout_variant
            sbtn = blueprint.button_text
            ssec_btn = blueprint.secondary_button_text

            if not sdesc:
                sdesc = self.regenerate_section_description(stitle, stype, page_plan.page_name, page_plan.branding)

            # Infill items using category-specific catalog first, then default schema items
            items = []
            if blueprint.requires_items:
                cat_items = self._get_category_specific_items(stype, page_plan.website_category, client)
                if cat_items:
                    items = cat_items
                else:
                    defaults = DEFAULT_ITEMS_BY_SECTION_TYPE.get(stype, [])
                    for item_dict in defaults:
                        items.append(dict(item_dict))

            # Assemble section dict
            sections.append({
                'id': blueprint.id,
                'type': stype,
                'title': stitle,
                'description': sdesc,
                'layoutVariant': slayout,
                'buttonText': sbtn,
                'secondaryButtonText': ssec_btn,
                'menuItems': page_plan.global_navigation if stype == 'navbar' else [],
                'items': items
            })

        return sections

    def regenerate_section_description(
        self,
        title: str,
        section_type: str,
        page_name: str = "",
        brief: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate varied, high-quality descriptive copy for a section.
        """
        import random
        t = str(title or page_name or 'Section').strip()
        p = str(page_name or 'this page').strip()
        c = str((brief or {}).get('client') or 'the organization').strip()
        raw_type = str(section_type or 'content').strip().lower()
        st = SECTION_TYPE_ALIASES.get(raw_type, raw_type)

        variations = {
            'navbar': [
                f"Global navigation header featuring {c}'s logo, primary site links, and direct conversion action.",
                "Clean, sticky navigation bar providing frictionless access to key product and company pages.",
                "Modern header with responsive menu controls, brand identity, and prioritized call-to-action."
            ],
            'hero': [
                f"High-impact introductory banner for {t} communicating the core value proposition and motivating user action.",
                f"Engaging hero section for {t} pairing an authoritative headline with clear supporting value statements.",
                f"Visually compelling header setting the stage for {p} with bold typography and prominent action buttons."
            ],
            'features': [
                f"Three-card capability grid detailing core architectural benefits, operational speed, and ease of integration.",
                f"Feature matrix illustrating key differentiators and technical solutions built to resolve customer pain points.",
                f"Interactive feature overview emphasizing performance, scalability, and measurable outcomes for {c}."
            ],
            'services': [
                f"Comprehensive service catalog for {t} detailing engagement deliverables, methodology, and scope.",
                f"Tailored service offerings designed to accelerate time-to-value and ensure predictable outcomes.",
                f"Specialized client solutions structured into transparent tiers with clear deliverables and support."
            ],
            'pricing': [
                f"Transparent subscription tiers for {t} with clear feature breakdowns, billing options, and tier badges.",
                "Predictable, scalable pricing plans designed to accommodate early-stage teams up to enterprise operations.",
                "Detailed feature comparison table providing full visibility into tier limits, SLAs, and support levels."
            ],
            'testimonial': [
                f"Verified client reviews and endorsements highlighting tangible business impact and operational efficiency.",
                f"Social proof showcase featuring executive testimonials, partner badges, and quantitative success metrics.",
                f"Direct quotes from engineering leads and founders who transformed their operations using {c}."
            ],
            'stats': [
                f"Quantitative performance metrics demonstrating {c}'s global scale, high availability, and customer satisfaction.",
                "Proven track record counters highlighting transaction volume, uptime reliability, and worldwide user adoption.",
                "Key performance indicators illustrating measurable business acceleration and industry leadership."
            ],
            'team': [
                f"Leadership and advisory board members driving {c}'s strategic vision and product innovation.",
                "Experienced multidisciplinary leaders combining deep technical background with customer-centric focus.",
                "Executive profiles detailing founding members, engineering heads, and key division leads."
            ],
            'faq': [
                f"Answers to frequent questions regarding implementation, security compliance, billing, and technical support.",
                f"Curated list of common pre-sales inquiries and technical answers to streamline decision making for {p}.",
                "Comprehensive knowledgebase answers addressing security, onboarding, and platform capabilities."
            ],
            'contact': [
                f"Direct communication channels including interactive inquiry form, office location, and priority support contacts.",
                f"Connect with {c}'s dedicated solutions architects for custom demonstrations, pricing, and onboarding support.",
                "Frictionless contact pathways with categorized inquiry routing and guaranteed response SLAs."
            ],
            'contact-form': [
                "Interactive multi-field inquiry form with validation, inquiry categorization, and instant confirmation.",
                "Direct contact form allowing prospective partners to request detailed proposals and schedule consultations.",
                "Streamlined inquiry portal connecting visitors directly with dedicated account representatives."
            ],
            'cta': [
                f"High-conversion closing banner encouraging visitors to start their trial or schedule a guided walkthrough.",
                f"Compelling call to action highlighting risk-free onboarding, immediate setup, and dedicated customer success.",
                f"Join thousands of satisfied teams already accelerating their development with {c}."
            ],
            'footer': [
                f"Comprehensive multi-column footer organizing product links, company documentation, legal terms, and social routes.",
                f"Global navigation anchor providing copyright information, compliance certifications, and newsletter registration.",
                f"Footer with complete sitemap links, status page monitoring, and direct support access."
            ],
            'content': [
                f"Structured information block for {t} organizing key technical explanations and supporting documentation.",
                f"In-depth analysis of {t} with scannable headers, explanatory copy, and contextual supporting graphics.",
                f"Clear editorial content explaining the core principles and operational methodology of {p}."
            ]
        }

        options = variations.get(st, variations['content'])
        return random.choice(options)

    def regenerate_section(
        self,
        title: str,
        section_type: str,
        page_context: Optional[Dict[str, Any]] = None,
        brief: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate an entire section structure with fresh copy, layout variant, and items.
        """
        raw_type = str(section_type or 'content').strip().lower()
        stype = SECTION_TYPE_ALIASES.get(raw_type, raw_type)
        page_name = str((page_context or {}).get('name') or (page_context or {}).get('page_name') or 'Page')
        desc = self.regenerate_section_description(title, stype, page_name, brief)

        raw_sec = {
            'id': str(uuid.uuid4())[:8],
            'type': stype,
            'title': title or f"{page_name} {stype.capitalize()}",
            'description': desc,
        }

        repaired = repair_wireframe_section(
            raw_sec,
            page_name=page_name,
            client_name=str((brief or {}).get('client') or '')
        )
        return repaired
