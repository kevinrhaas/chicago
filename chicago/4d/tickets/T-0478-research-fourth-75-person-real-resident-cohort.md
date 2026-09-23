---
id: T-0478
title: Research fourth 75-person real-resident cohort
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-02
pr: 641
claimed_by: steward/resident-research-pass-4-reconciled
blocked_on: null
needs_bake: false
---

Complete and land the fourth fixed 75-person resident-research cohort already preserved on `steward/resident-research-pass-4-reconciled`. The branch carries `pass_04_75_cohort.json` with 25 established profiles, 25 scene-date letter-list people and 25 earlier/uncertain letter-list people, for a cumulative 300 researched/reserved people after passes 1–4. It also carries authored findings with explicit corroborated enrichments, candidate identities and documented no-corroboration outcomes.

Do not redo or discard that research merely because the file-backed queue ticket was missing from `dev`. Reconcile the existing branch onto current `dev`, preserve its source records and findings, and bring its durable research handoff up to the same standard as passes 5–12.

Repository handoff is part of the ticket. Commit a cohort research package under `chicago/reference/resident-research/T-0478/` following `chicago/reference/resident-research/README.md`: a human-reviewable `T-0478_resident_research_working.xlsx`, a machine-readable `T-0478_resident_research.csv`, and a `README.md` method/source note, plus the completed JSON findings ledger and all new/updated source records. The workbook must retain stable person IDs, transcribed and normalized names, outcome/confidence, proposed facts, evidence for and against, candidate identities, source IDs/URLs/tiers, queries, access dates and notes.

**Acceptance:**

- Preserve the existing fixed manifest of exactly 75 unique people and prove no overlap with the first 225 reviewed people or later frozen cohort manifests.
- Preserve and validate the authored pass-4 findings rather than replacing omitted members with unexamined `pending` entries; documented no-corroboration remains a valid outcome when its search scope is recorded.
- Every member resolves to corroborated enrichment, candidate identity/duplicate lead, or documented no-corroboration; no member remains `pending` in the completion PR.
- The XLSX, CSV, README, JSON findings ledger and source records are committed and mutually traceable by stable person/source IDs.
- Candidate identities remain unasserted canonical facts unless their evidence independently reaches the later attestation threshold; conflicts and spelling variants stay visible.
- Any scene-date/presence or other population update carries the exact source and reasoning that justifies it.
- Reconcile cumulative compiler and sidecar outputs onto current `dev` without deleting newer resident research, reference files, tickets or generated artifacts.
- Relevant selector/compiler/source/published checks pass or inherited repository failures are explicitly separated from pass-4 regressions.
- The completion PR targets `dev`, records the cumulative reviewed total of 300 after pass 4, includes the durable research package, and closes T-0478.
