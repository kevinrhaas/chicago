# The 1880s scene stands on 1 July 1888

**Ticket:** T-1249, piece 1 of T-0473 (*Create an 1880s South Side terrain and urban-ground
epoch*). **Written:** 2026-09-17. **Machine copy:**
`data/terrain/1880s_scene_date_constraints.json`, re-derived on every commit by
`tools/check_1880s_scene_date.py`.

T-0473 asks for "a specific representative scene date in the 1880s **after checking landmark
construction dates**". This memo is that check, and the arithmetic that turns it into a day.

## 1. What the date had to satisfy

The date is not decorative. Four later tickets resolve against it:

| ticket | what it resolves against the date |
|---|---|
| T-1250 | which lake edge `shore_1880s_ic_edge` traces |
| T-1251 | which state of grade, fill and drainage the terrain spec describes |
| T-1252 | which heightfield is baked, and the scene file that selects the epoch |
| T-0474 – T-0477 | which Prairie Avenue street grid, mansions, residences and streetscape stand |

T-0475 is the one that binds hardest — "**Build the Prairie Avenue landmark mansion core**". A
representative date that predates the avenue's landmarks would ask that ticket to build the
avenue's best-documented house out of a scene in which it did not exist.

## 2. The landmark dates, and what was actually found

Two Historic American Buildings Survey records were retrieved at their Library of Congress item
endpoints on 2026-09-17 and read in full.

### HABS IL-1015 — John J. Glessner House, 1800 South Prairie Avenue

The record carries **two** dating statements, and they do not agree:

> Significance: **Designed and built between May 1885 and December 1887**, this house is
> considered the last of the fully personal works of the architect H.H. Richardson and one of
> his finest houses.

> Building/structure dates: **1886- 1887 Initial Construction**

They differ at the start of the work — May 1885 against 1886 — and agree at its end: **both
finish in 1887**, and the fuller one names December. The project takes from the record only what
both statements support, which is a floor and not a completion date:

> **The Glessner House was not complete before the end of 1887.**

The disagreement over the start is left in the data rather than averaged away. It bounds nothing
this ticket needs, and a midpoint would be an invention.

The record also gives NRHP reference number 70000233 and a 1958 Chicago Architectural Landmark
designation. Neither bears on the date.

### HABS IL-1077 — W. W. Kimball House, 1801 South Prairie Avenue

This record was opened **specifically because** the date usually given for the Kimball House —
1890–1892 — falls outside the decade T-0473 asks for, which would have made it the reading that
decided this ticket. It would have forced a choice between the avenue's two best-known houses.

**It does not date the house.** There is no `Building/structure dates` note and no year anywhere
in the significance statement, which says only:

> One of the few remaining residences along Chicago's earliest Gold Coast area, it was designed
> by Solon S. Beman for the founder of the Kimball Piano Company.

So the conflict does not exist in this corpus, because one side of it is not sourced here. The
1890–1892 figure is asserted **nowhere in this project**, and the record is committed in its
undated state (`habs_kimball_house_il_1077`) so that the absence is a recorded finding rather
than a gap the next run fills off the open web. A ticket that wants the Kimball House in an 1880s
scene has to date it from a source that states a date.

## 3. The derivation

Three steps, and `tools/check_1880s_scene_date.py` performs all three from the committed
readings on every commit:

1. Take the latest `not_before` over every reading of kind `lower_bound` — **1888-01-01**.
2. Carry it to the first 1 July on or after that day — **1888-07-01**.
3. Require the result inside the window T-0473 set, 1880-01-01 … 1889-12-31. It is.

**The year is evidence. The day and the month are not**, and `docs/LIBERTIES.md` § L241 says so
in those words. Nothing in this corpus mentions 1 July 1888. The day is chosen so the two scenes
this project intends to carry stand on the same ground in the same season at the same hour of
light, fifty-three years apart, and because midsummer is the only season for which any flora,
fauna or lighting behaviour has been built here at all.

## 4. What this replaced, and why it mattered

`tools/check_shoreline_states.py` has carried

```python
"1880s": date(1885, 7, 1),
```

since T-1152 (2026-09-15). Nothing documented it and nothing was meant to: T-1152 needed some day
inside the decade in order to prove that the 1880s address resolved through its own epoch to its
own shoreline state, and it wrote one in. It was scaffolding for a different assertion.

It was also **three and a half years too early**. On 1 July 1885 the Glessner House was a hole in
the ground at best — the earlier of the record's two statements has the work beginning in May of
that year. A scene on that date could not show the avenue this epoch exists to show.

A plausible-looking number sitting in a gate is read as settled by the next run that finds it,
which is why the fix is not to correct the literal but to remove it: the gate now reads the date
out of the committed readings, and the superseded date is recorded under `adopted.supersedes` so
it cannot quietly return.

