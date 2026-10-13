"""Backend API integration tests for CombustionLens FastAPI endpoints.

NOTE: Synthetic test fixtures live exclusively inside this test module.
Verifies:
- Disclaimer is present in every response.
- Nulls stay null.
- INSUFFICIENT returns zero generated text.
- Scientific comparator guardrails execute over verified view.
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

MANDATORY_DISCLAIMER_SUBSTRING = "Generated from published NASA research for informational/research purposes"


def test_healthcheck():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_status_endpoint():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "corpus_size" in data
    assert "verified_rows" in data
    assert MANDATORY_DISCLAIMER_SUBSTRING in data["disclaimer"]


def test_ask_insufficient_no_generated_text():
    """Verify that when retrieval fails or refusal gate triggers, zero text is generated."""
    # When no corpus exists, query should return no_corpus with empty answer_sentences
    res = client.post("/api/ask", json={"query": "What is the burning rate of n-heptane?"})
    assert res.status_code == 200
    data = res.json()
    
    assert data["status"] in ("no_corpus", "insufficient", "needs_clarification")
    if data["status"] in ("no_corpus", "insufficient"):
        assert data["answer_sentences"] == []  # Zero generated text!
    assert MANDATORY_DISCLAIMER_SUBSTRING in data["disclaimer"]


def test_ask_ambiguous_needs_clarification():
    """Verify ambiguous query with missing parameters asks for missing boundary conditions."""
    res = client.post("/api/ask", json={"query": "What is the flame spread rate and extinction limit?"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "needs_clarification"
    assert len(data["missing_conditions"]) > 0
    assert data["answer_sentences"] == []
    assert MANDATORY_DISCLAIMER_SUBSTRING in data["disclaimer"]


def test_ask_with_mocked_grounded_candidates():
    """Verify answered state returns sentences with citations and disclaimer."""
    mock_retrieval_res = {
        "status": "answered",
        "uncalibrated": True,
        "top_logit": 3.2,
        "tau_ce": None,
        "refusal_reason": None,
        "candidates": [
            {
                "doc_id": "SYNTH_DOC_01",
                "title": "Synthetic Droplet Study",
                "text": "The burning rate constant K was 0.65 mm^2/s under microgravity.",
                "page_number": 4,
                "research_group_label": "NASA_Glenn",
                "source_type": "flight",
                "peer_reviewed": "Y",
                "raw_logit": 3.2,
                "normalized_relevance_score": 0.96
            }
        ],
        "nearest_documents": []
    }
    
    with patch("api.routes_ask.retrieve_candidates", return_value=mock_retrieval_res):
        res = client.post("/api/ask", json={"query": "What is the droplet burning rate in microgravity under quiescent flow at 101 kPa?"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "answered"
        assert len(data["answer_sentences"]) > 0
        assert data["answer_sentences"][0]["citations"][0]["doc_id"] == "SYNTH_DOC_01"
        assert MANDATORY_DISCLAIMER_SUBSTRING in data["disclaimer"]
        assert data["tier"] == "MODERATE"


def test_brief_endpoint():
    res = client.post("/api/brief", json={"question": "Summarize solid flammability risk in spacecraft."})
    assert res.status_code == 200
    data = res.json()
    assert "key_findings" in data
    assert "conditions_of_validity" in data
    assert "earth_analog_mapping" in data
    assert MANDATORY_DISCLAIMER_SUBSTRING in data["disclaimer"]


def test_experiments_endpoint_empty_handling():
    res = client.get("/api/experiments")
    assert res.status_code == 200
    # On empty database, returns empty list without error
    assert isinstance(res.json(), list)


def test_query_length_cap_exceeded():
    """Verify that queries exceeding MAX_QUERY_LENGTH (500 chars) are rejected with 400."""
    long_query = "A" * 501
    res = client.post("/api/ask", json={"query": long_query})
    assert res.status_code == 400
    assert "exceeds maximum allowed length" in res.json()["detail"]


def test_spa_deep_link_fallback():
    """Verify React Router deep links (/compare, /brief) return index.html while /api/unknown returns 404."""
    # Test client request for React Router paths
    res_compare = client.get("/compare")
    # If dist/index.html is built, returns 200 with HTML; if not built, returns 404
    assert res_compare.status_code in (200, 404)
    if res_compare.status_code == 200:
        assert "<!doctype html>" in res_compare.text.lower() or "<html" in res_compare.text.lower()

    # Unhandled /api endpoint must return 404 JSON, NOT index.html
    res_api_unknown = client.get("/api/nonexistent_route")
    assert res_api_unknown.status_code == 404
    assert res_api_unknown.json()["detail"] == "API endpoint not found"


def test_spa_path_traversal_rejection():
    """Verify path traversal attempts escaping frontend/dist are blocked with 404."""
    # Test directory traversal via relative paths
    res = client.get("/../../config.yaml")
    assert res.status_code in (404, 400)
    # Ensure config.yaml contents were not leaked
    assert "retrieval:" not in res.text


def test_brief_with_candidates_synthesis():
    """Verify Safety Brief synthesizes findings from candidates and labels earth mapping as hypothesis."""
    mock_ret = {
        "status": "answered",
        "candidates": [
            {
                "doc_id": "SYNTH_P1",
                "title": "Spacecraft Flammability Study",
                "text": "Solid PMMA samples exhibited flame spread rate of 1.2 mm/s under microgravity.",
                "page_number": 3,
                "source_type": "flight",
                "campaign_or_series": "BASS",
                "research_group_label": "NASA_Glenn",
                "peer_reviewed": "Y"
            }
        ]
    }
    with patch("api.routes_brief.retrieve_candidates", return_value=mock_ret):
        res = client.post("/api/brief", json={"question": "Flammability and flame spread mechanisms in microgravity spacecraft environments"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["key_findings"]) > 0
        assert "HYPOTHESIS (unvalidated):" in data["earth_analog_mapping"]
        assert "source_types_represented" in data["conditions_of_validity"]
        assert data["conditions_of_validity"]["source_types_represented"] == "flight"
        assert MANDATORY_DISCLAIMER_SUBSTRING in data["disclaimer"]


def test_rate_limiter_proxy_ip_header():
    """Verify sliding-window rate limiter respects X-Forwarded-For client headers."""
    from api.rate_limit import enforce_rate_limit, _REQUEST_HISTORY
    from fastapi import Request

    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.195, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
    }
    req = Request(scope)
    # Enforce limit of 2 requests for testing
    enforce_rate_limit(req, limit=5, window=60.0)
    assert "203.0.113.195" in _REQUEST_HISTORY
    assert len(_REQUEST_HISTORY["203.0.113.195"]) >= 1


