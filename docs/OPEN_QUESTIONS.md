# Jev Open Questions

## Known

- Jev exposes typed decision outputs.
- Dynamic options and semantic labels are supported.
- Semantic competitors redistribute output probability.
- Moderate option growth does not cause naïve linear latency growth in the measured range.
- The API enforces a maximum of 255 choices in tested calls.
- Negation and semantic collisions can cause high-confidence failures.

## Likely

- A shared representation is reused across batched questions.
- Options are represented semantically rather than as fixed indices.
- A ranking-like or competition layer exists above representation encoding.
- The output layer has decision-type-specific behavior.

## Speculative

- Cluster-aware filtering or retrieval occurs internally.
- A top-k candidate set is reranked.
- The training objective includes calibration or preference optimization.
- A parallel sampler is a named architectural component rather than provider batching.

## Unknown

- Backbone family and size.
- Weight sharing between state and options.
- Exact latent-space geometry.
- Exact loss, data mixture and RLCD implementation.
- Internal attention, retrieval, cache and sampler details.
- Production-domain failure rates.

## What black-box testing cannot establish alone

Without weights, traces, controlled ablations or source access, behavioral tests
cannot uniquely identify the backbone, training objective or the exact number of
forward passes. Multiple architectures can implement the same input/output
mapping. These limits are part of the result, not a research failure.
