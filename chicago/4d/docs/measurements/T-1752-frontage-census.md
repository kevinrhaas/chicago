# T-1752 — the frontage census follows its authored ground

Measured 2026-09-29 against `dev` at `308dcacf1117d78ba62896bbaea4bf067b081b77`.
The frontage layer last changed at `590ad4c3` and is unchanged by Glessner v4.
This assertion repair unblocks the visible Glessner parcel T-1730 under the
visible-progress rule's exemption 3. No scene geometry changes here.

## Independent historical comparison

The historical `data/frontage/town_street_edge.json` files were compared by walk
ID, fence chunk/lot set/path, and refusal subject/wall/clause. Renumbered fence
IDs were not counted as new fences. The four other frontage records contribute
eight walks, two crossings, two posts and ten refusals throughout. These are
therefore whole-layer totals, not fitted to a browser reading.

| Commit / ticket | Walks | Crossings | Posts | Fences | Refusals | Street-edge faces |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `d48666be` / T-1707 — old expectations | 47 | 39 | 18 | 31 | 121 | 36 |
| `c5242517` / T-1734 — Clinton lots transpose | 47 | 39 | 18 | 28 | 120 | 36 |
| `1b01e8b8` / T-1736 — Clark block improves | 48 | 40 | 18 | 29 | 122 | 37 |
| `b4c27fa6` / T-1708 — Wells block improves | 49 | 41 | 18 | 30 | 122 | 38 |
| `e63c9e30` / T-1735 — La Salle block improves | 50 | 44 | 18 | 31 | 120 | 39 |
| `590ad4c3` / T-1751 — Franklin block improves | 51 | 46 | 18 | 32 | 119 | 40 |

The ticket initially suggested that new walls retired two fences. Comparison
disproves that cause: T-1734 removes three fences because the lots now front
Clinton and Canal, and T-1736 adds one. `_fence_runs` accepts only lots whose
`tier` matches the face. The retired runs cover Clinton's former north lots
`[0,2,4,6]` and south lots `[1,3]`, `[7]`; south lot 5's unimproved-lot refusal
retires with that frontage too.

## Clauses that produce the changes

`generate_frontage_works.build_street_edge` asks whether a committed footprint
stands on each block. Four builds replace the unimproved-block refusal with
one north-face walk each: `blk_washington_clark_north_walk_1`,
`blk_washington_wells_north_walk_1`, `blk_washington_lasalle_north_walk_1` and
`blk_washington_franklin_north_walk_1`. Their opposite Randolph-block walks
earn four crossings over Washington. The three adjacent pairs along its south
side—Franklin–Wells, Wells–La Salle and La Salle–Clark—earn three more. La Salle
also removes the written refusal of the 147.7 m Wells–Clark gap. Market and
Dearborn remain empty, with their block refusals intact.

Each new face earns one fence. Clark covers lot 4 at 5.50 m setback; Wells and
La Salle cover `[0,2,4,6]` at 4.50 m; Franklin covers `[0,2,4,6]` at 4.99 m.
All exceed the unchanged 3.0 m rule. Clark's other north lots 0, 2 and 6 stay
unimproved and acquire three written refusals. Residential buildings earn no
new hitching posts. These clauses explain every refusal delta in the table:
`-1, +2, 0, -2, -1`, leaving 119.

## Independent mesh arithmetic

`frontage.js` gives each named walk run one moving chunk, reuses it for its
crossings, and groups standing fences/posts by street. The records have 43
named moving chunks, ten unnamed river-polyline segments (three east, seven
west), four standing streets (South Water, Lake, Randolph, Washington), and
one shared mesh: **43 + 10 + 4 + 1 = 58**. Optional lettering remains separate,
so the existing conditional becomes 59/58. Camera-dependent far-merge artifacts
remain uncounted and their allowed-name assertion is unchanged.

## Verification

`python3 tools/generate_frontage_works.py --check` re-derived all five records
byte for byte: 97 walk/crossing runs, 32 fences, 18 posts and 119 refusals. No
generator, record, mesh, refusal clause or geometric tolerance changes. Only
seven independently established numeric constants move; every other smoke
condition remains. The walk-length, fence and deck floors stay 3050 m, 31 and
232. A source comparison stripping standalone comments confirms that these seven
constants are the only executable changes.

Published mobile parts 1–2 pass **158/0 in 2 m 50 s**, with zero page errors,
on `sha256:001a8c5194069f6e`; `tools/dev-smoke-state.json` records that tree. The
full non-browser gate, `CHECK_JOBS=2 bash tools/check.sh`, passes **708 steps,
none red**. The remaining browser parts were not rerun on this isolated census
repair.
