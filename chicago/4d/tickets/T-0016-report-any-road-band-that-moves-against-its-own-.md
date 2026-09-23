---
id: T-0016
title: Report any road band that moves against its own bank
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: M
legacy_id: R-M1d
parent: null
opened: 2026-08-17
closed: 2026-08-23
pr: 324
claimed_by: run 8/23/2026, 6:32:32 AM CT
blocked_on: null
needs_bake: false
---

A band collapsed 55 points (71 % → 16 %) and the suite said "229/2 before, 229/2 after" —
the gate is per station, the measurement per band. Bank each gated band's figure and REPORT
movement against it, both directions; a report, not a new bar. Deep history: § R-M1d (~7815).

**Acceptance:** replay R-W1's merge and the tool names south_water 250–600 m unprompted;
no threshold moves.
