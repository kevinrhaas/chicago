# T-2371 — the 1812 Prairie coach house is not in the 18th Street pictures

T-2371 asked for the Wheeler coach house (`wheeler_house_1812_prairie_coach_house`, the K12
two-storey building on the alley behind 1812 Prairie) to be matched to four pictures, under
the image gate (AGENTS.md rule 11):

| picture (Prairie library id) | what it is |
|---|---|
| `a18-rba-taylor-9974-prairie-south-from-18th` | J. W. Taylor #9974, the photograph (754 × 600) |
| `st-flinn-1892-looking-south-prairie-from-18th` | the same negative as a halftone plate, Flinn 1892 (2000 × 1431) |
| `st-picturesque-chicago-1892-prairie-avenue-p199` | the same negative, *Picturesque Chicago* 1892, p. 199 |
| `st-ghm-postcard-1908-prairie-south-at-18th` | the same negative, coloured, on a postcard postmarked 1908 |

**All four are one photograph.** The trees, the branch that arches over the walk, the coping
posts and the two figures far down the walk are the same in every print; only the crop, the
screen and the colouring differ. The Flinn plate and the *Picturesque Chicago* plate reach
furthest to the right (west), where the coach house would have to be. The Taylor print and
the postcard are cut tighter there.

**None of them shows the coach house.** The photographer stands on the west walk of Prairie,
north of 18th Street, and looks south along it. On the right is the Glessner house: its 18th
Street (north) face seen nearly square on, and its Prairie face receding. Beyond it are the
fronts of 1808, 1812 and 1816. The coach house stands on the alley 33–55 m west of the
Prairie lot line and 34–43 m south of the 18th Street line, behind Glessner's west range. It falls
outside the print's right edge. Even where a wider crop could take it in, Glessner stands
between.

## How that was shown, without leaning on a camera solve

`sightlines.py` (run it from `chicago/4d/`) does not fit one camera. A solve on a halftone this
coarse is loose: the focal length that the Glessner corner implies runs from about 1300 to
6000 px depending on where the Prairie face is taken to end, behind a tree trunk. So the script
sweeps **every camera the plate allows** and asks of each one whether any part of the coach
house is both inside the print and in sight. What fixes those cameras, read on the Flinn plate
at 1:1:

- **the horizon, y 727**: where the two edges of the west walk meet (x 1032). Two readings
  of the edges, one from rows 820–950 and one from the walk's full run to y 1290, put that
  point at (1025, 728) and (1032, 727).
- **Glessner's NE corner, x 1422**: the arris where the dark north face meets the light,
  receding Prairie face. The foot of the north face there is at **y 855**.
- **the picture area, x 105–1780, y 75–1290.**
- the print is level: Glessner's corner and the downpipes are vertical.

For an eye H metres up, the corner's foot sitting 128 px under the horizon ties the camera's
distance north of Glessner to its focal length (depth = f·H / 128). The corner's x then places
the eye east of the face. Each (eye height, distance, principal point) is therefore one whole
camera. The sweep runs the eye from 1.2 to 2.5 m, the distance from 1 to 120 m north of
Glessner and the principal point from x 500 to 1400 px. It keeps the 3,555 cameras that put
the photographer on the west walk (u 49.5–62 m). Against each it projects 1,088 samples of the
coach house: every metre over the top and four sides of its committed GLB's bounding box,
which is 11.38 m high and larger than the building because it carries the yard.

The occluder is the weakest Glessner the record allows: its footprint polygon raised only to
the lowest eave its record states (the 18th Street cornice, 22.6 ft = 6.89 m), with **no
roofs**. Its ridges (34.1–45.7 ft) would only hide more. Keith (1808) and 1812 itself, which
also stand in the way, are left out.

```
sightlines: 1088 samples of the coach house (its GLB box u -0.90..20.78, up to 11.38 m), 3555 cameras on the west walk (eye 1.2..2.5 m, 1..120 m north of Glessner, principal x 500..1400 px, focal 51..12800 px)
sightlines: 206657 of 3867840 camera-sample pairs fall inside the print; 0 of those clear Glessner taken as a bare 6.89 m prism
sightlines: the nearest sample that would clear the bare prism lands 123 px beyond the print's right edge (eye 2.5 m, 34 m north of Glessner, principal x 1400, focal 1741 px); and that is with every roof of Glessner left off
sightlines: hidden — from every camera the plate allows, each sample of the coach house is outside the print or behind Glessner
```

`plan-sightlines.jpg` draws it for two of those cameras (focal 2000 and 5000 px, eye 1.6 m).
Each shows the print's two edges as rays. The coach house (red) lies west of the right-edge
ray, and Glessner's block lies across the line to it.

## What follows

- **No reference view is committed for the coach house from these pictures.** A camera in
  `data/reference_views/wheeler_house_1812_prairie_coach_house/` would also join these four
  pictures to the coach house's card (`tools/compile_pictures.py` joins a picture to whatever a
  reference view names). That would put four photographs of something else on it. The image
  gate has nothing to compare: the pictures say nothing about the coach house, for or against.
  T-2371 closes with `ticket.mjs done --anyway --why`, and the reason is written in the ticket.
- **These pictures are of the fronts.** They do show 1812's front, small and far down the
  row, and 1808's and Glessner's. The finding is added to T-1885, the ticket that finishes the
  1812 house against its pictures, so its run solves this negative too.
- The coach house's own picture, if one exists, would be an alley view. The library has none
  today.
