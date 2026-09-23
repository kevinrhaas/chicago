---
id: T-0376
title: The documented tradespeople the papers name, whose trade the town never invented, join it as residents
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0368
opened: 2026-08-29
closed: 2026-08-29
pr: 531
claimed_by: run 8/29/2026, 4:48:21 AM CT
blocked_on: null
needs_bake: false
---
Piece 1 of 3 of **T-0368 — The letter lists mint new residents**, split because the
parent is a change of scale rather than a parcel: 1,967 documented people against a
town of 209. This piece takes the slice the evidence can carry first, and the one that
collides with nothing else in flight.

**The cohort, and why it is disjoint from every other ticket in this epic.**
`tools/compile_register.py` gives a person `replace_invented` when the papers read a
trade the town INVENTED a household for, and `new_resident` otherwise. So the people
this piece takes — `new_resident`, a trade the register could read, and known from
something other than a letter list — are by construction the tradespeople the
occupation census never raised a roof for: attorneys, auctioneers, schoolteachers,
milliners, hardware and dry-goods merchants, a surveyor, a watchmaker, a druggist.
T-0366 and T-0367 deal `replace_invented`; T-0373 takes the people with no trade at
all; T-0374 takes the letter lists. None of the four reaches into another's pool.

**They arrive without a roof, and that is not a defect.** Nothing reached says where
any of them slept. `data/town_census.json` already counts 52 households with no
dwelling, so the dataset has always been able to hold a person the sources place in the
town and nowhere in it; that is what these records are. A man the papers put at a
street keeps that street in his own note, and the storefront tickets (T-0263, T-0306)
are still the ones that may stand his shop.

**Acceptance:** (one demonstration, never weakened to pass)

- A derivation, not a list: a tool re-derives the whole minted set from the register,
  the gazetteer and the committed town on every commit, and `check.sh` fails if the
  tree stops matching it.
- Every refusal is printed with its reason, so the ratio of taken to refused is
  auditable rather than asserted.
- No minted resident carries an occupation the papers do not give them — including the
  milliners the trade mapper was reading as millers, which is fixed here because this
  ticket cannot mint an honest trade over it.
- Each minted person is graded `attested` and cites the newspaper run; the household
  around them claims nothing the sources do not say — no dwelling, no division, no
  family.
- `data/residents/index.json` and `data/town_census.json` move additively; no existing
  household loses a member, and the person count is stated before → after with the
  instrument named.
- `tools/smoke_renderer.mjs` reads the new counts on the card at both viewports;
  check.sh green; a changelog entry a visitor can check against the Evidence panel.
