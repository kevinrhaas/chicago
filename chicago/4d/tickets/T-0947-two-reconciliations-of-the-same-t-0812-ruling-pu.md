---
id: T-0947
title: Two reconciliations of the same T-0812 ruling put the Steamboat Hotel 36 m apart: dev carries one and PR #975 the other, with no test that would have caught it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-11
pr: 1147
claimed_by: run 9/11/2026, 2:44:39 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T20:41:04.137Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34640226800
---

**Found by T-0927, 2026-09-07,** reading PR #975 against `dev` before closing it as the
self-declared duplicate of #974. It is not a duplicate. Both PRs ruled T-0812 the same way
— the committed `kinzie` record beats the August prose reading of the Wright 1834 sheet —
and then put the Steamboat Hotel in two different places.

| | anchor (local E, N) | facade setback rule | station along the street |
|---|---|---|---|
| `dev`, from PR #974 | **920.20, 222.90** | 12.192 m — half the 80 ft platted street module the Original Town uses | 65.3 m short of the convergence: one platted 18 ft alley west of `council_house`'s footprint |
| PR #975 | **948.20, 246.77** | 7.00 m — the loose end of the measured band the buildings already on this bank front the *track* at (school 2.15, Cobweb Castle 2.89, Dearborn sheds 5.01-5.17, Kinzie & Hunter 5.35, brickyard 7.02, boatman's cabin 7.31) | 28.9 m short: the station where the clearance to Kinzie's kerb equals the gap to `council_house`, 2.73 m each side |

**36.79 m apart**, and the disagreement is a real argument, not a rounding: north of the
river the committed street is a traced offset from the bank rather than a plat, so whether
the platted 80 ft module applies there at all is the question. #974 says it does; #975 says
the neighbours' own measured setbacks say it does not. Nothing in either record cites the
other, and both were written on 2026-09-06.

Downstream, the same divergence moves a derived figure that is not obviously about
placement at all: the land-tract margin for Kinzie's Addition reads **58.5 m** on `dev` and
**40.9 m** on #975, from `tools/resolve_land_tracts.py --build`.

**Nothing caught it, and that is the second half of the finding.** Both records declare
`derivation.method: not_derivable` — see T-0946 — so no gate re-computes either placement,
and `--stale` only asks whether the mesh matches the record it was baked from. Two
mutually exclusive answers to one ruling can both be green.

Two smaller things #975 holds that `dev` does not, recorded so they are not lost with the
PR: `docs/RESEARCH/kinzie_alignment_1835.md`, which writes the alignment argument out in
full (the road-only mean of `control.kinzie_canal` at E -180.99, N +262.00 against the
committed vertex at [-181, 262], and the committed line's bearing of 90.46 degrees rather
than due east) — `dev` carries that reasoning only inside `position.note`; and an internal
inconsistency in #975 itself, whose `derivation.reason` says "3.00 m from North Water
Street's committed centreline" where its own `position.note` argues 7.00 m.

**Acceptance:**

1. One setback rule for the north bank is stated and argued — platted module or measured
   neighbour band — in the place placement rules are stated, not in one building's note.
2. The Steamboat Hotel carries the placement that rule gives it, and the record says which
   of the two 2026-09-06 derivations it is and why the other was not taken.
3. Whatever moves is re-baked in the same commit and `tools/resolve_land_tracts.py --build`
   is re-run, so the tract margin is the one the placement implies.
4. The alignment argument survives as a research document rather than only as a note, and
   PR #975's version is the starting point since it is the longer one.
5. The gate gap is named: either T-0946 lands a derivation method that would have caught
   this, or a check compares a re-derived placement against the committed one for the
   records that declare a recomputable rule in prose.

**Links:** T-0812 · T-0447 · T-0713 · T-0946 · T-0927 · PR #974 (landed) · PR #975 (closed).
