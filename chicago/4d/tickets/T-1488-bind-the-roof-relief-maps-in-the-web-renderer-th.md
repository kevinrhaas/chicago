---
id: T-1488
title: Bind the roof relief maps in the web renderer: the metric roof UVs a 4.48 m tile needs — the smart-project atlas is a per-object island pack and cannot tile one — one shared material per roof substrate, the two maps published, and the draw count measured at the critic stations at both viewports
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: T-1465
opened: 2026-09-20
closed: 2026-09-20
pr: 1597
claimed_by: run 9/20/2026, 6:26:56 PM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-21T00:27:41.752Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35544501763
---

Bind the roof relief maps in the web renderer: the metric roof UVs a 4.48 m tile needs — the smart-project atlas is a per-object island pack and cannot tile one — one shared material per roof substrate, the two maps published, and the draw count measured at the critic stations at both viewports.

Piece 2 of 2 of **T-1465 — Give every roof its covering and its texture before the 297 are built: shingle and roof_board substrates on the sheet, dealt by archetype, bound to the vendored relief maps on L263's exposure — a roof nobody can see the material of is not a reconstruction, it is a gap**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What T-1487 leaves you.** The sheet carries `shingle` (4.48 m, 0.14 m exposure, 32
courses, 228.6 px/m) and `roof_board` (4.00 m), the dealing rule is written and its liberty
recorded, and every roof primitive in the town is drawn on a material named for its
covering. The vendored library (T-1450) already ships both maps with their modules intact
and measured: `wood_shingles_weathered` carries 32 course cycles in `height16` and 32 in
`ao`, `roof_boards_weathered` matches `sawn_board` at 4.00 m.

**And the question it could not answer in one run.** `generators/build.py` `unwrap()` runs
`bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)` per object. That is a
per-object island pack in 0..1 laid out for an AO atlas, so a tile rate expressed in METRES
cannot be read off it: the same map would land at a different scale on every roof and on
every island of one roof. Something has to give UV0 a metric meaning for roof faces, or add
UV1, or go triplanar in a shader — and each of those is a different bargain with the AO
path (`bake_ao`, off by default today) and with `docs/GLB-CONTRACT.md`.

**Acceptance:**

- A **decision, argued in the ticket before it is built**, on how a 4.48 m tile reaches a
  roof face: metric UV0 on roof primitives, a second UV set, or world-space triplanar —
  and what each costs the AO path and the GLB contract.
- **The relief maps are bound, not the basecolors.** `normalMap`, `roughnessMap` and
  `aoMap` per substrate; colour stays on the per-vertex stream, so the condition grading
  and T-0048's per-building jitter both survive and `materialKey()` is unchanged.
- **How the renderer knows a roof is shingled.** Material names are NOT pinned by
  `docs/GLB-CONTRACT.md` and it says in terms that a renderer keyed on one is reading a
  convention nobody promised to keep. So either the contract PROPOSES pinning the substrate
  name — bilaterally, per that document — or the substrate travels in the material's
  `extras`. Pick one and say why.
- The two roof maps are **published** into `site/chicago/4d/` by `publish.sh`, or the
  reason they are not is written down.
- **The draw count is measured at the critic stations, both viewports, before and after**,
  and lands in the ticket. One shared shingle material across every shingled roof should
  cost one draw call, not one per building — T-0285's open question answered for the case
  that actually batches.
- **Bake** if the chosen route moves a vertex or a UV, which two of the three do.
- The `lake_market` and `south_water` critic frames show roofs reading as roofs — a shingle
  field legible as courses, a board roof as boards — at both viewports.

**Stop condition:** a visitor looking at a roof can tell what it is made of.

**Links:** T-1465 (the parent) · T-1487 (the sheet, which lands first) · T-1450 · T-0285 ·
L263 · `docs/GLB-CONTRACT.md` · `docs/RESEARCH/texture_library.md`.

---

## THE DECISION, argued before it was built (2026-09-20)

**How a 4.48 m tile reaches a roof face: derive the UV in the shader, from world
position and the face's own normal.** The three routes and what each costs:

| route | AO path | GLB contract | bake |
|---|---|---|---|
| metric UV0 on roof primitives | **breaks it.** `bake_ao` packs occlusion into UV0; a metric unwrap overlaps by construction — that is what tiling IS — so two roofs write the same texels | unchanged | all 384 |
| a second UV set (TEXCOORD_1) | keeps it | **adds a vertex attribute**, plus a UV branch through seven archetypes' `add_poly` call sites, none of which carry UVs today | all 384 |
| **world-derived UV in the shader** | **untouched** — no UV0 is read or written | **unchanged** — nothing about what a GLB contains moves | **none** |

