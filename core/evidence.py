"""CombustionLens Core: Metadata-Driven Evidence Tier Evaluator.

Evaluates evidence tiers strictly from paper_meta metadata attributes:
- research_group_label (distinct independent research group count)
- peer_reviewed ('Y' / 'N' / 'unknown')
- source_type ('flight', 'drop_tower', 'numerical', 'review', etc.)
- contradiction_flag (curated explicit flag only)

HARD RULE: Chunk counts and paper counts NEVER count as independent evidence.
NO NLP inference is used to judge independence or contradiction.
"""
from typing import List, Dict, Any, Tuple, Optional


def evaluate_evidence_tier(
    candidates: List[Dict[str, Any]],
    top_logit: Optional[float] = None,
    tau_ce: Optional[float] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """Determine evidence tier deterministically from metadata.
    
    Returns:
    - tier: 'INSUFFICIENT' | 'WEAK' | 'MODERATE' | 'STRONG' | 'CONFLICTING'
    - rationale: One-sentence explanation of the tier determination
    - details: Metadata audit details (groups, source types, peer review status)
    """
    if not candidates:
        return (
            "INSUFFICIENT",
            "No candidate sources found in corpus for this query.",
            {"distinct_groups": [], "peer_reviewed_count": 0, "contradictions": False}
        )
        
    # Check refusal gate first if calibrated tau_ce is active
    if tau_ce is not None and top_logit is not None:
        if top_logit < tau_ce:
            return (
                "INSUFFICIENT",
                f"Top cross-encoder relevance logit ({top_logit:.4f}) is below calibrated refusal threshold ({tau_ce:.4f}).",
                {"distinct_groups": [], "peer_reviewed_count": 0, "contradictions": False}
            )
            
    # Check for curated contradiction flags (Stretch tier)
    has_curated_contradiction = any(
        bool(c.get("contradiction_flag", False)) for c in candidates
    )
    if has_curated_contradiction:
        return (
            "CONFLICTING",
            "Curated literature flags indicate conflicting findings or divergent experimental trends between sources.",
            {"distinct_groups": [], "peer_reviewed_count": 0, "contradictions": True}
        )

    # Collect distinct research groups case-insensitively (excluding None / empty / unknown)
    group_map: Dict[str, str] = {}
    for c in candidates:
        grp = c.get("research_group_label")
        if grp and str(grp).strip().lower() not in ("unknown", "none", ""):
            key = str(grp).strip().lower()
            if key not in group_map:
                group_map[key] = str(grp).strip()

    distinct_groups = list(group_map.values())

    peer_reviewed_count = sum(
        1 for c in candidates if str(c.get("peer_reviewed", "")).strip().lower() in ("y", "yes", "true")
    )
    
    source_types = {
        str(c.get("source_type", "")).strip().lower() 
        for c in candidates if c.get("source_type")
    }

    details = {
        "distinct_groups": sorted(list(distinct_groups)),
        "group_count": len(distinct_groups),
        "peer_reviewed_count": peer_reviewed_count,
        "source_types": sorted(list(source_types)),
        "contradictions": has_curated_contradiction
    }

    # STRONG: 2+ distinct independent groups, no contradiction flag
    if len(distinct_groups) >= 2:
        return (
            "STRONG",
            f"Corroborated by {len(distinct_groups)} independent research groups ({', '.join(details['distinct_groups'])}) with no conflicting findings.",
            details
        )
        
    # MODERATE: Exactly one independent group with at least one peer-reviewed publication
    if len(distinct_groups) == 1 and peer_reviewed_count >= 1:
        grp_name = list(distinct_groups)[0]
        return (
            "MODERATE",
            f"Directly supported by 1 independent research group ({grp_name}) with peer-reviewed verification.",
            details
        )
        
    # WEAK: Only review/unknown sources, non-peer-reviewed data, or unverified group labels
    if source_types.issubset({"review", "unknown", ""}) or len(distinct_groups) == 0 or peer_reviewed_count == 0:
        return (
            "WEAK",
            "Evidence is preliminary, non-peer-reviewed, or supported solely by reviews/unverified sources.",
            details
        )

    # Fallback to WEAK if only single unverified group
    return (
        "WEAK",
        "Limited evidence support; conditions or group independence not fully verified.",
        details
    )
