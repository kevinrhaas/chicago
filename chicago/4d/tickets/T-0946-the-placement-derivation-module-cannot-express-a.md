---
id: T-0946
title: The placement derivation module cannot express a frontage on a street that is not axis-aligned, so the north bank's houses all read not_derivable
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-11
pr: 1148
claimed_by: run 9/11/2026, 3:10:26 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T21:13:53.090Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34642503655
---

**Salvaged from PR #975 by T-0927, 2026-09-07, before that PR was closed as a duplicate of
the landed #974.** Filed there as T-0874; that number was taken on `dev` by another run
while #975 sat open, and the ticket file has never existed on `dev`.

The placement derivation module cannot express a frontage on a street that is not
axis-aligned, so the north bank's houses all read `not_derivable`.

Found while placing the Steamboat Hotel onto the committed street records (T-0812).

`tools/validate.py` knows two derivation methods. `platted_corner` reads a control point
from `data/traces/street_control.json` and a street whose `axis` is `ew` or `ns`, and
asserts a named face against the platted frontage. `traced_waterline` reads a waterline.
There is no third, and 369 of the 374 committed phases declare `not_derivable`.

North of the river that is not a gap in the reading, it is a gap in the VOCABULARY. The
committed `north_water` line is a derived offset curve from the traced bank (T-0307,
T-0447), not a plat: the reach the Steamboat Hotel fronts runs 41.41 degrees east of
north, so it has no `ew`/`ns` axis and no control point can be hung on it. The hotel's
placement now follows a rule that is fully stated and fully recomputable — the facade
7.00 m from the committed centreline, at the station where the clearance from Kinzie
Street's kerb equals the gap to the Council House's footprint — and it still has to
declare `not_derivable`, because nothing can hold it. So does every other building on
that bank: the north-side school, Cobweb Castle, the four Dearborn bank sheds, the
Kinzie & Hunter warehouse, the brickyard, the boatman's cabin.

A `street_frontage` method would take a street id, a face, a setback from the committed
centreline, and re-derive the perpendicular distance from the placed footprint's front
wall to the nearest point on that street's committed path — the same arithmetic
`tools/generate_business_signboards.py::_nearest_on_path` already does to decide which
street a sign faces, so the recipe exists and is in use; it is simply not a gate.

**This is the ticket T-0947 turns on.** Two runs re-derived the same ruling and landed the
Steamboat Hotel 36 m apart, and nothing caught it, because a placement that declares
`not_derivable` is a placement no gate re-computes.

**Acceptance:**

1. A third derivation method is specified — id, face, setback, and what it re-derives —
   in the same place the other two are specified, and it is a gate rather than prose.
2. The Steamboat Hotel's placement re-derives under it, and stops declaring
   `not_derivable`.
3. The count of committed phases declaring `not_derivable` is re-measured and stated
   before and after.
4. No placement moves as a side effect of gaining a derivation. If a record does not
   re-derive to where it stands, that is reported as a finding rather than corrected in
   the same pass.

**Links:** T-0812 · T-0307 · T-0447 · T-0927 · T-0947 · PR #974 (landed) · PR #975 (closed).
