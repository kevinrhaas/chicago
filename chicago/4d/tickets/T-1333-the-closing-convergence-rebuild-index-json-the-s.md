---
id: T-1333
title: The closing convergence rebuild: index.json, the sidecars, the town census, the published residents and the final resident audit, with the exact household, person and grade deltas and every retired id's redirect, and acceptances 3, 5 and 9 stated as measured deltas rather than spot readings
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1144
opened: 2026-09-18
closed: 2026-09-18
pr: 1480
claimed_by: run 9/18/2026, 5:45:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T23:15:11.985Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35402702816
---

The closing convergence rebuild: index.json, the sidecars, the town census, the published residents and the final resident audit, with the exact household, person and grade deltas and every retired id's redirect, and acceptances 3, 5 and 9 stated as measured deltas rather than spot readings.

Piece 1 of 2 of **T-1144 — Converge the resident layer after the standing truth tickets: zero synthesis and mint drift, no false Chicago resident, and no 1835 claim above its dated evidence**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. One rebuild derives the whole closing set in the manifest's order — `index.json` and its
   `merged` table, the 1835 sidecars, the town census, the published residents and the final
   resident audit — and every one of them re-derives on a clean tree afterwards. Not five
   tools run by hand in an order nobody wrote down.
2. The report states **deltas, measured**: households, persons and grades, each as a number
   with its before and after, against the tree this ticket opened on. A count with no
   baseline is not a delta and does not close this.
3. Every retired id's redirect is named and **arrives** — no dead end, no chain, no id both
   retired and live. T-1144's redirect leg (PR #1469) built `redirect_faults()` and measured
   66 redirects arriving; this ticket's rebuild keeps that at zero faults rather than
   re-proving it by hand.
4. **Acceptances 3, 5 and 9 are stated here as measured deltas, not re-asserted.** They read
   clean on 2026-09-18 — no Mary Durbin, John Simmons, John Vincent or Logdson;
   `audit_scene_window_trades.py --check` reports 0 standing rows; all 820 uncertain
   households carry their `last_dated_appearance` leg — and T-1144 banked them deliberately
   "to the closing pass to state as deltas rather than claimed closed from a spot reading".
   A spot reading repeated is still a spot reading.
5. The gate re-derives the closing set, so a later branch that moves the town tree cannot
   leave this report stale and green. If a file in the set is not in `derived_manifest.json`,
   that is a finding of this ticket, not a footnote.

**NOT IN SCOPE:** the letter-list mint's drift and the one-letter-apart identity rule. That
is T-1334, it is read by T-1222, and it is a different question from rebuilding the layer.
