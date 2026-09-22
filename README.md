# Jev Architecture Research

> Black-box reverse engineering of the Jev decision model.

**Website:** [jev.com.tr](http://jev.com.tr/) · **Research archive:** [`docs/MASTER_REPORT.md`](docs/MASTER_REPORT.md)

This repository is an evidence-first archive of experiments that study Jev as a
black-box decision system. It is not a leaderboard and does not claim access to
Jev's weights, training data, source code or internal traces.

## Current conclusion

The strongest behavioral attribution is:

```text
Shared state/option representation
  + dynamic semantic option encoding
  + global semantic competition
  + typed choice/score/noul heads
  + ranking-like decision layer
  + batch-aware inference
```

The final 720-call controlled cluster experiment favored global joint semantic
scoring over strong cluster-first filtering. Hidden provider batching, top-k
reduction, reranking, the backbone and the training objective remain unresolved.

## Navigate the archive

| Document | Purpose |
|---|---|
| [Master report](docs/MASTER_REPORT.md) | Full timeline and synthesis |
| [Evidence matrix](docs/EVIDENCE_MATRIX.md) | Claim → evidence → caveats |
| [Hypothesis tracker](docs/HYPOTHESIS_TRACKER.md) | Status and confidence updates |
| [Architecture attribution](docs/ARCHITECTURE_ATTRIBUTION.md) | Competing pipeline explanations |
| [Failure surface](docs/FAILURE_SURFACE.md) | Negation, contradiction, collision and language failures |
| [Latency analysis](docs/LATENCY_ANALYSIS.md) | Scaling and complexity limits |
| [Calibration analysis](docs/CALIBRATION_ANALYSIS.md) | Brier, ECE and confidence behavior |
| [Open questions](docs/OPEN_QUESTIONS.md) | Known, likely, speculative and unknown |
| [Final meta-analysis](docs/FINAL_META_ANALYSIS.md) | What black-box evidence can and cannot establish |
| [Machine-readable KB](research/knowledge_base.json) | Structured claims and counterarguments |
| [Experiment receipts](research/receipts/) | Reproducibility metadata and caveats |

## Evidence discipline

Every conclusion is marked as observed, inferred or speculative. Synthetic
labels are not treated as production accuracy. API limits are preserved as
limits, not converted into model claims. Provider output is not used to train a
surrogate model in this repository.

## Reproducing the probes

The original scripts and curated result files are under
[`research/experiments/`](research/experiments/). Reproduction requires an
applicable Jev API account and an environment variable for the key; secrets are
never committed. See the receipts before running a costly or rate-limited probe.

## Citation

```bibtex
@misc{jev_architecture_research_2026,
  title  = {Jev Architecture Research: A Black-Box Reverse-Engineering Archive},
  author = {Şahin, Tunahan},
  year   = {2026},
  url    = {https://github.com/g0runmezadam/jev-architecture-research}
}
```

## License

Code and experiment scripts are MIT licensed. Research notes and curated data
are CC BY 4.0; see [`LICENSE`](LICENSE) and [`DATA-LICENSE.md`](DATA-LICENSE.md).
