---
id: T-0348
title: The identity policy cannot merge an unread initial with a read one, and the best witness reads seventeen of them
state: split
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

T-0299 filled `identity.json` with the three printings of the 1 July 1834 letter list: 175
merges declared, and **29 refused**. Every refusal is one rule doing its job — same surname,
different forename initials, which this project never merges — but the twenty-nine are three
different things and only one of them is what the rule was written for.

**Eleven are the case it was written for**, two READ initials that disagree, and the letter
lists are full of families where an initial is all that separates two people: `Lyman R.
Lovell` / `Lyman B. Lovell`, `R. C. Bristol` / `I. C. Bristol`, `[H]enry Swartwout jr.` /
`J[n]o. Swartwout jr.`, `C. C. Town[s]end` / `C. E. Townsend`, `Thomas [H]. Moreland` /
`Thomas U. Moreland`, `[I]saa[c] P. Pennington` / `[I]sa[a]c T. Pennington`, `Bolton
[P]arsons` / `[uncertain: Dalton Parsons]`, `John [H]. Kin[g]` / `[uncertain: John N.
King]`, `[L]. H. Scott` / `[uncertain: I. H. Scott]`, `[I]saac Clark` / `[uncertain: lense
Clark]`, and the second Pennington. Those should stay refused forever.

**Seventeen are an initial ONE printing could not read against the same initial another
prints whole** — `[?]. Beegle` against `A. Beegle`, `[?]nn M. Gooding` against `Ann M.
Gooding`, `[?]. M. Fish` against `E. M. Fish`, `[?] Adkins` against `J. Adkin[s]`, and
thirteen more. These are not a family. They are one entry of one list at one position, and
the 1834-07-16 reading pass named three of them in its own notes as exactly that: *"'[?]
Adkins' is J. Adkins (302); '[?]. M. Fish' is E. M. Fish (535); '[?]nn M. Gooding' is Ann M.
Gooding (537)"*. The mechanism cannot tell this kind from the kind above, because `[?]`
yields no initial and "no initial" reads as "a different initial".

**And one is an initial present in one printing and absent in the other**: `Samuel E. Toby`
against `Samuel. Toby`.

So the gazetteer keeps eighteen duplicate persons its own best witness resolves, and T-0299
shipped them rather than write a rule the policy forbids. The question is the owner's,
because it is a change to the identity POLICY and not to the code:

**May a merge be declared where one side's forename initial is `[?]` — unread — and the
other side's is read, when the two stand at the same entry of the same list?** The
conservative answer is no, and the cost is eighteen known duplicates. The other answer needs
a bound: same list, same entry, and the unread side supplying no competing letter.

`data/research/newspapers/identity.json` carries all twenty-nine in `refused_merges`, each
tagged `kind` (`unread_initial`, `read_initials_disagree`, `absent_initial`) with the shared
surname and the two initials — so whichever way this is ruled, the evidence is already
sitting where the rule would go.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The owner rules on the question above; the ruling is written into `identity.json`'s note
  and into `data/research/newspapers/README.md`, not only into a PR body.
- If the answer is yes: `tools/compile_gazetteer.py` gains the bounded exception; its
  self-test carries a case for the exception AND cases proving `Cohen, P.` / `Cohen, J.`
  and all eleven genuine disagreements above still refuse; the merges move from
  `refused_merges` into `merges`, each with a `merge_rule`, and the person count is stated
  before and after.
- If the answer is no: the ticket is withdrawn with the ruling recorded on it, and the
  eighteen duplicates are documented in the README as a known and accepted cost.

---

## SPLIT, 2026-08-29 — into T-0397 (shipped) and T-0392 (the owner's)

The run that took this found the ticket needed two demonstrations, not one, and that its
own diagnosis of the mechanism was incomplete. It says here that `[?]` "yields no initial
and 'no initial' reads as 'a different initial'". That is true of only four of the
seventeen. `unmarked()` DELETES the marker, so for seven of them the initial was taken
from the next letter of the same word — `[?]rah Fowler` read as `R.`, `[?]nn M. Gooding`
as `N. M.` — and for six more a middle initial collapsed into first position, so
`[?]. M. Fish` read as `M.` against `E. M. Fish`'s `E. M.` All seventeen `refused_because`
texts in `identity.json` were written on those readings, which means a committed record
was asserting letters no printing carried.

So the parser repair is not a step toward the ruling — it is a precondition for EITHER
answer being implementable, and a provenance defect in its own right. That is **T-0397**,
and it shipped: the policy did not move (177 merges, 29 refusals, before and after).

The question this ticket was opened for is untouched and whole in **T-0392**, now
`blocked-owner` with both options and their costs written out.
