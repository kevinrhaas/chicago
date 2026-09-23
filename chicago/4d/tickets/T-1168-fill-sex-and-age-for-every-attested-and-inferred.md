---
id: T-1168
title: Fill sex and age for every attested and inferred person: recorded where a source says, inferred from forename, office or register role where the evidence about that person allows, reconstructed from the population model otherwise — each value with its tier and reason
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-18
pr: null
claimed_by: run 9/18/2026, 2:25:44 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T07:26:24.605Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35319074035
---

99 of 1,287 persons carry a sex (84 m / 15 f); 10 carry a birth year; 9 an age. The owner asks
that "all people should have a best profile". Stage `attributes` of T-1167's writer.

**Rules, in order — the first that fires wins, and the value says which fired:**

| tier | rule | example |
|---|---|---|
| attested | a source states sex / age / birth (`biographical_evidence`, old-settler `age_1879_as_read` + `birth_year` in `data/research/old_settlers/people.json` and `death_notices.json` (757 rows with `birth_year`), the register's `adult` flag and baptism dates, Andreas's biographies) | Kimberly, Elston |
| inferred | sex from an unambiguous forename (`data/research/residents/` forename table built here from the attested 99 + the pools; ambiguous and initial-only names do NOT fire); adult status from a poll list (male, 21+ by law), a civic office, a marriage as party, a trade; child status from a baptism in window | `[?] G. Abbot` → unknown, no fire |
| reconstructed | the population model's sex × age band for the person's bucket (division, trade, household type), seeded by person id; initial-only letter-list names are sexed at the model's adult male rate for a letter list (the lists are overwhelmingly male — state the measured share from the 99) | |

Age is written as `birth_year` + `precision` (`year` / `band`) and `age_on_scene_date` derived;
a reconstructed band is the model's band, never a fake exact year.

**Acceptance:**

- Every person has `sex` and `birth_year` (or band) at some tier; counts per tier per rule
  printed before/after; zero attested or inferred value changed by a reconstructed one.
- The forename→sex table is committed with its evidence and refuses ambiguous names; a self-test
  proves `Marion`, `Jean`, `Leslie`, initials fire nothing.
- The old-settler and death-notice births are spent onto the cards they name (a spend of
  already-adjudicated rows — through `spend_old_settlers.py`'s pattern, no new source).
- The known-profile report (T-1160) re-runs and its sex/age tables now show the three tiers.
- Visible: the person card prints sex and age with the tier and reason (per T-1158).

**Stop condition:** no person is without a sex and an age band, and no value is above its tier.

**Links:** T-1167 · T-1158 · T-1161 · T-1160 · `data/research/old_settlers/`.
