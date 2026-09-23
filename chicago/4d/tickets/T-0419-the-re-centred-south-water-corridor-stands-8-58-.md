---
id: T-0419
title: The re-centred South Water corridor stands 8.58 m off its own block faces, and the strip between belongs to neither
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: null
pr: 1240
claimed_by: run 9/13/2026, 3:28:25 AM CT
blocked_on: Is the platted BLOCK grid on the South Water reach offset from the control too — branch A, which re-cuts 32 lots carrying 53 committed roofs and drops blk_south_water_lasalle (8 lots, 18 roofs, all of T-0429) into the river — or is the drawn line the block grid's own control, branch B, in which case the corridor and the blocks answer two different questions and 10 corridor readers each declare which? Measured 2026-08-30, re-measured 2026-09-13: the abandoned band is 6,132 m2 and 99.1% dry, the band the corridor claims instead is 54.0% river, and branch A's price rose from 43 to 53 roofs in the fortnight the question waited. See docs/ROADMAP.md K30(f).
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34747491256
---

The re-centred South Water corridor stands 8.58 m off its own block faces, and the strip between belongs to neither.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by **T-0009** while carrying out the owner's ruling of 2026-08-29 — the platted corridor
is derived from the street CONTROL rather than from the drawn line. On `south_water` that
translates the corridor **+8.58 m** in northing. Its block faces do not move: they come from
`generate_plat_lots.block_edges`, which offsets the DRAWN line by the same 12.192 m half-module.

So on that reach the corridor's south edge now stands 8.58 m north of the block's north face,
and **a strip 8.58 m wide belongs to neither**. Under the drawn corridor the two abutted by
construction, which is what several gates assume.

**This is why T-0009 did not swap the module default.** Making `plat_corridors.corridors()`
answer the control-derived ring town-wide was tried and measured on 2026-08-29: five gates that
read a corridor edge AGAINST a block face or a frontage line went red on an otherwise clean tree
— the cross-street platted-face census in `reconcile_665.py` (34 faces → 0), the southern-ground
stations (`measure_south_bank_ground.py`), the block-parcel street-line assertions and their
self-tests, and the far-timber census. None of them is wrong; they are all reading a plat whose
two halves are now derived from different lines.

**The question, which is the owner's kind of question and not an agent's:** is the platted BLOCK
grid on that reach also offset from the control, in which case the lots move and every roof
standing on them moves with them — or is the drawn line the block grid's own control, in which
case the corridor and the blocks are answers to two different questions and the gates should say
which one they are asking?

**Acceptance:** the strip is measured on the ground rather than in the abstract (how many lots,
how many committed roofs, how much of it is dry); the fork above is put to the owner with what
each branch costs; nothing moves until he answers. **Do not "fix" this by moving the lot grid.**

**Links:** T-0009 · K30(e) in `docs/ROADMAP.md` · `tools/plat_corridors.py` ·
`tools/generate_plat_lots.py` · T-0421.

---

## MEASURED 2026-08-30, RE-MEASURED AND PUT TO THE OWNER 2026-09-13

`tools/measure_corridor_strip.py` (new, gated in `check.sh`, baseline in
`tools/corridor_strip_baseline.json`). **Nothing moved**: no street line, block, lot, structure
record, coordinate or confidence. The full write-up is `docs/ROADMAP.md` § K30(f).

**There are two bands, not one.** A rigid translation gives up exactly what it takes.

| band | area | dry | platted lots in it | footprints lapping |
|---|---|---|---|---|
| **abandoned** — in the DRAWN corridor, outside the control one | 6,132 m² | **99.1 %** | **0** | `hogan_store`, `newberry_dole_warehouse`, `lasalle_slough_crossing`, `slough_log_bridge` — all `research` |
| **claimed** — in the CONTROL corridor, outside the drawn one | 6,132 m² | **46.0 %** (3,281 m² is river) | **0** | `dearborn_street_drawbridge` |

Each is 33 % of the drawn corridor's own 18,403 m². Both cut 8.58 m at their widest — the
displacement and nothing else. A lot on this row is 43.83 m deep, so the abandoned band is **19.6 %
of a lot depth and cannot hold a lot** under either branch. Zero lots is measured as AREA: all
sixteen lots on the row *touch* the band along their frontage, and a contact test answered
"sixteen".

**THE FORK, WITH WHAT EACH BRANCH COSTS.**

**A — the block grid is offset from the control too, so the lots move with the corridor.** Priced by
re-deriving the grid through `generate_plat_lots` with the control-centred line as `block_edges`'
input: four blocks deepen 8.58 m, **32 lots re-cut**, **53 committed roofs stand on them** — and
**`blk_south_water_lasalle` leaves the grid** (19 blocks/144 lots → 18/136) because a corner then
falls on water. That block is **8 lots and 18 committed roofs**.

**B — the drawn line is the block grid's own control, so the corridor and the blocks answer two
different questions.** Nothing in `data/` moves; **10 modules** that read `plat_corridors` or
`block_edges` each declare which line they ask, and the five gates T-0009 measured red are re-read
rather than repaired.

**What the ground says, and it is an argument rather than a ruling.** The control-derived corridor
is **54.0 % river**. `data/streets/1835.json` already records that this line "is shifted into the
dry half of the platted riverfront corridor", 8.28 m perpendicular, "with 3.91 m to spare before
its south edge". A plat corridor half in the water with the built street drawn in its dry half is
consistent with both halves of the record — and the abandoned band is then the dry remainder of the
platted corridor, which is exactly where four documented buildings already stand. Under branch A
that reading has to be wrong, and a documented block goes into the river with it.

### What changed in the fourteen days the question waited

The first measurement was made on 2026-08-30 and never reached a PR. Re-run against dev today the
**geometry of the fork is identical** — same +8.58 m, same two 6,132 m² bands, same zero lots, same
18 blocks / 136 lots / 32 re-cut, same block lost — but **branch A's price is not**:

| | 2026-08-30 | 2026-09-13 |
|---|---|---|
| committed roofs on the 32 re-cut lots | 43 | **53** |
| committed roofs on the block branch A loses | 9 | **18** |
| the claimed band's dry share | 47.6 % | **46.0 %** |

T-0429 filled `blk_south_water_lasalle`'s headroom on 2026-09-05 (PR #597) — exactly what the queue
asked of it — so nine more documented roofs now stand where branch A puts water. The dry share fell
because nine shore and heightfield tickets (T-0686, T-0799, T-0939, T-1064, T-1065, T-1071, T-1072,
T-0795, T-0219) re-cut the 1834 field this band is sampled on. Neither is an error; together they
say that **branch A gets more expensive every run that builds on South Water**.

The ratchet caught the dry share and missed the roofs, because the snapshot pinned block and lot
counts and not the built town standing on them. `roofs_on_moved_blocks` and `roofs_on_lost_blocks`
are pinned from today.

**Nothing moves until the owner answers**, per this ticket's own acceptance.
