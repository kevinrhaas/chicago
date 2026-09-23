# North Pier — research memo

Record: `data/structures/north_pier.json` · Archetype: `pier_crib` (new, this parcel)
Written 2026-08-11. Companion memo: `south_pier.md`; both share §2 and §3.

---

## 1. What this record is for

The north (weather) pier of the federal harbour works: the northern of the two timber
crib lines holding open the 1834 cut through the sand bar. Congress appropriated $25,000
on 2 March 1833; work began in June 1833 under Major George Bender; the schooner
*Illinois* came through on 12 July 1834, the first vessel to enter the river; the 1835
appropriation was $32,800. It is the reason there is a harbour at Chicago at all.

## 2. What is measured: the line, off the master survey

**Wright 1834 draws the harbour as two red lines with HARBOR lettered between them and a
flow arrow running east down the channel.** Both lines were read at native resolution off
the BPL master scan (`commonwealth:js957744g`) and transformed by the affine recorded in
`data/traces/gcp/wright_1834_gcps.json` — the same transform `tools/rederive_datum.py`
checks the datum against, so this is not a second georeference.

| reading | resource pixel | local E | local N |
|---|---|---|---|
| north pier, landward end (inner face) | 3211, 1417 | **+1243.5** | **+311.9** |
| north pier, drafted seaward end | 3705, 1540 | +1588.8 | +229.9 |
| south pier, landward end (inner face) | 3171, 1498 | +1215.9 | +252.5 |
| south pier, drafted seaward end | 3665, 1622 | +1561.2 | +169.6 |

- North line bearing **103.36°** from grid north; south line **103.50°**. Parallel to a
  tenth of a degree.
- Perpendicular separation **64.2 m**.

**The check that says the right two lines were read:** the documented entrance width is
200 ft = 61.0 m. The measured separation is 64.2 m — **four per cent**, from a direction
sharing no input with the text that supplies the 200 ft. That is what licenses the
bearing and the root at `inferred` rather than `conjectural`.

Picking precision about 5 resource pixels ≈ 3.5 m, on top of the sheet's own ±20 m.

### A correction to an existing committed trace

`data/traces/vectors/wright_1834_east.json` carries a feature `harbour_north_pier` read
on 2026-08-10 as "the inner of the two red pier lines running ENE from the river mouth",
px `[3105,1440] → [3640,1610]`. Two problems, both visible against the reading above:

1. **The compass word is wrong.** Those pixels descend the sheet going east, i.e. the
   line runs **ESE**, not ENE. The `local_enu` values in the file are right; the prose
   describing them is not.
2. **The start point is not on the pier.** At px 3105 the northern red line sits at about
   py 1414 and the southern at about py 1495; py 1440 is between them, in the channel.
   The end point (3640, 1610) lands near the *southern* line. So the committed reading
   runs from mid-channel to the other pier, which is why it comes out at 107° rather than
   103.4° and why `docs/ROADMAP.md`'s "north pier, outer end +1544 / +178" is about 60 m
   south of where the northern line actually ends.

Neither is load-bearing for anything yet — the file is scoping data for S2e — but the
S2e box argument should be re-derived from the numbers in the table above.

### What the shoreline trace does and does not give

`shoreline.geojson`'s "North shore of the harbour reach" says in its own note that
between the piers it follows "the pier's inner face as drafted", and it does so out to
about local E +1250: its vertex at (1234.9, 314.7) sits **7 m** from the raster reading of
the pier root, which is a good independent agreement. East of about E +1250 it wanders
north and turns at E +1409 — because the grey wash of the channel merges with the grey
wash of the lake margin north of the pier and the segmentation follows the outer envelope
of the two. The trace is therefore reliable for the pier's root and not for its line
beyond the mouth.

## 3. What the survey cannot give: a length or a width

**Length.** Both drafted pier lines run about **1,165 ft**. The north pier was about
700 ft at the end of 1834; the south pier was about 200 ft and did not reach 1,165 ft
before 1837. A sheet dated 1834 drawing both piers at the same length, longer than either
had been built, is drawing the **authorised** works and not the built ones. So the
drafted extent is not a length at any date this project models. Using it would have put a
thousand feet of pier in a scene where the evidence supports nine hundred for this one and
four hundred for its neighbour.

**Width.** Wright 1834 is drawn at about 1:7,200. At that scale a 25-ft crib is 0.13 mm
of paper — about a fifth of the width of the pen that drew the pier line. The red bands
are line weight; measuring one would be measuring the draughtsman's nib.

## 4. The length is an interpolation, and it is graded `inferred`

