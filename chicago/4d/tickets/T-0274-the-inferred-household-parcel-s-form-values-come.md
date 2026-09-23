---
id: T-0274
title: The inferred-household parcel's form values come from the archetype and cite the family band: 8 families, 10 claims outside it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 574
claimed_by: run 8/29/2026, 6:43:18 PM CT
blocked_on: null
needs_bake: true
---

The inferred-household parcel's form values come from the archetype and cite the family band: 8 families, 10 claims outside it.

The values are authored in `tools/generate_inferred_households.py`, `inferred_form`.

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

**Acceptance:** `tools/measure_family_deal.py --parcel household` reports 0 refusals and 0
off-band claims, its rows are gone from `tools/family_deal_baseline.json`, the moved records
are re-derived and re-baked in the same commit, and `tools/measure_band_claims.py --gate`
has not grown.

**The claims, each with the literal behind it:**

| family | claim | the literal |
|---|---|---|
| A2 | pitch 32.0 outside 33.69-45 deg | `18.0 if roof == "shed" else 32.0`, tail |
| A5 | eave 2.05 m outside 2.134-2.743 | `3.42 if door == "wagon" else (2.75 if door == "stable" else 2.05)` |
| C2 | eave 3.25 m outside 3.353-3.962 | `a(3.25)`, `frame_storefront` branch |
| C2 | pitch 33.0 outside 33.69-42.51 deg | `a(33.0)`, same branch |
| C3 | eave 3.25 m outside 5.486-6.706 | the same 3.25 m; the widest miss here |
| D2 | eave 2.05 m outside 2.134-2.438 | the programme pairs D2 with `outbuilding`; man door |
| D2 | pitch 18.0 outside 18.435-33.69 deg | the same pairing, shed |
| D3 | eave 2.78 m outside 2.438-2.743 | `a(5.05 if two else 2.78)`, `frame_dwelling` branch |
| H1 | eave 2.5 m outside 3.353-3.962 | **LATENT** — the programme pairs H1 with `log_dwelling`, whose branch deals a flat 2.5 m: a metre short |
| W4 | eave 2.05 m outside 2.743-5.486 | man door |

This parcel keys its form on the **archetype** rather than the family, which is why
`tools/measure_band_claims.py`'s own root-cause section quotes this function. Two records
escape their default through a programme `form` override and are worth reading before
repairing: `brown_boarding_house` (H1) stands at 2.9 m rather than 2.5 — still outside the
band, and invisible to `band_claims_baseline.json` because that record carries no
`reconstruction.family` — and `temple_lake_st_building` (C3) stands at 5.05 m rather than
3.25. The override is not the repair; it is one building each.
