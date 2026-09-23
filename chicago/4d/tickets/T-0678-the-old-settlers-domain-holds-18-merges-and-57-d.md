---
id: T-0678
title: The old_settlers domain holds 18 merges and 57 death-notice matches naming a town person, is registered in no domains.json, and reaches neither hop of the spend measure
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 941
claimed_by: run 9/5/2026, 6:49:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T00:36:03.123Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33999561507
---

The old_settlers domain holds 18 merges and 57 death-notice matches naming a town person, is registered in no domains.json, and reaches neither hop of the spend measure.

`data/research/old_settlers/` holds two adjudications that name people this town has cards
for: `crosswalk.json` files 18 merges under rules OS1/OS2A, and
`death_notices_crosswalk_1835.json` files 57 matches out of Fergus's old-settler death
notices, 36 of them carrying a derived birth-year interval and 51 a date of death. The
domain is registered in NO `data/research/domains.json` entry, so
`tools/measure_research_spend.py` measures neither hop for it: it appears in that tool's
output only as the line "not registered in domains.json (not measured)". T-0635
(consolidation pass 2) found it there while accounting for its own window.

The death notices are the delicate half and the crosswalk says so itself: the list's header
admits it also names citizens who arrived after 1843, so a match "does not mean the person
was in Chicago in 1835". Its 43 contested and 20 ambiguous rows are rivals still standing.
Whatever is carried is carried as evidence of a DEATH and of an interval the birth falls
in, never as an 1835 fact and never as a grade — the file's own `carry_rule`.

**Acceptance:**

1. `old_settlers` is registered in `data/research/domains.json` with what it holds and what
   a unit is, and both hops of the measure report it with a recorded ceiling.
2. The 18 merges and the 57 death-notice matches are either written onto the cards they
   name — with the record id, the death date and the birth interval, and no grade moving —
   or the ceiling states, per group, why they are not.
3. Nothing is read that was not already read.
