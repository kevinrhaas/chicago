---
id: T-1429
title: The nearest-street reading crosses the river: a bank test for nearest_frontage, so a roof is not credited with a corridor on the far side of the water
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-21
pr: 1623
claimed_by: run 9/21/2026, 6:07:19 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T12:28:43.880Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35591950221
---

The nearest-street reading crosses the river: a bank test for nearest_frontage, so a roof is not credited with a corridor on the far side of the water.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1191 on 2026-09-20, and written up in full in that ticket's own file under
*Finding, 2026-09-20: the river is not in the reading*.

`measure_frontage_fabric.nearest_frontage()` takes the smallest straight-line distance
from a footprint to every committed corridor. That was harmless while only the south and
west grid had corridors, because everything the north bank could be measured against was
already across the water and the readings were recorded as outliers with authored reasons
saying so. T-1191 put the north bank's own corridors in the reading, and now the crossing
happens in both directions and can produce a FALSE conformance rather than a stated
outlier: `fort_dearborn_out_building_a` and `_b` stand inside the unplatted military
reservation on the south bank and read 198.31 m and 195.52 m off Kinzie Street on the
north bank, which is an ordinary street, so the ancillary clause's "avoids a principal
street" stops firing and `placement_policy_1835` reads both as conforming.

**What this asks for:** a bank test in `nearest_frontage` — a corridor separated from the
footprint by the main stem or a branch is not that footprint's frontage. The water this
would test against is already committed (`data/traces`, the terrain water mask).

**Why it is its own unit:** it moves every setback reading in the tree at once —
`measure_frontage_fabric`, `measure_face_rule`, `placement_policy_1835`, the frontage
baselines and the outlier reasons that quote distances — and each of those carries a gate
and a self-test that would have to be re-read against the new numbers.

**Acceptance:** the two reservation out-buildings are outliers again, with their reasons
restored; every reading whose street changes is stated with its before and after; no
confidence and no coordinate moves.


## WHAT THE BANK TEST IS, 2026-09-21

Two clauses, because one does not reach. Both live in
`measure_frontage_fabric.nearest_frontage`, and its docstring carries the argument.

- **The bank.** A corridor the river stands between is not that footprint's frontage.
  The water is the scene epoch's own committed planform, read off
  `data/terrain/epochs/e1834_harbor_cut/terrain_spec.json`'s `water_polygons` list
  rather than off filenames typed into the module — the same list
  `generators/terrain_gen.py` cuts the heightfield's channel from, so a reach added to
  the terrain is in this reading in the same commit. Rings the spec declares ISLANDS
  are land and are not read: the bar between the piers is ground a person stands on.
- **The submerged stretch, and the fort out-buildings are why it exists.** The bank
  clause alone does not reach them. Thompson's plat draws Kinzie Street east to the
  town line and the 1834 harbour cut crosses it: Kinzie's own centre line stands
  between 0.52 m and 4.52 m UNDER water from local east 995 to its terminus at
  [1100, 251.8], and it is the south EDGE of that drowned corridor — clipping the dry
  spit at the channel bank — that `fort_dearborn_out_building_a` reached without
  crossing anything. So a point of corridor is frontage only where the street's own
  centre line, at the station nearest it, stands on land. A stretch of street the
  harbour cut took is not a street. With that clause the two out-buildings measure to
  Kinzie's dry end instead, across the channel, which the bank clause then refuses.

Five assertions were added to `--self-test` and each is exercised on the record that
earned it, so a corridor re-drawn or a reach added to the terrain moves those lines
rather than passing quietly.

## EVERY READING THAT CHANGED, BEFORE AND AFTER

