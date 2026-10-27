# 1729 Prairie — J. W. Taylor's photograph no. 1445, its camera (T-3161)

Two prints of one negative, both in the Prairie library and the image store, both from the Art
Institute of Chicago's Ryerson and Burnham Archives:

| library id | print | size | sha256 |
|---|---|---|---|
| `a16-aic-taylor-album-pullman-p69` | Taylor photo album no. 1, p. 69 (U525730) | 1200 x 923 | `8e9acc6fe325b5e7d7aa04c68396fe02cfb8e31b10e55a1a8e9fb8e2b29df345` |
| `a16-aic-taylor-pullman-from-nw` | print 16399 (CIM 184), with the Archives' grey scale | 1200 x 1100 | `7e09cff542e8006816e1c37ef2165813df4858e4e76675f68f9dc20964369bb5` |

Both carry "1445" scratched on the sidewalk and the same trees, carriage marks and shadows: one
negative. Phase correlation over scale puts the 16399 print at 1.015 x the album print, offset
(-6, +29) px; the stack's cap at (505, 160) on the album print lands at (507, 191) on 16399, where it
is read.

**Why it is not a reference view yet.** The library records both prints as "rights unknown — link
only" (AIC: "contact the Art Institute of Chicago Archives for publication information"). The image
gate's cameras need the picture in the tree, and committing a copy is a rights decision, which is
the owner's (AGENTS.md); the question is on T-3161. The 1801 Kimball Taylor print was committed
(T-2538) because its library entry is public domain by age. If the answer is yes, the two cameras
below go into `data/reference_views/pullman_house_1729_prairie/` with the prints copied beside the
Detroit print, and `node tools/photo_match.mjs` writes their match records.

## The camera (album print, 1200 x 923)

```json
{"principal_px": [600, 603.0], "focal_px": 1610.5, "eye": [69.18, 61.35, 1.6], "yaw_deg": 229.07,
 "sun_uvy": [1.0, 0.8, 1.0]}
```

For the 16399 print: `principal_px` [603, 641], `focal_px` 1634.7, the rest the same.

**How it was fitted.** Level (the house's verticals stand vertical in the print), the eye 1.6 m over
the walk. The near corner is the south-west corner, where the main cornice's top peaks at x 447,
y 299 and falls in a straight line both ways: to the Prairie front's north end at x 152, y 349 (the
north-west projection's corner, u 27.75, v -1.2) and to the 18th Street flank's east end at x 850,
y 379 (u 0, v 17.93); the cornice's top taken at 12.9 m, the GLB's. A least-squares fit of eye, yaw,
focal length and the principal point's height to those three points leaves residuals of 0.4-2.2 px.
The camera stands in 18th Street's far half west of Prairie Avenue's line, about 59 m from the
corner, looking north-east: further south and less west than the Detroit print's (88.3, 42.9), so
the flank is seen much more squarely (about 18 px a metre along it at the corner, against Detroit's
5-6).

**What it reads.** The flank's great stack (built, L-pullman-1729-flank-stack-3161): on the cornice at
x 487-522, y 272-292, its cap at y 160 (18.7 m). Light: the front and flank both lit, the shadows of
the street trees falling toward the camera's right, so the sun is low in the south-west, as in the
Detroit print.

## What differs from the build through it (for the match record when it joins the gate)

- **open — the 18th Street arcade's place.** Through this camera the arcade's west arch stands at x
  640-730 and its south arch at x 745-790, which puts the block's west face at about u 15.8 and its
  east end near u 10.5, with one window bay (x 545, both storeys) between the corner pier and the
  arcade. The build stands it at u 16.27-21.4 (T-3160, off the Detroit print, where the flank is seen
  at 5-6 px a metre) and draws it at x 580-695 here; the 1911 sheet puts it at u 15-20. The 1890
  Albertype plate, through its own camera, sits between the two (its arch about 20-30 px east of the
  build's). Moving the block is left until the pictures agree: the Detroit print's reading and this
  one differ by more than a camera's error at either.
- **open — the flank's window bays.** The photograph shows, east of the corner pier, one arched window
  over another (x 545), then the arcade with the paired and triple arched windows over its balcony
  (x 655-685, 725-765); the build draws a pair west of the arcade and three single bays east of it.
- **open — the deck stack at (18, 12.5)** rises just east of the flank stack in the render, where the
  photograph shows only cresting.
- **not shown — colour**: a toned albumen print; the walls print as light as the coping wall.
