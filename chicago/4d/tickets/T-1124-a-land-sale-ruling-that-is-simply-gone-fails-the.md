---
id: T-1124
title: A land-sale ruling that is simply GONE fails the gate: resident_rulings.json counted and identified against the merge base, with a stated withdrawal the only way a judgement may leave
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0999
opened: 2026-09-14
closed: 2026-09-14
pr: 1322
claimed_by: run 9/14/2026, 8:07:57 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T13:36:26.304Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34846525716
---

A land-sale ruling that is simply GONE fails the gate: resident_rulings.json counted and identified against the merge base, with a stated withdrawal the only way a judgement may leave.

Piece 1 of 2 of **T-0999 — Nothing in the gate can see a ruling that is simply GONE: a smaller resident_rulings.json is a legal one, and #1055 lost forty judgements under a green check.sh**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**THE INCIDENT, kept here because this ticket is written from it.** On 10 September 2026
the merge lap pushed onto #1055 and `data/research/land_sales/resident_rulings.json`
conflicted. The file is `hand_authored`; the lap's regex resolution took the branch's whole
block for the second conflict, and that branch had been cut before T-0850 and T-0990 cohort A
ruled. Forty entries left the file on one line — T-0850's twenty-six and cohort A's fourteen —
and twelve resident cards silently got back a federal land purchase each had been ruled it
could not have. #1073 restored them. This is the reason nobody was told.

**Why the gate was green the whole time.** `read_land_sales.py --check` asks whether a ruling
is WELL FORMED: that it names a spelling the register holds, and a person the proposal named.
Every remaining ruling was. It has no question that a missing ruling could fail, because a
smaller rulings file is a legal rulings file — the eight surviving entries re-derived perfectly
into a crosswalk perfectly consistent with them, and `check.sh` passed on #1055 and on every
commit after it. A derivation cannot see a shrinking input; it just derives less.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- a check that FAILS when the number of adjudicated rulings in `resident_rulings.json` falls,
  counting `ruled[]` and `retired[]` together, so a retirement is a move and not a loss;
- it is run by `check.sh`, and its own refusal fires in the self-test the way the other steps'
  do — asserting on a tree with an entry removed;
- it is checked against the MERGE BASE rather than a committed number, so a branch cannot
  satisfy it by editing a total downwards in the same commit;
- a DELIBERATE removal is still possible and must state itself — the ticket that removes a
  ruling says so, the same way `retired[]` already carries its reason;
- the commits of the incident are the fixture: `07a6a1b04` (49) -> `02ce7d97a` (8) must fail
  the new check, and `2e5aa8a02` (47 + 2) must pass it.

The general version — every `hand_authored: true` file in `data/research/` — is [[T-1125]] and
is deliberately not this ticket: each domain's arrays need a reading of their own before a
count over them means anything.
