---
id: T-0804
title: Minifying the published mirror's JSON is a measured 1.99 MB: decide whether the record must stay readable at its own URL
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the decision was made — publish.sh minifies the residents layer (L183) and the mirror is untracked
needs_bake: false
closed_at: 2026-09-10T04:20:11.756Z
claimed_run: null
---

Minifying the published mirror's JSON is a measured 1.99 MB: decide whether the record must stay readable at its own URL.

**Acceptance:** the owner's decision, recorded — and if it is yes, `tools/publish.sh` writes
minified JSON into `site/chicago/4d/` while `data/` stays authored as it is, with the gate
comparing the two by parsed content rather than by bytes.

**Why (T-0722, 2026-09-05).** Measured across the 1,831 published JSON files: 18.90 MB as
shipped, 16.91 MB minified — **1.99 MB**, larger than every other lever found in the tree
put together, and it costs the record nothing structurally: the mirror is generated, the
authored files under `data/` would not change.

**Why it was not just done.** It would make the published record unreadable at its own URL,
and this project publishes records people are meant to be able to open — a resident's card
at `data/residents/households/hh_*.json` is a document, not a payload. That is a decision
about what the mirror is *for*, which is the owner's and not a quiet optimisation. It is
also reversible in one line if he says no.
