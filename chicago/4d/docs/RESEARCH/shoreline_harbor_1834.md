# The lake shore, the harbour reach and the sand bar — how they were traced

**Traced:** 2026-08-10 · **Re-traced whole:** 2026-09-12 (T-0799) · **Epoch:**
`e1834_harbor_cut` · **Extent:** local E +314 … +1583, N −2122 … +1121 · **Tool:**
`tools/trace_shoreline.py` · **Output:**
`data/terrain/epochs/e1834_harbor_cut/shoreline.geojson`

This is ROADMAP **S2e parcel (a)** — the vectors the eastern terrain extension needs. It
carries no elevations and builds no ground; the terrain box still stops at local E +320.
What it settles is the question that had to be settled first: **where the 1835 water ended.**

## Why the shore could not simply be drawn

Everything east of roughly Michigan Avenue is later landfill, much of it fire debris after
1871. The modern coast is about a kilometre east of the 1835 one at the river mouth, so
tracing today's shoreline into an 1835 dataset would have been the single largest false claim
in it — and it would have looked like diligence. The shore has to come off the same 1834
sheet as everything else, through the same affine, carrying the same ±20 m.

## What was traced, and how

Same sheet, same transform, same wash convention as the forks: Wright draws water as a grey
wash band on the water side of a black bank line. Two things differ, and both are recorded in
the tool because they are the reason it is a second tool rather than a wider window.

1. **The background statistic.** The forks trace measures "darker than paper" against a local
   64-px block, which is what lets it find a 70 m channel inside a town of coloured ward
   washes. Lake Michigan is washed as a band a couple of hundred metres wide, and against a
   local background a band that wide *is* its own paper — the interior reads as unshaded and
   only the two edges survive. This trace measures against the whole window instead. That is
   the right answer here and the wrong answer at the forks.
2. **The sand bar is a hole.** The water body is one connected thing — main stem, the 1834
   cut, the old southward channel, the lake margin — and the bar is the island it runs round.
   So the bar comes out of the segmentation as a hole in the water, which is exactly what it
   is on the map, and it is carried as the water polygon's interior ring.

Six numbers are hand-placed on the scan and nothing else is: three seeds that pick the water,
and two anchors that claim a boundary run for a name. A run no anchor claims within 60 px is
not written.

## What came out

| feature | form | extent (local m) | confidence |
|---|---|---|---|
| `harbor_reach_water` | polygon + 1 interior ring | E 314…1574, N −589…503 | `inferred` |
| `sand_bar_1834` | polygon, 44 vertices, 1.5 km perimeter | E 1305…1498, N −436…225 | `inferred` |
| `south_shore_harbor_reach` | line, 102 vertices, 2 466 m | E 314…1257 | `inferred` |
| `north_shore_harbor_reach` | line, 57 vertices, 1 568 m | E 314…1464 | `inferred` |

`inferred`, not `documented`, for the same reason the forks river polygon is: a cadastral plat
is not a hydrographic survey, and the georeference is good to tens of metres, not to the metre.

## The cross-check that came free

The two traces overlap by 80 m — this window's west edge is at local E +314 and the forks
window's east edge is at E +398 — and they were produced by different segmentation settings in
different windows. In the overlap they agree to **0.1–5.7 m on the south bank and 0.5–1.3 m on
the north**, against a ±20 m georeference uncertainty. That is not proof the line is where the
river was; it is proof the segmentation is measuring the draughtsman's line rather than its own
parameters, which is the part that was worth checking.

## What is deliberately not in the file

- **The lake east of the traced shore.** One boundary run is found, reported and dropped:
  3,936 m of it, the whole east side of the water body, with no drawn line anywhere under it.
  It is not a shore — it is where the draughtsman stopped washing. Nothing in this file
  describes the lake beyond the traced edge. Since T-0799 the water polygon's eastern
  boundary is Wright's brush rather than this program's window.
- **Any elevation for the bar.** A sand bar is a surface that a couple of feet of lake stage
  moves, no source gives its height, and inventing one to make it render would be exactly the
  kind of quiet gap-filling `AGENTS.md` forbids. Elevations are argued for in
  `terrain_spec.json` or not at all.
- **The piers.** Wright draws the 1834 cut as a straight channel between two pier lines, and
  between them the traced boundary is the pier's inner face as drafted — not a natural shore.
  The feature says so in its own `note`. Piers are structures with phases (`docs/EPOCHS.md`),
  so their alignment is not a terrain claim and they are not modelled here.
- ~~**South of about N −580.** The trace leaves the window there.~~ **Closed by T-0799,
  2026-09-12.** The shore now runs unbroken to the foot of Wright's drawing at about
  N −2122 — 3.8 km of it against the 2.3 km published before — and the old southward
  channel closes inside that run rather than leaving it: behind the bar the wash narrows to
  the arrow Wright draws and its west bank runs on into the lake shore, so the channel and
  the shore are one line there and the trace does not pretend to divide them. The last 200 m
  along the foot of the wash carries the sheet's dark bottom edge rather than a clean pen
  line and is the weakest part of the run; `ink_distance_p90_m` on the feature is the number
  to read before using it.

