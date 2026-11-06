"""Script: Load experiments from CSV into DuckDB staging and verified view.

Loads data/experiments_staging.csv into data/experiments.duckdb.
Rejects invalid rows with explicit error reasons.
Handles empty CSV input gracefully without error.
"""
import os
import sys
import csv
import math
from pathlib import Path
import duckdb

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.units import convert_pressure_to_kpa, standardize_metric
from core.config import data_path

ALLOWED_FUEL_CLASSES = {"droplet", "cast_solid", "thin_sheet", "gaseous_jet"}
ALLOWED_O2_BASES = {"mole_fraction", "volume_percent", "mass_fraction"}
ALLOWED_PRESSURE_UNITS = {"kpa", "atm", "bar", "torr"}
ALLOWED_FLOW_REGIMES = {"quiescent", "forced_laminar", "forced_turbulent"}


def init_db(db_path: str = "data/experiments.duckdb") -> duckdb.DuckDBPyConnection:
    """Initialize DuckDB with experiments_staging table and experiments_verified view."""
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = duckdb.connect(db_path)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS experiments_staging (
        staging_id INTEGER PRIMARY KEY,
        experiment_series VARCHAR NOT NULL,
        run_id VARCHAR,
        fuel VARCHAR NOT NULL,
        fuel_class VARCHAR NOT NULL,
        geometry VARCHAR NOT NULL,
        scale_dimension_raw VARCHAR,
        O2_value DOUBLE,
        O2_basis VARCHAR,
        diluent VARCHAR,
        pressure_raw_value DOUBLE,
        pressure_raw_unit VARCHAR,
        gravity_level VARCHAR NOT NULL,
        flow_regime VARCHAR,
        flow_velocity_cm_s DOUBLE,
        metric_name VARCHAR NOT NULL,
        metric_value_raw DOUBLE,
        metric_uncertainty_raw DOUBLE,
        metric_unit_raw VARCHAR NOT NULL,
        measurement_method VARCHAR,
        pressure_std_kPa DOUBLE,
        metric_value_std DOUBLE,
        metric_unit_std VARCHAR,
        conversion_provenance VARCHAR,
        source_paper VARCHAR NOT NULL,
        source_page VARCHAR NOT NULL,
        curated_by VARCHAR NOT NULL,
        verified_by VARCHAR,
        verified_date DATE,
        doc_id VARCHAR,
        second_pass_agrees BOOLEAN
    );
    """)
    
    con.execute("""
    CREATE OR REPLACE VIEW experiments_verified AS
    SELECT * FROM experiments_staging
    WHERE verified_by IS NOT NULL
      AND trim(verified_by) <> ''
      AND trim(curated_by) <> ''
      AND lower(trim(verified_by)) <> lower(trim(curated_by))
      AND second_pass_agrees IS DISTINCT FROM FALSE
      AND metric_value_raw IS NOT NULL
      AND isfinite(metric_value_raw)
      AND source_page IS NOT NULL
      AND trim(source_page) <> '';
    """)
    return con


def validate_row(row: dict) -> tuple[bool, str, dict]:
    """Validate a staging CSV row against required constraints and standardize units."""
    row = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
    required_fields = [
        "staging_id", "experiment_series", "fuel", "fuel_class", 
        "geometry", "gravity_level", "metric_name", "metric_unit_raw", 
        "source_paper", "source_page", "curated_by"
    ]
    
    for f in required_fields:
        val = (row.get(f) or "").strip()
        if not val:
            return False, f"Missing required NOT NULL field: '{f}'", {}
            
    # Validate categorical constraints
    fuel_class = (row.get("fuel_class") or "").strip().lower()
    if fuel_class not in ALLOWED_FUEL_CLASSES:
        return False, f"Invalid fuel_class '{row.get('fuel_class')}'. Allowed: {ALLOWED_FUEL_CLASSES}", {}
        
    flow_regime = (row.get("flow_regime") or "").strip().lower()
    if flow_regime and flow_regime not in ALLOWED_FLOW_REGIMES:
        return False, f"Invalid flow_regime '{row.get('flow_regime')}'. Allowed: {ALLOWED_FLOW_REGIMES}", {}
        
    o2_basis = (row.get("O2_basis") or "").strip().lower()
    if o2_basis and o2_basis not in ALLOWED_O2_BASES:
        return False, f"Invalid O2_basis '{row.get('O2_basis')}'. Allowed: {ALLOWED_O2_BASES}", {}
        
    press_unit = (row.get("pressure_raw_unit") or "").strip().lower()
    if press_unit and press_unit not in ALLOWED_PRESSURE_UNITS:
        return False, f"Invalid pressure_raw_unit '{row.get('pressure_raw_unit')}'. Allowed: {ALLOWED_PRESSURE_UNITS}", {}

    # Validate staging_id integer
    try:
        int((row.get("staging_id") or "").strip())
    except ValueError:
        return False, f"Invalid staging_id '{row.get('staging_id')}'. Must be an integer.", {}

    for field in ("O2_value", "pressure_raw_value", "flow_velocity_cm_s",
                  "metric_value_raw", "metric_uncertainty_raw"):
        value = row.get(field)
        if value not in (None, ""):
            try:
                number = float(value)
            except (TypeError, ValueError):
                return False, f"Invalid numeric field: '{field}'", {}
            if not math.isfinite(number):
                return False, f"Non-finite numeric field: '{field}'", {}
            if field != "metric_value_raw" and number < 0:
                return False, f"Negative physical value: '{field}'", {}
            if field == "pressure_raw_value" and number == 0:
                return False, "Pressure must be positive", {}
            if field == "O2_value" and number > (100 if o2_basis == "volume_percent" else 1):
                return False, "Oxygen value is outside its basis range", {}
    agreement = str(row.get("second_pass_agrees") or "").lower()
    if agreement not in ("", "true", "false", "1", "0", "yes", "no", "y", "n"):
        return False, "Invalid second_pass_agrees boolean", {}

    # Validate verified_date if present
    v_date = (row.get("verified_date") or "").strip()
    if v_date:
        try:
            from datetime import datetime
            datetime.strptime(v_date, "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid verified_date '{v_date}'. Must be format YYYY-MM-DD", {}

    # Unit standardization
    clean_row = dict(row)
    provenances = []
    
    # Pressure standardization
    p_val = (clean_row.get("pressure_raw_value") or "").strip()
    if p_val and press_unit:
        try:
            std_p, _, p_prov = convert_pressure_to_kpa(float(p_val), press_unit)
            clean_row["pressure_std_kPa"] = std_p
            if p_prov:
                provenances.append(p_prov)
        except Exception as e:
            return False, f"Pressure standardization error: {e}", {}
    else:
        clean_row["pressure_std_kPa"] = None
        
    # Metric standardization (preserves raw value if metric category is unstandardized)
    m_val = (clean_row.get("metric_value_raw") or "").strip()
    m_name = (clean_row.get("metric_name") or "").strip()
    m_unit = (clean_row.get("metric_unit_raw") or "").strip()
    if m_val and m_unit:
        try:
            std_m, std_unit, m_prov = standardize_metric(m_name, float(m_val), m_unit)
            clean_row["metric_value_std"] = std_m
            clean_row["metric_unit_std"] = std_unit
            if m_prov:
                provenances.append(m_prov)
        except ValueError as e:
            err_msg = str(e)
            if "Unsupported unit" in err_msg:
                # Unsupported unit for a known metric (typo or invalid unit): reject row
                return False, f"Metric unit error: {err_msg}", {}
            else:
                # Unstandardized metric category: preserve raw value & unit
                clean_row["metric_value_std"] = None
                clean_row["metric_unit_std"] = None
                provenances.append(f"Unstandardized metric category ({m_name}); raw value and unit preserved")
        except Exception as e:
            return False, f"Metric standardization error: {e}", {}
    else:
        clean_row["metric_value_std"] = None
        clean_row["metric_unit_std"] = None

    clean_row["conversion_provenance"] = "; ".join(provenances) if provenances else "No unit conversion performed"
    return True, "", clean_row


def load_staging_csv(csv_path: str = None, db_path: str = None) -> int:
    """Load rows from staging CSV into DuckDB, reporting errors and rejecting invalid rows."""
    csv_path = csv_path or data_path("experiments_staging", "data/experiments_staging.csv")
    db_path = db_path or data_path("experiments_db", "data/experiments.duckdb")
    con = init_db(db_path)
    
    if not os.path.exists(csv_path):
        print(f"Staging CSV not found at '{csv_path}'. Initialized empty DuckDB schema.")
        con.close()
        return 0
        
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    if not rows:
        print(f"Staging CSV '{csv_path}' has 0 rows (header only). DuckDB schema ready.")
        con.execute("DELETE FROM experiments_staging;")
        con.close()
        return 0

    valid_rows = []
    rejected_count = 0
    
    for idx, raw_row in enumerate(rows, start=1):
        is_valid, err_msg, clean_row = validate_row(raw_row)
        if not is_valid:
            rejected_count += 1
            print(f"Row {idx} [REJECTED]: {err_msg}")
        else:
            valid_rows.append(clean_row)

    if rejected_count > 0:
        print(f"ERROR: {rejected_count} row(s) failed validation. Existing records preserved; load aborted.")
        con.close()
        return 0
        
    if valid_rows:
        # Pre-check for duplicate staging_ids to prevent partial insertion failure
        seen_ids = set()
        duplicates = set()
        for r in valid_rows:
            s_id = int(r["staging_id"])
            if s_id in seen_ids:
                duplicates.add(s_id)
            seen_ids.add(s_id)
        if duplicates:
            print(f"ERROR: Duplicate staging_id found in CSV: {sorted(list(duplicates))}. Load aborted to protect database.")
            con.close()
            return 0

        # Execute atomically within a single DuckDB transaction
        insert_sql = """
        INSERT INTO experiments_staging (
            staging_id, experiment_series, run_id, fuel, fuel_class, geometry,
            scale_dimension_raw, O2_value, O2_basis, diluent, pressure_raw_value,
            pressure_raw_unit, gravity_level, flow_regime, flow_velocity_cm_s,
            metric_name, metric_value_raw, metric_uncertainty_raw, metric_unit_raw,
            measurement_method, pressure_std_kPa, metric_value_std, metric_unit_std,
            conversion_provenance, source_paper, source_page, curated_by, verified_by,
            verified_date, doc_id, second_pass_agrees
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """
        
        con.begin()
        try:
            con.execute("DELETE FROM experiments_staging;")
            for r in valid_rows:
                def to_float(val):
                    return float(val) if val is not None and str(val).strip() != "" else None
                def to_int(val):
                    return int(val) if val is not None and str(val).strip() != "" else None
                def to_bool(val):
                    if val is None or str(val).strip() == "":
                        return None
                    return str(val).strip().lower() in ("true", "1", "yes", "y")

                con.execute(insert_sql, [
                    to_int(r["staging_id"]),
                    r["experiment_series"] or None,
                    r.get("run_id") or None,
                    r["fuel"] or None,
                    r["fuel_class"] or None,
                    r["geometry"] or None,
                    r.get("scale_dimension_raw") or None,
                    to_float(r.get("O2_value")),
                    r.get("O2_basis") or None,
                    r.get("diluent") or None,
                    to_float(r.get("pressure_raw_value")),
                    r.get("pressure_raw_unit") or None,
                    r["gravity_level"] or None,
                    r.get("flow_regime") or None,
                    to_float(r.get("flow_velocity_cm_s")),
                    r["metric_name"] or None,
                    to_float(r.get("metric_value_raw")),
                    to_float(r.get("metric_uncertainty_raw")),
                    r["metric_unit_raw"] or None,
                    r.get("measurement_method") or None,
                    to_float(r.get("pressure_std_kPa")),
                    to_float(r.get("metric_value_std")),
                    r.get("metric_unit_std") or None,
                    r.get("conversion_provenance") or None,
                    r["source_paper"] or None,
                    r["source_page"] or None,
                    r["curated_by"] or None,
                    r.get("verified_by") or None,
                    r.get("verified_date") or None,
                    r.get("doc_id") or None,
                    to_bool(r.get("second_pass_agrees")),
                ])
            con.commit()
        except Exception as e:
            con.rollback()
            con.close()
            print(f"DATABASE TRANSACTION ERROR: {e}. Rolled back all changes.")
            return 0
            
    verified_count = con.execute("SELECT COUNT(*) FROM experiments_verified;").fetchone()[0]
    total_staging = con.execute("SELECT COUNT(*) FROM experiments_staging;").fetchone()[0]
    print(f"Loaded {len(valid_rows)} valid rows into staging ({rejected_count} rejected).")
    print(f"Total staging rows: {total_staging}. Verified view rows: {verified_count}.")
    con.close()
    return len(valid_rows)


if __name__ == "__main__":
    load_staging_csv()
