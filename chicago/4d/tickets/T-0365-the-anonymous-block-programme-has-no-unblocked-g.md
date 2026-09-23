---
id: T-0365
title: The anonymous-block programme has no unblocked ground left: every block with headroom is on the South Water reach T-0009 holds open
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 581
claimed_by: run 8/29/2026, 9:18:05 PM CT
blocked_on: null
needs_bake: false
---
The anonymous-block programme has no unblocked ground left: every block with headroom is on the South Water reach T-0009 holds open.

Filed by **T-0317** as its successor, which is T-0028's programme rule — *one run, one
demonstration, one successor* — and this is the run where the succession has nothing to hand on.

**What was re-derived on 2026-08-29**, after `blk_randolph_market` took its second deal and went
`at_capacity` (`tools/reconcile_665.py`). Every platted block still carrying headroom:

| block | state | headroom | free lots | what holds it |
|---|---|---|---|---|
| `blk_south_water_franklin` | open | 4 | 2 | the South Water street line, **T-0009**, `blocked-owner` |
| `blk_south_water_lasalle` | open | 8 | 3 | the same |
| `blk_south_water_clark` | open | 4 | 2 | the same |
| `blk_south_water_dearborn` | open | 4 | 2 | the same |
| `blk_south_water_market` | gated | 27 | 8 | **T-0183**, `blocked-owner` — Market x South Water is a bend in Wacker Drive, not a crossing, and the node rule cannot derive a control point |

That is the whole of it. `blk_south_water_clinton` is `not_a_block` and no trace will ever join it
(T-0163), and every other platted block in the schedule is `at_capacity`.

**Why the four `open` ones are not simply workable.** They front the reach whose committed street
line is the open question in T-0009, and **T-0143 and T-0188 each refused to tighten a party-line
row against a line that may move**. That refusal is not a preference — a run stands ON the face,
so a face that moves moves the whole row, and the metres would be re-derived rather than corrected.
T-0317 inherited that refusal and did not reopen it.

**So this is a fork for the owner, not a missing number** (AGENTS.md § RECONSTRUCTED IS A TIER
draws that line, and it puts committed street CONTROL on the owner's side of it). The options, in
the shape the two blocking tickets already state them:

1. **Answer T-0009** — commit the South Water street line as it stands, and the four `open` blocks
   carry 20 roofs of headroom between them the next morning.
2. **Answer T-0183** — settle the Market x South Water control point, and `blk_south_water_market`
   alone carries 27 roofs on ground already measured dry (`tools/measure_block_gating.py`: South
   Water is 25 m away, 0 of 5 samples wet).
3. **Neither yet** — and then the programme's next visible ground is the CORE DENSITY standard on
   blocks that already stand (the T-0079 -> T-0105 -> T-0143 -> T-0188 line), which is a different
   programme with a different acceptance, not this one's successor.

**Acceptance:** the owner picks one of the three, or names a fourth. If it is (1) or (2), this
ticket closes by filing the next `open the block` ticket against the ground that unblocks. If it
is (3), it closes by recording that T-0028's programme is complete for the ground the project
holds, and the succession stops rather than being handed on to a block that cannot be built.

**Links:** T-0028 (the programme) - T-0317 (the run that filed this) - T-0009 - T-0183 - T-0163 -
T-0143 - T-0188 - `tools/reconcile_665.py` - `tools/measure_block_gating.py`.

---

## HOW THE FORK WAS ANSWERED — re-derived 2026-08-30, and this ticket closes on it

**The owner took option 1.** T-0009 closed on 2026-08-29 (PR #567) with the sentence this ticket
was waiting for: the drawn South Water line **does not move**. The corridor was re-derived from
committed control — `south_water` is `recentred` by +8.58 m, `lake`/`market`/`randolph` are
`centred` inside a centimetre, `canal` disagrees by 2.33 m and is filed as T-0421 — and
`data/streets/1835.json` was not touched. So T-0143's and T-0188's refusal to tighten a row
against a line that may move is **discharged** for this reach, and T-0317's inherited refusal
with it.

**He also took option 2, and the ground refused it.** He ruled on 2026-08-29 that Market x South
Water be closed from the 1834 sheets and this project's own bank. Executed on the line as
committed, T-0183 (PR #573) measured what comes out: South Water has converged on Lake Street
before it reaches Market and the two platted corridors overlap by 14.9 m, so the closure emits
`blk_south_water_market` as a bowtie; carried as far north as the committed waterline allows, the
block has **2.8 m of depth at Market against the 24.384 m one platted lot fronts**. The 27 roofs
this ticket's table credited to that block **are not on that ground**. They stay in the South
balance, the block stays `gated`, and what to do with the wedge is back with the owner. This
ticket therefore hands on NO successor for option 2 — filing one would be filing against ground
that has been measured away.

**The table, re-derived today** (`tools/reconcile_665.py` on this branch, regenerating
`data/reconstruction/1835_665_roof_programme.json` byte-identical to what dev already carries —
so these are dev's own figures, not this run's):

| block | state | headroom | free lots | what holds it now |
|---|---|---|---|---|
| `blk_south_water_lasalle` | open | 8 | 3 | **nothing** — T-0429 |
| `blk_south_water_franklin` | open | 4 | 2 | **nothing** — T-0430 |
| `blk_south_water_clark` | open | 4 | 2 | **nothing** — T-0431 |
| `blk_south_water_dearborn` | open | 4 | 2 | **nothing** — T-0432 |
| `blk_south_water_market` | gated | 27 | 8 | T-0183 — the wedge, `blocked-owner` |

`coverage.schedulable_on_committed_ground` reads **20** against 296 gated on coverage, which is
the same 20 the four rows above carry. Every other platted block in the schedule is `at_capacity`,
`reserved` (the Public Square) or `not_a_block` (`blk_south_water_clinton`, T-0163) — unchanged
from this ticket's original derivation.

## THE SUCCESSION, WHICH IS WHAT THIS TICKET CLOSES BY FILING

T-0009 filed **T-0420** for all four blocks at once. That is one ticket carrying four
demonstrations, and T-0028's programme rule is *one run, one demonstration, one successor* — its
own body says so ("Take ONE block per run … four blocks is four runs"), which makes it an L in an
M's clothing: any run claiming it could finish a quarter of it and would have to leave it claimed
and open, the exact failure `tickets/README.md § A claim is only real once its PR merges` records
costing seventy minutes on T-0062. So T-0420 is **split** into one ticket per block —
**T-0429 / T-0430 / T-0431 / T-0432** — each one run, each carrying its own re-derived headroom
table, each `needs_bake: true` because it deals roofs. The children took T-0420's exact place in
QUEUE; nothing was re-ranked.

**The programme's runway, stated so the next run does not re-derive it:** four runs of committed
ground, 20 roofs. After them the anonymous-block programme has nothing left on ground this project
holds — the market wedge is with the owner, and the 296 remaining roofs are gated on terrain,
hydrology and street control reaching them, not on recipes. That is option 3's answer arriving one
programme-length later than this ticket offered it, and the run that closes the last of the four
is the one that should record it.
