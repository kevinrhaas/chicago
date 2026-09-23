---
id: T-0325
title: The resolver reads the two marker dialects the Democrats of early 1835 speak
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0298
opened: 2026-08-28
closed: 2026-08-28
pr: 491
claimed_by: run 8/28/2026, 7:59:00 PM CT
blocked_on: null
needs_bake: false
---

Piece 1 of 2 of **T-0298 — Reading the Democrat, January to June 1835: the eight issues
only the deposit can open**. The parent says in as many words: *"Do the resolver work
first, in its own change, and read afterwards."* This is that change; T-0326 is the read.

**Six of the eight issues resolved to ZERO columns.** Measured against the deposit on
2026-08-29, before any of this: `tools/compile_gazetteer.py`'s `column_starts()` found no
column boundary at all in 1835-01-21, the 03-25 Extra, 05-20, 05-27, 06-04 and 06-10. So
every claim citing them would have failed the gate with *"the transcription carries no
ISSUE PAGE / COLUMN marker"*, and the reading pass could not have landed a single one.

**The parent's open question — defect or gap? — is a GAP.** It recorded 05-27, 06-04 and
06-10 as *"bare `=====` rules carrying no page or column at all"*. They are not bare. The
rules are decoration around a page banner, and every column carries its own rule:

| issues | shape |
|---|---|
| 01-21, 03-25 Extra, 05-20 | `[Source PDF page 9; newspaper page 1; column 1]` |
| 05-27, 06-04, 06-10 | `PRINTED PAGE 1 — SOURCE PDF PAGE 13`, then `--- SOURCE PDF PAGE 13, COLUMN 1 ---` |

46 bracket markers and 72 dash rules under 12 banners: **118 column markers invisible to a
resolver already corrected twice for exactly this** (T-0289's third ruled dialect, T-0258's
1833 dash-column one).

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `column_starts()` reads both shapes, and all six issues resolve their columns.
- The census is run over every artifact in `corpus.json` before and after: the six move
  and **nothing else does**.
- `--self-test` carries a case per new dialect plus negatives, and each one is shown to
  fire when the resolver is broken.
- The dialect count in `data/research/newspapers/README.md` and in the tool's own header
  is corrected, and the parent's "defect" reading is corrected with it.
- Anything left uncitable at column level is named with the reason, not left silent.
