---
id: T-0827
title: The committed market line is fitted to N Wacker Drive and stands 9.1 m off the Thompson plat's own module
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: 1206
claimed_by: run 9/12/2026, 1:21:48 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T18:54:46.705Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34709324295
---

The committed market line is fitted to N Wacker Drive and stands 9.1 m off the Thompson plat's own module.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0451**, reading the Thompson plat's North Division tier.
`tools/measure_north_division_streets.py` fits the sheet to four committed South Division
corridors (residuals ≤ 0.46 m) and then reads every other corridor through that one fit.
Five of the six North Division corridors land within 2.3 m of the committed line they
continue. **Market lands 9.08 m west of it** — four times the worst of the other five —
and the committed `market → franklin` pitch of 118.5 m is already the one South Division
pitch off the plat's 400 ft module, where the other five read 122–123.6 m.

The suspect is the parent line rather than the North Division. `market`'s `name_2026` is
**N Wacker Drive**, which stands on ground made after the river was walled, and the
record is fitted to it. Nothing in this reading can choose between the two lines: what
would is a re-fit of `market` off the plat's own module — Franklin stepped one module
west — measured against whatever surviving control the 1834 sheets carry on that line.

`market_north` is graded `inferred` and cites only `thompson_plat_1830` until this is
settled; every other North Division line is `attested`. Moving `market` moves
`market_north` with it, and re-scores `generate_plat_lots.py`'s Market–Franklin blocks.
