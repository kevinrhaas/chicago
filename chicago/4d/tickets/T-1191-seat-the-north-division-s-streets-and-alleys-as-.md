---
id: T-1191
title: Seat the North Division's streets and alleys as platted corridors: Kinzie's Addition and the Kinzie–Michigan tier off Wright and Hathaway, with block faces, mid-block alleys and corridor control, so a north-side roof can be dealt to a lot
state: open
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
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
