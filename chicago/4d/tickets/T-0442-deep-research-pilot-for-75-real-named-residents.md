---
id: T-0442
title: Deep research pilot for 75 real named residents
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-08-31
pr: 609
claimed_by: run 8/31/2026, 3:36:41 AM CT
blocked_on: null
needs_bake: false
---

Research and enrich a stratified 75-person pilot drawn only from attested or inferred real
residents. Exclude every reconstructed person. The cohort must include both residents with
existing occupational evidence and names known only from post-office letter lists. Treat a
name match as a candidate until corroborated; preserve competing identities and explicit
non-matches rather than silently combining people.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A committed, reproducible cohort manifest names exactly 75 non-reconstructed residents and
  records why each was sampled.
- Every cohort member receives a research outcome: corroborated enrichment, one or more
  candidate identities, or a documented no-finding result with the searches and sources tried.
- Enrichments use resolving repository source records and per-attribute provenance; ambiguous
  facts remain candidates and never become asserted household facts.
- A durable research-source ledger ranks source types and records every consulted source,
  including negative and conflicting findings.
- Resident cards visibly expose new corroborated details and candidate-identity warnings.
- `tools/check.sh`, the published-tree gate, and relevant mobile/desktop resident-card smoke
  checks pass; the PR reports before/after coverage and findings for the pilot.
