---
id: T-0880
title: publish.sh minifies four resident mirror files the synthesizer writes pretty, and the drift ratchet fails on the reformat
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
closed_at: 2026-09-10T04:20:07.481Z
claimed_run: null
---

publish.sh minifies four resident mirror files the synthesizer writes pretty, and the drift ratchet fails on the reformat.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while landing T-0798, which had to run `./tools/publish.sh` and then revert four
files to keep `tools/check.sh` green.

`tools/synthesize_resident_research.py` writes into BOTH `chicago/4d/data` and
`site/chicago/4d/data`, and its drift ratchet (T-0838) compares the committed bytes of
both against a fresh run of the writer. `./tools/publish.sh` also writes the mirror, and
it MINIFIES. For four files the two disagree:

    site/chicago/4d/data/residents/households/hh_adams_william_h.json
    site/chicago/4d/data/residents/households/hh_miller_john.json
    site/chicago/4d/data/residents/households/hh_murphy_john.json
    site/chicago/4d/data/residents/index.json

On `dev` those four are committed in the writer's pretty form while the other 1,335
household mirrors are minified, so the ratchet is green today. Run `publish.sh` and they
become minified — identical JSON, different bytes — and the ratchet fails all four with
"has drifted from the writer and is not on the T-0838 baseline". The content is not
drifting; only the formatting is, and `--write-baseline` would paper over a real gate.

So any run that publishes has to notice and revert them, which is a trap rather than a
gate. T-0798 did exactly that and shipped nothing about it.

**Acceptance:** one tool owns the mirror's bytes. Either the synthesizer stops writing
`site/` and leaves it to `publish.sh` (and the ratchet reads only `chicago/4d/data`), or
it writes the mirror through the same minifier `publish.sh` uses. Then `./tools/publish.sh`
followed by `bash tools/check.sh` is green on a clean `dev` with no file reverted by hand,
and the four files above are committed in whichever form the surviving writer produces.
