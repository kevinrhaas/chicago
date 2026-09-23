---
id: T-0010
title: Finish the heightfield east
state: done
epic: GROUND
requested_by: loop
seen: true
effort: M
legacy_id: T-E3
parent: null
opened: 2026-08-17
closed: 2026-08-22
pr: 313
claimed_by: run 8/22/2026, 1:24:06 PM CT
blocked_on: null
needs_bake: true
---

Finish the heightfield east (= S2e's remaining band): ground a visitor can walk onto that
is not there today. Deep history: § T-E3 (~7347). NEEDS THE BAKE.

**Acceptance:** the eastern band walks; shoreline per the 1834 map ruling already recorded.

---
**MEASURED 2026-08-22 by the T-0105 run, which passed over this ticket and owes the reason.
It reads as ALREADY DELIVERED, by S2e parcel (b) on 2026-08-11 — three months of tickets after
the ROADMAP box that became this card was written, and the box (§ T-E3, authored 2026-08-14)
never caught up.** The next run should verify and close it rather than build it again.

* `data/terrain/epochs/e1834_harbor_cut/heightfield.json` carries
  `box_local_enu_m {"e": [-320.0, 1700.0], "n": [-400.0, 400.0]}` — S2e's own requirement was
  "the box must reach about E +1700", and `terrain_spec.json § box_derivation.e_max` argues that
  number off the north pier's 1835 head rather than rounding to it.
* The eastern band is modelled ground, not a flat fill: E +800..+1200 is **90.6 % dry** with
  relief from -5.30 m to +3.75 m, E +1200..+1700 is 36.0 % dry as the shore and the bar take over.
* It carries buildings: the fort complex stands 832 m east of where the field used to stop, and
  STATUS records that twelve of its fourteen structures land on it.
* The shoreline half of the acceptance is in force too — `terrain_spec.json § shore_runs` takes
  `south_shore_harbor_reach` and `north_shore_harbor_reach` from `shoreline.geojson`, which is the
  Wright 1834 trace this ticket names.


---
**VERIFIED AND CLOSED 2026-08-22.** The delivery claim above is confirmed, and closing it
turned up the part nobody had done.

**The acceptance, measured rather than argued** — `tools/measure_east_band.mjs`, written for
this and re-runnable by anyone who doubts it:

* the field used to stop at local **E +320.0** (the 257² box of 2026-08-10). It reaches
  **E +1700.0** now — S2e's own stated requirement, met exactly, and **1,380 m of ground
  gained east**.
* the band is modelled ground, not a lid: E +320..800 is **91.2 % dry**, E +800..1200 is
  **90.6 % dry** with relief from −5.30 m to +3.75 m, and E +1200..1700 is **36.0 % dry** as
  the shore, the cut and the bar take over.
* **229 placed 1835 records stand east of the old edge**, 228 of them on the field and all 228
  over dry ground. The 229th, `heacock_house_monroe`, is off the field to the **south** and
  says so in its own note — that is T-0026's ground, not this ticket's.
* **it walks.** All 228 on-field stands were taken through the real walker in a real browser
  and all 228 stood: on the modelled grid, with the eye exactly one eye-height over the floor
  and the floor never below the field. Two of them — `slough_log_bridge` and `north_pier` —
  stand on their own DECK rather than on the field, which is what a deck is for. A four-leg
  east-bound transect from the old edge to the fort, driven on the W key, moves on every leg
  and never leaves the grid.
* the shoreline half is in force: `terrain_spec.json § shore_runs` takes
  `south_shore_harbor_reach` and `north_shore_harbor_reach` from the Wright 1834 trace in
  `shoreline.geojson`, which is the ruling this ticket names.

**AND THE PART THAT WAS STILL OPEN, which is why this run cost more than a state change.**
The ground arrived on 2026-08-11; `docs/LIBERTIES.md` L17 was revised the same day and both
piers' `ground_contact` blocks were regraded. **Nine records were never told.** They said, in
the present tense, on the card a visitor reads, that they stood outside the modelled box on no
ground at all — `cobweb_castle`, `steamboat_hotel`, `jb_beaubien_homestead`,
`watkins_school_house`, `brickyard_north_side`, `newberry_dole_warehouse`, `slough_log_bridge`,
`north_pier`, `south_pier`. Every one of them has stood on traced ground for eleven days. The
notes are corrected in place, dated, with the superseded reasoning kept and the field's actual
reading under each building recorded. No confidence moved, no citation was added or removed,
and no coordinate changed — prose is stripped from the mesh input hash, so none of this
costs a bake.

Left standing deliberately: `clybourn_cabins` and `clybourn_slaughterhouse`, whose "far outside
the modelled terrain" is about the ATTESTED site being miles up the North Branch and is still
true; and `heacock_house_monroe`, which is genuinely off the south edge.
