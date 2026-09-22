# Receipt: Final Pipeline Attribution

- Date: 2026-09-22
- Source: `final-pipeline-attribution.json`.
- Design: 10 clusters × 25 options, four layouts, six target positions, 30 cache-bypass repetitions: 720 calls.
- Controls: random option IDs per repeat, randomized cluster/member ordering, fixed description template.
- Results: target winner 720/720; cluster winner 720/720; cluster mass approximately .981–.998 by layout.
- Caveat: provider internals, hidden batching and top-k behavior remain unobservable.
- Conclusion: global joint semantic scoring is the best current behavioral explanation; weak position probability effect remains.
