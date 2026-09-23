---
id: T-0094
title: The fort's pickets are flat-topped and dark, where the plate draws them pointed and pale
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-24
pr: 362
claimed_by: run 8/24/2026, 7:57:06 AM CT
blocked_on: null
needs_bake: true
---

The fort's pickets are flat-topped and dark, where the plate draws them pointed and pale.

Found by T-0044's image-accuracy pass on `data/sources/assets/prefire_views_kevin_2026_08/p4_0.png`
— the coloured view of the fort from across the river. The plate's stockade is a line of POINTED
pickets in a pale tone that reads as weathered or whitewashed sawn timber; the model's are flat-topped
and dark. `fort_dearborn_palisade` already records `picket_height_m`, `picket_width_m` and
`picket_spacing_m` as **reconstructed** and says so — a point on the top is the same class of claim and
the plate is the only evidence for it. **The whitewash is a separate question and a trap**: the
whitewashed board fence at this fort belongs to the compound of the 1850s (see the record's own
research note), so the TONE must not be taken from that and needs its own warrant.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The `palisade` archetype tops its pickets, the record carries the new form value at the tier its
evidence earns with the plate cited, and a before/after from `p4_0`'s own stand is committed.
Geometry — needs the nightly bake.

---

## Outcome, 2026-08-24: REFUTED. The acceptance is answered, not weakened.

The ticket is a claim about two pictures, and neither had been measured.
`tools/measure_picket_plate.py` measures both and lands on the opposite of each half.

**Clause 1 — "the archetype tops its pickets" — was already true when the ticket was written.**
`generators/archetypes/palisade.py::_picket` has built a four-triangle sharpened head on every post
since the archetype was written, sized by `PalisadeParams.picket_point_m`, whose own docstring says
*"no source describes the head of a Fort Dearborn picket"*. The committed master agrees
independently: 21,504 picket positions on exactly three heights — 6,144 feet at 0.000 m, 12,288
shoulders at 3.388 m, **3,072 apexes at 3.700 m**, four per post over 768 posts. **0.312 m of head,
8.4 % of the picket.** It reads at the wall and it still reads from `p4_0`'s own stand across the
river. The clause is now HELD rather than merely true: `--gate` in `check.sh` refuses a stockade
whose apexes go flat, get capped, wear under 4 % of the picket, or get stacked on a full-height
post — proved red end to end against a real GLB with its 3,072 apexes rewritten to the shoulder.

**And the plate does not draw them pointed.** `p4_0` rules the curtain's cap straight to **0.45 px
rms** over 138 resolved columns while resolving individual pickets at a **10 px pitch** on a **43
px** wall — so a head of the model's own proportion would have serrated that line by **3.6 px**,
eight times the residual. `p4_1` rules the same flat cap. The draughtsman had the resolution and
drew none. That does not make the head wrong; it makes the plate uncitable for it.

**Clause 2 — "the record carries the new form value" — is HALF DONE, and the half is named.** The
head is now declared where a reader meets it: in the record's own `construction` note, which the
card shows, and in **L179**, which records it as the invention L47 covered in general and never
named. It is NOT a `form` attribute, and cannot be in this run: `generators/mesh_inputs.py` hashes
the resolved archetype parameters, so **any new key under `form` restales the GLB** — verified by
recomputing the hash, not assumed — ~~and there is no Blender on this runner~~. **What needs
baking, if a later run wants the attribute: nothing else.** Add `picket_head_m` (or a `picket_head`
enum) to `form` and to `palisade_params.CONSUMED`, resolve it to the current derived 0.312 m so no
vertex moves, and rebake `fort_dearborn_palisade__picket_1816` alone. The mesh would be unchanged;
only the manifest hash needs a real bake to restamp honestly.

> **THE STRUCK CLAUSE WAS FALSE, AND IT WAS THE INTEGRATOR'S ERROR — corrected 2026-08-24 by
> T-0200, hours later.** The pinned Blender was on that runner the whole time: 4.5.3 LTS at
> `blender-4.5.3-linux-x64`, exactly what `generators/blender.pin` names, and nobody ran
> `--version` before writing the sentence. The hashing half of the paragraph is correct and was
> measured; the "no Blender" half was assumed, and it is the assumption that deferred the work.
> **It is struck rather than deleted** — the finding above it is the ticket author's and stands;
> the excuse under it is not theirs. T-0200 did exactly what the paragraph specified, and the
> paragraph was right about the cost: `form.picket_head_m` = 0.312 m `reconstructed`, asserted
> equal to `PalisadeParams.picket_point_m`'s derivation before it was written, `picket_head_m`
> added to `CONSUMED` with bounds of 4–50 % of the picket, and both palisade masters rebaked on
> the pinned binary. **The mesh did not move: 21,728 vertices compared, 0 moved, and the GLB is
> byte-for-byte the file that stood before** — only `assets/manifest.json` changed,
> `579cb33f…` → `dd0c84b8…`. **L179 now carries the `Covers:` field it deliberately withheld.**

**The tone half needed its own warrant and does not get one.** `p4_0` paints this single continuous
north curtain across a **1.85×** range of tone in one view — median sRGB (200, 191, 158) / lum 191
east of the gate work, (117, 102, 76) / lum 103 west of it — against the fort's own frame range at
183, bare bank earth at 115, the paper at 218. `hewn_log`, the surface shipped, is sRGB
(158, 141, 120), **lum 143: between the plate's two readings of the same wall.** A source that
draws half a stockade darker than the model and half of it paler warrants moving it in neither
direction. The whitewash trap the ticket flagged stands and is refused twice over — Fergus's
board fence is the enclosure of 1850, after the pickets came down.

**Clause 3 — the view from `p4_0`'s own stand is committed**, with no "after" because nothing in
the scene moved: `docs/evidence/t-0094-p4_0-stand.png` is the stand, and
`docs/evidence/t-0094-plate-vs-model.png` puts the plate, that stand and the wall from outside it
in one strip.

**What the plate DOES say about the pickets** — its drawn rhythm is nearly three times coarser than
the model's — is **T-0185**, at the queue bottom. Row 3 of
`docs/RESEARCH/fort_dearborn_image_accuracy.md`, which seeded this ticket, is struck and corrected
in place so the same claim cannot be re-filed off the same sentence.
