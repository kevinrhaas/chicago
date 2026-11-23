# T-1931 — 2127-2129 Prairie on K01: the double building of flats, and 2141 left open

The S19 package of the T-1837 programme. The district draft (T-2352) is refined in place, under its own id
(`flats_2127_prairie`), onto the K01 frontage assembly (`generators/k01_emit.py`), on the pattern of 2120 Prairie
(T-3720), the last map-only brick house refined on sheet 35; liberty `L-k01-2127-prairie-1931`. 2129 is the
building's south half, not a building of its own (the T-1842 census alias), so the record carries both numbers.
2141, the 22nd Street corner, is a non-building frontage and stays open ground (below).

## What was looked for

- The Prairie library (`chicago/prairie_1904_v1/data/images.json`, `library.json`, the address crosswalk): no record
  names 2127, 2129 or 2141. The crosswalk reads all three `map_only_no_named_record`.
- The one picture that covers the frontage, `a20-glessner-2100-block-east-side-1890s` (the Glessner House blog's
  1890s view south down the east side of the block, captioned "2101-2141"), was opened and read. Its subject is the
  tall concave-mansard house and the porched Italianate house in the foreground; at its far right edge, behind the
  trees, stands a flat-topped block with round-headed ground-floor openings that no reading identifies. A building in
  the corner of a street view does not attest it (AGENTS.md rule 12), so no camera is solved and the building has no
  image gate. Its round heads are not the reason the design has them.
- The Blue Book (`data/residents_1904/former_residents.json`): no edition of 1904 or 1905 lists anyone at 2127.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by colour class along rows and columns and carried into the lot frame through the committed
trace's fit (`data/traces/prairie_1904_footprints_s35.json`, 0.1858 m a pixel; the frame turned as
`tools/draft_prairie_1904.py` turns it), with the sheet's key (`sanborn_1911_vol3_key.jpg`).

| reading | raster (column / row) | plan frame (u from the rear wall toward the street, v from the north wall, + south) |
|---|---|---|
| front wall (an ink line only: no stone band) | column 916 | u 24.0 |
| rear wall | column 1049 | u 0 |
| north wall | row 1458 | v 0 (the draft's fit: 0.6 m south of it) |
| south wall, on the lot line | row 1533 | v 13.85 |
| party wall, its thickness figure on it | row 1494.5 | v 6.74 |
| '3B' and 'F' (the key's flat), in each half | — | three storeys on a basement, two buildings of flats |
| two small stoops before the front | rows 1486-1492 and 1499-1504 | one either side of the party wall, about 3.3 m across both |
| light-court recesses, north flank | columns 973-994 and 1018-1027 | 0.6-0.9 m deep: not cut |
| light-court recesses, south flank | columns 967-988 and 1015-1023 | 0.6-0.9 m deep: not cut |
| solid dot in each half and on the porch | — | the key's composition or gravel roof: flat |
| rear porch, yellow, dashed outline, '3' | columns 1046-1071, rows 1478-1513 | u -4.55 to 0, v 3.54-10.06: three decks |

## The design (all reconstructed; no picture of 2127-2129 is known)

A 1.5 m principal floor on the basement and three flats' storeys of 3.8, 3.5 and 3.3 m; a red pressed front over buff
common flanks; five bays on the front, two for each flat's front rooms and the middle one on the party wall's line
carrying the entrance and the stair halls' lights over it; the principal storey's lights and the paired door
round-headed under one arch band with stone keys, flat stone lintels above; a bracketed cornice under the flat roof;
two stacks on the party wall; one broad stone flight to the door. The sheet's two stoops are built as one flight and
the two doors as K07's pair of leaves under one round head, one leaf a flat: K01 builds one entrance. At the rear, the
sheet's open three-storey frame porch is K01's rear veranda three decks high (the module took a third deck for it,
`generators/archetypes/k01_rear_veranda.py`; a two-deck veranda takes the path it took before, and every other K01
asset was re-emitted byte-identical), on paired posts, railed, with a flight to the yard.

## Not built

- The light-court recesses in both flanks (K01 lays the main body as one rectangle; the flank lights gather where the
  courts are).
- A composition or gravel roof: the K04 kit has none, so the flat roof is flat-seam tin, seen only from the air.
- A roof over the porch's top deck, and the flights between its decks.

## 2141 Prairie

The 22nd Street corner is not a building. The sheet draws nothing on the frontage (the register: "no notation; none;
1911 use vacant frontage. Corner frontage has no dwelling footprint"), the T-1842 census rules it open ground
(r35-2141-open-corner), and no source names a house there. A 1911 empty lot is not proof of 1904 vacancy, so open
ground is the working state, as the district draft left it, and nothing is invented on it. Its yard and boundary are
T-1945's; any detached rear building, T-1938's.

## Checks

`node tools/photo_match.mjs` with throwaway review cameras (no picture to match, so nothing was committed under
`data/reference_views/`): the front from the north-east (`after-ne.jpg`) and south-east (`after-se.jpg`), the rear from
the north-west (`after-rear.jpg`) and the air over the rear (`after-air.jpg`); the draft from the same poses
(`before-ne.jpg`, `before-rear.jpg`). The draft stood its front 2.75 m behind the sheet's front line, under six equal
bays and one door, with a closed two-storey frame range at the rear where the sheet draws an open three-storey porch.
The first build refused a round-arched stone door head in a brick front; the door is cut round in the brick under the
arch band instead, as 1945 Prairie's is.

Costs: the full GLB is 4047040 bytes and the web (light) GLB 1696992 bytes, against the draft's 45364-byte web GLB; the scene's load and frame costs are the smoke's (`node tools/smoke_budget.mjs --for-diff`), run on this change.
