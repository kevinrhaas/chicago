# T-2344 — 1612 Prairie (Goodman) refined from the district draft on the K01 frontage kit

Piece 1 of T-1860. The district draft's `goodman_house_1612_prairie` (T-2334) is replaced IN
PLACE, under the same id, by a `k01_frontage` record; the draft builder now skips `s20-1612-f`
(`data/components/prairie_1904/draft_prairie_1904.json`), so no draft copy stands beside it, and
the frontage row names the house so its stable keeps `goodman_house_1612_prairie_coach_house`
(unchanged, byte for byte).

## What the house is built on

| | read from | tier |
|---|---|---|
| outline: one 19.8 x 11.25 m rectangle round trace `s20fp-1612-b1` (220.5 m2) — the front house, its north wing and the two-storey rear wing (`s20-1612-a1`) | Sanborn 1911 sheet 20, read in the lot frame at 0.5 m cells | inferred |
| two storeys over a basement, the half storey an attic in the roof ('2½B', the T-1840 census re-reading) | sheet 20 | attested |
| brick with a stone (blue) Prairie front | sheet 20 | attested |
| Italianate stone front: smooth ashlar, common-brick returns, paired windows, arched columned entrance, high stoop, bracketed cornice, basement lights | T-1837 register frontage-20-004 / pa-1612-1 (not a source record) | reconstructed |
| every height, opening, the roof (32-degree tin hip with a street dormer), chimneys, rainwater, stone kind, brick colour, trim | the K01-K10 kits, inside RECONSTRUCTION-RULES ranges | reconstructed |

Liberty: `L-k01-1612-goodman-2344`; 1612's front is retired from `L-draft-prairie-16-18-west-2334`.

## Not built, and why

- The register's **segmental** window heads: a K01 wall cuts a rectangular hole and K09 lays no
  segmental ring on one, so the heads are flat under K09 hoods.
- The census's **small frame porch on the south wall** and the **one-storey brick piece** behind
  the wing's north half: K01 builds one rectangle; an attached range is T-2343's to teach it.
- The rectangle **closes a 7.0 x 2.25 m court** the trace leaves at the north-west corner.
- The **north corner's quoins**: the K02 corner bond on a K01 front returns at the south corner
  only (written for 1808, whose north corner meets Glessner).
- Found on the way: the K05 roof union this kit dresses its caps on refuses most pitches for this
  plan ("the ridge … does not part two covering planes"): of 25-42 degrees with 0.30-0.45 m eaves,
  only 32/0.45, 32/0.38 and 36/0.38 built. 32 was taken; the slates are cut for 45 and up, so the
  roof is seamed tin.

## Before and after, the same stands (`tools/qa_k01_t2344.mjs`)

Actual published `/1904/` app; desktop 1280x800 at full detail, mobile 390x780 at light. The
stands are written in the refined footprint frame, and the `before` run shifts them by the
origin's move (2.0 m west, 0.5 m south), so each pair is shot from the same spot. Frame times are
software GL on the runner — a relative reading, not a device claim. JS heap is Chromium's
`usedJSHeapSize`.

| | load to ready | JS heap | draws | triangles | frame (median of 5) |
|---|---|---|---|---|---|
| desktop before (draft) | 26.7 s | 645-646 MB | 49-51 | 1.415-1.426 M | 2.3-3.5 s |
| desktop after (K01) | 34.4 s | 657-658 MB | 66-68 | 1.479-1.491 M | 2.6-3.4 s |
| mobile before (draft) | 13.1 s | 209-225 MB | 19-21 | 94-101 k | 0.61-0.78 s |
| mobile after (K01) | 13.9 s | 218-237 MB | 36-38 | 158-166 k | 0.75-0.90 s |

Every stand is inside the scene budget (`withinBudget: true`) at both viewports, with no page
error and no failed request. The assembly's web GLB is 1.76 MB (the draft's was 37 kB; 1808's
K01 is 2.02 MB). The K01 kit has no light derivative yet, so the light tier draws the full
assembly: about +64 k triangles, +17 draws and +10 MB of heap on the phone profile — the cost the
next K01 refinements on this block should be measured against.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-{before,after}-{desktop,mobile}.json`.
