---
id: T-0490
title: Final resident, household and occupation citation and coverage audit
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-02
pr: 668
claimed_by: null
blocked_on: T-0489 must land the inferred-resident and household integration on dev.
needs_bake: false
---

Perform the closing audit of the resident programme after both attested and inferred updates have landed. This ticket establishes that the final 1835 population/household/occupation data can be traced back through the research corpus, that attested and inferred claims remain distinguishable, and that unresolved evidence has not been silently converted into fact.

Use the complete research corpus and the wider reference set: cohort artifacts, identity master, attested/inferred change ledgers, 1830 and 1840 census work, 1833–34 voter lists, letter lists, newspapers, directories, land/property/tax, probate, church/marriage, naturalization/immigration, military and published histories/reminiscences.

**Acceptance:**

- Audit every canonical resident/person and every inferred household member for stable ID, evidence class, scene-date status and usable provenance.
- Every asserted name, household membership, occupation/trade, kinship, address/property, arrival/migration and civic/voter fact has a source citation or an explicit inference record; no material attribute relies only on prose notes or chat history.
- Attested and inferred records are machine-distinguishable and user-facing provenance does not present inference as direct documentary attestation.
- Run duplicate and identity-conflict checks across all aliases/spelling variants and the census/voter/letter-list crosswalks; unresolved competing candidates remain visible.
- Reconcile household/population totals and demographic constraints against the available census material without forcing false exactness where the historical sources are aggregate or incomplete.
- Produce `chicago/reference/resident-research/final/audit/` containing a master XLSX, CSV and README/coverage report with at least: canonical person ID, household ID, evidence class, research-ticket provenance, source coverage by category, unresolved flags, and audit result.
- Report coverage metrics for identities, occupations, household membership, kinship, property/address, voter/civic evidence and census linkage, plus a named list of remaining research gaps.
- File follow-up tickets for material unresolved gaps that can be improved with identifiable sources; do not keep the final audit open merely because historical evidence is genuinely unavailable.
- Re-run resident compilers, source/sidecar validators, canonical/published mirror checks and relevant project gates.
- The completion PR targets `dev` and becomes the closing receipt for the resident-research programme: it reports final attested count, inferred count, unresolved count, households, occupation coverage and citation coverage.
