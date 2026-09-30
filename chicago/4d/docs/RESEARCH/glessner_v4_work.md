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


Final candidate refinements after checkpoint 3: HABS north service landing and
ten steps; deeper bounded split-face granite using existing vertices; subtle
mineral variation; restrained brick and copper contrast; pale varied linen
shades and muted green frames. Original maps now total 12,691,945 bytes across
27 maps. An isolated material export verifies 25 materials and UV0 bindings;
the renderer confirms imported glass transmission 0.94 / IOR1.52 / roughness0.065.
The optional overcast review lighting is mathematically defined and recorded,
not a photographic backdrop. Final all-variant bake is running.


## Checkpoint 4 — exact baked-asset recovery

Pinned Blender rebuilt all four Glessner variants. Final v4 master:
49,288,948 bytes, 422,723 triangles, SHA256
`9a4f768973e409bdeb555a19d9f365ad4df190c794039e4769e7828262ad48f5`.
The web derivative is 21,493,940 bytes. All four derivatives were regenerated,
then scenes compiled and the published mirror rebuilt.

The GitHub connector rejects bodies exceeding 16 MiB, including base64 overhead;
there is no authenticated native git push configured in this workspace. Direct
upload of both large GLBs therefore failed. The source/maps and **exact baked
assets** are preserved by `docs/RESEARCH/glessner-v4-recovery/`: seven archive
parts, per-part and per-member SHA256 values, and a verifier/restorer at
`tools/recover_glessner_v4.py`. Verification reports all 13 members byte-identical
to the working assets. This is a transport recovery measure, not a new asset
format. Restore the archive before continuing validation in a fresh checkout.
Checkpoint 5 supersedes this transport limitation: the normal publish/check path now
materializes only the two exact ignored v4 GLBs from the committed package. The
canonical derivative producer refreshes that package after a deliberate rebuild.
No authenticated native push or renderer format change is required.

Final source validation: parameter/license validation passed with 0 errors and
259 inherited warnings; isolated version regressions passed with 0 failures.
Preflight and mobile published smoke are still running. Desktop completed parts1–4,
then was stopped at the start of part5 to relieve memory pressure; resume parts5–13
after mobile finishes. Both smoke
viewports have the same three inherited frontage-count failures already owned
by T-1752: 51 walks / 46 crossings / 58 authored meshes / 40 block faces against
older asserted counts. Data, frontage renderer and assertions match pre-v4
commit `590ad4c3`, and published files match source. No assertion was weakened.

Final 1600-pixel actual-GLB overcast renders are running serially. The preceding
review drove additional material, stone-relief and shade corrections; no final
photographic-quality acceptance claim is made at this checkpoint.


## Checkpoint 5 — close-up correction and durable build lifecycle

The 1600-pixel entry review rejected the earlier repeated star carving, crumpled
stone normal and closed uniform blinds. New geometry now has four foliate scrolls,
nested arch mouldings, three distinct central capitals and an egg-and-dart sill.
The first subsequent 800-pixel render exposed false diagonal joints caused by
chamfering the convex fragments of an arch subtraction as though each were a
physical stone. The fix constructs each stone once and clips only its completed
surfaces, preserving depth, material and true perimeter. A regression samples
805 exterior points and 616 aperture points each on brick and granite.

Original generated granite and turf albedos supplement the numeric PBR library;
the exact prompts and unchanged bitmaps are preserved beside the recipes.
Granite crystal scale, normal strength, common-brick body colour and oak midtones
are being judged against the actual GLB renders, not merely the source maps.
An optional documented CC0 sky-only HDRI supplies real cloud radiance in review
lighting without adding buildings or historical scene evidence.

Packaging is now part of the canonical v4 derivative producer, followed by the
ordinary provenance/asset gates. Fresh checkouts restore only the two missing
outputs. Stale existing output is refused, never overwritten with an earlier
model. Focused tests cover both optimized and passthrough producers, fresh
restoration, custom output directories, unrelated versions and failed producers.
Promotion of v4 to default must explicitly retire or retarget this alternate-only
package; that future operation is outside the present v4 comparison.

