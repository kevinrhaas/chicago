---
id: T-1314
title: Reconstruct the family members the sources COUNT and do not name: the 1840 census bands back-projected onto the bridged heads, as the programme's named_families stage
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1170
opened: 2026-09-18
closed: 2026-09-18
pr: 1453
claimed_by: run 9/18/2026, 6:15:55 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T12:50:53.250Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35338400512
---

Reconstruct the family members the sources COUNT and do not name: the 1840 census bands back-projected onto the bridged heads, as the programme's named_families stage.

Piece 3 of 3 of **T-1170 — Give the attested and inferred heads the families the sources name: spouses, children, kin and dependants from the baptism and marriage registers, the 1840 census rows of heads the layer carries, Andreas and old-settler biographies and the ruled kin ties — inferred where named, reconstructed where only counted**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The `named_families` stage of `data/reconstruction/1835_resident_reconstruction_programme.json`
  is implemented in `tools/reconstruct_residents_1835.py` and writes the members the sources
  COUNT and do not name: an 1840 row's "1 male 5-10" on a head the bridge has already
  matched, an "and family" notice, a baptism naming the child and not the siblings.
- The 1840 bands are back-projected five years and a child under 5 in 1840 — born after
  1835-07-01 — is NOT present. The 1840 row is used ONLY where the head is already an 1835
  resident; the T-0507 line stands for everyone else.
- Every member carries `tier`, `basis` naming the counting row, `seed` and `replaceable_by`,
  and no attested or inferred member is displaced by a reconstructed one.
- Household size distribution before/after printed against the model.

This is the half of T-1170 that RECONSTRUCTS. The half that reads what the sources NAME is
T-1312 (landed) and seating those people is T-1313.
