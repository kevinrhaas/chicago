---
id: T-0183
title: The Market and South Water corner needs one control point, and the node rule may not be able to make it
state: done
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-31
pr: 573
claimed_by: run 8/29/2026, 6:42:06 PM CT
blocked_on: null
needs_bake: false
---

The Market and South Water corner needs one control point, and the node rule may not be
able to make it.

Found by **T-0163**, which split the two street-control refusals apart and measured them.
`blk_south_water_market` — north South Water, south Lake, west Market, east Franklin — is
the one that is genuinely waiting: `tools/measure_block_gating.py` carries South Water
toward it over **25 m with 0 of 5 samples wet**. Dry ground, real block, 27 roofs of
headroom behind it, and the largest single unlock left that street control can actually
deliver.

**The block is well attested.** The post office stood at the **southwest corner of Franklin
Street and South Water Street** from 2 Nov 1832 to 3 Mar 1837, which puts it there on the
scene date (`docs/research/03-structures-north.md`) — so South Water and Franklin met, and
the block between Market and Franklin fronting South Water is not in doubt.

## What is missing

One control point, at **Market × South Water**. The committed set
(`data/traces/street_control.json`) holds exactly four:

| point | streets |
|---|---|
| `lake_canal` | Lake × Canal |
| `lake_market` | Lake × Market |
| `randolph_canal` | Randolph × Canal |
| `kinzie_canal` | Kinzie × Canal |

**None of them is on South Water Street at all.** Market's committed centreline runs from
the data box at N -400 north to `lake_market` and stops there — at its only control point,
where Lake crosses it. It is not carried the further ~110 m north to South Water, because
there is nothing to carry it to.

## Why this may be harder than adding a row to a file

The project's `node_rule` makes a junction from "the set of nodes SHARED BY THE TWO NAMED
SURFACE ROADWAYS", averaged. Market's modern successor is **North Upper Wacker Drive** and
South Water's is **East Upper Wacker Drive** — and around the forks those are plausibly the
SAME carriageway changing name at a bend, not two roadways that cross. If so there is no
shared-node pair to average and the rule cannot produce this point as written.

**This is stated as the thing to check, not as a finding.** It was not verified: deriving
control needs the network (`tools/refetch_control.py --discover`), which is on-demand and
deliberately outside `tools/check.sh`. The `lake_market` note already warns that Market's
successor is "three stacked streets ... and only the top one is the plat's", so whoever
takes this should expect the same care there.

If the rule genuinely cannot make the point, that is a decision about the rule and belongs
with the owner rather than in a steward run: a bend node is not a crossing, and adopting one
would widen what counts as control for every future placement.

## Acceptance

Either a control point at Market × South Water is derived under a rule this project will
accept — recorded in `data/traces/street_control.json` with its OSM node ids and the rule it
was made under, Market's centreline carried north to it, and `blk_south_water_market`
building in `tools/generate_plat_lots.py` with its 27 roofs moving out of the West and South
balances into a real block — or the reason the rule cannot make it is recorded on the block
and on `node_rule`, and the owner is asked the one question that would settle it.

`tools/measure_block_gating.py` must keep passing either way: if the block starts building,
it leaves the refusal list and the gate stops measuring it.

---

## WHAT WAS FOUND — 2026-08-27. The rule cannot make the point, and it does not say so.

The check this ticket asked for was run, against today's OpenStreetMap, and it reproduces:

    python3 tools/refetch_control.py --discover market_south_water    # exits 1

`--discover` learned two things in this slice. It can now read a junction out of the new
`refused_control` section of `data/traces/street_control.json` — entries with the `osm_ways`
and the search centre but deliberately **no coordinate**, because a refused junction has no
committed position — and it now compares the set it discovers against the control already in
the file and refuses one it recognises.

### The reading

| | |
|---|---|
| named ways | `North Upper Wacker Drive` × `West Upper Wacker Drive` |
| shared surface-roadway nodes | **2** — `28358888`, `28358944` |
| mean | E 447161.86, N 4637285.38 — local **(89.16, −110.42)** |
| spread | 17.68 m |
| and that is | **`lake_market`**, already committed, to the id and to the centimetre |

The way geometry says why. North Upper Wacker's northernmost way (`931237154`) **ends** at
node `28358944`; West Upper Wacker's first way (`319358162`) **begins** at it and runs
north-east to E 447213.3, N 4637344.7; its other carriageway (`319358170`) comes back down to
`28358888`. The two arms are one carriageway pair changing name through a **bend at the Lake
Street junction** — not two streets crossing at South Water. The ticket guessed exactly this
("plausibly the SAME carriageway changing name at a bend") and it is now measured rather than
suspected.

