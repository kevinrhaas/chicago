---
id: T-0902
title: publish.sh and the resident synthesizer write four mirror files in two different shapes, so whichever ran last decides whether check.sh is green
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
closed_at: 2026-09-10T04:20:07.989Z
claimed_run: null
---

publish.sh and the resident synthesizer write four mirror files in two different shapes, so whichever ran last decides whether check.sh is green.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0695, 2026-09-06**, which ran `./tools/publish.sh` as every PR must and watched
`bash tools/check.sh` go from green to red on four files its own diff never touched.

Two writers disagree about the same four paths in the mirror:

    site/chicago/4d/data/residents/households/hh_adams_william_h.json
    site/chicago/4d/data/residents/households/hh_miller_john.json
    site/chicago/4d/data/residents/households/hh_murphy_john.json
    site/chicago/4d/data/residents/index.json

`tools/synthesize_resident_research.py` writes them INDENTED — `site/chicago/4d/data` is one
of its `DRIFT_ROOTS`, so it writes the mirror as well as the source — and `tools/publish.sh`
writes them MINIFIED, which is the shape the other 1,335 mirrored household files are in.
The T-0838 drift ratchet compares the committed tree against a fresh run of the synthesizer
with a baseline of zero, so whichever tool ran last decides whether the gate passes: publish
last is four FAIL lines, synthesize last is green.

**This is a trap for every unit of work in this app, not a cosmetic difference.** Publishing
is mandatory in the same commit as any data change, and the gate that goes red names files
the author never opened, in a check about resident synthesis — so it reads as the author's
fault. T-0695 spent part of a run finding that out and landed with the four files restored
to their dev bytes, which fixes nothing and only defers it.

**Acceptance:** one of the two tools owns the shape of these four files and the other stops
writing them — either the synthesizer stops writing under `site/` and publish mirrors its
output, or publish leaves the paths the synthesizer owns alone — stated in `docs/` beside the
publish contract; running `./tools/publish.sh` and `tools/check.sh` in either order on an
untouched dev gives the same answer; and no household record's content changes, only which
tool writes it and in what shape.
