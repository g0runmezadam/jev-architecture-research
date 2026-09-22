# Jev Failure Surface

All entries below are behavioral observations from synthetic or controlled
cases. They are not estimates of production error rates.

| Failure family | Example | Observed behavior | Confidence behavior | Interpretation |
|---|---|---|---|---|
| Negation | “Customer does not want a refund” | Billing remained dominant (`billing≈0.95`, confidence `.93`) | High confidence error candidate | Strong evidence of semantic-polarity weakness |
| Double negation | “Not impossible that they do not want a refund” | Billing `.88`, confidence `.82` | Still high | Unstable compositional negation |
| Contradiction | Text and metadata disagree | Billing `.94–.97` in tested variants | `.91–.96` | Source priority not identified |
| Ambiguity | “Something went wrong with a charge” | Sometimes one-hot billing | Confidence can be `1.00` | Overconfidence under semantic collision |
| Sarcasm | “Great, another mysterious charge” | Billing one-hot | Confidence `1.00` | Pragmatic/sarcastic intent not robust |
| Semantic collision | Duplicate payment vs payment issue | One close anchor can dominate | High confidence | Anchor-sensitive decision space |
| Turkish negation | Explicit Turkish non-request | Sales/billing split, confidence `.36` | Low confidence | Multilingual polarity uncertainty |
| Long context | 180 unrelated sentences plus final billing fact | Billing remained one-hot in one case | High | No failure in this narrow test; not general proof |

## Failure interpretation

**Observed:** failures cluster around polarity, contradiction, sarcasm and close
semantic options rather than appearing as random output noise.

**Inferred:** confidence is not globally reliable; it is better behaved for
clear semantic matches than for compositional language phenomena.

**Speculative:** a calibration layer may be trained on easier decision examples,
or the endpoint may post-process a sharp decision distribution.

## Limitations

The synthetic gold labels are sometimes subjective, multilingual coverage is
small, and no natural production dataset was used. These results identify failure
families, not operational risk percentages.
