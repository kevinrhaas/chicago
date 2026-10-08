# T-2171 shoreline validation

Actual published /1812/ app, desktop 1280x800 full detail and mobile 390x780
light detail. Both loaded 21/21 structures, with zero page errors or failed
responses. `browser-validation.json` records camera positions, frame budgets
and four sampled terrain heights: the former lake notch is dry; the retained
river and adjacent lake are wet. Screenshots show the same generated shoreline
in the scene and overview map.

The 1812 scene retains one pre-existing tree diagnostic: it has no Wells Street
centreline, so trees retain their prior E316 limit. The scene index and tree
renderer are unchanged from dev b6aef1c7; this is not a shoreline regression.

The pinned Blender 4.5.3 terrain build measured maximum 6 mm deviation from the
heightfield over 210,897 independent rays, with zero misses. The terrain-spec
self-test asserts a monotone outer join, continuity and unchanged river-side
attachment, outlet and lower-spit trace vertices. The comparison and confidence
limits are in `../../RESEARCH/shore_1812_pre_cut.md` and L403.

Full repository and smoke results are recorded in the PR after their final run.
