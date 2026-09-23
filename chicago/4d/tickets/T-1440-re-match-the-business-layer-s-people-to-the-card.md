---
id: T-1440
title: Re-match the business layer's people to the cards the merge rulings already settled: the fullest agreement takes a printing, rivals are refused, and the folded cards answer to their own printed names
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1190
opened: 2026-09-20
closed: 2026-09-20
pr: 1564
claimed_by: run 9/20/2026, 6:28:34 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T12:12:46.366Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35506620874
---

Re-match the business layer's people to the cards the merge rulings already settled: the fullest agreement takes a printing, rivals are refused, and the folded cards answer to their own printed names.

Piece 1 of 3 of **T-1190 — Converge the business layer: register, businesses, persons and structures agree by id; every reconstructed firm carries its substitution rule and liberty; the trade-census crosswalk, the order book and the Businesses view print the finished count**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**THE FINDING T-1432 HANDED OVER**, and it is the whole of this piece. The staffing join put
each card's own name beside every name the register printed for it — the first time the two
had stood in one place — and three cards disagreed: `kinzie_james` held three houses printed
*J. H. Kinzie*, *John H. Kinzie* and *John S. Kinzie*; `hogan_john`, a card with no trade
recorded, held both of *John S. C. Hogan*'s; `bradley_joseph` held the travelling dentist
printed *J. C. Bradley*.

**AND `data/residents/card_merge_rulings.json` HAD ALREADY RULED EVERY ONE OF THOSE CARDS.**
C2 folded `kinzie_j_h` onto `kinzie_john_h` — *"the Kinzie surname holds a James as well as a
John, so the bare initial J would be two rivals and refused, but 'J. H.' agrees with John
Harris"*; C3 folded `kinzie_john_s` onto the same card; D1 holds `kinzie_james` distinct —
*"John H. Kinzie and James Kinzie are brothers, not a duplicate"*; C2 folded `hogan_j_s_c`
onto `hogan_john_s_c`. The register was not told. `compile_register.py`'s matcher reads only
`households/`, where a folded card is not, and among the cards that remain it returned
whichever `sorted` reached first — the SHORTEST key every time, because a tuple sorts before
its own extension. The least specific card of a surname swallowed every fuller printing of it,
and a tie had nowhere to be refused.

**Acceptance:**

1. **The fullest agreement wins.** A printing goes to the card that agrees with it furthest —
   a spelled forename outranking a longer card it disagrees with, and `J. H.` reaching John
   Harris over James. The compatibility rule itself does not move: a candidate must still
   share the surname and agree on every compared initial.
2. **Rivals are refused.** Where two cards stand equal the match is `person_id: null`, which is
   this layer's own way of saying a printed name has no town card — the second half of C2's
   sentence, which was never implemented.
3. **A folded card answers to its own printed name.** `index.json`'s `merged` table is read and
   each folded card offered as an alias of its survivor, so the printings the folds were made
   ON resolve to the person the ruling says they are.
4. **One tokenizer.** `initials` and the new `forename_readings` come off one parse in
   `compile_gazetteer.py`; `initials`' answer is unchanged and the gazetteer re-derives.
5. **Gated.** Self-test cases for each of 1-3, proved to fire when the rule is removed, and
   every downstream derivation the register feeds re-built in the same commit.
6. **Stated.** Every changed row published, with its reason, in
   `docs/RESEARCH/business-layer-identity-2026-09.md`.

**What this piece does NOT do.** It makes no new identity ruling. `bradley_joseph` stands:
the town holds exactly one Bradley card, the printing is compatible with it, and deciding that
*J. C. Bradley*, surgeon dentist at the New York House for one week of June 1835, is not
Joseph Bradley — a resident with no 1835 trade and a clerkship in the 1843 directory — is a
reading of evidence, not a mechanical rule. It stays in the join's
`questions_for_the_convergence` and is T-1190's to rule with a source in hand.

**Stop condition:** every proprietor, partner and staff row in the business layer names the
card the project's own rulings say it names, or names none.

