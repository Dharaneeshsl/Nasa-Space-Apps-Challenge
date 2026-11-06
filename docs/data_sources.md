# CombustionLens: Data Sources & Accessibility Audit

Current collection: see [NASA_COLLECTION.md](NASA_COLLECTION.md) and `data/provenance/collection_manifest.json` for actual downloaded records, rights determinations, hashes and integration limits. The historical planning notes below predate this collection. The ingestion policy now distinguishes explicit NTRS public-use permission from public-domain status.

> [!NOTE]
> All URLs, API endpoints, and license claims below are preliminary working notes and are marked **not verified** until verified against official NASA Space Apps Challenge releases.

## 1. NASA Technical Reports Server (NTRS)
- **Base URL:** `https://ntrs.nasa.gov` *(to be verified upon challenge release)*
- **API Availability:** REST API endpoints (`/api/citations/search`) *(not verified)*
- **License / Copyright Rule:** Works created exclusively by US federal employees within official duties are in the public domain in the United States. Works with contractor, university, or foreign co-authors require case-by-case review. **Strict Rule:** Only papers verified with `license_status = public_domain_confirmed` in `paper_meta.csv` are indexed.
- **Access Protocol:** Batch query and download via official API or manual curation *(to be verified)*.

## 2. Physical Sciences Informatics (PSI)
- **Base URL:** `https://psi.nasa.gov` *(to be verified)*
- **Accessibility Status:** Under audit per flight campaign (e.g., FLEX, BASS, Saffire, ACME) *(not verified)*.
- **Usability Assessment:** Format and schema feasibility must be evaluated directly on released files *(not verified)*.
