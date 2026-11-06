# Changelog: AI Website Design Automation Platform

All notable changes and architectural milestones for this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-04 — Production Release (Phase 9 Complete)

### Completed
- **Phase 9: Final Stabilization & Documentation**
  - Pruned unused dependencies from `backend/requirements.txt` (removed obsolete `openai>=1.0.0` dependency; providers use lightweight `requests`).
  - Removed unused imports and dead code in `backend/sitemap_app/services.py`.
  - Archived obsolete migration script `patch_html.py` and cleaned up residual artifacts.
  - Added strict dictionary payload validation in `SitemapUpdateSerializer`.
  - Hardened all 8 REST API controllers (`/api/config/`, `/api/init-brief/`, `/api/generate-sitemap/`, `/api/update-sitemap/`, `/api/export-json/`, `/api/generate-wireframe/`, `/api/regenerate-section/`, `/api/evaluate-quality/`) with standard JSON exception envelopes.
  - Added SQLite migration `0001_initial.py` for `Sitemap` and `Page` persistence models.
  - Created complete project documentation: `README.md`, `docs/PROJECT_OVERVIEW.md`, `docs/CHANGELOG.md`, and updated `docs/ARCHITECTURE.md`.
  - Created automated Phase 9 test suite (`backend/tests/test_phase9_stabilization.py`) with 20 comprehensive unit and integration tests.
  - Full test suite verified: **144 tests passed with 100% pass rate**.

---

## [0.9.0] - 2026-11-04 — Phase 8: Testing & Model Benchmarking

### Added
- Standardized test prompt catalog with 20 distinct industry test prompts across 10 categories.
- Benchmarking test harness (`backend/tests/benchmark_suite_20.py`) evaluating `qwen2.5:3b`, `nemotron-mini:4b`, `claude-3.7-sonnet`, and deterministic fallback.
- Benchmark results dataset (`backend/benchmark_20_prompts_results.json`).
- Detailed benchmark report (`docs/MODEL_BENCHMARK.md`) establishing `qwen2.5:3b` as the primary local model (40.9 tok/s, 4.99s latency, 100% JSON validity, 2.18GB VRAM).
- System-wide testing report (`docs/TESTING_REPORT.md`) detailing quality verification metrics.
- Automated test suite (`backend/tests/test_phase8_benchmarking_and_testing.py`) containing 26 unit and integration tests.

---

## [0.8.0] - 2026-11-03 — Phase 7: Design Quality & Generation Optimization

### Added
- Expanded industry category taxonomy to 10 distinct sectors in `backend/sitemap_app/analyzer.py`.
- Comprehensive `CATEGORY_PAGE_BLUEPRINTS` in `backend/sitemap_app/page_planner.py` featuring 8–10 tailored sections per category.
- Anti-Repetition & Layout Diversity Engine (`enforce_layout_diversity`) preventing adjacent duplicate layout variants and section pairings.
- Zero-placeholder copywriting mandates in `backend/sitemap_app/wireframe_service.py`.
- 8-dimension formal Quality Evaluation Engine (`backend/sitemap_app/quality_evaluator.py`) scoring wireframes 0–100 with letter grades (A+, A, B, C, F).
- REST endpoint `POST /api/evaluate-quality/`.
- Architecture and blueprints documentation in `docs/GENERATION_PIPELINE.md`.
- Automated test suite (`backend/tests/test_phase7_quality_optimization.py`) with 10 unit and integration tests.

---

## [0.7.0] - 2026-11-02 — Phase 6: Responsive Design & Wireframe Editor

### Added
- Multi-device responsive canvas toggle (`#deviceToggleGroup`): Desktop (1024px+), Tablet (768px), and Mobile (375px).
- Responsive grid collapsing rules and mobile navigation drawer in `frontend/css/wireframe.css`.
- Page Switcher dropdown (`#pageSelectDropdown`) with "All Pages" multi-board view and single-page focus view.
- Complete section CRUD: Add Section modal (32 section types), Move Up/Down reordering toolbar, and Delete confirmation.
- Real-time inline text editing synchronized with sidebar properties.
- Component Type Replacement modal.
- Targeted section-level (`POST /api/regenerate-section/`) and page-level regeneration (`POST /api/generate-wireframe/`).
- Auto-saving state manager syncing to `localStorage` with header save status indicator.
- Automated test suite (`backend/tests/test_phase6_editor.py`) with 17 unit and integration tests.

