---
id: T-0253
title: May an invented building stand on the river margin of a platted street corridor
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

May an invented building stand on the river margin of a platted street corridor?

Handed on by **T-0134**, which settled the measurement and could not settle this.

**What is measured and closed.** `tools/measure_south_bank_ground.py` sweeps the south bank
from the Dearborn crossing east to the Reservation's west line. Beside South Water Street's
platted line — the frontage image 3 of the owner's brief of 2026-08-18 draws low warehouses
on — the smallest footprint family F1 allows stands at ZERO positions, at any bearing, on
ground inside the 0.30 m walker step tolerance, and zero inside 0.35 m. The ground outside the
corridor is the river bank and it falls into the water inside its own width. Full finding:
`docs/RESEARCH/south_bank_dearborn_ground.md`.

**What is not measured, because it is a decision.** The platted 80 ft corridor occupies this
bank down to the water. `docs/LIBERTIES.md` L79 records the travelled tracks running 5.8–10.5 m
inside an 80 ft corridor, and South Water's committed `track_width_m` is 10.5, so about 7 m of
legal corridor stands between the wheel line and the corridor's north edge at this reach, on
ground the heightfield holds flat to 0.05 m. A freight shed there would be in nobody's way and
would be standing in the platted street.

**Why this is not just a placement.**

- It would be the first record in this project placed KNOWINGLY inside a corridor. The 29 that
  lap one today are documented records the plat was fitted around, and T-0009 owns getting them
  out; this would push the count the other way on purpose.
- `tools/measure_corridor_intrusion.py --gate` refuses a new lap by construction, and its
  written-refusal mechanism (T-0195) exists for documented records whose escape is blocked —
  not for admitting invented ones. `--write-baseline` is documented as "only to record a
  repair". Using it to bank a deliberate new lap is a different act and should be named as one.
- The live alternative is that what the plate draws on the south bank is WHARFED OUT over the
  water rather than standing on the bank — the wharfing-out practice of the south bank is
  already held reasoning here, the five South Water landings (T-0062) and the two attested
  docks stand on it, and that belongs to the wharf layer (T-0059), not to the ground.

**Acceptance:** either a stated rule for when a reconstructed building may stand on the river
margin of a platted corridor — written where the corridor gate can read it, with the plate's
south-bank warehouses built under it — or a written refusal that sends the reach to the wharf
layer instead, with T-0134's exclusion entry updated to say which.

**Links:** T-0134 · T-0133 · T-0071 · T-0009 · T-0059 · T-0062 · T-0195 ·
`docs/LIBERTIES.md` L79, L164 · `data/exclusions.json` → `south_bank_warehouses_dearborn_reach`.
