---
id: T-0111
title: Dearborn's worn track stops 2.7 m short of its causeway deck
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-24
pr: 361
claimed_by: run 8/24/2026, 7:56:58 AM CT
blocked_on: null
needs_bake: false
---

Dearborn's worn track stops 2.7 m short of its causeway deck.

Found working T-0110: the street record's path ends at [699, 18] while the drawbridge
approach fill (`dearborn_south` in `terrain_spec.json`) carries the ground to the deck end
at [697.65, 20.7] — so after T-0110's drape fix the track climbs the fill cleanly and then
gives out on bare crest, 2.7 m before the boards, about a metre east of the fill's axis.

**Why the obvious one-line fix is wrong, measured (T-0110's PR reverted it):** appending a
bend to `path_local_enu_m` fails two gates. `tools/generate_plat_lots.py --check` re-derives
every block face by offsetting the WHOLE street polyline, so a 3 m worn-track bend moves
platted lot lines the length of Dearborn; and the extended corridor makes the drawbridge's
draw phase a new corridor intrusion (`measure_corridor_intrusion.py --gate`, 0.61 m). The
plat line and the worn wheel line are different claims, and today one field carries both.

**The shape of the fix:** either a per-street drawn-track override the renderer prefers and
the plat/corridor consumers ignore (schema + compile + streets.js), or teach the plat module
to use only the plat-derived span. Then bend the last metres onto the fill crest —
reconstructed, bounded by the approach record's own deck-end coordinate, with the liberty
recorded (T-0110's PR carries ready wording for the record note and ledger entry in its
history).

**Acceptance:** from South Water Street the Dearborn track runs continuously up the fill and
butts the causeway deck end with no bare crest between, the platted block and lot grid
re-derives byte-identical, the corridor-intrusion gate stays at its committed count, and the
smoke's T-0110 approach-coverage stations extend to the deck end (n 20.5) and pass.

**Links:** T-0110 (the drape fix and the revert) · T-0046 / L147 (the approach fills) ·
`tools/generate_plat_lots.py` (block faces from street polylines) ·
`tools/measure_corridor_intrusion.py`.
