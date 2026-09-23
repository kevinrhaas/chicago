# North Water Street ran inside the river, and the street was the record that was wrong

> **Sequel, 2026-09-04:** T-0447 finished the job at the east end — the last two
> vertices of the schematic this memo replaced had survived because they were dry.
> See [north_water_east_end.md](north_water_east_end.md).

**T-0226. Settled 2026-08-28.** The question the ticket set was research, not a nudge:
North Water Street's committed centreline stood inside the terrain's water mask for
**477.4 m of its 843.3 m**, in one unbroken run from `[200.2, 55]` to `[675.4, 95.7]`,
and the ticket refused in advance to let either record be moved to make the picture
work. Two records disagreed by up to 86 m and both had sources behind them. One of them
had to be shown wrong.

## What the disagreement actually was

Measured off the committed heightfield at 20 m stations, walking north from the main
stem to the first dry cell — the same test the renderer runs, `heightfield.sample(e, n)
< -0.10`:

| E | old street N | north bank N | street south of the bank by |
|---|---|---|---|
| 200 | 55.0 | 140.8 | 85.8 |
| 300 | 63.5 | 113.5 | 50.0 |
| 400 | 71.2 | 106.9 | 35.8 |
| 500 | 79.3 | 95.8 | 16.5 |
| 600 | 88.3 | 93.1 | 4.8 |
| 660 | 94.2 | 95.7 | 1.5 |
| 680 | 96.2 | — | dry from here east |

The two lines converge eastward and cross at about E +678. Everything west of that is
river.

## The four readings that decide it, and none of them is a preference

**1. The bank is a trace; the street line was not, and said so.**
`data/terrain/epochs/e1834_harbor_cut/river.geojson` carries `traced_from:
wright_1834`, the grey bank-wash segmentation method, the IIIF region and its sha256,
`affine_rms_m: 17.5`, and a stated `uncertainty_m: 20`. North Water Street's record
carried `geometry_confidence: reconstructed` — the bottom tier — and a note in its own
words: *"A schematic bank-following path used for orientation and readout … the
committed street module does not yet carry enough control to claim this curve as a
trace."* It has no entry in `data/traces/street_control.json`, which is where a street's
control lives. (The ticket said the line graded `inferred`; it graded one tier lower
than that, which strengthens rather than weakens the finding.)

**2. The error is four times the trace's own uncertainty.** 86 m against ±20 m is
4.3×. Tracing wobble cannot produce it, and neither record's error bars reach the other.

**3. The project had already adjudicated this exact conflict, in writing, in the bank's
favour.** `data/reconstruction/1835_north_division_initial_parcel.json` places the North
Division's roofs under the standing constraint *"Reject any footprint whose sampled
terrain cell is water; **proximity to North Water Street never overrides the
authoritative water mask**"*, and the `north_water_west` cluster's own rule is *"keep
every roof north of the authoritative water mask"*. The decision was made when the
roofs were placed; it had simply never been carried back to the street.

**4. The fabric is where the bank says, not where the street line said.** That parcel's
occupied envelope has its south edge at N +105 — north of every point the old street
line held west of E +700 — and the nearest riverfront roofs of the `north_water_west`
cluster stand at N +153 to +168. Not one building in the town was placed against the old
line. A street with its whole fabric 60 to 100 m to the north of it is not where the
street was.

**A schematic path is also, by construction, the record that CAN be wrong by 86 m.** It
was drawn to follow the bank, and the finding is that it did not — it fails its own
stated definition, which is the cleanest possible refutation.

## What was changed, and what was not

The bank is untouched. The street is re-derived FROM it, by
`tools/derive_north_water.py`, which is committed and gated: North Water Street fronted
the main stem, so its platted corridor is laid with its south line on the bank and the
centreline falls **12.192 m** north of it — half the 80 ft `thompson_module_1830` this
project applies town-wide. The fit is the fewest straight runs that clear the bank at
every 5 m station (running-max over ±15 m, so metre-scale notches in a 2.5 m raster are
cleared rather than followed) and never stand more than 8 m beyond the setback, with
0.5 m of give below it — 2.5 % of the trace's own ±20 m, and the difference between a
street and a line that changes bearing every 30 m.

    [240, 136.5] [560, 106.2] [780, 110.2] [830, 108.5] [920, 190] [970, 270]

Six bends where there were eight; 807.3 m of centreline, **none of it wet**; the drawn
6 m track between 12.0 m and 26.3 m clear of the waterline with both its edges dry along
the whole reach, so no panel is trimmed. `tools/measure_road_joints.mjs` reads **0 bends
refused for water** where it read 3, 0.000 m² uncovered, and 0 page errors.

## The one thing that is deferred, and it is a finding of its own

**The west terminus is the slough, not Wolf Point.** The attested *"Unnamed slough,
north side"* (`hydrology.geojson`, confidence `attested`; Wright 1834 draws it running
north out of the main stem, across Kinzie Street, ending at Michigan Street) meets the
river in a funnel between E +170 and E +270, reaching N +145. A ribbon may not paint
over a watercourse — R-BUG4 — and the town's other two slough crossings are modelled
**structures**, `slough_log_bridge` and the La Salle Slough Crossing, not roadway. So
the derived line begins at `[240, 136.5]`, on the funnel's east shoulder and 16.5 m
clear of its nearest water, and the reach west of it waits on a crossing record.
**T-0254** carries that. The old line's west end at `[200, 55]` was 85.8 m out in the
river and drew nothing, so no drawn roadway is lost.

**Links:** T-0226 · T-0184 (which found it) · T-0106 (the 1834 survey windows) ·
T-0254 (the crossing) · `tools/derive_north_water.py` · `tools/measure_road_joints.mjs`
· ROADMAP **B-BUG4**.