## 5. What this memo does NOT settle

- **The lake edge.** `shore_1880s_ic_edge` is still `geometry: null`, still `planned`, and the
  gate fails if it acquires a line here. T-1250 owns the sourced trace. *(Settled by T-1250 —
  see § 7.)*
- **The Illinois Central.** The epoch's old placeholder note asserted that "the Illinois Central
  trestle line already fixed the shore in 1852". No source in this corpus says that. The claim
  is neither repeated nor denied in the epoch record now; it is T-1250's to establish or refuse. *(Ruled by
  T-1250 — see § 7.3.)*
- **The ground.** No grade, fill, drainage or railroad earthwork is described anywhere yet
  (T-1251), and no heightfield is generated or baked (T-1252).
- **The scene file.** There is still no `data/scenes/1880s.json`. A scene must stand on a
  heightfield, so the scene file lands with T-1252 rather than here; adding one now would point
  a scene at an epoch with no ground.

## 6. Retrieval notes for the next run

- LOC **item** endpoints (`https://www.loc.gov/item/<id>/?fo=json`) answered 200 to unattended
  retrieval on 2026-09-17, though they rate-limit to 403 under a burst; a `--retry-delay 15`
  recovered every time.
- LOC **search** (`https://www.loc.gov/search/?…&fo=json`) answered 403 to the same client on the
  same day. Sibling HABS records are reachable by item id, not by search.
- `www.encyclopedia.chicagohistory.org` **did not resolve** from this runner on 2026-09-17, so the
  Encyclopedia of Chicago entries this project already cites could not be re-read. Nothing here
  depends on them.
- No period sheet for the 1880s lakefront has been identified yet. T-1250 needs one, and it will
  need georeferencing the way `rees_rucker_1849` was.

## 7. T-1250, 2026-09-28 — the four sheets georeferenced, and the 1904 lake edge

**The owner's ruling of 2026-09-26 moved the Prairie Avenue scene to 1904**, and Glessner House
supplied the sheets that answer §6's last bullet: Sanborn's 1911 Chicago vol. 3, sheets 20, 28
and 35, and Robinson's 1886 atlas, plate 10 (`chicago/reference/prairie-avenue/sanborn-1911-and-
robinson-1886/`). Each now has a source record (`sanborn_1911_chicago_v3_sheet_20`, `_28`, `_35`,
`robinson_1886_chicago_plate_10`); the Sanborn records carry the Library of Congress item,
`https://www.loc.gov/item/sanborn01790_020/`, read on 2026-09-28.

### 7.1 Where the georeferencing lives, for the next ticket that reads these sheets

| file | fit | RMS (2-D) | how it is checked |
|---|---|---|---|
| `data/traces/gcp/sanborn_1911_v3_sheet_20_gcps.json` | similarity at the printed scale, 0.05078 m/px | 2.46 m, 3 dof | leave-one-out per point; free affine printed beside it |
| `data/traces/gcp/sanborn_1911_v3_sheet_28_gcps.json` | similarity at the printed scale, 0.05056 m/px | 0.34 m, 1 dof | **three standing houses (1800, 1801, 1900 Prairie) land 1.47 m RMS, worst 1.90 m, from their OpenStreetMap outlines** — the fit never saw them |
| `data/traces/gcp/sanborn_1911_v3_sheet_35_gcps.json` | similarity at the printed scale, 0.18585 m/px | 0.05 m, 2 dof | a coarse copy (0.6 ft/px); its Prairie & Twentieth crossing is sheet 28's second control point |
| `data/traces/gcp/robinson_1886_plate_10_gcps.json` | similarity at the printed scale, 0.34597 m/px | 4.54 m, 3 dof | the weakest: a photographed, curved, rotated page |

All four are written by `tools/georef_prairie_1904.py` from picks in the tool and the modern
control in `data/traces/prairie_1904_control.json` (OpenStreetMap, fetched 2026-09-28 through the
editing API because Overpass refused the runner), and `check.sh` re-derives them. The formula is
the one every GCP file here uses — `local_e = a*px + b*py + c ; local_n = d*px + e*py + f` — so a
footprint pixel off any of these sheets goes into the local frame with six numbers.

