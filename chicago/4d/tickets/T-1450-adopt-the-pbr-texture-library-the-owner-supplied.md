---
id: T-1450
title: Adopt the PBR texture library the owner supplied: it is dimensionally interlocked with the material sheet and its relief maps carry the modules they declare, so wire normal/roughness/AO per substrate now and vendor the whole set for the Unreal target
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1568
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T13:15:49.499Z
claimed_run: null
---

Adopt the PBR texture library the owner supplied: it is dimensionally interlocked with the material sheet, and ten of its twenty-five maps declare a module their pixels do not contain.

The owner supplied a 25-material PBR library (`Chicago_1835_PBR_Texture_Library`, four
parts, ~80 MB, CC0 per its LICENSE.txt, deterministic procedural synthesis with a seed per
material). Each material ships basecolor, roughness, AO, metallic, ORM, 16-bit height and
BOTH normal conventions, plus a `material.json`, a manifest, a contact sheet and research
notes.

**IT WAS GENERATED AGAINST THIS REPO'S MATERIAL SHEET, and that is the valuable part.**
`generators/common/materials.py` SUBSTRATES and the library agree to two decimals on the
tiling rate, the texel density and the mean roughness — seven substrates, not one of them
a coincidence:

| substrate | sheet `tile_m` / `texel_px_per_m` / roughness | library `span_m` / `px_per_m` / `mean_roughness` |
|---|---|---|
| clapboard | 4.48 / 228.6 / 0.86 | 4.48 / 228.57 / 0.86 |
| board_and_batten | 4.272 / 239.7 / 0.88 | 4.272 / 239.7 / 0.88 |
| vertical_board | 4.58 / 223.6 / 0.90 | 4.58 / 223.58 / 0.90 |
| hewn_log | 4.08 / 251.0 / 0.92 | 4.08 / 250.98 / 0.92 |
| sawn_board | 4.00 / 256.0 / 0.94 | 4.00 / 256.0 / 0.94 |
| heavy_timber | 4.00 / 256.0 / 0.90 | 4.00 / 256.0 / 0.90 |
| chinking / cat_and_clay | 2.04 / 251.0 / 0.95 | 2.04 / **501.96** / 0.95 |

The dimensional contract §3.2 argues for — *every tile a whole multiple of the surface's
own rhythm* — is already honoured in the metadata. The `material.json` schema also carries
a `confidence` tier per material with attested/reconstructed split out in prose, which is
this project's epistemics arriving in an asset pipeline unprompted.

**THE MODULE IS IN THE RELIEF, NOT IN THE COLOUR — and that is the whole finding.** A
first reading of the basecolors said ten of the twenty-five had lost their module, and
that reading was wrong: it measured the one map the renderer must not use. Take the
row-mean (or column-mean) of each map, drop the DC term, read the dominant spatial
frequency, and the declared module is present in every relief map tested:

| material | declares | `height16` | `ao` | `basecolor` |
|---|---:|---:|---:|---:|
| `clapboard_weathered_oak` | 32 courses | **32** | **32** | 1 |
| `board_and_batten_weathered` | 12 battens | 24 (two edges each) | **12** | 2 |
| `vertical_sawn_board` | 20 boards | **20** | 40 (two edges each) | 1 |
| `wood_shingles_weathered` | 32 courses | **32** | **32** | 1 |
| `hewn_log_oak_chinked` | 12 courses | **12** | 36 | **12** |

The relief is not faint, either: clapboard's height spans 47,219 of 65,535. What IS flat is
the colour — the basecolors span 16 to 26 values out of 255, which is why the contact sheet
reads as tinted noise.

**AND THE RENDERER MUST NOT TAKE THE BASECOLORS ANYWAY.** `renderers/web/js/buildings.js`
is explicit: *"BASE COLOUR (R-W5a) and ROUGHNESS (R-W5a2) ARE CARRIED PER VERTEX rather
than per material... The whole untextured town is one draw call in the colour pass."*
`materialKey()` hashes `map`, `normalMap`, `aoMap` and `roughnessMap` uuids — and NOT
colour, deliberately, so that two walls differing only in paint share a batch. It is also
the sheet's own architecture: *"No substrate owns a colour."*

So adopting the four separate clapboard **basecolors** would do three bad things at once:
split one draw call into one per finish, defeat T-0048's per-building tone jitter, and
contradict §1.1. Adopting the **normal, roughness, AO and height** of ONE clapboard
substrate does none of them — every clapboard wall in the town keeps sharing a material, so
the draw count rises by the number of distinct substrates in view (a handful), not by
building count.

That is also the shape T-0285 asks someone to price. Its problem is that each master gets
its OWN baked 512² atlas, so no two AO'd buildings can batch; a SHARED substrate tile is the
opposite case, and is the "shared atlas across masters" route named in its acceptance.

**THE GENERATOR SHIPS**, at `tools/generate_1835_pbr_library.py` (367 lines, numpy/scipy,
deterministic, seeded per material). `clapboard()` really does draw 32 courses with a
staggered butt joint; the flat basecolor is a palette-mapping choice downstream, not a
missing module. So a colour that needs more life is a regeneration, not a re-authoring —
and the maps we actually want are already right.

