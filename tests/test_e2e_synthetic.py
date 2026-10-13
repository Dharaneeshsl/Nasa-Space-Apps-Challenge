"""End-to-End Integration Test for CombustionLens with Synthetic Fixtures.

HARD RULES:
1. All fixtures are synthetic and live strictly within tests/.
2. No real data or mocks: executes full pipeline (ingest -> chunk -> embed -> index -> retrieve -> rerank -> ground -> number-check).
3. Verifies zero fabrication, number verification, citation validation, and non-operational disclaimer.
"""
import os
import tempfile
from pathlib import Path
import pytest
import fitz
import yaml
from fastapi.testclient import TestClient

from api.main import app
from scripts.build_index import build_vector_index


@pytest.fixture
def synthetic_pipeline_env():
    """Builds a real, isolated ChromaDB index from a synthetic PyMuPDF PDF in a temporary directory."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        tmp_path = Path(tmpdir)
        pdfs_dir = tmp_path / "pdfs"
        index_dir = tmp_path / "index"
        pdfs_dir.mkdir(parents=True, exist_ok=True)
        index_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create Synthetic PDF
        pdf_file = pdfs_dir / "SYNTH_TEST_PAPER_01.pdf"
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text(
            fitz.Point(50, 50),
            "In this microgravity experiment, the burning rate constant of n-heptane droplets "
            "under quiescent conditions at 101 kPa was measured as 0.78 mm^2/s. "
            "Soot-free spherical extinction was observed consistently across all runs."
        )
        p2 = doc.new_page()
        p2.insert_text(
            fitz.Point(50, 50),
            "Under forced flow conditions, droplet flame transitions occurred at 50 kPa."
        )
        doc.save(str(pdf_file))
        doc.close()

        # 2. Create Synthetic Metadata CSV (license_status = public_domain_confirmed)
        meta_csv = tmp_path / "paper_meta.csv"
        meta_csv.write_text(
            "doc_id,title,authors,year,campaign_or_series,research_group_label,source_type,peer_reviewed,license_status\n"
            "SYNTH_TEST_PAPER_01,Synthetic Microgravity Droplet Combustion Study,NASA Research Team,2024,FLEX,GroupA,flight_experiment,true,public_domain_confirmed\n",
            encoding="utf-8"
        )

        # 3. Create Synthetic config.yaml with calibrated tau_ce
        config_file = tmp_path / "config.yaml"
        cfg_data = {
            "retrieval": {
                "top_k_bi": 5,
                "top_k_ce": 3,
                "tau_ce": -5.0  # Threshold allows high-relevance match to pass refusal gate
            },
            "model": {
                "generator_model": "",  # Uses deterministic grounded extraction
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "cross_encoder_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
            },
            "paths": {
                "chroma_dir": str(index_dir),
                "paper_meta": str(meta_csv),
                "pdfs_dir": str(pdfs_dir)
            }
        }
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(cfg_data, f)

        # 4. Execute Build Pipeline to create ChromaDB collection
        build_vector_index(
            config_path=str(config_file),
            persist_dir=str(index_dir),
            pdfs_dir=str(pdfs_dir),
            meta_path=str(meta_csv)
        )

        # Set environment variables for FastAPI client
        old_chroma = os.environ.get("COMBUSTIONLENS_CHROMA_DIR")
        old_config = os.environ.get("COMBUSTIONLENS_CONFIG_PATH")
        os.environ["COMBUSTIONLENS_CHROMA_DIR"] = str(index_dir)
        os.environ["COMBUSTIONLENS_CONFIG_PATH"] = str(config_file)

        yield {
            "tmp_path": tmp_path,
            "index_dir": index_dir,
            "config_file": config_file,
            "doc_id": "SYNTH_TEST_PAPER_01"
        }

        # Restore environment
        if old_chroma is not None:
            os.environ["COMBUSTIONLENS_CHROMA_DIR"] = old_chroma
        else:
            os.environ.pop("COMBUSTIONLENS_CHROMA_DIR", None)

        if old_config is not None:
            os.environ["COMBUSTIONLENS_CONFIG_PATH"] = old_config
        else:
            os.environ.pop("COMBUSTIONLENS_CONFIG_PATH", None)


def test_synthetic_end_to_end_ask_pipeline(synthetic_pipeline_env):
    """End-to-end verification of /api/ask using synthetic un-mocked ChromaDB index."""
    client = TestClient(app)

    # 1. Targeted query with boundary conditions (fuel: n-heptane, gravity: microgravity, pressure: 101 kPa, flow: quiescent)
    query = "What is the burning rate of n-heptane droplets under quiescent conditions in microgravity at 101 kPa?"
    resp = client.post("/api/ask", json={"query": query})

    assert resp.status_code == 200
    data = resp.json()

    # Verify status and generation mode
    assert data["status"] == "answered"
    assert data["generation_mode"] == "deterministic_fallback"

    # Verify synthesized sentences
    assert len(data["answer_sentences"]) > 0
    first_sentence = data["answer_sentences"][0]
    assert "0.78" in first_sentence["text"] or "burning rate" in first_sentence["text"].lower()

    # Verify verified citations exist and match synthetic doc
    assert len(first_sentence["citations"]) > 0
    cite = first_sentence["citations"][0]
    assert cite["doc_id"] == "SYNTH_TEST_PAPER_01"
    assert cite["page"] == 1
    assert cite["paper_title"] == "Synthetic Microgravity Droplet Combustion Study"

    # Verify number check did not hide valid grounded number
    assert len(data.get("hidden_sentences", [])) == 0

    # Verify transparent multi-factor ranking
    assert len(data["rank_breakdown"]) > 0
    top_rank = data["rank_breakdown"][0]
    assert top_rank["doc_id"] == "SYNTH_TEST_PAPER_01"
    assert "s_rel" in top_rank
    assert "s_corrob" in top_rank
    assert "s_source" in top_rank
    assert "rank_score" in top_rank

    # Verify non-operational safety disclaimer
    assert data["disclaimer"] == (
        "Generated from published NASA research for informational/research purposes. "
        "Not validated for operational flight or terrestrial fire safety decisions."
    )


def test_synthetic_end_to_end_out_of_scope_refusal(synthetic_pipeline_env):
    """Verifies that an out-of-scope query refuses with zero generated text."""
    client = TestClient(app)

    # Completely unrelated query
    resp = client.post("/api/ask", json={"query": "What is the orbital speed of the International Space Station?"})
    assert resp.status_code == 200
    data = resp.json()

    # Out of scope query should either be refused (insufficient) or lack groundable sentences
    # Crucially, zero generated text must be output
    assert len(data["answer_sentences"]) == 0
    assert data["disclaimer"] == (
        "Generated from published NASA research for informational/research purposes. "
        "Not validated for operational flight or terrestrial fire safety decisions."
    )
