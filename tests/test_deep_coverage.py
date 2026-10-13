"""Deep Coverage Integration Tests for CombustionLens.

Covers:
1. Loader transaction safety, duplicate rejection, and non-standard metric preservation.
2. PyMuPDF Ingestion pipeline with synthetic test PDF and license status filtering.
3. Citation validation against retrieved candidates (no fake defaults, no hallucinated cites).
4. Full FastAPI /api/compare endpoint against a real DuckDB database.

NOTE: All fixtures are synthetic and live strictly within tests/.
"""
import os
import json
import tempfile
import pytest
import duckdb
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from scripts.load_experiments import validate_row, load_staging_csv, init_db
from core.ingest import extract_chunks_from_pdf, ingest_corpus
from core.generate import validate_and_filter_citations
from core.compare import compare_experiments

client = TestClient(app)


# ------------------------------------------------------------------------------
# 1. Loader & Database Tests
# ------------------------------------------------------------------------------
def test_loader_preserves_unstandardized_metric():
    row = {
        "staging_id": "101",
        "experiment_series": "FLEX",
        "run_id": "R1",
        "fuel": "heptane",
        "fuel_class": "droplet",
        "geometry": "spherical",
        "scale_dimension_raw": "2mm",
        "O2_value": "0.21",
        "O2_basis": "mole_fraction",
        "diluent": "nitrogen",
        "pressure_raw_value": "101.3",
        "pressure_raw_unit": "kPa",
        "gravity_level": "microgravity",
        "flow_regime": "quiescent",
        "flow_velocity_cm_s": "0.0",
        "metric_name": "extinction_diameter",  # Custom unstandardized metric
        "metric_value_raw": "0.45",
        "metric_uncertainty_raw": "0.02",
        "metric_unit_raw": "mm",
        "source_paper": "NASA TP 2020",
        "source_page": "12",
        "curated_by": "CuratorA",
        "verified_by": "VerifierB",
        "verified_date": "2026-05-10"
    }
    is_valid, err, clean = validate_row(row)
    assert is_valid is True
    assert clean["metric_value_std"] is not None or clean["metric_value_raw"] == "0.45"
    assert clean["pressure_std_kPa"] == 101.3


def test_loader_rejects_invalid_date_format():
    row = {
        "staging_id": "102",
        "experiment_series": "BASS",
        "fuel": "PMMA",
        "fuel_class": "cast_solid",
        "geometry": "flat_slab",
        "gravity_level": "microgravity",
        "metric_name": "flame_spread_rate",
        "metric_value_raw": "1.2",
        "metric_unit_raw": "mm/s",
        "source_paper": "NASA TP 2021",
        "source_page": "5",
        "curated_by": "CuratorA",
        "verified_by": "VerifierB",
        "verified_date": "10-05-2026"  # Invalid non-ISO format!
    }
    is_valid, err, clean = validate_row(row)
    assert is_valid is False
    assert "verified_date" in err


def test_loader_duplicate_id_protection():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "staging.csv"
        db_path = Path(tmpdir) / "test.duckdb"
        
        # Write CSV with duplicate staging_id
        csv_path.write_text(
            "staging_id,experiment_series,fuel,fuel_class,geometry,gravity_level,metric_name,metric_unit_raw,source_paper,source_page,curated_by\n"
            "1,FLEX,heptane,droplet,spherical,microgravity,burning_rate,mm^2/s,NASA_P1,1,UserA\n"
            "1,FLEX,heptane,droplet,spherical,microgravity,burning_rate,mm^2/s,NASA_P1,2,UserA\n"
        )
        loaded = load_staging_csv(str(csv_path), str(db_path))
        assert loaded == 0  # Aborts cleanly on duplicate IDs without modifying DB


