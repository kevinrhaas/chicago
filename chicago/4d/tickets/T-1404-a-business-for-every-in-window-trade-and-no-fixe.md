---
id: T-1404
title: A business for every in-window trade and no_fixed_premises for the trades that carry none, with the physicians' and lawyers' census gaps worked from the research first, the Sept-Dec 1835 crosswalk re-run, and what remains short written to the order book for T-1186
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1182
opened: 2026-09-19
closed: 2026-09-19
pr: 1537
claimed_by: run 9/19/2026, 4:09:13 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T21:56:14.984Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35469364861
---

A business for every in-window trade and no_fixed_premises for the trades that carry none, with the physicians' and lawyers' census gaps worked from the research first, the Sept-Dec 1835 crosswalk re-run, and what remains short written to the order book for T-1186.

Piece 4 of 5 of **T-1182 — Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The parent's clauses 3, 4 and 6, unchanged. Every person whose `roles[]` reaches
1835-07-01 with a trade that implies premises (the `works_trades` + `public_trades` of
the signage rule, plus lawyer/physician offices) and who holds no business role gets one:
`inferred` where a source says they practised in Chicago, never `attested`. Trades that
carry no premises (labourer, teamster, clerk, boatman) get `no_fixed_premises` on the
role instead. The physicians' gap (3 vs 14) and lawyers' gap (18 vs 22) are worked FROM
THE RESEARCH first; what remains short is written to the order book for T-1186, not
invented here. The Sept-Dec 1835 crosswalk is re-run and its deltas re-printed;
documented zeros (bank, lottery office, lyceum) stay zero.

Note for whoever takes it: `data/research/residents/scene_window_trade_audit.json`
already reads `count: 0` on its own rule (a trade at a claiming grade with no source
covering 1835). That is the WRITE gate, not this clause — a person can pass it and still
have no workplace. Do not read the zero as the clause already met.

