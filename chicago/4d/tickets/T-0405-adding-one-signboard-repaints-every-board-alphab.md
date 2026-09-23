---
id: T-0405
title: Adding one signboard repaints every board alphabetically after it, and some lose a line
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-12
pr: 1177
claimed_by: run 9/12/2026, 1:25:03 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T06:55:14.822Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34677897940
---

**Measured on T-0263's own diff, 2026-08-29.** One board was added to the town —
`frederick_thomas_shop`, on South Water Street east of Dearborn, because the
American settled its trade. `tools/generate_business_signboards.py` then rewrote
**eleven other boards** that have nothing to do with it, all over the town:

| board | mounting before → after | what the board says |
|---|---|---|
| `goss_cobb_saddlery` | wall → awning | loses `Lake & Canal Streets` |
| `h_jones_store` | awning → facade painted | unchanged |
| `hogan_store` | bracket → wall | **gains** `Merchants / Chicago—Illinois` |
| `madore_beaubien_house` | wall → awning | unchanged |
| `miller_house` | awning → facade painted | unchanged |
| `peck_store` | facade painted → bracket | loses `South Water Street` |
| `philo_carpenter_log_shop` | wall → awning | `Drugs and Medicines` → `Druggist` |
| `pruyne_kimball_drugstore` | wall → awning | loses `South Water Street` |
| `robert_kinzie_store` | awning → facade painted | unchanged |
| `sauganash_hotel` | awning → bracket | unchanged |
| `thomas_church_store` | facade painted → bracket | unchanged |

**The cause is a global cycle walked in a global order, not a local rule.** The
mountings are dealt from `MOUNTING_CYCLE` as the generator walks the selected
frontages, and the walk is in structure-id order. `frederick_thomas_shop` sorts
under `f`, so **every board from `g` onward advanced one position in its cycle**
— which is exactly the set above, and exactly nothing before it. The docstring's
stated intent is LOCAL: *"assigned so that no two boards within `NEIGHBOUR_M` of
each other share a mounting, a style or a ground colour"*. A rule that only has
to separate neighbours does not have to renumber the whole town to admit one
frontage in the middle of the alphabet.

**Why it matters beyond churn.** The mounting decides how many lines a board has
room for (`room < 3` drops the `place` line and swaps `trade` for
`trade_short`), so a reshuffle silently changes WHAT BOARDS SAY. Peck's board
stopped naming South Water Street, and Pruyne & Kimball's stopped naming it, for
no reason connected to Peck or to Pruyne. Carpenter's log shop stopped saying
`Drugs and Medicines` — the 1833 wording T-0130 chose for that specific shop to
distinguish it from his South Water store — and now says `Druggist`, which is the
other shop's line. Those are wording decisions the table argues case by case,
undone by an unrelated insertion.

It is also a review hazard: it puts ~190 lines of unrelated diff into every PR
that adds a storefront, which is where a real regression hides.

**Acceptance:**

- Adding one board to the middle of the set changes THAT board and any board
  whose `NEIGHBOUR_M` separation actually required a different deal — and no
  others. Demonstrate with the `frederick_thomas_shop` insertion re-run against
  its parent commit: the diff names the new board and, if any, the neighbours,
  with the separation that forced each one.
- The neighbour separation the docstring promises still holds afterwards, and is
  asserted rather than assumed.
- Any board whose wording changes as a consequence has that change argued in
  `SIGN_WORDING`'s own `why`, not produced by a shifted cycle.
- `tools/check.sh` re-derives the record byte for byte, as now.

---

## Resolved — the deal is a function of the board's own id (2026-09-12)

`build_record` dealt each frontage its cycle entry point from a counter walked down its
trade class in id order. It now takes it from `_rank(sid, len(cycle))` — the same stable
per-id device the STYLE preference order has always used — so a board's entry point is a
function of its own structure id and of nothing else. The de-confliction loop is
untouched and is now the ONLY thing that can move a board off that point; it reads the
signs already placed, so it reaches a board when, and only when, a new board lands within
`NEIGHBOUR_M` of it.

**Acceptance, answered in order.**

1. *Adding one board changes that board and any board whose separation required it.*
   The ticket's own case, re-measured by withholding `frederick_thomas_shop` and
   re-deriving the town without it:

   | | boards re-dealt by the insertion | furthest |
   |---|---|---|
   | before | 11 | 904.4 m |
   | after | 1 — `john_holbrook_store` | 17.2 m |

   And the same test over every board, not just that one (`--prove-locality`, which
   withholds each of the 34 in turn):

   | | consequences | outside `NEIGHBOUR_M` | furthest |
   |---|---|---|---|
   | before | 109 | 103 | 1,162.8 m |
   | after | 3 | 0 | 38.4 m |

   The three that remain are `frederick_thomas_shop` → `john_holbrook_store` at 17.2 m,
   `carpenter_south_water_store` → `h_jones_store` at 36.8 m and
   `chicago_democrat_office` → `harmon_loomis_store` at 38.4 m — neighbours, which is
   what the rule is about.

2. *The separation is asserted rather than assumed.* `_neighbours_differ` runs on every
   build and REFUSES TO BUILD on any pair inside `NEIGHBOUR_M` that shares a mounting, a
   style or a ground colour. One exception is permitted and it is named in the record
   rather than hidden: a class whose cycle is a single mounting — the `works` cycle is
   `["facade_painted"]`, because a works paints its front and hangs nothing at all, so
   `dole_warehouse_south` and `mason_blacksmith_shop` at 16.8 m cannot differ and the
   record says so. The pairs are written to `rule.separation`, and the assertion was
   proved by breaking it: forcing two neighbours onto one mounting, and onto one style,
   each fires.

3. *Any wording change is argued, not produced by a shifted cycle.* Six boards letter
   differently for the one-off re-deal, and every one of them is a tier of its own
   `SIGN_WORDING` entry with the reason on the board's own record: three now letter the
   FULL entry (`carpenter_south_water_store` regains "Wholesale & Retail Druggist /
   South Water Street", `harmon_loomis_store` regains "& Hardware",
   `john_holbrook_store` regains "Wholesale & Retail"), and three letter the short tier
   with `_sign_wording`'s own sentence naming the line dropped and why —
   `chicago_democrat_office`, `frederick_thomas_shop`, `peck_store`.

   The hazard the ticket names is now refused outright instead of argued case by case.
   `_wordings_differ` rejects a build in which any two boards letter the same thing —
   which is exactly what a shortening can do to two entries the table deliberately words
   apart. T-0130's case is the one it is written for: Carpenter's log shop is worded
   "Drugs and Medicines" and his South Water store "Wholesale & Retail Druggist" to tell
   the two shops of one druggist apart, and BOTH shorten to "Druggist". It fires when
   forced.

4. *`tools/check.sh` re-derives byte for byte.* It does, and it gained a step: the
   locality proof runs in the gate (~4 s) so the claim cannot rot. CHECK PASS, 313 steps.

**The one-off cost, stated rather than buried:** 17 of the 34 boards hang differently and
6 letter differently, once, because the deal was re-dealt. No board was added or removed,
no style changed, and the mounting mix is no narrower than it was (facade 13→10, bracket
8→9, wall 5→8, awning 7→5, post 1→2).
