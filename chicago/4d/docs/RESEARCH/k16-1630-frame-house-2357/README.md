# 1630 Prairie refined from the district draft to a whole K16 clapboard frame house (T-2357)

Piece 3 of T-1862 (1626, 1628 and 1630), split by house: 1628 is T-2355, 1626 T-2356, and this
is 1630, the register's *small earlier frame house*, which wanted a frame kit rather than K01's
brick. The draft T-2334 stood is refined **in place**: `house_1630_prairie` keeps its id, its
traced main-body rectangle (13.25 m deep, 5.5 m along Prairie) and its placement, and its
archetype changes from `prairie_draft` to `k16_timber`. The draft rules' `skip` names
`s20-1630-f`, so the draft builder stands no second building there, and the frontage row names
the house (`house_id`), so its stable keeps `house_1630_prairie_coach_house`.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1630-b1`, T-1840 census `s20-1630-f`: *'2BB frame
(yellow) dwelling (D) with a 1-storey frame piece at its Prairie face'*), through the draft's fit:
a two-storey frame main block, a two-storey wing standing 2.25 m out on its south side at the rear
(u 1.0-4.5, the draft's `r2`) and a one-storey piece across the whole front (1.5 m deep, the
draft's `r3`), built as the porch.

Built, all from the K16 kit (`data/components/prairie_1904/k16_timber.json`): clapboard laid
board by board on a water table over a 0.45 m foundation, every outside corner turned with its
pair of corner boards; K06 two-over-two sash in the kit's flat timber casing — three bays on the
front, three a storey on each long side, two on the rear, one a storey on each face of the wing;
a four-panel door at the north end of the front (the draft rules' entrance side); a deep frieze
under a boxed eave with scroll brackets round both blocks; a low 22° hip in weathered shingle on
the main block, a flat deck on the lower wing (eave 5.8 m against the main block's 6.4 m), one
brick stack on the ridge; the kit porch across the front — oiled floor, lattice skirt, chamfered
end posts with brackets, beaded ceiling — with three timber risers up to the door. Body paint a
fawn, trim cream, sash dark green. Liberty `L-k16-1630-frame-house-2357`; 1630 is retired from
`L-draft-prairie-16-18-west-2334` (its stable stays there).

## What the kit learned: a whole house

K16 (T-2322) built sample panels and T-2323 one street FRONT, standing against a plain stand-in
body. A small frame house wants every face closed in timber, so `generators/archetypes/
k16_timber.py` learned a second record layout, `frame_house` (`k16_timber_params.py` validates
it):

- **blocks** in the draft's own lot plan frame (u toward the street, v along it), so the record
  keeps the draft's position and rotation. Each block's walls run counter-clockwise from above;
  every wall is a kit `clapboard_wall` built in its own frame and set down on its side (`place`),
  turning its corner with a 0.3 m return that the next wall's cladding takes up from. A block
  standing `against` another is walled on its other three sides, its last wall ending on the
  wall it meets without a corner (`return_m` 0, new to `_clapboard_wall`).
- **doors** in a wall: `_cased_door`, a four-panel leaf at the casing's reveal, its stiles and
  rails flush and its panels sunk, the jambs and head lined, the casing's feet on the water
  table's drip cap and its head's drip cap ended on a clapboard butt line, as the windows' are.
- **roofs**: a hip over the eave rectangle, or a flat deck just over a lower block's eave.
- **the porch** on the front, as two mirrored kit halves, with timber **steps** (risers solved
  equal from the floor height) in front of the door; and one **stack**.

No other K16 bytes moved: the specimen and 1638's front rebuild byte-identical
(`k16_timber.py --check`, `k16_emit.py --check`); 1638's manifest entry carries the new code
hash. `tools/check_timber_kit.py` holds every wall and the porch of a whole house to the kit's
rules part by part — scale, laps, stagger, end grain, proud trim, timber classes, no doubled face,
costs, metric UVs — and its thickness rule now measures in a wall's own frame, so a wall turned
onto another side is held to the same 0.12-0.22 m. Two self-tests break the layout (a block whose
walls skip round it out of order; corners with no return) and both are refused.

## Before and after, the same stands (`tools/qa_k16_t2357.mjs`)

Actual published `/1904/` app; *before* is `dev` at b3a3c8679 (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique
from the south and north walks, rear (between the house and its stable), roof (the air). 0 page
errors and 0 failed requests on all four runs; every stand `withinBudget`. Frame times are
software GL on the runner, a relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 30.2 → 20.7 s | 26.2 → 26.4 MB | 95-122 → 95-122 (±0) | 1.749-3.089 M → 1.781-3.121 M (+32 k) | 2.32-4.31 → 2.36-4.42 s |
| phone before → after | 13.3 → 13.0 s | 26.2 → 26.3 MB | 63-104 → 63-104 (±0) | 349-551 k → 381-583 k (+32 k) | 0.58-0.84 → 0.63-0.88 s |

The master is 1.67 MB and the web derivative 0.20 MB (1628's K01 house is 0.94 MB). The house
batches into the scene's existing material draws, so it costs no draw call at either tier. K16
has no light derivative, so the phone's light tier draws the full house: +32 k triangles.
Load swings by seconds between runs on this runner and neither the fall nor a rise is a claim.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-before.json` (both
viewports) and `browser-validation-after-{desktop,mobile}.json`.

## Limits

- No photograph, plate or description of 1630 has been read; every form is the kit's.
- The roof is a choice, not a reading: the draft drew a 40° gable; this is a low hip, because the
  bracketed boxed eave runs round all four walls. A source showing a gable front replaces it.
- The porch has a post at each end only, the kit porch's; a long porch of the period may as well
  have had a middle post.
- No gutters or downpipes (a box gutter is taken to lie in the boxed eave); no rear door; no cellar
  lights.
