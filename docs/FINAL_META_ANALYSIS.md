# Final Meta Analysis

## What do we actually know?

**Observed:** Jev is a dynamic typed decision service whose outputs depend on
semantic option descriptions, not only option index. It supports choice, score
and noul tasks, shows joint competition among related options, and exhibits
shared/batched latency behavior. The final controlled 250-option study produced
720/720 target winners and no strong cluster-position effect.

## What do we only suspect?

**Inferred:** Jev likely uses a shared state/option representation and a
ranking-like decision space with typed heads. Global joint scoring is the most
parsimonious pipeline explanation. A weak order/presentation bias is plausible.

**Speculative:** retrieval, top-k reduction, reranking, RLCD training, a
parallel sampler, and any named backbone.

## What can never be known from this black box alone?

The exact weights, training data, internal representations, loss function,
forward-pass count and provider-side batching are not identifiable from outputs
alone. They require access to traces, source, weights, or carefully designed
interventions unavailable at the endpoint.

## Strongest conclusions

1. Jev is not adequately explained by a fixed label-index classifier.
2. Dynamic semantic option use is strongly supported.
3. Joint semantic competition and typed decision heads are strongly supported behaviorally.
4. A shared/batch-aware inference path is strongly supported behaviorally.
5. Global joint semantic scoring is the best current pipeline explanation, but not a proof of single-stage internals.

## Weakest conclusions

- The identity of the backbone.
- The presence or absence of RLCD.
- The exact calibration mechanism.
- Retrieval or reranking as a hidden stage.
- Any claim that the behavioral graph equals a latent embedding map.

## Single best explanation

```text
shared state/option encoder
  + global semantic competition space
  + ranking-like typed decision layer
  + choice/score/noul heads
  + context-sensitive confidence output
  + batch-aware inference
```

This is a behavioral family attribution, not a recovered implementation.
