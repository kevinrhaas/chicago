---
id: T-0487
title: Adjudicate the complete resident research corpus against newspaper and census evidence
state: done
epic: META
requested_by: owner
seen: true
effort: L
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-02
pr: 668
claimed_by: null
blocked_on: null
needs_bake: false
---

Adjudicate the completed resident-research programme as one corpus before canonical promotion. The twelve completed research cohorts cover 836 named non-reconstructed residents/candidates; their findings, candidate identities, negative searches and source records must be reconciled with the completed newspaper letter-list sweep and the available 1840 Chicago census/name-crosswalk research.

The purpose is identity resolution, not bulk assertion. Preserve contradictory geography, OCR/name variants, candidate matches and negative searches. A candidate record is not a resident fact until the evidence bridges the identity. Census evidence five years after the 1835 scene date may corroborate identity and later household composition, but must not silently back-project 1840 ages, children, spouses, occupations or addresses into 1835.

**Owner classification ruling (2026-09-02):**
- `attested`: a named circa-1835 Chicago resident whose identity/residence is confidently corroborated by the available evidence; retain all supporting source IDs/citations.
- `inferred`: a real named person reasonably believed to be a circa-1835 Chicago resident but not strong enough for attested status.
- `inferred` / `projected_resident`: a named person seen in at least one relevant source (including a qualifying post-office letter-list record) for whom the evidence remains too thin or geographically ambiguous to assert a stronger profile. This remains filterable under the top-level inferred grade.
- `reconstructed`: reserved for a later, explicit reconstruction pass and not part of the current resident population.

**Acceptance:**
- Every completed research cohort/findings ledger is included exactly once and the cumulative reviewed set reconciles to the programme total.
- Every researched person receives a deterministic adjudication outcome with retained source IDs and reasoning.
- Letter-list evidence is tested against independent research and census evidence rather than automatically treated as proof of residence.
- Candidate identities remain unasserted where the evidence does not bridge them.
- 1840 census links retain census serial/page/row/name confidence/mapping confidence and are explicitly dated as later evidence.
- The adjudication output is machine-readable and human-reviewable, and no canonical resident facts are silently changed in this ticket.
- The completion PR targets `dev` and hands a stable adjudication ledger to T-0488.
