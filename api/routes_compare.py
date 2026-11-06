"""FastAPI Routes for Experiment Comparison: /api/experiments and /api/compare.

Connects to DuckDB view experiments_verified only.
Never allows LLM-extracted numbers in comparison tables.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from api.schemas import ExperimentItem, CompareRequest, CompareResponse, CompareCheck
from core.compare import compare_experiments
import duckdb
from pathlib import Path

router = APIRouter(prefix="/api", tags=["Compare"])
from core.config import data_path
DB_PATH = None  # Optional explicit override for isolated callers/tests.


def get_db_connection():
    db_path = DB_PATH or data_path("experiments_db", "data/experiments.duckdb")
    if not Path(db_path).exists():
        from scripts.load_experiments import init_db
        return init_db(db_path)
    return duckdb.connect(db_path, read_only=True)


@router.get("/experiments", response_model=List[ExperimentItem])
def get_verified_experiments() -> List[ExperimentItem]:
    """Retrieve all rows from experiments_verified view."""
    try:
        con = get_db_connection()
        rows = con.execute("SELECT * FROM experiments_verified;").fetchall()
        col_names = [desc[0] for desc in con.description]
        con.close()
    except Exception as e:
        return []

    results = []
    for r in rows:
        d = dict(zip(col_names, r))
        # Format date if present
        if d.get("verified_date"):
            d["verified_date"] = str(d["verified_date"])
        results.append(ExperimentItem(**d))
    return results


@router.post("/compare", response_model=CompareResponse)
def compare_experiments_endpoint(req: CompareRequest) -> CompareResponse:
    """Compare two verified experiments via deterministic scientific guardrails."""
    try:
        con = get_db_connection()
        row_a = con.execute(
            "SELECT * FROM experiments_verified WHERE staging_id = ?;", [req.id_a]
        ).fetchone()
        row_b = con.execute(
            "SELECT * FROM experiments_verified WHERE staging_id = ?;", [req.id_b]
        ).fetchone()
        col_names = [desc[0] for desc in con.description]
        con.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database access error: {e}")

    if not row_a or not row_b:
        raise HTTPException(
            status_code=404, 
            detail=f"One or both experiments (ID {req.id_a}, {req.id_b}) not found in verified view."
        )

    exp_a = dict(zip(col_names, row_a))
    exp_b = dict(zip(col_names, row_b))

    res = compare_experiments(exp_a, exp_b)

    checks = [
        CompareCheck(
            name=c["name"],
            result=c["result"],
            reason=c["reason"],
            values=c["values"]
        )
        for c in res["checks"]
    ]

    return CompareResponse(
        state=res["state"],
        checks=checks,
        series_a=res["series_a"],
        series_b=res["series_b"],
        metric_name=res.get("metric_name"),
        metric_unit=res.get("metric_unit"),
        value_a=res.get("value_a"),
        value_b=res.get("value_b"),
        uncertainty_a=res.get("uncertainty_a"),
        uncertainty_b=res.get("uncertainty_b"),
        uncertainty_reported=res.get("uncertainty_reported", False),
        provenance=res["provenance"],
        harmonized_units=res["harmonized_units"]
    )
