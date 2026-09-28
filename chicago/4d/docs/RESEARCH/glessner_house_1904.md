# The Glessner House as it stood in 1904: an exterior specification

**Ticket:** T-1731, piece 1 of T-1729 (*Build the Glessner House at 1800 Prairie as it stood in
1904*). **Written:** 2026-09-28. **Machine copy:**
`data/research/glessner_house_1904_spec.json`. **Built by:** T-1732 (place and bake it on the
T-0474 parcel and T-1252 ground as the default version). T-1730's alternate versions read the
same sources.

**This is a specification, not a scene change.** No structure record, mesh or `docs/LIBERTIES.md`
entry exists for the house yet. The values marked `reconstructed` below become scene claims, and
need their liberty entries, only when T-1732 builds them.

## 1. Sources, and what each one is allowed to do

| source id | what it is | date it describes | used for |
|---|---|---|---|
| `habs_glessner_house_il_1015_drawings` | HABS IL-1015 measured drawings, sheets 1–6 | 1963–1965 | every dimension |
| `habs_glessner_house_il_1015_data_pages` | HABS written data, 27 pp. | 1963 | construction, the 1946 alteration list, the 1945 carriage door, legal description |
| `glessner_story_of_a_house_1923` | J. J. Glessner's own account, in the HABS transcription | 1886–1923 | materials as built, courtyard, vines, service arch |
| `inland_architect_1888_02_glessner_exterior` | the published exterior photograph, Feb 1888 | winter 1887–88 | brackets the 1965 elevation; 18th Street eave line; stable gable and turret |
| `glessner_porte_cochere_doors_c1888` | George Glessner's photograph of the carriage doors | c. 1888 | the doors' design |
| `sanborn_1911_vol3_sheet_28` | Sanborn 1911, vol. 3, sheet 28 | 1911 | the house's position on its lot; storeys and materials in 1911 |

All six records are new with this ticket. The drawings, the data PDF and the Sanborn sheet were
read from files already committed (`chicago/prairie_1904_v1/research/public/`,
`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/`). The two photographs were
fetched from Glessner House's website into a scratch directory, matched byte for byte against the
checksums the Prairie library had recorded (`research/glessner-dossier.json`, assets), viewed,
and **not committed**: their reproduction rights are `check_required`, so they are cited in text
only. The 4D project's older record `habs_glessner_house_il_1015` (dates only, drawings "NOT
read") is left as it is; the library's README asks that its trail be extended, not rewritten.

**How the drawings were measured.** Printed dimension strings are quoted as printed. Everything
else was measured on the 400-dpi scans against each sheet's own scale bar: sheets 2–3 at 37.2 px
per foot (checked against the printed 161′-3″ and 74′-0″), sheets 4–5 at 99–101 px per foot
(checked against the printed 26′-10″ north-range depth), and sheet 6 at 75.8 px per foot across
(checked against 74′-0″) and 73.9 px per foot up, a figure fixed by the sheet's own annotation
"48.62 ± 0.02 at top of north chimney" and confirmed by its "24.30 at soffit of 2nd flr windows"
to 0.4 ft. Tolerances are given with each value.

## 2. Phase discipline

The dossier's order is kept: the **1885 Richardson sketch** is design intent and nothing here
rests on it; the **February 1888 Inland Architect photograph** and the **c. 1888 porte-cochère
photograph** date the finished exterior; the **1892** changes are interior; the house is modelled
**as it stood on 1 July 1904**.

The HABS survey is 1963–1965, so each value it gives had to clear two tests before it could
stand for 1904:

1. **The 1946 alteration list does not touch it.** HABS data p. 2 lists what the research-centre
   conversion of September 1946 changed: stable loft and basement partitioned; stable door
   replaced; loft door closed up; stable, kitchen and laundry fixtures and the coal furnace
   removed; school-room woodwork painted; the door of the underpass on the east facade replaced;
   the courtyard entirely paved as a parking lot. It says the original plan and finishes were
   left untouched and names **no change to the masonry or the roofs**.
