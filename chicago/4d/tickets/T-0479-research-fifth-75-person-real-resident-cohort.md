---
id: T-0479
title: Research fifth 75-person real-resident cohort
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-02
pr: 650
claimed_by: chatgpt-resident-agent-a7c4f2 9/2/2026, 3:26:42 PM CT
blocked_on: null
needs_bake: false
---

Continue the resident-identity research programme with a fifth fixed, non-overlapping 75-person cohort drawn only from real named residents. Exclude every reconstructed or hypothesised `inf_*` person, every explicitly unnamed/count placeholder, and every person already selected by the pilot, pass 2, pass 3, or the in-progress T-0478 pass-4 selector.

Four prior cohorts consume 100 non-letter-list selections. The current manifest contains only nine remaining non-letter-list entries that are both real and individually named: Oscar Pratt, Gholson Kercheval, Walter Kimball, Henry S. Lampman, Benjamin Hall, Harriet Murphy, Charles H. Taylor, Peter Temple and John S. Wright. T-0479 therefore exhausts those nine rather than duplicating six prior profiles merely to preserve the earlier 25/25/25 ratio. The remaining 66 places are split evenly between 33 scene-date postal-list names and 33 earlier/uncertain postal-list names. This 9/33/33 distribution is a consequence of cohort exhaustion, not a change in evidence standards.

Research each selected person as deeply as the evidence permits using the repository reference corpus plus external primary, institutional and strong local-history sources: newspapers, directories, voter lists, census material, land/property, probate, naturalization/immigration, marriage/church records, military records and published reminiscences. A surname is a search clue only. Do not infer heritage, ethnicity, immigration origin, kinship, marriage, occupation or household membership from a surname or an unsupported name match.

For ambiguous identities, preserve one or more candidate records with explicit supporting and conflicting discriminators rather than merging them into resident facts. A generic exact-name match without a dated Chicago/Cook County, occupation, address, relative, migration, civic or document linkage is insufficient. Negative searches are valid documented outcomes and are not evidence that the person did not exist.

PR #625 was the initial tranche, not completion: 66 postal-list members remained explicitly pending. The remaining research can proceed in parallel with pass 4; only cumulative compiler/sidecar integration must be reconciled after the T-0478 baseline lands. The completion work must commit a cohort research package under `chicago/reference/resident-research/T-0479/` following `chicago/reference/resident-research/README.md`: a human-reviewable XLSX workbook, a machine-readable CSV export, and a README/method note, plus the completed JSON findings ledger and all new/updated source records. Findings that exist only in chat, browser notes or an unpushed working tree do not count.

**Acceptance:**

- A committed reproducible pass-5 selector and manifest contain exactly 75 unique real named residents: all nine remaining named non-letter-list people, 33 scene-date postal-list people and 33 earlier/uncertain postal-list people.
- The selector proves no overlap with the first three merged cohorts and carries a frozen collision lock for all 75 IDs claimed by the T-0478 pass-4 selector.
- Reconstructed people, hypothesised `inf_*` people, and entries whose names explicitly denote an unnamed/count placeholder are rejected even if their technical grade is not `reconstructed`.
- Every cohort member has an outcome: corroborated enrichment, explicit candidate identity/duplicate lead, or documented no-corroboration result; no member remains `pending` in the completion PR.
- The XLSX, CSV, README, findings ledger and source records are committed and mutually traceable by stable person/source IDs; the workbook retains evidence for/against, candidate identities, source tiers, queries, access dates and limitations.
- New sources are recorded in the resident source ledger/source registry with source tier, query/result and limitations; only high-confidence facts are promoted into household/person data.
- Any household edits carry per-attribute provenance and preserve conflicting evidence instead of overwriting it silently.
- Research may complete in parallel with T-0478; cumulative compiler/sidecar integration is reconciled onto the pass-4 baseline before this ticket closes.
- A research note records methods, strongest findings, candidate/no-find counts, limits and the cumulative reviewed total.
- Relevant JSON/selector/compiler checks pass; any environment-only smoke limitation is reported rather than bypassed.
- A completion PR targets `dev` and records the pass-5 results and continuation baseline; PR #625 alone does not close this ticket.

**Completion:** merged PR #650 supplies the completed 75-person findings ledger, source records, durable XLSX/CSV/README package, selector/gates, and cumulative 375-review integration on `dev`.