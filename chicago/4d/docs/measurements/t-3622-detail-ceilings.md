# T-3622 — the three scene-detail ceilings re-priced at desktop West prairie (2026-11-17)

The owner answered T-3622 with (a) on Manager's 4D Board: raise Full, Balanced and
Light by the standing rule (the reading plus T-0672's recorded margin for each
rung, rounded up to 5,000), so that nothing in the scene changes and dev's
desktop smoke part 5 goes green in one PR. The question priced (a) on dev
c8649f3cd (Light 1,270,000). The stand climbed past that before the answer could
land, so the same rule is applied here to the gate's own reading on the day.

## The priced reading: the gate (CI content build, desktop part 5)

Run 44005328098, job 133783569052, PR #2111 head 21e322489 (dev with one 1904
Prairie Avenue house, which no 1835 stand can see). PR #2125 at 3b25f122c and
PR #2129 at f01e96648 read the same figures at West prairie. #2125 is now on dev.

| tier | West prairie | margin | sum | new ceiling | old ceiling |
|---|---:|---:|---:|---:|---:|
| full | 3,584,847 (6806 calls) | 18,059 | 3,602,906 | **3,605,000** | 3,495,000 |
| balanced | 2,728,359 (6759 calls) | 16,806 | 2,745,165 | **2,750,000** | 2,675,000 |
| light | 1,287,071 (5157 calls) | 15,791 | 1,302,862 | **1,305,000** | 1,190,000 |

The phone (390x780) passed part 5 in the same build, inside the old ceilings.
Draw-call limits (7,800 general, Light's 90-call floor), reaches and shadow tiers
are unchanged. Light's raise is the fourth owner-authorized exception for the
floor (after T-2015, T-2035 and T-2339).

CI spread, all six stands (triangles):

| stand | full | balanced | light |
|---|---:|---:|---:|
| West prairie | 3,584,847 | 2,728,359 | 1,287,071 |
| Lake Street at Canal | 3,220,345 | 2,540,151 | 1,149,642 |
| Lake and Market | 2,837,293 | 2,274,747 | 826,638 |
| the forks, from Wolf Point | 2,757,480 | 2,221,876 | 1,092,502 |
| the Sauganash at 26 m | 2,026,577 | 1,616,064 | 624,103 |
| the open aerial | 2,010,471 | 1,590,015 | 579,757 |

## A second reading: `tools/measure_detail_ceilings.mjs --only desktop`, local

The published mirror of dev 23a783a02, read on the steward runner. Raw rows are in
`t-3622-detail-ceilings-desktop-local.json`.

| stand | full | balanced | light |
|---|---:|---:|---:|
| West prairie | 3,491,683 | 2,666,382 | 1,268,729 |
| Lake Street at Canal | 3,220,345 | 2,540,973 | 1,151,292 |
| Lake and Market | 2,837,293 | 2,274,747 | 826,638 |
| the forks, from Wolf Point | 2,622,147 | 2,167,720 | 1,083,673 |
| the Sauganash at 26 m | 2,035,051 | 1,656,554 | 626,764 |
| the open aerial | 2,010,471 | 1,590,015 | 579,757 |

The two instruments agree to the triangle at Lake and Market and the aerial, and
within about 1,700 at Lake at Canal. They differ at the three stands that look
onto the water: West prairie by 93,164 at Full, the forks by 135,333. T-3612's
schooners sail a circuit on the vessels layer's own clock (`vessels.js`), so a
stand that sees the river or the lake counts them wherever they happen to be
when the reading is taken. This is the likely cause, not a proven one. It means
West prairie's figure swings by tens of thousands between readings, which is
larger than any of the three margins. The ceilings are priced on CI's reading,
the higher of the two and the gate's own. A ceiling that has to hold against
sailing boats may want pricing at the boats' worst place on their circuit; that
is a follow-up, not part of this answer.
