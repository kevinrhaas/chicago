---
id: T-0367
title: The documented tradesmen the papers DO place need roofs on their own street, and the deal has no way to ask
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0264
opened: 2026-08-29
closed: 2026-08-29
pr: 529
claimed_by: run 8/29/2026, 4:42:09 AM CT
blocked_on: null
needs_bake: false
---

Piece 2 of 3 of **T-0264 — Documented people replace the invented**, split because the
parent needed more than one run's demonstration to be done.

**T-0366 refused 26 documented tradesmen for one reason: the papers say where they
were.** J. K. Botsford advertised at the corner of Dearborn and Lake; D. Graves baked
on South Water Street; L. W. Montgomery made boots on South Water; John T. Temple is on
Lake Street and South Water both. Every one of them practises a trade this town invented
a household for, and every one of them was refused, because the reconstructed roof the
deal would have reached for stands wherever the occupation census put it — which is
almost never the street the man advertised from. Moving him there would contradict the
advertisement that names him.

`tools/replace_invented_residents.py --report` prints the 26 with their places. What it
cannot do is ASK where a reconstructed roof stands: a household's dwelling is a
structure id, and its street lives in a placement note in prose, not in a field.

**Acceptance:** (one demonstration, never weakened to pass)

- A reconstructed dwelling can be asked which street it fronts, derived from the
  committed geometry rather than read out of a note.
- A placed documented tradesman takes a reconstructed roof ONLY on the street his own
  record names; where no roof of his trade stands on that street he stays refused, and
  the refusal says which street was wanted and what stood there instead.
- Before → after on the invented-person count, and every new card carries its citation.
- The refusals T-0366 printed shrink by exactly the number this ticket seats, and the
  report says so.

Related: **T-0263** and **T-0306** place the BUSINESSES on those same streets; a man
whose shop those tickets stand somewhere must not be given a dwelling that fights it.
