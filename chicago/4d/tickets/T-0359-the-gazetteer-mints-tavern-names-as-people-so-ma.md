---
id: T-0359
title: The gazetteer mints tavern names as people, so Maddock's Tavern and Haddock's Tavern cannot be reconciled
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 546
claimed_by: run 8/29/2026, 9:36:20 AM CT
blocked_on: null
needs_bake: false
---

The newspaper gazetteer keys persons on the whole normalized name, and `identity.json` is the one
place two spellings may be declared one. Its rule — **same surname, different initials never
merge, with or without a rule** — exists because the post-office letter lists are full of
families, and it is right.

It also mints **buildings as people**. `person_haddock_s_tavern` ("Haddock's Tavern") and
`person_maddock_s_tavern` ("Maddock's Tavern") are two entries in the persons table, and so are
`Graves, [Mr.]` and `Mr. [Dexter] Graves`. The compiler then reads "Tavern" as the surname and
"Haddock's" / "Maddock's" as the forename, and refuses the merge under the families rule:

    FAIL  identity.json merge "Haddock's Tavern" <- "Maddock's Tavern": same surname,
          different initials — this project never merges those, with or without a rule

T-0324 established that these are one building beyond argument — G. Spring's standing For-Sale
notice reads "Haddock's Tavern" in four legible settings (1834-06-18, 1834-09-03, 1834-10-15,
1834-11-19) and "Maddock's Tavern" in exactly one (1834-07-09), which is precisely the condition
the 1834-07-30 reading pass set for closing it: "the two anchors stay separate until an issue
prints both spellings in a way that decides it." The evidence closed it and the ledger cannot
record it. **The rule is not wrong; it is being applied to something that is not a person.**

That matters for T-0262, the July 1835 register: a register minted off this table will carry
tavern signboards as inhabitants of the town, and the duplicate pairs among them cannot be
cleaned by the machinery that cleans people.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A building or sign name in the persons table is either classified as a place, or the reason it
  is not is written down. Whichever way it goes, the families rule for actual people is
  UNCHANGED — this ticket must not become a hole in it.
- The Haddock's/Maddock's Tavern pair is reconciled, or the ticket says in as many words why a
  reconciliation the evidence closes still cannot be recorded.
- Whatever lands is gated: `compile_gazetteer.py --check` and its self-tests stay green, and the
  new classification has an assertion that fires when broken, like every other one there.

**Links:** T-0324 (found it) · T-0304 (the firm half of the identity policy) · T-0262 (the
register that will read this table) · `data/research/newspapers/identity.json` ·
`tools/compile_gazetteer.py`
