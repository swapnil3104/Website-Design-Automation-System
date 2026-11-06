"""
backend/sitemap_app/schemas/wireframe.py
Formal Pydantic v2 schemas and validation/repair engine for Wireframes.
Phase 4 — AI Wireframe Generation Engine
"""

from __future__ import annotations
import uuid
import re
from typing import List, Optional, Dict, Any, Union, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator

from .sitemap import (
    BriefContextModel,
    SUPPORTED_SECTION_TYPES,
    SECTION_TYPE_ALIASES,
)

# Canonical supported layout variants from docs/WIREFRAME_SCHEMA.md
SUPPORTED_LAYOUT_VARIANTS = {
    # Hero variants
    'layout-split-right',
    'layout-split-left',
    'layout-centered',
    'layout-full-bg',
    'layout-asymmetric',
    'layout-minimal',
    'layout-bold-text',
    'layout-video-bg',
    'layout-stacked',
    # Grid & Content variants
    'layout-grid-2',
    'layout-grid-3',
    'layout-grid-4',
    'layout-split',
    'layout-cards',
    'layout-list',
    'layout-multi-column',
    'layout-default',
}

# Layout variant alias dictionary for normalizing informal LLM outputs
LAYOUT_VARIANT_ALIASES = {
    'default': 'layout-default',
    'split': 'layout-split',
    'split-right': 'layout-split-right',
    'split-left': 'layout-split-left',
    'split_right': 'layout-split-right',
    'split_left': 'layout-split-left',
    'centered': 'layout-centered',
    'center': 'layout-centered',
    'full-bg': 'layout-full-bg',
    'full_bg': 'layout-full-bg',
    'asymmetric': 'layout-asymmetric',
    'minimal': 'layout-minimal',
    'bold-text': 'layout-bold-text',
    'stacked': 'layout-stacked',
    'grid-2': 'layout-grid-2',
    'grid-3': 'layout-grid-3',
    'grid-4': 'layout-grid-4',
    'grid_2': 'layout-grid-2',
    'grid_3': 'layout-grid-3',
    'grid_4': 'layout-grid-4',
    '2-col': 'layout-grid-2',
    '3-col': 'layout-grid-3',
    '4-col': 'layout-grid-4',
    'cards': 'layout-cards',
    'card-grid': 'layout-cards',
    'list': 'layout-list',
    'multi-column': 'layout-multi-column',
    'columns': 'layout-multi-column',
    'footer-columns': 'layout-multi-column',
}

# Standard Lucide Icons by Domain / Category
LUCIDE_ICONS_BY_CATEGORY = {
    'features': ['Zap', 'Shield', 'Activity', 'Sparkles', 'Cpu', 'Database', 'Cloud'],
    'services': ['CheckCircle', 'ArrowRight', 'Briefcase', 'Layers', 'Tool', 'Compass'],
    'pricing': ['CreditCard', 'Check', 'Award', 'Tag', 'DollarSign', 'Star'],
    'stats': ['TrendingUp', 'Users', 'Globe', 'Activity', 'Award', 'Clock'],
    'testimonials': ['Star', 'Quote', 'ThumbsUp', 'Heart', 'UserCheck'],
    'contact': ['Mail', 'Phone', 'MapPin', 'MessageSquare', 'Clock', 'Send'],
    'faq': ['HelpCircle', 'ChevronDown', 'Info', 'CheckCircle'],
    'security': ['Shield', 'Lock', 'Award', 'CheckCircle', 'Key'],
    'general': ['Check', 'ArrowRight', 'Star', 'Sparkles', 'Plus']
}

CANONICAL_LUCIDE_ICONS = {
    'Check', 'CheckCircle', 'Zap', 'Shield', 'Activity', 'Cpu', 'Server', 'Database',
    'Cloud', 'Wifi', 'CreditCard', 'DollarSign', 'ShoppingCart', 'ShoppingBag', 'Tag',
    'Percent', 'Compass', 'MapPin', 'Navigation', 'Calendar', 'Clock', 'Mail',
    'Phone', 'MessageSquare', 'Send', 'Bell', 'HelpCircle', 'User', 'Users', 'Heart',
    'ThumbsUp', 'Star', 'Sparkles', 'ArrowRight', 'ArrowLeft', 'ChevronDown', 'Plus',
    'Search', 'ExternalLink', 'Lock', 'Award', 'Key', 'FileCheck', 'TrendingUp',
    'Layers', 'Tool', 'Briefcase', 'Globe', 'UserCheck', 'Quote', 'Info'
}


