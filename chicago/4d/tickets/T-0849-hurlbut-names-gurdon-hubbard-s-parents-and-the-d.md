---
id: T-0849
title: Hurlbut names Gurdon Hubbard's parents and the dataset has nowhere to put them: kin[] rows point at a household in this town, and Elizur and Abigail Hubbard have none
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-10
pr: 1088
claimed_by: run 9/10/2026, 5:06:52 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T22:32:34.015Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34535457509
---

Hurlbut names Gurdon Hubbard's parents and the dataset has nowhere to put them: kin[] rows point at a household in this town, and Elizur and Abigail Hubbard have none.

**Where this came from.** T-0753 wrote everything else in `bk_afc_004` onto
`hh_hubbard_gurdon.json` — the origin chain "Windsor, Vermont, by way of Montreal" and a
`birth_year` of 1802 with the birthplace in its note — and stopped at the clause it could not
place: "He was born in Windsor, Vt., in 1802 and parents were Elizur and Abigail (Sage)
Hubbard." T-0753's acceptance asked its run to answer whether a person record has anywhere to
put a birth place, a birth year and two parents' names at all. The first two are answered and
written; this is the third, and it is a schema ruling rather than a reading.

**What the dataset actually holds.** The only relationship structure here is the household-level
`kin[]` block the owner ratified on 2026-09-05 — graded, reciprocal, legal only against its
declared inverses. Both of the two rows committed today (`hh_kinzie_john_h` and
`hh_kinzie_james`, the half brothers out of `bk_afc_015`) carry a `household` key naming an `hh_`
id IN THIS DATASET and a `value` naming a person in it. Elizur and Abigail Hubbard were living
in Montreal in 1818, were never in Chicago, and have no household and no person id here. There
is no field on a person for a parent's name, and 1,362 person records carry none.

**The two readings, set out.**

1. **KIN STAYS INSIDE THE TOWN, AND PARENTAGE OUTSIDE IT IS EVIDENCE RATHER THAN STRUCTURE.**
   `kin[]` exists to stop a shared surname from flattening two men into one and to say how two
   households in the scene are joined; a row that points at nobody cannot be reciprocal, cannot
   be checked against its inverse, and buys the model nothing a note does not. Under this reading
   the parents stay where they are — in `bk_afc_004`'s `entities`, and in the prose of the
   `birth_year` note — and nothing is added. The cost: a reader of the card cannot see a parent's
   name without opening the claims file, and every other card in this position stays silent the
   same way.

2. **AN EXTERNAL KIN ROW, WITH THE HOUSEHOLD KEY NULL AND A NAME IN ITS PLACE.** The same graded
   block, with `household: null` and a `name_as_read` carrying the source's own string, so
   "Elizur Hubbard" and "Abigail (Sage) Hubbard" are legible on the card at the grade the rung-4
   layer supports (`inferred`, on Hurlbut's compiler prose of 1881). The cost: the reciprocity
   rule that makes `kin[]` checkable no longer holds for these rows, so the gate has to learn a
   second shape, and every genealogical name in the corpus becomes eligible — which is a large
   population and not obviously one this project wants inside its residents layer at all.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- One of the two readings is chosen, in writing, with the reason; or the ticket is
  `block --owner` on it. Guessing which is not an outcome.
- If reading 2 is chosen: the shape is documented beside `kin[]`, `check.sh` gains the gate that
  keeps a null-household row from claiming an inverse it has not got, and Hubbard's two parents
  are the demonstration.
- If reading 1 is chosen: it is recorded as a rule where a later run will meet it, and the
  ticket closes without a data change.
- `tools/check.sh` green.

**Links:** T-0753 (the reading that stopped here) · T-0594 · T-0734 (the kinship measurement
`kin[]` was ratified to spend) · `data/research/books/claims/american_fur_company_hurlbut.json`
bk_afc_004
