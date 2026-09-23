---
id: T-1385
title: Every lodging card printing who lived there, and the crews and the harbour-works gang seated once a committed source gives a complement and a strength
state: split
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1372
opened: 2026-09-19
closed: 2026-09-19
pr: null
claimed_by: run 9/19/2026, 4:08:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T21:48:50.525Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35469356342
---

Every lodging card printing who lived there, and the crews and the harbour-works gang seated once a committed source gives a complement and a strength.

Piece 2 of 2 of **T-1372 — Crews, the works gang and the guest lists: the vessels in port and the pier-works hands seated, and every lodging card printing who lived there**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

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

**THE CREWS AND THE HARBOUR-WORKS GANG ARE NOT IN THIS RUN AND ARE NOT REFUSED.** They
wait on a committed source, as written below — an enrolment return or shipping article
that gives an 1830s lake schooner her complement, and the Chief Engineer's 1835 annual
report for the works' strength. `check_vessels` still FAILS the gate on any hull that
acquires a crew. This piece ships the one half of the ticket that a source already
settles, and the ticket stays open on the half that no source does.

---

**WHAT PIECE 1 LEFT HERE, 2026-09-19.** T-1384 seated the hulls and left every one of them
empty, so this ticket is now exactly two things and a wait.

- **The lodging cards.** Unchanged, and downstream of T-1371, which deals the lodging
  model's surge beds. Nothing about it was touched by the port reading.
- **The crews.** The hulls are seated — `data/reconstruction/1835_vessels_in_port.json`
  names each one, her master, her last port and her cargo, and moors her to the reach — and
  the transient cards already carry a `lodged_at[]` rung of `kind: vessel` that is gated and
  read by the People view. **Only the number is missing.** A committed source that gives an
  1830s Great Lakes schooner its complement — an enrolment or registry return, a shipping
  article, a marine list that prints hands as well as hulls — finishes it with nothing
  unpicked. Until then `check_vessels` in `tools/model_transients_1835.py` FAILS the gate on
  any hull that acquires a crew, which is deliberate: the refusal is now enforced rather
  than merely written down.
- **The harbour-works gang.** Still bounded by nothing. The federal improvement was at work
  through 1835 and no committed source gives its strength in any month;
  `docs/RESEARCH/north_pier.md` names the Chief Engineer's annual report for 1835 as the
  document that would settle it. A strength invented here would be the same defect as an
  invented crew.


**Result (2026-09-19, the lodging cards).** 15 built lodging places now print their
occupancy: 122 people against 135 ordinary-night beds. The Tremont reads 12 of 12 — 2
housed by the layer, 5 seated, 5 drawn; the Green Tree 8 of 8, all of them already under
that roof. The New York House (8 beds, nobody) and the Sauganash (7 beds, 2 seated) print
the ledger's own "no division, no mint" refusal and its "nobody keeps this house in this
dataset" note instead of a bare empty count. 80 reconstruction cards and 17 seats reach
the building card for the first time; nothing is written back into `households/`.
`seats_nobody` — true for one afternoon on 2026-09-19 and false from the moment T-1371
merged — is gone from the compiler and from `popup.js`.
