"""Fetch a bounded NASA combustion corpus with original metadata and SHA-256.

Only PUBLIC NTRS records are downloaded. NASA's copyright determination is
preserved verbatim; public access is never treated as public-domain status.
Existing unrelated metadata rows are preserved. No verification is fabricated.
"""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    '20210011385': 'BASS-II',
    '20150023456': 'FLEX',
    '20170008805': 'Saffire',
    '20180005168': 'Saffire',
    '20210017780': 'Saffire',
    '20220012861': 'Saffire',
}
FIELDS = ['doc_id', 'title', 'authors', 'year', 'campaign_or_series',
          'research_group_label', 'source_type', 'peer_reviewed', 'license_status',
          'source_url', 'ntrs_copyright_determination', 'sha256', 'retrieved_at']

def fetch(url):
    if not url.startswith('https://ntrs.nasa.gov/'):
        raise ValueError('Only official NTRS URLs are allowed')
    with urlopen(Request(url, headers={'User-Agent': 'CombustionLens-research-corpus/1.0'}), timeout=90) as response:
        return response.read()

def collect():
    data = ROOT / 'data'
    provenance = data / 'provenance'
    provenance.mkdir(parents=True, exist_ok=True)
    (data / 'pdfs').mkdir(exist_ok=True)
    (data / 'extracted').mkdir(exist_ok=True)
    meta_path = data / 'paper_meta.csv'
    existing = {}
    fields = list(FIELDS)
    if meta_path.exists():
        with meta_path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            fields = list(dict.fromkeys(fields + (reader.fieldnames or [])))
            existing = {r['doc_id']: r for r in reader}
    manifest = []
    failures = []
    for identifier, campaign in SOURCES.items():
        try:
            raw = fetch(f'https://ntrs.nasa.gov/api/citations/{identifier}')
            record = json.loads(raw)
            if record.get('distribution') != 'PUBLIC':
                raise ValueError('Record is not publicly distributed')
            downloads = [d for d in record.get('downloads', []) if d.get('mimetype') == 'application/pdf' and not d.get('draft')]
            if not downloads:
                raise ValueError('No public PDF')
            url = 'https://ntrs.nasa.gov' + downloads[0]['links']['pdf']
            content = fetch(url)
            if not content.startswith(b'%PDF-'):
                raise ValueError('Download is not a PDF')
            doc_id = f'ntrs_{identifier}'
            path = data / 'pdfs' / f'{doc_id}.pdf'
            path.write_bytes(content)
            (provenance / f'{doc_id}.json').write_bytes(raw)
            rights = record.get('copyright', {}).get('determinationType', 'UNKNOWN')
            # Do not equate GOV_PERMITTED or possible copyrighted content with public domain.
            status = 'public_use_permitted' if rights == 'PUBLIC_USE_PERMITTED' else 'unclear'
            authors = '; '.join(a.get('meta', {}).get('author', {}).get('name', '') for a in record.get('authorAffiliations', []))
            date = next((p['publicationDate'] for p in record.get('publications', []) if p.get('publicationDate')), '')
            row = dict(doc_id=doc_id, title=record['title'], authors=authors,
                       year=str(date)[:4], campaign_or_series=campaign,
                       research_group_label='unknown', source_type='flight', peer_reviewed='unknown',
                       license_status=status, source_url=f'https://ntrs.nasa.gov/citations/{identifier}',
                       ntrs_copyright_determination=rights, sha256=hashlib.sha256(content).hexdigest(),
                       retrieved_at=datetime.now(timezone.utc).isoformat())
            existing[doc_id] = row
            import pymupdf
            with pymupdf.open(path) as pdf:
                pages = [{'page': i+1, 'text': p.get_text()} for i, p in enumerate(pdf)]
            (data / 'extracted' / f'{doc_id}.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
            manifest.append({**row, 'pdf_url': url, 'bytes': len(content), 'pages': len(pages)})
            print(f'{doc_id}: {len(pages)} pages; {rights}', flush=True)
        except Exception as error:
            failures.append({'id': identifier, 'error': str(error)})
            print(f'{identifier}: FAILED: {error}', flush=True)
    with meta_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(existing.values())
    (provenance / 'collection_manifest.json').write_text(json.dumps({'sources': manifest, 'failures': failures}, indent=2), encoding='utf-8')
    return bool(failures)

if __name__ == '__main__':
    sys.exit(collect())
