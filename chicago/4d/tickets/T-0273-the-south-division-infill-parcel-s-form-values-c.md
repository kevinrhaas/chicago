---
id: T-0273
title: The South Division infill parcel's form values come from the archetype and cite the family band: 9 families, 10 claims outside it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 537
claimed_by: run 8/29/2026, 7:07:12 AM CT
blocked_on: null
needs_bake: true
---

The South Division infill parcel's form values come from the archetype and cite the family band: 9 families, 10 claims outside it.

The values are authored in `tools/generate_inferred_infill.py`, `_form_body`.

**Found by T-0172 (2026-08-28)**, which generalised `tools/measure_family_deal.py` from the
platted-block generator to all four anonymous parcels. The sweep's first assertion is green
everywhere — **0 refusals**: every archetype builds every size any of the four parcels may
deal it, at 400 synthetic deals per family. What it found instead is the second assertion,
K25's: 10 values whose note cites the family band and which sit outside it. Each is a
per-family CONSTANT, so it is made on 100 per cent of that family's deals, not on a tail.

The repair is one shape, and it is the one T-0144 and T-0145 already applied to the block
parcel: replace the literal with `family_bands.pitch_deg` / `wall_height_m`, sampled inside
the family's own band and bounded at both ends by `family_bands.eave_limits` so the
archetype's floor and ceiling hold. Ask the archetype for the limits; never retype them.

**This moves geometry**, so it re-derives the parcel's records and re-bakes what moved in
the same commit — `tools/validate.py --stale` hard-fails otherwise, and `check.sh` runs it.
Then `tools/publish.sh`, then `tools/measure_family_deal.py --write-baseline` to shrink
`tools/family_deal_baseline.json` by exactly the rows repaired. The baseline is a ratchet:
it may shrink and may not grow.

**Acceptance:** `tools/measure_family_deal.py --parcel infill` reports 0 refusals and 0
off-band claims, its rows are gone from `tools/family_deal_baseline.json`, the moved records
are re-derived and re-baked in the same commit, and `tools/measure_band_claims.py --gate`
has not grown.

**The claims, each with the literal behind it:**

| family | claim | the literal |
|---|---|---|
| A2 | pitch 32.0 outside 33.69-45 deg | `18.0 if roof == "shed" else 32.0`, outbuilding tail |
| A4 | eave 2.75 m outside 1.829-2.438 | `wall = 2.05 if family == "A3" else (3.42 if door == "wagon" else 2.75)` |
| A5 | eave 2.75 m outside 2.134-2.743 | the same default |
| C2 | eave 3.25 m outside 3.353-3.962 | `5.35 if stories == 2 else 3.25`, C/F branch |
| C3 | eave 5.35 m outside 5.486-6.706 | the two-storey half of the same literal |
| D2 | eave 2.75 m outside 2.134-2.438 | D2 falls past the D branch to the outbuilding tail |
| D2 | pitch 18.0 outside 18.435-33.69 deg | the same fall-through, shed |
| D3 | eave 2.78 m outside 2.438-2.743 | `wall = ... else 2.78` |
| D7 | eave 5.05 m outside 5.182-5.791 | `5.05 if family == "D7"` |
| F2 | eave 5.35 m outside 5.791-7.01 | the C/F two-storey wall |

Worth noticing while repairing: this parcel's outbuilding tail deals **2.75 m** where the
west parcel's deals **2.05 m** for the same man door. The two files are copies that have
already drifted, and they miss different families because of it — which is the argument for
the repair being a call into `family_bands`, not a better constant.
