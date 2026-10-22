# T-2928: Glessner's court face between the bow and the stair tower, to HABS sheet 4

The last strip of `habs04-court-exterior`, left open by T-2926. Every reading comes off the native sheet-4 scan
(`prairie_1904_v1/research/public/glessner-habs-sheet-4.png`) on T-2228's section controls: north wall x 1165,
grade y 5858, 100.6 px/ft across and 97.7 px/ft up, the frame T-2925 and T-2926 read the rest of the face on.
Lines were found by pixel profiles across each edge (`line_profile.py`), not by eye, and are good to about
±0.03 ft. S is sheet 4's own, then the plan's after T-2879's +0.65 ft re-zero, which is what the record holds.
Heights are feet above north grade.

The method was checked against T-2926 first: profiled the same way, its lower lights over the underpass give
63.70 and 66.67 for the frame's outer lines and 12.1 and 15.5 for sill-course top and lintel-course foot, its
recorded 63.69-66.70 and 12.1-15.5. So an opening here is the frame's outer line to the stones.

`strip-native-over-render.jpg` is the drawing above the rebuilt render from the `habs04-court-exterior`
camera, at the camera's own scale, on one grid (`../glessner-court-face-T-2926/native_over_render.py`).

## The first-floor window

| | sheet 4 S | plan S | height |
|---|---|---|---|
| frame (opening) | 42.65-47.79 | 43.30-48.44 | 9.13-13.31 |
| glass, inside the frame | 43.01-47.50 | | 9.53-13.00, meeting rail 11.2-11.3 |
| lintel stone | 42.32-48.10 | 42.97-48.75 | 13.31-14.51 |
| sill stone | 42.35-48.12 | 43.00-48.77 | 8.39-9.13 |

Built before: 43.0-47.5 and 9.5-14.6 under a thin lintel of its own, so its head stood 1.3 ft above the drawn
one and its lintel stone was a fraction of the drawn one's 1.2-ft depth.

## The second-floor light

| | sheet 4 S | plan S | height |
|---|---|---|---|
| frame (opening) | 44.61-45.74 | 45.26-46.39 | 19.46-24.38 |
| head stone | 44.26-46.09 | 44.91-46.74 | 24.38-25.65 |
| sill stone | 44.26-46.06 | 44.91-46.71 | 18.73-19.46 |

One pane: no rail or bar crosses it. Built before: 44.9-46.7 and 19.5-25.6, a two-sash light 1.8 ft wide,
which is the head stone's width read as the light's.

The ticket that filed this strip gave the window as "about 9.6-14.2 under a lintel stone about 14.2-15.3" and
the light as "about 20.0-25.0 under a stone at 25.0-26.2". Those were estimates; the profiles above supersede
them. Both now stand on their drawn stones as `rough_course` bands, the lights carrying `"courses"` so they lay
none of their own, and the light carrying `"panes": 1`.

## The basement light's grille

Sheet 4 draws twelve bars at a 0.345-ft pitch (S46.84-50.63) across the light's full drawn width (frame
46.66-51.0), between rails at 2.86 and 4.64 ft. The built light stops 0.95 ft short of the drawn south jamb,
held off the plan's drum (T-2880), so it takes the drawn pitch rather than the drawn count: nine bars at
0.355 ft, the first 0.355 ft off the north jamb, where there were six. Its rails, at 0.12 and 0.88 of the light,
already fell on the drawn ones.

## The leader at S42.4

Sheet 4 draws no leader anywhere on the strip. The eave gutter runs at about 27.0-27.6 ft from the drum to the
bow trough's end, drawn end-on at S38.9-39.3. T-2228 had placed the court-east-north leader at S42.4 as a
clearance-driven reconstruction, not a reading. It is removed with its straps, and the strip's gutter is
recorded as draining into the bow trough (`rainwater_details.court_east_into_bow`), whose court-bow leader
(T-2939) takes the water. How the gutter passes its water into the trough is not drawn; both keep their end caps
as built, and the rainwater test now checks that a gutter feeding a trough ends against it, level with its floor.
