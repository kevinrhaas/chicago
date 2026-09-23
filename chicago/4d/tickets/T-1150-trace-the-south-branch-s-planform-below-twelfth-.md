---
id: T-1150
title: Trace the South Branch's planform below Twelfth Street from a source that reaches Cermak
state: done
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0465
opened: 2026-09-15
closed: 2026-09-15
pr: 1367
claimed_by: run 9/15/2026, 4:36:33 PM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-15T23:25:27.533Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35026266671
---

Trace the South Branch's planform below Twelfth Street from a source that reaches Cermak.

Piece 2 of 4 of **T-0465 — Trace the South Branch and early lakefront through the expanded field**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance:** a period sheet that reaches Cermak is pinned, georeferenced the way
Wright 1834 was (`data/traces/gcp/*`, an affine fit with a stated RMS), and the South
Branch traced onto it from Twelfth Street south; `southern_branch` is then DELETED from
the terrain spec rather than amended, and L239 moves to Resolved.

**What T-1149 measured while sizing this, so it is not rediscovered.** The three
georeferenced sheets this corpus holds — Wright 1834, Hathaway 1834 and the Thompson
1830 plat — all end on the School Section's south line, which is why `evidence_limit`
sits at N -2149.4. So this ticket is blocked on ACQUISITION, not on effort. The obvious
source, the 1821 GLO township plat of T39N R14E (it covers North Avenue to 31st Street,
the lake to Crawford, and carries both the South Branch and the lake meander line), is
served from `glorecords.blm.gov` behind a login: its `api/SurveyPlats` endpoint answers
401 with a redirect to `/login` and its `results/` page 301s, so an unattended run
cannot fetch it. Reachable and worth trying next: Digital Commonwealth's IIIF (which
already serves Wright), the Library of Congress maps API, CARLI, and David Rumsey's
LUNA search — all four answered 200 from this runner on 2026-09-15. A canal-era sheet
(the I&M Canal surveys, or the Canal Trustees' subdivisions of sections 21, 28 and 33)
covers exactly this reach and is the likeliest find.
