---
id: T-1353
title: Mint the bounded transient cohort as reconstructed persons in camp, crew and party households, counted apart from the residents in the town census and filterable in the People view
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1178
opened: 2026-09-18
closed: 2026-09-19
pr: 1508
claimed_by: run 9/19/2026, 3:07:49 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T09:20:01.493Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35430931024
---

Mint the bounded transient cohort as reconstructed persons in camp, crew and party households, counted apart from the residents in the town census and filterable in the People view.

Piece 2 of 2 of **T-1178 — Reconstruct the transient population of 1 July 1835 as a bounded cohort: the land-sale visitors, the immigrants awaiting lots, the harbour-works gang and the crews ashore — who they were, how many, and where they slept (tents, wagons, floors, vessels) — for the camps the structure band will build**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

T-1352 has bounded the cohort: **192 to 900 persons**, with NO point reading adopted — the model
prints two candidate points with their arguments (twice the measured 1843 transient rate, 383; the
midpoint of the American's "some hundreds more", 550) and leaves the choice here. Take one, cite
`data/reconstruction/1835_transient_cohort.json`, and say which and why.

**Acceptance:**

- Reconstructed persons marked transient, grouped in `household` records of type `camp` / `crew` /
  `party`, `presence: present`, `presence_kind: transient` (a new vocabulary value — a transient is
  in the town on the day and is not a resident), each with basis and seed.
- `lives_at[]` of kind `camp` pointing at the grounds T-1214 places, or `vessel`, or
  `floor_of: <house>` for the "floor covered besides" cases.
- The town census reports residents and transients APART, and the resident counts do not move.
- The People view filters `transient`; each card says it is a visitor of the season.
- LIBERTIES entry.
- THE STANDING CONSTRAINT APPLIES: no Native or Métis person may be written here. T-1352's model
  carries the Native-visitor row as a bracket and not as people, and stage `underdocumented`
  (T-1177) is the only stage that may mint one.
- Two things T-1352 refused to supply and this ticket must resolve or do without: a crew
  complement for an 1830s lake schooner (no committed source gives one, so it seats no crews
  without one), and a strength for the harbour-works gang.

**Stop condition:** the summer crowd is in the town, counted apart from the residents, with
somewhere to sleep and a card that says it is a visitor.

**Links:** T-1178 (parent) · T-1352 (the bracket) · T-1214 (the camps) · T-1177 · T-1167.
