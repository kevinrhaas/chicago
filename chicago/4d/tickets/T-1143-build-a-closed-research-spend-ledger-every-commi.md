---
id: T-1143
title: Build a closed research-spend ledger: every committed research unit is asserted, later-only, outside Chicago, aggregate, refused, unresolved or linked to its owning ticket
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-15
pr: 1363
claimed_by: run 9/15/2026, 1:25:24 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T19:10:09.857Z
claimed_run: null
---

Build a closed research-spend ledger: every committed research unit is asserted, later-only, outside Chicago, aggregate, refused, unresolved or linked to its owning ticket.

**Owner closeout request, 2026-09-15.** The research audit read all 1,034 ticket files and
the committed research layers. `tools/measure_research_spend.py` reports 21,419 units read,
7,769 spent and 13,650 unspent, while `genealogytrails`, `newspapers` and `residents` are not
registered at all. That 13,650 is not a defect count: it mixes later people, people outside
Chicago, aggregates, surname-only rows and explicit refusals with facts that really are waiting.
The missing object is a closed ledger that can tell those classes apart unit by unit.

This ticket owns the accounting contract. It does not mint a person from every name and it does
not turn later evidence into an 1835 fact. A research unit is spent when it either reaches a
structured attested/inferred assertion, or carries a durable disposition explaining why it must
not. `unresolved` is temporary and must name the open ticket that owns the decision.

**Acceptance:**

1. Register every committed research domain, including `genealogytrails`, `newspapers` and
   `residents`, in `data/research/domains.json`, with the file patterns and stable unit id that
   define what one reading is. A file or row matched by no domain fails.
2. Generate one ledger row per unit with exactly one disposition: `asserted`, `later_only`,
   `outside_chicago`, `aggregate_only`, `refused`, or `unresolved`. An asserted row names the
   resident/household/business/structure id and exact structured field path it supports; a
   refusal names its rule and evidence; an unresolved row names an open ticket.
3. Preserve the present second-hop guarantee: every adjudicated person ruling still reaches its
   card. The 2026-09-15 baseline is 1,643 reached, 1,643 on a card, zero unwritten and zero without
   a stated source; remeasure rather than hard-code that count.
4. Extend `measure_research_spend.py` so it prints disposition totals per domain and fails on an
   unclassified unit, a dead target, a closed/missing unresolved ticket, or an attested/inferred
   assertion named only in prose. Keep the old read/spent figures for comparison.
5. Commit the generated ledger and a concise `docs/RESEARCH/` report containing the before/after
   totals and every unresolved ticket. Wire `--check` and a mutation self-test into `check.sh`.

**Stop condition:** zero unclassified units. A nonzero `later_only`, `outside_chicago`,
`aggregate_only` or `refused` count is an honest completion, not a reason to invent facts.

**Links:** T-0513 · T-0602 · T-0632 · T-0678 · T-0962 · T-0989 · T-1025 · T-1147.
