"""Script: Calibrate Cross-Encoder Refusal Threshold (tau_ce).

HARD RULES:
1. Calibrates tau_ce strictly on the dev split of eval/questions.csv.
2. Never tunes tau_ce on the held-out evaluation partition.
3. Automatically updates config.yaml using regex to preserve comments.
4. Distinguishes answerable vs refusal questions by category and gold_answer.
5. Handles empty dataset gracefully without crashing.
"""
import os
import sys
import csv
import re
import yaml
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.retrieval import retrieve_candidates, get_cross_encoder_model
import chromadb


def load_dev_questions(
    questions_csv: str = "eval/questions.csv", 
    config_path: str = "config.yaml"
) -> List[Dict[str, Any]]:
    """Load benchmark questions from CSV and partition into dev split using config seed."""
    p = Path(questions_csv)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        questions = [r for r in reader if r.get("question", "").strip()]
        
    if not questions:
        return []
        
    # Read seed
    seed = 42
    if Path(config_path).exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                s = cfg.get("evaluation", {}).get("split_seed")
                if s is not None:
                    seed = int(s)
        except Exception:
            pass
                
    random.seed(seed)
    indices = list(range(len(questions)))
    random.shuffle(indices)
    dev_count = max(1, len(questions) // 2)
    dev_indices = set(indices[:dev_count])
    
    return [q for idx, q in enumerate(questions) if idx in dev_indices]


def calibrate_threshold(
    questions_csv: str = "eval/questions.csv",
    config_path: str = "config.yaml",
    chroma_dir: str = "data/index"
) -> Tuple[float, Dict[str, Any]]:
    """Calibrate optimal tau_ce on dev questions."""
    print("=" * 60)
    print("COMBUSTIONLENS: CROSS-ENCODER REFUSAL GATE CALIBRATION")
    print("=" * 60)
    
    dev_questions = load_dev_questions(questions_csv, config_path)
    if not dev_questions:
        print(f"Empty dev split in '{questions_csv}'.")
        print("Status: Empty state verified. Ready for human benchmark questions.")
        print("=" * 60)
        return 0.0, {}
        
    # Check if vector index exists
    try:
        client = chromadb.PersistentClient(path=chroma_dir)
        collections = [c if isinstance(c, str) else getattr(c, "name", str(c)) for c in client.list_collections()]
        if "combustion_papers" not in collections:
            print(f"Vector index 'combustion_papers' not found in '{chroma_dir}'.")
            return 0.0, {}
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
        return 0.0, {}
        
    print(f"Calibrating over {len(dev_questions)} dev questions...")
    ce_model = get_cross_encoder_model()
    
    # Collect query top logits and label (1 = answerable, 0 = refusal/out-of-scope)
    samples = []
    for q in dev_questions:
        q_text = q["question"]
        cat = q.get("category", "").strip().lower()
        
        # Ambiguous questions are handled upstream by boundary conditions;
        # Comparative questions evaluate structured DuckDB tables, not text retrieval.
        if cat in ("ambiguous", "needs_clarification", "comparative"):
            continue
            
        if cat in ("refusal", "out_of_scope", "unanswerable", "negative"):
            label = 0
        elif cat in ("factual", "operational", "terrestrial", "in_domain", "answerable", "positive"):
            label = 1
        else:
            # Fall back to whether gold_answer is present
            label = 1 if bool(q.get("gold_answer", "").strip()) else 0
        
        # Dense retrieval
        ret = retrieve_candidates(q_text, config_path=config_path, chroma_dir=chroma_dir)
        top_logit = ret.get("top_logit")
        if top_logit is not None:
            samples.append((top_logit, label))
            
    if not samples:
        print("No valid retrieval candidates to evaluate. Keeping tau_ce uncalibrated.")
        return 0.0, {}
        
    # Search threshold grid from -5.0 to +10.0 in steps of 0.1
    best_tau = 0.0
    best_score = -1.0
    
    thresholds = [round(-5.0 + i * 0.1, 2) for i in range(151)]
    for tau in thresholds:
        tp, fp, fn, tn = 0, 0, 0, 0
        for logit, label in samples:
            pred = 1 if logit >= tau else 0
            if pred == 1 and label == 1:
                tp += 1
            elif pred == 1 and label == 0:
                fp += 1
            elif pred == 0 and label == 1:
                fn += 1
            elif pred == 0 and label == 0:
                tn += 1
                
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        # Refusal specificity (TN rate)
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        # Balanced score: harmonic mean between answerable accuracy and refusal specificity
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        score = 0.6 * f1 + 0.4 * specificity
        
        if score > best_score:
            best_score = score
            best_tau = tau
            
    print(f"Calibration Complete: Optimal tau_ce = {best_tau:.2f} (Dev Balanced Score = {best_score:.3f})")
    
    # Update config.yaml using regex to preserve all comments
    if Path(config_path).exists():
        content = Path(config_path).read_text(encoding="utf-8")
        if re.search(r'tau_ce:\s*.*', content):
            new_content = re.sub(
                r'([ \t]*tau_ce:[ \t]*)(?:null|none|[0-9.\-]+)?([ \t]*(?:#.*)?)$',
                rf'\g<1>{best_tau:.2f}\2',
                content,
                flags=re.MULTILINE
            )
            Path(config_path).write_text(new_content, encoding="utf-8")
            print(f"Updated '{config_path}' with retrieval.tau_ce = {best_tau:.2f} (comments preserved).")
        
    print("=" * 60)
    return best_tau, {"score": best_score, "samples_count": len(samples)}


if __name__ == "__main__":
    calibrate_threshold()
