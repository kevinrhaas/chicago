---
id: T-0695
title: A garbled printed forename refuses a match the reader can still make: C!;as. for Chas., J>ctij for John, Iia for Ira
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 995
claimed_by: run 9/6/2026, 12:03:15 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T17:33:27.655Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34047194177
---

A garbled printed forename refuses a match the reader can still make: C!;as. for Chas., J>ctij for John, Iia for Ira.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

T-0670 tightened the directory crosswalks to refuse a match where both readings print a full
forename and the two disagree. Three of those refusals are not two people disagreeing, they are a
scanner that could not read a contraction, and the refusal record already says so
(`garbled_reading: true` on the entry):

    Wesencraft, C!;as.   carpenter and wagon maker   Norris 1844   — Chas., i.e. Charles
    Hale, J>ctij. F.     botanic physician, 185 Lake Norris 1844   — John
    Couch, Iia           proprietor of the Tremont   Norris 1844   — Ira

`C!;as.` is recovered today, because `tools/name_agreement.py` carries `cas` in the printers'
contraction table; the other two are refused and the men behind them — John Hale and Ira Couch,
who kept the Tremont House — lose their 1844 entry to a transcription defect.

**The ask.** Fix the READING, not the rule: the printed page is legible and
`data/research/directories/claims/norris_1844_directory_entries.json` is where the garbled token
lives. Correct the `normalized.given` against the page image and leave the `as_printed` quote
damaged, which is the standing convention — a tidied quote cannot be found again. Then re-derive
both crosswalks and report which refusals become matches. Sweep the whole claims file for the same
class of damage rather than only these three; `name_agreement.garbled()` names them.

**Links:** T-0670 (the rule that surfaced them) · `tools/name_agreement.py` ·
`data/research/directories/norris_1844_crosswalk_1835.json` § forename_refusals.
