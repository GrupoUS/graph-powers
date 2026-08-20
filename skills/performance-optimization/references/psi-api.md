# Measuring a page — PSI, Lighthouse CLI, Unlighthouse

The single home for *how a synthetic measurement is taken*. `/perf § 2` decides which of the three
runs; this file is the invocation. Nothing here duplicates a threshold — those are `gates.*` in the
project config, with the web.dev context in `SKILL.md § Targets`.

## The ladder

| Tool | Use when | Cost |
|---|---|---|
| **PSI API** | default — one URL, no Chrome, no install | HTTP call |
| **Lighthouse CLI** | PSI returned 429, the page needs auth, or a custom throttle profile is required | needs Chrome |
| **Unlighthouse** | every route audited in one pass | needs Chrome, minutes |

## PSI API

```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed
```

| Param | Value |
|---|---|
| `url` | target |
| `strategy` | `mobile` \| `desktop` |
| `category` (repeatable) | `performance`, `accessibility`, `best-practices`, `seo` |
| `locale` | BCP-47 report locale (`${project.locale}`) |
| `key` | optional; **25,000 requests/day is the quota of a Google Cloud project that has a key.** Keyless works for ad-hoc runs but is rate-limited per IP at a level Google does not publish — a repeated or automated run needs a key |

Default emulation is mobile, 4× CPU slowdown, simulated Slow-4G. A single run is noise: for a gate,
take the median of 3.

### Run it

`curl` is an alias of `Invoke-WebRequest` in PowerShell and rejects `-s`; `jq` is a separate install
with no Windows story. Python's stdlib does both halves, and the plugin already requires it.

```bash
# Scores, straight to stdout — the common case needs no file on disk.
python -X utf8 -c "import json,sys,urllib.request;d=json.load(urllib.request.urlopen(sys.argv[1],timeout=120));c=d['lighthouseResult']['categories'];print({k:round(v['score']*100) for k,v in c.items()})" "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=mobile&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}"

# Save the raw report when it will be compared later. `<scratch>` is a real directory you pick:
# python -X utf8 -c "import tempfile;print(tempfile.gettempdir())"
python -X utf8 -c "import pathlib,sys,urllib.request;pathlib.Path(sys.argv[2]).write_bytes(urllib.request.urlopen(sys.argv[1],timeout=120).read())" "<psi-url>" <scratch>/psi-mobile.json
```

### Read a saved report

```bash
# Lab Core Web Vitals
python -X utf8 -c "import json,sys;a=json.load(open(sys.argv[1],encoding='utf-8'))['lighthouseResult']['audits'];print({k:a[k]['numericValue'] for k in ('largest-contentful-paint','cumulative-layout-shift','total-blocking-time')})" <scratch>/psi-mobile.json

# CrUX field data (real users, p75) — absent for a URL with too little traffic, which is a fact, not an error
python -X utf8 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('loadingExperience',{}).get('metrics',{}))" <scratch>/psi-mobile.json

# Top opportunities, biggest saving first — this is the fix order
python -X utf8 -c "import json,sys;a=json.load(open(sys.argv[1],encoding='utf-8'))['lighthouseResult']['audits'];o=[(v.get('details',{}).get('overallSavingsMs',0),k,v.get('title','')) for k,v in a.items()];[print(f'{ms:7.0f} ms  {k}: {t}') for ms,k,t in sorted((x for x in o if x[0]>100),reverse=True)[:5]]" <scratch>/psi-mobile.json

# Delta between two saved runs, per category — what `/perf compare` prints
python -X utf8 -c "import json,sys;g=lambda f:{k:v['score']*100 for k,v in json.load(open(f,encoding='utf-8'))['lighthouseResult']['categories'].items()};b,a=g(sys.argv[1]),g(sys.argv[2]);[print(f'{k:16} {b[k]:5.0f} -> {a[k]:5.0f}  ({a[k]-b[k]:+.0f})') for k in b]" <scratch>/psi-baseline.json <scratch>/psi-after.json
```

## Lighthouse CLI

```bash
npx lighthouse ${project.stagingUrl} --output=json --preset=desktop --port=9222 --chrome-flags="--headless=new --no-sandbox --disable-gpu --no-first-run --disable-extensions"
```

Give each sequential run its own port (`9222`, `9333`) or the second attaches to the first's
browser. If Chrome is not found automatically, set `CHROME_PATH`. When the project keeps a
Lighthouse CI config, run that instead with `numberOfRuns: 3`.

## Unlighthouse

```bash
npx unlighthouse --site ${project.stagingUrl} --throttle --samples 1
```

Writes `.unlighthouse/` — an interactive report aggregating one Lighthouse run per discovered route.
Use it when a single-URL audit is not enough and RUM is unavailable (Speed Insights under 24h old,
or staging with no traffic).

## Failures

| Symptom | Cause | What to do |
|---|---|---|
| HTTP 429 | quota or per-IP rate limit | retry once, then Lighthouse CLI; add `&key=` for repeated runs |
| HTTP 500 | the page failed its audit | try `strategy=desktop`, retry once after 30s |
| URL unreachable | DNS or deploy | `python -X utf8 -c "import urllib.request,sys;print(urllib.request.urlopen(sys.argv[1],timeout=10).status)" <url>` |
| `loadingExperience` empty | not enough CrUX traffic | report lab data only, and say the field data is missing |
