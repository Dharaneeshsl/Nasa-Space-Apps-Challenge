# CombustionLens — submission text

## Project summary

CombustionLens helps researchers explore NASA microgravity combustion findings and understand where they apply to future missions. Its interactive evidence explorer links four campaign summaries to NASA sources, explains their ranking, and separates published observations from team interpretations. Mission applicability checks gravity, fuel class, oxygen, pressure, ventilation and geometry, making missing evidence visible before a finding is transferred to a spacecraft scenario.

## Problem and solution

A combustion finding can be relevant without matching a mission's physical conditions. CombustionLens connects source discovery to a practical next research question. Users select orbital, lunar or Mars-transit contexts, search findings, inspect transferability boundaries and export source-linked briefs. A separate research backend retrieves indexed reports, reranks passages and provides page citations with numerical checks.

## NASA data

The project uses public NASA campaign information and original NASA Technical Reports Server reports. Six reports were collected, totaling 549 pages. Three explicitly public-use-permitted reports provide 457 indexed passages. Original record URLs, rights determinations and download hashes are retained. Four curated explorer summaries cover BASS, FLEX, Saffire VI and SoFIE-GEL.

## Implementation and results

React and TypeScript power the interface. Python/FastAPI, ChromaDB, sentence-transformer retrieval, cross-encoder reranking and DuckDB support the research backend. The explorer and mission-boundary checks operate deterministically without an API key. Optional model synthesis has a labeled source-excerpt fallback.

Local validation: 68 backend tests, 20 frontend tests and the production frontend build passed. Desktop Chrome review covered the explorer, mission applicability and the comparator empty state. A small retrieval-development benchmark recorded 8/8 development and 7/8 held-out gate classifications; these are not scientific answer-accuracy measurements.

## Scope and next steps

This is a solo-developed research prototype. Eight staged Saffire measurements await independent review and remain excluded from numerical comparison. The prototype does not predict fire risk or provide flight-qualified operating limits. Future work includes independently reviewed run-level records, broader evaluation and deployment validation.

## Repository

https://github.com/Dharaneeshsl/Nasa-Space-Apps-Challenge

## Before pressing Submit

Use the actual portal's field names and limits. Confirm the repository includes the current working changes and is accessible to judges. Add the actual demo link or recording if requested, and check the event's eligibility and deadline. No public demo URL or recording is asserted here.

## Use of AI tools

Codex assisted with software development, documentation, source collection and automated checks. The researcher must review scientific interpretations and submitted claims. The running backend uses sentence-transformer embeddings and a cross-encoder for retrieval and ranking. An external generative model is optional and is currently unconfigured; without it, the backend returns labeled source excerpts. The four-card explorer uses curated summaries and deterministic ranking.

## References

- NASA Technical Reports Server: https://ntrs.nasa.gov/ (original report IDs, rights records and hashes: data/provenance/collection_manifest.json).
- NASA, Studying Combustion and Fire Safety: https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/
- NASA, You're Hot Then You're Cold: https://www.nasa.gov/missions/station/iss-research/youre-hot-then-youre-cold/
- NASA, Flame Burns Out on NASA's Long-Running Spacecraft Fire Experiment: https://www.nasa.gov/centers-and-facilities/glenn/flame-burns-out-on-nasas-long-running-spacecraft-fire-experiment/
- NASA Science, SoFIE-GEL: https://science.nasa.gov/biological-physical/investigations/sofie-gel/