2. **Where the 1888 photograph shows it, the photograph agrees.** It does, opening for opening, on
   the Prairie Avenue front: one second-floor window, then groups of three, four and three under
   the eave; a small pair, two large windows, the fan-arched door and two large windows below;
   three-by-three basement lights under the large windows; the porte-cochère opening at the south
   end; three chimneys; a crested tile roof with no dormers on the Prairie slope; a stone parapet
   gable on 18th Street with its chimney at the apex. A front that is the same in 1888 and 1965 was
   the same in 1904 unless something says it changed and changed back, and nothing does.

**Excluded as later than 1904:** the courtyard paving (1946), the replacement stable and underpass
doors (1946; the museum says 1950s), the closed-up loft door (1946), the wooden stairs behind the
service wing (sheet 2: "added c. 1955"), the tar on the roof tiles (first recorded 1963, undated),
and the 1911 Sanborn label **GARAGE** on the west wing.

## 3. Frames and datums

- **Building frame (feet).** Origin at the NE corner of the granite, Prairie Avenue and 18th
  Street. `W` = feet west of the Prairie face, `S` = feet south of the 18th Street face. It is
  the HABS plans' own frame; their north arrow points down the sheet.
- **Lot frame (metres).** Origin at the lot's street corner, where the west line of Prairie Avenue
  meets the south line of E. 18th Street. The ticket calls this corner "the SW corner at
  Prairie & 18th": it is the SW corner of the intersection and the NE corner of the lot. x runs
  east, y north, so the whole house has x < 0 and y ≤ 0. The spec lists all four lot corners in
  this frame, the true SW (alley) corner included, so T-1732 can anchor on whichever corner
  T-0474 makes most certain.
- **Placement** (`inferred`, `sanborn_1911_vol3_sheet_28`): the north face stands on the 18th
  Street line (within about 1 ft), the west face on the alley line, and the east face **14.7 ft
  (± 1.5 ft) behind the Prairie Avenue street line**, measured at 6.0 px per foot. It is a 1911
  map, carried to 1904 because the building did not move. T-0474 owns the street lines. If it
  finds a different setback, re-derive `lot_m` from `building_ft` rather than editing it.
- **Heights.** East-face heights are above the HABS sheet 6 datum, **0.00 = the Prairie Avenue
  front-door sill**, with the sidewalk before the door at **−0.74 ft**. Section A-A (sheet 4)
  prints no heights; its values are measured above the grade it draws at the 18th Street wall
  ("north grade"). Where the two overlap (east-wing eave and ridge) they agree within about a
  foot. It is not Chicago City Datum.

## 4. The lot

- Legal description (`attested`, HABS data p. 1): Block 9, lots 39, 40 and the north 17 ft of
  lot 38, Assessor's Division of the SW fractional ¼ of Section 22, T39N, R14E. Bought 24 March
  1885 for $50,000.
- Depth (`inferred`): 175.95 ft, which is the 161′-3″ house plus the Sanborn setback.
- Frontage on Prairie Avenue: **unresolved, 74 or 77 ft.** Sanborn draws the 1800/1808 line about
  77 ft south of 18th Street. The house is 74′-0″. HABS sheets 2–3 draw a 1′-6″ brick wall just
  south of the east wing, which the Prairie library identifies as the retained north wall of 1808
  (`buildings.csv`, pa-1808-6). The widths of lots 38–40 are not stated in anything read. This is
  for T-0474.

## 5. The footprint

The outline in the spec is the ground-floor masonry, courtyard excluded: 34 points, about 7,054
sq ft, `attested` (HABS sheets 2–3, checked against Sanborn and the 1888 photograph). The house
is an E, or a squared C, open to the south. The courtyard is closed on the south by the
neighbour's wall.

| run | printed dimension | sheet |
|---|---|---|
| 18th Street face, overall | 161′-3″ (96′-6″ + 12′-0″ arch + 52′-9″) | 2 |
| Prairie Avenue face | 74′-0″ | 2 |
| east wing, E-W | 26′-6″ | 2, 3 |
| courtyard, E-W | 99′-3″ (11′-3″ + 21′-6″ + 21′-6″ + 45′-0″ from the east wing) | 3, 2 |
| west (stable) wing | 35′-6″ E-W × 59′-9″ N-S, so 14′-3″ short of the south line | 2, 3 |
| north range depth | 26′-10″ (1′-7″ granite + 4′-1″ corridor + 1′-8″ + 18′-0″ + 1′-6″) | 2 |
| courtyard, N-S | 47′-2″ (12′-8″ + 10′-0″ + 12′-0″ + 12′-6″) | 2 |

