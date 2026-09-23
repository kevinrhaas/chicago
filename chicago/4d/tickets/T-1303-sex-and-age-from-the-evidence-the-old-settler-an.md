---
id: T-1303
title: Sex and age from the evidence: the old-settler and death-notice births spent onto the cards they name, a committed forename→sex table that refuses ambiguity, and every person the sources or an unambiguous forename can settle given sex and birth_year at attested or inferred tier
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1168
opened: 2026-09-18
closed: 2026-09-18
pr: 1446
claimed_by: run 9/18/2026, 2:26:29 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T08:37:46.786Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35319074035
---

Sex and age from the evidence: the old-settler and death-notice births spent onto the cards they name, a committed forename→sex table that refuses ambiguity, and every person the sources or an unambiguous forename can settle given sex and birth_year at attested or inferred tier.

Piece 1 of 2 of **T-1168 — Fill sex and age for every attested and inferred person: recorded where a source says, inferred from forename, office or register role where the evidence about that person allows, reconstructed from the population model otherwise — each value with its tier and reason**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working)

- Sex is written for every person a gendered title or a forename that stands in one sex's
  naming settles, and for nobody else. An initial, a rank, a collective description
  ("The four Temple children") and a name the evidence splits all fire nothing.
- The forename→sex table is committed with the evidence for every name it lets fire —
  the people in this layer whose sex a source records, and the period pools — and it is
  DERIVED, so `--check` refuses a hand-widening. `Marion`, `Jean`, `Leslie` and
  `Francis`/`Frances` are refused by name with the reason beside each.
- The old-settler registry ages and the death-notice intervals already adjudicated in
  `data/research/old_settlers/` are spent into `birth_year`, with the arithmetic and the
  source's own limits on the card. A match resting on a single initial is refused.
- Counts before and after, per rule, are committed in a ledger and re-derive.
- No attested or inferred value already on a card is changed; the resident mints carry
  the fill rather than dropping it at the next rebuild.
- Visible: the card prints the sex with its tier and its reason, and a birth interval as
  the two years the arithmetic leaves open.

**Done (PR to follow).** 99 → 689 people with a sex (558 by forename, 32 by a period
contraction, 99 already recorded); 10 → 64 with a birth year (24 from the Calumet Club
registry of 27 May 1879, 30 from Fergus's obituary list, 6 refused as resting on one
initial). Refused: 205 initial-only, 379 whose forename this project has no evidence
about, 3 on a named ambiguity.

**FOUND AND HANDED TO T-1304:** no age is derived from an adult status here. A poll list,
a civic office or a trade says a person was an adult and says nothing about when they
were born, and the franchise's own age rule (male, 21) is not in any source record this
project holds — asserting it would be a liberty, not a reading. 244 people carry civic
evidence and 241 a role; that bound is the model's to draw, or a source record's to
establish first.

**ALSO FIXED, because the reading was wrong and it showed:** the profile report read a
rank as a forename — "Lieut. James Allen" was read as *Lieut* — and would have taught a
forename table that Col, Rev and Major are men's names. Ranks and honorifics are read
past to the name behind them now, and a collective description names nobody.
