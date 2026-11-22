# T-3721 — 2126 Prairie, the Robbins house completed: a structure version on K01

Piece 2 of T-1926 (the S15 package of the T-1837 programme). Piece 1, T-3720, refined 2120; piece 3, T-3722, solves
the plate's camera and signs off the parent's image gate. Liberty `L-k01-robbins-2126-3721`.

## Why a version

On 1 July 1904 the Robbins house was being built (census ruling r35-robbins-2126: the Hamill house razed in 1904, the
new house complete in the May 1905 plate). The default record keeps that works shell. The finished house is a
structure version (docs/STRUCTURE-VERSIONS.md) beside it:

    https://chicago.polecat.live/4d/dev/1904/?structure=robbins_house_2126_prairie&version=completed

K01 records are emitted in pure Python and `generators/k01_emit.py` reads only `data/structures/`, so no command could
build a K01 version. `generators/k01_versions_emit.py` does, through the same `k01_emit.glb_for`; it is a separate file
because `k01_emit.py` is hashed into every K01 mesh's inputs, and editing it would have restaled all of them. `bake.sh`
runs it beside `k01_emit.py`; `check.sh` runs its `--check`.

## What was read

| reading | where | value |
|---|---|---|
| main body | sheet 35 at full size, columns 666.4-732.4, rows 1386-1451.6 | 12.26 m deep, 12.19 m along the front |
| rear wing, '3' | columns 602-666.4, rows 1391.6-1432.4 | 12.0 m deep, v 3.57-11.15 |
| corner | column 666.4, row 1451.6, through 2120's committed corner | 1.47 m south of the draft's |
| scale on the plate | the front's 12.19 m over about 1160 px of the 2400 px copy | about 95 px a metre |
| bays | the plate | axes at 1.35, 3.65, 6.10 (door), 8.54, 10.84 m |
| principal floor | the threshold over the walk | about 1.26 m (built 1.28: seven risers) |
| sash | principal and chamber / attic | about 1.07 x 1.76 m / 0.85 x 1.2 m |
| entablature, sill course | over the chamber storey | 7.87-8.95 m, 9.1-9.45 m |
| top cornice | on blocks | about 11.2-11.8 m |
| door | round head with fanlight | about 1.6 m across, crown about 4.6 m |

## Not built

Pilaster heads, keystones, the marble panels and the carved panel over the door, the frieze's carving and dentil teeth,
six-over-six glazing, the door's side lights and cornice, the brick of the gate piers and their balls, the brick wall and
pier returned north, the corner scroll, and the sheet's two iron-clad flank bays. Each is in the liberty with its reason.

## Checks

`node tools/photo_match.mjs` with a throwaway camera on the plate (square-on, 25 m out, eye 1.5 m; not committed: the
camera is T-3722's to solve): `plate-side-by-side.jpg`. Review renders from the north-east (`after-ne.jpg`) and the
south-west rear (`after-sw_rear.jpg`). The first look hid the end chimneys behind the cornice (set 2.8 m back, 0.7 m
high) and drew the door brown; the chimneys were brought forward and raised and the door painted, in the record.
