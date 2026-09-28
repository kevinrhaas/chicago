# Terrain e1871_postfire — the ground the 1904 Prairie Avenue scene stands on

T-1251, 2026-09-28. The research behind `data/terrain/epochs/e1871_postfire/terrain_spec.json`.
Every elevation in that spec cites one of the numbered zones below, and every number here that
came from a reading is in `data/terrain/e1871_grade_readings.json`, which
`tools/check_terrain_e1871.py` re-derives the spec from on every commit.

**What this is and is not.** It is a zone table for the ground of 1 July 1904 between Michigan
Avenue and the lake, just north of 16th Street to Cermak Road (the owner's ruling of 2026-09-26
centred Prairie Avenue on 1904). It is not a heightfield — that is T-1252 — and it places no
street, curb or building. The epoch id stays `e1871_postfire`, which names the post-fire grade,
not the scene year.

**The one idea it rests on.** No survey of the 1904 levels of this reach has been found. But
this is the one stretch of old Chicago where the houses of the period still stand in numbers,
on the grades they were built to: the Glessner House (1886–87), the Kimball House, 1811, 1919,
2013 and 2017 Prairie, 2020 Calumet. A street re-graded since 1904 would have left them standing
above or below it. Their walks read within 0.2 ft of the crown of Prairie Avenue in front of them
on the modern bare-earth model. So on that stretch the modern crown **is** the 1904 crown, as an
inference with a stated basis; away from it the same reading is carried back with nothing to
confirm it, and is reconstructed.

Each zone states the date it describes. Where the 1888 ground would differ, it says how.

## Zone 1 — The vertical datum and its conversions

The internal datum is the one the 1835 ground uses (`data/datum.json`): Z = 0 at the summer-1835
water surface, exported as 580.0 ft "ASL". Two conversions are needed and both are stated:

- **NAVD88 → Z: subtract 580.0 ft.** The only modern elevations here (USGS 3DEP, `usgs_3dep_1m_dem`)
  are in NAVD88, and `data/datum.json` names no vertical datum for its "ASL". This file takes
  NAVD88 as that datum and says so.
- **Chicago City Datum → NAVD88: add 579.2 ft**, the Chicago Public Library's worked conversion
  that `docs/research/01-terrain-hydrology.md` § 1.1 quotes (and its warning not to use the
  579.88 ft figure, which is on the obsolete mean-tide-New-York datum).

**Cross-check.** City of Chicago benchmark 289, 23rd Street at Michigan Avenue
(`chicago_elevation_benchmarks`), is 13.572 ft CCD, fixed 1966 — 592.77 ft NAVD88 by the
conversion. The 3DEP model reads 592.77 ft at the benchmark's own coordinates. Two independent
measurements, forty-odd years apart, agree to the hundredth of a foot; it is enough to say the
model and the conversion are one datum.

## Zone 2 — The water surface in 1904

No lake stage for 1904 has been found in this corpus. The water is held at the 1835 plane, Z = 0,
so the two scenes' lake stands at one level. `docs/research/01-terrain-hydrology.md` § 1.2 gives
the historic range as 576–582 ft, which is Z −4 to +2; that bounds it. **Reconstructed.** A
Lake Michigan stage record for 1904 would replace it, and would also move every depth in zone 9.

## Zone 3 — Street crowns where the period's houses confirm them (Prairie Avenue, 18th Street to 2017 Prairie)

The crown of Prairie Avenue at 18th Street, midway to 20th and midway to 21st, read off the 1 m
bare-earth model (2017 acquisition): **Z +14.21, +15.08, +15.10 ft.** The walks before the
Glessner House (+14.46, and +14.09 on 18th Street), the Kimball House (+14.27), 1811 (+14.50),
1919 (+15.11), 2013 (+15.11) and 2017 Prairie (+15.16) read within 0.18 ft of the crown before
them (`terrain_spec.json` § evidence_limit.confirmed_reach). The confirmed reach is the stretch
those walks span, 25 m either side: N −3190.5 to N −3570.0. 2020 Calumet's walk (+15.78) is a
block east, on a street whose modern crown is refused, and confirms nothing here. **Inferred** for 1904: the houses stand at their built grade, and the Glessner House's
1965 measured elevation puts its front sill 0.74 ft over the walk before it (library measurement
row `pa-glessner-habs-sheet-6`, from `habs_glessner_house_il_1015`), which is a house built to its
street. One reading is refused: the ground before 1900 Prairie reads +16.74, 1.6–2.3 ft over its
neighbours, because the sample fell on the house's raised front terrace. **1888:** the same — the
Glessner and Kimball houses were built to this grade by 1887.

