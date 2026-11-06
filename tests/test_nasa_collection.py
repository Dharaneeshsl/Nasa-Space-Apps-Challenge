"""NASA permission gate and optional on-disk collection integrity checks."""
import csv
import hashlib
import json
from pathlib import Path
import pytest
from core.ingest import is_indexable_metadata

ROOT = Path(__file__).resolve().parents[1]

def test_public_access_alone_never_clears_ingestion():
    row = {'license_status': 'public_use_permitted', 'source_url': 'https://ntrs.nasa.gov/citations/123'}
    assert not is_indexable_metadata(row)
    row['ntrs_copyright_determination'] = 'GOV_PERMITTED'
    assert not is_indexable_metadata(row)
    row['ntrs_copyright_determination'] = 'PUBLIC_USE_PERMITTED'
    assert is_indexable_metadata(row)
    row['source_url'] = 'https://ntrs.nasa.gov.example.com/citations/123'
    assert not is_indexable_metadata(row)
    assert is_indexable_metadata({'license_status': 'public_domain_confirmed'})

def test_downloads_match_original_manifest():
    path = ROOT / 'data/provenance/collection_manifest.json'
    if not path.exists():
        pytest.skip('Run NASA collection first')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    assert not manifest['failures']
    for record in manifest['sources']:
        pdf = ROOT / 'data/pdfs' / (record['doc_id'] + '.pdf')
        if not pdf.exists():
            pytest.skip('Downloaded binaries are intentionally not committed')
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == record['sha256']

def test_staged_nasa_values_are_not_marked_independently_verified():
    path = ROOT / 'data/experiments_staging.csv'
    if not path.exists():
        pytest.skip('Run NASA table preparation first')
    with path.open(encoding='utf-8', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('curated_by') == 'Codex_first_pass']
    assert len(rows) == 8
    for row in rows:
        assert not row['verified_by'] and not row['verified_date']
        assert not row['pressure_raw_value'] and not row['metric_uncertainty_raw']
        assert not row['flow_regime']
        assert row['source_page'] == '29'
