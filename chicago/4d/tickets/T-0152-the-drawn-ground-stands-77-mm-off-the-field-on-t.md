---
id: T-0152
title: The drawn ground stands 77 mm off the field on the new east slopes
state: done
epic: RENDERING
requested_by: loop
seen: true
effort: M
legacy_id: R-W6(b)
parent: T-0012
opened: 2026-08-22
closed: 2026-08-23
pr: 320
claimed_by: run 8/23/2026, 12:18:46 AM CT
blocked_on: null
needs_bake: true
---

The drawn ground stands 77 mm off the field on the new east slopes.

Piece 2 of 2 of **T-0012 — Ship the 16-bit ground the script already computes**, split
because the parent needed more than one run's demonstration to be done. This piece is the
parent's third acceptance clause — worst error ≤ 13 mm — and it is RED, for a reason that
did not exist when the parent was written.

**Measured 2026-08-23, `node tools/measure_terrain_horizontal.mjs`, on the 16-bit ground
that ships today:**

| | R-W6, 2026-08-16 | today |
|---|---|---|
| lattice | 76.6 mm | 76.6 mm |
| drawn surface vs the field, after conforming | 1.4 rms / 3.8 p99 / **12.9 max** | 1.5 / 3.9 / **77.1** |
| samples past the 22 mm road lift | **0** | **56** (20 on dry ground) |
| median slope of those samples | — | **62 %** |

The bit depth did not move. **The ground did.** R-W6 named the mechanism — the cost is
(slope × displacement), and "flat platted prairie cannot show this artefact at any bit
depth" — and the terrain has since been extended east to the harbour mouth, which brought
in bank faces far steeper than anything the 16-bit answer was measured against. The worst
sample stands at E 60.0 N -175.0 on an **87 % slope**. The nearest to a street is 0.1 m
from the centreline of North Water Street, where the drawn ground is 25.0 mm BELOW the
field — so the road it carries floats rather than being buried, which is the same defect
the other way up.

**R-W6 wrote down what to do about exactly this, and named the trigger.** It declined the
skirt split — 1.5 km of apron on each side is what sets the quantisation volume — and
said: *"Reopen it if a future epoch's box grows or the ground gets a tighter consumer than
the road lift."* The box grew. 16 bits is the format's maximum, so raising the depth again
is not available; shipping the master uncompressed is +5.8 MB against a 22.32 MB payload
and a 25 MB budget, so that is not available either.

**Sized as its own ticket because it is its own demonstration:** a generator change in
`generators/terrain_gen.py`, a proposed amendment to `docs/GLB-CONTRACT.md` (bilateral —
propose, do not change unilaterally), and a terrain bake.

**Acceptance:** the drawn ground, measured at all 259,689 of the field's own sample points
after `conformGroundToField()`, is within the 22 mm road lift everywhere — 0 samples past
it — and `tools/measure_terrain_horizontal.mjs` says so on the bytes that ship.

**Links:** T-0012 (parent) · ROADMAP R-W6 (the table and the reopen condition), R-BUG3c ·
T-0151 (the other piece) · `docs/GLB-CONTRACT.md`.
