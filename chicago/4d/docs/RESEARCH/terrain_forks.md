# Terrain and hydrology at the forks — how the numbers were chosen

**Built:** 2026-08-10 · **Epoch:** `e1834_harbor_cut` · **Extent:** a 640 m square centred on
the datum origin at Wolf Point.

Everything here is downstream of `docs/research/01-terrain-hydrology.md`, which is the
specification. This memo records what was *implemented*, where the sources disagreed, which
reading was taken and why, and what in the dossier turned out to be unusable when someone tried
to build from it. It exists because `AGENTS.md` requires the disagreement to be written down
rather than silently resolved.

Re-derivable end to end:

```
python3 tools/trace_river.py                      # the river geometry, from the map
python3 generators/terrain_gen.py                 # the heightfield (no Blender needed)
blender -b -noaudio --factory-startup \
  --python generators/terrain_gen.py -- --glb     # + the ground and water meshes
```

---

## 1. Where the river geometry came from

**It is a trace, not a reconstruction.** `tools/trace_river.py` segments the Chicago River
channel off the Boston Public Library master scan of **Wright 1834** (IIIF
`commonwealth:js957744g`, region 868,1252 1120×1120, sha256 recorded in the GeoJSON) and
transforms it to EPSG:26916 through the *same* least-squares affine that fixed the datum
(8 GCPs, RMS 17.5 m — `data/traces/gcp/wright_1834_gcps.json`). No modern centreline was used
for the channel, and no vertex was placed by hand.

Wright draws the river the way period plats do: a black bank line with a **grey wash band on the
water side of it**, the middle of the channel left as bare paper. So the water is not one colour
to threshold; it is the region *between* two shaded bands. The trace separates the grey bank
wash from the pink/green/blue/yellow ward washes by its lack of hue departure from the local
paper (not by luminance), closes across the unshaded mid-channel, and traces the boundary.

| output | form | confidence |
|---|---|---|
| `river.geojson` → `chicago_river_forks` | water polygon, 70 vertices | `inferred` — planform traced from a tier-1 survey, but a cadastral plat is not a hydrographic one |
| `river.geojson` → three bank runs | LineStrings, one per division shore | `inferred`, same reason |
| `hydrology.geojson` → `north_side_slough` | **centreline**, 45 points, 7.1 m drafted width | `attested` for existence and course; `inferred` for width; `reconstructed` for depth (§1.2) |

The three bank runs are named for the divisions they bound — `north_division_shore`,
`south_division_shore`, `west_division_shore` — because the divisions *were* defined by the
river, and deriving the land zones from the bank runs (which `terrain_gen.py` does, by nearest
run) means the zone boundaries cannot drift out of step with the channel if the trace is ever
refit.

Every vertex carries the georeferencing reality: **±20 m**. Both 1834 sheets are anisotropically
stretched (Wright 3.7%), so a global affine cannot do better locally, and the two sheets disagree
about the forks by 58 m.

### 1.2 The slough's two grades, ruled on the evidence (T-0687)

For a month the committed `hydrology.geojson` and the generator that says it wrote it disagreed
about two provenance grades, and nothing could see it. `trace_river.py --check` reproduced
`river.geojson` byte for byte and reported `DIFF` on the hydrology file; the geometry was
identical to the millimetre and only two strings differed. T-0687 settled which side is right,
on the evidence rather than on which was newer.

**Width — `inferred`.** `drafted_width_m` is not an assumption: it is twice the interior
distance transform of the surviving wash fragments, read off this same BPL scan at 0.7115 m per
map pixel. That is reasoning from evidence about *this particular watercourse*, which is what
`inferred` means, and it is the same rung the water polygon and the three bank runs traced from
the same wash already sit on — a width measured inside a polygon cannot honestly be graded below
the polygon. What it measures is the width **as drafted on a cadastral plat**, not a sounded
channel, and the note in the file says so.

**Depth — `reconstructed`.** No source gives a depth for this watercourse or any other on the
town site. One foot is chosen: the shallowest value that still reads as standing water for
something Wright draws as a continuous channel rather than as marsh. That is invention within
bounds, which is the definition of `reconstructed` — this project's bottom tier since the
vocabulary rename, and its word for what the note calls conjectural. `conjectural` is not a
value in `CONFIDENCE` (`tools/validate.py`: `attested`, `inferred`, `reconstructed`); it
survives here and in `terrain_spec.json` as prose and as the name of a render channel, not as a
grade. Grading the depth `conjectural` in a `*_confidence` key was writing a word the vocabulary
does not have.

