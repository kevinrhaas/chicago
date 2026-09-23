---
id: T-0356
title: The claim vocabulary cannot say an advertisement announces an opening, so 17 businesses are excluded on a proxy
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 552
claimed_by: run 8/29/2026, 12:26:58 PM CT
blocked_on: null
needs_bake: false
---

T-0262 asked the register to exclude businesses "whose only 1835 evidence
`announces_opening` AFTER Jul 1". There is no `announces_opening` in the claim
vocabulary — the ticket describes a field `tools/compile_gazetteer.py` never grew — so
the register uses the derivable proxy instead: `first_evidence_after_scene_date`, a
business whose FIRST issue postdates 1835-07-01. Seventeen businesses.

The proxy is conservative in the right direction and it is not the same question. A
firm advertising for the first time on 8 August 1835 may well have been trading in
July; an advertisement that says "will OPEN on the first of September" is evidence it
was not. The register cannot tell those apart, so it excludes both and says so.

The fix is a field on the claim, not a heuristic: a business claim that announces an
opening carries the announced date, the extraction records it, and the register
excludes on the DATE rather than on the absence of earlier evidence.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The claim schema carries an opening announcement with its date, gated like every
  other claim field, with the quote machine-checked as usual.
- The seventeen `first_evidence_after_scene_date` businesses are re-read and each is
  either genuinely excluded (an announced opening after the scene date) or restored.
- The register's exclusion reads from the field; the proxy is removed, not kept beside
  it.
