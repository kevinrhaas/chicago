# T1789 reusable human library: source checkpoint

This is a source/data checkpoint on DEV cb93ad9cd5ea38654737e05002b1f1904be14e54, not a new canonical export, a photographic person or a completed T1789. Existing shipped GLBs and measurements retain their old source identities. New masters and their actual source/published images must be generated and inspected before those assets can change.

## Implemented source

`tools/human_period_wardrobe.py` assembles reusable original garments on unchanged cleared body, hair and c4d_humanoid_v1 inputs. Existing reconstructed Otis Bardwell selects a waistcoat/five-button/broad-hat assembly; Joseph Dufresne selects a six-button waistcoat and separate open short jacket; Martin Flynn selects a four-button waistcoat, shorter jacket/lapels and lower-crown/narrower-brim hat. These are deliberately different garment silhouettes, not individually researched likenesses or proof of the full three-person acceptance.

The existing connected-shoulder waistcoat pattern is explicitly reused on the adult35 source. Actual source testing found that clamping vertically displaced interior points onto its hem creates opposite-facing coplanar fans. The modular path instead tapers vertical ease continuously toward the fixed cut planes; it neither deletes the source triangles nor modifies body anatomy. The legacy construction remains available as a meaningful failing control.

Physical garment returns retain every input outer vertex, face, corner UV and weight. Their own per-corner UVs take a bounded barycentric step into the actual adjacent source UV triangle, intentionally reusing cloth texels without an unused-atlas claim. This repeats a material, so it is not an exclusive atlas for future uniquely painted or baked AO details. Buttons sample actual waistcoat triangles rather than guessing torso depth. Jackets carry connected folded front edges with real UV surfaces. Hats are closed hollow constructions around the actual unchanged hair, weighted only to the existing head bone. New caps, side surfaces and seams have nonzero per-corner UV area.

All dimensions, cut combinations, colors, button counts, hat profiles and material roughness are original reconstructions. Existing Mount1835 paintings are qualitative period-category analogies only; no source pixels, traced pattern, historical measurement, pre-July1 completion or named resident possession is claimed. The newspaper and cleared component rights remain those in the existing recipe/source records.

## Validation boundary

The normal workwear source test now exercises all three real assemblies, adult25/35 source preservation, all four hat/button LODs, complete shirt/collar/waistcoat/trouser/jacket UV surfaces, closed hat/button manifolds, portable weights, original outer UV/face preservation, and negatives for the old adult35 hem, bad thickness, degenerate UV input and a detached button run. These controls are CPU source geometry only. They do not prove Blender modifiers, export normals, continuous posed garment clearance, browser framing, period tailoring or photographic quality. No old canonical or technical PASS transfers to this candidate.

## Full T1789 acceptance remains in this same ticket

- The first bounded modular set must cover appropriate body/head bases, hair/facial hair and the stated garment families as evidence supports: shirt, waistcoat, trousers, work/outer coat, dress/skirt/bodice, apron/shawl, hats/bonnets. This checkpoint provides a source implementation for a male workwear subset; feminine garment families, further base/head/hair options, accessory interchange and any longer coat remain unfinished. Do not close the library from three male clothing/color/hat variants.
- Preserve existing residents and the distinction between identity and reconstructed appearance. Additional eligible residents and any additional cleared anatomical base require normal dated identity/source checks; no anonymous replacement or invented portrait is implied by the source kit.
- Canonically build the new .blend masters and export all three deliberately distinct test residents through the existing portable pipeline. Recheck the unchanged raw-normal0.001, UV/seam, skin/hierarchy, morph, sole, Khronos, metre/axes/scale and source/web contracts on the new outputs.
- Inspect actual complete garment layers at rest, idle, walk, independent head/jaw and the seated study; retain genuine crossings, fit defects and biomechanical limitations. Buttons must remain seated under actual skinning. Hat/brim must remain inside actual inspection framing rather than hiding outside old skin/hair bounds.
- Inspect fixed-camera, honestly lit near/profile/quarter/detail images and the actual published models at desktop/mobile, including near/mid/far transitions. Record bytes, triangles, materials/draws, textures/memory and frame cost without relaxing budgets. Technical or CPU geometry passes are not photographic acceptance.
- Demonstrate the complete library can assemble/refine Mark Beaubien using the shared source rather than an unrelated rig. Mark actor/scene work and horse/rider/driver/gear/gait acceptance do not follow from this checkpoint.

Future work continues under T1789; this plan creates no new photo follow-up tickets.
