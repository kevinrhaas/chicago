---
id: T-0032
title: The six-roof civic target counts three that were never built
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: T-I3(b)
parent: null
opened: 2026-08-17
closed: 2026-08-27
pr: 388
claimed_by: run 8/26/2026, 11:26:54 PM CT
blocked_on: null
needs_bake: false
---

Three of the six I3 civic slots count nothing; the arithmetic is closed so they cannot be
deleted without a claim. Both exits are in blocked_on and § T-I3(b) (~6311).


---
**OWNER RULING, 2026-08-17: "close it at 665 or 662 — either is close."** The pick is
delegated. Steward recommendation: **662** — T-I3(a) established the three slots were a
count of nothing, not miscategorized real roofs, so re-typing them into ordinary families
would invent three buildings on the strength of an arithmetic artifact. The filename
(`1835_665_roof_programme.json`) and tool name stay, with a one-line note that the total
they carry is now 662; renaming them is churn the ruling does not require. The implementing
run may take 665 instead with reasoning stated.

---
**RESOLVED 2026-08-27 at 662 — route 1, the recommended pick.**

**The measurement.** `tools/measure_institutional_claims.py` now carries a civic ledger and
settles each candidate against the committed dataset rather than against the dossier. On the
uncorrected data it printed: *the I3 target is 6 and the civic ledger settles 3 roof(s)
standing on the scene date (log_jail, council_house, chicago_lighthouse_1832)*. Three stood.
Four came later — court-house (fall 1835), engine house (contracted 30 Dec 1835), market
house (1837), custom house (1846). Two were public functions with no building of their own —
the US Land Office and a town hall never built. One stood and was roofless — the estray pen.

**What was changed.** `roof_total` 665 → 662, `principal_functional` 511 → 508,
`family_targets.I3` 6 → 3.

**What else moved, and it was not predicted.** The `institutional_public` matrix row
apportioned twelve roofs as south 10 / west 1 / north 1 while the named institutional records
stand **south 5 / west 1 / north 3** — a second disagreement between two authored views of the
same aggregate, of exactly the shape T-I3(a) found in the court-house. The row is now the
census, which carries the south district target 370 → **365** and the north 150 → **152**
(the ROADMAP box had predicted 370 → 367 and no change in the north). Downstream: remaining
327 → **324**, coverage-gated 299 → **296**, and every I3 slot has left the block schedule —
one at `blk_lake_franklin`, one at `blk_south_water_market`, three in the South balance.

**What a visitor sees.** The gate screen reads *338 buildings standing, of the 662 the town
held*. Nothing in the scene moved; the standing count is 338 before and after.

**Gated, not remembered.** The target and the institutional row are both asserted against the
ledger on every run of `tools/check.sh`, with nine self-test cases breaking each assertion in
memory to prove it fires. `1835_665_roof_programme.json` and `reconcile_665.py` keep their
names, each carrying one line saying the number in the name is history. Liberty **L182**
records that the total and its division split are ours. Full write-up:
`docs/RESEARCH/civic_public_buildings_1835.md` § 6a.
