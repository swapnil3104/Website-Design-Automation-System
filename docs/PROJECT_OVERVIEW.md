# Website Design Automation Platform: Project Overview

**Document Status:** Production Reference  
**Document Version:** 1.0.0  
**Project:** AI-Powered Website Design Automation Platform  
**Target Audience:** Software Engineers, UX Designers, Product Managers, System Administrators  

---

## 1. System Vision & Core Value Proposition

Modern website design workflows often suffer from disconnected handoffs, tedious placeholder copywriting, repetitive layouts, and brittle toolchains. The **Website Design Automation Platform** is an enterprise-grade AI system that bridges the gap between raw natural language intent and production-ready visual web architecture.

From a single sentence prompt or client interview, the platform generates:
1. An intelligent, multi-level **website sitemap** reflecting industry best practices and conversion psychology.
2. Complete, responsive, content-rich **visual wireframes** across every page in the sitemap.
3. Interactive **multi-device previews** (Desktop, Tablet, Mobile) with fluid breakpoint behaviors.
4. A flexible **browser-based editor** allowing real-time section reordering, component replacement, and inline text editing.
5. Production-ready **export packages** including Vite + Tailwind CSS v4 React component suites.

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│  Natural Prompt │ ────> │ Sitemap & Pages │ ────> │ Multi-Page Wire- │
│  or Client Brief│       │    Hierarchy    │       │  frame Canvas    │
└─────────────────┘       └─────────────────┘       └─────────┬────────┘
                                                              │
                          ┌─────────────────┐                 │
                          │ React / Tailwind│ <───────────────┘
                          │   Vite Export   │
                          └─────────────────┘
```

---

## 2. Core Architectural Pillars

The platform is designed around five non-negotiable architectural mandates:

### 1. Zero-Placeholder Copywriting
Generic placeholder text (`Lorem Ipsum`, `Title 1`, `Feature A`) undermines UX evaluation. The generation engine mandates rich, industry-authentic copy across all 10 supported website sectors—complete with domain-specific metrics, value propositions, and contextual call-to-actions.

### 2. Multi-Tier AI Provider Resilience
To ensure zero operational downtime, the system implements a cascading AI execution pipeline:
- **Primary Local Model**: `qwen2.5:3b` executing locally via Ollama with native JSON mode (40.9 tokens/sec, 4.99s latency, 2.18GB VRAM).
- **Frontier Cloud Fallback**: OpenRouter API supporting models like Claude 3.7 Sonnet and GPT-4.1 with automated retry and API key secret scrubbing.
- **Deterministic Offline Safety Net**: A high-fidelity fallback generator running in 0.01s that synthesizes complete wireframe containers without network dependencies.

### 3. Self-Healing Schema Validation
Large language models occasionally produce truncated JSON, trailing commas, or markdown fences. The platform incorporates a 4-tier self-healing repair pipeline:
1. Markdown fence and commentary isolation.
2. Trailing comma cleanup and bracket balancing.
3. Heuristic normalization (aliasing informal types like `testimonials-slider` to `testimonials`).
4. Strict Pydantic v2 validation ensuring schema conformance.

### 4. Layout Diversity & Anti-Repetition
Web designs look artificial when identical layouts appear sequentially. The platform's `PagePlanner` enforces layout diversity rules that prohibit adjacent sections from sharing layout variants (e.g., alternating `layout-grid-3` with `layout-split` or `layout-cards`).

### 5. Deterministic Client-Side State
The frontend relies on an event-driven `StateManager` that synchronizes mutations across canvas views, sidebar controllers, and persistent `localStorage` with sub-millisecond latency.

---

## 3. Detailed Feature Breakdown by Phase

### Phase 1: Architecture & Technical Foundation
- Standardized data contracts for Sitemap (`SitemapModel`) and Wireframe (`WireframeContainerModel`).
- Established the abstract `BaseAIProvider` interface with structured `CompletionRequest` and `CompletionResponse` dataclasses.
- Documented the catalog of 25 canonical page types, 32 canonical section types, and 18 layout variations.

### Phase 2: AI Provider Integration
- Implemented `OllamaProvider`, `OpenRouterProvider`, and `MockFallbackProvider`.
- Built `execute_completion_with_fallback()` with automatic retry mechanics and exponential backoff.
- Configured secret masking to ensure API keys and private tokens are never leaked to logs or client endpoints (`GET /api/config/`).

### Phase 3: Requirement Analysis & Sitemap Generation
- Created `RequirementAnalyzer` supporting 10 distinct website taxonomies (Business, SaaS, E-commerce, Portfolio, Agency, Healthcare, Education, Agriculture, Blog/Media, Restaurant).
- Implemented path syntax parsing (`Parent > Child`) and bulleted hierarchy extraction.
- Built dynamic brief clarification question generator tailoring inquiries to missing project specifications.

### Phase 4: AI Wireframe Generation Engine
- Built `PagePlanner` featuring 25 specialized page blueprints with strict vertical section sequencing.
- Implemented `WireframeService` orchestrating batch generation of all sitemap pages and single-page on-demand generation.
- Added mandatory top navbar and bottom footer framing across all generated views.

### Phase 5: Wireframe Component Library & Renderer
- Engineered modular `WireframeComponents` library containing zero-crash renderers for all 32 section types.
- Standardized Lucide SVG iconography across all components.
- Built Vite + Tailwind CSS v4 React export pipeline producing 20 modular JSX templates.

### Phase 6: Responsive Design & Visual Wireframe Editor
- Added multi-device responsive canvas toggle: **Desktop** (1024px+), **Tablet** (768px), and **Mobile** (375px).
- Implemented responsive grid collapsing rules (e.g., 4 columns → 2 on tablet → 1 on mobile).
- Built complete section CRUD: Add Section modal (32 types), Move Up/Down reordering, and Delete.
- Implemented inline two-way text editing synchronized with sidebar property controls.

### Phase 7: Design Quality & Generation Optimization
- Added comprehensive `CATEGORY_PAGE_BLUEPRINTS` with 8–10 diverse sections per website category.
- Implemented Anti-Repetition Engine enforcing alternating layouts and section types.
- Engineered 8-dimension formal `QualityEvaluator` scoring wireframes (0–100) and assigning letter grades (A+, A, B, C, F).

### Phase 8: Testing & Model Benchmarking
- Developed 20 standardized test prompts spanning 10 industry categories.
- Conducted empirical benchmarks comparing `qwen2.5:3b`, `nemotron-mini:4b`, `claude-3.7-sonnet`, and deterministic fallback.
- Selected **`qwen2.5:3b` as the primary local model** due to 1.77x higher throughput, 2.57x lower latency, and 710MB leaner VRAM footprint compared to alternatives.

### Phase 9: Final Stabilization & Documentation
- Eliminated dead code, unused dependencies (`openai`), and temporary migration scripts.
- Hardened all 8 REST API controllers with standard JSON exception envelopes.
- Verified database persistence models (`Sitemap`, `Page`) and Django initial migrations.
- Established 100% automated test pass rate across 144 unit, integration, and end-to-end tests.

---

## 4. Supported Taxonomies & Component Catalog

### 10 Canonical Website Categories
1. **Business / Corporate**: Consulting firms, enterprise services, corporate headquarters.
2. **SaaS / Tech**: Software platforms, developer tools, cloud infrastructure.
3. **E-commerce / Retail**: Online storefronts, boutique goods, consumer products.
4. **Portfolio / Creative**: Freelance designers, agencies, motion graphics, studios.
5. **Agency / Digital**: Marketing agencies, branding consultancies, development shops.
6. **Healthcare / Medical**: Dental clinics, hospitals, specialized wellness practices.
7. **Education / Learning**: Academies, universities, online course providers.
8. **Agriculture / Farming**: Sustainable farms, agricultural suppliers, harvest cooperatives.
9. **Blog / Editorial**: Digital magazines, tech publications, news portals.
10. **Restaurant / Hospitality**: Fine dining, bistros, coffee roasters, catering services.

### 32 Canonical Section Types

| Semantic Group | Section Types |
|---|---|
| **Navigation & Framing** | `navbar`, `footer` |
| **Hero Banners** | `hero`, `hero-split`, `hero-product`, `hero-cta`, `hero-centered` |
| **Content & Showcase** | `about`, `story`, `image-text`, `features`, `services`, `products`, `gallery`, `process`, `blog-grid` |
| **Social Proof & Metrics** | `stats`, `testimonials`, `team`, `trust-badges`, `case-studies` |
| **Conversion & Commercial** | `pricing`, `faq`, `contact`, `cta`, `newsletter` |
| **Industry-Specific** | `menu` (Restaurant), `timelines` (Agri), `doctors` (Health), `booking` |

---

## 5. Quality Evaluation Engine: The 8 Dimensions

Every generated wireframe can be scored on-demand via `POST /api/evaluate-quality/`:

```
                       Quality Score (0 - 100)
                                 │
     ┌──────────────┬────────────┴─────────────┬──────────────┐
     ▼              ▼                          ▼              ▼
 Requirement     Layout        Content     Component     Responsive
  Coverage      Quality       Relevance   Consistency   Correctness
   (15%)         (15%)          (15%)        (10%)         (10%)