### The part that was not anticipated, and is the actual finding

**The rule does not fail loudly — it returns a wrong answer that looks right.** Two nodes, a
17.68 m spread, a clean mean: the same shape `lake_market` itself has. Committed,
`market_south_water` would have stood **on Lake Street, 110 m south of the corner it names**,
and `blk_south_water_market` would have been generated with no depth at all. Nothing in the
old output said "bend". That guard is what the tool change buys, and it is why the refusal is
recorded as an entry rather than left as an absence.

### Why there is no crossing to find

Not because the modern city lost the corner — because it lost the **street**. Wacker Drive
only reaches South Water's platted line (about local N +5 to +11) at Franklin, 120 m east of
Market; west of Franklin it turns south-west onto the Lake and Market corner. That is also why
`data/streets/1835.json` already describes South Water's west approach as following *"the dry
south bank resolved by the committed heightfield"*: the modern control was never there to
follow. **The 24 m gap at Market is a question about the 1834 sheets and the bank, not about
OpenStreetMap.**

### One thing the errand did find, and did not adopt

The same extract and the same rule read **`West Upper Wacker Drive` × `North Franklin Street`**
as a clean two-node crossing: `28358941` (E 447281.12, N 4637399.57) and `28358883`
(E 447281.20, N 4637414.85), mean E 447281.16, N 4637407.21, spread 15.28 m, local
**(208.46, +11.41)** — 6.4 m north of Franklin's committed north end, and the corner the first
post office stood on from 2 Nov 1832 to 3 Mar 1837. It would be this dataset's **first control
point anywhere on South Water Street**. Measured here, recorded in `refused_control`'s
`not_the_same_as`, and deliberately **not** adopted: committing it re-derives placements, and
it does nothing for this block, whose gap is at the west end. Filed as its own ticket.

### Where it was recorded

- `data/traces/street_control.json` — `node_rule` gains the bend failure mode; new
  `refused_control.market_south_water` holds the reading, the verdict and the question; the
  `streets` table gains `south_water`, so a street a refusal names resolves.
- `tools/refetch_control.py` — `--discover` reads refusals, tolerates a missing committed
  coordinate, and exits 1 on a set already committed under another name.
- `tools/reconcile_665.py` → `data/reconstruction/1835_665_roof_programme.json` — the block's
  `waiting_on` now says what it is really waiting on.
- `docs/RESEARCH/thompson_plat_grid.md` § 6.1.

### The one question, and it is not the one this ticket opened with

The ticket expected to ask *"may a bend node be control?"*. That question is answered by
measurement and the answer is no — a bend node here is not a looser kind of control, it is a
point 110 m wrong. What is left is genuinely the owner's, because either answer sets a
precedent for every block after this one:

> **`blk_south_water_market` has 27 roofs of headroom on measured dry ground and no
> derivable control at its west corner. Should South Water Street's committed west end be
> CLOSED onto Market's corridor from the 1834 sheets and the committed bank — the same basis
> the rest of that curve already stands on, graded for what it is — or should its 27 roofs
> stop being scheduled as gated on street control and go back to the South balance, the way
> `blk_south_water_clinton`'s did when T-0163 measured them?**

`tools/measure_block_gating.py` still passes: nothing here moved a street line, so the block
is still classified `awaiting_control` and still measures dry.

---

## THE OWNER'S RULING, 2026-08-29

Asked whether to close South Water's west end on Market's corridor or to un-gate the
block's roofs to the South balance, the owner chose:

> **Close the west end on Market's corridor, from the 1834 sheets and the committed bank
> — the same basis the rest of that curve already stands on — and grade it for what it is.**

So `blk_south_water_market`'s **27 roofs of headroom on measured dry ground** become
schedulable: the single largest block of headroom left in the programme, and T-0365
measured that it and T-0009's four blocks were the whole of it.

**"Graded for what it is" is the load-bearing half of the ruling.** This end is NOT
derived control and must not be recorded as though it were. The node rule's refusal
stands — `tools/refetch_control.py --discover market_south_water` refuses it, correctly,
and that refusal is not to be softened to make this pass. What the ruling authorises is a
DIFFERENT basis, stated as such: the 1834 sheets plus the committed bank, which is what
the rest of this curve already rests on. The grade must make a reader able to tell this
corner from a corner that has a control point, and the position note must say the node
rule refused it and why.

**Acceptance for the run that takes this:**

- South Water's committed west end is closed on Market's corridor, derived from the 1834
  sheets and the committed bank, with the derivation written where the position is.
- The record grades it for its actual basis and NAMES the refusal: no derivable control
  at that corner, bend not crossing, nearest nodes 110 m away (measured 2026-08-27).
