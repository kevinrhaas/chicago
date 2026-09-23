---
id: T-1407
title: The crews of the vessels in port and the harbour-works gang seated, once a committed source gives a schooner her complement and the works their strength
state: blocked-tech
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1385
opened: 2026-09-19
closed: null
pr: null
claimed_by: null
blocked_on: a committed source giving an 1830s Great Lakes schooner her complement (an enrolment or registry return, a shipping article, or a marine list that prints hands as well as hulls), and the Chief Engineer's 1835 annual report for the harbour works' strength — the project holds neither, and an invented crew or strength is the defect this ticket exists to refuse
needs_bake: false
closed_at: null
claimed_run: null
---

The crews of the vessels in port and the harbour-works gang seated, once a committed source gives a schooner her complement and the works their strength.

Piece 2 of 2 of **T-1385 — Every lodging card printing who lived there, and the crews and the harbour-works gang seated once a committed source gives a complement and a strength**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**WAITING ON A DOCUMENT, NOT ON A DECISION.** T-1384 seated the hulls and left every one
of them empty; `data/reconstruction/1835_vessels_in_port.json` names each vessel, her
master, her last port and her cargo, and moors her to the reach, and the transient cards
already carry a gated `lodged_at[]` rung of `kind: vessel`. Only the number is missing.

- **The crews.** A committed source that gives an 1830s Great Lakes schooner her
  complement — an enrolment or registry return, a shipping article, a marine list that
  prints hands as well as hulls — finishes this with nothing unpicked. Until then
  `check_vessels` in `tools/model_transients_1835.py` FAILS the gate on any hull that
  acquires a crew, which is the refusal enforced rather than merely written down.
- **The harbour-works gang.** Still bounded by nothing. The federal improvement was at
  work through 1835 and no committed source gives its strength in any month;
  `docs/RESEARCH/north_pier.md` names the Chief Engineer's annual report for 1835 as the
  document that would settle it. A strength invented here would be the same defect as an
  invented crew.

A run that finds either document unblocks this ticket and seats the people. A run that
does not must leave both empty: the hulls are already waiting.