class SectionItemModel(BaseModel):
    """An individual item inside a grid, list, card, or multi-column section."""
    title: Optional[str] = Field(default="", description="Item headline or card title")
    desc: Optional[str] = Field(default="", description="Descriptive copy or summary")
    icon: Optional[str] = Field(default="Check", description="Lucide icon identifier or visual symbol")
    
    # Extended fields for testimonials / quotes
    name: Optional[str] = Field(default=None, description="Author or client name")
    role: Optional[str] = Field(default=None, description="Company, designation, or role")
    quote: Optional[str] = Field(default=None, description="Customer quotation text")
    
    # Extended fields for pricing, tags, and stats
    price: Optional[str] = Field(default=None, description="Price string (e.g. '$49/mo')")
    tag: Optional[str] = Field(default=None, description="Badge tag (e.g. 'Most Popular', 'Pro')")
    label: Optional[str] = Field(default=None, description="Label or category")
    value: Optional[str] = Field(default=None, description="Metric value (e.g. '99.9%', '10M+')")
    features: Optional[List[str]] = Field(default=None, description="Feature bullet points for pricing")
    
    # Extended fields for multi-column footers or sublists
    items: Optional[List[str]] = Field(default=None, description="Sub-links list")
    sub_items: Optional[List[str]] = Field(default=None, description="Alias for sub-items")

    @field_validator('title', mode='before')
    @classmethod
    def sanitize_title(cls, v: Any, info) -> str:
        s = str(v or '').strip()
        if not s and hasattr(info, 'data') and isinstance(info.data, dict):
            name = info.data.get('name')
            if name:
                return str(name).strip()
        return s

    @field_validator('desc', mode='before')
    @classmethod
    def sanitize_desc(cls, v: Any, info) -> str:
        s = str(v or '').strip()
        if not s and hasattr(info, 'data') and isinstance(info.data, dict):
            quote = info.data.get('quote')
            if quote:
                return str(quote).strip()
        return s

    @field_validator('icon', mode='before')
    @classmethod
    def normalize_icon(cls, v: Any) -> str:
        raw = str(v or '').strip()
        if not raw:
            return "Check"
        # Map common emoji or informal icon names to Lucide tokens
        emoji_map = {
            '⚡': 'Zap', '🛡️': 'Shield', '📈': 'TrendingUp', '🧠': 'Cpu',
            '🛠️': 'Tool', '🚀': 'Zap', '🎯': 'Award', '📦': 'Layers',
            '📘': 'Info', '📊': 'Activity', '🔍': 'Search', '🧩': 'Layers',
            '💳': 'CreditCard', '🏷️': 'Tag', '🏆': 'Award', '⭐': 'Star',
            '💬': 'MessageSquare', '🏅': 'Award', '❤️': 'Heart', '👤': 'User',
            '👥': 'Users', '🧑‍💼': 'User', '🧑‍💻': 'Cpu', '📰': 'FileCheck',
            '✍️': 'FileCheck', '📚': 'Layers', '🗂️': 'Layers', '❓': 'HelpCircle',
            '💡': 'Sparkles', '🛟': 'HelpCircle', '✅': 'CheckCircle', '📍': 'MapPin',
            '✉️': 'Mail', '📞': 'Phone', '🕒': 'Clock', '📝': 'FileCheck',
            '📨': 'Send', '🔗': 'ExternalLink', '🌐': 'Globe', '📄': 'FileCheck',
            '🔒': 'Lock', '✨': 'Sparkles', '📌': 'MapPin', '🔹': 'Check',
            '🌟': 'Star', '🖼️': 'Layers', '📷': 'Layers', '🌍': 'Globe'
        }
        if raw in emoji_map:
            return emoji_map[raw]
        # Clean string: Capitalize first letter
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', raw)
        if cleaned:
            # Capitalize first letter
            camel = cleaned[0].upper() + cleaned[1:]
            if camel in CANONICAL_LUCIDE_ICONS:
                return camel
        return "Check"

    @model_validator(mode='after')
    def harmonize_sublists(self) -> SectionItemModel:
        if not self.title and self.name:
            self.title = self.name
        if not self.desc and self.quote:
            self.desc = self.quote
        if self.sub_items and not self.items:
            self.items = self.sub_items
        elif self.items and not self.sub_items:
            self.sub_items = self.items
        return self


