---
id: T-1116
title: The 1840 head crosswalk reads a military rank as a forename: Lieut. James Allen is indexed under the key 'lieut|allen', and five other tools in this repo already strip lieut as a rank
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-13
pr: 1302
claimed_by: run 9/13/2026, 9:46:02 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T03:10:35.363Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34800062273
---

The 1840 head crosswalk reads a military rank as a forename: Lieut. James Allen is indexed under the key 'lieut|allen', and five other tools in this repo already strip lieut as a rank.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1003, which had to route around it.

`tools/crosswalk_census_1840_heads.py`'s `TITLES` set is `{mrs, mr, miss, ms, capt, dr, rev,
col, gen, major, maj, hon}` — it strips a captain and a colonel and a general, and not a
lieutenant. So `Lieut. James Allen` parses to forename `lieut`, surname `allen`, key
`lieut|allen`, and the town's James Allen is indexed under a rank. An 1840 head written
`James Allen` could not reach him; only a head written `Lieut Allen` could, and the book does
not write heads that way.

**This repo has already settled the principle twice.** T-0969 ruled that a courtesy title is
not a forename, and this set is where that ruling was applied. T-0987 stretch 8 (b44dffacb,
"a rank is not a name — Major, Judge and Doctor read as forenames") applied the same ruling
to the directories. Five tools strip `lieut` today —
`consolidate_town_cards.py` (`RANKS`), `read_fergus_1843_civic.py`, `read_fergus_obits.py`,
`survey_stated_kin.py` — and this one does not. It is a gap in one set, not an open question.

**Why T-1003 did not just fix it.** T-1003's card-merge route reaches this person through the
folded spelling `James Allen`, so the head `James P. Allen` became an L7 candidate without
the rank ever being parsed correctly — the fault is routed around for one person and still
stands for everyone. Widening `TITLES` re-keys every 1835 bearer written with a rank and
re-adjudicates the heads that were refused against them, so it wants its own measured
before/after against `counts_by_rule`, which is a run's work and not a line in someone
else's PR.

**Acceptance:** `lieut` and its spellings are stripped as a rank wherever this tool parses a
name, with the other four tools' sets as the precedent; the change is measured — every row
whose rule moves is named, with the count by rule before and after, and no head is promoted
to `matched` that a reading did not earn; `--self-test` and `--check` green on both
`crosswalk_census_1840_heads.py` and `spend_census_1840_heads.py`; `bash tools/check.sh`
green.
