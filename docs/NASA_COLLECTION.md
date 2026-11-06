# NASA collection status

Collected November 6, 2026, from NASA Technical Reports Server (NTRS).

| NTRS ID | Campaign | PDF pages | Original copyright determination | Indexed |
|---|---|---:|---|---|
| 20210011385 | BASS-II summary report | 144 | GOV_PERMITTED | No; rights review pending |
| 20150023456 | FLEX detailed results | 314 | PUBLIC_USE_PERMITTED | Yes |
| 20170008805 | Saffire flammability results | 36 | PUBLIC_USE_PERMITTED | Yes |
| 20180005168 | Saffire overview | 32 | PUBLIC_USE_PERMITTED | Yes |
| 20210017780 | Saffire IV/V | 14 | MAY_INCLUDE_COPYRIGHT_MATERIAL | No |
| 20220012861 | Flame temperature pyrometry | 9 | MAY_INCLUDE_COPYRIGHT_MATERIAL | No |

## Files and integration

- `data/pdfs/ntrs_<id>.pdf`: six original downloads, 549 total PDF pages. These binaries are Git-ignored; run the collector when preparing another checkout or deployment.
- `data/provenance/ntrs_<id>.json`: original, unmodified NTRS API responses.
- `data/provenance/collection_manifest.json`: URLs, SHA-256 hashes, original rights determinations and download results.
- `data/paper_meta.csv`: ingestion metadata. Publication years come from publication records. Peer-review and independent research-group labels remain unknown rather than assumed.
- `data/index/`: 457 indexed passages from three public-use-permitted reports. Indexes are Git-ignored and must be rebuilt for deployment.
- `data/bass_test_conditions.csv`: 31 first-pass condition rows from Table 7.1, PDF page 104 (printed page 96). Flow ranges, comments and the two unreliable oxygen-reading footnotes are preserved. These are conditions/outcomes, not invented spread-rate measurements.
- `data/experiments_staging.csv`: eight first-pass measurements from Saffire Table I, PDF page 29: spread rate and burn duration for samples 1-1, 1-2, 2-5 and 2-6. Pressure, uncertainty and the laminar/turbulent classification remain unspecified. Approximate or varying oxygen values were not flattened into exact values.
- `data/nasa_collection.duckdb`: eight staged rows, zero independently verified rows. The original `data/experiments.duckdb` is preserved because the installed DuckDB cannot read its newer storage version. Configuration points at the new database.

The ingestion gate now recognizes explicitly documented NTRS public-use permission separately from public-domain status. GOV_PERMITTED and potentially copyrighted documents are not indexed automatically. Public access alone never clears the gate.

## Reproduce

Use a Python environment with the project dependencies installed. From the repository root:

```powershell
python scripts/collect_nasa_data.py
python scripts/prepare_nasa_tables.py
python scripts/load_experiments.py
python scripts/build_index.py
python scripts/validate_data.py
```

The table preparer refuses to overwrite differing existing experiment rows. Review and merge existing curation deliberately. Original raw imagery in `datasets/` was preserved; it was not treated as calibrated physical measurements. The collector obtains published NASA reports and their tables, not a bulk mirror of the PSI repository.

## Remaining verification

Focused validation: 41 tests passed across collection integrity, source links, ingestion, unit conversion, comparison, evidence classification and numerical guardrails. This is not a full end-to-end test-suite result.

An independent reviewer must check the eight staged measurements and their experimental conditions before setting `verified_by`, `verified_date` and agreement fields. Compare intentionally exposes no verified rows until that happens. Do not invent reviewer identities or assume missing experimental conditions.

The historical `eval/questions.csv` contains answers and paper titles that have not been established against this collection. It was preserved and was not used for calibration. `eval/nasa_retrieval_benchmark.csv` contains 16 corpus-specific, first-pass questions with explicit dev/held_out splits. The development-only threshold is 3.9973 (8/8 development gate classifications; 7/8 held-out classifications). This small benchmark and its labels need independent review; results do not measure scientific answer accuracy. Results and source-page retrieval checks are recorded in `eval/nasa_retrieval_results.json`. Threshold selection used development rows only; the held-out failure was retained. The generator is intentionally optional: without an API key/model the app uses labeled deterministic source excerpts.

Structural validation passed (six PDFs, six metadata entries, no orphan files or invalid categories; eight staged rows). The latest complete backend run passed all 68 tests with bounded CPU settings after an earlier run exhausted Windows paging memory. The retrieval smoke result is saved at `data/provenance/retrieval_smoke.json`; it checks pipeline execution, not answer accuracy. Development calibration is recorded above. Dataset collection does not establish flight safety or submission compliance. See [current submission status](SUBMISSION_STATUS.md).