So the committed file was right on both counts and the generator had drifted; the fix is in
`tools/trace_river.py`, no committed grade moved, and no vertex moved — which also means no
Blender bake, since a `*_confidence` value *is* in the terrain's staleness hash and a `note` is
not.

**How the drift happened**, because the mechanism will recur. The file was born
`width: inferred` / `depth: conjectural` under the old `documented`/`derived`/`inferred`
vocabulary, in which `inferred` was the BOTTOM tier. A hand pass over the JSON
(`WIP: the confidence vocabulary rename (K16)`) then edited this generated file directly,
mapping the width up to `derived` and mapping the off-vocabulary `conjectural` onto `inferred`;
the mechanical rename (`tools/rename_confidence_vocab.py`, which only ever touched `data/`)
carried both one step further to `inferred` and `reconstructed`. The generator, being Python,
was never in that pass and was hand-corrected separately and differently. **A generated file
that gets hand-edited during a migration is the whole fault**, and it is exactly what the file's
own `_doc` forbids.

**The gate.** The reproduction that would have caught this on the day cannot be a per-commit
gate: it re-traces the scan, so it needs numpy, scipy and Pillow — which the agent sandbox does
not carry — and it fetches a 1,120 px IIIF region from Boston Public Library over the network.
A gate that installs a scientific stack and reaches the internet gets skipped. So the half that
costs nothing is gated instead: `trace_river.py --check-properties` compares every LITERAL the
two files carry — envelope, `_doc`, feature ids, kinds, names, grades, sources, the whole note
as a template around its one measured number, and the static provenance — against the module
constants the generator writes them from, offline, in milliseconds. `tools/check.sh` runs it.
It does **not** see a coordinate, a `drafted_width_m`, an affine RMS or the region sha256; those
still need the deliberate `--check` re-run, and that is the residual cost, stated rather than
hidden.

### 1.1 The slough is a centreline, and that is a finding

Wright draws a narrow winding watercourse running north out of the main stem, across Kinzie
Street, ending at Michigan Street. **It is not in the dossier's 30-zone table** — the dossier
knows of "three sloughs off the Main Branch" on the 1830 Thompson plat (§5) but does not place
any of them. This one is drawn on the master geometry source, 205 m east and 130 m north of the
origin, squarely inside the modelled box.

Its wash survives in only **five fragments** — the pink Kinzie ward band and the lot lines it
crosses erase the rest — so tracing a boundary would have produced a polygon whose shape was
mostly morphological invention wearing the authority of a trace. It is published as a
centreline with a measured drafted width instead, and the generator buffers it. That is the
honest form of what the map actually supports.

---

## 2. Where the sources disagreed, and what was done about it

### 2.1 Channel width: the map is wider than the dossier's estimate

| | width |
|---|---|
| Dossier zone 22, at the fort reach, **documented** (Swearingen 1803) | ~90 ft |
| Dossier zone 22, at the forks, **inferred** | 150–200 ft |
| **Traced off Wright 1834**, north branch | 239 ft (72.9 m) |
| **Traced off Wright 1834**, main stem | 229 ft (69.7 m) |
| **Traced off Wright 1834**, south branch | 188 ft (57.3 m) |

The drafted channel is 15–20% wider than the top of the dossier's inferred range for two of the
three reaches. **The trace was kept.** Reasoning:

1. The dossier's forks figure is explicitly *inferred* — an interpolation upward from a
   measurement taken 1.2 miles downstream. The map is the only observation of the channel *at
   the forks* this project holds, made by a surveyor a year before the scene date.
2. Narrowing the channel to hit an inferred number would replace an observation with a guess,
   which is exactly backwards.
3. The disagreement is about 10 m per bank. Every vertex already carries ±20 m of georeferencing
   uncertainty, so the correction would be smaller than the noise it was applied to.

Recorded on the water feature as `drafted_width_m` so the next reader sees the number rather
than having to re-measure it. **What would settle it:** a period sounding or a wharf-line survey
at the forks; the Graham 1857–58 hydrographic sheets are downstream but establish the drafting
conventions.

### 2.2 The datum origin sits on land, about 20 m from the water

The datum origin — `forks_pixel_wright` (1428, 1812), read by hand as "where the three channel
midlines meet" — falls, on this trace, on the **southern tip of the North Division wedge**,
about 20 m north-west of open water and roughly 55 m from the centre of the confluence basin.

