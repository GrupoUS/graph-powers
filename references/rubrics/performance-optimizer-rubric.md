# Performance Optimizer On-Demand Rubric

Load only to select metrics or score a cross-domain trade-off.

## Metric routing

- Browser/runtime: p75 LCP, INP, CLS, long tasks, request waterfalls.
- Build: route gzip size, chunk duplication, transform/build time.
- API/database: p50/p95 latency, query count, rows scanned, pool pressure.
- Memory: retained heap, allocation rate, GC pause, steady-state RSS.
- SEO/GEO: crawlability, metadata/schema validity, canonical/indexability.
- Security baseline: exploitable configuration gaps, dependency evidence, headers.

## Comparison rules

- Same environment, workload, warmup, sample count, and measurement tool.
- Report absolute and percentage change plus likely noise.
- Include correctness regressions and resource trade-offs.
- Do not extrapolate synthetic results to production without labeling the inference.

## Optimization priority

Rank by user impact × frequency × confidence ÷ implementation risk. Prefer
removing work over caching it, and local fixes over global complexity.
