# T-2759 — Glessner's bow terrace terminal and its coping join

The open item (T-2228 `terrace-post-join`): seen from the west, the model's coping and
brick cheek ran on in front of the rounded terminal post and hid its shaft, while HABS
sheet 4 (section A-A, looking east) draws the post whole from grade to crown with the
coping dying into its north side. Photograph 5 (c. 1923 court view) shows the same
arrangement; its rights are `check_required`, so it is a qualitative cross-check here and
nothing is measured or derived from it.

## What the plan says

`fit_plan_post.py` fits a circle to the ink of the terminal on sheet 2 (native scan,
calibrated on the printed 161 ft 3 in × 74 ft envelope, 37.25 px/ft):

    centre W33.81 / S46.20   radius 0.93 ft at the line's centre (0.88 inner edge, 0.99 outer)

The centre repeats T-2218's own plan pick (W33.73 / S46.20). `plan_wall_radii.py` reads the
wall's two lines about the terrace centre W27.8 / S28.8 band by band: inner 17.55–17.65 ft,
outer 18.65–18.75 ft, on the circle all the way into the post (the model's 17.6 / 18.8).

So on the plan the post is not centred in the wall band. It sits 0.25 ft outward of the
band's centre and stands about 0.6 ft proud of the wall's outer face. T-2218 had moved it to
S46.05 with a 0.75 ft radius to fit the section. That put the whole post inside the band's
end-on silhouette, so every west view lost the shaft.
`plan-terminal-overlay-before.jpg` shows the model's old post (cyan) against the plan's ring.

## What changed

- The post is built at the plan's reading: W33.81 / S46.20, radius 0.9 ft. Crown height
  5.1 ft and rise 0.75 ft are unchanged; both are section readings.
- The three reconstructed lower tread ends (T-2218's obscured turn) are re-seated on the new
  surface, 0.04 ft inside it as before, along their own tread lines. The inner ends and the
  seven measured upper boundaries are untouched.
- The coping's traced section profile is untouched. Past the traced end, the
  reconstructed shoulder now enters the post at its north side, at about 4.45 ft. That is
  just above the crown's springing (4.35 ft), where sheet 4 and photograph 5 both put the
  junction.

`terminal-sheet4-before-after.jpg` shows sheet 4, then the render before, then the render
after.

## What stays open

The two sheets put the junction at different points along S. Sheet 4 ends the coping at
S45.35 and shows 1.22 ft of clear shaft (S45.35–46.57). Built from the plan, the junction
lands at about S46.4–46.6, with about 0.5 ft of clear shaft and the post's south face at
S47.1. The same pair of sheets already disagrees by 0.63 ft the other way at the stair
tower (plan S56.10, section S56.73: T-2228 `section-controls.json`), so there is no
uniform datum shift to apply. The plan governs plan positions here, because the stair
boundaries are plan readings. The difference is recorded, not hidden.
