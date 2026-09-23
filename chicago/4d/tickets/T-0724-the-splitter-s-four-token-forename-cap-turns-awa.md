---
id: T-0724
title: The splitter's four-token forename cap turns away Rev. John Mary Irenaeus St Cyr, the parish priest whose own register is rung G2c
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 931
claimed_by: run 9/5/2026, 4:35:16 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T23:03:40.571Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33993351212
---
**Found by T-0692's coverage pass, 2026-09-04.** `split_name` caps forenames at four tokens
and refuses anything longer (R5). `Rev. John Mary Irenaeus St Cyr` reads as surname `Cyr`
with forenames `Rev · John · Mary · Irenaeus · St` — five — so the town's own card
`st_cyr_john_mary` is refused and has never been graded by the ladder.

**It is the priest.** The St Cyr parish register is rung **G2c**, the source that grades
35 of the town's people; the one man the ladder cannot see is the man who kept it. His card
is graded `attested` today on `andreas_1884_v1` and that grade rests on no rung at all.

**The cap is not the whole fault — the compound surname is.** `St Cyr` is two tokens and the
splitter takes only the last, so `St` lands among the forenames and pushes the count over.
Any fix has to handle the surname particle (`St`, `Van`, `De`, `Mc` where spaced) rather
than merely raising the cap, or the same name will merge onto a different `Cyr`.

**Acceptance:** the particle is handled by a stated rule with self-test cases in
`--self-test` (`Rev. John Mary Irenaeus St Cyr`, and at least one `Van`/`De` reading from
the corpus, and a counter-case that must NOT merge); `st_cyr_john_mary` carries a ladder
rung; `grading_proposal.json` is re-derived and any grade the change moves is reported
rather than applied silently; and no identity merges across two different surnames.
