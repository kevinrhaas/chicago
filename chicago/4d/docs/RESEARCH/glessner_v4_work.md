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
