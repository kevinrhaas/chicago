---
id: T-0241
title: Washington gets the street edge
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0191
opened: 2026-08-27
closed: 2026-08-27
pr: 423
claimed_by: run 8/27/2026, 6:18:01 PM CT
blocked_on: null
needs_bake: false
---

Washington gets the street edge.

Piece 2 of 2 of **T-0191 — Randolph and Washington get the street edge**, split because
the parent needed more than one run's demonstration. This half is the one that does not
fit today, and the number is why the split exists rather than a preference.

## It was built and measured, not deferred on a guess

Both streets were added to `EDGE_STREETS` together and generated together — 36 block
faces, 3,129.1 m of walk, 30 crossings, 35 fence runs, 239 walking decks. Read on the
published mirror with `tools/measure_detail_ceilings.mjs`, desktop 1280x800, worst of
T-0135's five stands:

| tier | ceiling | both streets | Randolph alone (shipped, T-0240) | Washington's share |
|---|---:|---:|---:|---:|
| `full` | 1,425,000 | 1,385,207 | 1,369,835 | +15,372 |
| `balanced` | 1,260,000 | **1,260,174 — OVER by 174** | 1,201,248 | **+58,926** |
| `light` | 1,050,000 | 761,404 | 745,904 | +15,500 |

Washington's seven block faces cost **58,926 triangles at `balanced`** at the worst stand
and only about 15,400 at the tiers either side of it — so this is not "the town is full",
it is `balanced` specifically, which is the rung T-0098 already recorded as the one
"squeezed to nothing" while `full` carried headroom.

## What unblocks it, and what does not

**Not a ceiling raise.** T-0237's acceptance names that route and refuses it, and the
count of re-basings written into `renderers/web/js/main.js` beside `DETAIL` is the
argument. This ticket is not a request for the sixth.

Any ONE of these makes Washington affordable, and each is somebody else's ticket:

- **T-0056** — the enclosure layer pays its full triangle cost at every scene-detail
  level. The street edge's fences are enclosures; a `balanced` tier that thinned them
  would pay for this street outright.
- **T-0223's remaining steps** — the timber cull's first step recovered ~160,000 at this
  stand. What is left of that ticket is the same shape of finding.
- **A `balanced` trim on the street edge layer itself** — the walk is already down to
  42.8 triangles a metre from 61.6 (see `EDGE_PLANK_UNDERSIDE` and the stringer-bay note
  in `tools/generate_frontage_works.py`); whether a further tier-conditional trim is
  honest is a real question and not a foregone one.

**Acceptance:** Washington Street's seven platted block faces carry the street edge by the
same rule, and all three tiers are inside their ceilings at all five stands at both
viewports — **without** raising a ceiling. If the run that takes this finds the 58,926
still unaffordable, that is a finding to write down, not a licence to re-base.

**Links:** T-0191 (parent) · T-0240 (Randolph, shipped) · T-0056 · T-0223 · T-0237 ·
T-0127 · `tools/generate_frontage_works.py` `EDGE_STREETS`.

---

## 2026-08-27 — SHIPPED, and the 174 was never the number

**The shortfall was 49,442, not 174.** The table above was measured against 1,425,000 /
1,260,000 — T-0229's one-day raise — and T-0229 gave those back before this ticket was
picked up. Re-measured on dev with Washington laid, `tools/measure_detail_ceilings.mjs`,
published mirror, worst of T-0135's five stands, desktop 1280x800:

| tier | ceiling | dev, Randolph only | with Washington |
|---|---:|---:|---:|
| `full` | 1,400,000 | 1,369,931 | 1,385,387 — PASS by 14,613 |
| `balanced` | 1,210,000 | 1,201,344 | **1,259,442 — OVER by 49,442** |
| `light` | 785,000 | 746,060 | 761,560 — PASS by 23,440 |

A run working to the ticket's own figure would have gone looking for a hundred and seventy
triangles and found fifty thousand.

## What paid for it: the middle rung had no reach at all

Of the three routes this ticket named, two were already spent — T-0056 measured the
enclosure layer and found it ALREADY thinning at `balanced` (three separate mechanisms had
fixed it and none had said so), and T-0223's cull had landed and been handed straight back
as T-0229's ceiling restoration. The third was the trim, and the trim was sitting in plain
sight: **`balanced` carried no furniture reach.** It drew every plank walk, fence, barrel,
wharf deck and moored hull in Chicago at any distance, exactly as `full` does, while `light`
had been culling at 350 m since T-0150. "Turn the quality down and less is drawn" was true
of the floor and false of the rung above it.

`tools/measure_furniture_reach.mjs` gained a `--level` flag — the same instrument pointed at
another tier rather than a second one written — and swept `balanced` at both viewports:

| reach | axial, desktop | forks, desktop | axial, mobile | frame delta (48²) |
|---|---:|---:|---:|---|
| none | 1,259,442 | 1,245,668 | 1,201,716 | — |
| 900 m | 1,238,488 | 1,239,100 | 1,180,762 | 0.00 / worst **0** |
| **800 m** | **1,190,670** | **1,195,188** | **1,133,376** | 0.00 / worst **0** |
| 700 m | 1,133,372 | 1,143,022 | 1,076,078 | 0.00 / worst **0** |

**The frame does not move.** Worst cell of ZERO against the same frame drawn whole, at all
five stands, at both viewports, clock held, with the baseline-against-itself residual also
0. 800 m is the LONGEST reach that gets the tier inside its ceiling — cut as little as buys
the room — and it leaves `balanced` 1.2 % clear against `full`'s 1.0 % and `light`'s 3.0 %,
so the ladder keeps its shape. 700 m stays on the table for whatever needs room next.

**No ceiling moved.** The acceptance said "without raising a ceiling" and nothing in
`DETAIL` changed.

## Both viewports, final

|  | desktop 1280x800 | mobile 390x780 |
|---|---|---|
| `full` | 1,385,387 / 1,400,000 | 1,293,397 / 1,400,000 |
| `balanced` | 1,195,188 / 1,210,000 | 1,133,376 / 1,210,000 |
| `light` | 761,560 / 785,000 | 710,686 / 785,000 |

The street itself: 36 block faces (Lake 12, Randolph 13, Washington 7, South Water 4),
3,129.1 m of walk in 40 runs, 30 crossings, 35 fence runs, 239 walking decks.

## What it did NOT fix, and the ticket for it

`light`'s **80-call floor** is red on desktop — 86 calls at Lake and Market with Washington
laid. It was red before this branch: clean dev reads **83**, breached by T-0240 the same
evening T-0147 restored the bar at 80. Mobile is inside it at 79. **T-0248** carries it,
including the measurement showing why the obvious lever (`far-merge.js`'s `FAR_M` derived
per tier) does not reach `light`.
