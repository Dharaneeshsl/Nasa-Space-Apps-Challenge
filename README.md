---
title: CombustionLens
emoji: 🛰️
colorFrom: red
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🛰️ CombustionLens: AI-Powered Spacecraft Fire Safety Intelligence

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA%20Space%20Apps-Challenge%20Submission-0B3D91?style=for-the-badge&logo=nasa&logoColor=white)](https://www.spaceappschallenge.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![React 18](https://img.shields.io/badge/React-18%20%7C%20TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=black)](frontend/)
[![Tests Passing](https://img.shields.io/badge/Tests-62%20pytest%20%7C%2010%20vitest-brightgreen?style=for-the-badge)](tests/)

> **A zero-fabrication, scientifically guarded AI platform for mission safety engineers, extracting validated fire safety intelligence from NASA microgravity and spaceflight combustion data.**
> 
> *Submitted for the **NASA Space Apps Challenge**.*

---

## ⚠️ Non-Operational Flight Safety Disclaimer

> [!CAUTION]
> **CombustionLens is designed for informational and scientific research synthesis based on published NASA literature. This software is NOT validated or certified for operational spaceflight maneuvers, real-time life-support abort procedures, or terrestrial fire safety engineering decisions without independent qualified engineering review.**

---

## 🌌 The Mission: Why CombustionLens?

### The Problem in Spaceflight
Fire represents one of the most catastrophic risks aboard crewed spacecraft and planetary habitats (ISS, Artemis lunar base, Lunar Gateway, Mars transit). However, **fire in microgravity behaves completely differently than on Earth**:
- **Absence of Natural Buoyancy:** Without gravity-driven convective buoyant updrafts, hot combustion products linger around the flame, forming spherical flames starved of oxygen unless forced ventilation is present.
- **Quiescent and Low-Flow Hazards:** Materials that extinguish quickly at 1-g can sustain smoldering or creeping flame spread under low-speed crew cabin airflows ($< 5\text{ cm/s}$).
- **Dangerous Extrapolations:** Standard terrestrial flammability indices (e.g., NASA-STD-6001 upward flame spread at 1-g) often fail to predict ignition and flame spread limits in partial gravity (Moon: $0.166\text{ g}$, Mars: $0.38\text{ g}$).

### The Problem with Generic AI / LLMs
When aerospace engineers query generic commercial Large Language Models (LLMs) or naive RAG pipelines about spacecraft fire safety:
1. **Physical Hallucinations:** LLMs invent droplet burning constants ($K$), misquote oxygen index limits (LOI), and mix disparate pressures ($101.3\text{ kPa}$ vs. $70.3\text{ kPa}$ exploration atmospheres).
2. **False Generalization:** They conflate 1-g terrestrial test results with genuine orbital microgravity flight experiments (FLEX, BASS, Saffire, ACME).
3. **No Refusal Discipline:** Generic LLMs answer questions even when empirical scientific evidence does not exist in literature, posing severe safety risks.

### The CombustionLens Solution
**CombustionLens** is purpose-built to eliminate hallucination through an architecture of **uncompromising scientific discipline**:
- **Zero-Fabrication Guarantee:** LLMs are never permitted to generate or extract numerical values into comparative tables. All physical numbers query human-verified DuckDB tables curated from peer-reviewed NASA publications.
- **Calibrated Refusal Gates ($\tau_{ce}$):** If cross-encoder relevance logits fall below calibrated empirical thresholds, the system issues an explicit refusal card rather than fabricating an answer.
- **Deterministic Physical Guardrails:** The comparator rigorously prevents comparisons across mismatched fuel geometries (droplet vs. flat sheet), disparate flow regimes (quiescent vs. forced flow), or unequal gravity levels.
- **Four-Tier Evidence Classification:** Answers are explicitly labeled with empirical rigor badges based on whether findings are corroborated by independent NASA research groups.

---

## 🚀 Key Innovations & Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               User Query / Mission Topic               │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                    [Ambiguity Boundary Gate]
                                   /                         \
                       Missing Boundary                   Specific Physical
                          Conditions                          Boundary
                              │                                   │
                    ┌─────────▼──────────┐              ┌─────────▼──────────┐
                    │ Refusal / Clarify  │              │ Dense Vector Top-20│
                    │   (Ask Parameters) │              │  (all-MiniLM-L6)   │
                    └────────────────────┘              └─────────┬──────────┘
                                                                  │
                                                        [Cross-Encoder Top-5]
                                                       (ms-marco-MiniLM-L-6-v2)
                                                                  │
                                                        [Calibrated Tau Gate]
                                                       /                     \
                                                  Score < Tau            Score >= Tau
                                                       │                      │
                                            ┌──────────▼─────────┐  ┌─────────▼──────────┐
                                            │ Out-of-Scope       │  │ Grounded Synthesis │
                                            │ Refusal Card       │  │ & Sentence Number  │
                                            └────────────────────┘  │ Matching Check     │
                                                                    └─────────┬──────────┘
                                                                              │
                                                                    [Evidence Tier Engine]
                                                                    (STRONG/MODERATE/WEAK)
                                                                              │
                                                                    ┌─────────▼──────────┐
                                                                    │ Grounded Answer +  │
                                                                    │ Citations + Pages  │
                                                                    └────────────────────┘
```

---

## 🛠️ Application Modules

| Module | Purpose | Key Guardrails & Features |
| :--- | :--- | :--- |
| **🔍 Ask** | Grounded Q&A across NASA combustion publications | • Page-level citations with fallback detection<br>• Calibrated cross-encoder refusal gate ($\tau_{ce}$)<br>• Transparent rank breakdown (semantic + corroboration + prior)<br>• Number checker verifies every digit against cited chunk |
| **⚖️ Compare** | Side-by-side experimental run analysis | • Zero LLM numbers — direct DuckDB view queries<br>• Fuel class, geometry & flow regime match validation<br>• Gravity regime parity check ($1\text{-g}$ vs $\mu\text{g}$)<br>• Interactive Recharts error-bar plots with scaled uncertainty |
| **🛡️ Safety Brief** | Comprehensive spacecraft fire safety synthesis | • Structured mission briefing across multiple NASA studies<br>• Source type attribution (Drop Tower vs ISS Flight vs Terrestrial)<br>• Terrestrial-to-microgravity mappings labeled as unvalidated hypothesis<br>• Clear scope boundaries and test limits |

---

## 🔬 Scientific Evidence Hierarchy

CombustionLens grades every grounded claim against NASA's strict evidentiary hierarchy:

| Tier | Status Badge | Definition & Criteria |
| :---: | :---: | :--- |
| **Tier 1** | <span style="color:#22c55e;font-weight:bold;">🟢 STRONG</span> | Replicated and corroborated by **$\ge 2$ independent research groups** across peer-reviewed flight/drop-tower studies. |
| **Tier 2** | <span style="color:#eab308;font-weight:bold;">🟡 MODERATE</span> | Derived from a **single research group** in peer-reviewed journal or conference literature. |
| **Tier 3** | <span style="color:#f97316;font-weight:bold;">🟠 WEAK</span> | Uncorroborated NASA Contractor Report or Technical Memorandum without independent validation. |
| **Tier 4** | <span style="color:#ef4444;font-weight:bold;">⚪ INSUFFICIENT</span> | Relevance score below $\tau_{ce}$ threshold or ungrounded query; **system refuses to answer**. |

---

## 📊 NASA Combustion Research Sources

CombustionLens is designed to ingest and index authentic microgravity combustion data from:
1. **NASA Physical Sciences Informatics (PSI) System:** Microgravity combustion flight databases.
2. **NASA Technical Reports Server (NTRS):** Public-domain NASA technical memorandums, contractor reports, and mission safety summaries.
3. **Pivotal Spaceflight Experiments:**
   - **FLEX & FLEX-2** (Flame Extinguishment Experiment — ISS): Droplet burning rates and cool-flame phenomena.
   - **BASS & BASS-II** (Burning and Suppression of Solids — ISS): Solid fuel flammability in low-speed forced flows.
   - **Saffire I–VI** (Spacecraft Fire Experiment — Cygnus cargo vehicle): Large-scale spacecraft fabric and material combustion tests.
   - **ACME** (Advanced Combustion via Microgravity Experiments — CIR on ISS): Gas flammability and soot dynamics.
   - **SoFIE** (Solid Fuel Ignition and Extinction — ISS): Exploration atmosphere fire safety testing.
   - **NASA Glenn 2.2s & 5.18s Drop Towers:** Ground-based microgravity simulation runs.

---

## 💻 Tech Stack

### Backend
- **Python 3.11+ / FastAPI:** High-performance asynchronous REST API with sliding-window proxy rate limiting and SPA fallback routing.
- **DuckDB:** In-process analytical database maintaining two-pass verified experiment views (`experiments_verified`).
- **ChromaDB:** Local, embedded vector database storing dense chunk embeddings with page-level metadata.
- **Hugging Face Transformers / Sentence-Transformers:**
  - Bi-Encoder: `sentence-transformers/all-MiniLM-L6-v2` (fast semantic retrieval)
  - Cross-Encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2` (high-fidelity re-ranking and refusal gating)
- **PyMuPDF (`fitz`):** High-precision PDF text and page extraction with strict token chunking (150–250 tokens).

### Frontend
- **React 18 + Vite:** Modern, responsive single-page application.
- **TypeScript:** Strict type safety matching backend Pydantic API schemas.
- **Tailwind CSS:** Clean, dark-mode aerospace HUD design inspired by NASA mission consoles.
- **Recharts:** Scientific visualization with experimental uncertainty error bars.
- **Lucide React:** Aerospace-grade interface icons.

### Quality Assurance & Benchmarking
- **pytest:** 62 automated unit and integration tests covering units, numbers, ranking, evidence tiers, retrieval, and API security.
- **Vitest:** 10 component tests verifying null-safe UI rendering and badge behavior.
- **Evaluation Runner:** 3-way evaluation harness comparing CombustionLens vs. Naive RAG vs. Direct LLM on a blind evaluation set.

---

## ⚡ Quickstart & Local Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Dharaneeshsl/Nasa-Space-Apps-Challenge.git
cd Nasa-Space-Apps-Challenge
```

### 2. Setup Backend
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run the Full Application
```bash
# Launch FastAPI server with built React frontend mounted at root
uvicorn api.main:app --host 0.0.0.0 --port 7860
```
Open **`http://localhost:7860`** in your browser. API docs are available at `http://localhost:7860/docs`.

---

## 🧪 Running Automated Test Suites

### Backend Tests (pytest)
```bash
pytest tests/ -v
```
*Current test suite: 62 passed, 1 skipped (real corpus test skipped until human data drop).*

### Frontend Component Tests (Vitest)
```bash
cd frontend
npm test -- --run
```
*Current test suite: 10 passed across 5 test suites.*

---

## 🐳 Docker Deployment (Hugging Face Spaces)

The application is fully containerized via a multi-stage Docker build:

```bash
docker build -t combustionlens:latest .
docker run -p 7860:7860 combustionlens:latest
```
Navigate to `http://localhost:7860`.

---

## 👥 NASA Space Apps Challenge Team

- **Project Name:** CombustionLens
- **Challenge Track:** Spacecraft Fire Safety & Microgravity Combustion Intelligence
- **Repository:** [https://github.com/Dharaneeshsl/Nasa-Space-Apps-Challenge](https://github.com/Dharaneeshsl/Nasa-Space-Apps-Challenge)

---

## 📜 License & Acknowledgments

- **License:** Released under the [MIT License](LICENSE).
- **Data Acknowledgments:** Dedicated to the researchers at NASA Glenn Research Center, NASA Physical Sciences Informatics (PSI), and the international spaceflight combustion research community whose flight and drop-tower experiments make human space exploration safer.
