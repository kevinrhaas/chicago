# The stable's north slope is too long at the top: the ridge comes down, the pitch stands (T-3095)

T-3080 left a residual on the north slope of the stable's E-W ridge, over the alley end.
Both early prints count 41-44 courses between the eave and the foot of the ridge roll under
the cresting: the c. 1887 Cornell print 41.7-43.9, HABS photograph 1 (1963) 40.6-42.7. The
model lays about 50 there at HABS's 5 in. Every camera fitted on measured controls puts the
eave where the model has it. T-3094 asked which part of the roof carries the difference:
the ridge's height, its plan line, the plane's pitch, or the alley gable's coping. This is
the first piece of T-3094. The rebuild is **T-3096**.

**Acceptance, stated before the work:** put each candidate roof to the count, which does not
depend on any camera, and to the six measured-control cameras of T-2758, none of which was
fitted to a roof point. Rule which candidate gives the same ridge both ways. Then state the
rebuild's numbers and its acceptance before anything is built.

    python3 docs/RESEARCH/glessner-stable-ridge-T-3095/read_ridge.py   # readings.json, ridge-candidates.jpg

It uses T-3072's cameras, count edges and counts (`../glessner-roof-module-T-3072/`) and
T-2758's fits (`data/comparisons/glessner/stable-roof-heights.json`). Nothing is re-fitted or
re-picked. The model's plane is checked against the committed GLB's tile vertices (42.51°,
tile foot y 22.71 m z 7.65, tiled top y 17.96 z 12.01). The GLB is gitignored; to make it,
run `python3 tools/recover_glessner_v4.py --materialize`.

## 1. Three ways to shorten a plane whose eave is right

The eave is fixed by every camera, so the plane can only lose its 3-4 ft of extra slope at
the top. That can happen in three ways:

| | what moves | what stands |
|---|---|---|
| **A** | the ridge comes down the same plane, so it moves north | the pitch, 42.5° |
| **B** | the plane flattens about its eave and the ridge comes down | the ridge's plan line, S 14.6 (in line with the 18th Street range's ridge) |
| **C** | the plane steepens about its eave and the ridge moves north | the ridge's height |

For A and B, the ridge height comes out two ways at each counted column. The first is where
the family's own plane is just long enough for the print's count. The second is where each
camera's ray through the print's roll foot meets that family's plane. The roll's foot is put
0.09 m under the tiled top, where a 0.14 m roll (`roof_edges.cap_radius_m`) bears on the
slope. That offset moves every family alike.

## 2. The ruling: A

| family | tiled top from the count | tiled top from the six cameras | camera minus count (min / median / max) |
|---|---|---|---|
| model | 12.01 m (about 50 courses) | | |
| **A, pitch stands** | **11.23-11.51 m** | **11.06-11.82 m** | **-0.24 / -0.12 / +0.31 m** |
| B, plan line stands | 10.12-10.87 m (pitch 31°) | 11.32-11.90 m | +0.76 / +1.04 / +1.43 m |

(`readings.json`, three columns on each print, two Cornell fits and three HABS 1 fits.)

- **B fails.** To be short enough for the count, a plane pivoting on its eave under an
  unmoved ridge line has to fall to about 31°. Every camera then sees its ridge 0.8-1.4 m
  higher than the count allows.
- **C fails.** If the ridge keeps its height and the plane steepens enough for the count
  (52.5°, ridge at y 19.37), the ridge stands closer to the camera. It then projects 15-30 px
  *higher* than the model's, but both prints draw the roll's foot *below* the model's.
- **A is consistent.** The count and the cameras agree to a median of 0.12 m, within the
  spread between T-2758's fits of a single print (0.5 m between the two Cornell fits).

`ridge-candidates.jpg` draws each family's ridge at its count height. Left is Cornell
(roof_level fit), right is HABS 1 (doorway fit). Red is the model, magenta A, green B,
blue C. Only A lies along the roll's foot in both prints.

So the ridge's height and its plan line carry the residual together, and the plane's pitch
does not. At the median count, the tiled top stands at **y 18.66 m, z 11.36 m**: 0.65 m lower
and 0.70 m further north than the model's. In the record's terms,
`stable_roof_rework.cross_ridge` goes from 38.6 to **about 36.5 ft** over north grade, and
`cross_ridge_S` from 14.6 to **about 12.3**. (The tiled surface stands 0.245 m over the
record's roof line, which is read off the GLB.)

## 3. The alley gable's coping

The model's alley gable wall stops under its tiles: the granite's top is 11.82 m, below the
tiled top at 12.01. Both prints draw a stone coping standing proud along the rake, with its
apex up at the cresting. T-2758 read that apex through the two Cornell fits at 38.75-40.63 ft
(11.81-12.38 m) on the alley face. Under A, the apex stands 0.45-1.0 m over the tiled top. So
the coping does not come down with the ridge. It stays where the prints put it, at about the
wall's present apex, and stands proud over the lowered roof. The apex's plan reading
(S 14.9-16.7 on the alley face) comes from a camera whose rake lands 10-15 px west of the
print's on that face. It is left to the rebuild to re-read, and it does not rule against A:
a coping apex is not the ridge.

## 4. Not settled, and handed to T-3096

- **How far the change runs east.** The counted columns span the plane from the alley to
  about 4 m east of it. The E-W ridge runs on east to the cupola. The record's ridge line at
  S 14.6 also carries the 18th Street range's skewed junction (`masonry_house_v4_west_roof.py`,
  `ridge_skew`) and the cupola's seat (T-2758 reads the cupola centre at S 13.0-14.4). The
  rebuild has to keep the cupola on the crossing or rule where it moves.
- **The south slope.** The south slope of the same ridge runs to the courtyard eave at S 35.
  It steepens nowhere under A: it flattens from about 47° to about 41°. No camera here sees
  it, so the rebuild checks it against the courtyard records (habs04, sheet 4).
- **Its rival.** T-3065 (PR #1261) rebakes the same GLB and edits the same two match records.
  T-3096 follows it rather than racing it, so the bake happens once.

**T-3096's acceptance, stated now:** on the rebaked GLB, `read_slope.py` (T-3080) and this
script, run unchanged, must give 41-44 courses between the model's eave and its roll foot on
the plane over the alley end. The cameras' roll foot must sit within 0.3 m of the model's in
every measured fit. The eave must still land within 0.4 m. The alley gable's coping must
stand proud of the tiles to an apex within T-2758's 38.75-40.63 ft. The rebuild must not
make any other Glessner match record worse.

## 5. What changed

- Two match records (`cornell-northwest-west-windows`, `habs-01-northwest`): the T-3080
  residual item now carries this ruling. It stays **open** and is owned by T-3096.
- No geometry, camera or GLB changes. The record's ridge stays at 38.6 ft and S 14.6 until
  T-3096 rebuilds it.
