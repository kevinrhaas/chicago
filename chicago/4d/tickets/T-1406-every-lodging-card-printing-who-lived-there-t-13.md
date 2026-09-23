---
id: T-1406
title: Every lodging card printing who lived there: T-1371's boarders, keepers and seats on the building card, with the empty beds named
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1385
opened: 2026-09-19
closed: 2026-09-19
pr: 1536
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T21:49:12.003Z
claimed_run: null
---

Every lodging card printing who lived there: T-1371's boarders, keepers and seats on the building card, with the empty beds named.

Piece 1 of 2 of **T-1385 — Every lodging card printing who lived there, and the crews and the harbour-works gang seated once a committed source gives a complement and a strength**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

- Every lodging place's card prints who is on it, compiled from T-1371's own ledger:
  the count against the ordinary night's beds, and the ways into a bed kept apart —
  housed here by the residents layer, seated here from elsewhere in it, drawn against
  the order book, a keeper drawn for a roof this programme raised.
- The 80 cards `data/residents/lodgers/` holds — 75 drawn lodgers and 5 drawn keepers —
  reach the building card, which `data/residents/index.json` cannot carry them to
  because that manifest summarises `households/` alone.
- The 17 seats given to people the layer already holds appear on the house they were
  seated in, and NOTHING is written back into their research cards.
- An empty bed is printed with the ledger's own refusal beside it or it is not printed
  as empty; no sentence of the compiler's own invention stands in for a reason.
- A lodger's trade stays blank, because T-1371 refused to draw one.
- `tools/check.sh` green; the smoke parts covering the diff green.

**Result (2026-09-19, PR #1536).** 15 built lodging places print their occupancy: 122
people against 135 ordinary-night beds. The Tremont reads 12 of 12 — 2 housed by the
layer, 5 seated, 5 drawn; the Green Tree 8 of 8, all of them already under that roof.
The New York House (8 beds, nobody) and the Sauganash (7 beds, 2 seated) print the
ledger's own "no division, no mint" refusal and its "nobody keeps this house in this
dataset" note instead of a bare empty count. 80 reconstruction cards and 17 seats reach
the building card for the first time; nothing is written back into `households/`.
`seats_nobody` — true for one afternoon on 2026-09-19 and false from the moment T-1371
merged — is gone from the compiler and from `popup.js`.

One smoke fixture repointed and no case dropped: the Sauganash was the card-order
assertion's example of a building with NO households and now has two, so `log_jail` —
the fixture the neighbouring no-household check already uses — witnesses the
five-section order and the Sauganash witnesses the six-section one.
