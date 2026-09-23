---
id: T-0061
title: Shed roofs have no gable ends, so 55 buildings are open to the sky
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-21
pr: 294
claimed_by: run 8/21/2026, 9:46:32 AM CT
blocked_on: null
needs_bake: false
---

**The owner's report, 2026-08-18, with a screenshot** (standing on Lake Street, SE 126°,
inspecting *Reconstructed D2 rough plank dwelling or shanty #04*): "there are some buildings
with partial roofs like it is supposed to be a slanted roof but it is not rendered correctly."
The frame shows a pale triangular gap where the side wall should close under the slope — you
see through the building to the sky.

**DIAGNOSED, not guessed.** `generators/inferred_placeholder.py` → `record_geometry()`:

```python
if roof_type == "shed":
    rise = min(wall_h * .72, math.tan(pitch) * d)
    quad(groups["roof"], ...)          # the single slope — and that is ALL
else:                                   # gable
    quad(groups["roof"], ...)          # two slopes
    quad(groups["roof"], ...)
    tri(groups["wall"], (0,wall_h,0), (0,ridge,-d/2), (0,wall_h,-d))   # end fill
    tri(groups["wall"], (w,wall_h,-d), (w,ridge,-d/2), (w,wall_h,0))   # end fill
```

**The gable branch fills its end walls with two `tri()` calls; the shed branch has none.**
A shed roof rises from the front wall to the back, which leaves a RIGHT TRIANGLE open on
each side wall, and `box()` only draws walls to `wall_h`. Nothing closes the gap, so the
interior and the sky show through.

**Scale: 55 records carry `roof_type: shed`** (against 254 gable, 5 other), so this is every
shed-roofed placeholder in the town, not a stray.

**The repair** is two `tri()` calls in the shed branch, mirroring the gable ones but sloping
front-to-back instead of to a centre ridge: for each side wall x ∈ {0, w}, the triangle
(x, wall_h, 0) · (x, wall_h+rise, −d) · (x, wall_h, −d). Watch the winding order — the gable
pair is wound opposite on the two ends so both faces point outward; get it wrong and the fill
is invisible from outside, which looks identical to the bug.

**No Blender needed** — this generator writes glTF directly (0 references to `bpy`), so the
improve runner can close it. `tools/check.sh` already asserts "inferred placeholder GLBs match
their records", so regenerate in the same commit or that gate will catch the drift.

**Acceptance:** no shed-roofed placeholder shows a gap from any angle — demonstrated with a
before/after pair from the owner's pose (Lake Street, SE 126°, the D2 shanty) — and a gate
that would have caught it: for every placeholder, the wall+roof surface encloses its volume,
or more simply, the shed branch emits the same face count per side as the gable branch. The
55 regenerated GLBs pass check.sh's existing placeholder assertion.

---

## Re-reported by the owner, 2026-08-21 — and it is the same building again

*"this needs to be fixed still if there is not already a ticket, the roof is incomplete on
these class of dwellings, add a ticket to do a sweep and fix these."* His frame is the dev
preview, standing on Lake Street, with the card open on **Reconstructed D2 rough plank
dwelling or shanty #04** — the identical building as the 2026-08-18 report above.

There was already a ticket: this one. It was diagnosed on the day it was first reported and
has sat open since while the queue ran elsewhere. A duplicate opened on the re-report
(T-0128) was withdrawn in favour of this entry. Taken now.

Nothing about the diagnosis changed; the sweep the owner asks for is the same fix applied to
every placeholder that carries a shed roof, not only the one he happens to be standing at.