**Why a similarity and not the affine `rees_rucker_1849` adopts.** The free affine was fitted and
is printed in each file as `affine_diagnostic`. On sheet 20 it comes out 5.84 per cent different
between its two axis scales, and the sheet says that is false: its printed Scale of Feet and its
66-ft street bands (Prairie 66.0 ft, 18th 65.2, Indiana 67.7; 16th Street printed 50 and reading
50.5) agree to about two per cent in both directions. What the affine reads as paper stretch is the
modern street net. **South Indiana Avenue's modern centreline stands 5–8 m east of the Indiana
Avenue both sheets draw** — the Sanborn block is two 178-ft lot tiers, a 20-ft alley and two
half-streets, 442 ft centre to centre, and OpenStreetMap has 126.8–129.4 m — and **Cermak Road
stands about 10 m south of the Twenty-Second Street sheet 35 draws**. So each modern crossing is
control only for the component that is still where the sheet draws it: Prairie Avenue crossings for
both (the corridor the houses still stand on, at the setbacks the sheets draw); Indiana and Calumet
crossings for their northing; the Cermak crossing for its easting. Scale is the printed bar's.
Robinson's plate is the exception to the band test: its bands are the engraver's (Prairie printed 66,
drawn about 55 ft), so it is scaled by its bar alone and says so.

**Twentieth Street is vacated** between Indiana and Calumet today and Calumet was re-laid north of
Twenty-First, so sheet 28 has one modern crossing that survives on both axes. Its second control
point is Prairie & Twentieth, northing transferred from sheet 35 (anchored at Twenty-First, 120 m
away), easting on the modern Prairie centreline. That is why its independent building check matters
more than its own RMS, and why the check is in the gate: `georef_prairie_1904.py` fails if the three
houses drift more than 5 m.

### 7.2 The lake edge: two bounds and a reconstructed line between them

`tools/trace_ic_edge_1904.py` writes `data/terrain/epochs/e1871_postfire/shoreline.geojson`.

- **Sanborn 1911 inks the water's edge in two short runs** — sheet 20 from the 16th Street row
  south about 60 m, sheet 28 from 40 m north of 18th Street to 80 m south of it — a pen line with
  the lake washed blue east of it, and stops although the tracks run on. **Robinson 1886 draws it
  the whole way from above 16th Street to 18th** as the west limit of its water-lining.
- **The edge moved.** Where both draw it the 1911 line stands east of the 1886 one by 14.0–18.7 m
  (mean 17.0) at the 16th Street run and 17.8–21.2 m (mean 19.9) at 18th. The fits put a few metres
  of that in doubt, not seventeen. The Illinois Central widened its right-of-way into the lake
  between the two sheets.
- **Both sheets are the wrong date, so both are bounds** — the house rule, and the ticket's own
  words. 1886 from before (the 1904 edge stood on it or east of it); 1911 from after (on it or west
  of it), which rests on one stated inference: a built edge beside the railway moves only lakeward
  unless something is removed, and nothing in this corpus records a removal. The spread is the band
  `ic_edge_1886_1911_band`; nothing is averaged.
- **The scene's waterline is reconstructed (L287)** on the band's eastern, 1911, bound: the nearer
  date, and Glessner House's reading that everything on these sheets but two houses stood in 1904.
  Where no 1911 sheet draws the edge, the 1886 planform moved east by the measured offsets stands in
  (segments A and C); below sheet 28's run the edge is carried along the easternmost drawn track,
  which runs parallel to it at 324 ± 2 px and straight on to the paper's edge (E); past that,
  to Cermak Road, it is a bearing and nothing bounds it (F).
- **Refused as a proxy: the modern railway.** At 18th Street the easternmost Metra / Canadian
  National track stands 78 m east of the 1911 water's edge, on the lakefill of the 1920s.

### 7.3 The 1852 trestle, ruled

The epoch's old note said the Illinois Central trestle "already fixed the shore in 1852", and
`docs/research/01-terrain-hydrology.md` § 4 still says "the Illinois Central's 1852 trestle then
fixed the line" with no source on the clause. The Chicago Public Library's *History of Grant Park,
1830–1871* (`cpl_grant_park_history_1830_1871`, tier 4) sources the trestle and refuses the
sentence: *"In 1852 the Illinois Central built a trestle about 300 feet east of Michigan Avenue and
the breakwater a little farther out. This left a substantial lagoon extending south to 12th street
where the railroad came on shore."* North of Twelfth Street the trestle stood in the lake with water
behind it, which is not a fixed shore; south of Twelfth — the whole of the Prairie Avenue reach —
the railroad ran on the beach and no trestle is described. The claim is not restored; what the
sheets show instead is that the edge beside the tracks moved.

### 7.4 What this still does not settle

- **Any height.** The shoreline is planform only. The zone table is T-1251's, the heightfield and
  the scene file T-1252's.
- **The ruled line on sheet 20's 16th Street row**, where the blue wash begins. It may be a shore
  turning east or only the edge of what the sheet covers; the trace starts below it and reads it
  as neither.
- **The lake south of 20th Street.** No sheet held here draws it east of Calumet Avenue. The Sanborn
  1911 sheet for that reach (sheet 36, by the index numbers printed on 28 and 35) would replace
  segment F, and it is on the same Library of Congress item.
