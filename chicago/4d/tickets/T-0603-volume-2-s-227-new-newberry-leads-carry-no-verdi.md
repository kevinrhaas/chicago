---
id: T-0603
title: Volume 2's 227 new Newberry leads carry no verdict, and T-0590's ladder is written and ready for them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 726
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T20:38:23.703Z
claimed_run: null
---

Volume 2's 227 new Newberry leads carry no verdict, and T-0590's ladder is written and ready for them.

**Where this stands.** T-0590 ruled all 319 leads volume 1 offered — 240 refused, 79 candidates testable in
a work this project already holds, 0 merges — anchored to the 542 cards they stand on, and brought the
domain's unspent ceiling down from 2,619 to 2,077. T-0578 then read volume 2, which raises the leads to
**546**. The 227 it adds carry nothing, and the ceiling went to 3,148 to admit the read.

**Why it is a small ticket.** The ladder exists, it is committed in `lead_crosswalk.json` under `ladder`,
and its five steps are mechanical: no exact surname key reached -> `ocr_variant_only`; no Chicago or Cook
card under the heading -> `locality_absent`; a Chicago card on an exact surname citing a held work ->
`testable_in_a_held_work`; a Chicago card on an exact surname citing nothing held -> `surname_only_chicago`;
a forename on the card that discriminates -> raised for a hand ruling, never merged on. The tool that
applied it to volume 1 can be pointed at volume 2.

**One thing to get right.** A lead row is now merged across volumes: a surname filed in both keeps its
`lead_v01_*` id (T-0578, so `lead_crosswalk.json`'s 1,248 references survive) and its `entries` now carry
BOTH volumes' cards. So some volume-1 rulings count cards in their own prose — '2 of the 5 card(s) heading
Abbott' — that were the count when volume 1 was all there was. Restate that arithmetic for every merged
row; do not change a verdict without saying which card changed it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every one of the 546 leads carries an outcome and a class, and every verdict is anchored to a card.
- The merged volume-1 rows have their card arithmetic restated, and any verdict that MOVES because volume 2
  added a card says so by name.
- `matched` stays 0 unless a card yields a forename that discriminates, and then it is a hand ruling.
- `tools/research_spend_baseline.json` records the LOWERING, with the new spent figure.
- No resident, household, structure or business is added or regraded — the index is a finding aid, and
  `read_newberry_index.py --check` still fails if the source id appears behind a person.

**Effort.** S. The ladder and the tool are written; this applied them to 227 more rows.

**DONE in PR #726, in the same run that read the volume** — not as a follow-up. T-0590's gate ("every
Newberry lead is ruled on, anchored, and re-derives from the cards") fails the moment a volume adds an
unruled lead, so the read could not merge without the ruling, which is exactly the contract that ticket
set out to create. `tools/rule_newberry_leads.py` was extended from `entries_vol_01.json` to every
`entries_vol_*.json` and its metadata from `volume: 1` to `volumes: [1, 2]`. Result over both volumes:
**546 leads ruled on 947 cards — 146 candidates `testable_in_a_held_work`, 400 refused (208
`ocr_variant_only`, 144 `locality_absent`, 48 `surname_only_chicago`), 0 merges, 0 discriminators
found.** `matched` is still reachable and still unreached. The acquisition list grows from 166 cards to
**274**, 60 of them still carrying a legible year. The spend rose with the read, 542 cards to 947, and
the ceiling raise in `research_spend_baseline.json` is 1,395 rather than the 2,027 an unruled read would
have cost.

**Links:** T-0590 (the ladder and volume 1's ruling) · T-0578 (the read that added them) · T-0562 ·
T-0602 (what the ratchet miscounts) · `data/research/newberry_index/lead_crosswalk.json`.
