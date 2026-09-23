---
id: T-0126
title: The openings-and-glazing half of the material sheet: one dark, one timber
state: done
epic: RENDERING
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-24
pr: 372
claimed_by: run 8/24/2026, 9:54:30 AM CT
blocked_on: null
needs_bake: true
---

The wall-and-roof half of `docs/RESEARCH/materials.md` landed as **T-0007**; this is the
family it deliberately left, split out rather than half-wired.

**Two things, both already recorded on the sheet:**

1. **§2.3 — four values for one idea.** `dark` ships at 0.35 in `frame_dwelling`, 0.40 in
   `log_dwelling`, `fort_structure` and `palisade`, `interior` at 0.60 in `outbuilding` and
   `placeholder_opening_dark` at 0.70 — three colours and four roughnesses across four
   generators, all meaning "what you see through an opening". Converge them onto one sheet
   row, the way T-0007 converged three whitewashes and two reds. `glass` (0.25, 45 slots)
   belongs to the same family and is already consistent; bring it onto the sheet with them.
2. **§4 finding 3 — `timber` is ONE NAME over TWO materials 3.2x apart in linear red.**
   `outbuilding.py`'s 0.208/0.172/0.128 and `frame_storefront.py`'s 0.66/0.56/0.40 are both
   defensible and are not the same thing. Only the outbuilding's ships, because no record in
   the dataset turns `framing_exposed` on — so this is latent, and it surfaces the first time
   a storefront exposes its framing beside a shed. Give them two names.

**Read before starting:** `generators/common/materials.py` (the sheet as code — add rows
there, do not re-declare a colour in an archetype), materials.md §2.3 and §4, and
`docs/LIBERTIES.md` L155.

**Watch the material COUNT, not just the values.** ROADMAP K36(a): `gltf-transform`'s palette
pass folds an asset with FIVE or more materials and leaves four alone, and 275 of the 334
assets sit at four. Renaming a slot is free; adding one tips the whole town at once. T-0007
shipped a material-count delta of zero and a triangle delta of zero, and this should too.

**NEEDS A BAKE** — it changes material assignment on committed geometry, so it stales every
archetype asset that carries an opening. T-0007's note: do not loop `tools/bake.sh --only`;
call Blender per structure and run the tail steps once.

**Acceptance:** every `dark` / `interior` / opening surface in the shipped GLBs resolves to
ONE sheet row; `timber` names two distinct materials; material-count delta 0; triangle delta
0; `tools/check.sh` green.
