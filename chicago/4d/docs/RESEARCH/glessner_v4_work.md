# Glessner v4 — resumable work record

Owner request, 2026-09-29. Work belongs to **T-1730**, claimed in
`kevinrhaas/chicago-tickets`. Branch: `steward/glessner-v4`; base dev:
`308dcacf1117d78ba62896bbaea4bf067b081b77`. The owner explicitly authorizes
periodic incomplete-work checkpoints so connection or context loss cannot lose
the implementation. A checkpoint is not a release or a passed gate.

## Acceptance

Build a selectable `glessner_house` version `v4` using the default as the starting
reference (the owner's new direction supersedes the old independent-build rule).
Correct the crossing gables, courtyard and garden-level openings, west-wing
south face, continuous northeast copper roofs, and east-wing chimneys. Make the
granite, brick, tile, copper, window/door frames, recesses and cutouts substantially
more realistic. Develop original PBR textures, normal maps and roughness maps.
Review actual renders against the photographs; do not describe a merely passing
validator as photographic quality. Keep the default/v2/v3 available for comparison.

## Evidence already inspected

- Owner's Pasted Graphic 14–18: modern overhead/courtyard/alley views.
- Pasted Graphic 19 and image(4)–image(8): modern street views and stone/entrance
  closeups. These are comparison references, not licensed texture sources.
- Local source library: `chicago/prairie_1904_v1/research/public/` (all six HABS
  sheets, photographs and captions), its README and research-gaps memo.
- HABS sheet 5 supplies actual variable stone-course heights; sheet 6 supplies
  the Prairie elevation. Late changes must be distinguished from 1904 fabric.

## Work parcels and integration

1. Evidence/data: `data/structures/versions/glessner_house/v4.json` and
   `docs/RESEARCH/glessner_house_v4.md`; face-by-face opening schedule, source
   tiers, dimensional reasoning. Geometry corrections must reach resolved params.
2. Geometry: opt-in `detail_profile == glessner_v4` in masonry-house params/build;
   `generators/archetypes/masonry_house_v4_detail.py`; real recessed openings,
   relief and joints, tile/copper detail, bounded original ornament.
3. Materials: `generators/archetypes/masonry_house_v4_materials.py`, original
   maps under `assets/textures/glessner-v4/`, metric UV0 export and license entry.
4. Integration: conditional input hashes for v4-only dependencies, bake all
   Glessner variants affected by the builder hook, web derivatives, sidecars,
   source/liberty/license accounting, changelog, full gate and published smoke.
5. Visual QA: `tools/render_structure_review.py`, actual GLB import and fixed
   Cycles cameras for street elevations, courtyard faces and overhead. Compare
   default/v4 at the same settings, then check desktop/mobile in the web renderer.

## Checkpoint 1

Remote branch exists. References and default GLB inspected. The default has nine
flat materials and no textures. Default daylight renders confirm flat window
panels, untextured roof and absent coursing. Evidence, geometry, materials and
render-review work are running in separate worktrees.

Only the v4 dependency-hash extension is integrated at this checkpoint. It imports
and resolves the existing default successfully. The v4 record, detailed builder,
textures and new baked assets are **not integrated yet**. No project-wide gate or
candidate quality claim is made at this checkpoint.

Resume by reading this page and the latest ticket, inspecting the branch diff,
then completing the parcels above. Never promote this work to main before the
finished version has been reviewed and the owner requests production promotion.

## Checkpoint 2 — implementation and original maps

The detailed builder, opt-in dispatch, v4 record, evidence dossier, source record,
materials and fixed-camera render tool are integrated. Original texture sources
and 21 maps are included (about 12.2 MB); the recipe reproduces them. The material
export probe under pinned Blender 4.5.3 confirms all maps use metric TEXCOORD_0,
which survives the existing unwrap and web batching. L305 records reconstructed
detail; the license inventory covers all texture files. Python compilation passes.

Eleven default reference renders and four first-candidate renders have been
reviewed. The candidate has visible stone/brick courses, roof tiles and recessed
sash, but **does not yet meet the owner's photographic-quality goal**. The first
raw GLB was 165 MB and is deliberately not committed. Invisible geometry is being
reduced. Remaining visual corrections include blank stair-tower openings, proper
bow windows/terrace, the open tunnel, chimney face winding/coursing, window-surround
proportions, and roof junctions. The newest three courtyard photographs are
accounted for in the data, but their geometry is still being integrated.

No candidate GLBs, web derivatives, sidecars or final gate claim accompany this
checkpoint. The shared masonry builder hook makes the previous Glessner outputs
stale until all four variants are rebuilt. Next: finish the detailed builder,
`blender -b --factory-startup --python generators/build.py -- --only glessner_house`,
derive the four matching web files, compile the scene, compare all cameras, then
run preflight and desktop/mobile published smoke. Use the pinned binary specified
by `generators/blender.pin`; no shared emit.py changes are needed for the UVs.

## Checkpoint 3 — detailed candidate, still under visual review

The geometry now has real openings and reveals, original textured masonry,
individual roof tiles and seams, corrected tower glazing and dining clerestory,
three alternating garden windows under the dining bay, the curved terrace
parapet with nine reconstructed risers, and the open courtyard passage. There
are nine original PBR fabrics, 27 source maps, and 25 material slots including
transmissive glass. The evidence dossier distinguishes historical HABS details
from present-day replacements. All 14 owner photographs have been inspected.

The candidate has been baked with pinned Blender 4.5.3 and reviewed from every
face. A v4-only export modifier removes an unused second UV set; a direct
comparison proved all 100 retained accessor arrays, indices, embedded images,
materials and scene metadata identical. The resulting master is 50,046,188
bytes. This checkpoint preserves source and maps; final baked assets follow
after the remaining service-door landing correction.

Isolated version tests pass 35 checks. Initial desktop/mobile web review loads
the selected version with zero page/HTTP errors, 37–42 draw calls and roughly
750–776k rendered triangles including shadow passes, within the existing budget.
This used software rendering and is not a device frame-rate measurement.
The full version test identified stale v2/v3 derivative provenance after their
rebuild; regenerate all four Glessner derivatives. Full smoke is still running;
1835 frontage census assertions have failed outside the changed model and their
baseline status is under investigation. Full preflight has not passed.

Remaining work: resolve the raised north-court service-door landing, finish the
photographic-quality review (current broad views still read as CG), bake/derive
the final assets, rerun selected-model browser QA, complete the full preflight
and both published smoke viewports, and record the exact results. T-1730 remains
open for owner comparison. Do not promote v4 or production merely on a checkpoint.
