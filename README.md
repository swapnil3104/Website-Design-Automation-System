# AI Website Design Automation Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.14.0-red.svg)](https://www.django-rest-framework.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.0%2B-purple.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/Tests-144%20Passed-brightgreen.svg)](#testing-and-verification)

An end-to-end AI-powered website design and wireframe automation system that transforms natural language prompts and client briefs into complete, responsive, multi-page website sitemaps and production-ready visual wireframes.

---

## 🌟 Key Capabilities

- **Zero-Friction Requirement Analysis**: Parses conversational prompts and structured briefs into 10 industry categories, extracting business goals, target personas, design styles, and navigation requirements.
- **Dynamic Sitemap Generation**: Builds hierarchical multi-page site maps with parent-child links, primary navigation detection, and conversion objectives.
- **AI Wireframing with Cascading Failover**: Generates complete wireframes powered by a multi-tier provider pipeline:
  - **Primary Local LLM**: `qwen2.5:3b` via Ollama (40.9 tokens/sec, 4.99s latency, 2.18GB VRAM).
  - **Cloud Frontier LLM**: Claude 3.7 Sonnet / GPT-4.1 via OpenRouter API.
  - **Deterministic Zero-Crash Fallback**: Offline generator producing full wireframes in 0.01s without network connectivity.
- **Modular Component Library**: Dedicated DOM renderers for **32 canonical section types** across 10 industry taxonomies with Lucide iconography.
- **Anti-Repetition & Layout Diversity Engine**: Guarantees distinct adjacent layouts across 8 canonical variations (Full-width, 2-Col, 3-Col, 4-Col Grid, Split 50/50, Sidebar 70/30, Centered Stack, Asymmetric).
- **Interactive Multi-Device Canvas**: Desktop (1024px+), Tablet (768px), and Mobile (375px) responsive previews with responsive grid collapsing, mobile navigation drawer, and aspect-ratio mockup placeholders.
- **Comprehensive Visual Editor**:
  - Full section CRUD (Add, Delete, Reorder with Move Up/Down toolbar).
  - Inline content editing with real-time two-way synchronization.
  - Section-level and page-level targeted regeneration.
  - Component replacement modal featuring all 32 categorized section types.
  - Auto-saving state manager with animated status indicators.
- **8-Dimension Quality Evaluation Engine**: Formally evaluates requirement coverage, sitemap quality, layout diversity, content relevance, component consistency, responsive correctness, JSON validity, and DOM render success (0–100 score and letter grade).
- **Multi-Format Production Export**: One-click download of structured JSON, or a complete Vite + Tailwind CSS v4 React application bundle with 20 modular JSX components.

---

## 🏗️ System Architecture