26 of 408. All of them off a street on the far bank and onto one on their own; no
footprint is left without a frontage.

    record                                before               after
    fort_dearborn_root_house              kinzie     13.34     lake      398.55
    fort_dearborn_palisade                kinzie     27.68     lake      375.81
    fort_dearborn_officers_quarters       kinzie     32.78     lake      392.71
    fort_dearborn_commandants_quarters    kinzie     32.96     lake      415.65
    fort_dearborn_blockhouse              kinzie     40.17     lake      373.89
    fort_dearborn_parade                  kinzie     42.03     lake      391.84
    fort_dearborn_magazine                kinzie     43.24     lake      388.65
    recon_1835_north_a2_048               kinzie     50.73     michigan_north  51.73
    fort_dearborn_guard_house             kinzie     52.05     lake      387.54
    recon_1835_north_d3_042               kinzie     52.12     michigan_north  55.04
    fort_dearborn_flagstaff               kinzie     53.70     lake      411.31
    fort_dearborn_sutlers_store           kinzie     60.22     lake      428.88
    chicago_lighthouse_1832               kinzie     61.77     lake      317.96
    fort_dearborn_store_house             kinzie     64.22     lake      394.94
    jb_beaubien_homestead                 kinzie     64.71     lake      360.15
    fort_dearborn_barracks                kinzie     66.04     lake      405.45
    fort_dearborn_artillery_house         kinzie     77.16     lake      401.30
    beaubien_barn                         kinzie     80.93     lake      347.65
    fort_dearborn_garrison_garden         kinzie     86.86     lake      223.16
    fort_dearborn_big_barn                kinzie     95.89     lake      270.75
    south_pier                            kinzie    114.19     lake      470.15
    fort_dearborn_wash_house              kinzie    144.13     lake      420.22
    fort_dearborn_shop                    kinzie    157.87     lake      381.64
    fort_dearborn_us_factors_house        kinzie    194.48     lake      287.59
    fort_dearborn_out_building_b          kinzie    195.52     lake      322.71
    fort_dearborn_out_building_a          kinzie    198.31     lake      312.17

Two roofs move the other way for the same reason: `recon_1835_north_a2_048` and
`recon_1835_north_d3_042` stand on the NORTH bank and were reaching Kinzie's drowned
east end; they take Michigan Street now, one metre further off, and both still conform.

## THE POLICY, AND THE THREE ROOFS THE ACCEPTANCE DID NOT PREDICT

`fort_dearborn_out_building_a` and `_b` are outliers again with the reasons T-1191 had
to withdraw, restored against the figures this reading returns.

Three more surfaced with them, and each is a real outlier rather than an exemption:
`beaubien_barn`, `fort_dearborn_big_barn` and `fort_dearborn_wash_house` were
conforming only because the street they were measured against — Kinzie, across the
water — is ordinary, and the ancillary clause avoids a PRINCIPAL street. On their own
bank the nearest street is Lake, and it is 270 m to 420 m away. Each carries its own
written reason in `OUTLIER_REASONS`. `fort_dearborn_shop`'s reason no longer quotes the
Kinzie distance the bank test retires. 54 of 77 documented roofs conform, 23 recorded
as outliers with their reason (was 59 and 18).

**No confidence moved and no coordinate moved.** No structure record was touched, so
nothing needed a bake.

## WHAT RE-DERIVED, AND THE ONE THING IT EXPOSED

`tools/reconcile_665.py` and `tools/redeal_anonymous_roofs.py --build` both read the
census and both re-derive in this commit. The redeal moves the two north-bank rows and
nothing else — no roof re-familied, re-seated or retired.

The 665 programme's documented trade share by street class moves further than that, and
the reason is worth stating rather than burying: `principal` goes from 20 buildings at
a 0.65 trade share to 39 at 0.3846, because nineteen Fort Dearborn reservation
buildings now count as principal-street buildings. **They are 270 m to 420 m from Lake
Street.** The census assigns every building to its nearest corridor with NO DISTANCE
BOUND, so a garrison that fronts no street at all votes in a measurement about the
business front. That was true before this ticket — the same buildings were voting in
`ordinary` off a Kinzie line across the channel — and this reading only moves which
bucket the noise lands in. It is filed as T-1511.
