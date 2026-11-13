# T-3566 — 1721 Prairie: Wirt Dexter's frame house of 1863 behind Little's brick front

The owner, 2026-11-12 (project thread, after a meeting with Bill Tyre): *"on 1721 prairie there is a
frame house to the rear of the building that should be standing you should be able to see images of
it"*. On a first pass that clapboarded the 1911 sheet's rear range, he sent his crop of the Detroit
print's left edge: *"you are missing the whole front entrance of that whole it has two hipped gable
front on the left and right and a center area that has a front porch and door that house was there
first and the other house facing prairie is technically the addition so dig in on that photo ... and
photo match that rear house to perfect"*; *"Chimneys, windows, everything"*; *"They look like bay
windows in the front left and right and shutters in the 2nd floor center"*; *"the house seems likely
to be symmetrical"*; *"Those might be bay windows in the second floor on the left and right also"*.
Liberty `L-k16-1721-frame-house-3566`.

## The house in its sources

| source | date | what it says of the frame house |
|---|---|---|
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`; library `cgn-1721-robinson-1886`) | 1886 | lot B (60.2 ft): a long **yellow (frame)** house on the north lot line, set back about 34 ft and running back about 100 ft, **stepped on its south side** |
| Inter Ocean, 1887 (quoted in the library) | 1887 | "tastefully constructed frame house" |
| George Glessner's photograph (`a16-ghm-blog-1721-dexter-c1888`) | c. 1888 | the house's street end before Little: two storeys, central gable, bracketed eaves, tall chimneys, shutters |
| Inland Architect plate (`inland_architect_1891_06_dexter_plate`) | 1891 | Little's brick front on the street line; behind its north flank a **clapboarded** block |
| Detroit Publishing print (`loc_det_4a08065_pullman_residence`; the owner's crop) | 1893-1901 | at its left edge, across the side yard between 1721 and the Pullman house, the frame house's **south front**: two gabled wings, a recessed middle with an arched porch on four posts and the door, a window with blinds over the porch, bracketed eaves, four tall stacks (one behind an elm) |
| Chicago Tribune, 28 Nov. 1901 (library `npo-1721-tribune-1901-11-28-dexter-residence-bought-by-spalding`) | 1901 | the sale to Spalding required the street-line brick front rebuilt or **moved back** to the 20 ft building line |
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | the bowed 3B brick block 9.7 m back from the street; behind it on the north line a "2B" range 19.9 x 6.2 m coloured **brick**, one-storey frame pieces at its east end |

## The reading

The frame house came first (1863); Little's brick front of 1889 was built on its street end. The print
looks north-east from 18th Street across the yard south of the house, so what it shows is the house's
south front, its entrance front, not its street end. Carried through the camera solved for the Pullman
house (the Pullman house, the brick front and the street furniture land on the print within a few
pixels), the front's features fix the plan and heights:

- the two gable peaks, the porch's middle and the window over the porch stand on one axis, the gables
  13.5 m apart about it: the owner's symmetry, measured;
- the wings' gables peak at about 10.9 m, the eaves at about 8.5 m, the porch floor about 1.4 m up, the
  ground windows' sills about 2.1 m and the upper ones 5.35 m;
- three stacks are seen: a pair close either side of the middle, topping out at about 13.5 m, and one
  over the east wing at 13.3 m; the fourth, over the west wing, stands where an elm hides it;
- the front's axis falls 11.65 m east of the 1904 brick block's rear wall and its wings' faces about
  9 m south of the north lot line; the east eave about 23 m east.

The house is placed in 1904 where the print puts it. That is 4 m east of the 1911 sheet's range, whose
west 4 m the moved brick front stands on; the part of the house west of the wings (the print's pale
clapboarded end beside Little's front) is the part the 1902 move displaced and is not built. The 1911
sheet's brick colour and its 6.2 m depth without wings are not followed: the print, the 1886 plate
(stepped south side) and the owner's ruling outweigh the one map.

## The build

`data/structures/dexter_house_1721_prairie_frame_house.json`, archetype `k16_timber` (a whole frame
house, T-2357), in a frame turned 90 degrees from the brick house's so its u runs south to its own front:

- `main`: the range 6.2 x 23.9 m under a 34 degree hip, walls to 8.35 m, the door on the axis and over
  it a window with louvred blinds;
- `pav_west`, `pav_east`: the wings, 7.0 m wide, standing 2.2 m out, each under a 29 degree gable with
  its ridge running back into the main roof, and on each face a two-storey canted bay (plan 4.2 m at the
  wall, 2.6 m across its front, 0.8 m deep) with paired sash in its front and one in each cant, both
  storeys;
- the kit's porch across the middle on four posts with its arcade, six risers;
- four stacks, two either side of the middle and one over each wing.
- painted from the print's tones (2026-11-13, the owner: "I am not convinced the color of the building is white"):
  the clapboard reads about the value of Little's buff brick and the trim and blinds well darker, so a fawn drab
  body, seal-brown trim and deep bronze-green sash and blinds; the hues are a liberty, as every picture is monochrome.

The K16 kit learned two things for it (`generators/archetypes/k16_timber.py`): a window's `shutters`
(a pair of louvred blinds folded open beside the casing, in the sash's dark green) and a house's
`chimneys` list, each stack over its own block's ridge. No other K16 record names either, and every
other K16 asset rebuilds to the same bytes. The brick house's K01 record loses the rear range it carried
(`rear_wings`), which this record replaces.

## The pictures

- `data/reference_views/dexter_house_1721_prairie_frame_house/detroit_det_4a08065.json`: the Pullman
  house's solved camera carried into this record's frame (with the Pullman house and the coach house as
  context; the 1904 brick front is left out, because the print shows the house before it was moved
  back). **matches**.
- `dexter_house_1721_prairie`'s `detroit_det_4a08065` and `inland_architect_plate` re-rendered with
  the frame house behind; the coach house's view of the print re-rendered.
