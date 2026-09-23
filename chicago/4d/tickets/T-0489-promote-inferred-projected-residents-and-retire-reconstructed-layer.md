---
id: T-0489
title: Promote inferred and projected residents and retire the pre-existing reconstructed resident layer
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
blocked_on: T-0488
needs_bake: false
---

Apply the owner-approved inferred classification to real named people left after T-0488 and remove the current reconstructed-person population so the resident list contains only evidence-based real people until a later reconstruction pass.

A real named person reasonably believed to belong to circa-1835 Chicago but lacking attested-level corroboration remains `grade: inferred`. The weakest evidence-based subset is explicitly tagged `resident_subtype: projected_resident`: the person is documented in at least one relevant source, but residence/identity/profile detail remains thin enough that the model must not imply more certainty. Letter-list-only people with no independent Chicago corroboration belong here rather than in `attested`.

Remove every person whose person `grade` is `reconstructed`. If a household becomes empty, remove the household. Structures or premises created solely to support those reconstructed residents may be removed/abandoned; preserve independently documented or otherwise useful anonymous structures, and remove stale resident/household occupancy links. Do not create replacement residents or relocate the evidence-based population in this pass—the later placement sweep will assign homes and workplaces after the broader circa-3,600-person reconstruction is mature.

**Acceptance:**
- No current resident person remains `grade: reconstructed`; the vocabulary may retain the value for future work, but the count is zero.
- Every retained resident is a real named/documented person or an evidence-supported inferred/projected person; placeholders that merely count unnamed people remain clearly non-individual if retained for source fidelity.
- Letter-list-only residents are no longer automatically attested: independently corroborated identities may be attested, while otherwise qualifying names are inferred/projected.
- `projected_resident` is a stable explicit subtype under `inferred`, and the resident index exposes counts sufficient to filter/summarize it.
- Empty reconstructed households are deleted and the manifest/mirror are rebuilt deterministically.
- Structures created solely for removed reconstructed households are removed or explicitly abandoned; independently documented structures are not deleted merely because a reconstructed occupant once used them.
- No new dwelling/workplace assignment is invented for the retained population.
- The completion PR targets `dev` and hands the evidence-only resident population to T-0490.
