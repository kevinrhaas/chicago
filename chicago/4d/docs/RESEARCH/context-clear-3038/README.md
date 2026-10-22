# T-3038 — the 1904 context city kept off the streets, the tracks and itself

The owner, 2026-10-22: "you put a building in the middle of the street, fix this and any others
that you did that", then "some white things sitting in the tracks and also some streets that dont
quite connect ... it seems odd to have streets ending like that do sharp edges for stuff like that
and make it more logical and correct, based on history of what was there".

## What was wrong on dev

`tools/build_context_1904.py` tested a projected stand-in's centre and corners against the street
grid's parcels, blocks and alleys only: never against its carriageways (18th Street's curve into
Calumet Avenue is a carriageway, not a block) and never against the Illinois Central's right of way.
The new contract, run on dev's `data/context/1904.json`, finds:

| fault | count |
|---|---|
| a stand-in's rectangle on a roadway, walk, alley, faded street or the right of way | 55 |
| one projected stand-in on another (all of them railway sheds) | 35 pairs |
| a tree in a roadway, an alley or on the tracks | 26 |
| a faded street on the right of way (the "white things in the tracks") | 2 |

East of Calumet below its curve the lots stopped 46 m behind Calumet's east line and the faded cross
streets stopped 10 m past them, in the grass. Sanborn 1911 sheet 28 draws Calumet's east lots at
20th Street running from the avenue's line back to the railway's.

The sweep of the placed 1904 structures (every sidecar footprint against the same ground) found one
more: the First Presbyterian Church (T-3009, drafted 2026-10-22) stood mirrored across 21st Street.
`site_record()` in `tools/draft_prairie_1904.py` turns v left of u, so v runs south for a
west-fronted site, and the row's v figures (measured north from the south face) were not mirrored.

## What changed

- **The sweep (`clear_city`).** Every stand-in is tested as its whole rectangle against the grid's
  carriageways, walks, parkways, curbs and alleys, the right of way with a 3 m fence strip, the faded
  streets (plus a 2 m walk for a projected one) and every stand-in already kept. It is cut back side
  by side off what it overlaps, or dropped when it would lose more than 40 % of a side. Trees keep off
  roadways, alleys, the right of way, the faded streets and every stand-in. Counts are written into
  the file (`projection.clearance`).
- **The right of way.** Read from `data/railway/1904_context.json` (verges, cinders, made ground, lake
  face). East of Calumet the lots run back to 3 m short of the west verge; a lot west of an avenue
  needs that avenue drawn clear of the railway. Faded streets are cut by the right of way and every
  end is found to 0.1 m (held 0.2 m back), so a street meets what stops it square.
- **Per-block seeds.** Each projected block draws from its own seed, so a later change to one block
  leaves the rest of the city as it is.
- **The contract** now fails on any of the faults above; `--self-test` proves each fires, including
  the owner's house on the curve, the faded street in the tracks, two stand-ins one on the other and
  a tree in Calumet's roadway.
- **First Presbyterian** is mirrored into the record's frame and stands north of 21st Street.

## Shots

`tools/qa_context_clear_t3038.mjs`, published `/1904/` app, 1280x800 full and 390x780 light;
`before-*` routes `data/context/1904.json` to dev's file (the church's before was shot from the site
published before the church fix). Stands: `curve-18th-calumet` (the owner's first view, from over the
tracks), `north-over-calumet` (the owner's second, 141 ft up), `south-past-20th` (the owner's third),
`church-21st-indiana`.

Phone cost (`browser-validation-mbefore-mobile.json` / `-mafter-mobile.json`, the same frames): the
141 ft aerial north over Calumet 1,705,536 → 1,712,206 triangles (+0.4 %; over the walking budget
on dev already, an aerial and not a smoke stand), south past 20th 737,258 → 740,552.

## Not changed

- Prairie Avenue's east lots between 16th and 18th: the right of way's reconstructed west margin
  (L-ic-tracks-2478, "the outermost tracks plus the spec's margins, smoothed") laps 1-3 m over the
  traced lots' rear lines, so the coach houses at 1701, 1709 and 1721 stand 1-2 m from the nearest
  track's centre. Both lines come from sheet 20; clamping the margin to the lots is the railway
  tool's work.
- Parts of one drawn sheet building may still overlap each other (a wing's rectangle on its main
  body's), as one building's parts do.
