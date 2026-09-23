---
id: T-1173
title: Reconstruct the trade households the occupation model still wants after the known and re-admitted people are counted: labourers, carpenters, teamsters, sawyers, masons, boatmen, clerks and the rest, by division, each head named from the pools with a family per the household model
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-18
pr: null
claimed_by: run 9/18/2026, 6:50:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T23:54:04.419Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35406958128
---

Stage `trades` of T-1167: the occupation model's `gap` per trade (T-1162), reduced by
everything T-1172 re-admitted with a trade, is filled with new reconstructed heads — the
business band that follows (T-1184 … T-1188) then ADOPTS these heads as its
proprietors rather than minting its own, so the two bands fill one quota — the town's
mechanics and labourers the rosters never printed. The retired programme's arguments (labourers
"the largest trade in any western town and the one no roster records"; carpenters from the
building rate; coopers from the packing volumes) are re-derived here against the model, not
copied.

**Rules:** per trade × division bucket, `to_reconstruct` heads: surname + forename from the pools
by the arrival model's community shares for that trade (Irish and German shares higher among
labourers; Yankee among clerks — the model's numbers, not this sentence), age band from the
occupation's model band (labourers young, master tradesmen older), family from the household
model, arrival/origin/reason from the arrival model, `presence: present`, division as bucketed,
`works_at[]` left for T-1189, `lives_at` left for T-1199. Every draw seeded.

**Acceptance:**

- The order book's trade buckets read filled; the occupation model's target vs (attested +
  inferred + reconstructed) table printed per trade, within bracket; two builds byte-identical.
- No trade exceeds its ceiling where the model states one; labourers are a residual and the
  tool prints the residual arithmetic.
- LIBERTIES entry; counts by community and by division printed.
- Visible: People view; the "Reconstructing the town" card.

**Stop condition:** every trade the model wants has its people.

**Links:** T-1167 · T-1162 · T-1163 · T-1165 · T-1172 · T-1189.
