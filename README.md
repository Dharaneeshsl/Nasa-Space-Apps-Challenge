---
title: CombustionLens
emoji: 🛰️
colorFrom: red
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# CombustionLens

> **AI-Powered Fire Safety Insights from NASA Microgravity Combustion Data**  
> *NASA Space Apps Challenge 2026: (Challenge track: "Flame in Freefall" - track name to confirm)*

---

## Non-Operational Disclaimer

> [!CAUTION]
> **Generated from published NASA research for informational/research purposes. Not validated for operational flight or terrestrial fire safety decisions.**

---

## Core Capabilities (MVP)

1. **Ask:** Grounded Q&A over license-cleared NASA technical papers with page-level citations, explainable ranking breakdown, and an explicit refusal state on insufficient evidence.
2. **Compare:** Scientific experiment comparator running strictly over human-verified DuckDB tables, with deterministic guardrails (fuel class, geometry, flow regime, atmospheric equivalence) preventing misleading comparisons.
3. **Safety Brief:** Structured synthesis detailing findings, conditions of validity, Earth-analog differences, limitations, and mandatory safety disclaimers.

---

## Hard Scientific Rules

- **Zero Fabrication:** Every experiment name, run ID, metric value, unit, geometry, and citation originates from an inspected NASA publication with title and page number.
- **Null on Ambiguity:** Any unverified datum is stored as `NULL` and displayed as `"not verified"`.
- **No LLM Numbers in Tables:** LLMs never extract numbers into comparative tables; all quantitative comparisons query the verified database directly.
- **Licensing Discipline:** Only public domain / legally clear NASA publications enter the retrieval corpus.

---

## Repository Structure

```
combustionlens/
├── README.md                  # Setup, architecture, data provenance, disclaimer
├── config.yaml                # Generator model, tau_ce, rank weights, paths
├── requirements.txt           # Pinned Python dependencies
├── Dockerfile                 # Multi-stage Docker build (Vite + FastAPI)
├── .gitignore
│
├── docs/                      # Pre-event logs & governance
│   ├── event_status.md        # Event date, pre-event coding rules
│   ├── survey_log.md          # Every NTRS query, hit count, decision
│   ├── data_sources.md        # NTRS/PSI access notes
│   ├── diff_audit.md          # Official statement vs. plan diff
│   ├── change_log.md          # Section 0 locked plan triggers & execution notes
│   └── profiling.md           # Peak RSS, cold start memory (psutil log)
│
├── data/                      # Scientific data layer (EMPTY SLOTS FOR HUMAN)
│   ├── paper_meta.csv         # Group label, source_type, license_status
│   ├── experiments_staging.csv # Hand-curated rows with page numbers
│   ├── experiments.duckdb     # Staging table + experiments_verified view
│   ├── pdfs/                  # License-cleared papers only (.gitkeep)
│   └── index/                 # Prebuilt ChromaDB (.gitkeep)
│
├── core/                      # Algorithmic engine (Headless, no UI dependencies)
│   ├── ingest.py              # PyMuPDF chunking, page metadata
│   ├── retrieval.py           # Dense top-20, cross-encoder top-5, refusal gate
│   ├── ranking.py             # Rank score and breakdown
│   ├── evidence.py            # Tiers from paper_meta
│   ├── generate.py            # Fixed generator, cache, citation check
│   ├── numcheck.py            # Normalized number matching
│   ├── units.py               # Deterministic conversions
│   └── compare.py             # Guardrail comparator
│
├── api/                       # Thin REST API layer
│   ├── main.py                # FastAPI entry point, static frontend mount
│   ├── schemas.py             # Pydantic schemas, null preservation
│   ├── routes_ask.py          # Grounded Ask endpoint
│   ├── routes_compare.py      # Experiment compare & fetch endpoints
│   ├── routes_brief.py        # Safety Brief synthesis endpoint
│   └── routes_meta.py         # System status & corpus health endpoint
│
├── frontend/                  # React 18 + Vite + Tailwind UI
│   ├── package.json           # Pinned dependencies
│   ├── vite.config.ts         # Vite configuration with API proxy
│   ├── tsconfig.json          # TypeScript configuration
│   └── src/
│       ├── pages/             # Ask.tsx, Compare.tsx, SafetyBrief.tsx
│       ├── components/        # RefusalCard, GuardrailCard, TierBadge, RankBreakdown, etc.
│       ├── lib/api.ts         # Type-safe API client
│       └── test/              # Vitest + RTL frontend test suite
│
├── eval/                      # Evaluation & benchmarking
│   ├── questions.csv          # Human-written gold answers, dev/held-out split
│   ├── grade_sheet.csv        # Blind grading matrix
│   ├── run_eval.py            # Benchmark runner across 3 systems
│   └── results.md             # Metrics, ablation, limitations
│
├── tests/                     # Deterministic test suite
│   ├── test_units.py
│   ├── test_compare.py
│   ├── test_numcheck.py
│   ├── test_evidence.py
│   ├── test_ranking.py
│   ├── test_api.py
│   └── test_smoke.py          # 5 smoke tests
│
└── scripts/                   # Data prep and profiling utilities
    ├── build_index.py         # Ingest PDFs to ChromaDB
    ├── load_experiments.py    # CSV to DuckDB staging & verified view
    ├── validate_data.py       # Data integrity check
    └── profile_memory.py      # Peak RSS and latency profiling
```

---

## Quickstart (Local Development)

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch FastAPI Backend
```bash
uvicorn api.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 3. Launch React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to interact with CombustionLens.

---

## Running Test Suites

### Backend Unit & Integration Tests (pytest)
```bash
python -m pytest tests/ -v
```

### Frontend Component & UI Tests (Vitest)
```bash
cd frontend
npm test -- --run
```

---

## Production Docker Deployment (Hugging Face Spaces)

```bash
docker build -t combustionlens:latest .
docker run -p 7860:7860 combustionlens:latest
```
Open `http://localhost:7860`.
*(Note: Hugging Face Spaces hardware specs e.g., CPU Basic 2 vCPU, 16 GB RAM are to be re-verified before the event).*
