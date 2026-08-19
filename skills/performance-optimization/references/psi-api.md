# PageSpeed Insights API Reference

Synthetic CWV measurement. No Chrome / Lighthouse install required.

## Endpoint

```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed
```

Query params:
- `url` — target URL
- `strategy` — `mobile` | `desktop`
- `category` (repeatable) — `performance`, `accessibility`, `best-practices`, `seo`
- `locale` — BCP-47 report locale (`${project.locale}`)
- `key` — optional API key (raises 25k/day → higher quota)

## Examples

```bash
# Mobile, all categories
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=mobile&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}" \
  -o /tmp/psi-mobile.json

# Desktop
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=desktop&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}" \
  -o /tmp/psi-desktop.json
```

## Parse

```bash
# Top-level scores
jq '{
  perf: (.lighthouseResult.categories.performance.score * 100 | round),
  a11y: (.lighthouseResult.categories.accessibility.score * 100 | round),
  bp: (.lighthouseResult.categories["best-practices"].score * 100 | round),
  seo: (.lighthouseResult.categories.seo.score * 100 | round)
}' /tmp/psi-mobile.json

# Core Web Vitals (lab data)
jq '.lighthouseResult.audits["largest-contentful-paint"].numericValue,
    .lighthouseResult.audits["cumulative-layout-shift"].numericValue,
    .lighthouseResult.audits["total-blocking-time"].numericValue' /tmp/psi-mobile.json

# CrUX field data (real-user, p75)
jq '.loadingExperience.metrics' /tmp/psi-mobile.json

# Top opportunities
jq '.lighthouseResult.audits | to_entries
    | map(select(.value.details.overallSavingsMs // 0 > 100))
    | sort_by(-.value.details.overallSavingsMs)
    | .[0:5]
    | map({audit: .key, savings: .value.details.overallSavingsMs, display: .value.displayValue})' \
  /tmp/psi-mobile.json
```

## Error handling

| HTTP | Cause | Fallback |
|---|---|---|
| 429 | Quota exhausted | `npx lighthouse <url> --preset=desktop --port=9222 --chrome-flags="--headless=new"` |
| 500 | Page failed audit | Try desktop strategy; retry once after 30s |
| URL unreachable | DNS / deploy issue | `curl -I <url>` first |

## Compare baseline vs after

```bash
# Run baseline before change
curl -s "..." -o /tmp/psi-baseline.json

# Apply optimization, re-run
curl -s "..." -o /tmp/psi-after.json

# Delta
jq -n --slurpfile b /tmp/psi-baseline.json --slurpfile a /tmp/psi-after.json '
  ($b[0].lighthouseResult.categories | to_entries) as $bcats
  | ($a[0].lighthouseResult.categories | to_entries) as $acats
  | [range(0; $bcats | length)]
    | map({
        cat: $bcats[.].key,
        before: ($bcats[.].value.score * 100 | round),
        after: ($acats[.].value.score * 100 | round),
        delta: (($acats[.].value.score - $bcats[.].value.score) * 100 | round)
      })'
```
