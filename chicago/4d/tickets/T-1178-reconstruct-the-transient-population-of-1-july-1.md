---
id: T-1178
title: Reconstruct the transient population of 1 July 1835 as a bounded cohort: the land-sale visitors, the immigrants awaiting lots, the harbour-works gang and the crews ashore — who they were, how many, and where they slept (tents, wagons, floors, vessels) — for the camps the structure band will build
state: split
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-18
pr: null
claimed_by: run 9/18/2026, 7:34:43 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T00:36:09.893Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35409558514
---

The owner: *"there may be people who are completely transient and living in a tent or on the
street … Maybe there are tents or other encampments defined further out for some people? If
something like that is historically accurate good."* The June 1835 land sales filled every bed
and every floor; the population model (T-1161) carries a transient bracket separate from
the residents. Stage `transients` of T-1167.

**Rules:** the bracket's size and composition (male, 20–40, speculators and their agents,
immigrant families with children waiting on lots, the pier gang, sailors) → reconstructed persons
grouped in `household` records of type `camp`/`crew`/`party`, `presence: present`, `presence_kind:
transient` (a new vocabulary value — a transient is in the town on the day and is not a resident),
`lives_at[]` of kind `camp` pointing at the camp records T-1214 will place, or `vessel`, or
`floor_of: <house>` for the "floor covered besides" cases — each with basis and seed. Evidence for
WHERE camps stood is written here from what the sources say (Andreas, the *American*'s June–July
issues, the reminiscences of the sale) with the candidate ground stated as a polygon list for
T-1214 — the lake shore south of the fort, the prairie edge west of the Canal Street approach,
Wolf Point, the North Side commons — each `reconstructed` with the sentence that suggested it.

**Acceptance:** the transient bracket filled; the census's residents are NOT inflated by it
(the town census reports residents and transients separately); the camp-ground candidates
committed as `data/reconstruction/1835_camp_grounds.json`; LIBERTIES entry; visible: the People
view filters `transient`, and each card says it is a visitor of the season.

**Stop condition:** the summer crowd is in the town, counted apart, with ground to stand on.

**Links:** T-1167 · T-1161 · T-1164 · T-1214.
