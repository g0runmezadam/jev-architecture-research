# Jev Hypothesis Tracker

| ID | Hypothesis | First appearance | Supporting experiments | Contradicting experiments | Status | Current confidence |
|---|---|---|---|---|---|---:|
| H1 | Single-stage global joint semantic scoring | Architecture probes | Final 720-call cluster test; near-duplicate redistribution | Cluster mass/latency plato leaves staging possible | Weakly Supported | 70% research weight |
| H2 | Candidate reduction + reranking | Architecture probes | Near-duplicate and duplicate competition are compatible | Final layout test found no strong cluster-position signature | Unresolved | 10% |
| H3 | Hierarchical/cluster-first filtering | Cluster attribution | Stable cluster mass with intra-cluster variation is compatible | Target/cluster winners stable across all layouts | Weakly Supported | 8% |
| H4 | Shared encoder + typed heads | Initial architecture hypothesis | Typed outputs, question scaling, score/noul behavior | No internal access | Supported | High |
| H5 | Encoder-only architecture | Initial comparison | Semantic robustness can be encoder-based | Typed/ordinal/threshold behavior suggests a decision layer | Weakly Supported | Low-medium |
| H6 | Encoder + ranking head | Score/semantic geometry phase | Close-option competition, duplicate anchors, score behavior | Ranking loss is not observed | Supported | Medium-high |
| H7 | Calibration-focused objective | Calibration phase | Brier/ECE, ambiguity and score behavior | High-confidence negation/collision failures | Weakly Supported | Medium |
| H8 | Traditional fixed classifier | Baseline | Some easy cases look classifier-like | Permutation, dynamic options, semantic competition | Rejected as complete explanation | Low |
| H9 | Retrieval + reranker | Stage attribution | Cluster/anchor behavior compatible | No retrieval-specific latency or ablation signature | Unresolved | Low-medium |
| H10 | Decision-native architecture | Attribution phase | Typed decision space and threshold regions | Encoder + ranking head explains much of data | Weakly Supported | Medium |

Status is about explanatory adequacy, not logical possibility. Confidence updates
are grounded in the cited raw experiments and are not model probabilities.
