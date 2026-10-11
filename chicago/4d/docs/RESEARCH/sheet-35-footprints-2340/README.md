# Sheet 35's 1904 building footprints (T-2340)

**What:** every building on the Prairie Avenue lots of Sanborn 1911 vol. 3 sheet 35
(20th to 22nd Street, both faces) as an outline in local metres, each keyed to its
[T-1842 census](../../../../prairie_1904_v1/data/sheet_census/sheet-35.json) polygon:
**31 grounds, 60 buildings (31 fronts, 29 alley buildings), 226 parts**, in
[`data/traces/prairie_1904_footprints_s35.json`](../../../data/traces/prairie_1904_footprints_s35.json).

**Why:** T-2161 drafts this block, and requires each house's footprint "from the
reconciled Sanborn polygon, never the viewer's parcel rectangle". The census names every
building but digitises none. T-2327 and T-2328 did sheets 28 and 20 for T-2159 and T-2160;
this is the same reading for sheet 35, and T-2161 waits on it.

**How:** the same tracer (`tools/trace_prairie_1904_footprints.py`), given sheet 35 as one
more `SHEETS` entry: its fit (`data/traces/gcp/sanborn_1911_v3_sheet_35_gcps.json`), its
census and the four T-0474 blocks between 20th, 21st and 22nd Streets. **Sheets 20 and 28's
outlines, metadata and overlays are byte-for-byte unchanged** by everything below
(`--check` on all three sheets).

## The copy is 3.7 times coarser, and the rules say so

Sheets 20 and 28 are 5,879 × 7,323 px scans at 0.0506–0.0508 m/px. Sheet 35 is the
1,602 × 2,000 px copy the owner attached (the source record and the reference README both
flag it), **0.186 m/px**. Read with the fine scans' rules unchanged, it traced 69 parts and
six contract failures. Four general rules, each with a self-test:

1. **The pixel rules are paper lengths.** A drawn wall, a letter, the gap a porch leaves
   are printed at a fixed size, so every `*_PX` rule is divided by the scan's resolution
   ratio, rounded to one decimal so that the two scans the rules were set on read at exactly
   1.0. Sheet 35 reads at 3.7: bridge 2 px (+1, rule 2), wall half-width 1 px, smallest
   part 0.9 m², smallest building 1.8 m².
2. **On a coarse scan a wall is found by its darkness.** A one-pixel wall blurs into the
   pink wash (a wall pixel reads `(134, 96, 95)`, which the brick rule accepts), so it
   joined the parts it divides. At 2× or coarser, a pixel whose mean channel is under 140
   is line, and a straight wall broken for up to 3 px by lettering is closed along rows and
   columns. Not applied on the fine scans, where it would eat the darker washes' edges.
3. **A service building joined to the house by a long rear range.** 2035's census names a
   rear building "joined to a 2-storey brick building on the alley"; drawn continuous with
   the house, it begins 24 m back on a 54 m lot, ahead of the rear 30 % the split looks in.
   The rear share now widens (30 → 45 → 60 %) only when the step before split nothing **and
   nothing on the lot stands apart from the house** (sheet 20's 1720 keeps the joined-outline
   rule). 2009's garage splits the same way at 30 %.
4. **Several frontages on one lot.** The T-0474 grid has one strip, `prairie_2000`, under
   2000, 2010 and 2018. The buildings nearest the street, one per frontage, are the fronts,
   taken in address order (numbers rise southward, so north first); every other building
   goes to the front whose strip along the street holds its centre. Each lot's division is
   written on the row (`frontage_shares`). It applies only where every front begins in the
   street half of the lot, so sheet 20's 1700/1706, two townhouses drawn as one building,
   stay one share.

And two that are about the record, not the scan:

- **A non-building frontage with nothing drawn on it** (2141, "no building, street to
  alley") is carried as `census_ids_on_ground`, not reported as untraced.
- **`for_1904: phase_unresolved`** for 2126, which the census leaves open (Robbins, building
  or rebuilding about then). T-2161 declares one phase; the outline is the 1911 one.

## Limits

- **Accuracy:** the fit is a similarity at the printed scale on 2 degrees of freedom, so its
  0.05 m residual says little away from its crossings, and the file says so. A pixel is
  0.19 m; relative accuracy inside a lot is about **0.4 m** (sheets 20 and 28: 0.1 m).
- **Parts are rougher than on 20 and 28.** Outlines follow the drawn walls well (see the
  overlays), but at 0.19 m/px dashed interior lines sometimes close into walls, so several
  houses (2036, 2112, 2140) carry thin `range` strips inside their outer wall around a
  `main` body. The main body, which the draft builder stands the house on, is the
  reliable reading; T-2161's fit (largest rectangles inside the fill) is robust to the
  strips. 2125's frame stable is not recognised as a crossed square and comes out as five
  small `porch` parts; its outline is right.
- **Outlines carry the sheet's roof marks.** The wavy edge symbols and corner dots sit on the
  walls, so outlines bulge by up to about half a metre in places.
- **2140's `walls` id** (a non-building use) goes onto the house outline with its front, the
  rule every sheet uses for a non-building use at the street.
- **2108 and 2110's alley buildings trace as two**, one per lot, as drawn; T-2161 rules
  that the 2108/2110 coach house is one shared building and stands Rees at 2110.
- **Tiers:** outlines and part roles are INFERRED, as on sheets 28 and 20. Storeys are not
  read here: the census notation is the storey reading.

## Overlays

`overlay-west.jpg` and `overlay-east.jpg`: building outlines in red, parts by role (main
blue, range green, porch orange, stone front purple), drawn on the copy enlarged 4× so the
lines read at the fine sheets' paper scale. Regenerate with
`python3 tools/trace_prairie_1904_footprints.py --sheet 35 --overlay docs/RESEARCH/sheet-35-footprints-2340`.