This is not a defect and nothing was changed. It is inside the ±20 m working uncertainty, and it
**independently corroborates the cross-check already recorded in
`docs/RESEARCH/datum_derivation.md`**: the modern OSM waterway-junction node lies 39.4 m *south*
of the Wright point. Two independent methods now put the true junction south of the recorded
origin. If the datum is ever re-derived, that is the direction it should move.

One practical consequence: the scene's `forks` camera anchor was a placeholder at (−20, −30),
which the traced channel puts **in the middle of the South Branch**. It has been moved to
(−100, −28) yaw 75° — on the west bank at Wolf Point, which is what the name meant, "looking
directly down the main channel" (chicagology_prefire273).

### 2.3 Zone 13 (bank crest +2 to +4 ft) versus zone 11 (marshy shore +0.5 to +2.0 ft)

These cannot both describe the same stretch of bank: a crest at +2 to +4 ft is not a place where
"land and water mingled". Read as describing **different stretches**, which is what the sources
support — zone 11's language is specifically about the **South Division** ("a strip along the
river shore that was still more marshy"), while zone 13 is a general reconciliation of the plain
with the measured banks at the fort.

Implemented as: the marshy strip is applied to the **South Division shore only**, 30 m (98 ft)
wide at +1.25 ft, blending to the +2.4 ft plain over its outer 18 m. The north and west shores
get no marsh strip and their banks rise straight to +3.6 and +3.2 ft, which is zone 13's range.
So both zones are realised, in the places their sources put them.

### 2.4 Zone 19 (North Division +4 to +7 ft) versus zone 13 at the same bank

Same shape of problem: the north bank at the forks has to be both "+2 to +4" (zone 13) and part
of a division at "+4 to +7" (zone 19). Resolved as a **profile rather than a level**: the bank
crest is 3.6 ft, rising to 4.6 ft at 300 m inland. Zone 13 is satisfied at the bank, zone 19
from a little way back, and the gradient between them is 0.31 ft across a 300 ft chord — inside
the dossier's own flatness rule.

The same treatment fixes the West Division (zone 18, +3 to +6 ft, against zone 13 at the point):
3.2 ft at the bank rising to 4.3 ft at 300 m.

### 2.5 Channel bed: the 18 ft sounding is at the fort and did not travel

Zone 20 gives −12 to −18 ft for the main stem, with the −18 ft pool at the fort bend. The
**shallow end** is used here because the forks are the upstream end of that reach, and
Swearingen's "upwards of 18 feet" is a measurement 1.2 miles downstream. The branches take the
midpoint of zone 21's inferred −6 to −10 ft.

The channel *cross-section* is a smooth exponential approach to the bed and carries **no
evidence at all** — no pre-dredging cross-section of the river at the forks exists. It is under
water, it is marked `conjectural` in the confidence channel, and it is there so the ground
surface reaches Z = 0 exactly at the traced bank line.

---

## 3. What the terrain actually contains

Elevations in feet above the summer-1835 water surface, which is Z = 0 (`data/datum.json`).
Measured out of the built heightfield, not copied from the spec.

| where | built value | dossier zone | zone's range | tag |
|---|---|---|---|---|
| water surface | 0.00 ft, flat | 1 | 0.00 | `documented` |
| South Division plain, 250 m back | **+2.71 ft** | 9 | +2 to +3 | `inferred` |
| South Division marshy shore strip | **+1.25 ft** over 30 m | 11 | +0.5 to +2.0 | `inferred` |
| South Division bank crest | **+2.4 ft** | 13 | +2 to +4 | `inferred` |
| North Division bank crest → 300 m inland | **+3.6 → +4.6 ft** | 13 / 19 | +2 to +4 / +4 to +7 | `inferred` |
| West Division bank at Wolf Point → 300 m | **+3.2 → +4.3 ft** | 13 / 18 | +2 to +4 / +3 to +6 | `inferred` |
| west-prairie swales | **−0.75 / −0.6 ft** below the prairie | 18 | 1–2 ft swales | `conjectural` |
| main-stem bed at the forks | **−11.7 ft** at the deepest | 20 | −12 to −18 | `conjectural` |
| branch beds | **−7.4 ft** typical | 21 | −6 to −10 | `conjectural` |
| north-side slough bed | **−1.0 ft** | *(not in the table)* | — | `conjectural` |

**Total relief inside the box: 4.30 ft of land, 16.0 ft including the channel floor.** The
dossier's cap is "no relief greater than ~+14 ft above lake anywhere inside downtown"; the
highest ground here is +4.3 ft.

### Flatness, audited rather than asserted

