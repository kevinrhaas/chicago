---
id: T-0378
title: The names the post office held letters for in more than one return join the town, and letter_list_only reaches the visitor's card
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0374
opened: 2026-08-29
closed: 2026-08-29
pr: 535
claimed_by: run 8/29/2026, 7:09:47 AM CT
blocked_on: null
needs_bake: false
---

The names the post office held letters for in more than one return join the town, and letter_list_only reaches the visitor's card.

Piece 1 of 2 of **T-0374 — letter_list_only reaches the visitor's card, and the 1,536 names known only from the post office**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**THE SIZING THAT CAUSED THE SPLIT** (measured on dev at caefea5b, after the 31 July 1835
letter list landed on dev in #532 and grew the pool from 1,530). The parent's pool is 1,530 register persons carrying `letter_list_only` with
action `new_resident`. Put through the eight refusals `tools/mint_documented_residents.py`
already derives — garbled 415, surname already minted 250, the town already names that
family 101, placed outside the town 22, a surname and nothing else 10, a firm 6 — **726
survive**. That is a town of 225 people gaining 726, and which of them the reconstruction
should hold is a question about scale that belongs to the owner, not a refusal an agent
should invent. So it is T-0379's, with the measurement, and this ticket takes the slice
whose evidence the corpus itself ranks highest.

**THE SLICE, AND WHY IT IS THIS ONE.** Of those 726, twelve are named in MORE THAN ONE
return of uncalled-for letters. The Democrat reprinted a single return over consecutive
weekly issues, so mentions are not returns; grouping a name's issues at a gap of more
than sixty days separates the reprints from a genuinely later list. Eighteen names clear it and twelve
survive the refusals, five of them spanning January 1834 to May 1835 — sixteen months in
which the post office at Chicago twice held a letter nobody called for. A name the office held once is a person
somebody wrote to; a name it held in two returns months apart is a person somebody kept
believing was reachable at Chicago. That is the corpus ranking its own evidence, and it
is what makes this slice a rule rather than a sample.

**Acceptance:** (stated before working — never weakened to pass)

- `letter_list_only: true` is carried onto each minted person, declared in
  `tools/measure_layer_reads.py` and RENDERED by `renderers/web/js/residents.js`, so a
  letter-list name and a documented tradesman never read as the same evidence on the card.
- No minted resident carries an occupation. The papers give these twelve none, and the
  occupation block is absent rather than invented.
- The pass is a derivation, gated by `--check` in `tools/check.sh` like the deal and the
  documented mint beside it, with every refusal printed and its reason readable.
- `town_census.json` totals move additively; no household loses a member.
- Before → after on the person count, with the instrument named.
