# The district draft's 20th-22nd block, east side (T-2352)

Piece 2 of T-2161, the 20th-22nd block of the owner's district draft pass. The builder T-2329 wrote (`tools/draft_prairie_1904.py`) is run on sheet 35's east side, and the result is read in the actual published `/1904/` app. The west side is T-2351, and this branch stands on its builder changes (the sheet's crossed-stable outlines, `service_outline`, are what let the east side's alley buildings fill as whole buildings too).

## What stands

There are seventeen buildings on the avenue: 2001, the 2003/2005 pair, 2009 Mayer, 2011, 2013 Reid, 2017, 2021 High, 2027, the 2031-2035 limestone row (Tolman, Otis, Stone), 2101, 2109 Roloson, 2115 Armour, 2123, 2125 and the 2127-2129 flats. Behind them stand sixteen alley buildings: a stable or coach house on every lot the sheet draws one, and 2035's brick-and-frame rear building. That covers every east-side row of the T-1842 census (frontage-35-072 to -091) and every detached rear polygon the T-2340 trace owns there.

All of it is data in `data/components/prairie_1904/draft_prairie_1904.json`: block `35` now drafts both sides, its east side under its own pass and liberty (`L-draft-prairie-20-22-east-2352`), with one frontage row per address. **No builder or archetype code changes on this side.** The records re-derive under `--check`; every record that stood before this branch, the west side's included, is byte-identical, and so are their GLBs.

## The study's rulings, visible

- **2141 as a non-building frontage.** Ruling r35-2141-open-corner keeps the 22nd Street corner open in 1904; its row is `skip`, and nothing stands on it.
- **2129 is the flats' second number** (census alias), not a building. The 2127 flats stand as one building under one roof, `flats_2127_prairie`, with 2129 in its `aka`.
- **The 2031-2035 row** (ruling r35-2031-2035-row) is three houses with a shared cornice line, not three copies: one bracketed flat cornice over all three, and doors that differ (2031 north, 2033 south, 2035 toward the corner).
- **2013's 'Fire Proof Construction'** is a construction class, not a facade (census note). On this coarse copy the trace reads its colour as frame; the record keeps the register's masonry.
- **The 2003/2005 pair** is attested as attached on a party wall, so the two share one design with mirrored doors.
- **1911 garages are 1904 stables.** Every GARAGE on the alley is backcast as the census reads it. 2035's rear building, whose use the census does not read, stands as an outbuilding (`stone_house_2035_prairie_rear_building`).

## Landmark silhouettes (from the register, not bespoke)

- 2009 Mayer: the kit's shaped street gable for its ogee gable, two bays wide.
- 2011: a turret under a cone on the south front corner, over the stone rounded bay the sheet draws.
- 2021 High: a steep gable to the avenue and a turret under a cone on the north front corner.
- 2013 Reid: a flat roof behind a plain heavy cornice, central entrance.
- 2115 Armour: the Second Empire mansard with dormers, central entrance.

## Captured and measured

Captured with `node tools/qa_draft_t2352.mjs` on the published `/1904/` app. *Before* is the tree of T-2351's head as this branch took it (its west-side records committed but not yet compiled into the scene, so the before shots show the block empty on both sides). *After* is this branch. Desktop is 1280×800 at full detail, and phone is 390×780 at light. There are six stands: the east walk south from 20th Street, across the avenue at 2009 and at 2115, the east walk north from 22nd Street, the east alley, and the air.

All four runs had **0 page errors and 0 failed requests**, and every stand was within the detail budget. All six named records (`mayer_house_2009_prairie`, `reid_house_2013_prairie`, `otis_house_2033_prairie`, `armour_house_2115_prairie`, `flats_2127_prairie`, `house_2125_prairie_coach_house`) are placed in the after runs.

Because *before* had neither side of the block compiled, the delta below is the **whole block, both sides**: 59 structures (91 → 150 in the scene), 26 of them T-2351's and 33 this branch's.

| | load to ready | JS heap (after GC) | draw calls at the stands | triangles at the stands |
|---|---|---|---|---|
| desktop before → after | 25.7 → 35.7 s | 24.7 → 28.9 MB | 24-61 → 26-61 | 0.10-1.56 M → 0.23-1.75 M |
| phone before → after | 12.7 → 13.2 s | 24.6 → 28.8 MB | 17-51 → 21-53 | 46-478 k → 155-592 k |

This side's 33 GLBs add 881 KB of web derivatives (4.62 MB of masters). The renderer batches by material key, so draw calls rise by at most four. The phone, the release gate, loads within half a second of before and gains 4.2 MB of heap. The desktop's longer load is on this runner's software GL at full detail, where every one of the block's 59 new GLBs is fetched and decoded before ready; it is a relative reading, not a device claim, and the same holds for `frame_ms_median` in the JSON (up roughly 10-60 % at the stands that face the block).

## Not drafted here

- 2005's 16 ft brick wall on its south line: the draft archetype draws no boundary walls (T-1912).
- Rounded and canted bays stay square-cornered projections, and 2109's veranda tower and 2115's cresting are left to their tickets, as the register asks.
- Several narrow party-wall fronts (2011, 2013) fit as a main body and a side wing rather than one rectangle, because the coarse copy's trace steps along their side walls; T-1915 and T-1916 refine them.
