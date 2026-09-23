---
id: T-1121
title: The minted person hugunin_leonard_c stores the name 'Leonard, C. Hugunin' with the comma one word to the left, so the surname-first rule reads Leonard as the surname though the record id and the gazetteer's other printing both say Hugunin
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-17
pr: 1377
claimed_by: run 9/16/2026, 11:28:19 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T05:52:42.614Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35181833062
---

The minted person hugunin_leonard_c stores the name 'Leonard, C. Hugunin' with the comma one word to the left, so the surname-first rule reads Leonard as the surname though the record id and the gazetteer's other printing both say Hugunin.

**Acceptance:** `display()` no longer carries a printing's second comma into the card
it orders, so a reader of the CARD lands on the family name a reader of the LINE does;
`hugunin_leonard_c` reads `Leonard C. Hugunin`, the town directory files it with Hiram
Hugunin instead of between the two Leonards, and the 1840 crosswalk stops counting it
as one of the Leonards in its refusal of `John Leonard`. The mint's own gate refuses
any card whose comma moves the family name, its self-test breaks that assertion and
requires the gate to name it, and the name-reading table proves the round trip
`surname(display(x)) == surname(x)` over every printing it holds. The fix stays the
SMALLEST one that closes it: a general rule was measured over the 1,050-name pool
first and is refused here for moving 84 readings, most of them correct.
