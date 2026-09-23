---
id: T-0255
title: The dooryard planting rule reads every street in the town with no bound on reach, so a track across the river can turn a house's yard
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-12
pr: 1208
claimed_by: run 9/12/2026, 1:57:25 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T19:42:36.171Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34712445241
---

`tools/generate_dooryard_plantings.py` seats a house's stems *away from the nearest street* — the
yard is behind the house — and `candidates()` finds that street by scanning **every record in
`data/streets/1835.json`**, with no bound on distance and no notion of which bank a street is on.

**Measured 2026-08-28 on T-0099.** Adding `fort_bank_track`, a 23.91 m track on the SOUTH bank
below the fort's north gate, changed the yard of `recon_1835_north_d4_039` — a dwelling on the
NORTH bank at about `[1139, 321]`. The new track stands **61.6 m** from it; `michigan_north`,
the street that dwelling actually fronts, stands **68.3 m**. So a track across open water, with
no crossing between them for hundreds of metres, became that house's nearest street and turned
its two cottonwoods about 6 m. The re-derived output was committed on that PR — the rule's
answer, not a fault in the run — but nobody chose this behaviour and nothing states it.

**It also means the layer is order-dependent in a way the gate cannot see.** Any street added
anywhere in the dataset may silently re-seat stems at a house it has nothing to do with, and the
only signal is a `--check` drift a later run has to decide about with no rule to decide against.

**Acceptance:** the rule states, in its own docstring and in the record it writes, what "the
nearest street" is allowed to mean — a bound on reach, or a refusal to cross the water mask, or
both — with the figure argued from the committed data rather than picked; the re-derivation is
green under it; and the census of which houses change yard under the new definition is reported
(zero is an acceptable answer, and so is a number, but not silence).

**Links:** T-0099 (where it was found) · T-0074 (the layer) · `docs/STATUS.md` § Shipped
2026-08-28 — T-0099.
