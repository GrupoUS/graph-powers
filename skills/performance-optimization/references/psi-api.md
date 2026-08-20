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

> **Where the JSON goes.** These examples write to `<scratch>/…` — substitute a real directory
> before running. `/tmp` is POSIX-only, and hardcoding it here would break every Windows machine
> and violate this repository's own no-absolute-paths rule. Get a portable one with:
> `python -X utf8 -c "import tempfile;print(tempfile.gettempdir())"`.

```bash
# Mobile, all categories
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=mobile&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}" -o <scratch>/psi-mobile.json

# Desktop
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=desktop&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}" -o <scratch>/psi-desktop.json
```

## Parse

`jq` is a separate install with no Windows story. Python's stdlib reads the same JSON, and the
plugin already requires Python.

```bash
# Top-level scores
python -X utf8 -c "import json,sys;c=json.load(open(sys.argv[1],encoding='utf-8'))['lighthouseResult']['categories'];print({k:round(v['score']*100) for k,v in c.items()})" <scratch>/psi-mobile.json

# Core Web Vitals (lab data)
python -X utf8 -c "import json,sys;a=json.load(open(sys.argv[1],encoding='utf-8'))['lighthouseResult']['audits'];print({k:a[k]['numericValue'] for k in ('largest-contentful-paint','cumulative-layout-shift','total-blocking-time')})" <scratch>/psi-mobile.json

# CrUX field data (real-user, p75)
python -X utf8 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('loadingExperience',{}).get('metrics',{}))" <scratch>/psi-mobile.json

# Top opportunities, biggest saving first
python -X utf8 -c "import json,sys;a=json.load(open(sys.argv[1],encoding='utf-8'))['lighthouseResult']['audits'];o=[(v.get('details',{}).get('overallSavingsMs',0),k,v.get('title','')) for k,v in a.items()];[print(f'{ms:7.0f} ms  {k}: {t}') for ms,k,t in sorted((x for x in o if x[0]>100),reverse=True)[:5]]" <scratch>/psi-mobile.json
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
curl -s "..." -o <scratch>/psi-baseline.json

# Apply optimization, re-run
curl -s "..." -o <scratch>/psi-after.json

# Delta between two runs, per category
python -X utf8 -c "import json,sys;g=lambda f:{k:v['score']*100 for k,v in json.load(open(f,encoding='utf-8'))['lighthouseResult']['categories'].items()};b,a=g(sys.argv[1]),g(sys.argv[2]);[print(f'{k:16} {b[k]:5.0f} -> {a[k]:5.0f}  ({a[k]-b[k]:+.0f})') for k in b]" <scratch>/psi-baseline.json <scratch>/psi-after.json
```