class SectionStylesModel(BaseModel):
    """Visual style overrides applied to a section element."""
    padding: Optional[int] = Field(default=None, ge=0, le=200, description="Vertical padding in px")
    margin: Optional[int] = Field(default=None, ge=0, le=200, description="Vertical margin in px")
    fontSize: Optional[int] = Field(default=None, ge=10, le=72, description="Base font size in px")
    fontWeight: Optional[str] = Field(default=None, description="Font weight (e.g. 400, 600, 700)")
    headingFont: Optional[str] = Field(default=None, description="Font family for headings")
    paragraphFont: Optional[str] = Field(default=None, description="Font family for body copy")
    align: Optional[str] = Field(default="left", description="Text alignment: left, center, right")
    theme: Optional[str] = Field(default="light", description="Theme variant: light, dark, accent")


class ResponsiveSettingsModel(BaseModel):
    """Responsive layout settings across desktop, tablet, and mobile breakpoints."""
    columns_desktop: int = Field(default=3, ge=1, le=6, description="Grid columns on desktop (>=1024px)")
    columns_tablet: int = Field(default=2, ge=1, le=4, description="Grid columns on tablet (768px - 1023px)")
    columns_mobile: int = Field(default=1, ge=1, le=2, description="Grid columns on mobile (<768px)")
    stack_on_mobile: bool = Field(default=True, description="Whether multi-column content stacks vertically on mobile")
    hide_on_mobile: bool = Field(default=False, description="Whether section is hidden on small screens")


