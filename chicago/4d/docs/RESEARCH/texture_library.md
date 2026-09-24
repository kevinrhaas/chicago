# The 1835 PBR texture library — provenance, and what may be believed of it

*Supplied by the owner 2026-09-19; vendored at `assets/textures/chicago_1835_pbr/`.
T-1450 owns the adoption. This page is the provenance record its LICENSE requires and the
measurement that says which of its maps may be bound to a surface.*

## Where it came from

25 materials, procedurally synthesised by `tools/generate_1835_pbr_library.py` — which
ships inside the library — with a seed committed per material, so every map re-derives.
Each carries `basecolor`, `roughness`, `ao`, `metallic`, a packed `orm`, a 16-bit `height16`
and **both** normal conventions (`_gl` and `_dx`), plus a `material.json` stating its span in
metres, its texel density, its mean roughness, its colour space and a confidence tier.

The LICENSE is permissive and carries one condition, which this project would have imposed
anyway:

> Historical confidence labels and provenance notes should remain attached so reconstructed
> surfaces are not silently represented as attested evidence.

One material is not purely procedural: `muddy_rutted_street` is derived from an AI-generated
mud study that ships beside the generator as `source_mud_ai.png`. No third-party photograph
is embedded or sampled anywhere in the set.

## It was authored against this repository's material sheet

`generators/common/materials.py` and the library agree to two decimals on tiling rate, texel
density **and** mean roughness across seven substrates — clapboard 4.48 m / 228.6 px per m /
0.86, board-and-batten 4.272 / 239.7 / 0.88, vertical board 4.58 / 223.6 / 0.90, hewn log
4.08 / 251.0 / 0.92, sawn board and heavy timber 4.00 / 256.0, chinking 2.04 m. materials.md
§3.2's rule — every tile a whole multiple of the surface's own rhythm — is already kept.

Two divergences are real and are T-1450's to settle: `cat_and_clay_chimney` renders 2.04 m
at 1024 px, which is 502 px per m against the chinking row's 251; and the library assigns
tiling rates to brick (4.20 m) and stone (4.00 m) where the sheet leaves both `None` because
no source gives a course dimension.

## What the maps actually contain — measured

Take the row-mean or column-mean of a map, drop the DC term, read the dominant spatial
frequency, and compare it with the module `material.json` declares. **The declared module
lives in the relief maps, not in the colour:**

| material | declares | `height16` | `ao` | `basecolor` |
|---|---:|---:|---:|---:|
| `clapboard_weathered_oak` | 32 courses | **32** | **32** | 1 |
| `board_and_batten_weathered` | 12 battens | 24 (two edges each) | **12** | 2 |
| `vertical_sawn_board` | 20 boards | **20** | 40 (two edges each) | 1 |
| `wood_shingles_weathered` | 32 courses | **32** | **32** | 1 |
| `hewn_log_oak_chinked` | 12 courses | **12** | 36 | **12** |
| `chicago_clay_brick_lime_mortar` | — | — | — | 48 × 40 |

The relief is strong: clapboard's height spans 47,219 of 65,535. The **colour** is what is
flat — the basecolors span 16 to 26 values of 255, which is why a contact sheet of this
library reads as tinted noise and why a first pass over it concluded, wrongly, that ten of
the twenty-five had lost their module. That reading measured the one map this renderer must
not use.

## Which maps may be bound to a building, and which may not

`renderers/web/js/buildings.js` carries **base colour and roughness per vertex, not per
material**, so that two walls differing only in paint share a draw call — the whole
untextured town is one draw call in the colour pass. `materialKey()` hashes the `map`,
`normalMap`, `aoMap` and `roughnessMap` uuids and deliberately not the colour. The sheet
says the same thing from the other end: *no substrate owns a colour*.

So:

- **Bindable**: `normalMap`, `roughnessMap`, `aoMap` (and `height16` for a future
  displacement or parallax path) — one set per SUBSTRATE. Every clapboard wall keeps sharing
  one material, so the draw count rises by the number of substrates in view, not by the
  number of buildings. This is the "shared atlas across masters" route T-0285 asks to be
  priced, and it is the opposite of the per-master AO bake that cannot batch.
- **Not bindable**: the basecolors. Binding the four clapboard finishes as textures would
  split one draw call into one per finish, defeat T-0048's per-building tone jitter, and
  contradict §1.1.

## What this library does not settle

R-W2a finding 2 stands: **no source in this repository states what any Chicago roof of 1835
was covered with.** The library ships `wood_shingles_weathered` and `roof_boards_weathered`
regardless, and its own note concedes the 0.14 m shingle exposure is "a declared
reconstruction outside the attested North Side school". An asset arriving is not evidence
arriving. Those two, and the brick and stone tiling rates, are adoptable only behind an
L-number in `docs/LIBERTIES.md` that names the claim and whose authority it rests on.

The ground and waterfront maps are held back for their own parcel. materials.md §1.2: the
ground, roads and water are **runtime canvases**, not assets, and *"three parcels have
already been burned by treating the ground as a building surface."*

## Why the whole set is vendored

Unreal is a stated future target. The DirectX normals, the packed ORM and the 16-bit
displacement are exactly what that engine consumes and are not what the web renderer needs —
they cost nothing to carry now and would be expensive to reacquire. The maps the web
renderer cannot use today are not dead weight; they are the other engine's half of the set.
