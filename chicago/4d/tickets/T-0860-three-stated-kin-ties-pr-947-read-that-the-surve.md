---
id: T-0860
title: Three stated kin ties PR #947 read that the survey's patterns could not reach: the Beaubien brotherhood and the two Harmon sons
state: done
epic: TOWN
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 961
claimed_by: run 9/5/2026, 11:42:50 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T04:44:55.469Z
claimed_run: null
---

Three stated kin ties PR #947 read that the survey's patterns could not reach: the Beaubien brotherhood and the two Harmon sons.

**Acceptance:** the three ties carry kin rows on both people, each under a written
ruling; the Miller ruling on `dev` is untouched; the kin gate and validate.py's
reciprocity check both pass.

## Where this came from

Draining the open-PR backlog. **#947** and **#949** were rival runs at T-0734.
#949 landed (the machinery: `survey_stated_kin.py`, `kin_survey.json`,
`kin_rulings.json`, 13 rulings). #947 was parked on `hold` and, read against `dev`
before being closed, turned out to carry **three ties `dev` does not have**:

| tie | on dev |
|---|---|
| Mark Beaubien — brother of Jean Baptiste | `hh_beaubien_mark` carried NO kin at all |
| Charles Loomis Harmon — son of Elijah Dewey Harmon | `hh_harmon_brothers` carried NO kin at all |
| Isaac Dewey Harmon — son of Elijah Dewey Harmon | same |

**The owner's ruling, in session:** land the three, leave Miller as `dev` has it.
The two runs disagree on Miller — #949 landed it at `inferred`, #947 refused it
because "Samuel, the landlord" is a surname the dataset carries five times and
identifying him is a crosswalk ruling. That disagreement is NOT reopened here.

## Why the survey could not see them

**#947 adds no tools.** It is data-only, so its findings were readings a person
made, not something this survey derives. Two separate gaps:

1. **`his brother Jean Baptiste`** — the pattern reads `<relation> of <Name>`, and
   English puts no "of" after "his brother".
2. **`lists his five surviving children: 'Charles Loomis Harmon, Isaac Dewey
   Harmon, …'`** — one subject and five others, which no `<relation> <Name>`
   pattern reaches.

## Acceptance, restated as what shipped

- `PROSE_POSSESSIVE` reads `his|her <relation> <Name>`. Measured before adding it:
  10 matches over the committed prose, and the resolution step refuses the
  non-names ("his mother Potawatomi") on its own.
- The documented ellipsis rule now covers a **compound** forename, and applies
  only after the printed name has failed to resolve — so a re-read can fail to
  find somebody but cannot find the wrong somebody.
- `data/residents/kin_readings.json` — an authored seam for a reading no pattern
  reaches, whose **quote must still stand at the path it cites** or `--check`
  refuses it. It earns the right to be asked, nothing about the answer.
- Widening the net surfaced one new question and it is answered, not ignored:
  "his sons Charles Henry" is REFUSED on #947's own reading.

