# CombustionLens: Change Log & Project Governance

> **Change Control Rule (Section 0):**  
> This plan is locked. Changes are allowed only when one of the five triggers fires:
> 1. Official challenge statement differs from assumptions (apply decision rules in Section 1.2).
> 2. Gate P1 or P2 fails (drop to Fallback or Floor data tier).
> 3. Event checkpoint E1 (Hour 8) shows too few verified rows (switch demo plan per Section 4.2).
> 4. Demo pair fails verification (substitute the best verified pair).
> 5. Event date or pre-event coding rules turn out different (adjust calendar, not scope).

---

## 1. Trigger Log

| Date | Trigger | What Changed | Rationale / Approver |
| :--- | :--- | :--- | :--- |
| 2026-10-12 | Plan Locked | Initial lock of `CombustionLens_FINAL_PLAN.md` | Baseline locked for pre-event survey |
| 2026-10-12 | Tech Stack Lock | User-directed change: Streamlit replaced by React + FastAPI (Hugging Face Spaces Docker SDK) | Decouple UI state entirely from core logic, enable custom Recharts error bar viz, headless core testing with pytest/Vitest |
| 2026-10-12 | Scientific Guardrail Extension | Added explicit metric_name and gravity_level equality checks to comparator; unverified pressure set to failure; O2 basis harmonized | Prevents comparing burning rate with spread rate or 1-g with microgravity; guarantees physically sound comparisons |
| 2026-10-13 | Robustness & Integration Hardening | Implemented SPA fallback in FastAPI for React Router deep links (/compare, /brief); reverse-proxy X-Forwarded-For rate limiting with periodic memory pruning; regex word-boundary ambiguity matching; generation_mode tracking ('llm' vs 'deterministic_fallback'); created un-mocked synthetic end-to-end pipeline test (`tests/test_e2e_synthetic.py`); added `.env.example`. | Passed 55/55 active pytest tests and 9/9 Vitest frontend tests; clean frontend production build. |
| 2026-10-13 | Reviewer Remediation & Safety Integrity Pass | Resolved Items 1-16: Added path traversal guard in `serve_spa` (404 for unmapped extensions/escapes); added `skip_ambiguity_check` to `generate_answer` for Safety Brief multi-study topic synthesis; narrowed rate-question ambiguity keywords; fixed `calibrate_tau.py` ambiguity handling and comment retention; scoped evidence tier calculation strictly to cited candidates in generated answer; labeled brief Earth-analog extrapolation as unvalidated hypothesis and renamed source types; added physical metric unit equivalence & inert diluent check in comparator; stopped defaulting missing page/title in retrieval; lowered chunking size to 150-250 tokens for `all-MiniLM-L6-v2`; guarded loader against ragged CSV rows and enforced case-insensitive verification view (`lower(trim(verified_by)) <> lower(trim(curated_by))`); stripped guardrails from System B naive RAG baseline in `run_eval.py`; overhauled `unblind_and_score.py` for dev/held-out split evaluation and deficit analysis. | Passed 62/62 active pytest tests (1 skipped real-corpus test) and 10/10 Vitest frontend tests; 0 errors on clean `npm run build`. |

---

## 2. Execution Notes
- **Staged Delivery:** 4-stage sequential implementation with strict testing and review stops.
- **Data Target:** Target 10 verified rows by Oct 20 for Gate P1/P2 feasibility.
- **Blind Evaluation:** Enforce at least one outside blind grader for at least 10 benchmark answers.
- **Demo Polish:** Budget ~10% of event time specifically for demo video and presentation polish.
- **Explicit Refusal Rationale:** Every refusal state must emit a clear, one-sentence "why we refused" reason.
- **Demo Rehearsal:** Prepare and rehearse two demo scripts (passing pair vs. guardrail failure).
- **Ablation Honesty:** Explicitly list in `eval/results.md` where the full system lost to naive RAG.

---

## 3. Parking Lot (DO NOT IMPLEMENT)
*Ideas deferred or prohibited from hackathon MVP to prevent scope creep:*
- Provenance view with raw PDF source passage viewer.
- Query suggestions / autocomplete in Ask search.
- PDF export of the Safety Brief.
- Interactive physical coverage / experimental parameter gap map.
