---
id: T-0459
title: Signboards are mounted over doors and windows, when the same wall has blank face to put them on
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-03
pr: 678
claimed_by: run 9/2/2026, 11:57:24 PM CT
blocked_on: null
needs_bake: false
---

Reported by the owner on 2026-08-31 from the dev preview: signs sit over doors
and over windows on walls that have blank face going spare. The Sauganash Hotel's
board is the one in the screenshot, over a window bay.

## Measured

`data/signage/town_business_signboards.json` holds **36 signs**. By mounting:

| mounting | count | flat on the wall? |
|---|---|---|
| `facade_painted` | 14 | **yes** |
| `wall_board` | 6 | **yes** |
| `bracket_board` | 8 | no — out on an arm |
| `awning_board` | 6 | no — on the hood |
| `post_board` | 2 | no — free-standing |

**Twenty signs are mounted flat against a facade.** Those are the ones that can
cover an opening, and every one of them carries a size and an anchor —
`board_w_m` 1.38–3.56, `board_h_m` 0.60–1.15, `anchor_local_enu_m`,
`arm_height_m` — so the geometry to place them well already exists.

## The cause

`tools/generate_business_signboards.py` mentions doors and windows sixteen times
and **not once as geometry**. Every mention is trade reasoning — *"lodging is
sold to arrivals who have to find the door"*, *"a name goes where it is seen
furthest"*, *"an office is a door among doors"*. The generator reasons carefully
about WHICH door a board belongs beside and has no idea where the openings are.

So a board is placed at a height and an offset that suit the trade, and whatever
is behind it is behind it.

## What the owner asked for, and it is a licence not just a constraint

Three moves are explicitly allowed, in this order of preference:

1. **Move it** — put the board on blank face on the same wall. Most facades have
   some.
2. **Reshape it** — the same copy on a **longer and narrower** board. A sign is
   text on a rectangle and the rectangle may be re-proportioned to fit the gap it
   is going into. Nothing in the sources fixes an aspect ratio.
3. **Shrink it and fix it to the door front** — a small board on the door itself,
   which is what a modest office took anyway.

**Acceptance:**

1. The generator gains the facade's openings as INPUT — door and window
   rectangles per wall — and a board is placed only where it covers none.
2. A sweep over all 36 signs reports, per sign, whether it covered an opening
   before and what was done: moved, reshaped, shrunk to the door, or already
   clear. The count is stated, not summarised.
3. Where reshaping is used, the copy is unchanged and only the rectangle moves —
   a board may be made longer and narrower to fit, and the lettering scales with
   it.
4. If a wall genuinely has no clear face, that is reported per building with the
   measurement, and the board goes to the door front rather than over glass.
   **No sign is left over an opening silently.**
5. An assertion fires when a board overlaps an opening, so this cannot come back.
   This is a visible-quality fault and the renderer smoke is where it belongs.
