"""Small, first-pass corpus-specific gate check, not a scientific accuracy benchmark.

Fits only on explicit dev rows. Held-out rows never influence the threshold.
Gold labels were prepared by the project agent and require independent review.
"""
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(key, '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    import torch
    torch.set_num_threads(1)
    import yaml
    from core.retrieval import retrieve_candidates
    path = ROOT / 'eval/nasa_retrieval_benchmark.csv'
    rows = list(csv.DictReader(path.open(encoding='utf-8', newline='')))
    results = []
    for row in rows:
        response = retrieve_candidates(row['question'])
        nearest = response.get('nearest_documents', [])
        results.append(dict(id=row['id'], split=row['split'], question=row['question'],
            answerable=row['category'] == 'factual', top_logit=response.get('top_logit'),
            gold_doc=row['gold_citation_paper'], gold_page=row['gold_citation_page'],
            retrieved=[{'doc_id':c['doc_id'], 'page':c.get('page_number')} for c in nearest]))
        print(row['id'], results[-1]['top_logit'], flush=True)
    dev = [r for r in results if r['split'] == 'dev']
    thresholds = sorted({r['top_logit'] for r in dev if r['top_logit'] is not None})
    if not thresholds:
        raise RuntimeError('No development retrieval scores')
    thresholds += [min(thresholds)-.01, max(thresholds)+.01]
    def score(tau):
        positive = [r for r in dev if r['answerable']]
        negative = [r for r in dev if not r['answerable']]
        return .5 * sum(r['top_logit'] is not None and r['top_logit'] >= tau for r in positive)/len(positive) + .5 * sum(r['top_logit'] is None or r['top_logit'] < tau for r in negative)/len(negative)
    tau = max(thresholds, key=lambda t: (score(t), t))
    for row in results:
        row['accepted'] = row['top_logit'] is not None and row['top_logit'] >= tau
        row['gate_correct'] = row['accepted'] == row['answerable']
        row['gold_page_in_top5'] = any(c['doc_id'] == row['gold_doc'] and str(c['page']) == row['gold_page'] for c in row['retrieved']) if row['answerable'] else None
    report = dict(method='First-pass development gate calibration; not independently reviewed',
        benchmark_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), tau_ce=tau,
        dev_balanced_accuracy=score(tau), results=results)
    target = ROOT / 'eval/nasa_retrieval_results.json'
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    # Store as a development threshold, never claim independent scientific validation.
    config_path = ROOT / 'config.yaml'
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    config['retrieval']['tau_ce'] = tau
    config['retrieval']['calibration_status'] = 'development_only_pending_independent_review'
    config['evaluation']['split_seed'] = 42
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    print('Saved', target, 'development tau:', tau, flush=True)

if __name__ == '__main__':
    main()
