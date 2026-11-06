"""
backend/sitemap_app/schemas/sitemap.py
Formal Pydantic v2 schemas and validation/repair engine for Sitemaps.
Phase 3 — Requirement Analysis & Sitemap Generation
"""

from __future__ import annotations
import uuid
import re
from typing import List, Optional, Dict, Any, Union, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator


# Canonical supported section types from docs/ARCHITECTURE.md & docs/WIREFRAME_SCHEMA.md
SUPPORTED_SECTION_TYPES = {
    # Structural
    'navbar', 'footer',
    # Hero Variants
    'hero', 'split-hero', 'centered-hero', 'cta-hero',
    # Content & Story
    'content', 'main-info', 'supporting-info', 'story', 'about', 'values', 'team',
    # Services & Features
    'features', 'services', 'services-grid', 'product-grid', 'process',
    # Conversion & Proof
    'pricing', 'pricing-table', 'testimonial', 'stats', 'case-study', 'case-studies', 'cta',
    # Interactive & Form
    'contact', 'contact-form', 'contact-details', 'location', 'faq',
    # Booking & Commerce
    'booking-search', 'search-form', 'filters', 'promo', 'offers', 'trust',
    'cart', 'checkout', 'trip-types',
    # Editorial & Media
    'gallery', 'blog-grid', 'articles', 'newsletter'
}

# Semantic Aliases mapping informal or AI-generated section types to canonical identifiers
SECTION_TYPE_ALIASES = {
    'nav': 'navbar',
    'header': 'navbar',
    'navigation': 'navbar',
    'site-header': 'navbar',
    'hero-section': 'hero',
    'hero-banner': 'hero',
    'banner': 'hero',
    'main-information': 'main-info',
    'main_info': 'main-info',
    'supporting-content': 'supporting-info',
    'supporting_info': 'supporting-info',
    'key-features': 'features',
    'feature-list': 'features',
    'service-list': 'services',
    'services-list': 'services',
    'pricing-plans': 'pricing',
    'pricing-table': 'pricing',
    'testimonials': 'testimonial',
    'reviews': 'testimonial',
    'social-proof': 'testimonial',
    'statistics': 'stats',
    'metrics': 'stats',
    'case-studies': 'case-study',
    'call-to-action': 'cta',
    'action-banner': 'cta',
    'contact-us': 'contact',
    'questions': 'faq',
    'faqs': 'faq',
    'help': 'faq',
    'foot': 'footer',
    'bottom': 'footer',
    'site-footer': 'footer',
}