The full mobile published smoke completed 569 passes and the same three
T-1752 frontage-census failures, with zero page errors. Its full log is in
`glessner-v4-qa/mobile-checkpoint4.log`; its standing-record tree hash is deliberately
unavailable because later model changes were made before the result was filed.
Desktop parts 5–13 continue after the earlier interrupted full run completed
parts 1–4. The first preflight's four failures were resolved (public citation
contained a private research path; local tickets directory was a symlink). Their
focused checks now pass. The final full preflight and newest-model browser/visual
reviews still remain. No photographic-quality acceptance is asserted here.


Checkpoint 5 baked candidate: pinned Blender emitted **580,172 triangles**,
28 materials, and 20,000 lawn blades. The automatic canonical derivative hook
refreshed the exact two-file package successfully. Current bytes/hashes:

- `assets/gltf/versions/glessner_house/v4/glessner_house__as_built_1887.glb`: 70,375,492 bytes; SHA256 `e72fad0af84e141179b9969c4af3bb63d030f986afffe522238caba990fc99a1`.
- `assets/web/versions/glessner_house/v4/glessner_house__as_built_1887.glb`: 32,115,656 bytes; SHA256 `0b7ec129659d83a385fd5eb7d925e09f836e7f1f10279179b6fa89f69399b5d0`.

The full preflight is running against this candidate. Neutral entry/access
and sky-lit courtyard renders remain under visual review.


The new neutral 800-pixel entry confirms the false diagonal joints are gone.
The granite is finer and cooler, with coherent carving and window reveals. The
service view confirms warmer timber, corrected brick tones and finer lawn detail.
These actual-model renders and their hashes/settings are preserved under
`images/glessner-v4/refined-02-neutral/`. Rock-face relief still reads too shallow
in the frontal neutral view; a controlled material study is under way before
photographic acceptance. Dev was rechecked via native remote and exact GitHub
branch endpoint and remains `308dcacf`; there is no integration drift.


Checkpoint 5 is remote commit `ba854300291e5d30638c7cabd8e1c2bd27feed3a`.
Desktop continuation completed **311 passed, 0 failed**, stages5–13. The full
preflight completed 708 passing steps and four integration failures: new tests
need the gate's self-test classification, the package checker needs written
writer classification, and the new steps need measured isolation rows. These
are being corrected; the earlier source-use/ticket-layout failures are gone.

A decoded web-geometry audit found 14-bit quantization collapsed 6,146 of20,000
blades and 35,176 additional tiny ornament/limestone triangles. An exact-v4
16-bit trial preserves every blade, cuts maximum measured position error from
3.31 to0.65mm, and reduces (but does not eliminate) submillimeter ornament
collapse. Default/v2/v3 controls remain byte-identical. Measured residuals are
retained, not described as lossless. The normal producer will apply16bits to
the next v4 derivative and refresh its archive.

The next master refines broad split-face stone relief, roller shades and the
bow door. The door's former full-height oak backing made its glass opaque;
HABS photo5 supports four upper panes above a lower raised wood panel. Later
protective grille details are not carried back from the modern photograph.


Refined03 candidate: pinned Blender emitted approximately669,811 triangles,
28 materials, and20,000 lawn blades. The v4 derivative uses16-bit positions,
with the existing default/v2/v3 web products re-derived byte-identically.
Master:78,455,116bytes, SHA256
`52f214b2d5dc145077bf79eb3783aa5ec9e608163da0b7038f158cf63da87f14`.
Web:34,021,988bytes, SHA256
`343971c33615fc2ca015acdb7e6027f19e9630e2a693f47eeaad7c77cff9cd8b`.
The exact package now has11parts.

The current neutral and directional entry views confirm the false arch seams
remain absent and the larger stone relief survives export. They also reveal
broad triangular wedges in place of the reference's finer chipped rock faces.
Further bounded multiscale relief is in development. HABS photo5 confirms
raised roof-ridge crests missing from the cap-tile geometry; these and the
courtyard dormer projections are being reviewed before a final bake. These
images are candid work-in-progress evidence, not photographic acceptance.

T-1752's isolated frontage-census repair was completed in local commit
`0ff8eb2af5f9a9d6b442096337405da53045d227` and integrated here. Seven
independently derived constants replace stale counts; every assertion
operator, condition and floor remains. Its isolated gate passed708steps,
and published mobile parts1–2 passed158/0 with zero page errors. Final
integrated browser coverage remains due. The current full preflight also
checks the repaired new-tool classifications and isolation measurements.

