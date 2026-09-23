---
id: T-0197
title: Three of the fort image-accuracy table's eight rows were refuted in two days; audit the rest before building to them
state: done
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-28
pr: 439
claimed_by: run 8/27/2026, 11:31:47 PM CT
blocked_on: null
needs_bake: false
---

Three of the fort image-accuracy table's eight rows were refuted in two days; audit the
rest before building to them.

## What happened

`docs/RESEARCH/fort_dearborn_image_accuracy.md` compares the render against the two Fort
Dearborn plates, row by row, and it has seeded a run of tickets. In two days, **three of its
eight rows were struck as wrong** — each by a run that went and measured the plate instead
of looking at it:

| row | the claim | what measurement found |
|---|---|---|
| 3 | "Pickets are flat-topped and dark; the plate's are pointed and pale" | **wrong in both halves.** The archetype has built a sharpened head since it was written — 3,072 apexes over 768 posts, 0.312 m, 8.4 % of the picket — and `p4_0` rules the curtain's top FLAT, 0.45 px rms over 138 resolved columns, while resolving individual pickets at a 10 px pitch. A head of that proportion would have serrated the line by 3.6 px, eight times the residual. (T-0094) |
| 4 | "The corner works do not rise above the curtain with roofs and lanterns as the plate draws them" | **`p4_0` draws no work at either angle it shows.** Its two roofed, lanterned works stand at 0.435 and 0.521 of the wall — over the GATE. A corner work stands at 0.000 or 1.000. (T-0095) |
| 5 | "No gate is drawn in either documented wall" | **a gate has been drawn in both since the archetype was written** — though measuring it turned up a real defect nobody had claimed: both stood a quarter open, 0.90 m of a 3.6 m gateway, from a leaf built off a midpoint that collapsed onto its own jamb. (T-0095) |

Row 7 was closed properly by T-0097. **Rows 1, 2, 6 and 8 have never been measured.**

## Why the whole table is now suspect

The three struck rows share one method: **a person compared a lithograph to a render by
eye and wrote down the difference.** That method produced a claim that was exactly backwards
(row 3), a claim that mislocated the plate's most prominent structures by half a wall
(row 4), and a claim about something that had existed all along (row 5). Nothing about rows
1, 2, 6 and 8 was produced differently.

The cost is not hypothetical: row 3 became T-0094 and row 4 became half of T-0095, and both
runs spent their whole budget establishing that the ticket was wrong rather than improving
anything a visitor sees.

## What is still open, and what it is feeding

- **Row 1** — "no road anywhere on the reservation; both plates show a travelled way at the
  fort." Feeds the fort-approach work.
- **Row 2** — the bank track from the north gate to the water. Deferred to T-0004's bank,
  and carried by **T-0099**.
- **Row 6** — a flagstaff and flag over the fort, "the most conspicuous single feature of
  `p4_0`". Carried by **T-0096**, and already partly answered elsewhere: `exclusions.json`
  assigns that flagstaff to the FIRST fort. Note T-0095 found the plate's two tall works are
  ALSO first-fort signature (two blockhouses), which sharpens the question of how much of
  `p4_0` is the second fort at all.
- **Row 8** — "no trees at the fort; `p4_0` puts a tree mass east of the walls." Carried by
  **T-0098**.

## The larger question this raises

`p4_0` is a retrospective lithograph. T-0094 already established the principle that **a
tier-5 retrospective plate may refute a claim made about itself but may not hold a build
red** — its plate gate reports and does not gate. If a growing share of `p4_0`'s content is
first-fort, the table's framing — render versus plate, plate wins — is the wrong question,
and the right one is which fort each feature belongs to.

## Acceptance

- Rows 1, 2, 6 and 8 are each either **measured off the plate** the way rows 3-5 now have
  been, or struck with the reason they cannot be.
- Every ticket descending from an unmeasured row is re-read against the finding and
  corrected, withdrawn or confirmed — naming which.
- The table gains a header stating how a row must be established before it may seed a
  ticket, so the next reader does not repeat the method that produced three wrong rows.
- Where a feature is first-fort rather than second, that is recorded on the row rather than
  argued again in each ticket.
