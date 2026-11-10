# Joseph portable cloth source study — 2026-11-10

Artifact-only authoring measurement, based on DEV `2c9df872237b9dc2e6c95564eb6a4e125b80f185`. No model/asset adoption, placement, workflow change or production promotion. Otis/Martin and their adopted clips/assets are preserved.

The recovered original cloth study supplies deterministic packed 128-square linen/wool color, ORM and OpenGL tangent-normal maps. The new flag defaults off and accepts only Joseph Dufresne (`dufresne_joseph_1835`). A separate measurement-only recipe commit enables `authoring_studies.woven_cloth_near_v1` only on his existing proof variant, so the existing native worker loop can exercise the study without a workflow edit. That configuration must not be treated as runtime adoption or silently merged as the default recipe.

Only LOD0/1 cloned garment materials receive maps and material extras. A Blender Text datablock retains the source report; root/scene export metadata is unchanged to protect far bytes. Standard image/Mapping/Separate Color/Normal Map nodes are intended to preserve portable glTF bindings. Actual packed images, color/factors, KHR_texture_transform parity across LOD0/1, extras through WEB/publishing and unchanged geometry/rig/weights/UV/clips need native readback. Near material names add `__woven_near`; existing contract/inspectors accept that slot suffix. `source_material` is provenance, not an existing runtime lookup. Optional dress colors use exact material names, so any later Joseph recolor needs explicit HumanActor review.

The runtime common fabric patch skips marked portable normal+roughness materials, avoiding double weave/relief. Ordinary/far cloth retains its existing shader. This also omits that shader's wear/rumple/sheen on the portable study and requires matched actual HumanActor views.

Original generated pixels are CC0-1.0; authoring/runtime tools remain GPL-3.0-or-later. No third-party, captured or historically measured textile is sampled. Existing worker sources, L418, L-human-modular-workwear-1789 and assets/LICENSES.md remain bounded reconstruction/license provenance, not photographic acceptance. The 32 mm repeat, thread periods and micrometre height coefficients are authoring choices. Average UV calibration does not resolve inherited 0.16–16.42 UV/metre chart stretch.

Conservative RGBA8/full-mip arithmetic: at most ten 128-square images per near GLB, 873,800 bytes each; net 1,048,552 bytes for both near LODs versus the replaced 256-square shirt image, without cross-GLB sharing. Far/Otis/Martin increment zero. Actual encoded bytes, decoder/transient/GPU storage and the original phone memory ceiling remain unmeasured.

Pre-overlay source controls: seven Python tests, real Three/three existing GLB fabric controls, two measured isolation rows and audit passed under original SUP120 in 2.129 seconds, resources accepted/cleanup0; all 973 foreign isolation rows preserved. This default-off verdict is not a claim that the same default assertion passed on the opted-in recipe. A separate actual-config matrix binds the measurement commit.

Current Joseph source LOD0 walk observation found 988 inside witnesses among 2,336 selected closest BODY witnesses across 73 keys/midpoints. Selected maxima: trousers 1.452 mm, shirt 0.241 mm, waistcoat 0.684 mm, jacket 0.020 mm; these are not deepest/global/continuous-fit bounds. Textile maps change no geometry and do not fix/reclassify them. Fit, full wardrobe motion, world interaction, native rendering and photographic acceptance remain open.

Native qualification must require these exact far MASTER/WEB SHA256 values from successful producer 42774580234/source8745, bound by its selective per-file receipt. The older reused parent run stays cancelled; whole ZIP verification was not claimed. No expected-hash retargeting:

- `dufresne_joseph_1835.lod2.glb`: `eefe9c3be331feccb07df68171e6fba8f3bd58adae93625b9ead431e2a83e8b4`
- `dufresne_joseph_1835.lod3.glb`: `e72758e3a8e3fb43bc6f7e9fd0085575d2592a0fe7be8104a32e6a5be2f91e26`
- `web/dufresne_joseph_1835.lod2.glb`: `510241fda94c9b762e3ae42e1ae725c5f2d7cffe4a84feb35afd39e8956d4f68`
- `web/dufresne_joseph_1835.lod3.glb`: `fadb5b3cc3ec37eb095eb5957bfdd8c1e6f007a9390e8baa39d192a5f58e6146`

After ROOT's final review only: existing `chicago-4d-humans.yml` on this dedicated measurement branch, `build_teamsters=true`; seated/dress/render flags false, `source_ref=''`, `library_source_run=''`. No dispatch is performed by preparing this branch. Any later library-still or native HumanActor/world qualification requires its own reviewed source-bound execution. No budget/sample/quality bar is changed.

## Missing-tangent failure and scoped correction

Official native run42815699269 at source834fcbcee9de46de3270e28c786ed5fae57ae6c6 failed the unchanged hierarchy warning guard: Joseph rootLOD0 had four MESH_PRIMITIVE_GENERATED_TANGENT_SPACE warnings, and the parented control had those same four beyond its eleven expected hierarchy warnings. The24 container validations had zero errors; the browser measurement step was skipped. This run remains NONPASS. No private job log is included here.

The shared exporter now requests actual tangent export only when selected Joseph LOD0/1 materials carry the explicit portable marker and a linked tangent-space Normal Map image. Root and parented controls already use the same human_export.py; parenting/rigid-frame policy does not determine this flag. Other identities, unmarked materials and far LODs retain export_tangents=False. No validator warning whitelist, threshold or assertion changes are made. Native emission of the expected TANGENT accessors and exact far four-file hashes must be confirmed by a new reviewed native run; cheap source controls do not establish that result. Near tangent vertex storage is additional to the earlier texture-only arithmetic and still needs actual measurement.
