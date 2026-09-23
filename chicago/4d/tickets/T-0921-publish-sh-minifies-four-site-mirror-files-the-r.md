---
id: T-0921
title: publish.sh minifies four site mirror files the resident synthesizer writes pretty, so whichever ran last flips the T-0838 drift ratchet
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
closed_at: 2026-09-10T04:20:08.325Z
claimed_run: null
---

publish.sh minifies four site mirror files the resident synthesizer writes pretty, so whichever ran last flips the T-0838 drift ratchet.

`tools/publish.sh` writes `site/chicago/4d/data/**` minified. `tools/synthesize_resident_research.py`
also writes four of those files — `data/residents/households/hh_adams_william_h.json`,
`hh_miller_john.json`, `hh_murphy_john.json` and `data/residents/index.json` — and writes them
INDENTED. The two disagree on bytes and not on content, so whichever tool ran last decides what is
committed, and `--drift` compares BYTES against the T-0838 baseline. Run `publish.sh` in any PR and
those four files fail the ratchet; re-run the synthesizer and they pass again. T-0743 hit it, reverted
the four files to dev and filed this rather than banking a baseline entry for a formatting difference.

The ratchet is the point of T-0838 and it is right to be byte-exact. The fix belongs on one of the two
writers: either `publish.sh` leaves the synthesizer's four files alone, or the synthesizer writes them
the way `publish.sh` does, or `--drift` compares parsed content for the files both tools write and says
so in the file. Whichever is chosen, one tool must stop being able to silently flip the gate.

**Acceptance:** running `publish.sh` and then `synthesize_resident_research.py --drift` on an
otherwise clean checkout leaves the ratchet green, in either order, and a self-test holds it.
