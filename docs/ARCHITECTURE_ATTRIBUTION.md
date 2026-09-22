# Jev Architecture Attribution

## Most likely architecture family

**Observed:** Jev accepts dynamic choices, score levels and noul questions;
semantic options influence probability; batches of questions are processed with
sub-linear total latency in the measured range.

**Inferred:**

```text
Shared state representation
  + dynamic semantic option representation
  + semantic competition / ranking-like decision space
  + typed choice, score and noul heads
  + threshold/anchor-sensitive probability output
  + batch-aware multi-question inference
```

## Most likely pipeline

The simplest current pipeline is:

1. Encode the state once or in a shared batch representation.
2. Encode options as semantic candidates rather than class indices.
3. Compare candidates in a shared decision/ranking space.
4. Apply a typed head for choice, ordinal score or noul.
5. Return a calibrated-looking probability distribution and decision.

This is an inference, not an observed internal trace.

## Competing explanations

### Global joint scoring — best supported

Near-duplicates redistribute mass; randomized cluster layouts preserve the target
cluster and target winner; target ID is randomized; no strong layout latency
signature appears.

### Candidate reduction + reranking — possible, not required

Latency plateaus and stable cluster mass are compatible with a top-k stage. The
final test did not expose it because a hidden stage could preserve the correct
cluster.

### Hierarchical filtering — weakly supported

Cluster mass stability and intra-cluster effects are compatible, but cluster
position did not produce the expected strong signature.

### Order-sensitive decision pipeline — secondary effect

Target position 1 had a small probability penalty, but winner stability was
perfect. This is more consistent with a weak presentation/tie-break effect than
with a dominant pipeline stage.

## Confidence estimates

| Explanation | Estimate | Why |
|---|---:|---|
| Global joint semantic scoring | 70% | Best fit to randomized 720-call test and duplicate mass behavior |
| Candidate reduction + reranking | 10% | Possible from latency plateau, not required by controlled layout test |
| Cluster-aware filtering | 8% | Cluster mass is stable; no strong cluster-position effect |
| Order-sensitive staging | 12% | Small target-position effect, no winner instability |

These are qualitative research weights, not statistical posterior probabilities.

## What remains unknown

- Backbone model and parameterization.
- Whether state and options share weights.
- Exact ranking loss or pairwise objective.
- Source of confidence calibration.
- Internal top-k/retrieval/batching implementation.
- Whether the 255 limit is endpoint-only.

## Evidence that would change the result

The attribution would move toward filtering/reranking if randomized equal-length
IDs caused systematic cluster-position changes in cluster mass, or if target
probability stayed fixed for all but a small active subset while latency scaled
with that subset. It would move toward a stronger order-sensitive pipeline if
identical semantic candidates systematically changed winner by position across
independent ID randomizations.
