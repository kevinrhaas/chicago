---
id: T-0796
title: The small tract north of Kinzie Street lettered Michigan St — small parcels and an alley where every neighbour is whole blocks, and a road curving north through it — is unidentified: which survey, which legend swatch, and what the sources call it
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
claimed_by: run 9/12/2026, 7:35:49 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T12:58:01.890Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34693915041
---

**The owner, 2026-09-05, on the crop of the North Branch:** *"look at that michigan street area
north of the river, that has some alleys and small parcels, so that must be special"* — and then:
*"that looks to me the michigan st area is fractional section 16, which must have a meaning in other
sources and is described somehow i hope."* Source sheet: `chicago/pre_fire_v1/maps/images/1834-wright-map.jpg` (T-0787).

## What the sheet shows

Immediately **north of Kinzie Street**, east of the North Branch and west of the open unsurveyed
ground that carries the sheet's title, Wright draws a **small square tract** unlike anything around
it: a grid of **small parcels with a mid-block alley**, an internal street lettered **Michigan St**,
and a wash of its own colour. Every neighbour is whole blocks — the Original Town's north-division
blocks 1–7 to its south, Kinzie's Addition's 54 to its east, Wabansia's 79 across the branch. Small
parcels and an alley on an 1834 sheet mean ground somebody expected to build densely, or had
already built on.

Two further things on the same crop: a **road drawn as a curved double line** leaves the
Kinzie/North Water corner and curves north through this tract — the only road Wright draws that is
not a platted street, apart from the fort's; and the tract's **"Michigan St" is not Kinzie's
Addition's Michigan Street**, which lies a quarter-mile east on the Addition's river tier.

## What the project has

Nothing under any name. `data/streets/1835.json` has no street north of Kinzie west of Wolcott; no
road north of the river at all beyond `north_water`; and the tract layer T-0792 asks for does not
exist yet. The North Division parcel places roofs east of here on a grid it does not have (T-0789).

## The owner's section reading, and how to test it

The owner reads the tract as *fractional section 16*. **That should be tested, not adopted**, because
the sheet's own control says otherwise about the numbering: `data/traces/gcp/wright_1834_gcps.json`
G1 is *"State St & Madison St — PLSS section corner: sections 9/10/15/16"*. Madison is the line
between 9 (north) and 16 (south); State is the line between 9 (west) and 10 (east). On that
numbering the whole Original Town north of Madison sits in **section 9** — the legend's *"Part of
Canal Sec. No. 9"* — Kinzie's Addition in fractional 10, the lake-shore strip south of Madison in
fractional 15, and **section 16 is the School Section**, a mile to the south. A tract north of the
river cannot be in 16 on that numbering. Either the owner is reading a different numeral, or the
tract carries a label this review's crops did not resolve. **Read it on the 600 dpi scan and say
which.** The owner is right that a named fractional section *"must have a meaning in other sources"*
— the federal land register (`data/research/land_sales/`) sells by section, and a section number
read here is a key straight into it.

## The ask

1. **Identify the tract.** Read its wash against the legend's swatches (T-0792's two unresolved
   ones, *Surveyed 1833* grey-green and *Part of Canal Sec. No. 9* dark green, are the candidates);
   read any numeral or name on or beside it on the registered scan; then go to the sources — Andreas
   on the additions north of the river, the Democrat's 1834–35 land notices, the canal
   commissioners' sales — and say what it was called and who laid it out. Wolcott's Addition and the
   canal commissioners' own north-bank lots are the first two things to test.
2. **Its street, its alley, its parcels** into the data with the sheet cited — the parcel module
   here is its own (small lots, an alley), and it must not be the Thompson module.
3. **The road.** Trace the curved road off the sheet as a `data/streets/` entry of the same kind as
   `fort_road` — a track, not a platted corridor — and find its name: the road north from the
   Kinzie house toward Green Bay is the obvious candidate, and the sources that name the Green Bay
   road's start will say.
4. **The section numbering, settled once**, in the tract layer's doc: which PLSS section each tract
   on the sheet falls in, from the GCP corner outward, so that a land-sale row that names a section
   lands on the right ground and the owner's question has a written answer.

**Done when** the tract has a name and a source, its street/alley/parcels and the road are in the
data off the sheet, and the section-numbering note answers the owner's reading either way.