class WireframeSectionModel(BaseModel):
    """Detailed layout and content model for a single page wireframe section."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Section unique ID")
    type: str = Field(default="content", description="Canonical section type identifier")
    title: str = Field(default="Section Title", description="Primary headline of the section")
    description: str = Field(default="", description="Descriptive copy or body text")
    layoutVariant: str = Field(default="layout-default", description="CSS layout modifier")
    buttonText: Optional[str] = Field(default="", description="Primary Call to Action button copy")
    secondaryButtonText: Optional[str] = Field(default="", description="Secondary action button copy")
    menuItems: List[str] = Field(default_factory=list, description="Navigation links for navbar")
    items: List[SectionItemModel] = Field(default_factory=list, description="Sub-items, cards, or link groups")
    styles: Optional[SectionStylesModel] = Field(default=None, description="Visual style overrides")
    responsive: Optional[ResponsiveSettingsModel] = Field(default=None, description="Breakpoint layout settings")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Auxiliary properties")

    @field_validator('id', mode='before')
    @classmethod
    def ensure_valid_id(cls, v: Any) -> str:
        s = str(v or '').strip()
        return s if s else str(uuid.uuid4())[:8]

    @field_validator('type', mode='before')
    @classmethod
    def normalize_type(cls, v: Any) -> str:
        raw = str(v or 'content').strip().lower()
        return SECTION_TYPE_ALIASES.get(raw, raw)

    @field_validator('layoutVariant', mode='before')
    @classmethod
    def normalize_layout_variant(cls, v: Any) -> str:
        raw = str(v or 'layout-default').strip().lower()
        if raw in SUPPORTED_LAYOUT_VARIANTS:
            return raw
        return LAYOUT_VARIANT_ALIASES.get(raw, 'layout-default')

    @field_validator('title', mode='before')
    @classmethod
    def clean_title(cls, v: Any) -> str:
        s = str(v or '').strip()
        return s if s else "Section"

    @field_validator('description', mode='before')
    @classmethod
    def clean_description(cls, v: Any) -> str:
        return str(v or '').strip()

    @field_validator('menuItems', mode='before')
    @classmethod
    def sanitize_menu_items(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            cleaned = [str(item).strip() for item in v if str(item).strip()]
            return cleaned[:10]
        return []

    @model_validator(mode='after')
    def apply_defaults_by_type(self) -> WireframeSectionModel:
        """Ensure section has appropriate responsive and layout defaults based on its type."""
        # Set default responsive settings if none provided
        if not self.responsive:
            if self.layoutVariant == 'layout-grid-4':
                self.responsive = ResponsiveSettingsModel(columns_desktop=4, columns_tablet=2, columns_mobile=1)
            elif self.layoutVariant == 'layout-grid-3':
                self.responsive = ResponsiveSettingsModel(columns_desktop=3, columns_tablet=2, columns_mobile=1)
            elif self.layoutVariant in ('layout-grid-2', 'layout-split', 'layout-split-left', 'layout-split-right'):
                self.responsive = ResponsiveSettingsModel(columns_desktop=2, columns_tablet=1, columns_mobile=1)
            else:
                self.responsive = ResponsiveSettingsModel(columns_desktop=1, columns_tablet=1, columns_mobile=1)
        return self


class PageWireframeModel(BaseModel):
    """Complete wireframe definition for a single page."""
    page_name: str = Field(default="Page", description="Display name of the page")
    page_path: str = Field(default="", description="Hierarchical path (e.g. 'Home' or 'Services/Detail')")
    page_id: Optional[str] = Field(default=None, description="Matching sitemap page ID")
    objective: Optional[str] = Field(default="", description="Conversion or informational objective")
    page_type: Optional[str] = Field(default="generic", description="Canonical page category")
    sections: List[WireframeSectionModel] = Field(default_factory=list, description="Ordered section list")

    @field_validator('page_name', mode='before')
    @classmethod
    def clean_page_name(cls, v: Any) -> str:
        s = str(v or 'Page').strip()
        return s if s else "Page"

    @model_validator(mode='after')
    def ensure_page_path(self) -> PageWireframeModel:
        if not self.page_path:
            self.page_path = self.page_name
        return self


class WireframeContainerModel(BaseModel):
    """Root response envelope for multi-page wireframes."""
    website_type: str = Field(default="Website", description="Website industry category or title")
    brief: Optional[BriefContextModel] = Field(default_factory=BriefContextModel, description="Project context")
    wireframes: Dict[str, PageWireframeModel] = Field(
        default_factory=dict, description="Map of page_id -> PageWireframeModel"
    )

    @field_validator('website_type', mode='before')
    @classmethod
    def clean_website_type(cls, v: Any) -> str:
        s = str(v or 'Website').strip()
        return s if s else "Website"


# =====================================================================
# Deterministic Fallback Items by Section Type
# =====================================================================

DEFAULT_ITEMS_BY_SECTION_TYPE = {
    'features': [
        {
            'title': 'High-Performance Engine',
            'desc': 'Optimized for speed, efficiency, and seamless user experience across all devices.',
            'icon': 'Zap'
        },
        {
            'title': 'Enterprise Security',
            'desc': 'Built with industry-leading encryption and automated compliance protocols.',
            'icon': 'Shield'
        },
        {
            'title': 'Intelligent Analytics',
            'desc': 'Actionable data insights and real-time tracking designed to accelerate decision making.',
            'icon': 'Activity'
        }
    ],
    'services': [
        {
            'title': 'Strategic Advisory',
            'desc': 'Tailored consulting and roadmap planning to achieve measurable business growth.',
            'icon': 'Compass'
        },
        {
            'title': 'End-to-End Implementation',
            'desc': 'Full-cycle delivery from initial architecture to reliable production deployment.',
            'icon': 'CheckCircle'
        },
        {
            'title': 'Continuous Optimization',
            'desc': 'Proactive monitoring, performance enhancements, and dedicated ongoing support.',
            'icon': 'TrendingUp'
        }
    ],
    'pricing': [
        {
            'title': 'Starter',
            'price': '$29/mo',
            'tag': 'Essential',
            'desc': 'Ideal for emerging projects and small teams establishing their foundation.',
            'icon': 'Check',
            'features': ['Up to 5 Users', 'Standard Integrations', 'Email Support', 'Core Analytics']
        },
        {
            'title': 'Professional',
            'price': '$79/mo',
            'tag': 'Most Popular',
            'desc': 'Full suite of advanced capabilities designed for scaling operations.',
            'icon': 'Award',
            'features': ['Unlimited Users', 'Advanced Automations', 'Priority 24/7 Support', 'Custom Reports']
        },
        {
            'title': 'Enterprise',
            'price': 'Custom',
            'tag': 'Custom Tier',
            'desc': 'Dedicated infrastructure, custom SLAs, and specialized security architecture.',
            'icon': 'Shield',
            'features': ['Dedicated Success Manager', 'Custom API Limits', 'SSO & Audit Logs', 'Tailored SLA']
        }
    ],
    'stats': [
        {
            'value': '99.9%',
            'title': 'Uptime Guarantee',
            'desc': 'High-availability infrastructure engineered for zero downtime.',
            'icon': 'Activity'
        },
        {
            'value': '10M+',
            'title': 'Transactions Processed',
            'desc': 'Trusted by organizations globally to handle mission-critical volume.',
            'icon': 'TrendingUp'
        },
        {
            'value': '24/7',
            'title': 'Expert Support',
            'desc': 'Dedicated engineers standing by around the clock to assist you.',
            'icon': 'Clock'
        }
    ],
    'testimonial': [
        {
            'name': 'Alexandra Chen',
            'role': 'Chief Technology Officer, NextEra Corp',
            'quote': 'The platform delivered immediate efficiency gains and transformed our day-to-day workflow within days of rollout.',
            'icon': 'Star'
        },
        {
            'name': 'Marcus Vance',
            'role': 'VP Product, ScaleWave Systems',
            'quote': 'Unmatched reliability and clean design. Our engineering velocity doubled without adding headcount.',
            'icon': 'Star'
        },
        {
            'name': 'Sophia Rodriguez',
            'role': 'Director of Operations, FinEdge',
            'quote': 'Outstanding attention to detail. Every feature feels purposefully designed to eliminate friction.',
            'icon': 'Star'
        }
    ],
    'team': [
        {
            'name': 'David Miller',
            'role': 'Founder & CEO',
            'desc': '15+ years scaling technology enterprises and pioneering customer-centric software.',
            'icon': 'User'
        },
        {
            'name': 'Elena Rostova',
            'role': 'Head of Engineering',
            'desc': 'Distributed systems architect with deep expertise in cloud scalability and reliability.',
            'icon': 'Cpu'
        },
        {
            'name': 'Jordan Lee',
            'role': 'Lead Product Designer',
            'desc': 'Award-winning design strategist focused on intuitive user journeys and accessibility.',
            'icon': 'Sparkles'
        }
    ],
    'faq': [
        {
            'title': 'How quickly can we get started?',
            'desc': 'Onboarding is instantaneous. You can configure your account and deploy your first project in minutes.',
            'icon': 'HelpCircle'
        },
        {
            'title': 'What integrations are supported?',
            'desc': 'We provide pre-built connectors for all major platforms, along with robust REST and Webhook APIs.',
            'icon': 'HelpCircle'
        },
        {
            'title': 'Can plans be upgraded or downgraded?',
            'desc': 'Yes, you can adjust your subscription at any time directly through your billing portal with no lock-in.',
            'icon': 'HelpCircle'
        }
    ],
    'footer': [
        {
            'title': 'Product',
            'items': ['Overview', 'Features', 'Solutions', 'Roadmap', 'Pricing']
        },
        {
            'title': 'Resources',
            'items': ['Documentation', 'Guides', 'API Reference', 'Status Page', 'Community']
        },
        {
            'title': 'Company',
            'items': ['About Us', 'Careers', 'Leadership', 'Press', 'Contact']
        },
        {
            'title': 'Legal',
            'items': ['Privacy Policy', 'Terms of Service', 'Security', 'Compliance']
        }
    ]
}


# =====================================================================
# Validation & Auto-Repair Functions
# =====================================================================

def repair_wireframe_item(item: Any, default_icon: str = "Check") -> Dict[str, Any]:
    """Clean and repair a single item dictionary."""
    if not isinstance(item, dict):
        if isinstance(item, str) and item.strip():
            return {
                'title': item.strip(),
                'desc': '',
                'icon': default_icon
            }
        return {'title': 'Item', 'desc': '', 'icon': default_icon}

    raw_title = str(item.get('title') or item.get('name') or item.get('label') or '').strip()
    raw_desc = str(item.get('desc') or item.get('description') or item.get('quote') or '').strip()
    raw_icon = str(item.get('icon') or default_icon).strip() or default_icon

    res: Dict[str, Any] = {
        'title': raw_title or 'Feature Item',
        'desc': raw_desc,
        'icon': raw_icon
    }

    # Pass through optional structured properties
    for key in ('name', 'role', 'quote', 'price', 'tag', 'label', 'value'):
        val = item.get(key)
        if val is not None and str(val).strip():
            res[key] = str(val).strip()

    # Pass through list fields
    if isinstance(item.get('items'), list):
        res['items'] = [str(x).strip() for x in item['items'] if str(x).strip()]
    elif isinstance(item.get('sub_items'), list):
        res['items'] = [str(x).strip() for x in item['sub_items'] if str(x).strip()]

    if isinstance(item.get('features'), list):
        res['features'] = [str(x).strip() for x in item['features'] if str(x).strip()]

    return res


def repair_wireframe_section(
    section: Any,
    sitemap_menu_items: Optional[List[str]] = None,
    page_name: str = "",
    client_name: str = "",
    existing_ids: Optional[set] = None
) -> Dict[str, Any]:
    """
    Deterministically cleans, normalizes, and repairs a section dictionary.
    - Resolves missing or duplicate IDs
    - Normalizes section type aliases
    - Chooses suitable layoutVariant
    - Infills empty items for itemized sections
    - Ensures navbar has valid menuItems
    - Ensures footer has valid link columns
    """
    if existing_ids is None:
        existing_ids = set()

    if not isinstance(section, dict):
        section = {}

    # 1. Section ID
    sec_id = str(section.get('id') or '').strip()
    if not sec_id or sec_id in existing_ids:
        sec_id = str(uuid.uuid4())[:8]
    existing_ids.add(sec_id)

    # 2. Section Type
    raw_type = str(section.get('type') or 'content').strip().lower()
    canonical_type = SECTION_TYPE_ALIASES.get(raw_type, raw_type)
    if canonical_type not in SUPPORTED_SECTION_TYPES:
        canonical_type = 'content'

    # 3. Title & Description
    raw_title = str(section.get('title') or '').strip()
    if not raw_title:
        type_titles = {
            'navbar': client_name or 'Brand',
            'hero': f"Welcome to {client_name or page_name or 'Our Platform'}",
            'features': "Key Capabilities & Features",
            'services': "Our Core Services",
            'pricing': "Transparent Pricing Plans",
            'testimonial': "What Our Clients Say",
            'stats': "Proven Track Record",
            'team': "Meet Our Leadership",
            'faq': "Frequently Asked Questions",
            'contact': "Get in Touch with Us",
            'contact-form': "Send Us a Message",
            'cta': f"Start Your Journey with {client_name or 'Us'}",
            'footer': "Footer",
        }
        raw_title = type_titles.get(canonical_type, f"{page_name} {canonical_type.capitalize()}")

    raw_desc = str(section.get('description') or '').strip()
    if not raw_desc:
        type_descriptions = {
            'navbar': 'Global navigation header with logo and primary actions.',
            'hero': f"Discover how {client_name or page_name} delivers modern, reliable solutions tailored to your requirements.",
            'features': 'Explore the core architectural features and capabilities engineered for performance and reliability.',
            'services': 'Comprehensive, professional services designed to solve complex challenges.',
            'pricing': 'Select the subscription tier that best matches your team size and operational needs.',
            'testimonial': 'Read feedback and verified reviews from leaders who depend on our platform.',
            'stats': 'Demonstrating scale, reliability, and measurable outcomes worldwide.',
            'team': 'Our multidisciplinary team combines deep domain expertise with technical excellence.',
            'faq': 'Find answers to common questions about our platform, security, and onboarding.',
            'contact': 'Reach out to our team for tailored inquiries, technical support, or partnership opportunities.',
            'cta': 'Join thousands of satisfied teams today. Create your account and get started in minutes.',
            'footer': 'Global footer navigation with quick links, legal resources, and company contact details.'
        }
        raw_desc = type_descriptions.get(canonical_type, f"Detailed information regarding {raw_title}.")

    # 4. Layout Variant
    raw_layout = str(section.get('layoutVariant') or '').strip().lower()
    layout_variant = LAYOUT_VARIANT_ALIASES.get(raw_layout, raw_layout)
    if layout_variant not in SUPPORTED_LAYOUT_VARIANTS:
        # Assign canonical default based on section type
        variant_defaults = {
            'hero': 'layout-split-right',
            'features': 'layout-grid-3',
            'services': 'layout-grid-3',
            'pricing': 'layout-grid-3',
            'stats': 'layout-grid-3',
            'testimonial': 'layout-grid-3',
            'team': 'layout-grid-3',
            'footer': 'layout-multi-column',
            'cta': 'layout-centered',
            'faq': 'layout-list',
            'contact': 'layout-split',
            'contact-form': 'layout-split-left',
        }
        layout_variant = variant_defaults.get(canonical_type, 'layout-default')

    # 5. Button Text
    btn_text = str(section.get('buttonText') or '').strip()
    sec_btn_text = str(section.get('secondaryButtonText') or '').strip()
    if not btn_text:
        if canonical_type == 'navbar':
            btn_text = 'Contact Us'
        elif canonical_type in ('hero', 'cta'):
            btn_text = 'Get Started'
            if not sec_btn_text:
                sec_btn_text = 'Learn More'
        elif canonical_type == 'pricing':
            btn_text = 'Select Plan'
        elif canonical_type in ('contact', 'contact-form'):
            btn_text = 'Send Message'

    # 6. Menu Items (Navbar)
    menu_items = section.get('menuItems')
    if canonical_type == 'navbar':
        if not isinstance(menu_items, list) or len([m for m in menu_items if str(m).strip()]) < 3:
            if sitemap_menu_items and len(sitemap_menu_items) >= 3:
                menu_items = list(sitemap_menu_items[:6])
            else:
                menu_items = ['Home', 'About', 'Services', 'Pricing', 'Contact']
        else:
            menu_items = [str(m).strip() for m in menu_items if str(m).strip()][:8]
    else:
        menu_items = [str(m).strip() for m in menu_items if str(m).strip()][:8] if isinstance(menu_items, list) else []

    # 7. Items Infilling & Normalization
    raw_items = section.get('items')
    repaired_items = []
    if isinstance(raw_items, list) and len(raw_items) > 0:
        for idx, it in enumerate(raw_items):
            repaired_items.append(repair_wireframe_item(it))
    else:
        # Infill default items for card/list sections
        if canonical_type in DEFAULT_ITEMS_BY_SECTION_TYPE:
            defaults = DEFAULT_ITEMS_BY_SECTION_TYPE[canonical_type]
            for it in defaults:
                repaired_items.append(dict(it))

    # 8. Responsive Settings
    responsive = section.get('responsive')
    if not isinstance(responsive, dict):
        if layout_variant == 'layout-grid-4':
            responsive = {'columns_desktop': 4, 'columns_tablet': 2, 'columns_mobile': 1, 'stack_on_mobile': True}
        elif layout_variant == 'layout-grid-3':
            responsive = {'columns_desktop': 3, 'columns_tablet': 2, 'columns_mobile': 1, 'stack_on_mobile': True}
        elif layout_variant in ('layout-grid-2', 'layout-split', 'layout-split-left', 'layout-split-right'):
            responsive = {'columns_desktop': 2, 'columns_tablet': 1, 'columns_mobile': 1, 'stack_on_mobile': True}
        else:
            responsive = {'columns_desktop': 1, 'columns_tablet': 1, 'columns_mobile': 1, 'stack_on_mobile': True}

    repaired = {
        'id': sec_id,
        'type': canonical_type,
        'title': raw_title,
        'description': raw_desc,
        'layoutVariant': layout_variant,
        'buttonText': btn_text,
        'secondaryButtonText': sec_btn_text,
        'menuItems': menu_items,
        'items': repaired_items,
        'responsive': responsive
    }

    if isinstance(section.get('styles'), dict):
        repaired['styles'] = section['styles']
    if isinstance(section.get('metadata'), dict):
        repaired['metadata'] = section['metadata']

    return repaired


def repair_page_wireframe(
    page_data: Any,
    sitemap_menu_items: Optional[List[str]] = None,
    brief: Optional[Dict[str, Any]] = None,
    page_name_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cleans, validates, and infills a complete single-page wireframe structure.
    Ensures mandatory sections (navbar, hero, content/features, footer) exist.
    """
    if not isinstance(page_data, dict):
        page_data = {}

    client_name = ""
    if isinstance(brief, dict):
        client_name = str(brief.get('client') or '').strip()

    name = str(page_name_override or page_data.get('page_name') or page_data.get('name') or 'Page').strip()
    path = str(page_data.get('page_path') or name).strip()
    page_id = str(page_data.get('page_id') or page_data.get('id') or '').strip()

    raw_sections = page_data.get('sections')
    if not isinstance(raw_sections, list):
        raw_sections = []

    existing_ids = set()
    cleaned_sections = []

    for s in raw_sections:
        if isinstance(s, dict):
            cleaned_s = repair_wireframe_section(
                s,
                sitemap_menu_items=sitemap_menu_items,
                page_name=name,
                client_name=client_name,
                existing_ids=existing_ids
            )
            cleaned_sections.append(cleaned_s)

    # Check for mandatory framing sections: Navbar and Footer
    section_types = [s['type'] for s in cleaned_sections]

    if 'navbar' not in section_types:
        navbar_sec = repair_wireframe_section(
            {'type': 'navbar', 'title': client_name or 'Brand'},
            sitemap_menu_items=sitemap_menu_items,
            page_name=name,
            client_name=client_name,
            existing_ids=existing_ids
        )
        cleaned_sections.insert(0, navbar_sec)

    if 'hero' not in section_types and len(cleaned_sections) <= 2:
        hero_sec = repair_wireframe_section(
            {'type': 'hero', 'title': f"{name} Overview"},
            sitemap_menu_items=sitemap_menu_items,
            page_name=name,
            client_name=client_name,
            existing_ids=existing_ids
        )
        # Insert hero right after navbar
        cleaned_sections.insert(1, hero_sec)

    if 'footer' not in section_types:
        footer_sec = repair_wireframe_section(
            {'type': 'footer', 'title': 'Footer'},
            sitemap_menu_items=sitemap_menu_items,
            page_name=name,
            client_name=client_name,
            existing_ids=existing_ids
        )
        cleaned_sections.append(footer_sec)

    return {
        'page_name': name,
        'page_path': path,
        'page_id': page_id or str(uuid.uuid4())[:8],
        'sections': cleaned_sections
    }


