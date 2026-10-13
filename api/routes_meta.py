"""FastAPI Route: /api/status

Surfaces global corpus metrics, verified row counts, and calibration mode.
Used by application footer on every view.
"""
import os
import csv
import duckdb
import yaml
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter
from api.schemas import StatusResponse

router = APIRouter(prefix="/api", tags=["Metadata"])


@router.get("/status", response_model=StatusResponse)
def get_system_status() -> StatusResponse:
    # 1. Corpus size from license-cleared papers in paper_meta.csv
    corpus_size = 0
    meta_path = Path("data/paper_meta.csv")
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                corpus_size = len([r for r in reader if r.get("license_status") == "public_domain_confirmed"])
        except Exception:
            corpus_size = 0

    # 2. Verified rows count from DuckDB and human-readable last update
    verified_rows = 0
    db_path = Path("data/experiments.duckdb")
    last_update = None
    if db_path.exists():
        try:
            con = duckdb.connect(str(db_path), read_only=True)
            verified_rows = con.execute("SELECT COUNT(*) FROM experiments_verified;").fetchone()[0]
            con.close()
            mtime = Path(db_path).stat().st_mtime
            last_update = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            pass

    # 3. Calibration mode from config
    tau_mode = "uncalibrated (tau_ce is null)"
    cfg_path = Path("config.yaml")
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                c = yaml.safe_load(f) or {}
                tau_val = c.get("retrieval", {}).get("tau_ce")
                if tau_val is not None:
                    tau_mode = f"calibrated (tau_ce = {tau_val})"
        except Exception:
            pass

    return StatusResponse(
        corpus_size=corpus_size,
        verified_rows=verified_rows,
        last_data_update=last_update,
        tau_ce_mode=tau_mode
    )
