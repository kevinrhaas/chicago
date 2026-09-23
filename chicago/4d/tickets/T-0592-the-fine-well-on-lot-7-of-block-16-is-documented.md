---
id: T-0592
title: The fine well on lot 7 of block 16 is documented and the town has no well to draw it with
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 820
claimed_by: run 9/4/2026, 5:49:45 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T23:34:53.339Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33926189060
---

G. Spring's For-Sale notice names TWO structures on lot 7 of block 16 — "a large
Dwelling-House **and fine well**" — and both are documented as plainly as each other. T-0423
seated the address (`docs/LOT-ADDRESS.md`, L216) and drew the house's lot; the well is
recorded on the record as documented and ABSENT, with the reason, rather than passed over.

The reason: **this town has no well.** There is no well archetype in `generators/archetypes`,
no well in any committed structure, enclosure or yard record, and no well in the flora or
frontage layers. Drawing this one is raising a new kind of object for the whole scene rather
than placing a known one — and it would be the only well in Chicago, on the one lot whose
address happens to resolve, which is a distribution no source supports.

**So the question this ticket owes is not "draw a well here" but "what does this town do
about wells".** A frontier town of 3,265 people did not have one. The corpus, Andreas and the
ordinances between them may say enough to place wells as a CLASS — by lot, by density, by the
same kind of aggregate argument the 665-roof programme uses for roofs — in which case lot 7's
is one of many and the address is not what puts it there. If they do not, the honest answer is
that the well stays stated-and-absent, and that is a finding rather than a failure.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The corpus, Andreas and the ordinances are read for what they say about wells in 1835
  Chicago, and the reading is written down whether or not it supports drawing any.
- EITHER a well class is placed on an argued rule with its own liberty and its grade, and lot
  7's well is one of them and cites its own notice; OR the reading refuses, and the refusal
  is recorded where the next run will find it instead of re-asking.
- If a well is drawn: a new archetype, `./tools/bake.sh --only` per affected structure, and
  `tools/publish.sh` in the same commit. That is a bake and it is why this is not XS.
- `recon_1835_blk_south_water_dearborn_d3_03`'s `lot_address` note stops saying the town has
  no well, if it stops being true.

**Links:** T-0423 (the address this comes out of) · `docs/LOT-ADDRESS.md` · **L216** ·
`data/research/newspapers/lot_addresses.json` · claims `chicago_democrat_1834_06_18#c006`,
`chicago_democrat_1834_09_03#c005`, `chicago_democrat_1834_10_15#c006`,
`chicago_democrat_1834_11_19#c010`.
