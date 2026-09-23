# Which PLSS section is which, on Wright's sheet

The owner asked a question of the crop north of the river — *"that looks to me the
michigan st area is fractional section 16, which must have a meaning in other sources
and is described somehow i hope"* (2026-09-05, T-0796). The instinct is right and the
number is not, and the reason is worth writing down once rather than re-deriving every
time a source names a section.

## The corner the project already owns

`data/traces/gcp/wright_1834_gcps.json` G1 is *State St & Madison St — PLSS section
corner: sections 9/10/15/16, T39N R14E*. That one committed point fixes the whole
numbering, because in a township the sections of a row run 7–12 west to east and then
13–18 east to west. At the State/Madison corner that puts

| | west of State | east of State |
|---|---|---|
| **north of Madison** | **9** | 10 |
| **south of Madison** | **16** | 15 |

and a section is one mile square. So section 9 runs from Madison Street north to the
line a mile above it — Chicago Avenue — and from State Street west to the line a mile
west of it, Halsted Street. Section 16, directly below 9, is the mile between Madison
and Roosevelt: **the School Section**, which this very sheet letters, washes and names
in its own legend.

## What that makes each tract on the sheet

| tract | section |
|---|---|
| the Original Town (Thompson 1830, *Surveyed by Canal Comrs in 1830*) | 9 |
| Wabansia (*Surveyed in 1831*) | 9, its north-west part, across the North Branch |
| **the Michigan St tract north of Kinzie Street** | **9** |
| Kinzie's Addition (*Surveyed 1833*) | fractional 10, cut by the lake |
| the School Section (*1833*) | **16** |
| the lake-shore strip south of Madison | fractional **15**, which the legend names |

So the tract north of Kinzie Street is in **section 9**, not 16. No ground north of the
river can be in 16 on the numbering the project's own control carries: 16 is a mile
south of Madison Street, and the sheet draws it, a mile from this tract, under its own
name.

What is true of the owner's reading is everything except the digit. The tract *is* in a
named canal section; the legend's ninth wash is *Part of Canal Sec. No. 9*; and a
section number read here *is* a key straight into `data/research/land_sales/`, which
sells by section. The key is 9.

## The check

The derivation is not fitted to anything but G1 and the mile. Run the committed section
corner and the committed Kinzie Street line through Chicago's own numbering — 800 to the
mile, counted from Madison — and Kinzie Street comes out at **390 north** against the
**400** it actually carries. Twenty metres, on a sheet whose fit carries 16.19 m RMS.
`tools/read_michigan_st_tract.py --check` re-derives that on every commit.

## Where the numbers are

`data/traces/michigan_st_tract_grid.json`, under `sections` — the corner in local ENU,
each section's box, the check, and the answer in the owner's own terms.
