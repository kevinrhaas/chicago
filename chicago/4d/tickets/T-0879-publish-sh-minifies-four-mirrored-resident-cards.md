---
id: T-0879
title: publish.sh minifies four mirrored resident cards that the synthesis-drift ratchet then fails: any run that publishes must hand-revert them
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-06
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T10:23:01.569Z
claimed_run: null
---

publish.sh minifies four mirrored resident cards that the synthesis-drift ratchet then fails: any run that publishes must hand-revert them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while working T-0797, and it costs every publishing run a hand-revert.

`tools/publish.sh` ships the residents layer minified — 1,385 of the 1,389 mirrored files
are one line, and the published-residents gate says so in its own words: "1389 file(s)
carry their source's value exactly, 1385 of them shipped on one line". Four are not:

    site/chicago/4d/data/residents/households/hh_adams_william_h.json
    site/chicago/4d/data/residents/households/hh_miller_john.json
    site/chicago/4d/data/residents/households/hh_murphy_john.json
    site/chicago/4d/data/residents/index.json

They stand pretty-printed on `dev`, and `publish.sh` minifies them on every run. That is
the correct published form and the value is unchanged — but `site/chicago/4d/data` is one
of `synthesize_resident_research.py`'s `DRIFT_ROOTS`, that ratchet compares BYTES against a
fresh run of the writer, and the writer writes these four pretty. So the moment a run
publishes, four files "drift from the writer" and `check.sh` goes red on a parcel that
never touched the residents layer. T-0797 hit it and reverted the four by hand to land.

**Acceptance:** decide which of the two is right — the writer should mirror what publish
ships, or the ratchet should compare mirrored files by VALUE the way the
published-residents gate already does — and make the pair agree, so a publish is not a
red. Whichever way it goes, `./tools/publish.sh && ./tools/check.sh` on an otherwise
untouched checkout must be green.
