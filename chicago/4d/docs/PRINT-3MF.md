# Printing a structure (3MF)

`tools/export_print_3mf.py` turns one structure's GLB into a watertight, standalone,
single-piece 3MF for a home FDM printer (T-3395). The owner, 2026-11-05: *"a printable
3mf file … a standalone watertight print of the glessner house … just the structure of
the house of course, this may be something we will want to do for other structures at
some point"*.

```bash
pip install numpy scipy scikit-image manifold3d      # the last two only for this tool
python3 tools/recover_glessner_v4.py --materialize    # Glessner's GLB is packaged
python3 tools/export_print_3mf.py --structure glessner_house \
    --out glessner_house_1-250.3mf --preview glessner_house_1-250.png --report glessner_house_1-250.json
python3 tools/export_print_3mf.py --structure <structure_id> [--phase <phase_id>] --out x.3mf
python3 tools/export_print_3mf.py --glb assets/gltf/<file>.glb --scale 150 --out x.3mf
```

## Defaults, and why

| setting | default | why |
|---|---|---|
| scale | 1:250 | Glessner (about 52 x 25 x 15.6 m with its stoops and court wall) comes out about 208 x 98 x 62 mm, which fits a 220 mm bed with room to spare. Use `--scale 200` on a 256 mm bed. |
| minimum feature | 1.0 mm | two 0.4 mm nozzle widths plus margin. Anything thinner (cresting, finials, railings, downpipes, flagpoles) is thickened to it; thick walls keep their true size. At 1:250 that is 25 cm real. |
| voxel | 0.2 mm | one common layer height. The solid is rebuilt at this resolution, so detail finer than it (rustication joints, roof-tile courses) is softened, which the nozzle would do anyway. |
| base | 1.6 mm slab | under the footprint plus a 1 mm lip, enclosed courts floored, so the print stands and has bed grip. `--base-mm 0` for none. |
| smoothing / simplify | 0.6 voxel blur, 0.05 mm | flattens voxel stairs; the simplifier (manifold3d) never breaks the closed surface. |

## Roofs: one course pattern everywhere

The owner, 2026-11-06: *"make the roof surface a consistent version of the roof, all of
the roofs have different patterns and some nubs, let make the tiles consistent in form
across all the roof surface"*. A modelled tile is about 1 mm at 1:250, below what a
nozzle draws, and voxelized it came out as a different moiré on each roof plane with
the odd tile standing proud. So by default (`--roof-tiles uniform`) the tile materials
(`--tile-material`, default `roof_plane_*`) are left out and the roof deck
(`--deck-material`, default `roof_plane`) carries one shingle course every 1.2 mm up the
slope, 0.4 mm proud at the butt (`--course-mm`, `--course-depth-mm`), counted from grade
so every roof, dormer and cone has the same spacing. The courses are contoured from a
sub-voxel distance field, so they come out even rather than aliased against the voxel
grid. Ridge and hip rolls are tile material too; anything over 8 cm off the deck
(`--roll-m`) is kept. `--roof-tiles modelled` prints the tiles as modelled. A structure
with no tile/deck materials by those names keeps its roof as modelled.

Sheet-metal roofs take the same courses (the owner, 2026-11-06, of the copper roof on
Glessner's dining bay: *"Yes the turret should match"*). Its standing seams are 2 cm
wide and 1.6 cm proud, 0.06 mm on the print; voxelized they came out as lines of
one-voxel nubs that the thickener then swelled into beads. So for `--sheet-material`
(default `copper`; `none` to skip) the broad sloped sheets join the deck and take the
courses, the narrow seams and folds lying on them go, and the metal's other pieces
(finials, flashing, cresting) stay as modelled.

## What it keeps and drops

- **Dropped by material name**: lawn, turf, drive, paving, ground, water, vines, ivy,
  foliage, trees, people (`DEFAULT_EXCLUDE` in the tool). `--exclude 'glob'` drops
  more; `--include 'glob'` keeps a material a default would drop.
- **Dropped as ground clutter**: anything under 0.6 m tall more than 1.5 m from a wall
  (walks, kerbs). Steps and stoops next to the walls stay.
- **Dropped as loose**: any piece not joined to the house (the 3MF is one object).
- **Kept**: everything in the structure record, including attached masonry. Glessner's
  9 ft south court wall (HABS sheet 2, liberty L-glessner-court-wall-2201) is part of
  `glessner_house` and prints with it.

## How it makes a solid out of a render model

A render GLB is a soup of single-sided planes with no floors and the odd opening no one
sees from the street (Glessner has one where its roofs meet above the court), so the
tool never tries boolean unions. It rasterises the triangles into voxels, flood-fills
the outside air, and treats ball-sized covered air that the outside cannot reach
through an opening narrower than 4 m (`--room-ball-m 2`) as a room and fills it; the
room and the outside air then grow toward each other so a room fills to its walls while
window reveals, porches and the carriage passage keep their air. Lower `--room-ball-m`
for a small building whose rooms are under 4 m across.

The output is marching cubes over that solid, simplified by manifold3d, then checked
twice: manifold3d's own status, and an independent count that every edge is used
exactly twice in opposite directions, with positive signed volume and one shell. The
tool refuses to write a file that fails. `tools/test_export_print_3mf.py` (in
`check.sh`) proves the method on a toy house with an open door, a roof gap, a wire
flagpole, a lawn, a kerb and a floating pebble.

Nothing this tool writes is committed: a 3MF is a deliverable, not a scene asset.
