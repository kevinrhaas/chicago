---
id: T-1042
title: A firm style's surnames are read as one name, so 'H. Doty & Co.' stands on Lake Street as a man called Co
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-12
pr: 1172
claimed_by: run 9/11/2026, 11:37:56 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T05:27:07.946Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34673359649
---

A firm style's surnames are read as one name, so 'H. Doty & Co.' stands on Lake Street as a man called Co.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`adopt_street_faces.surnames()` and `replace_invented_residents.stands()` both take the
LAST word of a proprietor string for its surname. On a person that is right. On a firm's
own trading style — which 28 of the 199 houses carry among their proprietors, T-0398 —
it is a guess, and the corpus shows both ways it goes wrong:

- **It invents a man.** `H. Doty & Co.` and the five printings of `J. L. Wilson & Co.`
  each yield the surname `co`, so the adoption table records somebody called Co standing
  on Lake Street, and refusal 5 ("a man does not keep two shops on one street") can fire
  on him. `compile_register.py` fixed exactly this for its own matching in T-0304, after
  two firms ending `& Co.` matched Daniel Elston's soap works — `firm_surnames()` is that
  fix and it reads ALL the surnames out of a style.
- **It loses a man.** `Clark, Filer & Co.` yields `clark` alone and Filer is dropped;
  `Harmon, Loomis & Co.` loses Loomis; `Fullerton & Botsford` keeps Botsford and loses
  Fullerton. Nine of the 39 committed adoptions carry a style of this shape.

Since T-0398 the row itself carries `partners` and `firm_styles`, so the pass can tell
the two apart without re-deriving anything. What it must NOT do is simply drop the
styles: that is what loses Clark and Filer both.

**Acceptance:** every surname a proprietor string names is read out of it, styles
included, by ONE shared derivation rather than three; no surname is invented from a firm
suffix; the adoptions the change moves are each named in the PR with the reason, and the
occupants and refusals downstream re-derive green.
