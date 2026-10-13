"""Unit tests for core/ranking.py transparent multi-factor ranking.

NOTE: Synthetic test fixtures live exclusively inside this test module.
"""
import pytest
from core.ranking import (
    compute_s_corrob,
    compute_s_source,
    rank_candidates,
    load_ranking_weights,
)

SYNTHETIC_CANDIDATES = [
    {
        "doc_id": "SYNTH_DOC_001",
        "raw_logit": 3.5,
        "research_group_label": "Group_Alpha",
        "source_type": "flight",
        "contradiction_flag": False
    },
    {
        "doc_id": "SYNTH_DOC_002",
        "raw_logit": 1.5,
        "research_group_label": "Group_Beta",
        "source_type": "drop_tower",
        "contradiction_flag": False
    },
    {
        "doc_id": "SYNTH_DOC_003",
        "raw_logit": -0.5,
        "research_group_label": "Group_Alpha",
        "source_type": "numerical",
        "contradiction_flag": False
    }
]


def test_corroboration_scoring():
    # 0 groups
    assert compute_s_corrob(0) == 0.00
    # 1 group
    assert compute_s_corrob(1) == 0.33
    # 2 groups
    assert compute_s_corrob(2) == 0.67
    # 3+ groups
    assert compute_s_corrob(3) == 1.00
    assert compute_s_corrob(5) == 1.00
    # Contradiction flag deduction
    assert compute_s_corrob(2, has_contradiction=True) == 0.34  # 0.67 - 0.33
    assert compute_s_corrob(1, has_contradiction=True) == 0.00  # floor at 0.0


def test_source_prior_scoring():
    assert compute_s_source("flight") == 1.00
    assert compute_s_source("drop_tower") == 0.80
    assert compute_s_source("parabolic_flight") == 0.60
    assert compute_s_source("numerical") == 0.50
    assert compute_s_source("review") == 0.40
    assert compute_s_source("unknown") == 0.00
    assert compute_s_source(None) == 0.00


def test_rank_candidates_arithmetic():
    ranked = rank_candidates(SYNTHETIC_CANDIDATES)
    assert len(ranked) == 3
    
    top = ranked[0]
    assert top["doc_id"] == "SYNTH_DOC_001"
    
    # Check normalized s_rel for highest logit is 1.0
    bk = top["ranking"]
    assert bk["s_rel"] == 1.0
    assert bk["s_source"] == 1.00
    # Distinct groups: Group_Alpha and Group_Beta -> 2 groups -> 0.67
    assert bk["s_corrob"] == 0.67
    
    # Check arithmetic: 0.60*1.0 + 0.25*0.67 + 0.15*1.00 = 0.60 + 0.1675 + 0.15 = 0.9175
    expected_score = round(0.60 * 1.0 + 0.25 * 0.67 + 0.15 * 1.00, 4)
    assert top["rank_score"] == expected_score
    assert "S_source is an environmental representativeness prior" in bk["source_type_caveat"]


def test_rank_candidates_empty():
    assert rank_candidates([]) == []
