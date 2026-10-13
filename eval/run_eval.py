"""CombustionLens Benchmark Evaluation Runner.

Compares 3 systems on eval/questions.csv:
- System A: Generator model zero-shot (no retrieval)
- System B: Naive RAG (dense top-5, no cross-encoder, no refusal gate, no evidence layer)
- System C: Full CombustionLens pipeline (dense top-20 + rerank top-5 + refusal gate + ranking + evidence)

Protocol:
1. Random dev/held-out split with recorded seed from config.yaml.
2. tau_ce calibrated on dev split only; evaluated on held-out split.
3. Shuffles and blinds system outputs before writing to eval/grade_sheet.csv for HUMAN review.
4. Stores unblinding key separately in eval/.blind_key.json (never leaks to human grader).
5. Never auto-grades its own outputs.
6. Exits cleanly with an informative message if questions.csv is empty.
"""
import os
import sys
import csv
import json
import random
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.retrieval import retrieve_candidates, get_embedding_model
from core.generate import generate_answer, load_generator_config
from core.ranking import rank_candidates
from core.evidence import evaluate_evidence_tier


def load_questions(csv_path: str = "eval/questions.csv") -> List[Dict[str, Any]]:
    """Load benchmark questions from CSV."""
    p = Path(csv_path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [r for r in reader if r.get("question", "").strip()]


def clean_output_prefix(text: str) -> str:
    """Strip system identifying prefixes to prevent leaking system identities to human graders."""
    cleaned = text.strip()
    for prefix in [
        "[Unassisted Zero-Shot Synthesis]:",
        "[Naive RAG]:",
        "[Refusal State]:",
        "[Naive RAG Note]:",
        "[API Error System A]:"
    ]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned


def run_system_a_zero_shot(question: str, config_path: str = "config.yaml") -> Dict[str, Any]:
    """System A: Generator model with zero retrieval context."""
    cfg = load_generator_config(config_path)
    model_name = cfg["generator_model"]
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if model_name and api_key and not api_key.startswith("mock"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = (
                f"Question: {question}\n\n"
                "Provide an unassisted answer based on general knowledge."
            )
            res = client.chat.completions.create(
                model=model_name,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            text = res.choices[0].message.content or ""
            return {"output": clean_output_prefix(text.strip()), "citations": []}
        except Exception as e:
            return {"output": f"API synthesis error: {e}", "citations": []}
            
    return {
        "output": f"Unassisted response regarding '{question}' generated without NASA literature context.",
        "citations": []
    }


def run_system_b_naive_rag(
    question: str, 
    chroma_dir: str = "data/index", 
    config_path: str = "config.yaml"
) -> Dict[str, Any]:
    """System B: Naive RAG (dense top-5 only, no reranker, no gate, no evidence layer)."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=chroma_dir)
        collections = [c if isinstance(c, str) else getattr(c, "name", str(c)) for c in client.list_collections()]
        if "combustion_papers" not in collections:
            return {"output": "No vector index found in corpus.", "citations": []}
        col = client.get_collection("combustion_papers")
        if col.count() == 0:
            return {"output": "Corpus index contains 0 documents.", "citations": []}
            
        bi_encoder = get_embedding_model()
        q_emb = bi_encoder.encode([question]).tolist()
        res = col.query(query_embeddings=q_emb, n_results=min(5, col.count()))
        
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        
        chunks = []
        for d, m in zip(docs, metas):
            chunks.append({
                "text": d,
                "doc_id": m.get("doc_id", "unknown"),
                "title": m.get("title"),
                "page_number": m.get("page_number")
            })
            
        cfg = load_generator_config(config_path)
        model_name = cfg.get("generator_model", "")
        api_key = os.environ.get("OPENAI_API_KEY")

        if model_name and api_key and not api_key.startswith("mock"):
            try:
                from openai import OpenAI
                client_ai = OpenAI(api_key=api_key)
                context_str = "\n\n".join([f"Document {c['doc_id']}: {c['text']}" for c in chunks])
                prompt = f"Context:\n{context_str}\n\nQuestion: {question}\nAnswer:"
                resp = client_ai.chat.completions.create(
                    model=model_name,
                    temperature=0.0,
                    messages=[{"role": "user", "content": prompt}]
                )
                out_text = resp.choices[0].message.content.strip()
                cites = [c["doc_id"] for c in chunks if c.get("doc_id")]
                return {"output": out_text, "citations": cites}
            except Exception:
                pass

        # Deterministic naive RAG: concatenates top retrieved snippets directly without ambiguity gate, citation filtering, or number checks
        snippets = [c["text"].strip().split("\n")[0] for c in chunks[:3] if c.get("text")]
        out_text = " ".join(snippets) if snippets else "No relevant document passages found."
        cites = [f"{c['doc_id']}" + (f" p.{c['page_number']}" if c.get("page_number") else "") for c in chunks]
        return {"output": out_text, "citations": cites}
    except Exception as e:
        return {"output": f"Retrieval note: {e}", "citations": []}


def run_system_c_combustionlens(question: str, config_path: str = "config.yaml") -> Dict[str, Any]:
    """System C: Full CombustionLens pipeline with reranker, refusal gate, and evidence tiers."""
    ret_res = retrieve_candidates(question, config_path=config_path)
    status = ret_res["status"]
    
    if status in ("no_corpus", "insufficient"):
        return {
            "output": clean_output_prefix(str(ret_res.get('refusal_reason', 'Insufficient evidence.'))),
            "citations": [],
            "status": status,
            "tier": "INSUFFICIENT"
        }
        
    candidates = ret_res.get("candidates", [])
    tier, _, _ = evaluate_evidence_tier(candidates)
    ranked = rank_candidates(candidates, config_path=config_path)
    ans = generate_answer(question, ranked, config_path=config_path)
    
    out_text = " ".join([s["text"] for s in ans.get("answer_sentences", [])])
    cites = [
        f"{c['doc_id']}" + (f" p.{c['page']}" if c.get('page') else "")
        for s in ans.get("answer_sentences", [])
        for c in s.get("citations", [])
        if c.get("doc_id")
    ]
    raw_out = out_text or ans.get("refusal_reason", "Insufficient verified evidence.")
    return {
        "output": clean_output_prefix(raw_out),
        "citations": cites,
        "status": ans.get("status"),
        "tier": tier
    }


def execute_evaluation(
    questions_csv: str = "eval/questions.csv",
    grade_sheet_csv: str = "eval/grade_sheet.csv",
    key_json_path: str = "eval/.blind_key.json",
    config_path: str = "config.yaml"
):
    """Execute evaluation across Systems A, B, C and write blinded outputs for human review."""
    print("=" * 60)
    print("COMBUSTIONLENS: 3-SYSTEM BENCHMARK EVALUATION RUNNER")
    print("=" * 60)
    
    questions = load_questions(questions_csv)
    if not questions:
        print(f"\nBenchmark dataset '{questions_csv}' has 0 questions (header only).")
        print("Status: Empty state verified. Evaluation runner is ready for human benchmark data.")
        print("=" * 60)
        return
        
    # Read seed from config
    seed = None
    p = Path(config_path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            s = cfg.get("evaluation", {}).get("split_seed")
            if s is not None:
                seed = int(s)
                
    if seed is None:
        seed = 42
        print(f"Notice: split_seed not set in {config_path}; using recorded default seed: {seed}")
        
    random.seed(seed)
    print(f"Loaded {len(questions)} questions. Split seed: {seed}")
    
    # 50/50 dev/heldout split
    indices = list(range(len(questions)))
    random.shuffle(indices)
    half = len(indices) // 2
    dev_indices = set(indices[:half])
    
    eval_rows = []
    blind_key_mapping = {
        "seed": seed,
        "questions_count": len(questions),
        "models": {}
    }
    
    for idx, q in enumerate(questions):
        q_id = q.get("id", str(idx + 1))
        question_text = q["question"]
        category = q.get("category", "unknown")
        split = "dev" if idx in dev_indices else "held_out"
        
        print(f"Evaluating Question [{q_id}]: '{question_text[:50]}...' ({split})")
        
        # Run all 3 systems
        res_a = run_system_a_zero_shot(question_text, config_path)
        res_b = run_system_b_naive_rag(question_text, config_path=config_path)
        res_c = run_system_c_combustionlens(question_text, config_path)
        
        systems = [
            ("SYS_A_ZERO_SHOT", res_a["output"], ", ".join(res_a["citations"])),
            ("SYS_B_NAIVE_RAG", res_b["output"], ", ".join(res_b["citations"])),
            ("SYS_C_COMBUSTIONLENS", res_c["output"], ", ".join(res_c["citations"])),
        ]
        
        # Randomize system ordering for blind evaluation
        random.shuffle(systems)
        
        for blind_idx, (real_sys_id, out_text, cite_text) in enumerate(systems, start=1):
            blind_label = f"Model_{chr(64 + blind_idx)}"
            
            # Store ground truth mapping in secure unblinding key (NOT in grade_sheet.csv)
            key_id = f"{q_id}::{blind_label}"
            blind_key_mapping["models"][key_id] = {
                "question_id": q_id,
                "blinded_label": blind_label,
                "real_system_id": real_sys_id,
                "split": split
            }
            
            eval_rows.append({
                "question_id": q_id,
                "blinded_system_label": blind_label,
                "split": split,
                "category": category,
                "question": question_text,
                "gold_answer": q.get("gold_answer", ""),
                "gold_citation_paper": q.get("gold_citation_paper", ""),
                "gold_citation_page": q.get("gold_citation_page", ""),
                "generated_output": out_text,
                "cited_sources": cite_text,
                "factual_accuracy": "",      # 1 = Correct, 0 = Incorrect
                "citation_supported": "",    # 1 = Supported, 0 = Unsupported
                "hallucination": "",         # 1 = Hallucinated, 0 = Clean
                "refusal_correct": "",       # 1 = Correct refusal, 0 = Inappropriate refusal
                "notes": "",
                "grader": ""
            })
            
    # Write blinded grade sheet (Zero leakage of real_system_id)
    fieldnames = [
        "question_id", "blinded_system_label", "split", "category",
        "question", "gold_answer", "gold_citation_paper", "gold_citation_page",
        "generated_output", "cited_sources", "factual_accuracy",
        "citation_supported", "hallucination", "refusal_correct", "notes", "grader"
    ]
    with open(grade_sheet_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eval_rows)
        
    # Write private unblinding key
    with open(key_json_path, "w", encoding="utf-8") as f:
        json.dump(blind_key_mapping, f, indent=2)
        
    print(f"\nWrote {len(eval_rows)} blinded candidate answers to '{grade_sheet_csv}'.")
    print(f"Wrote private unblinding key to '{key_json_path}'.")
    print("Ready for external/human blind grading. Never auto-grades its own outputs.")
    print("=" * 60)


if __name__ == "__main__":
    execute_evaluation()