Three projections on the courtyard faces are measured rather than printed (± 0.5 ft):

- **Round stair tower** on the east wing's courtyard face: centre W 27.3, S 55.0, outer radius
  5.25 ft, so it projects 6 ft into the courtyard.
- **Hall bow** in the inner NE corner: printed "9′-6″ R" inside, centre W 28.0, S 27.7, outer
  radius 10.1 ft. It sweeps from the east wing (at S 37.6) to the north range (at W 38.1).
- **Dining-room bay** on the north range: five facets, 19.4 ft wide, projecting 10.3 ft. The
  interior is printed as 17′-8″ × 11′-0″.

The north range's courtyard face is taken as a straight line at S 26.83. Sheet 2's 14′-3″ +
34′-0″ chain puts it about 1.1 ft further north beside the stable. That is inside the outline's
tolerance and is noted, not modelled.

## 6. The masses

**East wing (Prairie Avenue range).** 74 × 26.5 ft. Two storeys over a raised basement, with an
attic in a steep N-S gable (Sanborn "2B"; HABS sheets 4, 6). Stone parapet gables at both ends.

- Eave **27.1 ft** above the door datum (sheet 6). Ridge **45.7 ft**, cresting to 46.3.
- Pitch about **54.5°**, `inferred`: this assumes the ridge is centred on the wing, and no roof
  plan confirms it. HABS says "steeply pitched, gabled roofs".
- The Prairie slope has no dormers. The courtyard slope carries three small pyramid-roofed dormers
  (sheet 4: centres S 32.3, 45.0, 66.8; 4.4 ft wide; eave 32.9, apex 37.0 above north grade) and
  the stair tower (wall top 32.5, cone apex 42.3).
- Sheet 4 also draws a **large pyramid-roofed element** beyond the section plane at the north end
  of that slope: 16.7 ft N-S, eave 32.9, apex 43.9. The 1888 photograph shows no taller block on
  18th Street, so it is read as a large dormer or pavilion on the east wing's west slope
  (`inferred`). Its E-W depth is not drawn anywhere (GAP 3).
- The north gable (1888 photograph) has a coping rising to a chimney centred on the apex, and a
  narrow round-arched window with radiating voussoirs.
- The south gable is drawn edge-on in stone on sheet 4. Sanborn prints "WALL B." inside it, which
  is recorded as read and not interpreted. In 1904 the three-storey house at 1808 masks most of
  it.

**North range (18th Street).** W 26.5–125.75, 26′-10″ deep, two storeys over the basement
(Sanborn "2B").

- Floor levels above north grade (sheet 4): basement −2.0, first 6.0, second 17.4, attic 27.6 ft.
- Gable roof, ridge E-W, **34.1 ft** above north grade and 14.6 ft south of the 18th Street face.
- Eave **23.1 ft** on 18th Street and 26.5 ft on the courtyard side. Pitch **36.6°** both ways.
  The courtyard slope flattens to about 27° over its lowest 5.7 ft.
- The profile comes from the one section cut, at W 51.3, and is assumed to hold along the range.
- Its west end (about W 96.5–125.75) is the service block: kitchen, pantries and back stairs,
  entered **"through the great arch on Eighteenth Street"** (Glessner 1923).

**West wing: the coach house** (HABS's "service (west) wing"). 35.5 × 59.75 ft at the alley,
**1½ storeys** (Sanborn), with the furnace room beneath it (Glessner 1923).

- **1904 use: stable and carriage house** (`inferred`). Sheet 2 dots probable stall partitions
  "based on early drawings". Sheet 3 marks the coachmen's quarters and the hay loft. HABS lists the
  stable and harness-room finishes. Glessner writes in 1923 "the carriage house and stables (now
  garage)". That dates the conversion only to before 1923, and to before 1911 by the Sanborn
  label. Nothing read puts it before 1904, so a 1911 "garage" is not backdated. The exterior is the
  same either way.
- The 1888 photograph shows the 18th Street eave running level into the foot of this wing's north
  stone gable, and a small square louvred turret with a pyramidal roof riding its N-S ridge. So:
  eave 23.1 ft `inferred`; gable and turret `attested` as forms.
