# Extending the ground east to the harbour — the box, the cell, and what the bar is worth

**Built:** 2026-08-11 · **Epoch:** `e1834_harbor_cut` · **Extent:** local E −320 … +1700,
N −400 … +400 — 2 020 × 800 m. Supersedes the 640 m square in `terrain_forks.md`, which
remains the memo for how the forks half was built.

This is ROADMAP § S2e parcel (b). Parcel (a) traced the shore, the 1834 cut, the old
southward channel and the sand bar and stopped there, on purpose: it wrote its own note
saying the file was "the evidence, not the ground". This slice makes it ground.

Re-derivable end to end:

```
python3 generators/terrain_gen.py                 # the heightfield (no Blender needed)
blender -b -noaudio --factory-startup \
  --python generators/terrain_gen.py -- --glb     # + the ground and water meshes
```

---

## 1. Why the ground had to move

Measured on the morning of 2026-08-11, before any of this: of the structure records then in
`data/structures/`, **twenty stood outside the modelled terrain box** — South Water Street,
Lake Street, the whole business district, the Dearborn Street bridge, the north-bank agency
houses and the Beaubien homestead. `tools/heightfield.py`'s `covers()` had just been written
to stop the ground-contact gate reporting a perfect landing for a building 832 m past the edge
of the world, so the dataset was correctly describing twenty buildings standing over nothing.

That is not a rendering artefact. It is the commercial heart of 1835 Chicago outside the
model.

## 2. The box, and where each of its four numbers comes from

Everything here is a measurement or a stated limit, not a round figure.

| edge | value | what fixes it |
|---|---|---|
| west | **−320** | unchanged; the forks tracing window |
| east | **+1700** | § 2.1 below |
| south | **−400** | the South Branch's traced water ends at N −404.5, where the forks tracing window closes |
| north | **+400** | the North Branch's traced water ends at N +401.6, same reason |

**The north and south edges are capped by evidence, not by cost.** Below N −404.5 the South
Branch is simply not traced, and a box reaching further south would draw open prairie across a
river that is still there. Standing 4.5 m inside that limit is the largest honest box, and it
happens to be worth having: it holds the sand bar down to N −400 of its traced −436, and it
puts 80 m of land north of the 1834 cut's north bank at N +321, so the harbour has a north
shore instead of an edge.

ROADMAP § S2e proposed "roughly 2.0 km × 0.7 km". The east–west figure survives; the
north–south one is 800 m rather than 700, for the two reasons above, and both directions are
now limited by the trace rather than by an estimate.

**What the box truncates, stated rather than hidden:** the bar's southern hook below N −400
(34 m of a 660 m island), the old southward channel below N −400 and therefore the natural
outlet at about Madison Street (local N −525, from the State & Madison ground-control point),
and the lake shore north of N +400. All three stay in `shoreline.geojson` and
`data/traces/vectors/wright_1834_east.json` as evidence. None is modelled ground.

### 2.1 The eastern limit, re-derived — and NOT from the piers

ROADMAP § S2e reached +1700 partly on the strength of "north pier, outer end E +1544,
N +178", read from `wright_1834_east.json`'s `harbour_north_pier`. **That reading is wrong and
the figure with it.** `docs/RESEARCH/north_pier.md` § 2 went back to the raster and found that
the two committed pixels are not both on the north line — one sits mid-channel and the other
lands near the *south* line — so the committed feature runs from mid-channel to the other pier
and comes out at 107° where the north line runs at 103.36°. The corrected root is
**E +1243.5 / N +311.9**.

The same memo settles something that matters more for this box. **Wright drew the harbour
works as AUTHORISED, not as built:** both drafted lines run about 1 165 ft, longer than the
north pier was in 1834 and longer than the south pier ever was before 1837. So the drafted
seaward ends at E +1588.8 and +1561.2 are an authorisation drawing and cannot set anything.

Re-derived from what is left:

| easternmost … | local E | source |
|---|---|---|
| traced LAND — the sand bar's east edge | +1497.5 | `shoreline.geojson`, ±30 m |
| the 1835 north pier's head (900 ft adopted, ±30 m band) | **+1510** | `north_pier.md` §§ 2, 4 |
| traced WATER — the tracing window, not a shore | +1573.6 | `shoreline.geojson` |
| *(drafted pier head — an authorisation, unusable)* | *+1588.8* | — |

