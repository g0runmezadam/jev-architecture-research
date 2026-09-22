# Jev Evidence Matrix

| Claim | Evidence | Source experiment | Confidence | Alternative explanations |
|---|---|---|---|---|
| Dynamic semantic option encoding | Label permutation; semantic decoys; near-duplicate competition | Architecture probes, semantic geometry, stage detection | High | Prompt wording, option descriptions, hidden fixed ontology |
| Options compete jointly | Related candidates redistribute probability; entropy rises with duplicates | Behavioral probes, semantic geometry, stage detection | Medium-high | Top-k/reranking, anchor matching |
| Shared state/batch representation | 1→100 question latency is sub-linear in measured range | Question scaling, latency surface | High behavioral / medium architectural | Provider batching, caching, endpoint scheduling |
| Typed decision heads | Choice, score and noul have different schemas and behavior | Deep suite, score probes | High behavioral | One universal head with API adapters |
| Ordinal score behavior | Score inversion; expected-value relation | Score probes, score sweep | Medium-high | Post-processing from a categorical distribution |
| Ambiguity is sometimes preserved | Close candidates split mass; severe ambiguity raises entropy | Training-signal, geometry, calibration probes | Medium-high | Confidence heuristic or output calibration layer |
| Evidence saturates | 1→20 evidence examples rapidly approach a plateau | Training-signal probes | Medium | Prompt redundancy and semantic repetition |
| Deterministic inference in tested conditions | 30-repeat exact request distributions were identical in earlier study | Score/determinism probes | Medium | Deterministic API wrapper or fixed seed |
| Smooth semantic distance is not supported | Distance chain was non-monotonic; anchors dominated | Semantic geometry | Medium-high | Poorly controlled descriptions; lexical anchors |
| Strong cluster filtering is not required | 720/720 target and cluster winners; cluster mass layout-stable | Final pipeline attribution | Medium-high | Hidden top-k preserving target cluster |
| Weak order sensitivity exists | Target position 1 had lower mean target mass, but never lost | Final pipeline attribution | Low-medium | Remaining wording/serialization or ID effects |
| Calibration is imperfect | Negation and collision yielded high-confidence errors | Failure probes, deep suite | High | Subjective gold labels in synthetic cases |
| Jev is not a fixed-index classifier | Dynamic option sets, permutation robustness, 255 option behavior | Architecture probes | High | Flexible wrapper around a fixed semantic ontology |
| Laya is not a behavioral twin | Large differences in multilingual, score and negation behavior | Deep Laya comparison | Medium | Prompt/checkpoint mismatch |

Confidence labels are qualitative and explain the strength of replication,
control, and alternative explanations; they are not probability estimates.
