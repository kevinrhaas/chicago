---
id: T-1049
title: With the place vocabulary resolved, refuse an out-of-town newspaper person as a Chicago appearance in read_newspapers(), record the refusal in its own class, and re-derive every card that loses a press reading
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1047
opened: 2026-09-11
closed: 2026-09-12
pr: 1175
claimed_by: run 9/11/2026, 11:47:52 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T06:19:16.042Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34673822849
---

With the place vocabulary resolved, refuse an out-of-town newspaper person as a Chicago appearance.

Piece 2 of 2 of **T-1047**, itself piece 2 of **T-1040**. BLOCKED ON T-1048 — do not start this one first; a guard built on the unresolved vocabulary refuses Fort Dearborn.

## THE FINDING

`tools/consolidate_resident_evidence.py`'s `read_newspapers()` hands EVERY gazetteer person to the resident identity pool with evidence class `newspaper_1833_1835`, reading only the name and the first mention. It never looks at `associated_places`. So a man the papers place at Michigan City is offered to the clustering as a Chicago appearance, and merge rule M1 — identical normalised name — puts him on whatever Chicago card shares his name.

`hh_miller_samuel` is the worked example T-1040 was filed on. After T-1046 that card cites one press reading, `person_col_samuel_miller`, whose gazetteer record correctly reads `occupations: [agent]`, `associated_places: [Michigan City]` — David Carver's agent at Michigan City, Indiana. The card's note still says "A CONTEMPORARY CHICAGO PAPER OF 1833-1835 PRINTS THIS PERSON BY NAME IN THE TOWN" and its rung G1b is spent partly on that reading. The sentence is false of it. Strip it and the card is the 1832 muster and the 1833 tax list, which is what it should have rested on.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- a newspaper person the resolved vocabulary places OUTSIDE the town, and nowhere inside it, is not offered to the pool as a Chicago appearance;
- the refusal is RECORDED in its own evidence class and not dropped — named, counted, and visible in the master the way the letter-list class already is, because a suppressed refusal is invisible and a named one can be argued with;
- `hh_miller_samuel` no longer cites the Michigan City reading, and its note no longer claims a Chicago paper printed the man in the town;
- every card that loses a press reading is re-derived in the same pass, and every rung that MOVES is stated with its count. This reached 132 households at filing; if the resolved vocabulary makes it fewer, say the new number;
- `bash tools/check.sh` is green.

## WHAT LANDED

`read_newspapers()` now asks `resolve_place_vocabulary.person_resolution()` where the
papers put a person, BELOW the existing date test — `newspaper_after_1835` is a refusal
about WHEN and this one is about WHERE, and a reading that fails the date never reaches
the town at all, so the older class keeps its rows and its count. A person the resolved
vocabulary places outside the town, and nowhere inside it, takes evidence class
`newspaper_out_of_town`. No rung reads that class, no class family counts it, and
`independent_records` does not let it corroborate; the ladder's own "no scene-window
evidence" early-out reads it beside `newspaper_after_1835`.

**The refusal is kept.** `identity_master.json` carries a `place_refusals` block — every
refused reading by name, the identity it was offered to, the printed place that decided
it, and whether that identity stands on a card — plus two counts in `counts`. The corpus
that ruled each place is cited, not copied, so the two cannot drift.

**THE SECOND FAULT, and the reason a first attempt changed nothing.** `mint_civic_
residents.carry_over()` keeps what ANOTHER pass wrote onto one of this pass's cards, by
copying any key the derivation no longer writes. Two of those keys are this pass's OWN:
an evidence block that has gone empty, and `sources`, which is unioned so that
`old_settlers.py --apply-citations` survives. So a card could gain evidence and never
lose it — `hh_miller_samuel` went on citing the Michigan City notice after the
derivation had stopped producing it. `BLOCK_KEYS` are now excluded by name, and a
`retracted` set names the sources a refused reading was the only support for, so this
pass's own retraction is told apart from another pass's addition.

## THE COUNTS, against dev c3103f6c2

- **122 readings refused**, across **121 identities**, on **67 distinct printed places** —
  Hennepin 14, Juliet 12, Plainfield 7, Albany 6, Detroit 5, New York 4. 15 of the
  refusals were on an identity the town still carries.
- **109 rungs moved**: 76 `G1b attested → G0 not_1835_resident`, 24 `G3 inferred → G0`,
  3 `G2e → G3`, 2 `G2e → G0`, 2 `G1b → G3`, 1 `G1b → G2b`, 1 `G1b → G2e`.
- **78 households un-minted** and **90 re-derived**. The filing estimate was 132
  households; the resolved vocabulary — which places 27 of the naive test's 193 INSIDE
  the town and refuses to decide 25 more — makes it **168 touched, 78 of them removed**.
- `hh_miller_samuel`: `G1b attested` → `G2b inferred`, no `press_evidence`, no
  `chicago_democrat_1833_1835` in `sources`, and the note no longer says a contemporary
  Chicago paper printed the man in the town. The 1832 muster and the 1833 tax list are
  what is left, which is what the ticket asked for.
- L220 restated 479 → 401 and L223 14 → 13 in `docs/LIBERTIES.md`; five research-spend
  ceilings raised with the same reason on the record — the corpus did not grow, the town
  shrank under it.
- `bash tools/check.sh`: **PASS, 312 steps, none red.**