## What this settles for the terrain extension

Measured, rather than estimated:

| | local E |
|---|---|
| current terrain box east edge | +320 |
| mainland shore, at its most eastward (the fort reservation) | **+1257** |
| sand bar, east edge | **+1497** |
| traced window east limit | +2043 (the wash stops at +1583, well inside it) |

So ROADMAP S2e's proposed **E +1500** box is confirmed as the right order of magnitude but is
about 3 m from clipping the bar. **+1560** is the number to use — it takes the whole bar and
stops inside the traced evidence rather than past it.

Two consequences for parcel (b), the heightfield:

- The bar is **land inside the water**, so the "distance from the waterline" rule that builds
  the forks terrain needs a signed distance that understands islands, not just banks.
- The extension roughly triples the modelled area. At the current 2.5 m cell that is ~213k
  samples (~425 KB int16); the evidence east of the built blocks does not support 2.5 m detail,
  so a coarser cell out there is worth considering — but that is a resolution decision, not a
  provenance one, and it belongs with the terrain spec.

## Re-running it

```
pip install numpy scipy pillow pyproj
python3 tools/trace_shoreline.py            # rewrites the GeoJSON
python3 tools/trace_shoreline.py --check    # re-traces and diffs against what is committed
python3 tools/trace_shoreline.py --debug    # + a PNG overlay of water, island and runs
```

Like the forks trace and the datum re-derivation, it is **not** in `tools/check.sh`: it needs
the network and three libraries the gate deliberately does not require. The IIIF region's
sha256 is recorded in the output, so the input is pinned even though the fetch is not.

## T-0799 — the east edge in one run, and how the window stopped deciding anything

*2026-09-12, on the owner's ask: "both piers, the cut, the sand bar to its tip, the old
channel to where Wright closes it, and the shore to the sheet's bottom margin — one run, no
window."*

The 2026-08-10 trace worked in an 1802 × 1500 px box around the harbour, and three of the four
things that box did were damage. Its east edge fell **inside** the lake wash, so the traced
water ended on a straight line of window and the harbour polygon published that line as its own
eastern boundary; its south edge cut the shore off at local N −589, a kilometre short of where
Wright draws it; its north edge cut it off again above the harbour. The box was doing the one
job a window must never do — deciding where a shore ends.

The window is now the whole sheet east of the forks box: `REGION = (1878, 150, 2222, 4800)`,
margin to margin. The wash band closes on itself inside it, so the whole east edge arrives as
**one ring with no window edge in it at all**, and the only window edge the trace still carries
is the deliberate junction with `tools/trace_river.py` at local E +314.

That leaves the trace with a question the window used to answer for it: which half of that ring
is a shore? It is answered on the drawing. **Wright draws a shore and does not draw the far side
of a wash** — so a boundary vertex belongs to a shore when there is a drawn line under it, and
the rest is dropped. "A drawn line" had to be sharpened once: a luminance threshold alone calls
the pigment a brush pools at the edge it dries against "ink", and along the bottom third of the
east edge that pooled band comes within a few units of it. A pen line is a **ridge** — darker
than what lies on either side of it, so a grey closing fills it in and the black top-hat is
large. A wash edge is a **step**, and a closing leaves a step where it found it. Measured on
this sheet: the inked south shore reads 138–142, the pooled east edge 40–64, open lake 12.

The result, both published runs: **a median 1.42 m from the drawn line** (p90 5.7 m north,
7.4 m south), against a dropped east edge whose nearest ink is hundreds of metres away.

### The blast radius, and why the committed walk still stands

Opening the window moves the background percentile the wash test measures against, so the
segmentation shifts by a pixel or two *everywhere* — a median 0.8 m on the south shore, 1.3 m on
the north, against a declared uncertainty of ±20 m. None of that is a better reading, and the
ground is carved from this file: republishing a kilometre of re-simplified vertices would have
moved the committed heightfield under every consumer of it for no gain, while destroying the one
thing a change like this has to be able to show — that only the east edge moved. It is the same
argument `splice_lettering` already makes for one lettering box, at the scale of the whole file.

So the trace **splices**. The committed walk stands wherever the fresh one agrees with it inside
`SPLICE_TOL_M`; the fresh walk is spliced onto the ends that used to run along a window edge, and
onto the reaches the window cut off. The tolerance is measured rather than chosen: the **sand bar
is the control** — a closed island wholly inside the old window, which nothing in this ticket
touches — and its worst committed vertex stands 6.32 m from the fresh walk (median 0.63 m, p95
2.21 m). Seven metres is set just clear of that. At it the bar stands whole, 43 of 43 vertices,
which is the assertion that matters; the north shore keeps 43 of 57 and the south 68 of 92, and
the 14 and 24 that go are exactly the vertices that used to lie along a window edge.

The terrain re-bake is **T-0800**, not this: nothing here moves the ground, and
`tools/measure_no_build_ground.py --gate` still reports zero cells of modelled land outside the
refused polygons. `--retrace-all` publishes the fresh walk everywhere for the day that changes.
