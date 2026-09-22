# Jev Calibration Analysis

## Direct metrics

On the 150-case synthetic deep suite:

- Jev accuracy: `150/150`.
- Brier score: `0.0030`.
- ECE: `0.0477`.
- p50 latency: approximately `285–293 ms`.

The labels and cases were controlled/synthetic. These values are evidence of
behavior on that set, not production calibration proof.

## Confidence behavior

**Observed:** Jev often assigns one-hot or near-one-hot distributions to clear
cases, splits close semantic candidates, and increases entropy in severe
ambiguity. Score output tracks the expected value of its probability distribution
within the tested range.

**Observed counterexamples:** negation and semantic-collision cases produced
high-confidence errors or overconfident one-hot outputs. The confidence attack
set had Jev correct on 6/9 cases under its chosen synthetic labels.

## Interpretation

**Inferred:** Jev has calibration-like output behavior and appears to preserve
some ambiguity, but calibration is context-sensitive and imperfect.

**Not established:** RLCD, a specific loss function, temperature scaling,
isotonic regression, or any particular post-processing implementation.

## Metrics caveats

Brier and ECE depend on label quality, class balance, probability semantics and
dataset construction. The 150-case set was not a random production sample. A
reliability diagram over natural, independently labeled data is still missing.
