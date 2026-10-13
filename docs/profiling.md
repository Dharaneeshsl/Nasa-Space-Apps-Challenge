# CombustionLens: Resource & Memory Profiling Log

> **Deployment Target:** Hugging Face Spaces (Docker SDK; hardware specs e.g., 2 vCPU, 16 GB RAM to re-verify before event)

## 1. Local Peak RSS Profiling (`psutil`)

| Test Date | Environment / OS | Event / Action | Peak RSS (MB) | Cold-Start Duration (s) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-12 | Windows 11 (Python 3.14.7) | Full Stack + PyTorch Runtime (/api/ask, /api/brief) | 279.5 MB | 3.54s | Query latency: 0.03s; PyTorch + Core + FastAPI live memory |
| 2026-10-12 | Windows 11 (Python 3.14.7) | Cold-start & Query (/api/ask, /api/brief) | 116.3 MB | 0.75s | Query latency: 0.01s; Clean empty-corpus handling verified |
| 2026-10-12 | Windows 11 (Python 3.14.7) | Cold-start & Query (/api/ask, /api/brief) | 68.5 MB | 1.08s | Query latency: 0.01s; Clean empty-corpus handling verified |
| 2026-10-12 | Windows 11 (Python 3.14.7) | Cold-start & Single Query (/api/ask) | 66.3 MB | 0.72s | Query latency: 0.01s; Empty-corpus refusal state verified |

## 2. Memory Optimization Milestones
- **ChromaDB Indexing:** Pre-built index loaded from disk (zero re-embedding at startup).
- **Model Footprint:**
  - `all-MiniLM-L6-v2`: ~90 MB on-disk weights (~120 MB RAM in-memory estimate)
  - `ms-marco-MiniLM-L-6-v2`: ~90 MB on-disk weights (~120 MB RAM in-memory estimate)
  - PyTorch CPU Runtime: ~178 MB (empirically measured delta with `psutil`)
  - Full Peak RSS (FastAPI + PyTorch + App): **279.5 MB** (empirically measured)
