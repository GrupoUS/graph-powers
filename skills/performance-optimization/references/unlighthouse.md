# Unlighthouse — Site-wide Crawl

> TODO: full reference deferred. Add when crawl-based audits become a recurring need.

Quickstart:

```bash
bunx unlighthouse --site ${project.stagingUrl} --throttle --samples 1
```

Output: `.unlighthouse/` — interactive HTML report aggregating per-route Lighthouse runs.

Use when: PSI single-URL audit insufficient (need every route audited in one pass) and Vercel Speed Insights data not yet aggregated (< 24h since enable, or staging without traffic).