```

1. **Requirement Coverage (15%)**: Assesses whether all requested pages and specific brief capabilities are present.
2. **Sitemap Quality (10%)**: Checks hierarchy validity, slug formatting, unique page IDs, and clear navigation labels.
3. **Layout Quality (15%)**: Penalizes consecutive identical layout variants and rewards structural diversity.
4. **Content Relevance (15%)**: Detects and penalizes generic dummy text (`Lorem Ipsum`, `Product 1`) while checking for domain keywords.
5. **Component Consistency (10%)**: Verifies structural anchors: top navbar, hero on home, and bottom footer.
6. **Responsive Correctness (10%)**: Validates item counts for grid layouts (e.g. exactly 4 items for 4-column cards).
7. **JSON Validity (15%)**: Enforces strict Pydantic v2 schema validation without fallback degradation.
8. **Rendering Success (10%)**: Simulates headless DOM instantiation of all sections with zero JavaScript errors.

---

## 6. Development & Deployment Guide

### Running Development Server
```bash
cd backend
python manage.py runserver 8000
```

### Running Test Suites
```bash
# Complete 144-test suite
python -m unittest discover -s backend/tests -p "test_*.py"

# Targeted phase suites
python -m unittest backend.tests.test_phase9_stabilization -v
python -m unittest backend.tests.test_phase8_benchmarking_and_testing -v
python -m unittest backend.tests.test_phase7_quality_optimization -v
```

### Production Checklist
- [x] Set `DEBUG=False` in `backend/.env`.
- [x] Configure explicit `ALLOWED_HOSTS` and CORS origins in `backend/core/settings.py`.
- [x] Ensure Ollama service is running (`systemctl status ollama` or local desktop client).
- [x] Verify database migrations: `python manage.py migrate`.
- [x] Verify system check: `python manage.py check --deploy`.

