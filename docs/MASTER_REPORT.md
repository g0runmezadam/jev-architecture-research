# Jev Black-Box Research Archive — Master Report

Status: completed evidence archive, 2026-09-22

## Evidence convention

- **Observed:** directly measured in a recorded Jev/API call or reproducible local run.
- **Inferred:** an explanation supported by multiple observations, but not directly visible inside the model.
- **Speculative:** a plausible mechanism without discriminating evidence.

## Executive Summary

**Observed.** Jev accepts dynamic option sets and typed decision requests (`choice`, `score`, `noul`). It follows semantic labels through permutation, redistributes probability among related options, preserves ambiguity in selected cases, saturates quickly when evidence is repeated, and answers batched questions with sub-linear total latency in the measured range. In the final controlled 250-option experiment, the intended target won all 720 repetitions and the intended semantic cluster won all 720.

**Inferred.** The most economical behavioral family is a shared state/option representation with a semantic competition or ranking-like decision layer, typed heads, and batch-aware inference. A weak presentation/order effect exists, but no strong cluster-position signature was found.

**Speculative.** The system may use a top-k, retrieval, reranking, or provider-side batching stage. The evidence cannot identify a backbone, RLCD loss, internal sampler, or exact latent geometry.

## Timeline of Discoveries

1. **2026-09-21 — Baseline setup:** Jev and local Laya were run through the same harness on an RTX 3060 Ti 8 GB system.
2. **Baseline comparison:** Jev 23/23 on the initial 23 checks; Laya variants lower but much faster. This established behavioral contrast, not architecture.
3. **150-case deep suite:** Jev 150/150, Brier 0.0030, ECE 0.0477; synthetic deterministic labels, not production calibration proof.
4. **Architecture probes:** label permutation, option cardinality, decoys, noul inversion and question scaling weakened fixed-index classifier explanations.
5. **Score/determinism:** score tracked expected probability value; Jev rejected more than ten score levels at the API boundary; repeated requests were deterministic in the tested sample.
6. **Latency surface:** Jev question batching was sub-linear in the measured 1–100 question range; payload and output limits remained visible.
7. **Training-signal probes:** feature changes, evidence accumulation, contradiction and semantic collisions revealed anchor-sensitive decisions and localized failures.
8. **Semantic geometry:** probability did not follow a smooth one-dimensional semantic-distance decay; threshold-like/anchor-sensitive regions appeared.
9. **Stage detection:** near-duplicate growth redistributed mass and increased entropy modestly; exact and paraphrase duplicates exposed tie-break/anchor effects; 500/1000 options hit the 255-choice API limit.
10. **Final attribution:** 720 cache-bypass calls with randomized IDs, equal-length templates, 10 clusters and 4 layouts found 720/720 target winners and no strong cluster-position effect.

## Key Experiments

| Experiment | Main observation | Source |
|---|---|---|
| Label permutation | Semantic target followed reordered labels | `architecture-probes-short.json` |
| Option cardinality | Jev remained stable through 255 options; Laya hit its own head limit earlier | `architecture-probes-scaling.json` |
| Question scaling | Jev total latency did not grow linearly from 1 to 100 questions | `architecture-probes-scaling.json`, `latency-surface-bounded.json` |
| Score inversion | Jev followed semantic ordinal reversal in the controlled test | `score-probes.json` |
| Near-semantic decoys | Related candidates redistributed probability sharply | `behavioral-research-probes.json`, `semantic-decision-geometry.json` |
| Failure probes | Negation, collision and sarcasm produced high-confidence failures | `manifold-language-probes.json`, `behavioral-research-probes.json` |
| Near-duplicate explosion | 10→250 duplicates: target mass 1.00→0.88; p50 282→338 ms | `stage-detection.json` |
| Final cluster attribution | 720/720 target winners; cluster mass about .981–.998 by layout | `final-pipeline-attribution.json` |

## Architecture Attribution

### Most likely family

**Inferred, high confidence:**

```text
Shared state/option representation
        + dynamic semantic option encoding
        + joint semantic competition or ranking-like layer
        + typed choice/score/noul heads
        + threshold/anchor-sensitive probability output
        + batched multi-question inference
```

### Pipeline attribution

**Inferred, medium confidence:** global joint semantic scoring is the simplest
explanation of the final controlled experiment. **Weakly inferred:** a hidden
top-k, retrieval, or reranking stage remains possible but was not required by
the observed cluster-position behavior.

### Confidence snapshot

These are research weights, not statistical probabilities:

| Explanation | Weight |
|---|---:|
| Global joint semantic scoring | 70% |
| Candidate reduction + reranking | 10% |
| Cluster-aware filtering | 8% |
| Order-sensitive staging | 12% |

## Supported Hypotheses

- Dynamic semantic option encoding — **high**.
- Shared or batch-aware state representation — **high**.
- Typed decision heads — **high**.
- Semantic competition/ranking-like decision layer — **medium-high**.
- Ambiguity and confidence geometry are decision-dependent — **medium-high**.
- Evidence saturation — **medium**.
- Weak order/presentation bias — **low-medium**.

## Rejected or Strongly Weakened Hypotheses

- Pure label-index classifier.
- Fixed output head requiring a predeclared class list.
- Simple independent softmax routing.
- Pure accuracy-only explanation.
- Strictly linear, independent forward pass per option/question.
- Strong cluster-first filtering as a necessary part of the final decision.

“Rejected” means not a credible complete explanation of the observations; it does
not mean mathematically impossible inside a black box.

## Open Questions

- Does an internal top-k stage exist even when it leaves cluster mass unchanged?
- Is duplicate behavior caused by semantic anchors, parser order, or tie-breaking?
- Is calibration learned, post-processed, or provider-side?
- What is the backbone and whether state/options share weights?
- What is the actual multi-question sampler/batching implementation?
- How much of the observed behavior survives natural, non-synthetic data?

## Future Research Directions

1. Equal-length random-ID cluster experiment with target positions 1/5/25 and independent option-order controls.
2. Provider/API ablations if an official raw endpoint or local implementation becomes available.
3. User-labeled minimal-pair boundary sets rather than subjective synthetic labels.
4. Surrogate-model comparison only on independently labeled data and under applicable provider terms; do not train on restricted provider output.

## Reproducibility

The raw JSON files live in `clduab11-jev-test/results/`. Scripts live in
`clduab11-jev-test/scripts/`. Experiment assumptions, caveats and timestamps are
indexed in `research/receipts/`. The archive intentionally preserves API-limit
failures as evidence rather than treating them as model behavior.