**+1700** clears the pier head by 190 m and the high end of its error band by 160 m; clears the
tracing window by 126 m, so the entire traced water body is inside the box; and stands 203 m
(665 ft) off the bar, inside dossier zone 30's "−10 ft at 600–1 000 ft offshore" — the box ends
about where the lake reaches the depth the dossier gives it. Three independent reasons, none of
them the drafted piers.

## 3. One cell size, and the argument for not being clever

S2e suggested a coarser cell east of the built blocks, "where the evidence does not support
2.5 m detail anyway". The field ships at a **uniform 2.5 m**. Four reasons, in the order they
weigh:

1. **The built blocks are east.** That is the whole finding this parcel started from: twenty
   of the records then held stood between E +347 and +1090. "East of the built blocks" now
   means the reservation, the old channel and the bar, not the town.
2. **The waterline is not a texture.** This generator's central design is that the ground's
   Z = 0 contour *is* the drawn waterline — the water needs no shoreline geometry because it is
   the plane Z = 0 and the terrain occludes it. Coarsening the cell quantises the shoreline, in
   exactly the quadrant whose shoreline is the most-cited line on the sheet and the one this
   project has spent two parcels tracing.
3. **The saving is not worth the contract.** A 5 m cell east of E +1100 would save about
   150 KB. Three readers share one grid definition — `renderers/web/js/terrain.js`,
   `tools/heightfield.py` and this generator's own mesh builder — and every one of them assumes
   a single uniform `origin_e / origin_n / cell_m / cols / rows`. The published tree is 13.2 MB
   of a 25 MB budget. Breaking a three-reader contract for 1 % of a budget we are half into is
   the wrong trade.
4. **It would not have saved much geometry either, and this was measured rather than assumed.**
   The box grew 3.94× in area (0.410 → 1.616 km²) and the decimated ground mesh grew 3.05×
   (44 347 → 135 249 triangles, 890 KB → 3.52 MB). Triangle count is set by the planar-dissolve
   pass, not by the sample count, so a flat plain costs little whatever the cell is.

The dossier asks for **5–10 ft** cells. 2.5 m is 8.2 ft and inside that; 5 m is 16.4 ft and
outside it. A coarser east would have put the only part of the field outside the dossier's own
recommendation under the only part of the town the dossier describes in feet.

Cost as shipped: 809 × 321 = **259 689 samples, 519 378 bytes** (507 KB), against 66 049 and
132 KB before.

## 4. What was added to the zone table

The generator's architecture did not change: everything is still a function of the signed
distance from the traced waterline, and land is still assigned to a division by which traced
bank it is nearest to. Three things were generalised, each because the east demanded it.

**(a) Levels became profiles in E.** The town's ground does not vary with distance from the
river; it varies west-to-east. §1.15's one usable sentence — "east of State Street … from nine
to ten feet above the surface of the lake, whereas to the west of State Street … only two to
three feet above the river" — is a statement about a north-south line. So `near_ft` and
`far_ft` became `crest_profile` and `plain_profile`, piecewise-linear tables in local E, and
the bank face width became one too. A constant profile reproduces the old scalar exactly, which
is how the forks were left alone (§ 6).

**State Street is not estimated.** Two of the eight ground-control points that fix this
project's datum sit on it: State & Madison, the PLSS section corner, at local **E +837.6**, and
Wolcott & Ohio — Wolcott being today's North State Street — at **E +822.5**. The break-of-slope
band is centred on E +830 and runs +780 to +880: 100 m, or 328 ft, inside dossier zone 10's
200–400 ft transition, falling 4.7 ft where the zone states 5–6 ft per 300 ft.

**(b) Islands.** The sand bar is land the water goes round — the interior ring of the harbour
polygon — so water membership had to understand holes, and the bar got its own crest and its
own beach face. § 5 is about its height.

