# The 18th Street / Prairie-Calumet alley corner from the air, inside `light` (T-3312)

T-1936's roof stand over the east-side alley (eye E 1500, N -3250, 60 m up; target E 1461,
N -3300, on the ground; `tools/qa_t1936_coach_houses.mjs`) read **1,598,204 triangles** on a
390x780 phone at `light`, against the tier's **1,270,000**. The ticket named three suspects:
the 1800 Calumet palm house, the Pullman glasshouse ranges and their planting, and the parkway
trees.

## What carries it

`node tools/qa_t3312_alley_corner.mjs` charges every draw of the held frame, the sun's pass
included, to its top-level layer, and every structure batch's draw ranges to their records
(`browser-validation-mobile.json`, `layersOff` / `structuresOff`):

| layer | triangles | view | sun |
|---|---:|---:|---:|
| structures | 1,316,964 | 1,078,336 | 238,628 |
| context city | 88,416 | 88,416 | 0 |
| railway | 59,506 | 32,687 | 26,819 |
| street trees | 54,164 | 22,724 | 31,440 |
| street grid | 46,521 | 39,011 | 7,510 |
| terrain | 21,231 | 21,231 | 0 |

Of the structures, the largest are the big Prairie Avenue houses seen whole from the air at
60-150 m: Ream 1901 (164,033), Doane 1827 (155,380), Moulton-Lowden 1912 (130,644), 1828
(107,523), Field 1905 (99,740), Dent 1823 (90,654), Field Jr 1919, Kellogg 1923 and Keith 1906
(63,000-73,000 each). **None of the named suspects carries it**: the four Pullman glasshouse
records are 44,502 together, the palm house's lodge 4,096, the street trees 54,164. Broken down
by batch (`tools/qa_t3012_triangles.mjs`'s `QA_FOCUS=ream_house_1901_prairie`, run at this stand
with its viewport set to 390x780 and its tier to `light`), Ream's weight is its untextured batch: 24 pieces, 80,500 triangles in the colour
pass. That is the house's mouldings, sash bars and carved courses, on a screen where one pixel
there is 9-22 cm across.

## The change: far pieces draw from a coarser copy at `light` (`renderers/web/js/far-colour.js`)

T-3286 already cuts each heavy piece a clustered twin for the sun's pass (`far-shadow.js`). That
twin cannot go into the colour pass, because a pool there mixes the faces meeting at a corner
and a surviving wall triangle would be lit by its neighbour's normal (the unit test's control
shows the sun's cut doing exactly that). So each heavy piece gets a second twin, cut the same
way in 8 cm cells except that a pool never mixes two normals: every face larger than a cell
keeps its own normal, and the detail smaller than one closes up. In the colour pass at `light`
only, a piece is swapped for its twin where the twin's worst vertex shift (sqrt(3) x 8 cm =
13.9 cm) projects to at most one pixel at the nearest depth of the piece's sphere. `full` and
`balanced` are untouched, and the twins are cut only when the batches are built for a tier
below `full`, so a desktop at `full` carries none.

The cell was chosen on the roof stand, published app, roof stand only (`far-colour.js` keeps
the table): 4 cm cells kept too much of each piece (1,382,582 / 1,363,567), 6 cm came to
1,285,925 / 1,277,298, still over, and **8 cm with a 0.8 keep ratio reads 1,241,166**; 10 cm
reached 1,224,205 for more changed pixels.

## Measured (published /1904/, 390x780, `light`) — `tools/qa_t3312_alley_corner.mjs`

Each stand renders the same held frame with the twins off and on and reads every pixel back;
the positive control hides every piece the test swaps, with no twin in its place.

| stand | off | on | pieces swapped | pixels changed | control (swapped hidden) |
|---|---:|---:|---:|---:|---:|
| **roof (60 m over the alley)** | **1,598,078** | **1,241,166** | 201 | 722 of 304,200 | 997 |
| front yards (32 m) | 423,999 | 423,999 | 43 (all out of view) | 0 | 0 |
| oblique, alley north (1.7 m) | 790,733 | 700,240 | 145 | 39 | 39 |
| rear alley south (1.7 m) | 1,000,647 | 931,767 | 296 | 0 | 0 |
| air, T-2992's (110 m), *not gated* | 1,823,232 | 1,543,358 | 393 | 101 | 178 |

Draw calls rise by 7-103 (a swapped piece leaves its coalesced run), against light's 7,800.
No page errors or failed requests. `roof-diff.jpg` is the roof stand's off frame with every
changed pixel in magenta (`QA_IMAGES=1` writes the off, on and diff frames as PNG), and
`roof-crop-off-on-diff.jpg` is one far house at 4x, off | on | diff: the changed pixels are the
hairline rims of the far mansard decks and cornices, moved by under a pixel, and the off and on
frames cannot be told apart.

Where nothing changes (front yards, rear alley) the swapped pieces are behind nearer walls or
out of the frustum; the triangles they save there are real (68,880 at the rear alley) and no
pixel can show it. The control does change pixels at the three stands where swapped pieces are
in view, so the comparison can see them.

Cost: 394 pieces in 1904 get a colour twin, 178,033 triangles and 245,154 vertices more in the
structure batches' buffers, cut in about 330 ms of main-thread time at load on the CI machine.

## Not settled here

- **The air stand is over `light` on dev already** (1,823,232; T-2992 brought it
  under 1,270,000, and the town has grown since). This change takes it to 1,543,358; the
  rest is its own ticket.
- The view filter (`view-occlusion.js`) reads its occluders once a frame inside the first
  batch's preparation, after that batch's swap, so a swapped piece of that batch occludes
  nothing in that frame. The filter stays conservative; the readings above are net of it.