- Roof pitch is **reconstructed at 45°**, bounded by the house's own measured roofs (36.6° and
  54.5°). That puts the ridge about 40.9 ft above north grade.
- The turret's dimensions and the south-end roof termination are reconstructed.

## 7. Chimneys

| chimney | where | top | source | tier |
|---|---|---|---|---|
| north gable | apex of the east wing's north gable, S 0.5–3.1 | **48.62** above door (printed) | sheet 6, 1888 photo | attested |
| south | Prairie slope near the ridge, S 57.2–61.2 | 48.5 above door | sheet 6, sheet 4, 1888 photo | attested |
| middle | 2 ft east of the ridge, S 25.8–28.6 | 48.5 above door; base on the slope at 42.4 | sheet 6, 1888 photo | attested |
| great chimney | behind the north gable, S 16.5–20.5, 4 ft wide | 46.6 above north grade | sheet 4, 1888 photo | attested |

The great chimney does not appear on sheet 6 because the east ridge hides it from a street-level
camera. The E-W sizes and positions of all four are reconstructed.

## 8. The street faces

**Prairie Avenue (east)**, all `attested` (sheet 6, confirmed by the 1888 photograph).

- The spec lists every opening, with d (ft north of the south end) and z (ft above the door).
- Second-floor heads are at 24.30 (printed) and sills at 19.8. The three multi-light groups have
  carved-capital colonnettes between the lights, and a carved string course runs under the group
  of four.
- First-floor windows run 9.2–14.5 ft. The small pair at the south end runs 11.8–16.2 ft.
- The front door (d 38.6–43.6, 0–7.75 ft; 4.7 × 7.5 ft leaf on sheet 5) is heavily panelled oak
  with iron straps and a square grilled window. It has a stone lintel and a carved tympanum of
  2.6 ft radius, set in a fan of radiating voussoirs of 6.4 ft radius.
- The porte-cochère opening is d 3.84–11.62, from 1.9 ft below the datum to 7.0 ft above it. Its
  floor is sunk about 1.2 ft below the sidewalk, and its corner stones are rounded. The
  underpass runs through to the courtyard, where its exit is about 9.6 ft wide and 8.1 ft clear
  (sheet 4).
- Double-hung sash, one pane per sash as drawn in 1965 (`inferred` for 1904).

**E. 18th Street (north).** No HABS elevation exists, so openings are read as gaps in the granite
on the first- and second-floor plans (sheets 2–3, ± 0.4 ft). Heights come from the pair of narrow
corridor windows that sheet 5 draws: about 0.8 ft glazed, first floor 9.3–15.2 ft, second floor
20.5–23.8 ft above grade. These are the "narrow windows in its north side along 18th Street, just
enough to light the narrow corridors" that passers-by remarked on (Glessner 1923).

- The **great arch** (sheets 2, 5): 12′-0″ clear at W 96.5–108.5, semicircular, springing 4.6 ft,
  crown 10.8 ft, voussoir ring 19 ft across. It opens onto a recessed porch with steps, and there
  is a 12-ft window above it at 20.0–23.7 ft.
- The stable's **carriage doorway** (sheets 2, 5): W 134.9–147.0, 11.9–12.1 ft wide, 12.6 ft to a
  single flat granite lintel. Its 1904 doors are not known, because they were replaced in 1946.
- Above the doorway, sheet 3 shows a 7.2-ft upper opening, probably the loft door HABS says was
  closed in 1946. It is inferred open in 1904.

**Alley (west).** The stable wall is granite (sheets 2–3). Openings are listed by S. The courtyard
gate is at S 61.3–70.8, between a stub of the stable wall and a granite pier. It is "the
courtyard entrance from the alley" through which the family moved in, unseen, in December 1887.
West-face heights are not drawn and are reconstructed.

## 9. Materials

