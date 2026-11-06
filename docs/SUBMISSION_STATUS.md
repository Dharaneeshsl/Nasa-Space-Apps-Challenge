# Submission candidate status — November 6, 2026

## Latest verified results

- Backend: **68 passed**, one dependency deprecation warning. Run with OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1 and MKL_NUM_THREADS=1. An earlier unbounded run exhausted Windows paging memory; the complete bounded rerun passed.
- Frontend: **20 passed** across eight files. Test workers are now limited to one after the initial parallel run exhausted memory.
- Production frontend build: passed.
- Chrome: homepage and mission-applicability page rendered and navigation succeeded. Footer connected to the running API and displayed three papers, zero verified rows and the development calibration status. This is a limited desktop review, not a comprehensive mobile/export/browser test.
- Docker engine: installed but its info request returned HTTP 500. A Docker image build and public deployment remain unverified.
- NASA corpus: six downloaded reports (549 pages); three permitted reports indexed as 457 passages. Source-file hash test passed.
- Structured data: 31 BASS condition records and eight staged Saffire measurements; zero independently verified measurements.
- Retrieval benchmark: 8/8 development and 7/8 held-out gate classifications, threshold 3.9973. These are development results, not independently validated scientific accuracy.

## Remaining submission requirements

1. Confirm the team's official event, eligibility, deadline and required deliverables in the submission portal. The official Flame in Freefall search result matches the project theme, but fetching its full statement returned HTTP 502. Challenge fit alone does not establish submission compliance.
2. Prepare and check the actual submission entry and demo recording; neither is established by local tests.
3. Verify a deployment accessible to judges, if required by the event. No public deployment has been verified here.
4. Independently review the staged experimental measurements before advertising or enabling verified numerical comparison. Until then, demonstrate the explorer and applicability workspace and disclose the comparator's empty state.

Official challenge: https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/

The prototype can be demonstrated locally. An unconditional final submission-ready confirmation is not supported until the external requirements above are resolved. No flight qualification, NASA endorsement or award outcome is claimed.
