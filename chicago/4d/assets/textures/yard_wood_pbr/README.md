# Yard woodpile wood — `yard_wood_pbr`

T-3474. One atlas, `woodpile_atlas/`, that `renderers/web/js/yard.js` binds on the woodpile mesh
(every year with woodpiles: 1812 and 1835). Six cells, drawn at 1024 px and shipped at 512 (the
published tree's byte budget); a face samples a window of the inner 480 px, which is `WOOD_CELL_M` =
0.85 m of wood (565 px to the metre); the 16 px round it is a gutter of the same picture so the mips
of one cell do not bleed into the next.

| cell | what it is | where it is drawn |
|---|---|---|
| `rick_ends_a`, `rick_ends_b` | split billet ends racked in a rick: quarters, eighths, halves, slabs, small rounds, with rings, rays, bark rinds, checks, axe facets, weathering | a rick's outward face |
| `rick_sides` | the sticks along their length: bark and split faces in courses | a rick's top and its ends |
| `round_end` | one sawn round: rings, checks from the rim, kerf, axe scores | the chopping block's top, a log's ends, the end of a billet |
| `log_bark` | oak/hickory bark, interlacing ridges along x | a log's side, the block's side, a stake, a skid |
| `split_face` | a split face along the grain | the billets on the ground, a slab, a loose stick |

`material.json` gives each cell's `[x, y, w, h]` in image pixels (origin top left). Rebuild with:

    python3 assets/textures/yard_wood_pbr/tools/generate_yard_wood_pbr.py
    python3 tools/ktx2_sheets.py --only yard_wood_pbr/

The masters (base colour, OpenGL normal, packed ORM, 16-bit height) are PNG; the renderer loads the
`*_web.jpg` maps or their `.ktx2` derivatives. The look is reconstructed and procedural; no photograph
is used (`docs/LIBERTIES.md` L-t3474-yard-wood-surfaces).
