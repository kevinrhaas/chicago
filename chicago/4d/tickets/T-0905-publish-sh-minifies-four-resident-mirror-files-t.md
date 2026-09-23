---
id: T-0905
title: publish.sh minifies four resident mirror files that synthesize_resident_research.py writes expanded, so whichever ran last decides whether check.sh is green
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
closed_at: 2026-09-10T04:20:08.159Z
claimed_run: null
---

publish.sh minifies four resident mirror files that synthesize_resident_research.py writes expanded, so whichever ran last decides whether check.sh is green.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0778, 2026-09-06**, which touched neither residents nor the synthesizer.

`./tools/publish.sh` rewrote four files in the published mirror that no part of that
unit changed:

    site/chicago/4d/data/residents/index.json
    site/chicago/4d/data/residents/households/hh_adams_william_h.json
    site/chicago/4d/data/residents/households/hh_miller_john.json
    site/chicago/4d/data/residents/households/hh_murphy_john.json

It **minified** them — the JSON compares equal on all four, only the whitespace moves.
`tools/synthesize_resident_research.py --drift` then failed all four as new drift off
the T-0838 baseline, because that gate re-runs the writer and diffs `read_bytes()`, and
the writer emits the mirror EXPANDED. `dev` holds the expanded form, so the two writers
disagree about the same four paths and **whichever ran last decides whether `check.sh`
is green**. T-0778 restored them to dev's bytes and said so in its PR; that is a dodge,
not a fix.

**Acceptance:** one writer owns those bytes. Either `publish.sh` stops re-serialising
files the synthesizer already wrote into the mirror, or the synthesizer emits what
`publish.sh` emits — stated, with the reason, and with a self-test that fires when the
two forms diverge again. The drift baseline is not to be widened to paper over it: it
is a ratchet standing at zero, and T-0837 is what got it there.
