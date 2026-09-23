---
id: T-0792
title: The legend's nine coloured tracts are the town's survey history — who surveyed what ground, when, for whom — and the project has no tract layer
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: null
claimed_by: run 9/12/2026, 6:19:08 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T23:32:59.024Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34724869993
---

**The source, 2026-09-05.** The owner added a second copy of J. S. Wright's manuscript survey of
1834 at `chicago/pre_fire_v1/maps/images/1834-wright-map.jpg` — the Historic Urban Plans (Ithaca) reproduction of the
**National Archives original**, 5050 × 6628 px at 600 dpi, with its own caption: *"Two portions are
missing, the larger being near the lower center … the manuscript was mounted on cloth to repair this
tear."* It is a different scan of the same drawing this project already traces as `wright_1834`
(the BPL/Leventhal copy, 4204 × 5166 px, IIIF `commonwealth:js957744g`). The owner's instruction:
*"review this and create tickets to update and enhance the map … several items from this map should
be incorporated including the streets, there are streets documented here that are missing, including
the blocks, where the public square is, where the various sloughs are, things like 'the kinzie block'
… look at all of the streets and block numbers … the lakeshore edge and that whole area … the whole
path of the river going south … note the sections as labeled in the legend."*

## What the sheet shows

Wright's legend is nine coloured swatches, each a survey tract with its date and, by implication,
its owner:

| swatch | tract | what it colours on the sheet |
|---|---|---|
| blue | **U.S. Military Reservation** | the Fort Dearborn ground south of the river's bend, bounded on the south by Madison's line |
| pink | **Surveyed by Canal Comm. in 1830** | the Original Town — Thompson's plat, all three divisions |
| red | **Wabansia, surveyed 1831** | the tract north of Kinzie Street, west of the North Branch |
| green | **Kinzie's Addn, surveyed 1833** | east of the Original Town north of the river, to the lake |
| yellow | **School Section, 1833** | section 16, south of Madison to 12th, State to the west line |
| grey-green | **Surveyed 1833** | (to be read on the registered scan — the long canal-lot strips west of Des Plaines, and/or the North Water strip) |
| brown | **Fractional Section 15** | the lake-shore strip east of State Street, south of Madison |
| orange | **Surveyed in 1833** | (to be read — a second 1833 survey, distinct from the school section) |
| dark green | **Part of Canal Sec. No. 9** | the west-side strips between the Original Town's west line and the section line |

The owner: *"note the sections as labeled in the legend, those will be helpful."*

## What the project has

No tract layer of any kind. Ground is either the Original Town's plat module or unplatted; the
military reservation is a shore run and a no-build polygon, not a tract; nothing records that the
ground under Wabansia was surveyed two years before the ground under the Addition, or that the
school section belonged to the school fund and the canal sections to the canal commissioners, or
where the Original Town's pink stops and the canal strips' green begins.

## Why this is foundational

Three things the town needs come from the tracts and nowhere else:

1. **Who could sell what.** A lot in the pink was the Canal Commissioners' to sell (1830); in the
   yellow, the school fund's (October 1833); in the green, John H. Kinzie's; in the blue, nobody's.
   `data/research/land_sales/` reads federal, canal and school sales into one file and has no
   ground to sort them onto.
2. **What was platted on 1 July 1835.** The legend dates every survey; the town's *platted extent*
   on the scene date is the union of the tracts surveyed by then, and it is drawn here.
3. **Where the plat's rules change.** Thompson's 80 ft streets and 8-lot blocks stop at the pink's
   edge. Kinzie's Addition and the School Section have their own modules (T-0789, T-0791), and the
   tract polygon is what tells a generator which module to apply.

## The ask

1. **`data/reconstruction/1835_survey_tracts.json`** (or the reserved-ground file's sibling): nine
   polygons traced off the registered scan (T-0787) along the colour boundaries, each with the
   legend's wording verbatim, its survey date, its owner on the scene date with the source for that,
   and a grade. The lake-shore tracts close on the shore T-0793 traces.
2. **Read the two ambiguous swatches** — the grey-green *Surveyed 1833* and the orange *Surveyed in
   1833* — by matching swatch to ground on the sheet, and say which ground each is. Do not guess
   from the legend order.
3. **Sort the land sales onto the tracts.** Every row in `land_sales/` that names a section or a
   tract gets the polygon it falls in; the count per tract is the first honest statement of how much
   of the town's ground had changed hands by the scene date.
4. **Feed the generators.** The plat module reads the tract it is inside to choose its street width
   and block module; the reserved-ground file cites the blue polygon for the fort; the flora zones
   can read *unplatted* as a fact rather than an absence.

**Done when** nine dated, owned tract polygons exist with the legend cited, the two ambiguous
swatches are resolved to ground, the land-sale rows are sorted onto them, and at least one generator
reads the layer.

## Added by T-1065, 2026-09-12 — a control inside the reservation swatch

Wright's *L. House* glyph is now read and committed — resource pixel (2941, 1604), local
E +1055.59, N +172.54, at `data/traces/wright_1834_lighthouse_glyph.json`. It sits **inside the
reservation swatch**, 40.9 m in from the derived tract's edge (the derivation reports that margin
itself: `tools/resolve_land_tracts.py --check`). Two uses when this layer is built:

1. **A control, not just an occupant.** When the reservation's blue edge is traced off the legend's
   swatch, this glyph is a point of known pixel and known metres inside it — so the traced polygon
   can be checked against something on the same sheet rather than only against the affine.
2. **A margin that should not shrink.** 40.9 m is the current distance from the tower to the
   *derived* tract, which L108 says is a floor and short of the documented 75.69 acres. A traced
   blue edge should put the tower further inside, not nearer the boundary; if it does the opposite,
   one of the two readings is wrong and that is worth knowing early.

T-1065 deliberately did not author this swatch — a tract authored outside the tract layer is the
thing this ticket exists to prevent.
