# Research Archive Receipts

Archive created: 2026-09-22
Environment: Windows, local RTX 3060 Ti 8 GB, Jev API `jev-1.13.0`, local Laya
comparison environment under `D:\jev-benchmark`.

## Receipt rules

- Raw outputs are preserved under `clduab11-jev-test/results/`.
- Local cache was bypassed explicitly for final 30-repeat and 720-call studies.
- API failures are preserved as observations, not silently dropped.
- Synthetic labels and wording are marked as such.
- No provider output was used to train a surrogate model.
- Every conclusion separates observation from inference and speculation.

## Experiment registry

| Receipt | Experiment | Inputs | Repetitions | Main caveat |
|---|---|---|---:|---|
| `baseline-and-deep.md` | 17-case, 150-case Jev/Laya comparison | Controlled benchmark cases | 1 suite each | Not production accuracy |
| `architecture-probes.md` | Permutation, cardinality, decoy, inversion, question scaling | Dynamic options/questions | Varies | API and prompt effects |
| `score-latency.md` | Score sweep, determinism, latency surface | 2–100 score levels; bounded grids | Varies | Endpoint limits and cold starts |
| `geometry-failure.md` | Semantic geometry and failure surface | Synthetic controlled states | Varies | Subjective labels, small language set |
| `stage-detection.md` | Near duplicates, adversarial candidates, scaling | 5–250 options; 30 repeats | 30/condition | 255-choice API limit |
| `final-pipeline.md` | Cluster position and target position | 10×25 options, 4 layouts | 720 total | Equal template controls; API remains black box |

## Reproduction

Scripts corresponding to the final attribution are:

- `clduab11-jev-test/scripts/behavioral_research_probes.py`
- `clduab11-jev-test/scripts/semantic_decision_geometry.py`
- `clduab11-jev-test/scripts/stage_detection.py`
- `clduab11-jev-test/scripts/cluster_duplicate_attribution.py`
- `clduab11-jev-test/scripts/final_pipeline_attribution.py`

The API key is intentionally not stored in this archive. Reproduction requires
the operator's environment configuration and an applicable provider account.
