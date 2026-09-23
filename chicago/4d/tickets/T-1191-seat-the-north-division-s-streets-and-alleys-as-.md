---
id: T-1191
title: Seat the North Division's streets and alleys as platted corridors: Kinzie's Addition and the Kinzie–Michigan tier off Wright and Hathaway, with block faces, mid-block alleys and corridor control, so a north-side roof can be dealt to a lot
state: done
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-20
pr: 1552
claimed_by: run 9/19/2026, 12:27:10 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T06:31:49.634Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35457966596
---

The owner: *"there are a number of streets on the north side, and north west of the river from
the 1834 wright map and the 1834 hathaway map … you may need to build streets and alleys
according to that map for the housing here, there are some small lots."* Today `data/streets/
1835.json` holds the north-side names (kinzie, north_water, wolcott, market_north … michigan_north;
Kinzie's Addition tier illinois_north, cass, rush, pine, sand; ohio_north … indiana_north at
`traffic: none` with 2-point paths) but **no north-bank street has a platted corridor**:
`data/traces/street_control.json` measures eleven corridors, none north of the river, and
`tools/plat_corridors.py` returns none there; `alleys: true` on exactly two records town-wide.
Kinzie's Addition's 52 blocks are numbered and its streets seated (`kinzie_addition_street_grid.json`,
`kinzie_addition_block_numbering.json`, `seat_kinzie_addition_streets.py`); the Thompson North
Division's six corridors are read (`north_division_streets.md`, T-0451). What is missing is the
CONTROL layer that lets the lot generator and the corridor gates work north of the river.

**Acceptance:**

- `street_control.json` gains a corridor entry for every North Division and Kinzie's Addition
  street the two sheets draw between the north bank and the addition's north line (the memo's
  N +760 envelope), read off `wright_1834` (`wright_1834_nara_hup` for the fit) and
  `hathaway_1834`, with the reading recorded in `data/traces/` at the sheets' pixel positions
  and the ~20 m horizontal uncertainty stated per corridor; widths from
  `hathaway_1834_street_widths.json` (the 80 ft module where the sheet reads it; the addition's
  narrower corridors where it reads those).
- Mid-block alleys: where either sheet draws one, an alley corridor (the 18 ft module) with its
  sheet reading; where neither does, the record says `alleys: false` with the reading cited —
  absent is an answer only when the sheet was read for it.
- `plat_corridors.py` and `measure_corridor_intrusion.py --gate` now cover the north bank; the
  north-bank rule (`measure_north_bank_frontage.py`) unchanged; `data/streets/1835.json` records
  gain `corridor` + `status_1835` from the reading (platted-unopened vs worn, from the 1834
  traffic evidence the North memo cites).
- **Visible:** the street ribbons north of the river draw at their platted widths and the
  minimap shows the addition's grid; a screenshot from the Kinzie–Wolcott corner shows the new
  corridors.
- No Blender: streets are a drawn-at-load layer; `needs_bake: false`.

**Stop condition:** a generator can ask, for any north-side point, which corridor it is in and
which block face it fronts.

**Links:** T-0451 · `docs/RESEARCH/north_division_streets.md` ·
`docs/RESEARCH/1835_north_division_extent_and_infill.md` · `docs/RESEARCH/kinzie_alignment_1835.md`
· `docs/RESEARCH/north_water_street_and_the_bank.md` · `data/sources/wright_1834.json` ·
`data/sources/hathaway_1834.json`.

---

## Finding, 2026-09-20: the river is not in the reading

Putting the north bank's corridors into `plat_corridors.corridors()` changed which street
seventeen documented roofs are measured against, and sixteen of those changes are the point
of this ticket — the Steamboat Hotel stops being 203 m off State across the water and comes
to 20.47 m off Kinzie, the north-side school to 4.32 m off Clark, the Watkins school house
onto Michigan Street's own corridor. One change is an artefact, and it is recorded here
rather than fixed here because fixing it is a different ticket.

`measure_frontage_fabric.nearest_frontage()` measures a straight line from a footprint to
every committed corridor and takes the smallest. **It has no water in it.** So now that
both banks carry corridors, a roof on one bank can be credited with a street on the other,
in both directions:

- `fort_dearborn_out_building_a` and `_b` stand inside the unplatted military reservation
  on the SOUTH bank. They were outliers at 312 m and 323 m off Lake, a principal street
  the ancillary clause avoids. They now read 198.31 m and 195.52 m off Kinzie, which is
  ordinary, so no clause fires and `placement_policy_1835` reads both as CONFORMING. The
  reservation still has no street to front. Their two authored reasons had to be deleted
  because assertion 3 is a measurement and the measurement no longer supports them.
- `fort_dearborn_shop` and `fort_dearborn_us_factors_house` moved the same way and stayed
  outliers, so their reasons survive with re-measured prose.

The repair is a bank test in `nearest_frontage`: a corridor on the far side of the main
stem or a branch is not a frontage, and the project already commits the water it would
test against. That is a town-wide change to every setback reading in the tree — it would
move `measure_frontage_fabric`, `measure_face_rule`, `placement_policy_1835` and the
frontage baselines together — so it is its own unit of work and not a rider on this one.

Until it is taken, `1835_placement_policy.json` credits two reservation out-buildings with
a conformance they have not earned. Nothing is drawn differently and no building moved.
