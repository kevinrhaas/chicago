# T-3656 — owner-authorized Full allowance (18 November 2026)

The owner authorized “You can raise the budget as appropriate” and “So you can
merge to dev” after the desktop renderer reported a small Full-detail overage.

Published desktop run [44372747109](https://github.com/kevinrhaas/chicago/actions/runs/44372747109),
job 135043671104, implementation commit `6c83e8cf9558c0d6f9ffb422f299764837fc4ed2`,
measured **3,607,087 triangles and 6,813 draw calls** at the 1835 West prairie stand.
The existing Full ceiling was 3,605,000; the 7,800 draw-call limit passed. The run
later reached its 150-minute cap during stage 12, so it is not a complete smoke pass.

Apply the standing T-0672 pricing rule used by [T-3622](t-3622-detail-ceilings.md):

| Reading | Standing margin | Sum | Rounded up to 5,000 |
|---:|---:|---:|---:|
| 3,607,087 | 18,059 | 3,625,146 | **3,630,000** |

This is a 25,000-triangle (0.69%) increase in the declared Full allowance, with
22,913 triangles above the observed reading. Balanced remains 2,750,000; Light
remains 1,305,000. Draw-call limits, shadow policies, reach, inspection-specific
allowances and scene assets are unchanged. The independent policy test still
rejects an unapproved one-triangle increase and changes to the other policies.

Classroom commits `6c83e8cf9` and `45b35a2c7` do not change assets, data or generators
from base `169af6421`; the classroom code adds no 3D geometry. T-3622 recorded a
93,164-triangle spread between two Full readings at West prairie. Sailing vessels
on their own clock are a likely cause, not a proven attribution or a measured
worst-case bound. This allowance prices the observed maximum with the established
margin; a fresh stage 5 run must still exercise all stands and all three tiers.

The later DEV roof update in `169404c9f` changes only two 1904 houses (+31 and
−104 GLB triangles). Neither exists in 1835, so it cannot explain or repair this
West prairie reading. Source CI, the uncompleted renderer coverage and the fresh
budget check remain required before the DEV merge; this permission does not turn
incomplete runs into passes. No production promotion is authorized here.