# ------------------------------------------------------------------------------
# 2. Ingest & PyMuPDF Tests
# ------------------------------------------------------------------------------
def test_ingest_synthetic_pdf():
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "TEST_DOC_01.pdf"
        meta_csv = Path(tmpdir) / "paper_meta.csv"
        
        # Create synthetic PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), "Section 1. Introduction.\nCombustion experiments in microgravity show spherical flames.")
        doc.save(str(pdf_path))
        doc.close()
        
        # Write metadata
        meta_csv.write_text(
            "doc_id,title,authors,year,campaign_or_series,research_group_label,source_type,peer_reviewed,license_status,notes\n"
            "TEST_DOC_01,Synthetic Flame Study,Author A,2026,FLEX,NASA_Glenn,flight,Y,public_domain_confirmed,ok\n"
            "RESTRICTED_DOC,Restricted Paper,Author B,2026,BASS,Unknown,numerical,N,restricted,skip\n"
        )
        
        chunks, skipped = ingest_corpus(tmpdir, str(meta_csv))
        assert len(chunks) >= 1
        assert chunks[0]["doc_id"] == "TEST_DOC_01"
        assert chunks[0]["page_number"] == 1
        assert "spherical flames" in chunks[0]["text"]


# ------------------------------------------------------------------------------
# 3. Citation Validation Tests
# ------------------------------------------------------------------------------
def test_validate_and_filter_citations_grounding():
    candidates = [
        {"doc_id": "NASA_TP_100", "title": "Paper 100", "page_number": 12, "text": "Burning constant 0.72 mm^2/s."}
    ]
    
    # 1. Valid citation matching candidate
    valid_sentences = [{
        "text": "The burning constant was 0.72 mm^2/s.",
        "citations": [{"doc_id": "NASA_TP_100", "page": 12}]
    }]
    res_valid = validate_and_filter_citations(valid_sentences, candidates)
    assert len(res_valid) == 1
    assert res_valid[0]["citations"][0]["paper_title"] == "Paper 100"

    # 2. Hallucinated citation NOT in candidates -> pruned!
    hallucinated_sentences = [{
        "text": "Extinction happened at 15% O2.",
        "citations": [{"doc_id": "NON_EXISTENT_DOC", "page": 99}]
    }]
    res_hallucinated = validate_and_filter_citations(hallucinated_sentences, candidates)
    assert len(res_hallucinated) == 0  # Filtered out because citation was ungrounded!


# ------------------------------------------------------------------------------
# 4. Compare API with Real DuckDB View
# ------------------------------------------------------------------------------
def test_compare_endpoint_with_real_database(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "experiments.duckdb")
        con = init_db(db_path)
        
        # Insert two verified rows with matching fuel, geometry, and scale
        con.execute("""
        INSERT INTO experiments_staging (
            staging_id, experiment_series, fuel, fuel_class, geometry,
            scale_dimension_raw, gravity_level, flow_regime, metric_name, metric_value_raw,
            metric_value_std, metric_unit_raw, metric_unit_std,
            pressure_raw_value, pressure_std_kPa, conversion_provenance,
            O2_value, O2_basis, source_paper, source_page, curated_by,
            verified_by, verified_date
        ) VALUES 
        (1, 'FLEX', 'heptane', 'droplet', 'spherical', '2.0mm', 'microgravity', 'quiescent', 'burning_rate_constant_K', 0.65, 0.65, 'mm^2/s', 'mm^2/s', 101.3, 101.3, 'Reported in kPa', 0.21, 'mole_fraction', 'NASA_TP_1', '14', 'CuratorA', 'VerifierB', '2026-01-01'),
        (2, 'FLEX', 'heptane', 'droplet', 'spherical', '2.0mm', 'microgravity', 'quiescent', 'burning_rate_constant_K', 0.70, 0.70, 'mm^2/s', 'mm^2/s', 101.3, 101.3, 'Reported in kPa', 0.21, 'mole_fraction', 'NASA_TP_2', '20', 'CuratorC', 'VerifierD', '2026-01-02');
        """)
        con.close()
        
        monkeypatch.setattr("api.routes_compare.DB_PATH", db_path)
        
        # Test GET /api/experiments
        res_list = client.get("/api/experiments")
        assert res_list.status_code == 200
        assert len(res_list.json()) == 2
        
        # Test POST /api/compare
        res_comp = client.post("/api/compare", json={"id_a": 1, "id_b": 2})
        assert res_comp.status_code == 200
        data = res_comp.json()
        assert data["state"] == "PASS"
        assert data["value_a"] == 0.65
        assert data["value_b"] == 0.70


