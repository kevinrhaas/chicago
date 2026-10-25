# Glessner's 18th Street stand, and the walls behind its own walls (T-3152)

T-3146 left the desktop stand on 18th Street 45 m west and 32 m north of Glessner's centre
5,843 triangles inside Full's 4.6 M budget. On today's dev it is **over** it: 4,605,073 with
T-2227's filter on. The house's view pass is nearly whole there although the camera sees only
its north and west fronts. T-2227 hides a piece only when its whole box projects inside ONE
backing triangle, and Glessner's backing is cut into slivers.

## What the house offers

Glessner's walls are rock-faced granite relief (granite..granite_4, about 800,000 triangles,
none of 0.5 m²) over a flat **mortar backing**. The north front's backing is one plane, 2,318
triangles and 374 m², solid between its window rows. But its panels meet at T-junctions, so an
edge-matching outline cuts it into panel-sized pieces (1,628 unmatched edges, most of them seams
across solid wall). Single-triangle containment can't use it, and neither can a rectangle per plane:
the window rows cap every rectangle's height below a 4 m x 2 m cell's shadow.

## The change

`renderers/web/js/planar-occluders.js`, at load, for Glessner's double-sided opaque meshes only:

- each plane holding at least one 0.25 m² triangle and 16 m² in all is gathered (triangles
  more than 5 mm off it are left out);
- its OUTLINE is swept line by line (`boundarySegments`): every stretch of a triangle edge with
  a triangle beside it on one side only. A T-junction seam covered on both sides is interior;
  an opening, a crack or a fold is outline. One tolerance is spent: a T-junction vertex within
  **2 mm** of its line is taken as on it (the assets' int16 positions put such vertices up to
  about 1 mm off in the drawn mesh already);
- a 10 cm grid cell is PROVEN covered when its centre is in a triangle and no outline stretch
  meets the cell grown by 2 cm (connected, one covered point, no outline inside: inside the
  union). A summed-area table holds the proven cells.

`view-occlusion.js` `planeOccluded`, after T-2227's own test refuses a piece: the box must lie
wholly beyond the plane from the eye by 2 cm, every corner's sight line must cross the plane
beyond the near plane and at least 11.5° off grazing, and every cell under the bounds of the
box's shadow cast from the eye, grown by two pixels at the farthest crossing plus 5 mm and
2 cm (divided by the cosine), must be proven. Boxes crossing the viewport edge fail open, as
in T-2227. A cover stands only while every piece of its source mesh passes the backing's own
`active` test and the whole mesh's confidence range is opaque. The sun's pass, picking and
instance visibility are untouched.

46 planes, 356,287 proven cells, 3.0 MB of tables; about 0.5 s at load on this machine
(`planarCoverPlanes` over the master's 31 meshes; Full and Light only).

## Measured (published /1904/, Full, `node tools/qa_t3152_planar_covers.mjs`)

Covers off against on, T-2227's filter on both times, the same held frame:

| stand | viewport | covers off | covers on | pieces hidden by covers | pixels changed |
|---|---|---:|---:|---:|---:|
| **18th, 45 m W / 32 m N** | 1280x800 | 4,605,073 (over) | **4,473,480** | 568 (131,593 tris) | 1 of 1,024,000, 1 level |
| Prairie, 38 m E / 30 m S | 1280x800 | 4,505,684 | **4,385,268** | 410 (120,416) | 2 of 1,024,000 |
| 18th, 45 m W / 32 m N | 390x780 | 4,255,247 | **4,164,202** | 371 (91,045) | 1 of 304,200 |

Hiding Glessner changed 38,438-220,676 pixels at every stand (the positive control), and the
off/off repeat at the ticket stand changed none, so the comparison is deterministic.

The ticket stand's desktop row was read before `planarCoverPlanes` moved to numeric plane keys
(a speed change only: the master gives the same 46 planes and 356,287 cells either way). Its
re-read in the final build was cut off by the 600 s command limit.

**The changed pixels.** At the ticket stand it is one near-black pixel, (773, 352), going
(10, 9, 8) to (10, 9, 7). Halving the covers (`QA_BISECT=1`) traces it to one plane, the east
wing's inner wall at local x 41 m. It survives a 10 µm seam tolerance, so the 2 mm seam is not
the cause. Full's glass is `dark` (no transmission pass). It is the same class of difference
T-3012 accepted for T-2227 itself (3 pixels of 1,024,000 a few levels apart), and the QA gate
holds the covers to that bar: at most 4 pixels, none over 4 levels, every one listed.
**Unexplained, and stated here rather than hidden.**
