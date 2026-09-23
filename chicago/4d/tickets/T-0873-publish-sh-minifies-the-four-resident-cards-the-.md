---
id: T-0873
title: publish.sh minifies the four resident cards the synthesizer writes pretty, so the first republish after a synthesis spend turns the drift ratchet red
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
closed_at: 2026-09-10T04:20:07.142Z
claimed_run: null
---

publish.sh minifies the four resident cards the synthesizer writes pretty, so the first republish after a synthesis spend turns the drift ratchet red.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0783's run, 2026-09-06.** Two writers own the same four files in the
published mirror and they disagree about whitespace.

`tools/publish.sh` MINIFIES `site/chicago/4d/data/residents/**` — every card in that tree
is one line — and `tools/synthesize_resident_research.py` writes the same paths PRETTY,
two-space indented, because it writes the source and the mirror with one dump call.

Nothing was red on dev, because the two never ran in the same commit. PR #970 (T-0837)
spent 155 cards and wrote three of them plus `index.json` into the mirror in the
synthesizer's pretty form without a `publish.sh` pass, so dev carries four pretty files in
a tree of minified ones and `--drift` reads 0. The FIRST branch to republish - any branch,
for any reason - minifies them, and the ratchet fails four files it did not touch:

    FAIL site/chicago/4d/data/residents/households/hh_adams_william_h.json has drifted
    FAIL site/chicago/4d/data/residents/households/hh_miller_john.json
    FAIL site/chicago/4d/data/residents/households/hh_murphy_john.json
    FAIL site/chicago/4d/data/residents/index.json

T-0783 hit it on a structure-only PR and worked around it by restoring those four paths
from `origin/dev`, which is a workaround and not a fix: it leaves the mirror carrying four
files in a form `publish.sh` does not produce, and the next republish that forgets will
meet the same red. The ratchet is behaving exactly as designed - the fault is that a
whitespace difference between two generators reads as unread research drift.

**Acceptance:** the two writers agree about the published form of a resident card - either
the synthesizer stops writing the mirror and leaves it to `publish.sh`, or `--drift`
compares the mirror by parsed content rather than by bytes - the four files above carry
the form `publish.sh` produces, and a republish on a clean tree leaves `--drift` at 0 with
no path restored by hand.
