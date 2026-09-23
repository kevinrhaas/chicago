---
id: T-0200
title: The picket head is a form value on the record, and the reason it was deferred was false
state: done
epic: TOWN
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-24
pr: 379
claimed_by: run 8/24/2026, 2:06:24 PM CT
blocked_on: null
needs_bake: true
---

The picket head is a form value on the record, and the reason it was deferred was false.

T-0094 closed with a named half undone and gave two reasons for it. The first is true and was
measured: `generators/mesh_inputs.py` hashes the resolved archetype parameters, so a new key under
`form` restales the GLB. The second — *"and there is no Blender on this runner"* — is **false.**
The pinned build is installed and matches `generators/blender.pin` exactly: Blender **4.5.3 LTS**
at `blender-4.5.3-linux-x64`. Nobody checked before deferring, and the same false clause was
mirrored into `docs/STATUS.md`. This ticket does the work that reason deferred and corrects the
record of why it was deferred.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `picket_head_m` is a `form` attribute on `fort_dearborn_palisade`, in
   `palisade_params.CONSUMED`, with validation bounds, and the derived proportion stays as the
   fallback for a palisade record that states no head — the garrison garden's worm fence is
   untouched.
2. The value is **not hardcoded**: it is asserted equal to what
   `PalisadeParams.picket_point_m` derives from the record's own resolved parameters before it is
   written, and **no vertex moves.** Proved by comparing the rebaked GLB's vertex positions
   against the committed one, not asserted. A moved vertex is a failure and stops the run.
3. The rebake runs on the pinned Blender, one asset at a time, and the manifest restamps honestly.
4. **L179 carries the `Covers:` field it deliberately withheld** — its own text says the day a
   `picket_head` attribute exists, it claims it.
5. The false reason is corrected in T-0094 and in `docs/STATUS.md`, **struck rather than deleted**,
   and named as the integrator's error. The many other "no Blender" statements elsewhere in
   STATUS.md describe earlier runs and are not touched.

---

## Outcome, 2026-08-24: DONE, and the mesh did not move.

**The attribute.** `form.picket_head_m` = **0.312 m**, `reconstructed`, on
`fort_dearborn_palisade.picket_1816`, with its own note and its own confidence chip on the card.
`picket_head_m` joins `palisade_params.CONSUMED`; `PalisadeParams` gains the field and
`picket_point_m` reads it when the record states one and derives
`min(picket_width_m × 1.3, picket_height_m × 0.18)` when it does not. Bounds are stated as a
proportion of the picket, because that is what the head is — it is cut out of the height, so what
decides whether it reads is how much of the post it takes: **4 % to 50 %**, the floor being the
shipped gate's own `MIN_POINT_FRACTION`, so a value the params module accepts can never be one
`tools/measure_picket_plate.py --gate` then refuses. A `picket_head_m` stated on a **worm fence**
is refused outright: that fence has no pickets, so the value would be read by nothing and shown by
the popup anyway.

**The number is derived, not typed.** `0.24 × 1.3 = 0.312` exactly in IEEE-754 double, and the run
asserted `params.picket_point_m == min(width × 1.3, height × 0.18)` before writing anything.

**The proof that nothing moved, in three strengths.**

- **Control first:** rebaking the palisade with NO change to anything reproduced the committed
  master **byte-for-byte** (`b5d9bf86…`), so on this runner the bake is deterministic and a byte
  difference afterwards would have meant something.
- **After the change:** both rebaked masters are byte-for-byte the committed files —
  `fort_dearborn_palisade__picket_1816.glb` `b5d9bf86…` and
  `fort_dearborn_garrison_garden__fence_1816.glb` `dda7c6c9…`. `git status` does not list either.
- **Vertex for vertex anyway:** 3 primitives, **21,728 positions, 0 moved, max displacement
  0.000000 mm**, with NORMAL, TEXCOORD_0, `_CONFIDENCE` and the index buffer identical. The garden
  the same: 7,488 positions, 0 moved.

**What the bake actually cost:** one line each in `assets/manifest.json`.
`fort_dearborn_palisade__picket_1816` `579cb33f…` → `dd0c84b8…`, and
`fort_dearborn_garrison_garden__fence_1816` `5d60352e…` → `1c92409e…`. **The garden restaled and
that is not a bug in this change** — `mesh_inputs` hashes the resolved parameter object, and the
new field is on the class both wall kinds resolve through, so a worm fence that states no head
still hashes `picket_head_m: null` where it previously hashed nothing. It was rebaked rather than
left stale, and its geometry is unchanged. The web derivatives regenerate byte-identically from
the unchanged masters (`66f7fb5b…`, `576a7f0f…`), so `assets/web/` is untouched.

**The correction.** T-0094's clause and the matching passage in `docs/STATUS.md` are **struck in
place, not deleted**, and both now say what happened: the runner had the pinned Blender, the
deferral reason was wrong, and it was the integrator's error rather than the ticket author's
finding. The measured half of that paragraph — that a new `form` key restales the GLB — was
correct and is kept. **L179 gains
`Covers: fort_dearborn_palisade.picket_1816.form.picket_head_m`** and a `Revised:` field; the
"No `Covers:` field, deliberately" paragraph is kept verbatim above it, because it was the right
reading on the day and the entry's own last sentence promised exactly this.

**What a visitor sees that they did not before:** opening the stockade's card, a line reading
**picket head 0.312 m** under a `reconstructed` chip — the sharpened top of every picket in the
fort's wall, graded and claimed, where before it was an expression inside a Python property that
the confidence model could not reach.
