# The 1812 ground: the 1834 zone table with the works taken out

**Date:** 2026-10-02 · **Ticket:** T-2002 (piece 1 of T-1243, itself piece 2 of T-0468) ·
**Subject:** `data/terrain/epochs/e1830_natural/terrain_spec.json`, the zone table the 1812
Fort Dearborn landscape stands on · **Outcome:** an overlay that accounts for every block of the
1834 spec, five 1812 blocks of its own, the isthmus of L240 surfaced, and the old channel's
west bank left on Wright and graded conjectural where Harrison disagrees with it.

## 1. Why an overlay and not a copy

The 1834 spec (`e1834_harbor_cut`) has 37 top-level blocks in 1,713 lines. Most of them describe
**natural** ground: the three divisions' plain and ridge (dossier zones 3, 8–13, 18, 19), the
fort's flattened mound (zone 6), the sand hills (zone 5), the margin marsh (zone 11) and the
sloughs (zone 14). Nothing between 1812 and 1833 moved any of that. The rest describes **works**:
the 1833–34 cut, the bridge approaches of 1832–35, and the street sections of a town platted in
1830.

A copy would carry both kinds, and it would drift from 1834 as soon as 1834 was corrected. So
the 1812 spec names every 1834 block in `inherits.blocks` and gives each one a `take` and a
`why`:

| take | blocks | what it means |
|---|---|---|
| carry | 22 | the 1834 block as stated (grid, divisions, mounds, marsh, swales, bank, the lake rules, the evidence limit, …) |
| carry_except | 3 | `reaches` without the cut and with the old channel replaced; `dunes` without the 1835 boarding house's keep-clear; `surface_materials` with the bar's row moved to the spit |
| replace | 5 | `water`, `water_polygons`, `shore_runs`, `islands` and `not_modelled_in_this_box`, each by an 1812 block |
| drop | 3 | `approaches`, `approaches_note` and `street_sections`, because there was no bridge before 1832 and no street before the 1830 plat |
| own | 4 | the prose and identity of the file |

`tools/check_terrain_e1830.py` refuses an 1834 block that is not on the list. So a block added to
1834 next month turns this gate red until somebody decides what it means for 1812, and nothing
reaches the 1812 ground by default. Its `resolve()` builds the effective table, and that is what
the generator (T-2003) is meant to import.

**The box is 1834's, whole.** T-0464 carried it to Twenty-Second Street explicitly as "a frame
the 1812 and 1880s epochs can stand in". It contains the fort, the whole pre-cut mouth and the
corridor to Eighteenth Street. **South of Twelfth Street every vertex is conjectural** under the
carried `evidence_limit`, and the battle ground is south of Twelfth. That ground is modelled so
the scene has a floor, and it is not a reconstruction from evidence. The spec says so in its
scope.

## 2. The five 1812 blocks, and the zone each cites

| block | figure | zone | grade | the argument in one line |
|---|---|---|---|---|
| `lake_stage_1812` | Z 0, bound −4 to +2 | 2 | reconstructed | no 1812 stage is recorded; the 1835 plane keeps the epochs comparable, and § 1.2's 576–582 ft ASL bounds it |
| `spit_1812` | crest +4, face 12 m | 7 | reconstructed | the 1834 bar's surface carried to the spit: four of the 1834 spec's five reasons for zone 7's low end hold for 1812; the high-water one is an 1835 fact and is dropped |
| `isthmus_1812` | 100 ft wide, crest +4 | 7 | reconstructed | § 3 |
| `outlet_channel_1812` | bed −4 | 26 | reconstructed | zone 26's deep end, because in 1812 this channel carried the whole river; not zone 20's −12 to −18, because the bar "admitted only boats" |
| `north_lake_shore_1812` | a chord, then 1834 | 28 | reconstructed | sand caught by the pier was not there before it, so the 1812 shore lay west of 1834's; the chord is the least-land line the two committed points allow |

