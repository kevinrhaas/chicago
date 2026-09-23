---
id: T-0103
title: Every platted-block roof faces away from the street it fronts
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-24
pr: 356
claimed_by: run 8/24/2026, 4:51:09 AM CT
blocked_on: null
needs_bake: false
---

Every platted-block roof faces away from the street it fronts.

Found while building the South Water row (T-0101). `docs/GLB-CONTRACT.md` pins `rotation_deg` as
the **facade bearing, 0 = facing north**. `tools/generate_block_infill.py`'s `place()` derives
that bearing from `inward` — the vector pointing from the lot's street edge INTO the lot — so
every roof it has placed looks at the middle of its own block. A north-tier lot fronting South
Water gets 180.3°; every documented store on the same face carries 0.0°. The alley-facing yard
buildings carry the same flip in the other direction.

The frontage runs of T-0101 take the block face's own outward bearing and are correct. The rest
of what this generator has placed is not: **76 roofs across twelve blocks**, on the Lake,
Randolph and alley faces.

The fix is small — where `place()` takes its bearing from — and the cost is that 76 records move
with it, along with every derivation that reads their world polygons (dooryard pickets,
signboards, yard goods, sidecars, placeholder manifest entries). It is its own revertible unit
and its own before/after frame, which is why it was not swept into T-0101.

**Acceptance:** every roof this generator places fronts the street or alley the recipe says it
fronts, demonstrated in a frame at a station where the flip is visible, with the gates green and
the moved records' derivations regenerated in the same commit.

**Links:** docs/GLB-CONTRACT.md § pinned conventions · T-0101 · docs/LIBERTIES.md L142.
