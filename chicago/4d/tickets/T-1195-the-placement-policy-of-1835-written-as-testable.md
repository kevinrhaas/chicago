---
id: T-1195
title: The placement policy of 1835, written as testable rules with their evidence: who lived and worked where — merchants and forwarders on the river and Lake Street, professionals by the square and the hotels, mechanics on the side streets, labourers on the small lots and the fringes, farms and country seats outside — and how many buildings a main-street lot held
state: open
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The owner: *"spread the businesses and residences and all other civic and other structures across
the city correctly along lot lines and corners and lots … I think you will have multiple
buildings per lot in many cases in the major streets and probably it's spread out naturally over
time, do what you can to make the location of reconstructed businesses and residents as
reasonable and accurate as a historian would."* The project holds pieces of this policy already —
ROADMAP K1's "businesses toward the river and the built streets, residences further out", the
face rule (T-0024: a store never on a `light` street, commercial roofs on the street line), the
end rule (T-0023: the better roof nearer the drawbridge), the frontage-fabric ruling (T-0022: log
trade buildings DO stand on principal streets), the density standard (T-0079: three party-line
units per lot), the trade-share-by-street-class measurement (T-0213: 0.78 principal / 0.45
ordinary / 0.00 light), the North memo's four clusters and the West memo's five. Nobody has
written the whole policy in one place with the evidence for each clause, and the seating tickets
need it as a rule set, not a memory.

**Deliverable** — `data/reconstruction/1835_placement_policy.json` + `docs/RESEARCH/
1835_placement_policy.md`, built/checked by `tools/placement_policy_1835.py`, one rule per row:
`{ id, applies_to (household type | business type | archetype family), prefers[] (street class /
named streets / division / lot position corner|mid), avoids[], multi_building_lot_rule,
setback_class, evidence[] (the documented records that show it — e.g. every attested South Water
firm; Harmon's cabin on the outskirts; the Wolf Point taverns at the forks; the brickyard on the
north side clay; the tannery on the branch), tier, note }`. Clauses to write at least: the
commercial front (South Water / Lake / Dearborn / Clark north of Lake, corners first); the
professional row (Lake, Clark, the square, the hotels); the mechanics' streets (State, Dearborn
south of Lake, the Canal approach, the North Water bank for heavy trades); the dwelling bands
(Randolph–Washington, the north tier under Kinzie, the west clusters) by household wealth class
(the H-family houses for merchants/professionals, D3–D5 for tradesmen, D1/D2 for labourers,
shanties and cabins on the fringes and the small lots); the noxious trades on the branches and
downwind (packing, tannery, slaughter, soap); the farms and country seats outside the plat
(the Beaubien/Kinzie/Clybourn places attested); lodging houses near the landings and the
stage/wagon approaches; **multi-building lots** — how many principal roofs a main-street lot
held (the party-line evidence, Wright's building-to-let pairs, the density standard) vs one on a
back street; corner preference for stores and taverns; the wet-ground refusals.

**Acceptance:** the policy file with every clause evidenced; `measure_face_rule.py`,
`measure_frontage_fabric.py` and `measure_end_rule.py` read their rules FROM it (one source of
truth); a dry-run scores every standing documented record against the policy and prints the
outliers with the reason each stands where it does (the outliers are evidence, and the policy
notes them); no roof moves.

**Stop condition:** T-1198, T-1199 and every build ticket seat by this file.

**Links:** T-0022 · T-0023 · T-0024 · T-0079 · T-0213 · `docs/ROADMAP.md` K1/K29/K31/K32 ·
`docs/RESEARCH/1835_north_division_extent_and_infill.md` · `docs/RESEARCH/west_division_infill_1835.md`.
