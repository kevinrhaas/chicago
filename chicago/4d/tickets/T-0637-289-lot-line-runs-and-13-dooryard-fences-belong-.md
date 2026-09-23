---
id: T-0637
title: 289 lot-line runs and 13 dooryard fences belong to nobody: join every enclosure to the household or business whose ground it bounds
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 828
claimed_by: run 9/4/2026, 8:17:25 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:54:37.054Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33935464750
---

289 lot-line runs and 13 dooryard fences belong to nobody: join every enclosure to the
household or business whose ground it bounds.

**Filed on the owner's instruction of 2026-09-04**, which named *"enclosures"* among the
things the core dataset has to hold, alongside residents, families, households, businesses,
occupations and town composition.

## What is on the ground, and what it knows

`data/enclosures/` holds eight records:

| record | runs | `belongs_to` |
|---|---|---|
| `town_lot_line_rails.json` | 147 | **0** |
| `town_lot_line_boards.json` | 83 | **0** |
| `town_lot_line_pickets.json` | 59 | **0** |
| `town_dooryard_pickets.json` | 13 | **0** |
| `sauganash_yard.json` | 1 | 1 |
| `western_hotel_wagon_yard.json` | 2 | 2 |
| `estray_pen.json` | 1 | 0 |
| `fort_dearborn_apron.json` | — (4 bands) | — |

The three town-wide lot-line families are **generated from the lot grid**, which is the
right way to build them and the reason none of them knows whose fence it is. 289 runs of
fence and 13 dooryards stand in the town and not one can answer "whose?".

Two named yards can, because they were authored by hand against a building.

## Why it matters beyond tidiness

A household's yard is part of the household. When a visitor opens a card, the fence round
that house is one of the few things in the scene that says *somebody lives here and this is
theirs* — and it currently says nothing. It is also the join that lets the enclosure layer
answer questions the household layer already can: which trades kept a fenced yard, whether
a lot fronted or backed a street, where goods stood.

## Dependency, and it is real

This runs AFTER the address work. A run whose lot the household layer cannot name has
nothing to join to, and 20 of 825 households carry a real `lives_at` today. T-0632 writes
the addresses the crosswalks hold and T-0633 puts businesses on the ground; this joins the
fences to what those two placed. Taking it earlier means joining 289 runs to twenty houses.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. Every lot-line and dooryard run gains a `belongs_to` naming the household id, business
   or structure whose ground it bounds — or an explicit, recorded refusal saying why not
   (unplatted ground, a lot no household claims, a run bounding two lots).
2. The join is **derived, not authored**: it comes from the lot the run was generated
   against and the household/business the lot holds, so a re-generation reproduces it. Say
   in the record which side of the run the owner is on where a run divides two lots.
3. Counts stated: runs joined, runs refused and why, and how many households gained a
   fence.
4. `sauganash_yard` and `western_hotel_wagon_yard` keep the `belongs_to` they were authored
   with — the derivation agrees with them or the disagreement is reported, not silently
   overwritten.
5. Nothing in the scene moves. This ticket adds a relation; it does not re-site a fence.
