"""CombustionLens Core: Transparent Multi-Factor Ranking Engine.

Formula (fixed baseline weights from config.yaml):
Rank = w_rel * s_rel + w_corrob * S_corrob + w_source * S_source
- s_rel: min-max normalized reranker raw logit across top-5
- S_corrob: based on distinct research_group_label count (with penalty for contradiction)
- S_source: environmental representativeness context prior (flight=1.0, drop_tower=0.8, etc.)

NOTE: Returns full arithmetic breakdown. S_source is explicitly annotated as
a context prior, not a scientific truth ranking.
"""
from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path

SOURCE_PRIOR_SCORES = {
    "flight": 1.00,
    "drop_tower": 0.80,
    "parabolic_flight": 0.60,
    "numerical": 0.50,
    "review": 0.40,
    "unknown": 0.00
}


def load_ranking_weights(config_path: str = "config.yaml") -> Dict[str, float]:
    """Load ranking weights from config.yaml or return unvalidated defaults."""
    default_weights = {"rel": 0.60, "corrob": 0.25, "source": 0.15}
    p = Path(config_path)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                rw = cfg.get("ranking_weights", {})
                return {
                    "rel": float(rw.get("rel", default_weights["rel"])),
                    "corrob": float(rw.get("corrob", default_weights["corrob"])),
                    "source": float(rw.get("source", default_weights["source"])),
                }
        except Exception:
            return default_weights
    return default_weights


def compute_s_corrob(distinct_group_count: int, has_contradiction: bool = False) -> float:
    """Compute corroboration score from count of distinct independent research groups."""
    if distinct_group_count <= 0:
        base = 0.00
    elif distinct_group_count == 1:
        base = 0.33
    elif distinct_group_count == 2:
        base = 0.67
    else:  # 3 or more
        base = 1.00
        
    if has_contradiction:
        base = max(0.00, base - 0.33)
    return round(base, 2)


def compute_s_source(source_type: Optional[str]) -> float:
    """Compute context prior score for environmental representativeness."""
    if not source_type:
        return 0.00
    st = str(source_type).strip().lower()
    return SOURCE_PRIOR_SCORES.get(st, 0.00)


def rank_candidates(
    candidates: List[Dict[str, Any]], 
    config_path: str = "config.yaml"
) -> List[Dict[str, Any]]:
    """Rank retrieved candidates using normalized relevance, corroboration, and source prior.
    
    Each candidate should have:
    - 'doc_id': str
    - 'raw_logit': float
    - 'research_group_label': Optional[str]
    - 'source_type': Optional[str]
    - 'contradiction_flag': Optional[bool]
    
    Returns candidates sorted descending by 'rank_score', with full arithmetic breakdown.
    """
    if not candidates:
        return []
        
    weights = load_ranking_weights(config_path)
    w_rel = weights["rel"]
    w_corrob = weights["corrob"]
    w_source = weights["source"]
    
    # 1. Min-max normalize raw logits across this candidate set (top-5)
    logits = [float(c.get("raw_logit", 0.0)) for c in candidates]
    min_logit = min(logits)
    max_logit = max(logits)
    span = max_logit - min_logit
    
    # Count distinct independent research groups supporting the query context
    valid_groups = {
        str(c.get("research_group_label")).strip().lower()
        for c in candidates
        if c.get("research_group_label") and str(c.get("research_group_label")).strip().lower() != "unknown"
    }
    distinct_group_count = len(valid_groups)
    
    scored_candidates = []
    for c in candidates:
        raw_l = float(c.get("raw_logit", 0.0))
        
        # Min-max normalization (0 to 1)
        if span > 1e-6:
            s_rel = (raw_l - min_logit) / span
        else:
            s_rel = 1.0  # Equal score if all logits identical
        s_rel = round(s_rel, 4)
        
        has_contra = bool(c.get("contradiction_flag", False))
        s_corrob = compute_s_corrob(distinct_group_count, has_contra)
        s_source = compute_s_source(c.get("source_type"))
        
        # Composite arithmetic
        composite_rank = (w_rel * s_rel) + (w_corrob * s_corrob) + (w_source * s_source)
        composite_rank = round(composite_rank, 4)
        
        breakdown = {
            "doc_id": c.get("doc_id"),
            "raw_logit": raw_l,
            "s_rel": s_rel,
            "s_corrob": s_corrob,
            "s_source": s_source,
            "weights": {"w_rel": w_rel, "w_corrob": w_corrob, "w_source": w_source},
            "rank_score": composite_rank,
            "distinct_groups_count": distinct_group_count,
            "has_contradiction": has_contra,
            "arithmetic_formula": (
                f"{w_rel}*{s_rel} + {w_corrob}*{s_corrob} + {w_source}*{s_source} = {composite_rank}"
            ),
            "source_type_caveat": (
                "S_source is an environmental representativeness prior (flight vs drop tower vs lab), "
                "not a scientific truth rating."
            )
        }
        
        out_cand = dict(c)
        out_cand["ranking"] = breakdown
        out_cand["rank_score"] = composite_rank
        scored_candidates.append(out_cand)
        
    scored_candidates.sort(key=lambda x: x["rank_score"], reverse=True)
    return scored_candidates
