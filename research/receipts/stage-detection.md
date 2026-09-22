# Receipt: Stage Detection

- Date: 2026-09-22
- Source: `stage-detection.json`, `stage-detection-remaining.json`.
- Design: cache-bypass 30 repeats for near duplicates, winner variants, adversarial insertions and 5–1000 option scaling.
- Key observation: 10→250 near duplicates changed target mass 1.00→0.88 and p50 latency 282→338 ms.
- Key limit: 500/1000 choices returned HTTP 400 because the endpoint allows at most 255 choices.
- Interpretation: independent linear per-option inference weakened; staged reduction not proven.
