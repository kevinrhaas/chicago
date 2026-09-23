---
id: T-1422
title: The seven schools' teachers and pupil counts, the Democrat and the American staffed to the model, and the register's third printing office adjudicated
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1411
opened: 2026-09-19
closed: 2026-09-20
pr: 1554
claimed_by: run 9/20/2026, 12:37:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T06:16:34.991Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35492019357
---

The seven schools' teachers and pupil counts, the Democrat and the American staffed to the model, and the register's third printing office adjudicated.

Piece 2 of 2 of **T-1411 — The churches, the schools and the press as establishments with their people: the five churches of the census with ministers attested and sextons reconstructed, the seven schools' teachers and pupil counts, the Democrat and the American staffed to the model, and the register's third printing office adjudicated**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

1. There is somewhere in the business layer to write a hand down for a house the register
   COMPILES. `data/businesses/rulings/establishment_staffing.json` is laid over the compiled
   records by `compile_businesses.apply_staffing_overlay`; it supplies `staff` and a new
   `staffing` block and touches no other field; `--check` re-derives it byte for byte and a
   hand edit to a compiled record is still refused.
2. `staffing` NAMES NOBODY and the compiler holds it to that. `writes_no_person` is checked,
   a hand carrying a person id or a name is refused, and a hand nobody has written carries
   `drawn: false` with the reason. A hand a SOURCE names is a different thing and goes in
   `staff` with its citation.
3. Every one of the seven schools the register carries names its teacher. Where the teacher
   is the keeper the record already prints, the block POINTS at that row and writes no second
   one — the model's assistant is 0–0–1 with a typical of nought, and drawing one would put a
   second schoolteacher in a room the model says held one.
4. Each school's pupil count is recorded as what the source actually gives. Six print a fee
   table and no roll. The one figure this project holds is carried with its own date on it
   and cannot be read as an attendance for 1 July 1835.
5. The Democrat and the American carry the model's printer rows. The Democrat's apprentice is
   drawn at `inferred` on the office's own advertisement of 20 May 1835 and names nobody; its
   journeyman and both the American's hands stand undrawn with the reason.
6. The register's third printing office is adjudicated: one house, two printed styles, ruled
   in `trade_class_rulings.json § one_house_rulings` with the argument written out, and the
   crosswalk's `printing_office` row reads 2 against the census's 2 while both records stand.
7. `./tools/check.sh` green and the smoke parts `smoke_budget.mjs --for-diff` names green.

**What the title asked for that the evidence answered differently, recorded rather than
quietly dropped:** the title says "the seven schools' teachers", written before the notices
were read. There are seven schools and there are seven teachers, and they are the same seven
people the register already prints as keeping them — so the honest delivery is a pointer and
not seven new staff rows. Two of the seven, moreover, had not opened on the scene date at
all: Everts on 10 August and Hunt on 17 August 1835, both conditional on "sufficient
encouragement", and the register itself says so with `opening_announced_after_scene_date`.
The trade-census crosswalk does not yet read that judgement — it reads the gazetteer's
`built_at_scene_date`, which is false only on a contradiction — and fixing it alone would
make the order book commission two reconstructed schools against a gap the evidence has
already explained by name and by date. That is **T-1428**, filed with the measurement and
the reason both halves have to move together.
