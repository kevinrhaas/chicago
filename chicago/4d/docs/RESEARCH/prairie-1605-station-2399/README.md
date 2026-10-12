# T-2399 — the Illinois Central's 16th Street station at 1605 Prairie, dressed as a station

Piece 2 of 2 of T-1866. The district draft (T-2335) stood the station as a plain two-storey gabled
frame building. This piece keeps that body and its id (`ic_16th_street_station_1605_prairie`)
and dresses it as a station from the draft rules' own frontage row (frontage-20-023 in
`data/components/prairie_1904/draft_prairie_1904.json`), built by the draft's builder
(`generators/archetypes/prairie_draft.py`, `station`). Liberty: `L-ic-16th-street-station-2399`.

## What was looked at first (the image gate, AGENTS.md rule 11)

- **The Prairie library, every record.** Three name the station: the Robinson 1886 crop
  (`cgn-16th-station-robinson-1886`) and the Glessner House atlas detail
  (`a16-ghm-blog-1720-atlas-crop`), both site plans, and the Chicago Tribune's "Sixteenth Street
  Station" sketch of 8 August 1886 (`cgn-16th-station-tribune-1886-sketch`).
- **The Tribune sketch is not this building.** Read from the image itself: a ONE-storey frame
  depot under one long gable, a deep bracketed eave and a wide platform beside the tracks. The
  1911 sheet prints this building as two storeys. The library's own note says the article
  describes the C. B. & Q. depot formerly at Sixteenth Street, moved three or four years before
  to Meagher Street and Stewart Avenue ("a one-story frame shanty about 70x20"). So it is not built
  toward and gives this building no image gate. If a picture of the I.C. station turns up, it
  becomes the image gate (`data/reference_views/ic_16th_street_station_1605_prairie/`).
- **Sheet 20 of the 1911 Sanborn** (the committed 5879 x 7323 copy) and **Robinson 1886 plate
  10**. Neither draws a platform, a canopy, a door or a sign.

## What is read off the sheet: the platform's edge

The sheet draws the right-of-way line touching the station's north-east corner, and beyond it
each track as a pair of rails 26-27 px (1.35 m) apart. Dark-line minima across the sheet's
rows, sheet pixels:

| row | track wall | right-of-way | west rail | east rail |
|---|---|---|---|---|
| 1270 | 4158 | (on the wall) | 4199 | 4226 |
| 1380 | 4159 | 4195 | 4232 | 4259 |
| 1485 | 4160 | 4227 | 4265 | 4292 |

Through the T-1250 fit (similarity, 2.46 m RMS) and into the record's plan frame (u toward the
street, v along the front, toward the south), the nearest track's west rail lies at u -2.05 m at
the north end (v 0) and u -5.49 m at the south (v 11). The platform stops 1.0 m short of it, so
its edge runs from u -1.05 to u -4.49. The platform tapers from 1.05 m to 4.86 m over the lot's
width, 36.0 m² in all. The canopy (2.0 m deep, v 3.2 to 11.0) stands only where the platform is
deeper than the canopy, so it never reaches over the track.

## What is built (all reconstructed but that edge)

- A timber platform, 0.3 m deck, plank seams running with the track, a dark edge timber and a
  step at each end.
- A lean-to canopy on the track wall: 7.8 m long and 2.0 m deep, falling 0.35 m to a fascia, on a
  braced bracket every 1.6 m or so.
- On the street front, a pair of passenger doors under a transom at the north end (the 16th
  Street end), under a bracketed hood 2.4 m wide.
- On the track side, the draft's carriage door narrowed to a 2.4 m baggage door, with no loft door
  over it.
- Three nameboards, dark with light raised block capitals: `ILLINOIS CENTRAL R.R. / 16TH ST.
  STATION` (6.4 m) on the street front between the storeys, `16TH STREET` (3.8 m) on the track
  wall over the canopy, and `16TH ST.` (2.2 m) on two posts at the platform's wide south end,
  lettered on both faces and parallel to the track. The wording is the sheet's own lettering of
  the building. The capitals are a 4 x 6 stroke alphabet in the builder (`GLYPHS`), so a board's
  wording is data.

Not built: the tracks (the 1904 scene draws no rails), further platforms or a crossing to them,
lamps, benches, signals, right-of-way fences, people.

## The draft stays the draft everywhere else

`python3 generators/draft_emit.py --check`: every other district-draft GLB is byte-identical
(the station's feature is read only from a record that names `station`). The manifest's
`inputs_sha256` moves for every `prairie_draft` asset because the archetype module is part of
each one's input hash. Their bytes do not move.

## Browser readings (the actual published /1904/ app, `node tools/qa_station_t2399.mjs`)

Camera stands, in scene-local metres: front (from across Prairie Avenue), oblique from the
north (the 16th Street corner) and from the south, rear (the track side), the platform end-on
from its south end, and the roof. Before is the committed draft; after is this branch.
Desktop is 1280x800 at full detail, mobile is 390x780 at light. Frame times are this runner's
software GL, so they are relative readings, not device claims.

| | load to ready | JS heap | page errors | front: draw calls | front: triangles in view |
|---|---|---|---|---|---|
| desktop before | 16.8 s | 31.7 MB | 0 | 110 | 1,740,516 |
| desktop after | 15.4 s | 31.7 MB | 0 | 110 | 1,745,912 |
| mobile before | 10.9 s | 31.7 MB | 0 | 78 | 354,200 |
| mobile after | 10.9 s | 31.7 MB | 0 | 78 | 359,596 |

The station's mesh goes from 101 KB to 312 KB as a master and from 21 KB to 46 KB as its web
derivative (3,906 triangles), with no new material and so no new draw call.
`before-*.jpg` and `after-*.jpg` are the shots from each stand; `browser-validation-*.json` holds the
raw readings.
