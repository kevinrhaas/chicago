---
id: T-1465
title: Give every roof its covering and its texture before the 297 are built: shingle and roof_board substrates on the sheet, dealt by archetype, bound to the vendored relief maps on L263's exposure — a roof nobody can see the material of is not a reconstruction, it is a gap
state: split
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: null
claimed_by: run 9/20/2026, 2:28:20 PM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-20T19:31:48.596Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35532164463
---

Give every roof its covering and its texture before the 297 are built: shingle and roof_board substrates on the sheet, dealt by archetype, bound to the vendored relief maps on L263's exposure — a roof nobody can see the material of is not a reconstruction, it is a gap.

**The owner's direction, 2026-09-20:** *"Roofs need to be addressed, you should as part of
the structures accept that there were period appropriate roofs and use the appropriate
textures accordingly, I would think that you would do all of that before you build all the
structure… you are being a bit dogmatic on the reconstruction concern, we have enough info to
build and take justified liberties to make this feel real."*

**And the refusal that prompted that was misread — by this project's own documents.** The
standing line has been "no source states what any Chicago roof of 1835 was covered with",
taken from `materials.py`'s docstring. What `docs/RESEARCH/materials.md` §2.2 actually grades
is narrower and more permissive:

| substrate | evidence | grade |
|---|---|---|
| `shingle` | *"the one direct attestation in the repository"* — the North Side school of 1833, **"a frame building twenty-six by thirty-eight feet; twelve-foot posts; sheeted and shingled roof"** | **attested** for that building; **inferred as the ordinary covering of a framed building here** |
| `roof_board` | `outbuilding.py`: *"a shingle field on an outbuilding would be claiming a finish"* | **inferred, and well argued** |

So the covering was never the open question. The open question was the **exposure**, and
§2.2 said exactly how to close it: *"Pick the exposure from a source or record a liberty."*
**L263 recorded the liberty on 2026-09-20** — 0.14 m, the same exposure this project already
committed for clapboard at T-0049, giving the 4.48 m roof tile at 228.6 px/m.

Everything needed to draw a roof is therefore committed. What is missing is the wiring.

## What is actually blocking it

`generators/common/materials.py` carries ONE roof substrate:

```
"roof_plane": Substrate(..., tile_m=None, ..., note="The roof plane, COVERING UNSTATED.")
```

There is no `shingle` row and no `roof_board` row, and `tile_m` is `None` — so no roof in
this town can be textured at all, whatever the atlas holds. The sheet grades roofs by
CONDITION (fresh, weathered, darkened, patched), which 218 records carry, and says nothing
about material.

Meanwhile the vendored library (T-1450) ships both maps with their modules intact —
measured, not assumed: `wood_shingles_weathered` carries **32 course cycles in `height16`
and 32 in `ao`**, exactly the module a 4.48 m tile at 0.14 m exposure wants, and
`roof_boards_weathered` matches `sawn_board` at 4.00 m.

## Why this runs BEFORE the build, which is the owner's point

297 roofs are still to build (T-1198, T-1199, T-1200 seat and raise them; T-1446 redeals the
anonymous ones). A roof built against a substrate with no covering and no tile has to be
rebuilt to get one — `materials.py` stales the whole town, so this is a full bake either way.
Doing it first costs one bake. Doing it after costs two and leaves every roof shipped in
between reading as untextured plane.

**Acceptance:**

- `materials.py` gains **`shingle`** and **`roof_board`** substrates: shingle at the L263
  tile (4.48 m, 0.14 m exposure, 32 courses, 228.6 px/m), roof_board as `sawn_board` at
  4.00 m. Both carry their §2.2 grade and their evidence in the row, as every other substrate
  does.
- **`roof_plane` survives as the fallback and nothing else** — the roof whose covering is
  genuinely undecidable. If every archetype resolves to shingle or board, the row says so and
  carries zero records rather than being deleted; a reader should be able to see that the
  question was answered rather than removed.
- **A dealing rule, argued and written down**: which archetypes take a shingle field and
  which take boards. §2.2's own reading is the starting point — framed buildings shingled,
  outbuildings boarded — and `outbuilding.py` already argues its half. Anything the rule
  asserts beyond those two gradings takes **an L-number**, in the form L263 used: what is
  claimed, on whose authority, and what would discharge it.
- **The relief maps are bound, not the basecolors.** T-1450 measured why: `buildings.js`
  carries base colour and roughness per vertex so the untextured town is one draw call, and
  `materialKey()` hashes the map uuids and deliberately not colour. Bind `normalMap`,
  `roughnessMap` and `aoMap` per substrate; leave colour to the vertex stream so the
  condition grading (fresh / weathered / darkened / patched) still reads and T-0048's
  per-building jitter survives.
- **The draw count is measured at the critic stations, both viewports, before and after**,
  and lands in the ticket. One shared shingle material across every shingled roof should cost
  one draw call, not one per building — that is T-0285's open question answered for the case
  that actually batches.
- **Bake** (`needs_bake`): `materials.py` stales the town. The `lake_market` and `south_water`
  critic frames show roofs reading as roofs — a shingle field legible as courses, a board roof
  as boards — at both viewports.
- The roof **condition** grading is untouched. This ticket gives the plane a material; what
  weathered it is already argued and is not re-opened.

**Stop condition:** no roof in the town is drawn on a substrate whose covering is unstated,
and a visitor looking at one can tell what it is made of — with the liberty that says so
recorded where they can find it.

**Links:** L263 (the exposure liberty, and the owner's ruling that took it) · T-1450 (the
vendored maps, and why colour is not bound) · T-0007 · T-0126 · T-1210 (the wall half of the
same rule) · T-1196 / T-1197 (the roof programme) · T-1198 / T-1199 / T-1200 (the build this
precedes) · T-0285 (the draw-call question) · `docs/RESEARCH/materials.md` §2.2, §3.1, §5 ·
`docs/RESEARCH/north_side_school_1833.md`.
