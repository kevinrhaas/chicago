# Sheet 28's 1904 building footprints, digitised (T-2327)

T-2159's draft builder has to stand each Prairie Avenue house "on the reconciled Sanborn
polygon, never the viewer's parcel rectangle". The T-1841 census of sheet 28 names every
building on the sheet and rules on its 1904 state, but says of itself *"Footprints are not
digitized and no dimension is claimed"*. Until this ticket, the only coordinates on these
blocks were the parcel lines (T-0474). This ticket supplies the missing input and builds
nothing on it.

## Acceptance

1. Every building on sheet 28's Prairie Avenue lots, 18th to 20th Street, on both faces, has
   an outline in local metres: houses, attached ranges and porches, and detached alley
   buildings. Each outline is read off the committed raster through the T-1250 fit, with
   its pixel readings kept beside it.
2. Every census polygon (`s28-NNNN-front`, `-wing`, `-rear`, and the vacant strip's shed)
   is assigned exactly one outline, and no building is left unnamed.
3. Each building is split into parts at its solid drawn walls, with each part's fabric
   (brick, stone or frame) and a declared role, so the builder can tell a main body from a
   rear range or a porch.
4. The outlines are deterministic and gated in `check.sh`: re-derived byte for byte, every
   outline inside its lot and counter-clockwise, every census id assigned exactly once.
   A self-test proves each of those refusals still fires.
5. The outlines are checked against houses this project has already modelled from other
   evidence, and the overlays are committed here.

## How it reads

`tools/trace_prairie_1904_footprints.py` classes every pixel as brick (pink), stone (blue),
frame (yellow) or not fabric, using fixed colour rules measured on the sheet's 25 most
common colours. It clips the fabric to each T-0474 lot (taken back to pixels through the
inverse of the fit). It then reads two things:

- **buildings**: fabric joined across its own walls and lettering (closed by 7 px, holes
  filled)
- **parts**: fabric split at solid walls (eroded a pixel so a JPEG-blurred wall still
  separates, then grown back). A dashed line does not split a part.

Each outline is pushed out 2 px from the fill to the centre of the drawn wall, traced along
pixel edges and simplified (Douglas-Peucker, 2.5 px = 0.13 m).

Census ids are assigned by one rule:

- The building nearest the street takes the frontage's `front` and `attached` ids.
- The others take its `detached_service` ids, nearest the alley first.
- A building on vacant ground takes that ground's id.

Two readings needed a rule of their own, and each is written in the tool and the data:

- **1815's alley garage is drawn against the house's rear wall**, so it closes into the
  house's group. Where the census names more detached buildings than stand apart, the
  street group's parts that begin in the rear 30% of the lot are split off as one building.
  The file notes this on the building.
- **1945's stable is a crossed square** (the census's own convention), and its diagonals cut
  the fill into four triangles. Low-fill parts that together make a near-rectangle covering
  most of a building are one part, marked `crossed: true`.

## What it found

23 lots, 38 buildings, 88 parts (`data/traces/prairie_1904_footprints_s28.json`, 288 KB).
Every census polygon on the sheet's Prairie lots has its outline. 1936 has none, correctly:
the census rules it an alias of 1918 with no footprint of its own.