**(c) The waterline is the shore RUNS, never the polygon boundaries.** This is a correctness
fix the extension forced. Both water polygons close across their tracing windows — the forks at
E +390, the harbour at E +314, and again out in the lake. A window edge is where the tracing
stopped, not a bank. Measuring shore distance to the polygon boundary would have raised a bank
across open water in three places. Distance is now taken to the five traced shore runs and the
island rings, which between them are the whole real waterline and nothing else.

Zones now built that were listed as "not modelled in this box" before:

| zone | what |
|---|---|
| 3 | lakeshore sand-ridge belt, +9.4 to +9.5 ft crest, on both sides of the river |
| 4 | beach face — the bank face widens east to 20–25 m so the shore slope stays 1:8 to 1:10 |
| 6 | the Fort Dearborn mound, apex near +11.0 ft |
| 7 | the sand bar (§ 5) |
| 8 | South Division plain east of State, +7.6 → +9.4 ft |
| 10 | the State Street break-of-slope |
| 12 | Swearingen's measured bank crests at the fort — 8 ft south, 6 ft north |
| 23 | the 1834 cut, bed −5 ft |
| 26 | the old southward channel, bed −2.5 ft |
| 30 | the offshore lake shelf |

Deliberately still absent, with reasons, in the spec's `not_modelled_in_this_box`: zone 5 (the
"white sand hills", no source places a single one), zones 14–17 (the slough, the two ponds and
the Wells Street marsh are all *inside* the box now and belong to S2e parcel (c) — cutting a
conjectural channel through the block where the business district stands is a decision that
should be made with the other watercourses, not smuggled in with the ground), zone 27, zone 28
(adding a year of accretion on top of a traced 1834 shore is editing the trace, not reading it)
and zone 29.

## 5. The bar's height is chosen, and this is the argument

**No source gives the elevation of the sand bar at any date.** Its planform is traced and
carries the sheet's ±20 m like everything else; its height is a number someone has to pick, and
S2e said so: "its height is a spec argument to be made in the open, not a number to pick."

Dossier zone 7 offers "+4 to +8 ft crest" for the sand tongue and tags the heights *inferred* —
that range is itself a reading of the landform type, not a measurement. **The low end is
taken, +4.0 ft**, for four reasons that can be argued with:

1. Fort Dearborn soldiers cut ditches through this bar repeatedly between 1816 and 1828 with
   hand tools, and a February 1834 storm breached it outright. A feature a work party trenches
   and one storm overtops is a low one.
2. CPL's reading of the 1839 Fort Dearborn Addition plat is that the ground east of Michigan
   Avenue "at best was probably a low sandbar".
3. The mid-1830s fall in a Lake Michigan high-water phase, so freeboard was small.
4. **The direction of the error matters.** Eight feet of sand would hide the harbour works
   behind a ridge and turn the 1834 cut into a canyon. A bar a foot too low is the less
   misleading of the two available mistakes.

It is emitted **conjectural** in the confidence channel — the only land surface in the box
that is — so a visitor sees the bar dithered. Its shape is evidence; its height is not. That is
precisely the distinction the confidence view exists to draw, and this is the clearest case of
it in the dataset.

## 6. What did NOT move, checked rather than asserted

The forks profiles are held constant out to E +390 (north, west) and +780 (south) so that
extending the box east could not move ground that already had buildings standing on it.
Verified against the pre-change field cell by cell:

- **Land is bit-identical.** Max |Δ| over the 54 359 land cells of the old 640 m box: **0.0000 m**.
- **No cell changed side of the waterline.** Zero.
- Everything that changed is under water: 11 003 sub-water cells, max **0.335 m**, from the new
  fort-bend, cut, old-channel and lake anchors slightly re-weighting the inverse-distance blend
  that sets the channel bed. The deepest point of the box moved from −11.7 ft to −17.4 ft
  because Swearingen's 18 ft pool at the fort bend is now inside it.

## 7. The flatness rule still holds, and the dossier contradicts itself once

`gradient_audit` reports **plain_block_max 0.468 ft per 300 ft**, against the dossier's 0.5 —
**the same number the 640 m field reported**, and at the same place: a west-prairie chord at
E −200 / N −270. The 1.6 km of new ground contributes nothing to the worst case.

Getting there took one real adjustment and one recorded disagreement.

