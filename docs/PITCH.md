# CombustionLens: judge-facing story

## Opening (20 seconds)

“A combustion finding can be correct and still be wrong for your spacecraft. Different gravity, fuel geometry, atmosphere or ventilation can make the transfer invalid. CombustionLens makes those boundaries visible.”

## Product demonstration (two minutes)

1. Toggle Earth and microgravity in the conceptual flame illustration. Explain that it teaches the question, not a quantitative simulation.
2. Prioritize detection in the explorer. Show the FLEX finding, its source, the team interpretation and its limitation.
3. Open mission applicability for the Moon. Show how a droplet result differs from a solid-material scenario, and how lunar gravity differs from microgravity.
4. Enter atmosphere values. Show that oxygen and pressure cells remain unknown: user inputs cannot manufacture matching evidence.
5. Export the assessment and an evidence brief. Both carry their limitations and source links.

## Architecture (30 seconds)

The local explorer and boundary checks are deterministic. The separate research backend implements dense retrieval, cross-encoder reranking, optional language-model synthesis, citation validation, numerical checks and a verified-record comparator. Clearly distinguish this implemented architecture from a calibrated, populated and evaluated deployment.

## Why this matters (20 seconds)

The useful output is not merely a summary. It is an auditable explanation of what the evidence says, where transfer fails, and which experimental conditions the next research request must establish.

## Claims to avoid

- Do not call editorial relevance scores probabilities or confidence.
- Do not describe unknown conditions as safe.
- Do not claim four campaign summaries are a comprehensive dataset.
- Do not claim NASA endorsement, operational validation or measured AI accuracy without evidence.

## Highest-value remaining submission work

Curate primary publications, independently verify experiment rows, calibrate the refusal threshold, evaluate on held-out questions, and record the actual workflow. These are substantive research milestones, not cosmetic finishing tasks. Confirm event requirements with the organizers before submission.