def repair_wireframe_container(
    data: Any,
    sitemap_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Repairs a root wireframe response container conforming to WireframeContainerModel.
    Ensures every page in the sitemap has a corresponding PageWireframeModel entry.
    """
    if not isinstance(data, dict):
        data = {}

    website_type = str(data.get('website_type') or (sitemap_data.get('website_type') if sitemap_data else '') or 'Website').strip() or 'Website'
    raw_brief = data.get('brief') or (sitemap_data.get('brief') if sitemap_data else {})
    if not isinstance(raw_brief, dict):
        raw_brief = {}

    # Extract global navigation menu items from sitemap
    sitemap_menu_items = []
    sitemap_pages_map = {}

    def extract_pages(pages: List[Dict[str, Any]], parent_path: str = ""):
        for p in pages:
            if not isinstance(p, dict):
                continue
            p_name = str(p.get('name') or 'Page').strip()
            p_id = str(p.get('id') or '').strip()
            p_path = f"{parent_path}/{p_name}" if parent_path else p_name
            if p_name and p_name not in sitemap_menu_items:
                sitemap_menu_items.append(p_name)
            if p_id:
                sitemap_pages_map[p_id] = {
                    'page': p,
                    'path': p_path
                }
            children = p.get('children')
            if isinstance(children, list) and children:
                extract_pages(children, p_path)

    if sitemap_data and isinstance(sitemap_data.get('pages'), list):
        extract_pages(sitemap_data['pages'])

    raw_wireframes = data.get('wireframes')
    if not isinstance(raw_wireframes, dict):
        raw_wireframes = {}

    repaired_wireframes: Dict[str, Any] = {}

    # Process all existing wireframe entries
    for p_id, p_wireframe in raw_wireframes.items():
        if not isinstance(p_wireframe, dict):
            continue
        mapped_info = sitemap_pages_map.get(p_id, {})
        page_ctx = mapped_info.get('page', {})
        p_path = p_wireframe.get('page_path') or mapped_info.get('path', '')
        p_name = p_wireframe.get('page_name') or page_ctx.get('name', 'Page')

        repaired_page = repair_page_wireframe(
            p_wireframe,
            sitemap_menu_items=sitemap_menu_items,
            brief=raw_brief,
            page_name_override=p_name
        )
        repaired_page['page_id'] = p_id
        repaired_page['page_path'] = p_path or p_name
        repaired_wireframes[p_id] = repaired_page

    # Ensure every sitemap page has a wireframe entry
    for p_id, info in sitemap_pages_map.items():
        if p_id not in repaired_wireframes:
            page_obj = info['page']
            p_path = info['path']
            synthesized_page = repair_page_wireframe(
                page_obj,
                sitemap_menu_items=sitemap_menu_items,
                brief=raw_brief,
                page_name_override=page_obj.get('name')
            )
            synthesized_page['page_id'] = p_id
            synthesized_page['page_path'] = p_path
            repaired_wireframes[p_id] = synthesized_page

    return {
        'website_type': website_type,
        'brief': raw_brief,
        'wireframes': repaired_wireframes
    }


def validate_wireframe(data: Dict[str, Any]) -> Tuple[bool, Optional[WireframeContainerModel], List[str]]:
    """
    Validates a wireframe container dictionary against WireframeContainerModel.
    Returns (is_valid, validated_model_or_none, list_of_error_strings).
    """
    errors: List[str] = []
    try:
        model = WireframeContainerModel.model_validate(data)
        return True, model, []
    except Exception as e:
        errors.append(str(e))
        return False, None, errors


def validate_page_wireframe(data: Dict[str, Any]) -> Tuple[bool, Optional[PageWireframeModel], List[str]]:
    """
    Validates a single page wireframe dictionary against PageWireframeModel.
    Returns (is_valid, validated_model_or_none, list_of_error_strings).
    """
    errors: List[str] = []
    try:
        model = PageWireframeModel.model_validate(data)
        return True, model, []
    except Exception as e:
        errors.append(str(e))
        return False, None, errors
