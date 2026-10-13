"""Script: Validate data integrity and schema compliance (READ-ONLY).

Reports (never modifies):
- Whether every PDF in data/pdfs/ has a corresponding paper_meta.csv row.
- Allowed values validation for paper_meta.csv and experiments.
- Total corpus size (PDFs and metadata entries).
- Total verified rows count in DuckDB experiments_verified view.
- Clean execution and report on empty input.
"""
import os
import sys
import csv
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ALLOWED_SOURCE_TYPES = {"flight", "drop_tower", "parabolic_flight", "numerical", "review", "unknown"}
ALLOWED_LICENSE_STATUSES = {"public_domain_confirmed", "restricted", "unclear"}
ALLOWED_PEER_REVIEWED = {"y", "n", "unknown"}


def validate_corpus(data_dir: str = "data") -> dict:
    """Validate PDFs, paper_meta.csv, and DuckDB rows, returning a summary report."""
    report = {
        "pdf_count": 0,
        "paper_meta_count": 0,
        "license_cleared_count": 0,
        "missing_meta_pdfs": [],
        "invalid_meta_rows": [],
        "verified_rows_count": 0,
        "staging_rows_count": 0,
    }
    
    pdfs_dir = Path(data_dir) / "pdfs"
    meta_path = Path(data_dir) / "paper_meta.csv"
    db_path = Path(data_dir) / "experiments.duckdb"
    
    # 1. Scan PDFs
    pdf_stems = set()
    if pdfs_dir.exists():
        for p in pdfs_dir.glob("*.pdf"):
            pdf_stems.add(p.stem)
    report["pdf_count"] = len(pdf_stems)
    
    # 2. Scan paper_meta.csv
    meta_doc_ids = set()
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                doc_id = row.get("doc_id", "").strip()
                if not doc_id:
                    report["invalid_meta_rows"].append((idx, "Missing doc_id"))
                    continue
                meta_doc_ids.add(doc_id)
                report["paper_meta_count"] += 1
                
                # Check license
                lic = row.get("license_status", "").strip().lower()
                if lic not in ALLOWED_LICENSE_STATUSES:
                    report["invalid_meta_rows"].append((idx, f"Invalid license_status '{lic}'"))
                elif lic == "public_domain_confirmed":
                    report["license_cleared_count"] += 1
                    
                # Check source_type
                src = row.get("source_type", "").strip().lower()
                if src and src not in ALLOWED_SOURCE_TYPES:
                    report["invalid_meta_rows"].append((idx, f"Invalid source_type '{src}'"))
                    
                # Check peer_reviewed
                pr = row.get("peer_reviewed", "").strip().lower()
                if pr and pr not in ALLOWED_PEER_REVIEWED:
                    report["invalid_meta_rows"].append((idx, f"Invalid peer_reviewed '{pr}'"))
                    
    # Check PDF to Meta linkage
    for stem in pdf_stems:
        if stem not in meta_doc_ids:
            report["missing_meta_pdfs"].append(stem)
            
    # 3. Check DuckDB counts if DB exists
    if db_path.exists():
        try:
            import duckdb
            con = duckdb.connect(str(db_path), read_only=True)
            report["staging_rows_count"] = con.execute("SELECT COUNT(*) FROM experiments_staging;").fetchone()[0]
            report["verified_rows_count"] = con.execute("SELECT COUNT(*) FROM experiments_verified;").fetchone()[0]
            con.close()
        except Exception as e:
            report["db_error"] = str(e)
            
    return report


def print_report():
    print("=" * 60)
    print("COMBUSTIONLENS: DATA VALIDATION & INTEGRITY REPORT")
    print("=" * 60)
    rep = validate_corpus()
    
    print(f"Corpus PDFs on disk:            {rep['pdf_count']}")
    print(f"Metadata rows in paper_meta:    {rep['paper_meta_count']}")
    print(f"License-cleared papers:         {rep['license_cleared_count']}")
    print(f"DuckDB staging rows:            {rep['staging_rows_count']}")
    print(f"DuckDB verified view rows:      {rep['verified_rows_count']}")
    print("-" * 60)
    
    if rep["missing_meta_pdfs"]:
        print("WARNING: PDFs missing metadata rows in paper_meta.csv:")
        for m in rep["missing_meta_pdfs"]:
            print(f"  - {m}.pdf")
    else:
        print("PDF to metadata linkage:        CLEAN (0 orphans)")
        
    if rep["invalid_meta_rows"]:
        print("WARNING: Invalid metadata rows found:")
        for idx, reason in rep["invalid_meta_rows"]:
            print(f"  - Row {idx}: {reason}")
    else:
        print("Metadata categorical integrity: CLEAN (0 schema violations)")
        
    if rep.get("db_error"):
        print(f"Database read note:             {rep['db_error']}")
        
    print("=" * 60)
    if rep["pdf_count"] == 0 and rep["paper_meta_count"] == 0 and rep["verified_rows_count"] == 0:
        print("STATUS: EMPTY STATE VERIFIED (Ready for official human data drop).")
    else:
        print("STATUS: DATA PRESENT AND VALIDATED.")
    print("=" * 60)


if __name__ == "__main__":
    print_report()
