---
id: T-1297
title: Rule the 718 name-on-a-roll units: the civic poll, voter and Black Hawk War lists, the 1830 census heads and the unruled directory entries
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1236
opened: 2026-09-17
closed: 2026-09-17
pr: 1427
claimed_by: run 9/17/2026, 7:23:23 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T01:38:07.618Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35290777493
---

Rule the 718 name-on-a-roll units: the civic poll, voter and Black Hawk War lists, the 1830 census heads and the unruled directory entries.

Piece 2 of 3 of **T-1236 — EPIC: rule on the unasserted units the person-fact passes do not own — the land-sale, civic, 1830-census, church, newspaper and directory names, the resident-pass reserved people, and the book readings of ground, harbour, weather, price and institution**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every one of the 718 units in this body carries a WRITTEN ruling — a named rule with
   a stated reason and a per-unit note — in the shape `data/research/spend_rulings.json`
   established. A silent reclassification is a fail.
2. No ruling upgrades a confidence, mints a person or invents a citation.
3. A unit that cannot be ruled on the evidence is recorded as unasserted WITH ITS
   REASON. That is a finished answer, not a deferral, and no ticket is filed per unit.
4. `python3 tools/measure_research_spend.py --check` stays green and the ledger carries
   no `civic`, `census_1830` or `directories` unit owned by this ticket.

**The corpus** — one question, a name on a roll, in three domains: `civic` 496
(`records/voter_lists_1833_1835.json` 345, `records/blackhawk_war_1832_chicago.json`
134, four small claim files 17), `census_1830` 204
(`records/schedule_chicago_1830.json` 200, `claims/schedule_town_findings.json` 4) and
`directories` 18 (`claims/norris_1844_town_findings.json` 16, two Fergus 1839 rows).

The parent's bound already names the likely answer for `census_1830`: those are 1830
heads, five years before the scene, on the same ladder T-1290 closed for 1840, and
**"nothing" is a complete answer** where it is the true one.

**Links:** T-1236 (parent) · T-1234 · T-1290 · T-1159.