| lot | kind | census ids | m² | metres from the street line | parts |
|---|---|---|---|---|---|
| 1800 | front | s28-1800-front, s28-1800-wing | 637 | 4.3–53.9 | 1 stone_front, 1 main, 6 range |
| 1808 | front | s28-1808-front, s28-1808-wing | 474 | 3.4–53.9 | 3 range, 1 main, 1 porch |
| 1812 | front | s28-1812-front | 202 | 6.0–33.1 | 1 main |
| 1812 | detached_service | s28-1812-rear | 120 | 39.3–53.9 | 1 main |
| 1816 | front | s28-1816-front, s28-1816-wing | 297 | 5.3–31.5 | 1 porch, 1 main |
| 1816 | detached_service | s28-1816-rear | 236 | 43.2–53.9 | 1 main |
| 1824 | front | s28-1824-front, s28-1824-wing | 275 | 7.7–34.3 | 1 stone_front, 1 range, 1 main |
| 1824 | detached_service | s28-1824-rear | 184 | 43.3–53.9 | 1 main |
| 1828 | front | s28-1828-front, s28-1828-wing | 235 | 6.4–36.2 | 4 range, 1 main |
| 1828 | detached_service | s28-1828-rear | 127 | 43.3–53.9 | 1 main |
| 1834 | front | s28-1834-front | 255 | 5.3–32.3 | 1 range, 1 main, 3 porch |
| 1834 | detached_service | s28-1834-rear | 143 | 43.3–53.9 | 1 main |
| 1834_1900 | vacant_ground_structure | s28-vacant-west-1834-1900 | 36 | 44.4–53.8 | 1 main |
| 1900 | front | s28-1900-front, s28-1900-wing | 283 | 6.1–31.0 | 2 range, 1 main, 1 porch |
| 1900 | detached_service | s28-1900-rear | 135 | 44.8–53.8 | 1 main |
| 1906 | front | s28-1906-front, s28-1908-wing | 523 | 6.0–36.0 | 4 range, 1 main, 1 stone_front |
| 1906 | detached_service | s28-1906-rear | 273 | 43.9–53.9 | 1 main |
| 1912 | front | s28-1912-front, s28-1912-wing | 380 | 6.3–36.9 | 1 main, 2 range |
| 1912 | detached_service | s28-1912-rear | 174 | 43.4–53.8 | 1 main |
| 1918 | front | s28-1918-front, s28-1936-wing | 398 | 6.4–35.5 | 1 main, 1 porch |
| 1918 | detached_service | s28-1936-rear | 351 | 41.8–54.0 | 1 main |
| 1801 | front | s28-1801-front, s28-1801-wing | 470 | 6.4–46.3 | 1 main |
| 1811 | front | s28-1811-front, s28-1811-wing | 259 | 6.6–35.3 | 1 range, 1 main |
| 1811 | detached_service | s28-1811-rear | 102 | 36.9–46.0 | 1 main |
| 1815 | front | s28-1815-front | 299 | 8.2–36.3 | 1 main, 1 range |
| 1815 | detached_service | s28-1815-rear | 79 | 33.5–43.2 | 2 stone_front, 3 range, 1 main |
| 1823 | front | s28-1823-front, s28-1823-wing | 253 | 9.1–29.0 | 1 main |
| 1827 | front | s28-1827-front | 480 | 6.6–37.7 | 2 range, 1 main |
| 1827 | detached_service | s28-1827-rear | 164 | 43.8–54.4 | 1 main |
| 1901 | front | s28-1901-front | 414 | 6.2–34.8 | 3 range, 1 main |
| 1901 | detached_service | s28-1901-rear | 243 | 43.8–54.7 | 1 main, 1 range |
| 1905 | front | s28-1905-front | 427 | 9.4–33.1 | 1 main, 1 range |
| 1905 | detached_service | s28-1905-rear | 350 | 44.7–54.6 | 1 main |
| 1919 | front | s28-1919-front, s28-1919-wing | 616 | 7.2–54.6 | 1 main, 1 range |
| 1923 | front | s28-1923-front | 340 | 8.5–33.9 | 1 main |
| 1923 | detached_service | s28-1923-rear | 134 | 45.6–54.7 | 1 main, 1 range |
| 1945 | front | s28-1945-front, s28-1945-wing | 290 | 7.9–29.1 | 1 main, 1 range |
| 1945 | detached_service | s28-1945-rear | 141 | 45.6–54.7 | 1 main |

`overlay-west.jpg` and `overlay-east.jpg` show the plate with each building in red and its
parts in colour: main blue, range green, porch orange, stone front purple.

## Checked against houses already modelled

Neither model was read by the tracer.

| house | its model's footprint | agreement with the trace |
|---|---|---|
| 1800 Glessner | ATTESTED (HABS), placed by T-1731 | IoU 0.874; areas 657 and 639 m² (2.7% apart); every bounding edge within 1.2 m |
| 1808 Keith/Field | RECONSTRUCTED 18 × 10.4 m main block | 97% of it lies inside the traced building; front walls 0.8 m apart. The trace adds the rear range to the alley, which the census rules part of the house in 1904 |

Both disagreements are inside the georeference's own independent check (standing houses
1.47 m RMS, worst 1.9 m).

## Tiers and limits

- Every outline is INFERRED for 1904: a 1911 survey carried back on T-1841's per-polygon
  ruling (present as mapped; 1911 garage labels backcast as stables).
- Part roles are INFERRED from colour, size and position by the rule written on each part
  (`role_rule`).
- Storeys are not read here. The census's printed notation (`3B; rear2B`) is the storey
  reading.
- Parts split only where a solid wall fully separates the fill. 1801 (a stone house and its
  attached garage), 1823 and 1919 read as fewer parts than the sheet draws. Their census
  wing ids stay on the building, and the builder places the rear range from the notation.
- Fabric the sheet leaves uncoloured (an outline-only open porch or areaway) is not traced.
- 1906 and its attached 1908 front are one building, as the census rules.
- The tool is written for more than one sheet (`SHEETS`). Sheets 20 and 35, for T-2160 and
  T-2161, need their own census rows and their own look at the overlays.

## Costs

`--check` re-derives sheet 28 in about 5 s; `--self-test` (16 cases) takes under 1 s.
Nothing in the scene reads the file yet, so it adds nothing to load, heap or frame time.