The planform blocks (`water_bodies_1812`, `shore_runs_1812`) are graded `inferred`, which is the
grade of the 1812 shoreline they read (T-1242). No block is better than that.

## 3. The isthmus (L240) gets a surface

L240 left the attachment `inferred` and asserted no ground across it, and it named this ticket as
the place to decide. **Surfaced**, because a gap in the spit puts a river mouth where the cut was
later dug. That would be the 1834 harbour drawn into 1812.

* **Where:** on `spit_attachment_gap_1812` itself, the 129.1 m line from the spit root
  (E +1234.93, N +314.65) to the bar's north-west corner (E +1318.62, N +216.38), bearing 139.6°.
  The river's turn south is on its south-west side and the lake on its north-east side.
* **Width, 100 ft:** zone 7's low end. Both ends are fixed and neither face has a reading, so the
  narrowest neck zone 7 allows is the least land invented. The bar's trace a little south is
  108 m wide at N +205, and that is recorded as the upper alternative.
* **Height, +4 ft:** the spit's. A lower neck is a breach, which is the landform the February
  1834 storm made. A higher one is the zone 3 ridge.

**A finding on the way:** Wright's bar is **108–164 m** wide over most of its length, which is
wider than zone 7's stated 100–300 ft (30–91 m). The trace is the reading, so nothing is narrowed;
the dossier's width row should be read as about the spit's neck, not its body.

## 4. The old channel's west bank (T-1286's question)

T-1286 measured Harrison 1830 against the derived shore. Near the fort the two agree, but down the
old channel Harrison's west bank runs 40 m west of Wright's at 150 m from the fort, 71 m at 200 m,
and then a median 120 m, worst 157 m. He letters "Old Mouth of River very shallow" at local
N −69, which is 357 m north of the adopted station. The ticket asked which of three things this
is.

* **(a) the single-anchor transform failing away from the fort:** this is weighed against. A
  rotation large enough to move the bank 120–157 m would throw the main stem out by about 85 m,
  where the two sheets agree to about 20 m. A local distortion of the 1884 re-engraving is not
  excluded.
* **(b) the plate's settler-memory additions:** this stays open. The plate admits them, and its
  source record says no line can be separated from them.
* **(c) a mouth that really moved:** the answer splits.
  * *For the mouth, against.* Littoral drift here runs south, so a natural outlet migrates south
    as its spit grows, not 357 m north. Wright's 1834 bar tip also stands 9.2 m from
    Swearingen's 1803 station. Harrison's "old mouth" at N −69 reads better as one of the
    soldiers' cuts of 1816–28, which were dug near the fort.
  * *For the bank, open.* A channel that carried the river until 1833 could have been wider in
    1812, which is the direction Harrison draws. But one year of silting does not move a bank
    120 m.

**Verdict: undecided.** So the spec does what the ticket asked for when the question cannot be
closed. The bank stays on Wright, by the owner's ruling of 2026-09-17, and so does the outlet.
Every vertex of the channel, its west bank, and the ground within 157 m west of it, from N −69 to
the outlet at N −426.75, is emitted **conjectural** (`channel_west_bank_ruling`). Any pre-1833
survey of the reservation's south line, or a second scaled sheet that draws the channel, would
decide it.

## 5. What this leaves open

* **Nothing is generated.** The 1812 river polygon (`water_bodies_1812.mouth`), the heightfield
  and the ground and water meshes are **T-2003**, which imports `resolve()` and bakes them.
* **The 1812 blocks are deliberately not named like `compile_scene.GROUND_GROUPS`.** A block in
  one of those groups goes on the Evidence panel and is held to the generator's `CONSUMED` map,
  and wiring that map is the generator's job. The gate refuses the collision until then.
* **Liberties:** L362 (the isthmus), L363 (the shore north of the root) and L364 (the stage and
  the outlet bed).
