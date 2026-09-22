# Jev Latency Analysis

## Measurements

### Question scaling

Earlier question-scaling probes used 1, 2, 5, 10, 20, 50 and 100 questions.
Jev remained roughly in the 260–350 ms region after cold-start effects. This is
sub-linear in question count over the measured range.

### Option scaling

In the final controlled experiment, 250 options were processed in roughly
350–364 ms across layouts. In the stage-detection study, irrelevant option p50
latency moved from approximately 286 ms at 5 options to 333 ms at 250 options.
Near-duplicate p50 moved from 282 ms at 10 duplicates to 338 ms at 250.

### State size

The bounded surface study did not show large Jev growth across the tested
500–1000-token state range, but output/token limits appeared at high option and
question combinations. This does not establish unlimited context complexity.

### Cache behavior

Local cache was explicitly bypassed in the 30-repeat studies. Earlier repeated
requests were deterministic, but cached versus uncached API internals cannot be
observed. Local cache timing must not be confused with provider inference time.

## Complexity interpretation

**Observed:** measured latency is not consistent with a naïve independent linear
forward pass per question/option.

**Inferred:** shared encoding, provider batching, parallel option processing or
staged candidate handling is likely.

**Not established:** O(1), O(log N), O(N), or an exact piecewise complexity class.
The endpoint includes serialization, scheduling, token generation and hard
limits. 500 and 1000 options were rejected with `Must have at most 255 choices`,
so no model complexity can be inferred there.

## Reproducibility

See `latency-surface-bounded.json`, `architecture-probes-scaling.json`,
`stage-detection*.json` and `final-pipeline-attribution.json`.
