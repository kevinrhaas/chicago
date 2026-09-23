---
id: T-0230
title: Two named South Water frontages carry a reconstructed trade, so neither a signboard nor a hitching post will ever stand at them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-12
pr: 1176
claimed_by: run 9/12/2026, 1:29:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T06:44:37.760Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34678124958
---

Two named South Water frontages carry a reconstructed trade, so neither a signboard nor a hitching post will ever stand at them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by **T-0194**, which stood hitching posts at the street edge's trading frontages
and had to refuse these two by the clause it shares with the signboard rule.

`tools/generate_business_signboards.py` decides which frontage announces itself, and
`tools/generate_frontage_works.py` now reads the same table to decide which frontage gets
a post. Both require the TRADE to be held `attested`, `documented` or `inferred` — a
`reconstructed` trade would put furniture and lettering on an invention. That clause is
right, and it is doing what it should for the anonymous `inf_` slots, whose trades were
dealt by the roof schedule.

**But two of the frontages it turns down are NAMED, documented buildings** standing on
platted lots on South Water Street and Lake Street:

| record | `function.value` | `function.confidence` |
|---|---|---|
| `frederick_thomas_shop` | `shop` | `reconstructed` |
| `physicians_office` | `physicians_office` | `reconstructed` |

Both are documented enough to be placed, reconciled onto the plat (T-0198/T-0199 moved
Frederick Thomas's shop 7.75 m onto its committed lot) and named on a card a visitor can
open. What is `reconstructed` is not that the building stood there — it is the WORD this
project chose for what was done inside it. So each stands on a busy trading street with a
plank walk in front of it, a fence behind it, and no board and no post, and the reason is
a grade on a field rather than anything a visitor could reason about.

**The question is which of two things is true**, and it should be answered by reading the
records rather than by relaxing a clause:

1. the trade really is unknown for these two, in which case the refusal is correct and
   worth stating on the record so it reads as a finding rather than an oversight; or
2. the trade is known and the field is under-graded — `frederick_thomas_shop` is named
   for a man and a shop, and a directory, an advertisement or a tax entry naming the
   trade would move it to `inferred` at a stroke and light up both layers at once.

Related: **T-0221** reports that `measure_street_frontage.layer_of` misreads
`physicians_office` off its filename, so this record is already awkward for more than one
tool.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
Each of the two records' `function.confidence` is either upgraded against a source that is
cited, or the note on that field says in as many words why the trade cannot be graded
better — and whichever way it goes, `data/frontage/town_street_edge.json` and
`data/signage/town_business_signboards.json` re-derive and say the same thing. Never by
weakening the grade clause in either generator.

**Links:** T-0194 (found it) · T-0221 · T-0198 · T-0199 · docs/LIBERTIES.md L160, L159.