**THREE MATERIALS ASSERT WHAT THE SHEET REFUSES IN WRITING.** `materials.py` says, in
terms: *"No source in this repository states what any Chicago roof of 1835 was covered
with... inventing one here to make the sheet look finished is the exact move
docs/LIBERTIES.md exists to catch."* The library ships `wood_shingles_weathered` and
`roof_boards_weathered`. The same module leaves `brick` and `stone` at `tile_m = None`
because the rate is UNRESOLVABLE *"rather than filled with a modern brick"*; the library
ships brick at 4.20 m and limestone at 4.00 m. The library's own notes are honest about it
(*"brick dimensions are reconstructed, not Chicago-attested"*) — which is what makes them
adoptable **under a written liberty**, and not adoptable silently.

**THE GROUND MAPS ARE THE BEST PIXELS AND THE WRONG TARGET.** `muddy_rutted_street` is the
strongest asset here — broadband, no dominant periodicity (peak share 0.02), real aggregate
and rut structure. But materials.md §1.2: *"The ground, the roads and the water are the only
textured surfaces in the scene and they are **runtime canvases**, not assets... W2's atlas
must not absorb them — three parcels have already been burned by treating the ground as a
building surface."* Taking them is a separate decision from this one.

**Acceptance:**

- The library is vendored whole — all 25 materials, both normal conventions, the ORM pack,
  the 16-bit height, the manifest, RESEARCH_NOTES and the generator — under a stated path,
  with a `docs/RESEARCH/` note recording provenance. **Vendored whole because the Unreal
  target is real**: DX normals, packed ORM and 16-bit displacement are what that engine
  wants, and they cost nothing to carry now and are expensive to reacquire later. The
  LICENSE requires the confidence labels travel with the maps; they do.
- A **conformance tool** (`tools/check_texture_module.py --check|--self-test`) measures each
  adopted material's dominant spatial frequency **in its height and AO maps** — not its
  basecolor — against the module `material.json` declares, and is RED when they disagree.
  Self-test drives it against a synthesised tile of known period, and against a flat one.
  This is the gate that keeps the table above reproducible; a first reading that measured
  the wrong map got the answer backwards, and the tool exists so nobody repeats that.
- **What is wired into the web renderer now is relief only**: `normalMap`, `roughnessMap`
  and `aoMap` per SUBSTRATE, one material per substrate, basecolor left to the per-vertex
  tone stream. `materialKey()` is unchanged. The draw count at the critic stations is
  MEASURED before and after at both viewports and lands in the ticket — T-0285's question,
  answered for the case that actually batches.
- No basecolor map is bound to a building surface. §1.1's "no substrate owns a colour" and
  T-0048's jitter both survive, and the wealth gradient T-1210 deals stays readable.
- **The two liberties are TAKEN** (owner's ruling, 2026-09-20) and are already written:
  **L263** commits the shingle exposure at 0.14 m and with it the 4.48 m roof tile — the
  covering was never the open question, materials.md §2.2 grades it attested on the North
  Side school of 1833 and inferred elsewhere; the EXPOSURE is what had no source. **L264**
  commits the brick course at 70 mm and the brick length at 213 mm from a period 8 × 4 × 2¼ in
  common brick with a ⅜ in joint. Wiring them is this ticket's: `roof_plane` and `brick` gain
  their `tile_m` in `materials.py`, which stales the whole town — so this carries a bake.
- **The brick map is regenerated, not adopted as shipped.** The library runs 48 rows to its
  4.20 m span, an 87.5 mm course implying a brick just over 3 in tall; its brick LENGTH is
  right at 210 mm. Re-derive at `rows=60` with the shipped generator — deterministic and
  seeded — so the map carries the dimension L264 commits rather than the one that happened
  to ship. The conformance tool above is what holds it there.
- **Stone stays unsized and unbound.** The ruling named brick; §3.2 pairs them but the stone
  record's own note makes finish the prior question. `limestone_rubble_lime_mortar` waits.
- `cat_and_clay_chimney` is resolved to 251 px/m (512 px at 2.04 m) or its divergence is
  argued, per the chinking row: *"a wall whose two materials render at two densities reads
  as two walls."*
- The ground and waterfront maps are NOT wired into the terrain program here. §1.2: the
  ground is a runtime canvas and *"three parcels have already been burned by treating the
  ground as a building surface."* `muddy_rutted_street` is the strongest asset in the set
  (broadband, peak share 0.02, and derived from an AI mud study that ships beside it as
  `source_mud_ai.png`) and it still waits for its own parcel.
- Nothing in `materials.py` changes a committed constant to match an asset. The sheet is the
  source; the atlas is authored against it (materials.md §3.1).

**Stop condition:** every texture the town ships carries the rhythm its metadata claims,
measured in the map that holds it; no building surface takes a colour from an atlas; and the
Unreal-bound maps are in the tree whether or not the web renderer binds them yet.

**Links:** T-1210 (the fabric-by-household rule these maps would clothe) · T-0007 (the sheet
as code) · T-0126 (the openings half) · T-1447 (a figure nobody measured) ·
`docs/RESEARCH/materials.md` §1.2, §2.2, §3.1, §3.2, §3.4, §5 · R-W2a finding 2 ·
L263 · L264 · `docs/RESEARCH/texture_library.md`.