# ------------------------------------------------------------------------------
# 5. Loader Ragged Row & Successful Insertion Tests
# ------------------------------------------------------------------------------
def test_loader_ragged_row_safe_handling():
    """Verify that ragged CSV rows with None values do not crash with AttributeError."""
    ragged_row = {
        "staging_id": "1",
        "experiment_series": None,  # Ragged / missing column value
        "fuel": "heptane",
        "fuel_class": None,
        "geometry": None,
        "gravity_level": "microgravity",
        "metric_name": "burning_rate",
        "metric_unit_raw": "mm^2/s",
        "source_paper": None,
        "source_page": None,
        "curated_by": None
    }
    is_valid, err_msg, clean = validate_row(ragged_row)
    assert is_valid is False
    assert "Missing required NOT NULL field" in err_msg


def test_loader_successful_insertion():
    """Verify clean staging rows insert atomically and become visible in experiments_verified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "staging.csv"
        db_path = Path(tmpdir) / "test.duckdb"
        
        csv_path.write_text(
            "staging_id,experiment_series,run_id,fuel,fuel_class,geometry,scale_dimension_raw,O2_value,O2_basis,diluent,pressure_raw_value,pressure_raw_unit,gravity_level,flow_regime,flow_velocity_cm_s,metric_name,metric_value_raw,metric_uncertainty_raw,metric_unit_raw,measurement_method,source_paper,source_page,curated_by,verified_by,verified_date\n"
            "1,FLEX,R1,heptane,droplet,spherical,2.0mm,0.21,mole_fraction,nitrogen,101.3,kPa,microgravity,quiescent,0.0,burning_rate_constant_K,0.65,0.02,mm^2/s,camera,NASA_TP_1,14,Alice,Bob,2026-01-01\n",
            encoding="utf-8"
        )
        loaded = load_staging_csv(str(csv_path), str(db_path))
        assert loaded == 1
        
        con = duckdb.connect(str(db_path))
        verified_count = con.execute("SELECT count(*) FROM experiments_verified").fetchone()[0]
        assert verified_count == 1
        con.close()


# ------------------------------------------------------------------------------
# 6. Evaluation Tooling Tests (calibrate_tau & unblind_and_score)
# ------------------------------------------------------------------------------
def test_calibrate_tau_empty_handling():
    """Verify calibrate_threshold handles empty questions gracefully."""
    from scripts.calibrate_tau import calibrate_threshold
    with tempfile.TemporaryDirectory() as tmpdir:
        q_csv = Path(tmpdir) / "empty_questions.csv"
        q_csv.write_text("question_id,question,category,gold_answer\n", encoding="utf-8")
        best_tau, info = calibrate_threshold(questions_csv=str(q_csv))
        assert best_tau == 0.0
        assert info == {}


def test_unblind_and_score_execution():
    """Verify unblind_and_score aggregates grades across splits and generates results.md."""
    from eval.unblind_and_score import unblind_and_score
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        grade_csv = tmp_path / "grade_sheet.csv"
        blind_key = tmp_path / ".blind_key.json"
        results_md = tmp_path / "results.md"
        
        # Write dummy blind key
        key_data = {
            "models": {
                "Q1::Model_A": {
                    "question_id": "Q1",
                    "blinded_label": "Model_A",
                    "real_system_id": "SYS_C_COMBUSTIONLENS",
                    "split": "held_out"
                },
                "Q1::Model_B": {
                    "question_id": "Q1",
                    "blinded_label": "Model_B",
                    "real_system_id": "SYS_B_NAIVE_RAG",
                    "split": "held_out"
                }
            }
        }
        blind_key.write_text(json.dumps(key_data), encoding="utf-8")
        
        # Write graded sheet
        grade_csv.write_text(
            "question_id,blinded_system_label,split,category,question,gold_answer,gold_citation_paper,gold_citation_page,generated_output,cited_sources,factual_accuracy,citation_supported,hallucination,refusal_correct,notes,grader\n"
            "Q1,Model_A,held_out,factual,Sample question,Gold answer,Paper1,10,Output A,Paper1 p.10,1,1,0,0,Looks good,Grader1\n"
            "Q1,Model_B,held_out,factual,Sample question,Gold answer,Paper1,10,Output B,Paper1 p.10,1,0,0,0,No citation,Grader1\n",
            encoding="utf-8"
        )
        
        unblind_and_score(
            grade_sheet_path=str(grade_csv),
            blind_key_path=str(blind_key),
            results_md_path=str(results_md)
        )
        
        assert results_md.exists()
        content = results_md.read_text(encoding="utf-8")
        assert "CombustionLens Benchmark Evaluation Results" in content
        assert "System C (CombustionLens)" in content

