# Glessner's own close stands, inside Full's budget (T-3146)

T-3012 found two desktop stands right beside Glessner House over Full's **4.6 M** triangle
budget, with T-3012's view filter on: on Prairie 38 m east and 30 m south of the house's
centre looking at it (**4,675,021**), and on 18th 45 m west and 32 m north (**4,593,424**,
4,720,756 without the filter). On today's dev, framed the same way (eye 1.7 m up, aimed 7 m
up at the footprint's centre), they read **4,677,248** and **4,601,509**.

## What carries them

`QA_FOCUS=glessner_house node tools/qa_t3012_triangles.mjs` with the two stands
(`QA_STANDS`), every draw charged to its layer and every structure batch range to its record:

| stand | total | structures, view | structures, sun | Glessner, view | Glessner, sun |
|---|---:|---:|---:|---:|---:|
| Prairie, 38 m E / 30 m S | 4,677,248 | 1,709,232 | **2,425,893** | 1,353,013 | 1,421,694 |
| 18th, 45 m W / 32 m N | 4,601,509 | 1,855,753 | 1,859,223 | 1,408,436 | 1,421,694 |

Glessner is the house in front of the camera here, so it is drawn nearly whole in the colour
pass (its tile relief 275,144, five granite batches about 150,000-175,000 each, the court brick
165,000) and whole in the sun's (1,421,694 — at the Calumet stand T-3012 measured its sun's
pass at 584,800 because only that part of the house fell in the sun's ±240 m box there).
None of that is waste: the camera sees the house and the sun throws its shadow on what the
camera sees.

What is waste is the rest of the sun's pass on Prairie. Of its 2.43 M structure triangles, the
houses round the stand that draw **nothing** in the view still cast: Kimball 115,092, Law 68,723,
Spalding 45,140, Coleman-Ames 41,774, 1619 Prairie 39,450, Goodman 32,612 and twenty more, south
and west of the camera, whose shadows the sun throws away from the screen. Light has
left such pieces out since T-2529 (`shadow-casters.js`); Full never did.

## The change

Full now runs T-2529's sun-pass test, unchanged (`castersTowardView: true` on the `full` rung in
`main.js`): a structure piece is left out of the shadow map only when its bounding sphere,
swept along the sun's direction to 30 m below its base, lies wholly outside ONE plane of the
view frustum — where no point of its shadow can land on anything the camera sees. Everything
else goes to three's own shadow-camera cull as before; the colour pass, picking and instance
visibility are untouched. Balanced is unchanged.

## Measured (published /1904/, Full)

`node tools/qa_t3146_glessner_close.mjs` renders each held frame with the test off and on,
reads `renderer.info` triangles and every pixel back with `gl.readPixels`, and as a positive
control renders it with the sun casting nothing (the frame must change, or "no pixel changed"
could not see shadows). `QA_CONTROL=1` also renders the off frame twice.

| stand | viewport | off | on | within 4.6 M | pixels differing |
|---|---|---:|---:|---|---:|
| **Prairie, 38 m E / 30 m S** | 1280x800 | 4,677,248 | **4,383,566** | no, **yes** | 0 of 1,024,000 |
| **18th, 45 m W / 32 m N** | 1280x800 | 4,601,509 | **4,594,157** | no, **yes** | 0 of 1,024,000 |
| Prairie, 38 m E / 30 m N | 1280x800 | 4,092,427 | 3,980,834 | yes, yes | 0 |
| Prairie front, 40 m E | 1280x800 | 3,997,562 | 3,917,139 | yes, yes | 0 |
| 18th, 20 m E / 35 m N | 1280x800 | 4,285,583 | 4,146,354 | yes, yes | 0 |
| elevated, 45 m E / 45 m N, 30 m up | 1280x800 | 4,390,788 | 4,325,810 | yes, yes | 0 |
| Calumet's east walk at 20th (T-3008) | 1280x800 | 2,923,918 | 2,841,300 | yes, yes | 0 |
| **Prairie, 38 m E / 30 m S** | 390x780 | 4,638,119 | **3,769,954** | no, **yes** | 0 of 304,200 |
| **18th, 45 m W / 32 m N** | 390x780 | 4,921,521 | **4,162,199** | no, **yes** | 0 of 304,200 |

The no-shadow control changed 90,717-697,659 pixels at every stand, and the off/off control
changed none at the two ticket stands. No page errors or failed requests. Files:
`browser-validation-{desktop,mobile}-*.json`, and the two ticket frames as
`after-desktop-glessner-*.jpg`.

**Re-read after dev took T-3011** (the Indiana 18th-20th background row, #1302), on the
rebased tree, desktop: Prairie 38 m E / 30 m S **4,783,248 -> 4,489,566**, 18th 45 m W /
32 m N **4,600,755 -> 4,593,403**, both inside, every pixel the same
(`browser-validation-desktop-ticket-stands-after-t3011.json`). The background row cost
the Prairie stand about 106,000 and the test still clears it by 110,434.

## What is still thin

**18th, 45 m W / 32 m N stands only 5,843 inside at desktop (6,597 after T-3011).** From there the sun throws
Glessner's shadow toward the camera, so the test rightly keeps it (7,352 saved), and the
house's view pass is 1,408,436 of its 1,421,694 although the camera sees only its north and
west fronts: the court, south and east walls are behind its own walls, and T-2227's filter
proves a piece hidden only when its whole box falls inside ONE wall triangle, which Glessner's
finely cut faces rarely offer. Getting real headroom there is its own ticket (T-3152), not hidden
here.