## Zone 4 — Street crowns with nothing standing to confirm them

Prairie Avenue at 16th Street and midway to 18th (+12.29, +12.63 ft) and at 21st Street (+14.74,
40 m south of the confirmed reach); Indiana Avenue at 16th, 18th
and 21st (+13.22, +14.62, +14.70); Michigan Avenue at 16th, 18th and 21st (+12.58, +13.24,
+13.09). Each is on a corridor the 1911 sheets draw, and each is the modern crown carried back
with no building of the period to say it has not moved. **Reconstructed**, bounded by the
confirmed crowns of zone 3 (within 2.8 ft) and by benchmark 289. **Refused:** Calumet Avenue
(re-laid north of 21st Street, and 7.5 m off sheet 35's line at 21st) and both Cermak Road
crossings (a widened, divided carriageway about 10 m south of the Twenty-Second Street the 1911
sheet draws). **1888:** Indiana and Michigan were built up by then; no evidence moves these either
way.

## Zone 5 — The graded lots

The blocks between the streets stand at the grade of the streets about them — the practice that
the Glessner sill-to-walk figure shows at one house. How the grade runs between two crowns is
recorded nowhere, so the spec interpolates by inverse distance (power 2) over the crowns of zones 3
and 4, which cannot leave their range (Z +12.3 to +15.1). **Reconstructed.**

## Zone 6 — The post-fire fill, and why the two epochs are not offsets of one another

The fill is the difference between the 1904 grade and the 1835 surface at the same point. Along
Prairie Avenue it runs **2.9 ft at 16th Street to 5.7 ft between 18th and 21st**; at Indiana and
Michigan, 3.7–5.2 ft. It is stated as a difference and never used to derive one surface from the
other: the 1835 surface here is itself conjectural (the e1834 spec's `evidence_limit` at
N −2149.4, below which that ground is one row carried south at +9.4 ft), while the 1904 grade is a
set of crowns laid by ordinance and read off standing houses. **Inferred** (a difference of two
committed surfaces). The terrain dossier (§ 1.4) documents downtown raises of 4–14 ft in the
1850s–60s; the reach here was built up later and less, which is what these figures say.

## Zone 7 — The Illinois Central embankment

The sheets draw the right-of-way as tracks on dry ground with the lake washed against its east
edge (sheets 20 and 28). No level is held for the track bed or for the embankment's face. The bed
is held at the grade of the ground beside it — the least claim available: no cut, no bank — and
the lakeward face falls at 1 in 1.5, a stone breakwater's slope, from that grade to the water.
**Reconstructed.** A section of the Illinois Central's lakeshore works of the period would
replace both figures.

## Zone 8 — The made ground of 1886–1911

Between the 1886 and the 1911 water's edge is a strip 14–21 m wide that was lake when Robinson's
plate was drawn and ground when Sanborn's was (T-1250). In 1904 the scene line (L287) puts it on the
land side. **Inferred** as made ground; its date inside 1886–1911 is not known. **1888:** most of it
would be water.

## Zone 9 — The lake bed off the right-of-way

No sounding has been found. The bed falls from the breakwater's toe toward −8 ft with a 40 m e-fold
— the shape the 1835 spec's `channel_profile` uses for its lake shelf, at a smaller scale. Under
water and seen only from the shore. **Reconstructed.**

## Zone 10 — Where the original prairie still shows

Nowhere. Every block in the box is platted and built on, or kept as a yard, on the 1911 sheets, and
the graded crowns stand 2.9–5.7 ft over the 1835 surface. **Inferred.** (The ticket asked for this
zone "where it still shows"; the finding is that in 1904 it does not.)

## Zone 11 — The surface texture

Two octaves of value noise at ±0.05 ft — half the 1835 ground's ±0.10 — because graded, built-over
ground is flatter than prairie. A texture so the ground reads as ground, not a claim.
**Reconstructed.**

## Zone 12 — The evidence limit

Derived here, not inherited. **Grade:** south of 21st Street (half a block — 50 m — past the last used crown,
N −3659.9) the grade is held from 21st Street, because both Cermak crossings are refused. **Shore:**
south of the scene line's segment F (N −3365.2) no sheet bounds the lake edge at all (L287).
**Confirmed reach:** Prairie Avenue from the Glessner House's walk to 2017 Prairie is where zone 3
applies; outside it the crowns are zone 4's.