- `tools/refetch_control.py --discover market_south_water` still refuses. If a run finds
  itself editing that refusal to make this pass, it has taken the wrong path and stops.
- The block's 27 roofs are confirmed schedulable, or the reason they are not is recorded.
- A liberty entry, because a closed end on a non-control basis is a stated liberty.

---

## THE OWNER'S SECOND RULING, 2026-08-30 — THE 27 ROOFS GO BACK TO THE SOUTH BALANCE

PR #573 carried out the 2026-08-29 ruling faithfully and the ground refused it:
closing South Water's west end onto Market emits `blk_south_water_market` as a
**bowtie** (corridors overlap Lake's by 14.9 m), and carried as far north as the
committed waterline allows the block has **2.8 m of depth at Market against the
24.384 m one platted lot fronts**. That is the South Branch pinching the block
out, not a drawing error, and it is the right answer to have come back with.

Put the measured third option to the owner, he chose:

> **Return the 27 roofs to the South balance**, the way `blk_south_water_clinton`'s
> went back when T-0163 measured it.

**The wedge is NOT built.** Building it would mean re-deriving a committed
centreline up to 34 m north onto the waterline with no clearance and re-scoring
every gate that reads it — a large disturbance to a committed line for a block
2.8 m deep. Declined.

**What this settles and what it does not.** It settles where the 27 roofs go: to
the South balance, to be dealt onto ground that can carry them. It does NOT say
the plat was wrong to emit the block — the Thompson plat put a block there and
the river takes it away, and both facts stay on the record.
`generate_plat_lots.py`'s new refusal (a block whose rows have crossed) STAYS,
and `check.sh` goes on firing it: the refusal is the finding, and a later run
must not delete it to tidy the output.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The 27 roofs are returned to the South balance, and the reconciliation ledger
  shows the move with `blk_south_water_clinton`'s precedent cited.
- `blk_south_water_market` is recorded as a block the ground cannot carry, with
  the 2.8 m and the 14.9 m overlap on the record, and stops being scheduled.
- The crossed-rows refusal in `generate_plat_lots.py` and its `check.sh` step
  both REMAIN. A run that removes either has removed the evidence.
- The 665-roof total does not change — these roofs move, they are not lost. If a
  run finds the total must move, it says so with its reason.

---

## THE OWNER'S RULING, 2026-08-31 — the corridor EDGE, not the centreline

Two runs carried out the 2026-08-29 ruling and answered it differently. Both are
on the record; the owner ruled for **PR #573**, which is merged. **PR #577 is
closed unmerged**, and its work is sound — it answers a question that was put and
declined, rather than being wrong in its own terms.

**The question.** A platted corridor is 24.384 m. Put its **north edge** on the
committed bank and `blk_south_water_market` is a wedge with **2.8 m** of depth at
Market. Put its **centreline** on the bank — so the north half, 12.192 m of
platted street, hangs over the South Branch — and the block builds **8 lots,
4,957 m2, 107.0 m of frontage**. The whole difference between the two answers is
one half-corridor.

**Why the edge.** Three things, measured rather than preferred:

1. **The committed street does not overhang anywhere it can be checked.** Against
   the waterline at five eastings, `south_water`'s north corridor edge is south
   of the water every time — 22.0 m clear at E 100, 15.4 m at E 110, 8.3 m at
   E 120, and **0.2 m at Franklin**. Twenty centimetres is not a coincidence; it
   is the edge rule already in force. PR #577's case rested on this street
   already overhanging east of Franklin, and that could not be reproduced.
2. **The rule is committed as executing code, not as prose.** `generate_plat_lots.py`
   computes `headroom = (waterline - 2 * half_width) - (lake_n + half_width)` —
   north edge on the waterline, south edge a full width below — and its self-test
   runs in `tools/check.sh` on every commit. Re-run on 2026-08-31: *waterline at
   local N -71.0, leaving 2.8 m*.
3. **The two errors are not symmetrical.** The centreline reading puts eight
   buildings on ground the committed heightfield calls river. The edge reading
   leaves ground unbuilt that might be buildable. This project grades every
   invention it makes; a town smaller than the evidence allows is a cost it can
   carry, and a town standing in the water is not.

**This is falsifiable and is left that way.** The self-test fails loudly if the
headroom ever exceeds a lot's frontage — `THE GROUND HAS CHANGED` — so better
bank evidence reopens the block by itself. Nothing here needs to be remembered
for that to happen.

**What follows, and it is a real loss.** T-0365 called these **27 roofs** the
largest unblocked headroom left in the anonymous-block programme. They are not on
the ground: `blk_south_water_market` tapers to nothing at Market. Any queue
ranking that still counts them is counting a wedge.

