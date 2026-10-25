# T-3137 — the transom and the fan of Glessner's 18th Street gable light

Piece 2 of 5 of T-3117 (Glessner's photographic sign-off), handed on by T-3127. HABS 14 showed the
light's round head standing higher over its transom than built, which left the print's transom
about 0.3-0.5 ft under the build's 34.14-34.88 ft. The print also showed fewer, broader stones in
the fan than the 11 voussoirs built. HABS 01 does not resolve the transom, so both readings rested
on HABS 14 alone.

**Acceptance, stated before the work:** the transom read on HABS 14 and on a second picture, or
ruled on HABS 14 alone if no second picture resolves it; the fan's stones counted; both ruled,
rebuilt, Glessner rebaked and every Glessner view re-rendered.

## The second picture

HABS 17 is the second picture. It was taken from the north-east (T-3116 used it as a check on the
fan's crown), and it resolves the light from crown to sill in about 63 px: the dark round head, a
bright stone band, the dark sash and the bright sill.

## How it was read

- **HABS 14** is read on T-3116's own vertical. That is the projective map through sheet 6's
  crest, both stack stones, and the north pairs' sill and head (seven anchors). Each edge is the
  half-way crossing of a column-mean profile through the light (x 972-988).
- **HABS 17** is read linearly between the light's ruled head (36.2 ft ng) and sill (30.0), on
  the light's own column. Over a 6 ft span the camera's tilt does not matter. Its head and sill
  are the view's scale, so they read as built by construction.
- On both, the same picks taken on the render of the build return the built transom, and that
  method error is taken off the photograph's reading. `read_transom.py` holds the picks and
  re-derives `readings.json` (`--check` compares).

| ft ng, less the method | HABS 14 | HABS 17 | built before |
|---|---|---|---|
| transom's top | 34.45 | 34.32 | 34.88 |
| transom's foot | 33.68 | 33.90 | 34.14 |
| transom's centre against the build | -0.45 | -0.40 | |

HABS 14's other two readings show how far its vertical can be trusted. The head reads 0.32 ft
over the build and the sill 0.19 ft under it.

## The fan's stones

The fan was read on HABS 14, at about 18 px to the foot. For each ray from the spring's centre,
the side-by-side's intensity was averaged between radii 35 and 75 px and then detrended. Joints
show as minima. On the render of the 11 built voussoirs, this profile finds all ten joints, 17.2
degrees apart, so it can resolve joints that close together.

On the photograph it finds **six joints**: 30, 53, 75, 101, 125 and 151 degrees from the west
spring. They are about 24 degrees apart, with none within 10 degrees of the crown. The minimum
at 173 is the spring's bed, and 50 and 56 are one joint read twice. That makes **seven
voussoirs, keyed at the crown**. HABS 01 is coarser (about 5 px to the foot), but its profile also
finds 7-8 minima where its render of the 11 found 10-13.

## The ruling

- The transom comes down **0.4 ft**, to **33.74-34.48 ft** ng (its depth of 0.74 ft is kept).
  The two pictures read its centre 0.45 and 0.40 ft under the build's. The head (36.2), spring
  (35.15) and sill (30.0) are not touched. So the round head now stands on jambs that run
  **0.67 ft** plumb above the transom, which is how HABS 14 draws it.
- The fan has **seven voussoirs**, keyed at the crown, in place of the 11 that had no count
  behind them. Its ring (5.0 ft from the spring) and crown (40.15) are T-3127's and do not move.

Recorded in `data/structures/glessner_house.json` (the v4 detail schedule's north-gable light).
HABS 17 joins that schedule's sources.

## Result

`habs14-photo-before-after.jpg` and `habs17-photo-before-after.jpg` each show the photograph, the
render before and the render after.

- **HABS 14:** the re-rendered transom reads 34.35-33.59 ft on the same vertical, against the
  photograph's 34.31-33.52 (34.74-33.98 before). The fan profile on the new render finds six
  joints at 22, 48, 75, 102, 131 and 159 degrees. The middle two land on the photograph's 75
  and 101. The outer joints stand up to 8 degrees wider of the crown than the photograph's.
  At these radii that is what a 5 px error in the hand-picked spring centre does, so the stones'
  relative widths are not ruled; the build divides the fan equally.
- **HABS 17:** the transom's centre reads 34.03 ft on the new render against the photograph's
  34.04 (34.44 before).
- Glessner was rebaked (`bake.sh --only glessner_house`), and all 12 Glessner views were
  re-rendered and diffed against their previous renders. Apart from the light and its fan, the
  renders differ only by scattered shading noise. Every verdict is kept.