`generators/terrain_gen.py` checks the dossier's own modelling rule 1 — *outside the zones that
earn relief, hold local gradients under 0.5 ft per 300-ft block* — and prints the result on
every run. It measures the **fall across a 300 ft chord**, which is what the rule is about
(the drainage grade of the plain), not the cell-to-cell derivative, which on any real ground is
dominated by surface texture. Excluded: water, land within 48 m of a waterline, and the swales.

```
plain max 0.468 ft per 300 ft (mean 0.149) — PASS
plain cell roughness max 2.79   (the micro-relief, see below)
shore and swales max 95.4       (the bank faces, which earn it)
```

The division `far_ft` values were chosen inside their attested ranges to leave headroom under
that rule — that is a choice, and it is why they sit at the low end of zones 18 and 19 rather
than the middle.

### Micro-relief

±0.10 ft (30 mm) of two-octave value noise on land, at 70 m and 38 m wavelengths. Below the
0.25 ft the dossier asks the heightmap to be *quantised* at, and far below the resolution of any
statement in the record. It exists so a surface the sources describe as dead flat still reads as
ground rather than as a rendering error. **It is conjectural, and it is not reflected in the
`_CONFIDENCE` channel** — the channel carries the zone's tag, because that is the claim being
made. Recorded as a liberty (L7).

### Vertical exaggeration is 1.0, in the data and in the renderer

The dossier recommends "4–8× vertical exaggeration for legibility". **That recommendation was
not followed**, because `docs/EPOCHS.md` and `docs/LIBERTIES.md` L3 both require exaggeration to
default off and no zone to be invented to make the terrain interesting. The dossier and the
project's own standards contradict each other here; the standards win. Nothing in the pipeline
scales Z, and `terrain_spec.json` records `"exaggeration": 1.0`.

---

## 4. Unusable or self-contradictory in the dossier, found by building from it

1. **The 4–8× vertical-exaggeration recommendation contradicts the project's own honesty rules**
   (§3 above). It is the only place the dossier asks for something the repo forbids.
2. **Zones 11 and 13 cannot both apply to the same bank** (§2.3). Resolvable, but the table does
   not say so.
3. **Zones 13 and 19 overlap awkwardly at the north bank** (§2.4) — a bank crest below the floor
   of the division it belongs to. Resolvable as a profile, not as two levels.
4. **Zone 9 restates §1.3 with a wider range than §1.3 gives** — the prose says "two to three
   feet above the river", the table says "+2.0 to +3.5". The prose figure was used.
5. **No zone covers the sloughs off the Main Branch**, although §5 knows they exist and the
   master map draws one inside the modelled box (§1.1). The table is a lakefront-and-Loop
   inventory; the forks quadrant is thinner than the rest.
6. **Zone 22 gives no width for the North Branch at all** — only the main stem and "the forks".
   The trace supplies one.
7. **No bank profile anywhere.** Zones give crest heights but never a bank *face* — how far
   horizontally the ground takes to rise, or what shape it rises in. The 6 m face used here is
   `conjectural` and is the single largest un-sourced geometric assumption in the build. Its
   *shape* is an ease-out quadratic (steepest at the waterline, flattening into the plain) for
   two reasons: a natural alluvial bank is undercut by the flow, and — the reason that actually
   decided it — a profile that leaves the ground flat for the first metre inland makes the
   surface's Z = 0 contour badly conditioned, and that contour IS the drawn waterline, so the
   shoreline came out visibly snapped to the 2.5 m grid until the profile was changed.
8. `chicagoarchitecturehistory.com` §1.15 — the source of the two best elevation figures in the
   whole dossier — **gives no citation for them**, and was not re-fetched at its locator by this
   parcel. That is why every land elevation here is `inferred` and none is `documented`. The
   source record (`data/sources/chicago_architecture_history_115.json`) says so in its own note.
9. The epoch registry declares a `shoreline.geojson` layer. **It is not written**: the 1835 lake
   shore runs along the modern Michigan Avenue line, about 1.4 km east of this box. It belongs
   to whoever builds the harbour quadrant.

## 5. What would improve this

- A period sounding or wharf-line survey at the forks (§2.1).
- Andreas vol. 1 or Hill's *The Chicago River* at page-image level for a measured bank height at
  Wolf Point — the dossier names both as the best places to look and neither was reached.
- The 1830 Thompson plat georeferenced, to place the other two Main Branch sloughs and the
  "bayou near Wolf Point" (§1.1).
- A thin-plate-spline warp of Wright 1834 against many more control points, which would cut the
  ±20 m and might move the datum origin south onto the water (§2.2).
