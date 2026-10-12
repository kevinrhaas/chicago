# 1609 and 1611 Prairie, the lost frame pair, refined from the district draft to two K16 clapboard houses on one party wall (T-1867)

Package N08 of T-1837 (1609, 1611 and the 1607 association). The district draft (T-2335) stood the
pair Robinson 1886 plate 10 draws on lot 6 as two plain gabled boxes; this refines both **in place**:
`house_1609_prairie` and `house_1611_prairie` keep their ids, their traced main-body rectangles
(10.5 m deep; 4.75 m and 5.25 m along Prairie) and their placement, and their archetype changes from
`prairie_draft` to `k16_timber`. The draft rules' `skip` names `r1886-1609-f` and `r1886-1611-f`, so
the draft builder stands no second building there.

## What the pair is

The census (T-1840, frontage-20-024, `backcast_1886`) stands the pair for 1904 on the supplied expert
guidance: the 1911 sheet draws the four-storey loft at 1607-1611 in its place, and the register's
brief is a *pre-1911 paired frame house* — 'party-wall relationship to 1611, modest frame facade,
timber cornice, sash windows and bounded roof/stoop', 1611 with an 'independent door/window pattern'.

Read: each half's plan and the line the plate draws between them (the party wall), and frame
construction from the plate's yellow. Built, all from the K16 kit
(`data/components/prairie_1904/k16_timber.json`):

- clapboard laid board by board on a water table over a 0.45 m foundation, corner boards at the
  pair's four outer corners and none at the party line;
- K06 two-over-two sash in the kit's flat timber casing — **1609**: a door and one window below,
  two windows above on the front, three a storey on its north side, one a storey at the rear;
  **1611**: a door and two windows below, three above on the front, three a storey on its south
  side, two a storey at the rear;
- a four-panel door at each house's outer end (the draft's entrance sides), each under a small kit
  porch with timber steps (the register's 'bounded stoop');
- the register's 'timber cornice' as the kit's deep frieze under a bracketed boxed eave at 6.4 m,
  running across both fronts as one; a flat roof behind it in tar-and-gravel grey (the draft drew
  a 40-degree gable); two brick stacks side by side at the party wall;
- one pale stone-grey body paint on both halves, with the kit's cream trim and dark green sash.

Liberty `L-k16-1609-1611-frame-pair-1867`; both houses are retired from
`L-draft-prairie-16-18-east-2335`.

**1607 is not a house.** '1607-1611' is the address range of the 1910 E. T. Cade loft (four storeys,
brick; demolished 1942) that replaced the pair; it is not back-projected, and no 1904 building stands
under 1607. Parcel `prairie_1607` carries the pair.

**Pictures (rule 11).** None of the pair. The Prairie library was searched by address and by
building id on 2026-10-12: its one 1609 picture, `a16-cgy-1609-loft-1910` (chicagology, after 1910),
shows the loft that replaced the pair. So this ticket has no `## Image gate`; a picture that turns
up later opens one.

## What the kit learned: a party wall

`frame_house` closed a free-standing house: its first block walled on all four sides. A pair wants
neither half to build the wall they share, so the record may now name a `party_wall` — the side and
the house `with` it — and its first block stands `against` that side
(`generators/archetypes/k16_timber_params.py`). Everything else was already the kit's: a block that
stands against a side is walled on its other three, its first wall starting at that side without a
corner and its last ending on it without one, and its eave and roof stop on the line. So the two
fronts, rears and cornices run on into each other with no doubled wall, and no other K16 byte moved
(`k16_emit.py --check`, `check_timber_kit.py --check`: 1638's front, 1630, 1609 and 1611 all held to
the kit's rules part by part).

## Before and after, the same stands (`tools/qa_k16_t1867.mjs`)

Actual published `/1904/` app; *before* is `dev` at 5951d7799 (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique from
the north and south walks, rear (the lots behind), roof (the air). 0 page errors and 0 failed
requests on every run; every stand `withinBudget`. Frame times are software GL on the runner, a
relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 31.1 → 29.7 s | 31.7 → 31.8 MB | 109-157 → 110-157 | 1.751-1.946 M → 1.779-1.974 M (+28 k) | 1.94-3.19 → 2.00-2.81 s |
| phone before → after | 15.5 → 14.4 s | 31.7 → 31.8 MB | 77-118 → 78-118 | 370-558 k → 398-586 k (+28 k) | 0.47-0.97 → 0.50-0.84 s |

The masters are 0.75 MB (1609) and 0.83 MB (1611); the web derivatives 0.10 and 0.11 MB. The pair
costs one draw call at the closest stand and none at the others. K16 has no light derivative, so the
phone's light tier draws the full houses. Load swings by seconds between runs on this runner and
neither direction is a claim.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-before.json` (both viewports)
and `browser-validation-after-{desktop,mobile}.json`.

## Limits

- No picture or description of either house has been read; every form but the plans is the kit's.
- The roof is a choice, not a reading: a flat deck behind the cornice, where the draft drew a gable.
  A source showing the pair's roof replaces it.
- The pair wears one paint; separately owned halves may well have differed.
- No gutters or downpipes, no rear doors, sheds or porches, no cellar lights.
