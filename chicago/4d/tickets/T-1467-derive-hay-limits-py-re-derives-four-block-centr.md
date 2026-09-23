---
id: T-1467
title: derive_hay_limits.py re-derives four block centres one centimetre off in a steward sandbox and not in CI, so check.sh is red on a clean dev checkout for a PROJ version rather than a reading
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: null
claimed_by: null
blocked_on: Fixed, and the diagnosis in the title is wrong. The four Kinzie's Addition centroids were not a PROJ version difference: they sit exactly on the 2 dp rounding boundary, and sum()'s left-to-right accumulation drift — a few parts in 10^15 — was picking the digit, so the file read one value in a steward sandbox and the other in CI. derive_hay_limits.programme_blocks now sums with math.fsum (correctly rounded, order-independent) and the file re-derives exactly on both; merged in #1585. T-1486 owns the sweep of the remaining sites and is in flight as #1593.
needs_bake: false
closed_at: 2026-09-20T23:16:56.584Z
claimed_run: null
---

derive_hay_limits.py re-derives four block centres one centimetre off in a steward sandbox and not in CI, so check.sh is red on a clean dev checkout for a PROJ version rather than a reading.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1442's gate run (2026-09-20).** `./tools/check.sh` on this steward runner reports

    DIFF data/reconstruction/1835_hay_limits.json — the committed file is not what this tool derives
      differs: block_infill_programme

on a **clean `origin/dev` checkout** — reproduced with the working tree stashed — while
`chicago-4d-check.yml` is green on the same commits (`ee71a1b0`, and every dev run before it).

The difference is four of the 26 `blocks_outside_the_limit` rows, each one centimetre on one
axis of `centre_local_enu_m`:

| block | committed | this sandbox |
|---|---|---|
| `blk_superior_north_wolcott` | 888.7 | 888.69 |
| `blk_huron_north_wolcott` | 888.08 | 888.09 |
| `blk_erie_north_wolcott` | 887.47 | 887.48 |

All three are Kinzie's Addition blocks, which T-1437 (#1561) added; the file dates from
before it. The sandbox has `pyproj 3.8.0`.

**What this ticket owes:** a block centre that rounds differently on two machines makes a
re-derivation gate a reading of the runner rather than of the data. Either pin the projection
stack the gate re-derives under, or round the committed figure where the derivation is only
stable to a decimetre — and regenerate the file either way, since it has been stale against
T-1437 since that merge.