```
User Prompt / Client Brief
          │
          ▼
┌──────────────────────────────────────────────┐
│  Requirement Analyzer (analyzer.py)          │
│  - 10 Industry Taxonomies                    │
│  - Category-aware dynamic questions          │
│  - Hierarchy parsing & path syntax           │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Sitemap Engine (sitemap_service.py)         │
│  - Primary nav flags & parent-child linkage  │
│  - Self-healing repair pipeline              │
│  - Pydantic v2 validation (sitemap.py)       │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Page Planner & Blueprints (page_planner.py) │
│  - 25 Canonical page types                   │
│  - 8-10 Tailored sections per category       │
│  - Anti-Repetition & layout alternating      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  AI Wireframe Service (wireframe_service.py) │
│  - Ollama (qwen2.5:3b) / OpenRouter          │
│  - Multi-stage JSON heuristic repair         │
│  - Pydantic v2 validation (wireframe.py)     │
│  - Zero-crash deterministic fallback         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Frontend Presentation & Editor              │
│  - WireframeComponents (32 component types)  │
│  - Multi-device canvas (Desktop/Tablet/Phone)│
│  - Real-time inline & sidebar editing        │
│  - Vite + Tailwind v4 React ZIP export       │
└──────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
wireframe-ai/
├── backend/
│   ├── core/                          # Django configuration & settings
│   │   ├── config.py                  # Centralized typed configuration & secret protection
│   │   ├── settings.py                # Django app settings & logging
│   │   └── urls.py                    # Root URL router
│   ├── sitemap_app/                   # Core application
│   │   ├── analyzer.py                # RequirementAnalyzer & category detector
│   │   ├── page_planner.py            # PagePlanner & CATEGORY_PAGE_BLUEPRINTS
│   │   ├── quality_evaluator.py       # 8-Dimension Quality Evaluation Engine
│   │   ├── sitemap_service.py         # SitemapService & hierarchy engine
│   │   ├── wireframe_service.py       # WireframeService & generation coordinator
│   │   ├── views.py                   # REST API controllers
│   │   ├── urls.py                    # API route declarations (/api/*)
│   │   ├── serializers.py             # DRF serializers with dictionary validation
│   │   ├── models.py                  # Sitemap and Page SQLite persistence models
│   │   ├── providers/                 # AI Provider Subsystem
│   │   │   ├── base.py                # BaseAIProvider, CompletionRequest/Response
│   │   │   ├── ollama_provider.py     # Local Ollama client with JSON mode
│   │   │   ├── openrouter_provider.py # Cloud OpenRouter client with failover
│   │   │   ├── mock_provider.py       # Deterministic zero-crash provider
│   │   │   └── factory.py             # Resolver & cascading failover executor
│   │   └── schemas/                   # Pydantic v2 schemas & repair pipelines
│   │       ├── sitemap.py             # Sitemap validation & self-healing
│   │       └── wireframe.py           # Wireframe container validation & repairs
│   ├── tests/                         # Comprehensive automated test suite
│   │   ├── test_ai_providers.py       # Provider unit tests
│   │   ├── test_api_integration.py   # API integration tests
│   │   ├── test_phase3_sitemap.py     # Sitemap & analyzer tests
│   │   ├── test_phase4_wireframe.py   # Wireframe engine tests
│   │   ├── test_phase5_component_renderer.py # Component renderer tests
│   │   ├── test_phase6_editor.py      # Multi-device canvas & editor tests
│   │   ├── test_phase7_quality_optimization.py # Quality evaluator tests
│   │   ├── test_phase8_benchmarking_and_testing.py # Benchmarking tests
│   │   ├── test_phase9_stabilization.py # Stabilization & release tests
│   │   └── benchmark_suite_20.py      # Executable 20-prompt model benchmark
│   ├── .env.example                   # Template environment configuration
│   └── requirements.txt               # Backend Python dependencies
├── frontend/
│   ├── index.html                     # Sitemap generator & tree visualizer
│   ├── chat.html                      # Conversational briefing assistant
│   ├── wireframe.html                 # Visual wireframe canvas & editor
│   ├── css/
│   │   ├── style.css                  # Base application styles
│   │   ├── wireframe.css              # Wireframe canvas, board, and responsive rules
│   │   └── chat.css                   # Conversational UI styles
│   └── js/
│       ├── app.js                     # Sitemap application coordinator
│       ├── chat.js                    # Chat assistant workflow
│       ├── state-manager.js           # Pub-sub state store with localStorage sync
│       ├── wireframe-icons.js         # Lucide SVG icon catalog
│       ├── wireframe-components.js     # 32 Canonical component renderers
│       ├── wireframe-editor.js        # Canvas interaction, reordering & CRUD
│       └── wireframe.js               # WireframeApp & React JSX ZIP export
├── docs/                              # Comprehensive documentation suite
│   ├── PROJECT_OVERVIEW.md            # Deep project overview & user guide
│   ├── ARCHITECTURE.md                # System topology & API contracts
│   ├── GENERATION_PIPELINE.md         # Blueprints, prompts & repair pipelines
│   ├── WIREFRAME_COMPONENTS.md        # Catalog of all 32 section renderers
│   ├── WIREFRAME_SCHEMA.md            # JSON schema specifications
│   ├── MODEL_BENCHMARK.md             # Empirical model benchmarking report
│   ├── TESTING_REPORT.md              # Quality metrics & testing verification
│   ├── CODEBASE_AUDIT.md              # Initial audit & gap analysis
│   └── CHANGELOG.md                   # Full release history
└── Plan.md                            # Complete 10-phase execution plan
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Modern Web Browser (Chrome, Firefox, Edge, Safari)
- Optional: [Ollama](https://ollama.ai/) for local AI execution
- Optional: OpenRouter API key for cloud frontier models

### 1. Backend Setup

```bash
# Clone the repository
cd wireframe-ai/backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

### 2. Configure AI Providers in `.env`

```ini
# Choose provider: 'auto', 'ollama', 'openrouter', or 'mock'
AI_PROVIDER=auto

# Local Ollama Settings (Recommended: qwen2.5:3b)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# OpenRouter Settings (Optional cloud provider)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.7-sonnet
```

If Ollama is installed:
```bash
ollama run qwen2.5:3b
```

### 3. Start Application

```bash
# Apply database migrations
python manage.py migrate

# Run the Django development server
python manage.py runserver 8000
```

Open your browser to:
- **Interactive Wireframe Canvas**: `http://localhost:8000/static/wireframe.html` (or open `frontend/wireframe.html` directly)
- **Sitemap Generator**: `http://localhost:8000/static/index.html` (or `frontend/index.html`)
- **Conversational Assistant**: `http://localhost:8000/static/chat.html` (or `frontend/chat.html`)

---

## 📡 REST API Reference

All API routes return standardized JSON envelopes:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/config/` | Safe configuration (active provider, models, sanitizes secrets) |
| `POST` | `/api/init-brief/` | Dynamic clarification questions & category detection |
| `POST` | `/api/generate-sitemap/` | Full sitemap generation with hierarchy & navigation |
| `POST` | `/api/update-sitemap/` | Validate and update sitemap data |
| `POST` | `/api/generate-wireframe/` | Multi-page or single-page wireframe generation |
| `POST` | `/api/regenerate-section/` | Contextual regeneration of a single section |
| `POST` | `/api/evaluate-quality/` | 8-dimension formal quality evaluation report |
| `POST` | `/api/export-json/` | Download sitemap as a formatted JSON attachment |

---

## 🧪 Testing and Verification

The test suite contains **144 unit, integration, and end-to-end tests** covering all phases:

```bash
# Run the complete test suite
python -m unittest discover -s backend/tests -p "test_*.py"

# Run Django system health check
python backend/manage.py check

# Run Phase 9 stabilization suite specifically
python -m unittest backend.tests.test_phase9_stabilization -v
```

**Results:**
- **144 tests passed** (0 failures, 0 errors, 2 expected skips for offline Ollama service).
- **100% test pass rate** across all subsystems.

---

## 📄 License & Attribution

Developed as part of the Website Design Automation Project. Licensed under the MIT License.

