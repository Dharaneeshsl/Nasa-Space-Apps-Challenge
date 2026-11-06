---
title: CombustionLens
emoji: 🛰️
colorFrom: red
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# CombustionLens

A source-linked research workspace for exploring NASA combustion findings and the limits of transferring them to spacecraft missions. Prepared for [Flame in Freefall](https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/).

## What works

- **Evidence explorer:** four curated NASA campaign summaries, searchable findings, explainable ranking, three mission contexts and downloadable research briefs. Runs without a backend or API key.
- **Mission applicability:** six physical boundary checks that distinguish broad alignment, mismatch and unknown conditions, plus exportable research questions.
- **Research backend:** document retrieval, cross-encoder reranking, page-level citations, numerical checks, optional model synthesis and labeled source-excerpt fallback.
- **Verified comparator:** only independently verified experiment records are eligible. The current collection has zero verified rows, so the empty comparator is intentional.

This is a research prototype, not a flight-qualified fire-safety tool. Ranking scores are not probabilities. No NASA endorsement or independent scientific validation is claimed.

## Current evidence and checks

Six NTRS reports were collected (549 pages); three public-use-permitted reports supply 457 indexed passages. There are 31 BASS condition records and eight unverified Saffire measurements. A small development benchmark achieved 8/8 development and 7/8 held-out gate classifications; this does not measure scientific answer accuracy.

See [submission status](docs/SUBMISSION_STATUS.md) for the latest check results and outstanding requirements, [NASA collection](docs/NASA_COLLECTION.md) for provenance, [demo](docs/DEMO.md) for the walkthrough, and [pitch](docs/PITCH.md) for the presentation story.

## Run the explorer

```sh
cd frontend
npm ci
npm run dev
```

Open the local address printed by Vite. Original NASA links require internet access.

## Run the full application

Use Python 3.11 or newer with the dependencies in `requirements.txt`.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/collect_nasa_data.py
python scripts/prepare_nasa_tables.py
python scripts/load_experiments.py
python scripts/build_index.py
python scripts/validate_data.py
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn api.main:app --host 127.0.0.1 --port 7860
```

Open http://localhost:7860. API documentation is at `/docs`. PDF downloads, local databases and vector indexes are intentionally excluded from Git and must be regenerated on another machine. See `.env.example` for optional generation settings; never commit credentials.

Model loading needs sufficient available memory. On constrained machines, set `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to `1` before starting the backend or running its tests.

## Checks

```sh
python -m pytest tests -q
cd frontend
npm test
npm run build
```

Frontend tests use one worker to avoid exhausting memory on demo laptops. Backend integration tests load real models and need the model files and sufficient memory.

## Docker

```sh
docker build -t combustionlens .
docker run -p 7860:7860 combustionlens
```

The image build downloads the NASA corpus and models. It requires network access and a working Docker engine. A successful local frontend build is not evidence of a tested public deployment.

## License and sources

Application code: [MIT](LICENSE). NASA source provenance and original rights determinations are preserved in `data/provenance/`. Public accessibility alone is not treated as permission to index a report. See [data sources](docs/data_sources.md).