Route 3, with one correction to the plain triplanar the ticket named: a top
projection tiles in world XY, so the courses would run along a compass direction,
and this town's buildings do not — the Lake Street fronts alone sit at four
bearings, and a shingle course crossing the eave at 20 deg reads as a mistake from
the street. So the frame is taken from the FACE: `t = normalize(cross(n, up))` is
horizontal for any pitched roof and therefore lies along the eave, `b = cross(t, n)`
runs up the slope, and `uv = (dot(p,t), dot(p,b)) / tile_m`. Computed per VERTEX,
which is exact rather than cheap: `to_object()` sets `use_smooth = False`, so a
vertex carries its own face's normal and the projection is affine over a planar
face.

**How the renderer knows a roof is shingled: the material name, and
`docs/GLB-CONTRACT.md` § Roof coverings now PROPOSES the pin** — bilaterally, in
the terms that document requires, for `roof_<substrate>` and for nothing else.
The `extras` route the ticket offered is better-typed and was still rejected on a
measurement: the substrate is already in all 384 masters and all 384 web
derivatives, so the name costs no bake and `extras` costs 384 of them to carry a
fact the file holds. The 2026-08-17 objection in that document cited ROADMAP
K36(a) — 38 assets whose material names the `gltf-transform palette` pass had
merged away. **Re-measured for this ticket: across `assets/gltf/` and
`assets/web/`, 384 files each, ZERO materials are unnamed** (the pass has been off
since K36(b)). The name has exactly one writer, `roof_material_name()`.

## WHAT IS BOUND

`normalMap` from `normal_gl`, and the packed `orm` in BOTH `roughnessMap` (green)
and `aoMap` (red) — one file, two slots, the glTF-native packing the library
already writes, which halves the uploads against binding `ao` and `roughness`
separately. **The basecolors are NOT bound**: colour stays on the per-vertex
stream, so T-0007's roof-condition grading and T-0002's per-building jitter both
survive and `materialKey()` reads exactly what it read before. The tile rate is
read from the library's own `material.json` (`span_m`) rather than written into
the renderer, so it cannot drift from the sheet.

## THE DRAW COUNT, MEASURED — `critic_shots.mjs --metrics`, source tree, 2026-09-20

| station | viewport | before | after | Δ |
|---|---|---|---|---|
| lake_market | mobile 390x780 | 144 | 148 | **+4** |
| south_water | mobile 390x780 | 165 | 169 | **+4** |
| lake_market | desktop 1280x800 | 162 | 166 | **+4** |
| south_water | desktop 1280x800 | 189 | 193 | **+4** |

**T-0285's open question, answered for the case that actually batches.** One
shared shingle material across 241 shingled roof materials and one shared board
material across 128 costs **two batches, not 369** — `materialKey()` separates on
the map uuids and the maps are shared, so every shingled roof in the town merges
into one. The +4 rather than +2 is R-W5a2's own arithmetic read back: every batch
inside the sun's shadow box is a second draw call in the SHADOW pass, so two new
batches are two colour draws and two shadow draws. The figure is identical at both
stations and both viewports, which is what a batch-count change looks like as
against a visibility change.

## THE FRAMES

`lake_market` carries the close read at both viewports: the Sauganash's roof goes
from a flat plane to a lapped field whose courses run parallel to the eave, and
its colour does not move — the relief is the whole of the difference, which is
what "bind the relief, not the basecolor" was asked for. `south_water` looks along
the river at the far bank, so its roofs are at distance; that station priced the
draw cost above and `lake_market` carries the legibility. Every one of the four
frame hashes moved, which is the binding proving it ran.

## NO BAKE — and one correction that had to be given up to keep it that way

The chosen route moves no vertex and no UV, so `validate.py --stale` has nothing
to say and nothing was rebaked. **The generator-side docstring on
`roof_material_name()` still ends with the pre-pin sentence — "it is a LABEL and
not a contract … T-1488 has to choose" — and that is now wrong.** Correcting it
was written, run and then REVERTED: `generators/common/materials.py` is inside
every asset's input hash (`generators/code_inputs.py`), so the four-line docstring
edit staled **all 369 roofed assets** and `check.sh` refused the tree. That is
T-0164's lesson arriving in person — *"one full-town rebake, twenty minutes of
Cycles and 349 GLBs whose bytes change because Cycles is not bit-reproducible,
bought by a docstring correction."* The pin is recorded where it costs nothing and
where a reader of it lands — `docs/GLB-CONTRACT.md` § Roof coverings, which names
the function and the promise — and the docstring's correction rides the next run
that has reason to rebake the sheet.
