# The lakefront east of Prairie Avenue, 1 July 1904 (T-2478, T-2479)

The owner asked (2026-10-13) for the train tracks east of Prairie Avenue, the ground and plants
around them, and "probably a beach shore similar to how we have in 1835", with any walkways or other
features, built to photographic quality. This note is what the sources say that ground was, where
they differ from that guess, and what the scene draws on each reading.

## What the sources say

| Question | Reading | Sources |
|---|---|---|
| Was there a beach? | **No.** In 1904 the lake met the railway's own built edge. The 1886 and 1911 maps draw the water's edge right against the tracks, the 1911 edge a straight built line 17-20 m east of the 1886 one (made ground, L287); the 1891 atlas draws the railway's breakwater offshore. A sand beach returned only with the Burnham Park fill of the 1920s, east of all of this. | `robinson_1886_chicago_plate_10`, `sanborn_1911_chicago_v3_sheet_20`, `sanborn_1911_chicago_v3_sheet_28`, `carlson_greeley_1891_prairie_environs` |
| How many tracks? | Four or five in 1891; about eleven at 18th Street on the 1911 sheets, fourteen or fifteen towards 16th Street where the yard widens to the station. George Glessner's photograph from 18th Street, a decade and more before 1904, already shows seven or more. The scene draws the 1911 layout: the nearest dated drawing after 1904, and the photograph says the yard was already wide. | the same, and `ghm_george_glessner_ic_train_18th` |
| What were they laid in? | **Cinders**, filled nearly to the tops of the ties, and the same dark ground trodden flat between the tracks. No lawn and no pale broken stone shows in either Glessner photograph. | `ghm_george_glessner_ic_train_18th`, `ghm_george_glessner_ic_train_foot_18th_c1888` |
| Plants? | No photograph read shows this reach in summer. Both Glessner views are bare or winter. Weeds on the edges of a railway's disturbed ground are what the scene draws, and they are reconstructed. | none |
| Walkways? | **None along the water.** The c. 1888 view east from the foot of 18th Street goes from the parkway trees and the stone curb straight onto the tracks, with a row of white posts on the far side before the lake. The 18th Street footbridge over the tracks dates from 1933 and is not drawn. | `ghm_george_glessner_ic_train_foot_18th_c1888` |
| What stood at the water? | The edge the railway built and kept against the lake: stone and timber. Its make-up at this reach is not read off any source yet; T-2479 builds it as a reconstruction (riprap on the 1:1.5 face, a timber cap over piles), with the made ground between the last track and the crest. | none yet |

## How the tracks are placed

`tools/trace_ic_tracks_1904.py` reads the rail pairs the Sanborn 1911 sheets 20 and 28 draw (the
georeferenced copies T-1250 fitted), in a frame that runs along the scene's waterline
(`shore_1904_ic_edge`, L287): s along it from its north end and d west of it. Each 10 m bin's rail
centres are clustered and voted against the bin's best-drawn track, the clusters are linked into
tracks, and the tracks are joined across the gap between the two sheets, carried past the edge of a
sheet that cuts the yard on a slant, or closed onto a neighbour as a ladder would. Every stretch is
recorded with how it was got (`segments[].how`), and a track more than half traced is `inferred`,
otherwise `reconstructed`. Stretches that would fall on the embankment's lakeward face are left off
and recorded (`left_off_embankment_face_s`). `--check` re-traces and compares; `--check-properties`
holds the committed file.

The cinder ground runs from the westernmost track plus 4 m to the easternmost less 3 m, smoothed, and
never into a block of the 1904 street grid (its west line is the lots' rear line, sheet 20's
`ic_row`). A 3 m verge of weeds lies outside it on each side.

## The lake edge (T-2479)

The tracer also finds, every 5 m along the shore, where the committed heightfield's lakeward face
(terrain_spec `ic_row_embankment`, 1 in 1.5) meets its grade (the crest: the first point inland
within 0.12 m of the grade 12-16 m behind it) and where it meets the water, and smooths both over
15 m either way. It writes the face from 1.5 m lakeward of the waterline to the crest
(`lake_edge.face`), the crest line the cap timber follows (`lake_edge.crest`), and the made ground
from the crest to the east verge (`right_of_way.made_ground`). The east verge keeps at least 0.6 m of
made ground inland of the crest and narrows (to a metre at least) where the tracks crowd the edge,
which they do north of 18th Street, where the scene's waterline is the 1886 planform moved east.

The renderer drapes a riprap map over the face, cut finely across so the face's curve over the crest
does not let the heightfield's grass show through, and stands single limestone blocks on it within
about 110 m of the eye (50 m on a phone). The cap is one mesh along the crest; the piles one
instanced draw. Everything about the edge's make-up is `docs/LIBERTIES.md` L-ic-lake-edge-2479.

## What is reconstructed

Everything about the section and the look: the 85-lb ASCE rail, standard gauge (inferred from the
period's trunk lines), 8-ft ties every 0.53 m with a hand-laid track's irregularity, the ballast
bed's width, the colour and grain of every map (`assets/textures/prairie_1904_rail/`), the weeds'
species, height and density. The track positions are 1911's standing in for 1904's. All of it is
`docs/LIBERTIES.md` L-ic-tracks-2478.

## What would settle it

- An Illinois Central track chart or valuation map of about 1904 for this reach would replace the
  1911 layout and give the rail weight.
- A dated summer photograph of the tracks between 16th and 22nd Street would settle the verges.
- A railway engineering report or city record of the shore protection here would give the edge's
  make-up (T-2479).
