"""
backend/sitemap_app/providers/mock_provider.py
Deterministic fallback provider for offline development, automated testing, and CI/CD.
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from .base import BaseAIProvider, CompletionRequest, CompletionResponse, TokenUsage

logger = logging.getLogger(__name__)


class MockFallbackProvider(BaseAIProvider):
    """
    Deterministic provider that generates syntactically valid JSON responses
    matching the schema requirements of sitemaps and wireframe sections.
    """

    def __init__(self, name: str = "mock", config: Optional[Dict[str, Any]] = None):
        super().__init__(name=name, config=config)

    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generates deterministic mock responses tailored to the request prompt."""
        prompt_lower = (request.prompt or "").lower()
        sys_lower = (request.system_instruction or "").lower()

        # 1. Sitemap generation request
        if "sitemap" in prompt_lower or "sitemap" in sys_lower:
            mock_data = self._generate_mock_sitemap(request.prompt)
        # 2. Wireframe / section generation request
        elif "wireframe" in prompt_lower or "section" in prompt_lower or "layout" in prompt_lower:
            mock_data = self._generate_mock_wireframe(request.prompt)
        # 3. Dynamic brief / questions request
        elif "question" in prompt_lower or "brief" in prompt_lower:
            mock_data = self._generate_mock_questions(request.prompt)
        else:
            mock_data = {
                "message": "Mock completion response",
                "prompt_echo": request.prompt[:100]
            }

        content_str = json.dumps(mock_data, indent=2)

        return CompletionResponse(
            success=True,
            content=content_str,
            parsed_json=mock_data,
            model="mock-v1",
            provider_name=self.name,
            raw_response={"mock": True, "result": mock_data},
            status_code=200,
            usage=TokenUsage(prompt_tokens=50, completion_tokens=150, total_tokens=200),
            duration_ms=15.0
        )

    def _generate_mock_sitemap(self, prompt: str) -> Dict[str, Any]:
        return {
            "website_name": "Modern Business Solution",
            "website_type": "Business Website",
            "navigation": ["Home", "Services", "About", "Pricing", "Contact"],
            "pages": [
                {
                    "name": "Home",
                    "path": "/",
                    "title": "Welcome to Our Platform",
                    "description": "High-impact landing page highlighting core value propositions and social proof.",
                    "sections": ["navbar", "hero", "features", "stats", "testimonials", "cta", "footer"]
                },
                {
                    "name": "Services",
                    "path": "/services",
                    "title": "Our Professional Services",
                    "description": "Comprehensive overview of tailored service offerings and workflows.",
                    "sections": ["navbar", "hero", "services-grid", "process", "faq", "footer"]
                },
                {
                    "name": "About",
                    "path": "/about",
                    "title": "About Our Mission",
                    "description": "Our leadership, core values, origin story, and corporate milestones.",
                    "sections": ["navbar", "hero", "story", "team", "values", "footer"]
                },
                {
                    "name": "Pricing",
                    "path": "/pricing",
                    "title": "Flexible & Transparent Pricing",
                    "description": "Tiered subscription packages designed for teams of any size.",
                    "sections": ["navbar", "hero", "pricing-table", "comparison", "faq", "footer"]
                },
                {
                    "name": "Contact",
                    "path": "/contact",
                    "title": "Get In Touch",
                    "description": "Direct communication channels, interactive inquiry form, and headquarters map.",
                    "sections": ["navbar", "hero", "contact-form", "info", "footer"]
                }
            ]
        }

    def _generate_mock_wireframe(self, prompt: str) -> List[Dict[str, Any]]:
        # Check if blueprints are provided in prompt
        m = re.search(r'Required Section Blueprints:\s*(\[[\s\S]*?\])\s*INSTRUCTIONS', prompt)
        if m:
            try:
                blueprints = json.loads(m.group(1))
                if isinstance(blueprints, list) and len(blueprints) > 0:
                    sections = []
                    for bp in blueprints:
                        sec_type = bp.get('type', 'content')
                        layout = bp.get('layoutVariant', 'layout-default')
                        sec_dict = {
                            "id": bp.get('id', str(uuid.uuid4())[:8]),
                            "type": sec_type,
                            "title": bp.get('title', 'Section Title'),
                            "description": bp.get('description', 'Comprehensive section description communicating specific value and domain deliverables.'),
                            "layoutVariant": layout,
                            "buttonText": bp.get('buttonText', 'Explore'),
                        }
                        if sec_type == 'navbar':
                            sec_dict["menuItems"] = ["Home", "About", "Services", "Pricing", "Contact"]
                            sec_dict["items"] = ["Home", "About", "Services", "Pricing", "Contact"]
                        elif sec_type == 'footer':
                            sec_dict["items"] = [
                                {"title": "Platform", "items": ["Features", "Integrations", "Pricing"]},
                                {"title": "Company", "items": ["About Us", "Careers", "Contact"]},
                                {"title": "Legal", "items": ["Privacy", "Terms", "Security"]}
                            ]
                        elif bp.get('requires_items'):
                            sec_dict["items"] = [
                                {"title": f"{sec_type.title()} Solution {chr(65+i)}", "desc": "High performance verified capability with measurable results.", "icon": "check-circle"}
                                for i in range(bp.get('items_count', 3))
                            ]
                        else:
                            sec_dict["items"] = []

                        sections.append(sec_dict)
                    return sections
            except Exception:
                pass

        return [
            {
                "id": "mock-sec-nav",
                "type": "navbar",
                "title": "Main Navigation",
                "description": "Sticky brand navigation bar with logo and primary links.",
                "layoutVariant": "layout-default",
                "items": ["Home", "Services", "About", "Pricing", "Contact"]
            },
            {
                "id": "mock-sec-hero",
                "type": "hero",
                "title": "Transform Your Digital Presence",
                "description": "Engaging hero banner featuring high-converting headlines and primary action buttons.",
                "layoutVariant": "layout-split-right",
                "buttonText": "Get Started Today"
            },
            {
                "id": "mock-sec-features",
                "type": "features",
                "title": "Engineered for Performance",
                "description": "Explore the foundational capabilities that empower teams to scale effortlessly.",
                "layoutVariant": "layout-grid-3",
                "items": [
                    {"title": "Lightning Fast", "desc": "Sub-millisecond processing times.", "icon": "zap"},
                    {"title": "Enterprise Security", "desc": "SOC2 and GDPR compliant by default.", "icon": "lock"},
                    {"title": "Seamless Integration", "desc": "Connect with all existing tools.", "icon": "link"}
                ]
            },
            {
                "id": "mock-sec-testimonials",
                "type": "testimonial",
                "title": "Trusted by Industry Leaders",
                "description": "Hear how global brands elevated their operations using our architecture.",
                "layoutVariant": "layout-cards",
                "items": [
                    {"quote": "Decreased our build cycles by 70%.", "name": "Jane Doe", "role": "CTO"},
                    {"quote": "The cleanest architecture we have ever deployed.", "name": "John Smith", "role": "VP Engineering"}
                ]
            },
            {
                "id": "mock-sec-footer",
                "type": "footer",
                "title": "Site Footer",
                "description": "Global footer with privacy policy, terms, copyright, and social connections.",
                "layoutVariant": "layout-multi-column"
            }
        ]

    def _generate_mock_questions(self, prompt: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": "primary_goal",
                "question": "What is the primary objective of this website?",
                "options": ["Lead Generation", "Direct Product Sales", "Brand Awareness", "Customer Support"]
            },
            {
                "id": "target_audience",
                "question": "Who is the primary target audience?",
                "options": ["B2B Enterprise", "Individual Consumers", "Developers & Engineers", "Small Business Owners"]
            },
            {
                "id": "visual_style",
                "question": "Which design aesthetic best aligns with your brand?",
                "options": ["Minimalist & Modern", "Bold & Energetic", "Corporate & Trustworthy", "Technical & Dark Mode"]
            }
        ]

