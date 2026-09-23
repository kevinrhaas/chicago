---
id: T-0392
title: May an unread forename initial be merged with a read one at the same entry of the same list — the owner's ruling
state: blocked-owner
epic: PAPERS
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: T-0348
opened: 2026-08-29
closed: null
pr: null
claimed_by: null
blocked_on: May a merge be declared where one side's forename initial is [?] (unread) and the other's is read, at the same entry of the same list? No = eighteen known duplicates are an accepted cost; Yes = a bounded exception, same list, same entry, no competing letter.
needs_bake: false
---

The question T-0348 was opened for, kept whole and separated from the parser repair that
had to come first (T-0397, merged).

`identity.json` declares 175 merges across the three printings of the 1 July 1834 letter
list and refuses 29. Eleven of the refusals are the case the rule was written for — two
READ initials that disagree (`Lyman R. Lovell` / `Lyman B. Lovell`, `R. C. Bristol` /
`I. C. Bristol`, `Thomas [H]. Moreland` / `Thomas U. Moreland` and eight more). **Those
should stay refused forever.**

Seventeen are something else: an initial ONE printing could not read against the same
initial another prints whole, at the SAME entry of the SAME list — `[?]. Beegle` against
`A. Beegle`, `[?] Adkins` against `J. Adkin[s]`, `[?]. M. Fish` against `E. M. Fish`,
`[?]nn M. Gooding` against `Ann M. Gooding`. The 1834-07-16 reading pass, which its own
notes call the best witness of the three, names three of them as exactly that: *"'[?]
Adkins' is J. Adkins (302); '[?]. M. Fish' is E. M. Fish (535); '[?]nn M. Gooding' is Ann
M. Gooding (537)"*. And one more is an initial present in one printing and absent in the
other: `Samuel E. Toby` against `Samuel. Toby`.

Since T-0397 the parse can finally tell the kinds apart: an unread initial is `UNREAD` in
the position it was printed in, it equals no letter, and every refusal now states the
reading the page carries. So the mechanism is no longer the obstacle. **The policy is.**

**THE QUESTION, and it is the owner's because it changes what a declared identity IS:**

> May a merge be declared where one side's forename initial is `[?]` — unread — and the
> other side's is read, when the two stand at the same entry of the same list?

- **No** (the conservative answer): an unread initial is not the same as a read one, and
  the cost is eighteen known duplicate persons the project's own best witness resolves.
  Then this ticket is withdrawn with the ruling recorded on it, and the eighteen are
  documented in `data/research/newspapers/README.md` as a known and accepted cost.
- **Yes, bounded**: same list, same entry, and the unread side supplying no competing
  letter. Then `compile_gazetteer.py` gains that exception; its self-test carries a case
  for it AND keeps `Cohen, P.` / `Cohen, J.` and all eleven genuine disagreements
  refusing; the eighteen move from `refused_merges` into `merges`, each with a
  `merge_rule`; and the person count is stated before and after.

The evidence is already sitting where the rule would go: all 29 are in `refused_merges`,
each tagged `kind` (`unread_initial`, `read_initials_disagree`, `absent_initial`) with the
shared surname and — since T-0397 — the parsed `initials_read` of both sides.

**Acceptance:** the owner rules; the ruling is written into `identity.json`'s note and into
`data/research/newspapers/README.md`, not only into a PR body; and whichever branch it
takes is carried out above.

## Two more cases, from the 1 April 1834 list (T-0321, 2026-08-29)

Not the July list and not a `[?]` initial, but the same question with the forename
missing entirely rather than unread. The 1 April 1834 Chicago list is printed three
times; the 1834-04-08 reprint could read two of its names by surname alone and minted
`[uncertain: — Duncklo]` and `[uncertain: — Denny]`. The third printing —
`chicago_democrat_1834_04_16` c016, found on 2026-08-29 — sets `Hexekial’ Dunchi` and
`William Denoy` at those same two positions of that same return, so the forenames are
legible: Hezekiah and William.

Merges were written for both and the compiler refused both, correctly and by its stated
rule. So the readings stand in `normalized` and the gazetteer keeps two people with no
forename that it could name. **No = two more accepted duplicates on top of the eighteen
below; Yes = two more closed by the same bounded exception.** Nothing was changed here.