class BriefContextModel(BaseModel):
    """Structured contextual requirements and preferences for the website project."""
    client: Optional[str] = Field(default="", description="Client, organization, or brand name")
    type: Optional[str] = Field(default="Business Website", description="Human-readable website type")
    category: Optional[str] = Field(default="business", description="Standard industry category code")
    
    # Requirement Analyzer Core Fields
    business_objectives: Optional[Union[str, List[str]]] = Field(
        default="", description="Key commercial, brand, or operational objectives"
    )
    target_audience: Optional[Union[str, List[str]]] = Field(
        default="", description="Target customer demographics, personas, or market segment"
    )
    design_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Visual aesthetics, style, tone, colors, and typography directions"
    )
    required_functionality: Optional[Union[str, List[str]]] = Field(
        default_factory=list, description="Mandatory interactive features and technical capabilities"
    )
    required_pages: Optional[List[str]] = Field(
        default_factory=list, description="Explicit or strongly implied website pages"
    )
    navigation_requirements: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Header nav, footer nav, and CTA specifications"
    )
    content_requirements: Optional[Union[str, List[str], Dict[str, Any]]] = Field(
        default="", description="Content blocks, editorial priorities, and proof points"
    )

    # Backward Compatibility Fields (for frontend chat and legacy workflows)
    goals: Optional[str] = Field(default="", description="Legacy alias for primary goal")
    services: Optional[Union[str, List[str]]] = Field(default="", description="Offerings or products")
    features: Optional[Union[str, List[str]]] = Field(default="", description="Legacy alias for features")
    style: Optional[str] = Field(default="Modern, Clean", description="Visual style")
    tone: Optional[str] = Field(default="Professional", description="Brand voice and tone")
    language: Optional[str] = Field(default="English", description="Site primary language")
    showcase: Optional[str] = Field(default="", description="Primary showcase or hero focus")
    prompt_text: Optional[str] = Field(default="", description="Original natural language prompt")
    missing_fields: Optional[List[str]] = Field(default_factory=list, description="Unresolved brief fields")
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")

    # Domain-specific auxiliary fields
    trip_types: Optional[str] = Field(default=None)
    passenger_types: Optional[str] = Field(default=None)
    addons: Optional[str] = Field(default=None)
    payments: Optional[str] = Field(default=None)
    policies: Optional[str] = Field(default=None)
    auto_filled: Optional[List[str]] = Field(default_factory=list)

    @model_validator(mode='after')
    def harmonize_fields(self) -> BriefContextModel:
        """Keep legacy fields and new structured fields synchronized."""
        # Sync business_objectives <-> goals
        if self.business_objectives and not self.goals:
            if isinstance(self.business_objectives, list):
                self.goals = ', '.join(self.business_objectives)
            else:
                self.goals = str(self.business_objectives)
        elif self.goals and not self.business_objectives:
            self.business_objectives = [g.strip() for g in self.goals.split(',') if g.strip()]

        # Sync required_functionality <-> features
        if self.required_functionality and not self.features:
            if isinstance(self.required_functionality, list):
                self.features = ', '.join(self.required_functionality)
            else:
                self.features = str(self.required_functionality)
        elif self.features and not self.required_functionality:
            if isinstance(self.features, list):
                self.required_functionality = self.features
            else:
                self.required_functionality = [f.strip() for f in self.features.split(',') if f.strip()]

        # Sync style and tone into design_preferences
        if not self.design_preferences:
            self.design_preferences = {}
        if self.style and 'style' not in self.design_preferences:
            self.design_preferences['style'] = self.style
        if self.tone and 'tone' not in self.design_preferences:
            self.design_preferences['tone'] = self.tone

        return self


class SitemapSectionModel(BaseModel):
    """Section stub within a sitemap page."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Section unique ID")
    type: str = Field(default="content", description="Canonical section type identifier")
    title: str = Field(default="Section", description="Section headline or title")
    description: str = Field(default="", description="Purpose and content summary of the section")
    layoutVariant: Optional[str] = Field(default="layout-default", description="CSS layout modifier")

    @field_validator('type', mode='before')
    @classmethod
    def normalize_section_type(cls, v: Any) -> str:
        val = str(v or 'content').strip().lower()
        return SECTION_TYPE_ALIASES.get(val, val)

    @field_validator('id', mode='before')
    @classmethod
    def ensure_valid_id(cls, v: Any) -> str:
        s = str(v or '').strip()
        return s if s else str(uuid.uuid4())[:8]


class SitemapPageModel(BaseModel):
    """Hierarchical node in the website sitemap."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique page ID")
    name: str = Field(default="New Page", description="Display name of the page")
    description: str = Field(default="", description="Descriptive summary of the page purpose")
    objective: Optional[str] = Field(default="", description="Primary user or business objective of this page")
    is_primary_nav: Optional[bool] = Field(default=False, description="Whether this page is in top-level navigation")
    nav_label: Optional[str] = Field(default="", description="Concise navigation label")
    parent_id: Optional[str] = Field(default=None, description="Parent page ID if this is a subpage")
    order_index: Optional[int] = Field(default=0, description="Display order within its level")
    sections: List[SitemapSectionModel] = Field(default_factory=list, description="Section stubs in this page")
    children: List[SitemapPageModel] = Field(default_factory=list, description="Subpages nested under this page")

    @field_validator('id', mode='before')
    @classmethod
    def ensure_page_id(cls, v: Any) -> str:
        s = str(v or '').strip()
        return s if s else str(uuid.uuid4())[:8]

    @field_validator('name', mode='before')
    @classmethod
    def clean_name(cls, v: Any) -> str:
        s = str(v or 'New Page').strip()
        return s if s else 'New Page'

    @model_validator(mode='after')
    def set_nav_defaults(self) -> SitemapPageModel:
        if not self.nav_label:
            self.nav_label = self.name
        if not self.objective:
            self.objective = f"Guide visitors through {self.name} and provide relevant information and calls to action."
        return self


