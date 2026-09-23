# Handoff — K6 and K11, 2026-08-13

Written to a file rather than applied, because this session was told not to edit
`docs/ROADMAP.md`, `docs/STATUS.md` or `docs/LIBERTIES.md`. Everything below is proposed
text for those three, plus the things a later parcel should pick up.

---

## Proposed `docs/ROADMAP.md` edits

**K6 — mark DONE**, replacing the item body with:

> ### K6 — The river bulge at Clark Street · **DONE 2026-08-13**
> Not paper stretch and not a mis-traced stream: the traced south bank had been walked round
> the **outline capital G of "CHICAGO RIVER"**, which Wright letters across the channel, joined
> to the drawn bank by a brown foxing stain. `tools/trace_shoreline.py` gained a declared
> `LETTERING` window that reads the map's own type as type, spliced into the uncorrected ring
> so the declared box is the blast radius. Heightfield regenerated: **0 cells changed outside
> the corridor E +505 … +660, max |delta| 0.000000 m, 0 waterline crossings**; inside it 1 719
> cells, max 3.605 m, 620 crossings, all land → water. Gradient audit unchanged and passing
> (`plain_block_max` 0.468 ft / 300 ft). Memo:
> `docs/RESEARCH/clark_reach_bulge_1834.md`. The 78–80 m vs 15–19 m South Water discrepancy
> this item cited was this defect, so **`docs/RESEARCH/chicago_american_office.md` § 3 now
> overstates the Clark residual** and should be re-measured against the corrected trace.

**K11 — mark DONE**:

> ### K11 — Trees standing in the river · **DONE 2026-08-13**
> The river mask (`isWater`) begins 100 mm BELOW the water plane, so a stem could root in that
> band, pass the mask and render standing in open water — 36 of 618 stations were doing it.
> `trees.js` now requires every tree and thicket to stand `TREE_DRY_MARGIN_M` = 0.20 m clear of
> the epoch's own `water_surface_m` (0.15 m of sunk bole + the 0.03 m ground-mesh tolerance,
> plus 20 mm). 197 candidates rejected; lowest surviving station +0.201 m. New smoke assertion
> **"no tree stands below the waterline"**, alongside — not replacing — the river-mask check.

**New items worth adding to the K list** (both fell out of this work):

> ### K13 — The La Salle Street re-entrant, and the other Main Branch sloughs
> Wright draws a narrow watercourse dropping south off the main stem between plat blocks 19 and
> 18, at local E +462 … +469 — La Salle Street. The waterline trace carries its mouth (that is
> as far as Wright washes it) and nothing beyond. The dossier records that the 1830 Thompson
> plat shows **three sloughs off the Main Branch**, and ROADMAP § S2e makes Conley/Stelzer 1833
> the primary guide for where the streams come in and where they terminate. Parcel: identify
> the three, and carry the ones that are attested as `hydrology.geojson` CENTRELINES in the
> form the north-side slough already takes — never as traced boundaries, because the bank wash
> is not there to trace. Cross-check the State Street slough mouth the trace already carries at
> E +850 … +856 against dossier zone 14.
>
> ### K14 — The terrain decimator's tolerance cliff
> `generators/terrain_gen.py --decimate-deg` behaves as a cliff, not a dial, against
> `MESH_FIT_TOLERANCE_M`: after the K6 correction, 0.040 and 0.038 both land at 30 mm and are
> refused, while 0.030 lands at 3.1 mm — and costs 247 527 triangles / 6.4 MB against the
> previous 135 249 / 3.5 MB. The GLB now committed is the 0.030 one. Worth a look at whether
> the planar decimate is the right operator here, or whether the fit should be enforced by a
> quadric-error budget instead of a dihedral angle; the payload is inside the 25 MB budget
> (`tools/publish.sh` reports 19.16 MB) but the ground is now the largest single asset by a
> wide margin. **The rendered-triangle budget is the tighter constraint**: the smoke measures
> **564 681 tris at 1280×800 against a 600 000 budget** — 6 % of headroom, where before this
> change there was roughly 25 %. The terrain is `frustumCulled = false`, so all 247 527 of its
> triangles are in every frame. The next parcel that adds geometry will hit this ceiling
> before it hits the payload one.

---

## Proposed `docs/STATUS.md` entries

> **The Clark Street headland was the map's own lettering.** Fixed 2026-08-13. What makes it
> worth recording is that the trace had been *believed* against a measurement that disagreed
> with it: the South Water georeference note recorded 79.6 m of residual at Clark against
> 18.7 m at Dearborn and attributed the swing to paper stretch. Both numbers were right and the
> explanation was wrong. A 60 m local disagreement between two independent methods is a defect
> report, not an error bar.
>
> **`generators/terrain_gen.py --glb` had been unrunnable since `terrain_inputs` was
> extracted.** `terrain_inputs_sha()` is called before `main()` inserted `generators/` on
> `sys.path`; run as `python3 generators/terrain_gen.py` that path is `sys.path[0]` by accident,
> run under `blender --python` it is not, and the GLB half died on `ModuleNotFoundError`. The
> insert moved to import time. Nothing caught it because `tools/bake.sh` does not build terrain
> and the terrain GLB is a rare, deliberate invocation. **The heightfield and the GLB are now
> back in step**; the committed GLB before this run was baked at `--decimate-deg 0.04` and the
> one after at `0.03` (see K14).
>
> **The tree-placement gate and the river mask are two different questions.** `isWater` asks
> "is this the river" and its threshold is 100 mm under the datum, which is correct for that
> question and was silently wrong for "may a stem stand here". The release gate had a green
> check on the first question while the owner had a photograph of the second failing. Both
> checks are now present.

---

## Proposed `docs/LIBERTIES.md` — nothing owed

`tools/validate.py` reports liberties coverage unchanged (571 values owed, 570 declarations)
after this work. The lettering correction removes an artefact rather than adding an invention:
the waterline inside the declared box is still Wright's own wash, reconnected across his own
type. The tree margin narrows an existing placement rule and invents nothing. No new admission
is owed, and none was added.

---

## Things deliberately NOT changed

- **The stream at La Salle** (E +462 … +469). It is real, it is already traced as far as Wright
  washes it, and it is 70–150 m west of the bulge. Extending it south past the wash would be
  inventing a bank. See K13 above and § 4 of `docs/RESEARCH/clark_reach_bulge_1834.md`.
- **`isWater` / `SHORE_Y`.** Left at −0.10 m. It is the traced river mask that the gallery
  width, the three land divisions and the flora shore-distance field are all built on; moving
  it would move the ecology as a side effect of a placement fix.
- **The bank-distance field `dw` in `trees.js`.** Still measured to the river mask, so the
  ZONE 5 gallery band keeps the geometry the flora dossier argues for. The waterline gate is a
  hard rejection layered on top, not a new definition of the bank.
- **`docs/RESEARCH/chicago_american_office.md` § 3.** Its 79.6 m figure is now known to be
  measuring this defect rather than the georeference, but re-measuring it is a South Water
  parcel's job, not this one's — flagged in the K6 text above.
