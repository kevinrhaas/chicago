# 2021's stable on the east alley, 20th-21st: the district draft refined onto K12, its gable tin-clad over a one-storey south end (T-1938)

`high_house_2021_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2352) onto
the K12 coach-house kit (`k12_coach_house`), facing the alley on its east (`alley_side: east`), as 2001's, 2009's,
2011's, 2017's, 2027's, 2031's, 2033's, 2109's, 2123's and 2125's did. The draft rules' `skip` now names census row
`s35-2021-rear`, so the draft builder stands no second building in its place, and its phase is `as_standing_1904` (the
`__draft_1904` master and web derivative are retired). Liberty `L-k12-2021-stable-tin-1938`; the draft block liberty
`L-draft-prairie-20-22-east-2352` records the retirement.

It is the eleventh of T-1938's alley buildings to leave the draft. Still the draft's: 2013 (Reid, the image gate),
2035 (brick and frame), 2101 (a two-storey block on 21st Street with a one-storey range south of it along the alley)
and 2115 (brick, the largest on the alley).

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m a pixel
([crop](sanborn-1911-sheet-35-2021-stable.jpg), columns 1040-1190, rows 585-690, four times). One pink (brick)
outline on the alley, divided by a line across it: a part lettered '2' and GARAGE to the north and a part lettered '1'
to the south. Along the dividing line, on a strip of the sheet's yellow (frame), the note **TIN CL. 2ND**. No picture
of this alley is known, so the building has no image gate.

Median darkness profiles, peaks refined by a parabola through the three highest samples. The same rule reads 2017's
south wall at row 598.26 against #2376's 598.21, and 2027's north wall at 681.89 on the lot line #2345 stands it on.

| line | reading |
|---|---|
| alley line | column 1170.93 (rows 605-678) |
| yard (west) wall | column 1121.22, one line for both parts |
| north wall | row 601.16, 0.54 m south of 2017's stable (598.26); the key's fire-wall sign on the alley line at that junction |
| dividing line | row 659.99: the two-storey part 10.934 m along the alley |
| south wall | row 679.26: the one-storey part 3.581 m; 2027's barn 0.49 m south (681.89) |
| size | 9.239 m deep, 14.515 m along the alley in all |
| storeys | '2' and '1' |
| marks | a window mark on the two-storey part's alley wall (strokes over rows 631-640), 6.38 m from the north wall; a solid dot in each part's south-east corner (the key's vertical boiler, as this project reads the sheet's dots; not built); small figures inside the north and south walls (not read) |
| house behind | its one-storey rear range 11.94 m west (column 1057.02, rows 605.1-639.7) |

**The tin note.** It lies along the one line between the two parts, so it is read as that wall's second storey framed
and clad in tin over a brick first storey: the gable that rises above the one-storey part's roof. The T-1842 census
words it "its upper storey tin-clad", which can be read as the whole upper storey; a note meaning that would more
likely be written across the part than along one wall line. The liberty records both readings, and a finer copy of the
sheet settles it.

## What K12 builds

The kit in mirror image (`mirror`), as 2017's and 2123's, so its party wall stands at the north end where the
fire-wall sign is (2017's record leaves its own south end an open gable) and its open gable is the south end. The
one-storey part is the kit's range (T-1932), carried on south past the gable on the alley wall's line and as deep as
the stable, as 1730 Prairie's is, under the kit's flat roof at 3.2 m. Its south end faces 2027's barn across half a
metre and carries no opening.

On the alley, counted from the party wall: a carriage bay 3.0 m clear under the hatch and hoist, the mark as a stable
sash, and a man door, each with a loft sash. On the yard, counted from the gable: a stable sash, a door and a stable
sash, each with a loft sash, the door where the workyard walk leaves for the house's rear range. On the range, a door
on the alley and a sash on the yard. The roof is the kit's gable at 40 degrees, as 2017's and 2027's stables of about
this depth take.

## What the kit gained

`gable_upper: tin` (`generators/archetypes/k12_coach_house.py`) builds a brick building's open east gable in two
storeys: brick from the foot to the loft floor (`storeys.ground_m`, 3.6 m, the storey line the note's "2nd" names, and
above the range's roof at 3.45 m), and above it a framed wall clad in sheet tin to the apex, in the gable's plane and
to its thickness, in a new `tin_sheet` material (a weathered dull grey; reconstructed). The brick storey's top is
closed and the tin storey's foot lies on it, so nothing doubles. An opening may sit on either storey (`gable` or
`gable_upper`) but not across the line, and the field is refused on anything but a brick building's open east gable.

It changes no coach house already built: `python3 generators/k12_emit.py --check` re-emits every other K12 GLB to the
same bytes (their manifest entries move only because the kit, an input of each, changed). The kit's specimen GLB is
regenerated because it carries every material. `tools/check_coach_house_kit.py` adds `gable_upper` to the elevations
it closes: 36 variants, every piece seated or rooted, no doubled face, every elevation closed, every opening cut
through. Its self-test gains two cases (the tin storey 5 mm off the brick, refused as unseated; the tin storey left
out, refused as an open elevation).

`validate.py --stale`: 0 errors. `draft_prairie_1904.py --check`: 147 draft records. Back yards: 141 lots, and
2021's lot now carries two coach walks to the stable's yard door where the draft's outline had left an alley walk.

## In the app

`QA_TARGET=2021 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the alley from
the north and from the south, the yard face, the tin gable over the range from the yard, and the air) at 1280x800
full and 390x780 light. Both viewports: 0 page errors, 0 failed requests, all four records placed (this stable, the
house, 2017's stable and 2027's barn), no stand over the detail budget (`browser-validation-after-<viewport>.json`,
`after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 52.3 s | 125.6 MB | alley from north | 1,939 | 2.21 M |
| | | | alley from south | 2,853 | 3.69 M |
| | | | yard face | 876 | 0.94 M |
| | | | tin gable from the yard | 1,055 | 1.00 M |
| | | | air | 1,940 | 2.37 M |
| mobile, light | 31.4 s | 141.2 MB | alley from north | 1,267 | 0.38 M |
| | | | alley from south | 2,365 | 0.73 M |
| | | | yard face | 493 | 0.26 M |
| | | | tin gable from the yard | 677 | 0.32 M |
| | | | air | 2,579 | 0.89 M |

Times are this runner's software GL, relative only. The stable's GLB is 118,468 bytes as built and 33,268 bytes as
its web derivative. The first QA pass painted the tin a dull red-brown, and from the yard it read as the brick around
it; it is now a weathered grey, which reads as metal against the sky (`after-desktop-tin-gable-from-yard.jpg`).
