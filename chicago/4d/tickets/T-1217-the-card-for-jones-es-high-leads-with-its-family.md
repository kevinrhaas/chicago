---
id: T-1217
title: The card for jones_es_high leads with its family name, because the printing 'Es,Jones, High' sets it in the middle, and a re-mint would file it in the directory under es
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: 1384
claimed_by: run 9/17/2026, 1:51:31 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T08:55:23.538Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35191480414
---

The card for jones_es_high leads with its family name, because the printing 'Es,Jones, High' sets it in the middle, and a re-mint would file it in the directory under es.

**Found by T-1121**, which fixed the other card with two commas and deliberately left
this one alone. The printing is `Es,Jones, High`; `surname()` reads `jones` off it by
T-0638's first-token rule, and the id `jones_es_high` is right. But `display()` reorders
around the FIRST comma, so it moves `Es` to the end and the card reads `Jones, High Es`
with the family name still leading. Today that is harmless — the comma makes
`surname()` read the card as a surname-first printing, and it answers `jones`, which is
the right answer for the wrong reason, and `compile_scene.py surname_of()` strips the
comma clause and files it under `jones` too. It stops being harmless the moment the
comma goes: `Jones High Es` sorts in the town directory under `es`, away from the other
Joneses, and T-1121's gate does not refuse the comma precisely because removing it
would move the answer.

**Acceptance:** the card for `jones_es_high` carries the family name last, the town
directory files it with the other Joneses, and whatever rule gets it there is measured
over the whole 1,050-name letter-list pool before it lands. T-1121 measured one
candidate rule — put the token `surname()` picked last, wherever it fell — and it moved
84 readings, most of them correct ones, because a square-bracket supply and a bare
honorific are not forenames (`[uncertain: Bester], James`, `Baby, Mrs.`). Any rule
proposed here owes that same count.
