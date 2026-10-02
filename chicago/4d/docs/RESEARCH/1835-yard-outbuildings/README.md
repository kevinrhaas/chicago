# The yard outbuildings — captures and a written critique (T-1960)

Captured 2026-10-02 from the working tree with `tools/shoot.mjs`'s rig (swiftshader, HUD
hidden), at 1280×800 and 390×780. **Before** is the same tree with
`town_yard_outbuildings` left out of `data/yard/index.json`, so the only difference between
a pair is this record.

| station | where | what it shows |
|---|---|---|
| `yard-north` | blk_washington_wells, inside lot 2's yard, looking south | a merchant's stable and a whitewashed merchant's privy where the yard was empty |
| `alley-east` | the same block's alley, looking east | stables and privies lining the rear fences, house to house |
| `privy-close` | lot 4's privy, from its door side | the two-seat privy: corner posts, ledged door, shed roof falling to the alley |
| `cabin-yard` | blk_south_water_dearborn lot 3 | a labourer's privy, grey sawmill slab, partly behind a dooryard stem |
| `stable-alley-face` | lot 2's stable from the alley, sunlit | board-and-batten relief, sill, gabled roof |

## Critique

- **Scale reads right.** A privy stands just above the rail fence and well under the house
  eaves. A stable is a little lower at the eaves than a one-and-a-half-storey cottage. The door
  is a man's height in both. Nothing floats: each box stands on its lowest corner with the sill
  run below grade.
- **Variation reads house to house.** Whitewashed two-seaters behind the merchants' houses,
  board privies behind the tradesmen's, slab boxes behind the labourers', each weathered with
  its own house. The smoke counts the distinct tones (`the outbuildings differ house to house`).
- **Relief.** Battens, corner posts, ledged doors and the stable's loft door give the faces
  joints and shadow lines at walking distance. The sunlit alley face shows them best.
- **What falls short, stated.** (1) A board face in shade reads close to black. The scene's
  only fill is the calibrated sky (world.js), and mid-tone timber in shade is dark under it.
  The rail fences beside these yards read exactly the same, so this is about the furniture
  layers' albedo, not this record. The tones were lifted once toward silvered pine; going
  further would wash out the sunlit faces. (2) The faces are flat-shaded vertex colour, with no
  grain or ORM map. T-1963's wall relief is on the baked walls, and the yard layer has one
  material and no texture slot beyond the marks atlas. (3) No ground treatment: no trodden
  path to the privy door and no manure apron at the stable. That belongs to the yard ground,
  which T-1212's benchmark still owes.
- **Not imported from Glessner.** Nothing here takes Glessner's 1904 materials or planting as
  evidence. Every dimension and finish is bounded in docs/LIBERTIES.md **L353**.