---

## [0.6.0] - 2026-11-01 — Phase 5: Wireframe Component Library & Renderer

### Added
- Modular, zero-crash `WireframeComponents` library (`frontend/js/wireframe-components.js`) with dedicated DOM renderers for all 32 section types.
- Standardized Lucide SVG iconography catalog (`frontend/js/wireframe-icons.js`).
- Layout engine supporting 8 canonical configurations (Full-width, 2-Col, 3-Col, 4-Col, Split 50/50, Sidebar 70/30, Centered Stack, Asymmetric).
- Vite + Tailwind CSS v4 React export pipeline producing 20 modular JSX templates.
- Automated test suite (`backend/tests/test_phase5_component_renderer.py`) with 10 tests.
- Documentation in `docs/WIREFRAME_COMPONENTS.md`.

---

## [0.5.0] - 2026-10-31 — Phase 4: AI Wireframe Generation Engine

### Added
- Formal Pydantic v2 schemas (`backend/sitemap_app/schemas/wireframe.py`) for sections, items, and containers.
- Deterministic self-healing auto-repair pipeline normalizing aliases and infilling empty card/grid items.
- `PagePlanner` (`backend/sitemap_app/page_planner.py`) detecting 25 canonical page types and enforcing section weights.
- `WireframeService` (`backend/sitemap_app/wireframe_service.py`) with multi-stage JSON repair and cascading failover.
- Automated test suite (`backend/tests/test_phase4_wireframe.py`) with 17 tests.

---

## [0.4.0] - 2026-10-30 — Phase 3: Requirement Analysis & Sitemap Generation

### Added
- Modular `RequirementAnalyzer` (`backend/sitemap_app/analyzer.py`) extracting objectives, personas, and design preferences.
- Path syntax parsing (`Parent > Child`) and bulleted hierarchy extraction.
- Dynamic brief clarification questions generator (`generate_brief_questions`).
- Pydantic v2 sitemap validation schemas (`backend/sitemap_app/schemas/sitemap.py`).
- `SitemapService` (`backend/sitemap_app/sitemap_service.py`) generating primary nav flags and parent-child linkages.
- Automated test suite (`backend/tests/test_phase3_sitemap.py`) with 27 tests.

---

## [0.3.0] - 2026-10-29 — Phase 2: AI Provider Integration

### Added
- Abstract `BaseAIProvider` interface and dataclasses (`CompletionRequest`, `CompletionResponse`, `TokenUsage`).
- Concrete `OllamaProvider` with native JSON mode and health checks.
- Concrete `OpenRouterProvider` with multi-model fallback and API key sanitization.
- Deterministic `MockFallbackProvider` for offline development and testing.
- `execute_completion_with_fallback()` cascading failover pipeline.
- Centralized configuration in `backend/core/config.py` with secret scrubbing.
- Automated test suite (`backend/tests/test_ai_providers.py`) with 13 tests.
- Documentation in `docs/AI_PROVIDER_SETUP.md`.

---

## [0.2.0] - 2026-10-28 — Phase 1: Architecture & Technical Foundation

### Added
- System topology specification and architecture review (`docs/ARCHITECTURE.md`).
- Unified JSON schemas for Sitemap and Wireframe models (`docs/WIREFRAME_SCHEMA.md`).
- Catalog of 25 canonical page types, 32 section types, and 18 layout variations.
- System error handling and automated repair pipeline specifications.

---

## [0.1.0] - 2026-10-27 — Phase 0: Project Discovery & Codebase Audit

### Added
- In-depth codebase audit report (`docs/CODEBASE_AUDIT.md`) documenting architectural fragmentation, missing fallbacks, broken reasoning parameters, and fragile markdown stripping.
- 10-phase Master Execution Plan (`Plan.md`).

