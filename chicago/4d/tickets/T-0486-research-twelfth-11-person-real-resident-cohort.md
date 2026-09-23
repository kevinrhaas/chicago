---
id: T-0486
title: Research twelfth 11-person real-resident cohort
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-02
pr: 663
claimed_by: chatgpt-resident-agent-sol56 9/2/2026, 5:10 PM CT
blocked_on: null
needs_bake: false
---

Continue the resident-identity research programme with a fixed, non-overlapping 11-person cohort of real named residents. This queue ticket is the twelfth continuation after the pilot and passes 2–5 (375 reserved IDs). The frozen manifest for this ticket contains 0 scene-date letter-list names and 11 earlier/uncertain letter-list names; no named non-letter-list profiles remain in the eligible pool.

Exclude every reconstructed or hypothesised `inf_*` person and every unnamed/count placeholder. Do not infer heritage, ethnicity, immigration origin, kinship, marriage, occupation, address or household membership from a surname or an unsupported same-name match. Preserve competing candidates, spelling variants, contradictory geography and negative searches as explicit research outcomes rather than merging them into resident facts.

Use the repository source register plus external primary, institutional and strong local-history sources where available: newspapers, directories, census and voter material, land/property, probate, naturalization/immigration, marriage/church, military and published reminiscences. Record query strings, source URLs/IDs, access date, source tier and limitations in the findings/source ledgers. Every manifest member must receive a dated outcome: corroborated enrichment, candidate identity/duplicate lead, or documented no-corroboration; pending work must not be represented as a no-find.

Repository handoff is part of the ticket. Commit a cohort research package under `chicago/reference/resident-research/T-0486/` following `chicago/reference/resident-research/README.md`: a human-reviewable XLSX workbook, a machine-readable CSV export, and a README/method note, plus the filled JSON findings ledger and all new/updated source records. The workbook must retain stable person IDs, transcribed and normalized names, outcome/confidence, proposed facts, evidence for and against, candidate identities, source IDs/URLs/tiers, queries, access dates and notes. Findings that exist only in chat, browser notes or an unpushed working tree do not count.

**Acceptance:**

- The committed manifest contains exactly 11 unique person IDs and proves no overlap with the pilot, passes 2–5, or another remaining-cohort manifest.
- The manifest’s deterministic selector is reproducible from the remaining letter-list-only pool: sorted person IDs within present/uncertain strata, interleaved, then chunked in this fixed order.
- Reconstructed, hypothesised `inf_*`, unnamed/count placeholders and weak surname matches remain excluded; no silent household edits are made.
- Each member has a retained research outcome, candidate/conflict record where appropriate, and source limits; negative searches are documented rather than treated as proof of nonexistence.
- No manifest entry is `pending` in the completion PR; the XLSX, CSV, README, findings ledger and source records are all committed and mutually traceable by stable person/source IDs.
- The source registry/ledger, research note, status/roadmap/changelog references and published mirror move together when the research tranche is completed.
- Relevant JSON/selector/compiler checks pass, and any environment-only smoke limitation is reported rather than bypassed.
- The completion PR targets `dev`, records the cumulative reviewed total (836 after this cohort), and closes this ticket only after all research artifacts are committed. The already-merged planning scaffold reserves the cohort; it is not completion.
