---
id: T-1128
title: Four adults of St Mary's register have an exact namesake in the residents layer and no ruling on either: Solomon Juneau, Josette Chevalier, Patrick Carroll and Mary Durbin
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-14
pr: 1343
claimed_by: run 9/14/2026, 5:03:19 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T22:49:42.415Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34901836035
---

Four adults of St Mary's register have an exact namesake in the residents layer and no ruling on either: Solomon Juneau, Josette Chevalier, Patrick Carroll and Mary Durbin.

**Found by T-1110, 2026-09-14**, which rebuilt `st_marys_baptisms_crosswalk.json` against a
residents layer that had grown from 849 people to 1,308 since T-0503 wrote the pass. Four of
the adults that pass had filed as `no_candidate` — nobody of that surname in the town — now
reach a person whose name folds *identically*:

| register adult | readings | at Chicago | entries |
|---|---|---|---|
| Solomon Juneau | 4 | yes | 1833/5, 1833/8, 1833/10, 1834/17 |
| Josette Chevalier | 3 | yes | 1833/11, 1833/12, 1834/12 |
| Patrick Carroll | 1 | yes | 1835/1 |
| Mary Durbin | 1 | no | 1834/8 |

T-1110 did NOT rule on them, and deliberately. A merge in this file needs a written rule
naming both spellings verbatim, and these four have none; the standing surname-only refusal
could not carry them either, because its stated ground is that *no forename agrees* and here
one does — filing them under it would have put a false sentence in a provenance artifact. So
they sit in a fourth derived bucket, `exact_name_unruled`, which is a worklist and not a
verdict: `counts.all_places.exact_name_unruled` is 4, `counts_by_ruling.exact_name_unruled`
is 9 readings, and `exact_name_unruled[]` in the crosswalk names the pairs.

An exact name is evidence and it is not proof — Solomon Juneau is the Milwaukee trader, who
had every reason to stand godfather at Chicago and no reason to live there, and that is
exactly the kind of case the ladder wants ruled rather than assumed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Each of the four is ruled ONE BY ONE, in `MERGES` or `REFUSALS` in
  `tools/read_st_marys_baptisms.py`, where the rule is re-derivable — never by editing the
  emitted JSON.
- Every rule names both spellings verbatim and cites what decided it. A merge that rests on
  the identity of the name alone is a refusal, and says so.
- Solomon Juneau is ruled against his Milwaukee residence explicitly: sponsorship at a font
  is not residence, and `at_chicago` on a reading is about the ENTRY, not the man.
- `exact_name_unruled` reaches 0, `python3 tools/read_st_marys_baptisms.py --check` stays
  green, and `tools/check.sh` (which gates it since T-1110) passes.
