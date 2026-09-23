---
id: T-0969
title: The 1840 head crosswalk reads 'Mrs.' as a forename, so 'Mrs. Mary Brown' is ruled to agree in full forename with 'Mrs Rufus Brown'
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-07
pr: 1040
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-08T04:25:35.685Z
claimed_run: null
---

The 1840 head crosswalk reads 'Mrs.' as a forename, so 'Mrs. Mary Brown' is ruled to agree in full forename with 'Mrs Rufus Brown'.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while reading printed 220 for T-0964. `crosswalk_census_1840_heads.py` parses the head
`Mrs. Mary Brown` (33SQ-GYYJ-P5, printed page 220, line 5) into `forename: "mrs"`, and then rules
it a CANDIDATE against `brown_mrs_rufus` with the reason *"Full forename and surname agree (Mrs.
Mary Brown = Mrs Rufus Brown)"*. The two forenames on the page are **Mary** and **Rufus's
unnamed wife**; what agrees is the courtesy title, and the reason sentence states something the
records do not say.

The outcome is a candidate and therefore asserts nothing — no household of 1840 is carried back
and no grade moves — so this is not a false identity in the town. It is a false REASON on a real
ruling, and the reason is the part a reader is asked to trust.

**Two things to decide, not one.** Whether a courtesy title may ever stand as a forename (it
should not; `Mrs`, `Mr`, `Capt`, `Dr`, `Rev` and `Col` all appear as leading tokens in this
corpus), and what the rule should then do with a head whose real forename is known and whose
1835 counterpart's is not — refuse, or hold as a candidate on the surname with a reason that
says so. The second is a rules question and may be the owner's.

Scope: `tools/crosswalk_census_1840_heads.py`, its self-test, and a re-run of `--build` and the
spend. Every head on every leaf goes back through it, so the whole 910-row adjudication moves.


Resolved in T-0976 / PR #1040. The original reading above is preserved. See `docs/RESEARCH/open-pr-reconciliation-2026-09-08.md` for the repair, its limits and regression tests.