- **The adjustment.** The North Division's first draft rose from +3.6/+4.6 ft to +5.0/+6.0 by
  E +880. Along a chord where the distance-from-river ramp is also changing — the ground north
  of the main stem, where the north-side slough is the nearest water — the two effects add, and
  the audit read 0.532. Spreading the same rise to E +1210 brings it to 0.468. The end points
  are unchanged and still inside zone 19's "+4 to +7"; only the rate moved, and it moved
  because the audit said so.
- **The disagreement.** Dossier modelling rule 1 exempts "zones 3–7 and the fort mound" from
  the 0.5 ft rule. It does not list **zone 10**, the State Street break-of-slope — which the
  dossier itself specifies as "a drop of ~5–6 ft over 300 ft (≈2 % grade)". Zone 10 cannot obey
  rule 1 while doing what zone 10 says. Read as an omission from rule 1's list rather than a
  contradiction in the ground, and zone 10 is added to the exemption **by name** in the spec's
  `relief_bands`, with its own worst gradient reported in the audit rather than excused.

Every exemption is now declared in the spec and reported individually — bank faces, marsh
strip, swales, the State Street break, the two sand-ridge bands, the bar and the fort mound —
so no relief is quietly excused by a mask nobody can see.

## 8. Where Wright and the secondary sources disagree about the coast

The dossier § 4, following CPL and the McClendon shoreline map, says the pre-fill Lake Michigan
shore "ran approximately along modern Michigan Avenue" — local **E ≈ +1127**, using the same
modern-successor scoping the Fort Dearborn cross-check uses.

**Wright 1834 does not put it there.** The traced mainland shore behind the spit stands at
E +1245…+1257, and the lake shore north of the harbour at E +1331…+1365 — **120 to 240 m east**
of the Michigan Avenue line, far outside the ±20–25 m the georeference carries.

Recorded rather than averaged. **Wright is taken**, for three reasons: it is the primary survey
and the master warping raster, S2e names it as the source that drives the shore, and the two
statements are not quite about the same thing — south of the river mouth the *open-lake* coast
is the bar's east edge and the E +1245 line is the mainland bank behind a spit, while north of
the mouth a shore reading in 1834 is already downstream of a year of accretion against a new
pier. The gap is real and is not explained away by any of that; it is left on the record as the
honest ceiling on where the 1835 coast was.

A second, smaller one: the old channel measures about 90 m wide on the trace against the
dossier's 80–150 ft (24–46 m) for zone 26. A wash boundary on a plat and a narrative estimate,
neither a survey.

## 9. What this parcel hands to the next ones

- **Ground contact.** Every structure in `data/structures/` is now inside the modelled box —
  75 positioned phases at the time of writing, **zero outside**. Nineteen of the twenty
  stranded records land; the twentieth is the Dearborn Street bridge, whose abutments now have
  ground under them and whose deck stands 2.24 m above it. The eight phases that still stand
  off the ground all measure `approach_not_modelled`: four bridges and piers whose decks are
  over water by construction, and two Fort Dearborn records whose outlines reach the river
  bank.
- **`pier_crib` needs a one-ended contact mode.** `north_pier.md` § 7 predicted this: a pier
  lands at its root and never at its head, and `GROUND_CONTACT = "ends"` measures both. With
  the lake now modelled, the north pier's head is measured against a bed 1.8 m under water and
  reports a 3.29 m gap that is not a finding about anything.
- **The slough bridge has ground and no slough.** `slough_log_bridge` sits at E +805, in the
  State Street break-of-slope, crossing dossier zone 14 — which parcel (c) owns. Until then the
  bridge crosses dry rising ground.
- **Flora and fauna.** `z08_lakeshore` and `z09_sand_prairie` were written against a box that
  stopped at E +320 and declared themselves not plantable. They have modelled ground now and
  say so. **Not fixed here:** at priorities 12 and 11 they lose everywhere to
  `z02_mesic_prairie` at 22, whose 1.18–3.0 m elevation band covers the whole sand belt, so the
  beach, the ridge and the bar are currently planted as mesic prairie. The priorities were set
  when nothing east of E +320 had ground under it and the question could not arise.
- **L17's skirt** shrinks by most of its area east; see the entry's own revision.