Checkpoint6 is remote commit`1ac8d5439638bfa446c37404e0a250d8c9bc57eb`.
Source, two exact GLBs and candid rendered evidence are recoverable there.
Further stone/roof refinement continues; no final quality acceptance.

Refined03 full preflight completed PASS: check.sh, changelog and ticket-ID
checks are all green. This clears the four prior new-tool integration failures.
Final geometry refinements still require their own fresh bake and gate.

Draft PR201 tracks the recoverable implementation and the unfinished visual
acceptance: https://github.com/kevinrhaas/chicago/pull/201 . T-1752 is in review
against that PR; T-1730 remains claimed for this version and stays open for
the owner comparison after integration.


Refined04 master: 124,135,404 bytes, approximately 1,070,689 triangles,
SHA256 `5992aed6d90d6c5787ac18568f58a6e65a6952a204bfc160e9b4ead6aba73cdc`.
Dense split-face stone with selective within-stone normals, rough arch wedges,
flared dormer caps and timber lights, ridge crests and courtyard gutters are
now baked. Neutral and directional actual-model renders confirm more natural
stone relief. This remains an intermediate review; glazing convergence and
courtyard material variation are being examined before photographic acceptance.

The corrected light-mode browser baseline reads the actual
`chicago4d.settings.detail` preference and uses touch emulation. Refined03
submitted 2,164,635 triangles against the unchanged 825,000 light allowance;
the earlier harness used an unused preference key and its apparent light
reading was actually full. Both receipts are retained with that distinction.
The viewer currently uses the same GLB at all tiers. A source-derived reduced
v4 mesh and transactional tier switching are therefore necessary. Neither
default nor an older comparison version can substitute for this reduced v4.

A noncanonical derivative price of refined04 (47,037,292 bytes; SHA256
`a88652ca070ccd9db70c529d24b6579040823c4bf960ce5899bb6cbbef4d9e25`)
measured five desktop stands with explicit actual rendering frames. Maximum
was 3,430,985 rendered triangles and 105 calls at 18th Street; Prairie,
courtyard, stable and aerial were also measured. Zero browser or HTTP errors.
This price uses the ordinary producer with `--out` and explicitly overrides
only that GLB when serving the prior published tree; it is not final published
acceptance. The proposed full-only selected-v4 allowance is 3,800,000 triangles
(10.8% above that observed maximum), retaining 215 calls and every ordinary
town/light/balanced ceiling. Final canonical assets and both viewport readings
remain required. Checkpoint6 CI passed on GitHub.


Refined05 combined candidate (2026-09-30 UTC): dense multiscale stone,
correct analytic curved-stone normals, sealed 4 mm glass, a genuine Prairie
upper-door-light cutout, stable-turret timber louvres, flared dormers, ridge
crests and courtyard rainwater goods are baked together. The courtyard uses
coherent clay variants, sandy mortar and the documented 4 m lawn texture.
The new turf input's exact prompt and hash are in its provenance JSON.

Full master: 125,170,732 bytes, 1,071,475 triangles, SHA256
`73724f18a4afefe2f71ec7a608fe5f6f18df3d7ac74bd2dd6caaadd89e0ecec4`.
Full web: 47,924,540 bytes, SHA256
`f05f30274ca34e0a83c21495b23cca1a649dda241cfc052651bff0baf22bdf76`.
Light web: 25,156,180 bytes, 193,233 triangles, SHA256
`69f36870cda016d11474780c5fcb33a9a27a0340e37c1538c735b751e16b199a`.
The exact three-file recovery package has 20 parts.

The source-derived reduced mesh preserves all 172 openings. Independent
float32 position/confidence fingerprints match full geometry exactly for
glass, painted sash, wood, iron, linen, copper, backing and ground surfaces.
Another 108 cases confirm the reduced masonry keeps full geometry's random
sequence and material choices. These proofs cover architectural preservation;
they do not claim photographic appearance or a passing published frame budget.

The 1440 px actual-model entry render shows substantially better stone and
clearer glass, but still exposes flat gray glazing/interiors and simplified
carving. These remain active visual work. Refined05 published detail-switch
checks and fresh integrated gates are in progress; no final acceptance yet.
