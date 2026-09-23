---
id: T-0060
title: The smoke's mobile half no longer fits the runner's ten-minute command ceiling
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-20
pr: 272
claimed_by: run 8/20/2026, 2:09:07 AM CT
blocked_on: null
needs_bake: false
---

The smoke's mobile half no longer fits the runner's ten-minute command ceiling.

**Measured 2026-08-18 on T-0036's run**, serving the published mirror:
`SMOKE_VIEWPORT=mobile` was killed at 570 s having reached **208 passed / 2 failed**;
`SMOKE_VIEWPORT=desktop` was killed at 570 s at **143 passed / 0 failed**. ROADMAP § THE RUN
BUDGET records the last measurement, 2026-08-15: mobile finished in **4 m 43 s** at 214
assertions and only the desktop half overran. The suite has since grown past 300 assertions per
viewport, so **neither half fits any more** — and the assertion that goes unrun is always the same
one, because `zero page errors` is the LAST line of each viewport. A run can now merge without
ever having been told whether the page threw.

That section already names the durable fix: *"the smoke should take a test-name or section filter
the way it takes `SMOKE_VIEWPORT`, so the desktop half can be run as two commands that each fit."*
It is now the mobile half too, and it is load-bearing rather than a convenience.

**Acceptance:** `tools/smoke_renderer.mjs` takes a section or name filter (alongside
`SMOKE_VIEWPORT`, and saying out loud that a filtered run is not the gate, exactly as that flag
does), the page-error assertion is taken in EVERY filtered run rather than only in the tail, and
one run demonstrates the full mobile gate completing as two commands that each finish inside ten
minutes with the same total assertion count as an unfiltered pass. Update ROADMAP § THE RUN BUDGET
with the new measurements in the same PR.

---

## Analysis done 2026-08-19 — the mechanics, so a run implements rather than rediscovers

The owner asked for this next, after the Blender lane. Everything below was measured
against `tools/smoke_renderer.mjs` at 7,046 lines; the numbers are reproducible from the
scripts described.

**1. The sections already exist as comments.** Sixty banners of the form
`    // --- <name> ---------` run from line 817 to 6938, each opening a coherent group
(`the gate counts the town (T-0036)`, `the enclosure layer (T-0038)`, `the confidence
view`, `walking`, `budgets`, …). They are the natural stage names — do not invent a new
taxonomy, lift these.

**2. The body is ONE block, which is why this is a refactor and not a flag.** Everything
from the boot check to `zero page errors` sits inside a single `if (ready) { … }` at line
795, closing near 7010, inside the two-viewport `for`. There are 29 statements at the
loop's top level and effectively all the work is in that one block, so there is nothing to
filter without introducing structure.

**3. Beware the analysis trap that nearly cost a wrong design.** A regex sweep for
"binding declared in section A, name appears after section A" reports **46 cross-section
uses**, which would make block-wrapping impossible. Inspected one by one at the best split
point, **all eight apparent crossings were false**: `shown` at 2927 is an object KEY
(`shown:`), `want` at 4158 is a word inside a template string, `anchored` (4371), `off`
(2363), `on` (2287) and `back` (2290) are words inside COMMENTS, `sauganash` at 2805 is an
object key, and `d` at 2397 is a re-declaration at deeper indent that the indent-4 scan
missed. **Word-boundary matching over source text counts comments, strings and keys.**
Use a real parser, or verify each candidate by eye — do not trust the raw count either way.

**4. A candidate split point, already located.** Crossing counts per boundary bottom out
in the middle third at **section 15, `// --- the ground faces the sky ---`, line 2285**
(8 apparent crossings, all of them false per (3) above). Sections 16 and 17 tie. That is
where to cut if two commands is the shape.

**5. What the filter has to do, beyond selecting checks.** The cost is not the assertions,
it is the page work behind them — navigation, captures, probes, at 0.5–1.1 s per frame on
a software renderer. A filter that skips only `check()` calls saves nothing. The stages
have to be skippable *work*.

**6. The page-error assertion.** It is the LAST line of each viewport (line 7011), which
is exactly why a killed run never takes it. Whatever shape the filter has, that check must
run in every invocation — including one that stops early — which likely means hoisting it
into a `finally` or an explicit end-of-run block rather than leaving it as the tail.

## Why this ticket is still open after the analysis

**The verification cannot be done anywhere but a real runner.** The acceptance requires
the two filtered halves to reach the same total assertion count as an unfiltered pass —
that is a claim about the suite's behaviour, provable only by running it three times.
Attempted 2026-08-19 in the assistant's container: the desktop half dies in
`roadContrast` (smoke_renderer.mjs:503, called from 4052) taking a page screenshot, before
reaching any split point. A gate refactor shipped without that comparison is precisely the
change nobody can trust — so the implementation belongs to a run on the improve runner,
where the suite completes (654 checks, both viewports, ~55 min, measured on run 941).

**Acceptance is unchanged.** The analysis above narrows the work; it does not lower the
bar. Do not weaken an assertion, and do not declare victory on a filtered run alone.

---

## Implemented 2026-08-20 — what the analysis got right, and the two places it was wrong

An earlier run left a full mechanics analysis on `steward/t0060-analysis` (never PR'd);
its section census, its "the body is ONE block" reading and its warning about
word-boundary scans over source text all held up. Two corrections from the build:

**1. Two stages were not enough.** The analysis's split point (section 15, "the ground
faces the sky") is a fine boundary — but the second half alone still overran the
ten-minute ceiling (measured 565 s once and killed at 600 s once, same code, same
machine). The suite ships with FOUR stages: the original boundary plus cuts at
`// --- navigation ---` and at the flora census, each verified the same way.

**2. The verified-boundary scan had the exact blind spot it warned about.** Both the
analysis's scan and this run's first scan anchored on indent, and both missed
`terrainLoad` — declared at column 0, used across the boundary. It surfaced as a
ReferenceError the first time a stage ran alone. The shipped scan anchors on brace
depth; it found one more crossing (`streetLayer`), and both are now read once, above
the splits. Fresh-boot state was the other lesson: a staged run starts at the GATE
SCREEN, which stage 2's chrome checks are the ones to dismiss, so stages 3 and 4 open
with a preamble that enters the town exactly once (a no-op in an unfiltered pass).

Numbers, counts and the audit arithmetic are in ROADMAP § THE RUN BUDGET. The
unfiltered single-process reference runs in `.github/workflows/chicago-4d-smoke.yml`.
Reaching the tail of the suite for the first time in days also surfaced the
road-legibility red now filed as T-0114.
