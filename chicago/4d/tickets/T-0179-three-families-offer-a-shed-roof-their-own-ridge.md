---
id: T-0179
title: Three families offer a shed roof their own ridge band cannot carry: C1, F1 and F4
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 384
claimed_by: run 8/26/2026, 11:27:30 PM CT
blocked_on: null
needs_bake: false
---

Three families offer a shed roof their own ridge band cannot carry: C1, F1 and F4.

Found by T-0148's sweep, `tools/measure_ridge_reach.py`, which asks of every family and every
roof form its `roof` column names whether the authored `ridge_ft` band is reachable from some
eave in the eave band at some pitch in the pitch band, at every footprint in the footprint band.
Every family passes on the gable reading. Three fail on the shed one, because a shed's roof
climbs the WHOLE span rather than half of it and the ridge band was written for the gable:

* **C1** "front gable or shed", ridge 15-20 ft — 231 of 441 footprints unreachable, first at
  14x25 ft.
* **F1** "gable or shed", ridge 18-24 ft — 399 of 441, first at 18x33.8 ft.
* **F4** "gable or shed", ridge 17-24 ft — 441 of 441. No footprint in F4's own band can be
  roofed as a shed inside its own ridge band.

**Nothing is broken today and that is why this is a ticket and not a gate failure.** No
generator deals a shed to C1, F1 or F4: `_roof_kind` in both sampling parcels reserves the shed
for D2, A3, A4 and A5. So the gate passes a family when ANY form it names is reachable, and
prints these three as NOTE lines. The day a parcel deals one of them a shed — which the
crosswalk plainly permits — it will be built outside its own ridge band and the ridge gate will
bank it.

**Acceptance:** either the three families' shed reading is retired in the crosswalk (an owner
call about the specification, so `block --owner` if that is the answer), or the generators state
in one place that these families are gable-only and why, and `tools/measure_ridge_reach.py`
gates that statement against what the generators actually deal so the two cannot drift.

**Links:** T-0148 (opened this) · L176 · `tools/measure_ridge_reach.py` ·
`data/reconstruction/1835_family_archetype_crosswalk.json`.

---

## THE ANSWER (2026-08-27)

**Two of the three held, the third is refuted, and a fourth family nobody had measured joins them.**
`tools/roof_form.py` sweeps a family's whole authored footprint band against the shed the archetypes
ACTUALLY build, rather than the shed the sweep assumed:

| family | this ticket | measured | why the two differ |
|---|---|---|---|
| C1 | 231 of 441 | **231 of 441** | holds — `frame_storefront._shed_roof` falls back-to-front, so the run is the depth, and it never reads `gable_front` |
| F1 | 399 of 441 | **399 of 441** | holds — `outbuilding` with no open side, fall down the 32-50 ft depth |
| F4 | 441 of 441 | **0 of 441** | **REFUTED.** F4's own entry says `levels: 1/open`, "open posts with slab boards", "part-open sides"; an open long side turns `shed_axis` to fall across the 24-36 ft WIDTH (L73), and there the ridge band is reached at every footprint |
| W5 | not named | **84 of 441** | **ADDED.** W5 authors no rise:run, and the sweep reports a family with no pitch band before it tests any FORM — so W5's shed had never been measured at all |

So the refused set is **C1, F1 and W5**, and the sweep that produced the ticket's list could not see
one of its own cases.

**Acceptance, taken by the second route.** The crosswalk is not edited — retiring a family's shed
reading is the owner's, and L182's "How to resolve" puts the question to him. What is done instead:

- **One place.** `tools/roof_form.py` states which form every family is built with. It had five
  places, one literal per parcel, and they had already drifted: three named A5 among the shed
  families and two did not. One roof stands on the difference (`recon_1835_south_a5_044`) — filed as
  **T-0208**, held in `roof_form.AWAITING_BAKE` and banked by the gate so it cannot spread.
- **The refusal is recorded where a visitor can read it.** Thirteen committed roofs — nine C1, two
  F1, two W5 — carry a new paragraph on `roof_type` naming the offered form, the span a shed would
  climb, the ridge band it would miss and the count of the family's own footprints that miss it.
  Notes are not hashed into the staleness recipe, so no geometry moved and no bake is owed.
- **The gate holds the two together, five ways**, and `--self-test` breaks each in memory:
  a family dealt a shed its band cannot carry; a refused family's record without the refusal;
  a parcel that grows its own copy of the shed set; the open-sided table drifting from the
  crosswalk's words; a second parcel opting out. The sweep's grid and reach test are
  `roof_form`'s, so the gate and the generators answer the same question by construction.
- **A model bug fixed on the way.** `tools/ridge_model.py` turned a shed's span with `gable_front`.
  All three archetypes that build a shed ignore the orientation entirely and `frame_tavern` has no
  shed branch at all. No committed GLB is a shed on those archetypes, so `measure_ridge_band.py` —
  the gate whose whole job is to keep the model honest — had nothing to compare it against.

Recorded as **L182**.
