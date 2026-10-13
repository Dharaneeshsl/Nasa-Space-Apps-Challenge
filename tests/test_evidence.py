"""Unit tests for core/evidence.py metadata-driven evidence evaluation.

NOTE: Synthetic test fixtures live exclusively inside this test module.
"""
import pytest
from core.evidence import evaluate_evidence_tier


def test_evidence_insufficient_empty():
    tier, reason, details = evaluate_evidence_tier([])
    assert tier == "INSUFFICIENT"
    assert "No candidate sources" in reason


def test_evidence_insufficient_refusal_gate():
    synthetic_cands = [
        {"doc_id": "SYNTH_01", "research_group_label": "Group_A", "peer_reviewed": "Y"}
    ]
    # top_logit = 1.0, but tau_ce = 2.5 -> refusal gate triggers
    tier, reason, details = evaluate_evidence_tier(synthetic_cands, top_logit=1.0, tau_ce=2.5)
    assert tier == "INSUFFICIENT"
    assert "below calibrated refusal threshold" in reason


def test_evidence_strong_two_independent_groups():
    synthetic_cands = [
        {"doc_id": "SYNTH_01", "research_group_label": "NASA_Glenn", "peer_reviewed": "Y", "source_type": "flight"},
        {"doc_id": "SYNTH_02", "research_group_label": "JAXA_Combustion", "peer_reviewed": "Y", "source_type": "drop_tower"}
    ]
    tier, reason, details = evaluate_evidence_tier(synthetic_cands, top_logit=3.0, tau_ce=1.0)
    assert tier == "STRONG"
    assert details["group_count"] == 2
    assert "JAXA_Combustion" in details["distinct_groups"]
    assert "NASA_Glenn" in details["distinct_groups"]


def test_evidence_moderate_single_group_peer_reviewed():
    synthetic_cands = [
        {"doc_id": "SYNTH_01", "research_group_label": "NASA_Glenn", "peer_reviewed": "Y", "source_type": "flight"},
        {"doc_id": "SYNTH_02", "research_group_label": "NASA_Glenn", "peer_reviewed": "Y", "source_type": "flight"}
    ]
    tier, reason, details = evaluate_evidence_tier(synthetic_cands, top_logit=3.0, tau_ce=1.0)
    assert tier == "MODERATE"
    assert details["group_count"] == 1
    assert "Directly supported by 1 independent research group" in reason


def test_evidence_weak_review_only():
    synthetic_cands = [
        {"doc_id": "SYNTH_01", "research_group_label": "Unknown", "peer_reviewed": "N", "source_type": "review"}
    ]
    tier, reason, details = evaluate_evidence_tier(synthetic_cands, top_logit=3.0, tau_ce=1.0)
    assert tier == "WEAK"


def test_evidence_conflicting_curated_flag():
    synthetic_cands = [
        {"doc_id": "SYNTH_01", "research_group_label": "Group_A", "peer_reviewed": "Y", "contradiction_flag": True},
        {"doc_id": "SYNTH_02", "research_group_label": "Group_B", "peer_reviewed": "Y", "contradiction_flag": False}
    ]
    tier, reason, details = evaluate_evidence_tier(synthetic_cands, top_logit=3.0, tau_ce=1.0)
    assert tier == "CONFLICTING"
    assert details["contradictions"] is True
