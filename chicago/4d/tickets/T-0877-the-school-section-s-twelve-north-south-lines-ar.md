---
id: T-0877
title: The School Section's twelve north-south lines are read and not committed: Des Plaines, Jefferson, Clinton, Canal, Market, Wells and Clark run south of Madison and five more tiers carry no name
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-12
pr: 1212
claimed_by: run 9/12/2026, 4:36:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T22:32:17.308Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34720157159
---

The School Section's twelve north-south lines are read and not committed: Des Plaines, Jefferson, Clinton, Canal, Market, Wells and Clark run south of Madison and five more tiers carry no name.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while working T-0797, which committed the twelve EAST-WEST lines and read the
north-south ones without committing them.

Wright rules **fourteen** north-south lines across the School Section, and T-0797's module
measured every one of them (`grid.ns_lines` in
`data/traces/vectors/school_section_blocks_1834.json`, with the drawn corridor width and
the number of sampling bands that agreed). Seven carry a name on the sheet — **Des
Plaines, Jefferson, Clinton, Canal, Market, Wells, Clark** — and the rest are ruled and
unnamed; the two outer lines are the section's own west boundary and State Street.

None of them is in `data/streets/1835.json`. The blocks committed by T-0797 therefore name
their east and west neighbours as `west_sheet_name` / `east_sheet_name` strings rather than
as street ids, which is honest and is not what a bounded_by is for.

**Acceptance:** the twelve interior north-south lines committed with the same unopened /
unworn status the east-west tiers carry, the seven names taken from the sheet and
`name_1835: null` on the rest; each block's `bounded_by` then naming street ids on all four
sides. Note that `canal`, `clinton`, `market`, `wells` and `clark` already exist as
records of the town NORTH of Madison — decide, and say which, whether these are the same
streets continued or separate records, because `compile_register.py` keys a printed street
name onto one id and the choice moves where a notice lands.
