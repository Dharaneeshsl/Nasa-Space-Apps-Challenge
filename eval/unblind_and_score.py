"""Script: Unblind and Score Human Evaluation Results.

Reads:
- eval/grade_sheet.csv (human-graded matrix)
- eval/.blind_key.json (private unblinding mapping)

Computes:
- Split separation: scores dev and held-out splits independently
- Factual Accuracy (%)
- Citation Support Rate (%)
- Hallucination Rate (%)
- Appropriate Refusal Rate (%) on refusal-expected questions
- Deficit detection: Identifies where CombustionLens lost to Naive RAG.
- Generates/updates eval/results.md with empirical benchmark scores.
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Any


def unblind_and_score(
    grade_sheet_path: str = "eval/grade_sheet.csv",
    blind_key_path: str = "eval/.blind_key.json",
    results_md_path: str = "eval/results.md"
):
    print("=" * 60)
    print("COMBUSTIONLENS: UNBLINDING AND BENCHMARK RESULTS AGGREGATOR")
    print("=" * 60)
    
    if not Path(grade_sheet_path).exists():
        print(f"Grade sheet '{grade_sheet_path}' not found.")
        return
        
    if not Path(blind_key_path).exists():
        print(f"Unblinding key '{blind_key_path}' not found. Cannot unblind systems.")
        return
        
    with open(blind_key_path, "r", encoding="utf-8") as f:
        key_data = json.load(f)
    model_map = key_data.get("models", {})
    
    with open(grade_sheet_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    graded_rows = [r for r in rows if r.get("factual_accuracy", "").strip() != ""]
    if not graded_rows:
        print(f"No completed grades found in '{grade_sheet_path}'.")
        print("Status: Awaiting human grader completion of grade_sheet.csv.")
        print("=" * 60)
        return
        
    print(f"Found {len(graded_rows)} human-evaluated ratings. Unblinding across splits...")
    
    # Systems: SYS_A_ZERO_SHOT, SYS_B_NAIVE_RAG, SYS_C_COMBUSTIONLENS
    def create_metric_bucket():
        return {
            "total": 0,
            "fact_ok": 0,
            "cite_ok": 0,
            "cite_total": 0,
            "hallucinated": 0,
            "refusal_needed": 0,
            "refusal_ok": 0
        }

    splits = ["dev", "held_out", "overall"]
    systems = ["SYS_A_ZERO_SHOT", "SYS_B_NAIVE_RAG", "SYS_C_COMBUSTIONLENS"]
    metrics: Dict[str, Dict[str, Dict[str, int]]] = {
        s: {sys_id: create_metric_bucket() for sys_id in systems}
        for s in splits
    }
    
    # Track per-question scores for deficit analysis
    q_sys_scores = {}

    for r in graded_rows:
        q_id = r["question_id"]
        label = r["blinded_system_label"]
        key_id = f"{q_id}::{label}"
        
        info = model_map.get(key_id)
        if not info:
            continue
            
        real_sys = info["real_system_id"]
        split = info.get("split", "dev").lower()
        if split not in ("dev", "held_out"):
            split = "dev"
            
        if real_sys not in systems:
            continue

        cat = r.get("category", "").strip().lower()
        is_refusal_question = cat in ("out_of_scope", "refusal", "unanswerable")

        # Accumulate in specific split and overall
        for current_split in (split, "overall"):
            m = metrics[current_split][real_sys]
            m["total"] += 1
            
            if r.get("factual_accuracy", "").strip() == "1":
                m["fact_ok"] += 1
            if r.get("citation_supported", "").strip() == "1":
                m["cite_ok"] += 1
            if r.get("citation_supported", "").strip() in ("0", "1"):
                m["cite_total"] += 1
            if r.get("hallucination", "").strip() == "1":
                m["hallucinated"] += 1
            if is_refusal_question:
                m["refusal_needed"] += 1
                if r.get("refusal_correct", "").strip() == "1":
                    m["refusal_ok"] += 1

        if q_id not in q_sys_scores:
            q_sys_scores[q_id] = {}
        q_sys_scores[q_id][real_sys] = {
            "fact": r.get("factual_accuracy", "").strip() == "1",
            "hallucination": r.get("hallucination", "").strip() == "1"
        }

    # Print summary
    print("\nUNBLINDED BENCHMARK RESULTS:")
    print("-" * 60)
    for s in ["dev", "held_out", "overall"]:
        print(f"\n--- SPLIT: {s.upper()} ---")
        for sys_id in systems:
            m = metrics[s][sys_id]
            tot = m["total"]
            if tot == 0:
                print(f"[{sys_id}]: No graded evaluations.")
                continue
            fact_pct = (m["fact_ok"] / tot) * 100
            cite_pct = (m["cite_ok"] / m["cite_total"]) * 100 if m["cite_total"] > 0 else 0.0
            hall_pct = (m["hallucinated"] / tot) * 100
            ref_pct = (m["refusal_ok"] / m["refusal_needed"]) * 100 if m["refusal_needed"] > 0 else 0.0
            print(f"[{sys_id}]:")
            print(f"  Factual Accuracy:        {fact_pct:.1f}% ({m['fact_ok']}/{tot})")
            print(f"  Citation Support Rate:   {cite_pct:.1f}% ({m['cite_ok']}/{m['cite_total']})")
            print(f"  Hallucination Rate:      {hall_pct:.1f}% ({m['hallucinated']}/{tot})")
            print(f"  Appropriate Refusal:     {ref_pct:.1f}% ({m['refusal_ok']}/{m['refusal_needed']})")

    # Deficit analysis: where CombustionLens (C) lost to Naive RAG (B)
    deficits = []
    for q_id, s_map in q_sys_scores.items():
        if "SYS_B_NAIVE_RAG" in s_map and "SYS_C_COMBUSTIONLENS" in s_map:
            b_fact = s_map["SYS_B_NAIVE_RAG"]["fact"]
            c_fact = s_map["SYS_C_COMBUSTIONLENS"]["fact"]
            if b_fact and not c_fact:
                deficits.append(q_id)

    # Format Markdown report and write results.md
    md_lines = [
        "# CombustionLens Benchmark Evaluation Results",
        "",
        "Empirical human-graded evaluation comparing three systems across the NASA combustion benchmark.",
        "",
        "## Summary Table (Held-Out Split)",
        "",
        "| Metric | System A (Zero-Shot) | System B (Naive RAG) | System C (CombustionLens) |",
        "|---|---|---|---|",
    ]

    h_m = metrics["held_out"]
    def get_pct(m, key, denom_key="total"):
        d = m[denom_key]
        return f"{(m[key] / d) * 100:.1f}%" if d > 0 else "N/A"

    md_lines.append(f"| Factual Accuracy | {get_pct(h_m['SYS_A_ZERO_SHOT'], 'fact_ok')} | {get_pct(h_m['SYS_B_NAIVE_RAG'], 'fact_ok')} | {get_pct(h_m['SYS_C_COMBUSTIONLENS'], 'fact_ok')} |")
    md_lines.append(f"| Citation Support Rate | {get_pct(h_m['SYS_A_ZERO_SHOT'], 'cite_ok', 'cite_total')} | {get_pct(h_m['SYS_B_NAIVE_RAG'], 'cite_ok', 'cite_total')} | {get_pct(h_m['SYS_C_COMBUSTIONLENS'], 'cite_ok', 'cite_total')} |")
    md_lines.append(f"| Hallucination Rate | {get_pct(h_m['SYS_A_ZERO_SHOT'], 'hallucinated')} | {get_pct(h_m['SYS_B_NAIVE_RAG'], 'hallucinated')} | {get_pct(h_m['SYS_C_COMBUSTIONLENS'], 'hallucinated')} |")
    md_lines.append(f"| Appropriate Refusal Rate | {get_pct(h_m['SYS_A_ZERO_SHOT'], 'refusal_ok', 'refusal_needed')} | {get_pct(h_m['SYS_B_NAIVE_RAG'], 'refusal_ok', 'refusal_needed')} | {get_pct(h_m['SYS_C_COMBUSTIONLENS'], 'refusal_ok', 'refusal_needed')} |")

    md_lines.extend([
        "",
        "## Ablation & Deficit Detection",
        "",
        f"- **Questions where Naive RAG outperformed CombustionLens:** {len(deficits)}",
    ])
    if deficits:
        for d in deficits:
            md_lines.append(f"  - `{d}`: System C refused or missed fact where System B succeeded.")
    else:
        md_lines.append("  - None observed in current grading batch.")

    md_lines.extend([
        "",
        "## Evaluation Limitations & Scientific Honesty",
        "",
        "1. **Sample Size:** Benchmark evaluation is conducted on a targeted initial test suite; statistical significance requires expanding the question bank across further mission profiles.",
        "2. **Outside Graders:** Benchmark responses require independent external domain expert grading to eliminate team evaluation bias.",
        "3. **Weight Calibration:** Ranking weights (relevance, corroboration, source prior) are heuristic baseline values pending empirical grid optimization.",
        "4. **Non-Operational Scope:** Results are empirical research benchmarks and do not constitute certification for operational spacecraft fire safety.",
        "",
        "## Mandatory Governance Note",
        "",
        "> Benchmark answers were graded blind; system IDs were unblinded deterministically via `eval/.blind_key.json`.",
        "> Generated from published NASA research for informational/research purposes. Not validated for operational flight or terrestrial fire safety decisions.",
        ""
    ])

    Path(results_md_path).write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nWritten empirical results to '{results_md_path}'.")
    print("=" * 60)


if __name__ == "__main__":
    unblind_and_score()