class SitemapModel(BaseModel):
    """Complete validated hierarchical sitemap specification."""
    website_type: str = Field(default="Business Website", description="Overall category or title of the website")
    brief: Optional[BriefContextModel] = Field(default_factory=BriefContextModel, description="Project requirements brief")
    pages: List[SitemapPageModel] = Field(default_factory=list, description="Hierarchical tree of pages")

    @field_validator('website_type', mode='before')
    @classmethod
    def clean_website_type(cls, v: Any) -> str:
        s = str(v or 'Business Website').strip()
        return s if s else 'Business Website'


def repair_sitemap(sitemap_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically cleans, normalizes, and repairs a sitemap dictionary to conform to SitemapModel.
    - Resolves missing IDs with fresh 8-char UUIDs
    - Resolves duplicate IDs
    - Deduplicates page names at same hierarchy level
    - Prepend or hoist Home page if missing
    - Normalizes section types via SECTION_TYPE_ALIASES
    - Infills missing default sections (navbar, hero, content, footer)
    - Establishes parent_id and order_index relationships
    - Breaks circular parent-child loops
    """
    if not isinstance(sitemap_data, dict):
        sitemap_data = {}

    website_type = str(sitemap_data.get('website_type', 'Business Website')).strip() or 'Business Website'
    raw_brief = sitemap_data.get('brief') or {}
    if not isinstance(raw_brief, dict):
        raw_brief = {}

    brief_copy = dict(raw_brief)
    raw_pages = sitemap_data.get('pages', [])
    if not isinstance(raw_pages, list):
        raw_pages = []

    seen_ids = set()
    visited_objects = set()
    
    def get_unique_id(candidate: Any) -> str:
        cid = str(candidate or '').strip()
        if not cid or cid in seen_ids:
            cid = str(uuid.uuid4())[:8]
        seen_ids.add(cid)
        return cid

    def repair_section(sec: Any) -> Dict[str, Any]:
        if not isinstance(sec, dict):
            sec = {'title': str(sec or 'Section')}
        raw_type = str(sec.get('type') or 'content').strip().lower()
        canonical_type = SECTION_TYPE_ALIASES.get(raw_type, raw_type)
        return {
            'id': get_unique_id(sec.get('id')),
            'type': canonical_type,
            'title': str(sec.get('title') or canonical_type.capitalize()).strip(),
            'description': str(sec.get('description') or '').strip(),
            'layoutVariant': str(sec.get('layoutVariant') or 'layout-default').strip()
        }

    def repair_node(node: Any, parent_id: Optional[str] = None, order: int = 0, ancestors: set = None) -> Optional[Dict[str, Any]]:
        if not isinstance(node, dict):
            node = {'name': str(node or 'Page')}

        # Check Python object identity to prevent cyclical dictionary graphs
        obj_key = id(node)
        if obj_key in visited_objects:
            return None
        visited_objects.add(obj_key)

        raw_id = str(node.get('id') or '').strip()
        current_ancestors = set(ancestors or set())
        if raw_id and raw_id in current_ancestors:
            # Break circular reference
            return None

        raw_name = str(node.get('name') or 'Page').strip()
        if not raw_name:
            raw_name = 'Page'

        node_id = get_unique_id(raw_id)
        current_ancestors.add(node_id)

        # Process sections
        raw_sections = node.get('sections', [])
        if not isinstance(raw_sections, list):
            raw_sections = []
        cleaned_sections = [repair_section(s) for s in raw_sections if s is not None]

        # Infill default sections if empty
        if not cleaned_sections:
            page_lower = raw_name.lower()
            cleaned_sections = [
                {'id': get_unique_id(None), 'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id(None), 'type': 'hero', 'title': f'{raw_name} Hero', 'description': f'Introduction to {raw_name}', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id(None), 'type': 'features' if 'home' in page_lower else 'content', 'title': 'Key Highlights', 'description': f'Core information for {raw_name}', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id(None), 'type': 'footer', 'title': 'Footer', 'description': 'Global footer', 'layoutVariant': 'layout-default'},
            ]
        else:
            # Ensure navbar and footer exist for root pages
            if parent_id is None:
                has_nav = any(s['type'] == 'navbar' for s in cleaned_sections)
                has_foot = any(s['type'] == 'footer' for s in cleaned_sections)
                if not has_nav:
                    cleaned_sections.insert(0, {'id': get_unique_id(None), 'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation', 'layoutVariant': 'layout-default'})
                if not has_foot:
                    cleaned_sections.append({'id': get_unique_id(None), 'type': 'footer', 'title': 'Footer', 'description': 'Global footer', 'layoutVariant': 'layout-default'})

        # Process children recursively
        raw_children = node.get('children', [])
        if not isinstance(raw_children, list):
            raw_children = []
        
        cleaned_children: List[Dict[str, Any]] = []
        child_seen_names = set()
        for c_idx, child in enumerate(raw_children):
            c_node = repair_node(child, parent_id=node_id, order=c_idx, ancestors=current_ancestors)
            if c_node:
                c_name_key = c_node['name'].lower()
                if c_name_key not in child_seen_names:
                    child_seen_names.add(c_name_key)
                    cleaned_children.append(c_node)

        desc = str(node.get('description') or '').strip()
        if not desc:
            desc = f'Comprehensive {raw_name} page for {website_type}.'

        obj = str(node.get('objective') or '').strip()
        if not obj:
            obj = f'Deliver key {raw_name} value and drive target visitor actions.'

        is_primary = node.get('is_primary_nav')
        if is_primary is None:
            is_primary = (parent_id is None)

        nav_label = str(node.get('nav_label') or raw_name).strip()

        return {
            'id': node_id,
            'name': raw_name,
            'description': desc,
            'objective': obj,
            'is_primary_nav': bool(is_primary),
            'nav_label': nav_label,
            'parent_id': parent_id,
            'order_index': order,
            'sections': cleaned_sections,
            'children': cleaned_children
        }

    # Repair top-level page list
    repaired_pages: List[Dict[str, Any]] = []
    top_seen_names = set()
    for idx, page in enumerate(raw_pages):
        p_node = repair_node(page, parent_id=None, order=idx)
        if p_node:
            p_name_key = p_node['name'].lower()
            if p_name_key not in top_seen_names:
                top_seen_names.add(p_name_key)
                repaired_pages.append(p_node)

    # Ensure Home page exists at the very front
    home_idx = next((i for i, p in enumerate(repaired_pages) if p['name'].lower() in ('home', 'homepage')), None)
    if home_idx is not None and home_idx > 0:
        # Move Home to the very front
        home_page = repaired_pages.pop(home_idx)
        repaired_pages.insert(0, home_page)
    elif home_idx is None:
        # Insert a default Home page
        home_id = get_unique_id('p-home')
        repaired_pages.insert(0, {
            'id': home_id,
            'name': 'Home',
            'description': f'Main landing page for {website_type}.',
            'objective': 'Welcome visitors, establish credibility, and guide them to key sections.',
            'is_primary_nav': True,
            'nav_label': 'Home',
            'parent_id': None,
            'order_index': 0,
            'sections': [
                {'id': get_unique_id('sec-nav'), 'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id('sec-hero'), 'type': 'hero', 'title': 'Welcome Hero', 'description': f'Welcome to {website_type}', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id('sec-feat'), 'type': 'features', 'title': 'Key Highlights', 'description': 'Featured offerings and core benefits', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id('sec-cta'), 'type': 'cta', 'title': 'Get Started', 'description': 'Call to action and next steps', 'layoutVariant': 'layout-default'},
                {'id': get_unique_id('sec-foot'), 'type': 'footer', 'title': 'Footer', 'description': 'Global footer', 'layoutVariant': 'layout-default'},
            ],
            'children': []
        })

    # Re-index top-level order_index
    for idx, p in enumerate(repaired_pages):
        p['order_index'] = idx

    return {
        'website_type': website_type,
        'brief': brief_copy,
        'pages': repaired_pages
    }


def validate_sitemap(sitemap_data: Dict[str, Any]) -> Tuple[bool, Optional[SitemapModel], List[str]]:
    """
    Validates sitemap data against SitemapModel.
    Returns (is_valid, validated_model_or_none, error_messages_list).
    """
    errors: List[str] = []
    try:
        model = SitemapModel.model_validate(sitemap_data)
        return True, model, []
    except Exception as e:
        errors.append(str(e))
        return False, None, errors
