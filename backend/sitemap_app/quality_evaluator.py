"""
backend/sitemap_app/quality_evaluator.py
Comprehensive Quality Evaluation Engine for Wireframe Generation Optimization.
Phase 7 — Design Quality & Generation Optimization

Evaluates generated website wireframes across all 8 canonical quality dimensions:
1. Requirement Coverage
2. Sitemap Quality
3. Layout Quality
4. Content Relevance
5. Component Consistency
6. Responsive Correctness
7. JSON Validity
8. Rendering Success

Produces structured Quality Reports with 0-100 scores, letter grades (A+, A, B, C, F),
granular issue diagnostics, and actionable recommendations.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

from .schemas.wireframe import (
    SUPPORTED_LAYOUT_VARIANTS,
    validate_wireframe,
)
from .schemas.sitemap import SUPPORTED_SECTION_TYPES


@dataclass
class QualityIssue:
    severity: str  # 'critical', 'warning', 'info'
    dimension: str
    message: str
    page_id: Optional[str] = None
    section_index: Optional[int] = None


@dataclass
class QualityReport:
    overall_score: float
    grade: str
    dimension_scores: Dict[str, float]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_score': round(self.overall_score, 1),
            'grade': self.grade,
            'dimension_scores': {k: round(v, 1) for k, v in self.dimension_scores.items()},
            'issues': self.issues,
            'recommendations': self.recommendations,
            'metadata': self.metadata
        }


class QualityEvaluator:
    """
    Formal Quality Evaluation Engine for AI-generated website wireframes.
    Enforces industry design heuristics, layout diversity, schema compliance,
    and copy relevance.
    """

    GENERIC_COPY_PATTERNS = [
        r'\blorem\s+ipsum\b',
        r'\bfeature\s+[0-9]+\b',
        r'\bservice\s+[0-9]+\b',
        r'\bitem\s+[0-9]+\b',
        r'\bplaceholder\b',
        r'\btitle\s+here\b',
        r'\bdescription\s+goes\s+here\b',
        r'\bsample\s+text\b',
        r'\bquick\s+brown\s+fox\b',
        r'\bconsectetur\s+adipiscing\b',
    ]

    CATEGORY_VOCABULARY = {
        'agriculture': ['harvest', 'crop', 'soil', 'organic', 'farm', 'produce', 'agronomy', 'seed', 'yield', 'grower', 'cultivation', 'orchard'],
        'restaurant': ['culinary', 'dish', 'menu', 'chef', 'tasting', 'flavor', 'dining', 'table', 'wine', 'ingredient', 'cuisine', 'bistro'],
        'healthcare': ['clinical', 'patient', 'doctor', 'physician', 'specialist', 'care', 'medical', 'diagnostic', 'emergency', 'treatment', 'health'],
        'education': ['academic', 'curriculum', 'student', 'faculty', 'degree', 'admission', 'course', 'program', 'research', 'campus', 'scholarship'],
        'ecommerce': ['product', 'shop', 'order', 'shipping', 'checkout', 'cart', 'bestseller', 'catalog', 'collection', 'return', 'delivery'],
        'saas': ['platform', 'workflow', 'api', 'automation', 'pipeline', 'telemetry', 'integration', 'sla', 'cloud', 'enterprise', 'metric'],
        'portfolio': ['craft', 'design', 'selected', 'case study', 'brand', 'identity', 'experience', 'visual', 'prototype', 'interface', 'creative'],
        'agency': ['strategy', 'campaign', 'launch', 'roi', 'showreel', 'branding', 'sprint', 'client', 'creative', 'transformation', 'studio'],
        'blog': ['editorial', 'article', 'essay', 'newsletter', 'journalism', 'subscriber', 'publication', 'read', 'author', 'investigative', 'story'],
        'business': ['enterprise', 'corporate', 'consulting', 'advisory', 'operational', 'strategy', 'governance', 'leadership', 'client', 'roi', 'firm']
    }

    DIMENSION_WEIGHTS = {
        'requirement_coverage': 0.15,
        'sitemap_quality': 0.10,
        'layout_quality': 0.15,
        'content_relevance': 0.15,
        'component_consistency': 0.15,
        'responsive_correctness': 0.10,
        'json_validity': 0.10,
        'rendering_success': 0.10
    }

    def evaluate(
        self,
        wireframe_container: Dict[str, Any],
        sitemap_data: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Run complete 8-dimension evaluation on a wireframe container.
        Returns a structured QualityReport with letter grade and actionable suggestions.
        """
        if not isinstance(wireframe_container, dict):
            wireframe_container = {}
        if not isinstance(sitemap_data, dict):
            sitemap_data = {}

        issues: List[QualityIssue] = []

        # 1. Requirement Coverage
        cov_score = self._eval_requirement_coverage(wireframe_container, sitemap_data, issues)

        # 2. Sitemap Quality
        sm_score = self._eval_sitemap_quality(sitemap_data, issues)

        # 3. Layout Quality & Diversity
        layout_score = self._eval_layout_quality(wireframe_container, issues)

        # 4. Content Relevance & Copy Quality
        content_score = self._eval_content_relevance(wireframe_container, sitemap_data, issues)

        # 5. Component Consistency
        comp_score = self._eval_component_consistency(wireframe_container, issues)

        # 6. Responsive Correctness
        resp_score = self._eval_responsive_correctness(wireframe_container, issues)

        # 7. JSON Validity
        json_score = self._eval_json_validity(wireframe_container, issues)

        # 8. Rendering Success
        render_score = self._eval_rendering_success(wireframe_container, issues)

        dim_scores = {
            'requirement_coverage': cov_score,
            'sitemap_quality': sm_score,
            'layout_quality': layout_score,
            'content_relevance': content_score,
            'component_consistency': comp_score,
            'responsive_correctness': resp_score,
            'json_validity': json_score,
            'rendering_success': render_score
        }

        # Calculate weighted overall score
        overall = sum(dim_scores[d] * self.DIMENSION_WEIGHTS[d] for d in dim_scores)
        overall = max(0.0, min(100.0, overall))

        grade = self._calculate_grade(overall)
        recommendations = self._generate_recommendations(dim_scores, issues)

        website_category = str(wireframe_container.get('website_type') or sitemap_data.get('website_type') or 'business').lower()

        report = QualityReport(
            overall_score=overall,
            grade=grade,
            dimension_scores=dim_scores,
            issues=[asdict(i) for i in issues],
            recommendations=recommendations,
            metadata={
                'website_category': website_category,
                'pages_evaluated': len(wireframe_container.get('wireframes', {})),
                'total_sections': sum(len(p.get('sections', [])) for p in wireframe_container.get('wireframes', {}).values() if isinstance(p, dict))
            }
        )
        return report

    def _calculate_grade(self, score: float) -> str:
        if score >= 95.0:
            return 'A+'
        if score >= 90.0:
            return 'A'
        if score >= 80.0:
            return 'B'
        if score >= 70.0:
            return 'C'
        return 'F'

    # -------------------------------------------------------------------------
    # Dimension 1: Requirement Coverage
    # -------------------------------------------------------------------------
    def _eval_requirement_coverage(
        self,
        wireframe_container: Dict[str, Any],
        sitemap_data: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        wireframes = wireframe_container.get('wireframes', {})
        if not isinstance(wireframes, dict) or not wireframes:
            issues.append(QualityIssue('critical', 'requirement_coverage', 'No wireframes generated in container.'))
            return 0.0

        # Collect target pages from sitemap
        sitemap_pages = sitemap_data.get('pages', []) or []
        target_ids = set()

        def collect_ids(nodes: List[Dict[str, Any]]):
            for n in nodes or []:
                if isinstance(n, dict):
                    pid = str(n.get('id') or '').strip()
                    if pid:
                        target_ids.add(pid)
                    collect_ids(n.get('children') or [])

        collect_ids(sitemap_pages)

        # Check page coverage
        if target_ids:
            generated_ids = set(wireframes.keys())
            missing = target_ids - generated_ids
            if missing:
                missing_ratio = len(missing) / len(target_ids)
                penalty = missing_ratio * 50.0
                score -= penalty
                issues.append(QualityIssue('warning', 'requirement_coverage', f"Missing wireframes for {len(missing)} sitemap page(s): {list(missing)[:3]}"))

        # Check brief coverage (features, services, goals)
        brief = sitemap_data.get('brief') if isinstance(sitemap_data.get('brief'), dict) else {}
        expected_items = []
        for key in ('services', 'features', 'goals'):
            val = brief.get(key)
            if isinstance(val, list):
                expected_items.extend([str(v).lower() for v in val if str(v).strip()])
            elif isinstance(val, str) and val.strip():
                expected_items.extend([v.strip().lower() for v in val.split(',') if v.strip()])

        if expected_items:
            all_text = ""
            for p in wireframes.values():
                if isinstance(p, dict):
                    for s in p.get('sections', []):
                        if isinstance(s, dict):
                            all_text += " " + str(s.get('title') or '').lower()
                            all_text += " " + str(s.get('description') or '').lower()
                            for it in s.get('items', []):
                                if isinstance(it, dict):
                                    all_text += " " + str(it.get('title') or '').lower()

            matched = sum(1 for exp in expected_items if exp in all_text)
            coverage_pct = matched / len(expected_items)
            if coverage_pct < 0.5:
                score -= (1.0 - coverage_pct) * 20.0
                issues.append(QualityIssue('info', 'requirement_coverage', f"Only {matched}/{len(expected_items)} key brief terms explicitly referenced in wireframe copy."))

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Dimension 2: Sitemap Quality
    # -------------------------------------------------------------------------
    def _eval_sitemap_quality(
        self,
        sitemap_data: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        pages = sitemap_data.get('pages', []) or []
        if not pages:
            issues.append(QualityIssue('warning', 'sitemap_quality', 'Empty sitemap pages list.'))
            return 60.0

        page_ids = set()
        duplicate_ids = 0
        nameless_pages = 0

        def inspect_pages(nodes: List[Dict[str, Any]], depth: int = 1):
            nonlocal duplicate_ids, nameless_pages
            for p in nodes:
                if not isinstance(p, dict):
                    continue
                pid = str(p.get('id') or '').strip()
                pname = str(p.get('name') or '').strip()

                if not pname or pname.lower() == 'page':
                    nameless_pages += 1
                if pid:
                    if pid in page_ids:
                        duplicate_ids += 1
                    else:
                        page_ids.add(pid)

                children = p.get('children')
                if isinstance(children, list) and children:
                    inspect_pages(children, depth + 1)

        inspect_pages(pages)

        if duplicate_ids > 0:
            score -= duplicate_ids * 15.0
            issues.append(QualityIssue('critical', 'sitemap_quality', f"Detected {duplicate_ids} duplicate page ID(s) in sitemap."))

        if nameless_pages > 0:
            score -= nameless_pages * 10.0
            issues.append(QualityIssue('warning', 'sitemap_quality', f"Detected {nameless_pages} page(s) with generic or missing names."))

        # Check total pages breadth (1 to 15 is healthy)
        if len(page_ids) < 1:
            score -= 30.0

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Dimension 3: Layout Quality & Diversity
    # -------------------------------------------------------------------------
    def _eval_layout_quality(
        self,
        wireframe_container: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        wireframes = wireframe_container.get('wireframes', {})
        if not isinstance(wireframes, dict) or not wireframes:
            return 50.0

        for pid, p in wireframes.items():
            if not isinstance(p, dict):
                continue
            sections = p.get('sections', []) or []
            if len(sections) < 3:
                continue

            layouts = [str(s.get('layoutVariant') or '').strip().lower() for s in sections if isinstance(s, dict)]

            # Check for invalid layout strings
            for idx, lay in enumerate(layouts):
                if lay and lay not in SUPPORTED_LAYOUT_VARIANTS:
                    score -= 5.0
                    issues.append(QualityIssue('warning', 'layout_quality', f"Invalid layoutVariant '{lay}' on page {pid} section {idx}."))

            # Check adjacent layout repetition
            adjacent_dups = 0
            for i in range(1, len(layouts)):
                # Ignore adjacent default nav/footer framing
                if layouts[i] == layouts[i - 1] and layouts[i] not in ('layout-default',):
                    adjacent_dups += 1

            if adjacent_dups > 0:
                score -= adjacent_dups * 15.0
                issues.append(QualityIssue('warning', 'layout_quality', f"Page '{pid}' has {adjacent_dups} adjacent section(s) with identical layoutVariant."))

            # Check layout diversity (unique layouts count)
            unique_layouts = set(layouts)
            if len(sections) >= 3 and len(unique_layouts) == 1:
                score -= 25.0
                issues.append(QualityIssue('warning', 'layout_quality', f"Page '{pid}' has identical layout variant '{layouts[0]}' across all sections."))
            elif len(sections) >= 5 and len(unique_layouts) < 3:
                score -= 15.0
                issues.append(QualityIssue('warning', 'layout_quality', f"Page '{pid}' lacks visual diversity: only {len(unique_layouts)} unique layout(s) across {len(sections)} sections."))

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Dimension 4: Content Relevance & Copy Quality
    # -------------------------------------------------------------------------
    def _eval_content_relevance(
        self,
        wireframe_container: Dict[str, Any],
        sitemap_data: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        wireframes = wireframe_container.get('wireframes', {})
        if not isinstance(wireframes, dict) or not wireframes:
            return 50.0

        website_type = str(wireframe_container.get('website_type') or sitemap_data.get('website_type') or '').lower()
        brief = sitemap_data.get('brief') if isinstance(sitemap_data.get('brief'), dict) else {}
        client = str(brief.get('client') or '').lower()

        # Identify category key for vocabulary inspection
        matched_cat = None
        for cat_key in self.CATEGORY_VOCABULARY:
            if cat_key in website_type:
                matched_cat = cat_key
                break

        generic_matches = 0
        total_sections = 0
        has_category_terms = False if matched_cat else True
        all_text = ""

        for pid, p in wireframes.items():
            if not isinstance(p, dict):
                continue
            for idx, s in enumerate(p.get('sections', []) or []):
                if not isinstance(s, dict):
                    continue
                total_sections += 1
                title = str(s.get('title') or '').strip()
                desc = str(s.get('description') or '').strip()
                combined = f"{title} {desc}".lower()
                all_text += " " + combined

                # Check forbidden generic copy
                for pat in self.GENERIC_COPY_PATTERNS:
                    if re.search(pat, combined):
                        generic_matches += 1
                        score -= 20.0
                        issues.append(QualityIssue('critical', 'content_relevance', f"Generic placeholder copy detected on page '{pid}' section {idx}: '{title}'"))
                        break

                # Check minimum depth
                if len(desc) < 15 and s.get('type') not in ('navbar', 'footer'):
                    score -= 3.0
                    issues.append(QualityIssue('info', 'content_relevance', f"Section description is too short on page '{pid}' section {idx}: '{desc}'"))

        # Verify category vocabulary presence if known category
        if matched_cat and total_sections > 0:
            expected_vocab = self.CATEGORY_VOCABULARY[matched_cat]
            hits = [word for word in expected_vocab if word in all_text]
            if len(hits) >= 2:
                has_category_terms = True
            else:
                score -= 15.0
                issues.append(QualityIssue('warning', 'content_relevance', f"Copy lacks expected domain terminology for category '{matched_cat}'. Found only: {hits}"))

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Dimension 5: Component Consistency
    # -------------------------------------------------------------------------
    def _eval_component_consistency(
        self,
        wireframe_container: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        wireframes = wireframe_container.get('wireframes', {})
        if not isinstance(wireframes, dict) or not wireframes:
            return 50.0

        for pid, p in wireframes.items():
            if not isinstance(p, dict):
                continue
            sections = p.get('sections', []) or []
            if not sections:
                score -= 25.0
                issues.append(QualityIssue('critical', 'component_consistency', f"Page '{pid}' has no sections."))
                continue

            types = [str(s.get('type') or '').strip().lower() for s in sections if isinstance(s, dict)]

            # Check supported canonical types
            for idx, stype in enumerate(types):
                if stype and stype not in SUPPORTED_SECTION_TYPES:
                    score -= 5.0
                    issues.append(QualityIssue('warning', 'component_consistency', f"Unsupported component type '{stype}' on page '{pid}' section {idx}."))

            # Mandatory Framing: Navbar first
            if types[0] != 'navbar':
                score -= 25.0
                issues.append(QualityIssue('warning', 'component_consistency', f"Page '{pid}' missing mandatory Navbar at top (found '{types[0]}')."))

            # Mandatory Framing: Footer last
            if types[-1] != 'footer':
                score -= 25.0
                issues.append(QualityIssue('warning', 'component_consistency', f"Page '{pid}' missing mandatory Footer at bottom (found '{types[-1]}')."))

            # Primary Hero on Home page
            if pid == 'home' or p.get('page_type') == 'home':
                if 'hero' not in types:
                    score -= 15.0
                    issues.append(QualityIssue('warning', 'component_consistency', f"Home page '{pid}' missing high-conversion Hero section."))

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Dimension 6: Responsive Correctness
    # -------------------------------------------------------------------------
    def _eval_responsive_correctness(
        self,
        wireframe_container: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        wireframes = wireframe_container.get('wireframes', {})
        if not isinstance(wireframes, dict) or not wireframes:
            return 50.0

        for pid, p in wireframes.items():
            if not isinstance(p, dict):
                continue
            for idx, s in enumerate(p.get('sections', []) or []):
                if not isinstance(s, dict):
                    continue
                layout = str(s.get('layoutVariant') or '').strip().lower()
                items = s.get('items', []) or []
                item_count = len(items) if isinstance(items, list) else 0

                # Grid-3 responsiveness: single item in a grid is awkward
                if layout == 'layout-grid-3' and item_count == 1:
                    score -= 5.0
                    issues.append(QualityIssue('info', 'responsive_correctness', f"Single item in layout-grid-3 on page '{pid}' section {idx}."))

                # Grid-4 responsiveness: odd count like 3 in grid-4 leaves orphan column
                if layout == 'layout-grid-4' and item_count == 3:
                    score -= 3.0
                    issues.append(QualityIssue('info', 'responsive_correctness', f"Grid-4 with 3 items creates asymmetric grid wrap on page '{pid}' section {idx}."))

                # Navbar menu items count for mobile collapse
                if s.get('type') == 'navbar':
                    menu = s.get('menuItems', [])
                    if isinstance(menu, list) and len(menu) > 8:
                        score -= 5.0
                        issues.append(QualityIssue('info', 'responsive_correctness', f"Navbar has {len(menu)} items; recommended max is 7 for clean responsive collapse."))

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Dimension 7: JSON Validity
    # -------------------------------------------------------------------------
    def _eval_json_validity(
        self,
        wireframe_container: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        is_valid, validated_model, errors = validate_wireframe(wireframe_container)
        if is_valid:
            return 100.0

        score = 100.0 - min(60.0, len(errors) * 12.0)
        for err in errors[:3]:
            issues.append(QualityIssue('critical', 'json_validity', f"Pydantic schema validation error: {err}"))
        return max(0.0, score)

    # -------------------------------------------------------------------------
    # Dimension 8: Rendering Success
    # -------------------------------------------------------------------------
    def _eval_rendering_success(
        self,
        wireframe_container: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        score = 100.0
        wireframes = wireframe_container.get('wireframes', {})
        if not isinstance(wireframes, dict) or not wireframes:
            return 40.0

        for pid, p in wireframes.items():
            if not isinstance(p, dict):
                score -= 10.0
                continue
            sections = p.get('sections', [])
            if not isinstance(sections, list):
                score -= 15.0
                continue

            for idx, s in enumerate(sections):
                if not isinstance(s, dict):
                    score -= 5.0
                    continue
                # Required keys for rendering
                if not s.get('type'):
                    score -= 5.0
                    issues.append(QualityIssue('critical', 'rendering_success', f"Section {idx} on page '{pid}' missing 'type'."))
                if not s.get('title'):
                    score -= 2.0
                    issues.append(QualityIssue('warning', 'rendering_success', f"Section {idx} on page '{pid}' missing 'title'."))
                if not s.get('layoutVariant'):
                    score -= 2.0

        return max(0.0, min(100.0, score))

    # -------------------------------------------------------------------------
    # Actionable Recommendation Synthesis
    # -------------------------------------------------------------------------
    def _generate_recommendations(
        self,
        scores: Dict[str, float],
        issues: List[QualityIssue]
    ) -> List[str]:
        recs = []

        if scores.get('layout_quality', 100) < 90:
            recs.append("Increase visual rhythm by alternating adjacent section layouts (e.g. follow a 3-column grid with a split-content or cards layout).")

        if scores.get('content_relevance', 100) < 90:
            recs.append("Replace generic copy and placeholder labels with authentic domain-specific terminology, proof points, and client value propositions.")

        if scores.get('component_consistency', 100) < 90:
            recs.append("Ensure mandatory framing sections are present on all pages: sticky Navbar at the top and comprehensive Footer at the bottom.")

        if scores.get('requirement_coverage', 100) < 90:
            recs.append("Verify all sitemap pages are generated and client brief priorities (services, features, target audience) are reflected in section titles.")

        if scores.get('responsive_correctness', 100) < 90:
            recs.append("Balance grid item counts (e.g. 3 or 6 for grid-3, 4 for grid-4) to prevent orphan columns on mobile and tablet viewport collapsing.")

        if not recs:
            recs.append("Generation quality meets highest standard. Ready for export and client review.")

        return recs
