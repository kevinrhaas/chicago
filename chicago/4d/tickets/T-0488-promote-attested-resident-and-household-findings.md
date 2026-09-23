---
id: T-0488
title: Promote attested resident and household findings from the adjudicated research corpus
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
blocked_on: T-0487
needs_bake: false
---

Promote the high-confidence findings adjudicated by T-0487 into the canonical resident and household records. Preserve provenance at the attribute level and retain the complete research trail.

Where the evidence supports it, make resident profiles substantially more useful: normalized identity/name variants, age or birth-year bounds, sex where stated, marital/kin relationships, children/household members, occupation/trade, Chicago arrival chronology, origin, later census links, and documented business relationships. Update business or structure records only when the source actually identifies a business/premises/structure; do not assign a dwelling or workplace merely because one is convenient in the model.

**Acceptance:**
- Every promoted person remains traceable to the T-0487 adjudication and source registry.
- Attested facts cite source IDs that resolve in `data/sources/`; conflicting readings remain visible in notes/research metadata.
- Household members are added only when named or counted by evidence strong enough to support the relationship; no surname-only kinship inference.
- 1840 census household composition is stored as dated later evidence unless another source supports back-projection to 1835.
- Occupation, arrival, marital/kinship and business facts are promoted conservatively and do not overstate source precision.
- Canonical resident index/mirrors and any touched business/structure records remain internally consistent.
- T-0489 receives the remaining unasserted/inferred/projected set after the attested promotion.
