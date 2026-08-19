# Security Reviewer On-Demand Rubric

Load before Finder scoring or FP-Filter precedent checks.

## Finder evidence

Each retained finding must identify attacker capability, controlled source,
trust-boundary crossing, missing/insufficient guard, reachable sink, realistic
impact, file:line evidence, and mitigation direction.

Review authorization/tenant isolation, injection, SSRF, path traversal,
deserialization, credential exposure, webhook authenticity/idempotency,
cryptographic misuse, unsafe redirects, and state-changing CSRF where applicable.

## Hard exclusions

- Style, maintainability, or defense-in-depth advice without exploitability.
- Dependency/version claims without current advisory evidence.
- Theoretical races without a reachable concurrent path.
- Findings already blocked by a verified guard on every reachable path.
- Low/Informational issues or confidence below 8/10.

## FP-Filter verdict

Return CONFIRMED or REJECTED with confidence 1–10, the strongest disconfirming
evidence, applicable exclusion/precedent, and the exact source-to-sink trace.
