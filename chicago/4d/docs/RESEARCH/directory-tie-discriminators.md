# May a second discriminator break a directory tie? (T-0696)

**The answer is three answers.** A trade may NARROW a tie and never make it a match; a
premises may not, and the measurement that said it could was measuring the wrong thing; a
year may not, because there is nothing on either side to compare. The rule is
`tools/tiebreak.py`, which carries all three and a self-test, and is gated in `check.sh`
beside `name_agreement.py` — which, until this ticket, was not gated either.

## What the tie is

The crosswalks to Fergus 1843 and Norris 1844 match a printed entry to a person of 1835 on
the folded surname plus the first initial, refusing a full-forename disagreement since
T-0670. Two shapes survive that rule and it cannot decide either:

- **CONTESTED** — one printed line that two or more people of 1835 all meet. At most one of
  them is the person printed, so no match is made.
- **AMBIGUOUS** — one person of 1835 who meets several printed lines. Filed as such, not
  resolved.

T-0696 asked whether something else on the record — a trade, an address, a year — may be
allowed to pick a side.

## The ruling

### A trade may narrow a tie

Where exactly one side of a tie carries an 1835 trade that agrees with the trade printed
against the name, that side is **named** and the tie is filed as `discriminated`. The terms:

1. **Agreement is substring, either way**, after folding underscores to spaces and dropping
   case and punctuation. `none_recorded` is not a trade. The test is **coarse by
   admission** — the residents vocabulary and the directories' trade words are not the same
   vocabulary, and T-0661 is the ticket for the words themselves.
2. **It must name exactly one side.** Two named, or none, and the tie stands.
3. **It is a narrowing, not a match.** A discriminated tie stays out of `matches`, no
   person's grade moves in either direction, and the pass that spends this proposal decides
   for itself whether it will spend one. A tie broken on a trade IS a stronger claim than a
   tie left standing, and this is where that extra strength is held: in a separate list a
   reader has to opt into, not folded into the matches beside a rule-made match.
4. **The loser is filed as SILENT, not contradicted.** The directory does not say he is not
   the man; it says nothing about him. A refusal written as a contradiction would be a
   stronger claim than the evidence supports.
5. **The narrowing is `reconstructed`, never attested.** No source says these two readings
   are one person — the trade agreement is the reasoning, which is what `reconstructed`
   means here. The record carries the confidence of the 1835 trade it leaned on, so a
   reader can see whether that leg is attested (`attested` in six of the seven below).

### A premises may not — and the table in T-0696 was measuring the wrong thing

The ticket's coarse table reported that "an 1835 premises names exactly one of the rivals"
in 8 of 33 contested groups, which read as the strongest of the three discriminators. It is
not a discriminator at all.

The 1835 layer records a premises as a **structure id** — `hogan_store`, `peck_store` — and
the directories print a later **street address**, or, in both cases that survive on dev
today, not a place at all but a person to board with ("bds Charles L. P. Hogan"). Nothing
compares the two, because they are not comparable. What the test actually measures is which
rival **the town has already placed on the ground** — and preferring the better-documented
record is how a reconstruction invents a fact rather than finds one. Only 19 households
carry a `lives_at` and 43 a `works_at`, so the test is very nearly a test of whether a
person has a card with a building on it.

Both premises cases left on dev are the same Hogan group the trade settles on its own
evidence, so refusing the premises costs this dataset nothing today.

### A year may not

Neither side of any live tie carries a birth year in the 1835 layer, so there is nothing to
compare. Fergus's bracketed death notes, which with an age give a year of birth, are T-0574's
to read and are not spent here.

Both refusals are held in `tiebreak.REFUSED_DISCRIMINATORS` with their reasons, so a later
run proposing one has to argue with a named record rather than with a paragraph.

## The measurement, re-run on dev

The ticket's table was measured on 2026-09-04 and the tree has moved under it — T-0670's
tightening and the card work since have cut the ties roughly in half. Which is the argument
for a machine-checked measurement rather than a prose table: these numbers are now counted by
the crosswalks themselves, in `counts.ties_narrowed_by_a_trade`, and re-derived by `check.sh`.

| | T-0696 as filed (2026-09-04) | on dev, this pass |
|---|---|---|
| Fergus 1843 contested groups | 18 | 8 |
| Norris 1844 contested groups | 15 | 8 |
| Fergus 1843 ambiguous residents | 51 | 41 |
| Norris 1844 ambiguous residents | 28 | 23 |
| a trade settles a contested group | 6 of 33 | **1 of 16** |
| a trade picks one entry for an ambiguous resident | 6 of 79 | **6 of 64** |
| a premises settles a contested group | 8 of 33 | refused (2 of 16, and both the same group) |

**Seven ties narrowed**, and they are the good ones:

| volume | tie | resident | 1835 trade | named |
|---|---|---|---|---|
| Fergus 1843 | contested | John S. C. Hogan, against John Hogan | postmaster | "Hogan, John Stephen Coates, ex-postmaster" |
| Fergus 1843 | ambiguous | John Dean Caton | attorney | "Caton, John Dean, attorney" |
| Fergus 1843 | ambiguous | Silas B. Cobb | saddler | "Cobb, Silas Bowman, saddler and harness maker" |
| Norris 1844 | ambiguous | J. B. Cook | baker | "Cook, Josiah P. baker" |
| Norris 1844 | ambiguous | J. Curtiss | attorney | "Curtiss, James, state's attorney" |
| Norris 1844 | ambiguous | Russel E. Heacock | attorney | "Heacock, R. E. attorney at law" |
| Norris 1844 | ambiguous | Benjamin Jones | grocer | "Jones, B. & Co. dry goods and groceries" |

The yield is small and it was always going to be: the discriminator can only fire where the
1835 layer records a trade at all, and 1,228 of the people it holds carry `none_recorded`.
That is a finding about the residents layer, not about the rule.

## What this does not do

It writes nothing to a resident record. The crosswalks are proposals, and a narrowed tie is
a proposal with a named favourite and a filed refusal — one step better than a tie, and
several steps short of a fact.

**Links:** T-0670 (the forename rule this sits beside) · T-0661 (the trade vocabulary the
test wants) · T-0569 (the pass that spends these proposals) · `tools/tiebreak.py` ·
`tools/name_agreement.py` · `tools/crosswalk_fergus_1843.py` · `tools/crosswalk_norris_1844.py`
