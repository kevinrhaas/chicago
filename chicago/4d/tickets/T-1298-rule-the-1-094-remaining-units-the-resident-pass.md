---
id: T-1298
title: Rule the 1,094 remaining units: the resident-pass reserved people, the newspaper person units, the church register entries, the non-person book readings and the one genealogytrails unit
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1236
opened: 2026-09-17
closed: 2026-09-17
pr: 1425
claimed_by: run 9/17/2026, 7:24:10 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T01:04:45.697Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35290782143
---

Rule the 1,094 remaining units: the resident-pass reserved people, the newspaper person units, the church register entries, the non-person book readings and the one genealogytrails unit.

Piece 3 of 3 of **T-1236 — EPIC: rule on the unasserted units the person-fact passes do not own — the land-sale, civic, 1830-census, church, newspaper and directory names, the resident-pass reserved people, and the book readings of ground, harbour, weather, price and institution**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every one of the 1,094 units in this body carries a WRITTEN ruling — a named rule
   with a stated reason and a per-unit note — in the shape
   `data/research/spend_rulings.json` established. A silent reclassification is a fail.
2. No ruling upgrades a confidence, mints a person or invents a citation, and a hand-off
   names an OPEN ticket whose field genuinely owns the finding.
3. A unit that cannot be ruled on the evidence is recorded as unasserted WITH ITS
   REASON. That is a finished answer, not a deferral, and no ticket is filed per unit.
4. `python3 tools/measure_research_spend.py --check` stays green and the ledger carries
   no unit owned by this ticket.

**The corpus** — the remainder, five domains: `residents` 382 (the reserved people of
the pilot and passes 02-15 whose findings name no exact structured field), `newspapers`
378 (the person units of the thirteen held issues that no card names), `church` 272 (the
register entries outside the later-only and outside-Chicago rulings), `books` 61 (the
non-person readings — ground, harbour, weather, price, shipping, institution and
household) and `genealogytrails` 1.

The `books` 61 are the only non-person body in the whole epic: they are readings ABOUT
the town, not about a person, and the ruling has to say what a reading of the harbour or
the price of flour does for the 1835 scene when no person unit owns it.

**Links:** T-1236 (parent) · T-1234 · T-1147 · T-1157.
