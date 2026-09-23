---
id: T-1051
title: The Lake Street land-agency card ran from 14 May to 17 September 1834 and the corpus has read two of its nine impressions
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-13
pr: 1273
claimed_by: run 9/13/2026, 3:01:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T21:06:14.729Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34779292388
---

The Lake Street land-agency card ran from 14 May to 17 September 1834 and the corpus has read
two of its nine impressions.

Found by T-0408, which repaired the reading of that card's 11 June 1834 impression and had to
read the whole run to do it. `business_w_g_blanchard` stands in the register on TWO claims,
`chicago_democrat_1834_06_11#c008` and `chicago_democrat_1834_07_09#c025`, and its evidence
window therefore reads 1834-06-11 to 1834-07-09. The Democrat carries the same standing
advertisement — word for word, the same anchor — in at least nine issues:

| issue | transcription line | the name line as set | column |
|---|---|---|---|
| 1834-05-14 | 2612 (address) | `Wo  BDSAWIGI` (line 2604) | Tesseract fallback |
| 1834-05-28 | 2868 (address) | name line lost | Tesseract fallback |
| 1834-06-04 | — | `@s DRANCRAID,` | Tesseract fallback |
| 1834-06-11 | 2732 | `Wo. @ WRAWCUA` | Tesseract fallback |
| 1834-06-18 | 3275 (address) | name line lost in the interleave | — |
| 1834-07-02 | 4398 (address) | name line lost in the interleave | — |
| 1834-07-09 | 3590 | `Wo Gs WhANCWAMD,` | Tesseract fallback |
| 1834-07-16 | 5527 | `1* G. BLANCHARD,` | Vision |
| 1834-07-23 | 647 (address) | name line lost in the interleave | — |
| 1834-09-17 | 3292 | `[uncertain: BLALYCHARD,]` | Vision |

Two of those are extracted. **What it costs.** The register's `last_issue` for this house is
1834-07-09 when the paper has it running ten weeks longer, which is the span L211's survival
liberty is measured over; and the 1834-06-04 impression is already cited in c008's own note
without being a claim, which is a reading that exists in prose and not in the record.

**What this is NOT.** It is not the forename. Every impression that sets the name line sets
the forename garbled or loses it, and reading them at the page will not necessarily settle
`W.` against `F.` — see T-0408's `refused_firm_merges` declaration, which is what that
question belongs to.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The impressions of this card that the corpus can quote are extracted as claims on the house
  the register already carries, each with its own locator and its quote machine-checked against
  the transcription; an impression whose lines cannot be quoted verbatim is listed as refused,
  with the reason, rather than left silent.
- `business_w_g_blanchard`'s evidence window in the re-derived register reaches the last
  impression that was read, and the PR states the window before and after.
- Nothing here upgrades a confidence, invents a forename, or touches T-0408's refusal.

Links: T-0408 (which found it), T-0413, L211.
