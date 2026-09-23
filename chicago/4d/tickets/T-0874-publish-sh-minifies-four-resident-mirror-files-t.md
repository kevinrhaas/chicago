---
id: T-0874
title: publish.sh minifies four resident mirror files that the T-0838 synthesizer ratchet expects verbatim, so every publishing PR is one revert away from red
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded: fixed by T-0933 (#1024) and T-0938 (#1023) — the mirror is untracked, publish.sh is its one writer, DRIFT_ROOTS no longer includes site/, and --drift-self-test holds it; --drift is green on dev
needs_bake: false
closed_at: 2026-09-10T04:20:07.313Z
claimed_run: null
---

publish.sh minifies four resident mirror files that the T-0838 synthesizer ratchet expects verbatim, so every publishing PR is one revert away from red.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND WHILE LANDING T-0694 (PR #973), 2026-09-06. `./tools/publish.sh` rewrites
`site/chicago/4d/data/residents/index.json` and the three household cards
`hh_adams_william_h.json`, `hh_miller_john.json`, `hh_murphy_john.json` from
pretty-printed JSON to one minified line. The bytes are semantically identical —
verified with a `json.loads` comparison against `HEAD` — but `check.sh`'s step
**"the resident synthesizer has not drifted further from the cards it writes"**
(the T-0838 ratchet) compares those mirror files against what
`synthesize_resident_research.py` writes, and reports all four as drifted.

So the two tools disagree about the same four files, and the order they run in
decides whether the gate is green: `check.sh` then `publish.sh` passes and ships
the drift, `publish.sh` then `check.sh` fails. T-0694 hit it in the second order
and resolved it by restoring the four files from `dev` — which is a revert, not a
fix, and the next publishing PR will re-minify them.

**Acceptance:** one of the two tools gives way, ruled on rather than patched
around — either `publish.sh` leaves these four alone (they are the synthesizer's
output, not the publisher's), or the ratchet compares parsed JSON rather than
bytes. Whichever it is, `./tools/check.sh` is green immediately after
`./tools/publish.sh` on a tree where nothing else changed, and a test asserts that
ordering.
