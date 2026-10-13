"""Unit tests for core/retrieval.py retrieval pipeline, sigmoid display score, and refusal gate.

NOTE: Synthetic test fixtures live exclusively inside this test module.
"""
import pytest
from core.retrieval import sigmoid, retrieve_candidates


def test_sigmoid_display_calculation():
    # Large positive logit -> ~1.0
    assert sigmoid(10.0) > 0.999
    # Zero logit -> 0.5 exactly
    assert abs(sigmoid(0.0) - 0.5) < 1e-6
    # Large negative logit -> ~0.0
    assert sigmoid(-10.0) < 0.001


def test_retrieve_candidates_empty_corpus(tmp_path):
    # Non-existent or empty index directory returns status 'no_corpus'
    res = retrieve_candidates("flame extinction limit", chroma_dir=str(tmp_path))
    assert res["status"] == "no_corpus"
    assert "not found" in res["refusal_reason"] or "0 documents" in res["refusal_reason"]
    assert res["candidates"] == []


def test_refusal_gate_logic_mock():
    """Verify refusal gate rejects queries when top logit < tau_ce."""
    from unittest.mock import patch, MagicMock
    
    mock_collection = MagicMock()
    mock_collection.count.return_value = 2
    mock_collection.query.return_value = {
        "documents": [["Synthetic document chunk about microgravity droplet combustion."]],
        "metadatas": [[{
            "doc_id": "SYNTH_DOC_01",
            "title": "Synthetic Droplet Study",
            "page_number": 3,
            "research_group_label": "NASA_Glenn",
            "source_type": "flight"
        }]],
        "distances": [[0.85]]
    }
    
    mock_client = MagicMock()
    mock_col_obj = MagicMock()
    mock_col_obj.name = "combustion_papers"
    mock_client.list_collections.return_value = [mock_col_obj]
    mock_client.get_collection.return_value = mock_collection
    
    # Mock cross-encoder predicting low relevance logit (-1.5)
    mock_ce = MagicMock()
    mock_ce.predict.return_value = [-1.5]
    
    with patch("chromadb.PersistentClient", return_value=mock_client), \
         patch("core.retrieval.get_embedding_model") as mock_bi, \
         patch("core.retrieval.get_cross_encoder_model", return_value=mock_ce):
         
        mock_bi.return_value.encode.return_value.tolist.return_value = [[0.1] * 384]
        
        # Test with calibrated tau_ce = 0.5 (logit -1.5 is below 0.5)
        with patch("core.retrieval.load_retrieval_config", return_value={
            "top_k_bi": 5, "top_k_ce": 2, "tau_ce": 0.5,
            "embedding_model": "dummy", "cross_encoder_model": "dummy", "chroma_dir": "data/index"
        }):
            res = retrieve_candidates("What is the extinction limit of Heptane?")
            assert res["status"] == "insufficient"
            assert "below calibrated refusal threshold" in res["refusal_reason"]
            assert res["candidates"] == []
            assert len(res["nearest_documents"]) > 0

        # Test with uncalibrated mode (tau_ce = None)
        with patch("core.retrieval.load_retrieval_config", return_value={
            "top_k_bi": 5, "top_k_ce": 2, "tau_ce": None,
            "embedding_model": "dummy", "cross_encoder_model": "dummy", "chroma_dir": "data/index"
        }):
            res = retrieve_candidates("What is the extinction limit of Heptane?")
            assert res["status"] == "answered"
            assert res["uncalibrated"] is True
            assert len(res["candidates"]) == 1
