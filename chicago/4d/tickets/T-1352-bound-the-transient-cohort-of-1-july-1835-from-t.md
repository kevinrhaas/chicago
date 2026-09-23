---
id: T-1352
title: Bound the transient cohort of 1 July 1835 from the sources and say where it slept: the bracket's size and composition, and the camp-ground candidates committed for T-1214 — a derivation that writes no person
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1178
opened: 2026-09-18
closed: 2026-09-18
pr: 1496
claimed_by: run 9/18/2026, 7:36:23 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T02:11:51.965Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35409558514
---

Bound the transient cohort of 1 July 1835 from the sources and say where it slept: the bracket's size and composition, and the camp-ground candidates committed for T-1214 — a derivation that writes no person.

Piece 1 of 2 of **T-1178 — Reconstruct the transient population of 1 July 1835 as a bounded cohort: the land-sale visitors, the immigrants awaiting lots, the harbour-works gang and the crews ashore — who they were, how many, and where they slept (tents, wagons, floors, vessels) — for the camps the structure band will build**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

- A gated, derived model at `data/reconstruction/1835_transient_cohort.json` with a report beside
  it, bounding the transient cohort of the scene date as a RANGE with a stated method and a named
  comparandum per figure — and stating outright where the record bounds nothing, rather than
  carrying an invented number there.
- The camp-ground candidates committed as `data/reconstruction/1835_camp_grounds.json`, each with
  the sentence that suggested it, its confidence, and the COMMITTED geometry its extent resolves
  from — the file authors no coordinate.
- `tools/check.sh` re-derives both and holds every quoted sentence to the words the corpus
  carries, so a re-extraction that drops one fails rather than leaving the figure standing.
- A LIBERTIES entry for the reading that turns a phrase into a band.
- NO PERSON IS WRITTEN. The stage `transients` stays unimplemented and T-1353 mints the cohort.

**Stop condition:** the summer crowd of 1 July 1835 has a defensible size, a composition, and a
list of places it slept — all of it re-derivable, and none of it a person.

**Links:** T-1178 (parent) · T-1353 (the minting) · T-1214 (the camps) · T-1161 · T-1164 · T-1166.