| date | length | source |
|---|---|---|
| end 1834 | ~700 ft | `wikipedia_chicago_river` harbour-works summary |
| **1835-07-01** | **~900 ft (adopted)** | interpolation — this record |
| end 1835 season | 1,260 ft, "to twelve feet of water" | `andreas_1884_v1` I, scan pp. 487, 489 |

**No source reached gives a length for any date inside the 1835 season.**

Straight calendar interpolation puts 1 July at half the year and therefore at 980 ft. That
overstates it: crib building and sinking on Lake Michigan run in the open season, roughly
April to November, so by 1 July perhaps a third of a season's work is in the water and the
season-weighted figure is nearer 890 ft. Dossier 04 §3 reaches "roughly 800–1,000 ft" by
the same kind of reasoning. **900 ft** is the middle of that band and sits between the two
arithmetics.

**The error bar is the band**: anything from 800 to 1,000 ft is equally consistent, which
is ±30 m on a 274 m structure — an order of magnitude worse than the georeference, and the
reason the footprint is graded on the width rather than saved by the length.

### Two conflicts, recorded rather than averaged

1. **Inside this project's own research.** `docs/research/01-terrain-hydrology.md` §3.3
   interpolates the same pier at "roughly 1,000–1,300 ft" for summer 1835, because it
   works from 700 ft (1834) to 1,850 ft (Oct 1837) and had not found the end-of-1835
   figure. Dossier 04 found it. An interpolation that steps over a known intermediate
   value is superseded by one that does not, so 04's band is adopted and 01's is recorded
   as the reading it replaces.
2. **At the 1834 end.** Andreas has the north pier extended in spring 1834 "a like
   distance" — about 500 ft — while Wikipedia has it at about 700 ft by the year's end.
   Those are compatible as the start and end of one season's work, so both are kept and
   the year-end figure is where the arithmetic starts.

## 5. What is invented

- **`width_m: 7.62` (25 ft), `conjectural`** — the archetype's constant, shared with the
  south pier so both inherit one invention in one place. The only argument behind it is
  that a gravity crib in up to twelve feet of water carrying a working deck cannot be
  narrow, which supports "not narrow" and not twenty-five feet. The footprint inherits it,
  so the whole pier renders as massing (`_CONFIDENCE = 1.0` throughout).
- **`deck_height_m: 1.524` (5 ft), `inferred`** — the middle of dossier 01 zone 24's
  "~+4 to +6", which the dossier states without a citation. Everything a visitor sees of
  this pier is the band between the waterline and this number, so an error of a foot is an
  error of a fifth in the only dimension the eye can check.
- **`construction: timber_crib`, `inferred`** — no source record in this project states
  it. Zone 24 names the structure "North pier (timber crib)" and cites nothing; the texts
  held here give chronology, appropriations, supervisors and lengths and never say what
  the piers were made of. Timber cribbing sunk and stone-filled is how Great Lakes piers
  of the 1830s were built and what was available to a works run out of a frontier garrison
  with unlimited timber and no cement. A reading, not a report.
- **Crib module, 30 ft** — `pier_crib_params.CRIB_MODULE_FALLBACK_M`, deliberately not a
  record attribute (the argument `bridge_timber_params` makes about `pier_spacing_m`). A
  pier built out over several seasons ends where a season ended, not on an even module.

## 6. Why the phase is two months wide

A structure under continuous extension has no stable phase. This pier grew by about half
its own length during the 1835 season — roughly 3 ft a day if the work were even — so no
state of it lasted a fortnight. The `documented_range` is 1835-06-01 … 1835-07-31: the
value it carries is an interpolation stated *for* 1 July and wrong by a growing margin
either side of it. A scene at any other date finds no phase covering it and reports the
structure as excluded, which is the correct answer.

Adding phases is the fix and widening this one is not. An 1834 scene wants a 700 ft phase
closing 1834-12-31; an 1836 scene wants a 1,260 ft phase opening 1836-01-01. Both are
writable today from the same two sources; neither is written, because a phase nobody has
checked against a scene is a claim nobody has read.

## 7. Ground

`ground_contact: outside_modelled_ground`. The heightfield stops at local E +320; this
pier runs from E +1243 to about E +1510. There is no shore at its root, no lake around it
and no bar beside it. `pier_crib` declares `GROUND_CONTACT = "ends"`, which is the nearest
available reading and is half wrong by construction — a pier lands at its **root** and
never at its head — and that costs nothing while both ends are equally outside the box. It
will need a one-ended mode in the checker when S2e extends the terrain; written up in the
archetype's parameter module.

## 8. What would replace most of this

The Chief Engineer's annual report for 1835, or the House Document series — dossier 01
already names them. A single line in either would move `length_m` to `documented`. For the
width, J. D. Graham's 1857 and 1858 hydrographic surveys of the Chicago bar draw the piers
in plan at a usable scale.