- **Street walls** (`attested`): rock-faced granite ashlar in alternating high and low courses
  over brick. Sheet 5 gives the course heights. HABS: 6- and 8-inch granite sheets with deeper
  returns at openings.
  - The **stone's name conflicts**: "Wellesley granite" (Glessner 1923; HABS 1963) against
    "Braggville pink granite" (the museum, as the library's dossier records it, G02).
  - So does the **facing thickness**: 6/8 in (HABS) against about 7 in and 8–10 in (museum pages,
    per the dossier). Both disagreements are carried, not resolved.
  - The **tint is reconstructed** (pale pinkish grey). No colour evidence was read, and the 1888
    photograph is monochrome.
- **Courtyard walls** (`attested`, Glessner 1923 and HABS 1963 agree): common brick of slightly
  pinkish colour, grey Joliet limestone lintels and sills.
- **Roof** (`attested`): red baked terracotta tiles, unglazed (Glessner 1923), about 6 in wide
  with 5 in exposed (HABS 1963, when they were tar-covered; the tar is excluded). The ridge is
  crested with raised tiles at about 1.16-ft centres (sheet 6, 1888 photograph).
- **Hall bow roof:** copper sheathing (HABS 1963). `Inferred` for 1904; its form is reconstructed.
- **Porte-cochère doors** (`attested`, c. 1888 photograph; the same door is described in a 1945
  photograph by HABS):
  - two oak leaves, each three panels wide and six high, every square panel sunk in a circular
    moulding;
  - a horizontal iron strap two rows up, with a lock plate and two ring pulls;
  - scroll-ended strap hinges.
- **Ironwork:** Bower-Barffed and never painted (Glessner 1923).
- **Vines** (`inferred`): Boston ivy on the street fronts and Virginia creeper on the courtyard
  walls were both planted in 1887 (Glessner 1923). The 1888 photograph shows bare walls. How far
  they had grown by 1904 is unknown, so any coverage T-1732 draws is reconstructed. Bare walls are
  also defensible.

## 10. The courtyard

- 99′-3″ × 47′-2″ (sheets 2–3).
- In 1904 its south side is **the north wall of 1808 Prairie** (O. R. Keith house, 1886–1968),
  built by arrangement of the same brick "so that all walls of the courtyard are of the same
  texture and color" (Glessner 1923). West of that is 1808's rear building (Sanborn 1911). Both
  belong to T-0475's neighbour, not to this structure.
- Entered from Prairie Avenue through the underpass, and from the alley through the SW gate.
- Surface: the courtyard was **not a paved lot** (it was "entirely paved" only in 1946). A carriage
  way from the underpass to the gate and stable must have crossed it. Its line, its surface and
  any planting are reconstructed.

## 11. What T-1732 will have to reconstruct (and record in LIBERTIES when built)

The stable roof pitch (45°) and its ridge turret's size; the E-W depth of the pyramid-roofed
element; the E-W sizes and positions of the chimneys; the roofs over the hall bow and the dining
bay; the stable's south-end roof; north-face window heights beyond the pair sheet 5 draws;
west-face window heights; the granite tint; any vine coverage; the courtyard ground and carriage
way.

## 12. Gaps

1. **HABS photographs and captions.** 17 photographs; the Prairie library verified three
   captions. The caption list was not read. They would settle the courtyard faces, the stable roof
   and the pyramid element.
2. **HABS field notes FN-128** and the 1965 photogrammetric plates (north elevation level and
   inclined; NE angled view) were not acquired. The north stereopairs would give the 18th Street
   heights that no sheet draws.
3. **The Harvard (Houghton) Richardson drawings:** 102 drawings, 52 on microfilm at the Art
   Institute's Burnham Library (HABS data p. 6). Not seen. They carry the roof plan and the north
   and courtyard elevations.
4. **The 1923 *Story of a House* photographs** (12 exterior views) and plans are known only
   through the text transcription.
5. **Courtyard-face openings** are not transcribed. Sheets 2–4 hold part of them.
6. **Vines in 1904.** No dated photograph between 1888 and 1923 was read.
7. **Courtyard surface and planting in 1904.**
8. **Lot width** (74 or 77 ft) and the 1800/1808 line. This is for T-0474.
9. **Colour** of granite, brick, mortar, tile and woodwork. None was read.
10. **Stone name and facing thickness.** Carried, not resolved.

Gaps 1–4 and 9 are what **only Glessner House or the Houghton Library can close**: the museum
holds the historic photographs, family papers and restoration files (the library's dossier, G15),
and the Houghton holds the drawings. The owner's contact at Glessner House is the route.
