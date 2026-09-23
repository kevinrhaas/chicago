---
id: T-0211
title: The other nine group rows are cross-checked against nothing
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 458
claimed_by: run 8/28/2026, 6:46:44 AM CT
blocked_on: null
needs_bake: false
---

The other nine group rows are cross-checked against nothing.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0032 (PR #388), which corrected the tenth.

`data/reconstruction/1835_building_inventory.json` carries the same aggregate three ways —
`family_targets` (35 families), `district_group_matrix` (10 groups × 4 districts) and
`districts` (4 totals). `tools/reconcile_665.py` asserts that all three sum to `roof_total`
and that each group's families sum to that group's row total. **Nothing asserts anything
about a group's split BY DISTRICT**, and the two views were authored independently.

T-0032 found what that permits. The `institutional_public` row read **south 10 / west 1 /
north 1** while the town's named institutional records stand **south 5 / west 1 / north 3**.
Every sum closed. The consequence was live: `reconcile_665.py` apportioned the south's
phantom institutional headroom into family I3, the block schedule dealt those slots to
`blk_lake_franklin` and `blk_south_water_market`, and `generate_block_infill.py` refuses
institutional families by name (L93) — so each of those blocks was going to come up a roof
short for a reason nobody could see, while the North Division was told it had room for one
institutional roof when three of them already stand there.

**The fix for I3 does not generalise, and that is the ticket.** An institutional row can be
held to a census because Chicago's public buildings are enumerable. Dwellings, stores and
barns are not — an anonymous dwelling is a legitimate count-unit toward a documented
aggregate, so "the row equals what stands" is the WRONG assertion for the other nine rows.

What is wanted is the weaker, still-useful one: for each group and district, is the row's
figure consistent with what stands there and with the family targets that feed it — and
where a district is already OVER its group row, is that reported rather than silently
clamped? `reconcile_665.py` currently clamps with
`max(0, matrix[g][district] - built_district_group[(district, g)])` and then sheds the
excess with an unnamed loop, so a row that is wrong by five roofs looks exactly like a row
that is right. Measure first: print every (district, group) pair with its target, what
stands, and the sign and size of the gap, across all ten rows. The measurement may well
refute the premise — the other nine may be fine — and that is a good outcome to record.

Acceptance: one command prints the ten-row × four-district audit with the gaps, committed,
and either a gate that asserts what the audit shows can be asserted, or a written finding
that says the other nine rows are consistent and names the numbers that show it.
