"""Prepare traceable first-pass transcriptions; never populate verification fields."""
import csv
import json
import re
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def write_csv(path, rows, fields=None):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def prepare():
    # Publication year is from publication metadata, never acquisition year.
    path = DATA / 'paper_meta.csv'
    with path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        metadata = list(reader)
    for row in metadata:
        source = DATA / 'provenance' / (row['doc_id'] + '.json')
        if source.exists():
            record = json.loads(source.read_text(encoding='utf-8'))
            row['year'] = next((p['publicationDate'][:4] for p in record.get('publications', []) if p.get('publicationDate')), '')
    write_csv(path, metadata, fields)
    manifest_path = DATA / 'provenance/collection_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    by_id = {r['doc_id']: r for r in metadata}
    for record in manifest['sources']:
        record['year'] = by_id[record['doc_id']]['year']
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Preserve the original table's flow ranges, comments and oxygen footnotes.
    pages = json.loads((DATA / 'extracted/ntrs_20210011385.json').read_text(encoding='utf-8'))
    page = pages[103]
    assert page['page'] == 104 and 'TABLE 7.1' in page['text']
    lines = [s.strip() for s in page['text'].splitlines() if s.strip()]
    starts = [i for i, s in enumerate(lines) if re.fullmatch(r'GMT\d+-T\d+[ab]?', s)]
    conditions = []
    for i in starts:
        run, width, flow, oxygen, comment = lines[i:i+5]
        assert re.fullmatch(r'\d+(\.\d+)?', width)
        assert re.fullmatch(r'\d+(\.\d+)?( to \d+(\.\d+)?)?', flow)
        assert re.fullmatch(r'\d+(\.\d+)?b?', oxygen)
        conditions.append(dict(run_id=run, sample_width_cm=width, flow_cm_s_reported=flow,
            oxygen_volume_percent_reported=oxygen, comments=comment,
            oxygen_caveat='Source footnote b: oxygen reading might be inaccurate' if oxygen.endswith('b') else '',
            source_doc_id='ntrs_20210011385', source_pdf_page=104, source_table='7.1',
            source_url='https://ntrs.nasa.gov/citations/20210011385',
            curation_status='first_pass_pending_independent_review'))
    assert len(conditions) == 31
    write_csv(DATA / 'bass_test_conditions.csv', conditions)
    # Exact reported measurements in Saffire Table I (PDF page 29).
    # No graph digitization, invented error bars or inferred pressure values.
    saffire = json.loads((DATA / 'extracted/ntrs_20170008805.json').read_text(encoding='utf-8'))[28]['text']
    assert 'Table I.' in saffire
    rows = []
    for run, width, length, direction, flow, rate, duration in [
        ('1-1', '40.6', '94', 'concurrent', '20', '1.8', '420'),
        ('1-2', '40.6', '~10', 'opposed', '20', '1.3', '70'),
        ('2-5', '5', '29', 'concurrent', '20', '2.1', '145'),
        ('2-6', '5', '29', 'concurrent', '25', '2.6', '115'),
    ]:
        assert f'{rate} mm/s' in saffire and f'{duration} s' in saffire
        for metric, value, unit in [('flame_spread_rate', rate, 'mm/s'), ('burn_duration', duration, 's')]:
            rows.append(dict(staging_id=len(rows)+1, experiment_series='Saffire', run_id=run,
                fuel='cotton-fiberglass (SIBAL)', fuel_class='thin_sheet',
                geometry=f'flat fabric; {direction} flow',
                scale_dimension_raw=f'width {width} cm; length {length} cm; thickness 0.37 mm',
                O2_value='', O2_basis='', diluent='', pressure_raw_value='', pressure_raw_unit='',
                gravity_level='microgravity', flow_regime='', flow_velocity_cm_s=flow,
                metric_name=metric, metric_value_raw=value, metric_uncertainty_raw='', metric_unit_raw=unit,
                measurement_method='NASA-reported Table I; not independently remeasured',
                source_paper='Results of Large-Scale Spacecraft Flammability Tests', source_page='29',
                curated_by='Codex_first_pass', verified_by='', verified_date='', doc_id='ntrs_20170008805',
                second_pass_agrees='',
                curation_notes='First-pass transcription. Pressure and uncertainty unreported here. Oxygen varies or is approximate: consult Table I footnote i. Forced flow is reported; laminar/turbulent classification is not established here.'))
    target = DATA / 'experiments_staging.csv'
    if target.exists():
        with target.open(encoding='utf-8-sig', newline='') as f:
            previous = list(csv.DictReader(f))
        serialized_rows = [{k: str(v) for k, v in row.items()} for row in rows]
        if previous and previous != serialized_rows:
            raise RuntimeError('Existing staging data differs; refusing to overwrite')
    write_csv(target, rows)
    qa = ROOT / 'tmp/pdfs'
    qa.mkdir(parents=True, exist_ok=True)
    for doc_id, number in [('ntrs_20210011385',104), ('ntrs_20170008805',29)]:
        with pymupdf.open(DATA / 'pdfs' / f'{doc_id}.pdf') as doc:
            doc[number-1].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(qa / f'{doc_id}_p{number}.png')
    print(f'Prepared {len(conditions)} BASS condition records and {len(rows)} Saffire measurements. Verification fields intentionally empty.')

if __name__ == '__main__':
    prepare()
