---
id: T-1395
title: The name reader calls one named woman a group: 'The Harmon daughter later known as Mrs A. G. Burley' trips the COLLECTIVE article rule, so her age band carries a refusal written for a collective row
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-21
pr: 1615
claimed_by: run 9/21/2026, 2:38:31 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T08:26:07.318Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35573712444
---

The name reader calls one named woman a group: 'The Harmon daughter later known as Mrs A. G. Burley' trips the COLLECTIVE article rule, so her age band carries a refusal written for a collective row.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)


Found by T-1393's per-attribute completeness pass, which names every row that answers
nothing instead of summing them away.

`tools/spend_person_sex_age.py` reads a name as a group when ANY token of it stands in
its `COLLECTIVE` table, and `the` is in that table because "the rest of the household,
unnamed" is a count and not a name. That rule catches the six genuine collective rows —
and it also catches `harmon_daughter_burley`, "The Harmon daughter later known as Mrs
A. G. Burley", who is one woman: Andreas takes his particulars of Dr Elijah Dewey Harmon
from her, the card gives her one sex (`female`) and seats her as a `daughter`.

So her `age_band` block carries, word for word, the refusal written for a group: "A
COLLECTIVE DESCRIPTION NAMES NOBODY, so there is no age band to draw. This row stands for
more than one person." She stands for exactly one.

**The effect is right and the reason is wrong.** No band may be drawn for her either — her
own note says why, and it is a different why: "No birth year is claimed, so no age
follows: the marriage of 30 October 1808 bounds her birth after it and nothing bounds it
before 1835." A card that states a false reason for a true refusal is a provenance defect,
which is the one thing this project does not round off.

**Acceptance:** `COLLECTIVE` stops reading a leading article as a group on its own — a
name is a group when it carries a group WORD (rest, household, children, unnamed, others,
four), not when it begins "The". `reconstruct_sex_age.py` re-runs and `--check` re-derives;
the six genuine collective rows keep their refusal word for word and `harmon_daughter_burley`
gets the refusal her own evidence earns. T-1393's completeness table then shows her age
band unanswered for the stated reason, and `CONTRADICTED_ROWS` in
`tools/profile_population_1835.py` empties.

**Careful:** the sex pass measures its male rate over the non-collective rows, so moving a
row out of `collective()` moves a denominator. Re-run the pass rather than hand-editing,
and state the before/after rate in the PR.
