---
id: T-0753
title: Hurlbut gives Gurdon Hubbard a birth and a Montreal origin, and the household record holds neither
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 943
claimed_by: run 9/5/2026, 7:36:29 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T00:59:47.906Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34001601114
---

Hurlbut gives Gurdon Hubbard a birth and a Montreal origin, and the household record holds neither.

**What is there.** `bk_afc_004` carries more than the arrival date T-0594 spent: "He was
born in Windsor, Vt., in 1802 and parents were Elizur and Abigail (Sage) Hubbard" and
"Mr. Hubbard left Montreal, were his parents then lived". `hh_hubbard_gurdon.json`
carries `origin: null` — "Not attested in anything this project holds" — and the person
carries no birth at all.

**Why it was not done on T-0594.** That ticket's acceptance is a closed contract that
says in terms "Nothing else in the household moves". Writing `origin` would have been
widening it, and the run declined to.

**The two questions this ticket actually has to settle**, because neither is obvious:
- Montreal is where his PARENTS lived in 1818 and where he departed from as an indentured
  clerk of sixteen; his birth is Windsor, Vermont. `origin` is a household field about
  where a household came from, and Hubbard did not arrive as a household at all — he
  arrived as a company clerk seventeen years before the scene, and whatever household
  stands under his name in 1835 is not the one that left Montreal. An `origin` of
  "Montreal" may be a straightforwardly wrong reading of the field.
- Whether a person record in this dataset has anywhere to put a birth place, a birth year
  and two parents' names at all, or whether that is a schema question first.

**The grade is settled either way** and is the same finding T-0594 made: this is Hurlbut's
own narrative, outside the quotation marks in which Hubbard speaks, and the source record
grades that layer rung 4. Anything taken from it is `inferred` at best.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Either the two questions above are answered and the fields written at a grade the
  rung-4 layer supports, or the ticket is `block --owner` on the field-shape question
  with both readings set out. Guessing which is not an outcome.
- `tools/check.sh` green.

**Links:** T-0594 (the arrival, and the voice finding) · T-0575 (the read) ·
`data/research/books/claims/american_fur_company_hurlbut.json` bk_afc_004
