# K14 compared beside a newer neighbour: 1708 Prairie at its own age (T-2365)

Piece 2 of T-2361 (K14, T-2325). T-2364 found that every house now on the 1600 block (K01)
already stood in 1886, so the newer neighbour had to wait for 1708 Prairie, an empty lot on the
1886 plate, to stand on K01 (T-1872, PR #1988). This piece names the K14 condition kit on it and
shows it beside 1808 Prairie (built 1886, T-2358) in the actual published 1904 app.

**Acceptance (stated before working):** 1708's record names the K14 kit with a completion year
the evidence allows; its GLB is rebaked from that record; in the published `/1904/` app, in one
session (so one sun, one sky, one exposure), 1708 and 1808 are each shown front and oblique at
desktop 1280x800 and mobile 390x780 with zero page errors, every 1708 stand within the scene
budget, and the costs read off the frame; 1708's two reference views are re-rendered from the
new GLB and still match their pictures (the image gate).

## The completion year: 1901, a bound

- **After 1886.** Robinson's 1886 atlas, plate 10 (`robinson_1886_chicago_plate_10`), read
  through its committed fit (`data/traces/gcp/robinson_1886_plate_10_gcps.json`, 4.54 m RMS),
  draws lot 1708 empty between the stone-fronted mansion at 1700-1706 and the house at 1712
  (T-2364's finding, recorded on T-2361).
- **By 1901.** The Glessner House Museum's photograph of 1700-1706 under construction in the
  summer of 1901 (`glessner_blog_1700_1706_construction_1901_photo`; T-3212 solved its camera)
  shows 1708's canted bay, hooded door and railing standing finished at its left edge.

Nothing held narrows the fifteen years between. The kit is evaluated at the later bound, the
youngest the evidence allows, as 1608's was at its plate's: 1904 - 1901 = 3 years, so
a = 3 / 40 = 0.075, inside the kit's own "new work" band (a = 0 to 0.1). The weathering shown is
therefore a floor; any year from 1887 to 1900 would darken it, to 1808's 0.45 at most. Recorded as
`L-k14-1708-newer-2365`.

## What changed in the GLB

`_TONE` (the kit's grey multiplier on the vertex) in the web tier, min / mean:

| material | before (K03 full-age masks) | after (K14 at 1901) | 1808 (K14 at 1886) |
|---|---|---|---|
| `brick` (common brick side and rear walls) | 0.74 / 0.917 | 0.98 / 0.996 | 0.883 / 0.992 |
| `brick_front` (rough red-brown front) | 0.80 / 0.982 | 0.985 / 0.999 | — |
| `brick_unit_*` (the bond's unit bodies) | 0.866 / ~0.96 | 1.0 / 1.0 | 1.0 / 1.0 |
| `limestone_trim` | untoned | 0.977 / 0.998 | 0.86 / 0.993 |
| `rough_stone_trim`, `bay_stone` | untoned | 0.976 / ~0.997 | 0.93 / ~0.99 |

The brick unit bodies drop their K03 tone because a kit house tones the panel its brick is laid
in (T-3244), as on 1808 and 1608; the stone dressings take the kit's dressed-trim response, as on
1608. GLB bytes: full 3,757,412 -> 3,777,224 (+19.8 KB, the tone channel on the dressings); web
3,223,652 -> 3,212,272 (-11.4 KB). Triangles and draw calls are unchanged by the kit (it adds no
fabric; the readings below differ only by what streamed in).

## Beside 1808, in the published app

`tools/qa_k14_t2365.mjs` (after `tools/publish.sh`). Stands are in each house's own footprint
frame: 1708's front face is u = 12.8; 1808's refined footprint puts its front at u = 34.7 now,
so T-2358's stands were moved with it. Frame times are this machine's software GL, a relative
reading, not a device claim.

| viewport | state | stand | triangles | draw calls | frame ms (median of 5) | within budget |
|---|---|---|---|---|---|---|
| desktop | after | 1708-front | 1,360,968 | 1,311 | 6977 | yes |
| desktop | after | 1708-oblique | 1,886,427 | 1,728 | 7895 | yes |
| desktop | after | 1808-front | 4,018,472 | 1,828 | 13348 | yes |
| desktop | after | 1808-oblique | 4,770,737 | 2,486 | 14656 | no: over the near budget (4.7 M), within the far budget (6.67 M) |
| mobile | after | 1708-front | 430,439 | 997 | 1865 | yes |
| mobile | after | 1708-oblique | 516,271 | 1,656 | 2020 | yes |
| mobile | after | 1808-front | 863,792 | 1,649 | 3015 | yes |
| mobile | after | 1808-oblique | 857,600 | 1,766 | 3245 | yes |
| desktop | before | 1708-front | 1,316,328 | 1,255 | 7039 | yes |
| desktop | before | 1708-oblique | 1,879,174 | 1,714 | 7958 | yes |

Zero page errors and zero failed requests at both viewports; the one `problems` line in every
stand is the Fort Dearborn monument's review annotation, which says itself that it does not block
release. **The 1808 desktop oblique's 4.77 M triangles are not this change's:** 1808 is untouched
here, and the stand looks up the 1800 block toward its densest houses at full detail. It is
recorded, not gated, by this script; every 1708 stand is gated.

Pictures: `desktop-*.jpg`, `mobile-*.jpg`, `before-desktop-1708-*.jpg`, and `comparison.jpg`
(1708 before and after, its oblique, and 1808 beside it). At street distance the difference is a
shade, as it should be for a three-year-old front: the K03 mask's dark foot and sill streaks are
gone from 1708, while 1808's stone keeps its eighteen years.

## The image gate

Both of 1708's reference views were re-rendered from the rebaked GLB
(`node tools/photo_match.mjs data/reference_views/house_1708_prairie/<view>.json`) and looked at
again. Every recorded difference stands as it was; one is added to each record, the walls'
weathering, `within tolerance`: the prints show a new, evenly toned front, and the front brick's
grey level through the Christmas print's camera is unchanged (49.9 before and after over a
70 x 30 px patch between the upper windows), so T-3244's colour ruling stands. Both verdicts are
`matches`; `node tools/image_gate.mjs --ticket` passes for T-2365.

## Not changed: the kit's `status` line

`data/components/prairie_1904/k14_condition.json` still says the kit is built to on two houses'
walls and that the newer neighbour waits on T-1872. Its prose is part of every K01 house's
resolved-params input hash, so editing that one sentence read 60 committed GLBs as stale under
`validate.py --stale` (measured here, then reverted). The houses that name the kit are the records
themselves (`grep -l k14_condition.json data/structures/*.json`: 1608, 1708, 1808); refreshing the
sentence belongs with the next change that rebakes the K01 town anyway.

## Rights

`glessner_blog_1700_1706_construction_1901_photo` is held with its rights pending (a permission
request is out: `rights-requests/ghm-george-glessner-2026-10.md`). The condition takes one fact
from it, that 1708 stood finished in the summer of 1901, and no shape, colour or texture. The
attribute is banked in `tools/rights_derivation_baseline.json` beside 1708's other
attribute already banked on the same photograph (its front brick's colour), not sole support (the 1886 plate is the
other bound). If the request is refused, the later bound falls back to 1904 (the T-1840 census
and the 1911 sheet), which makes the front younger still, a = 0.
