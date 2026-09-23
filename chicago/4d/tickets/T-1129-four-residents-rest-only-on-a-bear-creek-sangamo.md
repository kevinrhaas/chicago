---
id: T-1129
title: Four residents rest only on a Bear Creek, Sangamon County marriage, and their cards say the church list names them at Chicago
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-17
pr: 1378
claimed_by: run 9/17/2026, 12:03:47 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T06:38:38.472Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35184106653
---

Four residents rest only on a Bear Creek, Sangamon County marriage, and their cards say the church list names them at Chicago.

**Found by T-1128, 2026-09-14**, which had to rule on the register adult "Mary Durbin" and
looked at the card she was supposed to merge into.

`hh_durbin_mary` says, in its arrival note and again on the person: *"church_1833_1835 names
this person at Chicago by 20 May 1834."* The record it cites, `st_cyr_marriage_002_2`, says the
opposite in capitals: *"NOT CHICAGO. Footnote 5 on this page places the last three couples of
May 1834 at Bear Creek, Sangamon County, Illinois, in the home of Hy Durbin ... This person is
not evidence of anybody standing in Chicago."* `at_chicago` on that record is `false`.

It is not one card. Held against both church record files, FOUR people in `data/residents/`
have exactly one source and every church reading behind it is `at_chicago: false`:

| household | person | record | place |
|---|---|---|---|
| hh_durbin_mary | Mary Durbin | st_cyr_marriage_002_2 | Bear Creek, Sangamon Co. |
| hh_simmons_john | John Simmons | st_cyr_marriage_002_1 | Bear Creek, Sangamon Co. |
| hh_vincent_john | John Vincent | st_cyr_marriage_003_1 | Bear Creek, Sangamon Co. |
| hh_logdson_cery | Cery Logdson | st_cyr_marriage_004_2 | Bear Creek, Sangamon Co. |

These are the three couples of St Cyr's May 1834 journey down the state, married in a house in
central Illinois, standing in a layer that is meant to be the people of Chicago on 1 July 1835.
The mint read the register as a Chicago roll — which is the exact failure T-0573's own reading
note was written to prevent — and the arrival sentence it generated is a false statement in a
provenance artifact, not merely a placement error.

T-0841 is open on a different question about the same register (the grade of its keeper) and
does not own this one: this is about people the mint took FROM the list, not about the priest.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `tools/mint_civic_residents.py` (or whichever step spends `church_1833_1835`) must not mint
  a person whose every reading is `at_chicago: false`, and must PRINT the refusal, as it prints
  its others. The rule is in the tool, re-derivable, not a hand edit to four JSON files.
- The four cards are removed or re-stated by a rebuild of the layer, not by hand; whichever it
  is, the card must not claim Chicago on a record that says Bear Creek.
- A gate catches the next one: `check.sh` fails if any resident's sole evidence is a set of
  church readings that are all `at_chicago: false`.
- The count in every derived artefact that reads the layer moves with it, and the run says by
  how much rather than leaving a reader to diff.
