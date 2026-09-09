---
name: webapp-testing
description: "Use when a real browser must verify rendered UI, E2E flows, authenticated behavior, screenshots, console, page errors, network, hydration, focus, or responsive behavior. Trigger on browser smoke, E2E, visual evidence, flaky UI, hydration mismatch, focus bug, layout regression, or page errors. Not for unit tests, API-only probes, or static review."
license: Complete terms in content/skills/webapp-testing/LICENSE.txt
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# Real-browser verification

Choose clean headless Chrome for deterministic smoke evidence; attach CDP only for an authenticated
or extension-specific symptom and never close or alter the user's tab. Persistent state is allowed
only when persistence is the scenario. Lightpanda DOM checks are never screenshot/layout authority.

Define the route, user action and observable assertion before running. Capture console, page/network,
screenshot, focus and responsive evidence only when relevant; distinguish a product failure from test
flakiness. Read `content/skills/webapp-testing/references/browser-setup.md` for sessions, CDP, waits, selectors and resource
limits. Stop with reproducible pass/fail evidence or a bounded blocker; route unit/API/static work to
its proper tool.
