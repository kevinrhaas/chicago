# Charles's existing coat: canonical near-material candidate

Only the already drawn 1904 actor
`hi_pa1904_glessner_john_j_c1900_charles_nelson_1904` changes. The coat keeps
`garment_outer__livery_coat_green_1904`, original effective linear green
`[.014,.026,.019]`, roughness `.86` and metalness zero. Three original 128-square
color/ORM/tangent-normal maps are a reconstructed textile liberty, not captured
historical cloth. Existing appearance overrides, macro rumple/wear/sheen, identity,
rig, idle/walk, other materials and four whole-file FAR baselines remain binding.

## Actual output and limits

The immutable recipe pins eight actual current GLB parents at
`fc5a52b6cab3eed78e2db5864aa811dff5df2795`, not a retained Blender master. Its
SHA256 is `2b604e409564a0340c497bd158307a22620aad3efaa542aecff55a2e0d8dc4d3`.
The separate admission records the four reviewed output hashes and actual
implementation/runtime hashes. Full integrated reproduction took 40.138 seconds
under the original resource limits and reproduced all four previously qualified
children byte-exact. Exactly those four files are staged in this candidate.

| File under `assets/humans/` | SHA256 | Bytes |
| --- | --- | ---: |
| `nelson_charles_1904_coachman.lod0.glb` | `ebb5594ce5aadf36da25f87676252e8026c3cd993760b2cbd9f1c6d3fb9351af` | 9093740 |
| `nelson_charles_1904_coachman.lod1.glb` | `f87895b5004268335f91a5d4b821b19beaf4ae917c90c7cde9410ddff5825aea` | 7980556 |
| `web/nelson_charles_1904_coachman.lod0.glb` | `8660b20793909061ecc0c81b31c4b6e4fd26c2da0afa04c7b741788495c28820` | 4670520 |
| `web/nelson_charles_1904_coachman.lod1.glb` | `86a5fdfa5d173c89a94e925424975f3f83ada548d2c5953106ac7c9b496cf4b6` | 1714028 |

Actual raw MASTER verification protects the complete original BIN prefix, all
expanded triangle PN/UV/JOINTS/WEIGHTS/morph corner bytes, nodes, rig, clips and
noncoat JSON/material/image data. Official MikkTSpace requires only 7 LOD0 skirt,
19 LOD1 body and 1 LOD1 skirt duplicate vertices. Existing rows remain; no triangle,
winding, UV repaint or averaged tangent is introduced. Independent canonical WEB
checks use actual source-triangle correspondence and exact decoded semantics,
including TRIANGLES mode, morph names/order/defaults and material sampling.
The baseline WEB body degeneracies remain 5/0 position and 70/25 UV faces at
LOD0/1. No new tolerance or precision is introduced. All four official glTF
Validator 2.0.0-dev.3.10 results had zero errors and zero warnings.

The actual repository canonical pipeline is glTF-Transform 4.5.0, image caps
2048/1024, opaque color JPEG92, meshopt scene quantization/medium/normal16.
MikkTSpace 1.1.1 is used with the official transform's handedness convention.
Color uses explicit IEC sRGB encoding; normal/ORM are linear data. Actual SOURCE
means lie inside the intended linear palette's eight-bit quantizer intervals.
The aggregate metric repeat is 35.4148087722316 across both LODs; differing body
and skirt UV densities yield area-based periods 57.5427/24.0058 mm. Uniform
physical thread size and UV fit are not claimed.

Raw WEB growth is 78116 bytes across both near files. Three RGBA8 maps with full
mips cost 262140 bytes per LOD, or 524280 if both are separately resident. The
selected-published research measured Full deltas of 262140 texture bytes and
56584 buffer bytes, retained all six originals and real recolor/lifetime controls,
and showed a subtle, still stylized change. That research remains STRICT NONPASS:
seven native completed-transfer cancellation findings were retained. It is not
full published release, phone memory, clothing fit or photographic acceptance.
The original MASTER03, WEB01 and defaults05 NONPASS receipts are retained.

## Canonical regeneration and refusal policy

`human_export.sh --master` stages all eight fresh Charles canonical files before
any active write. Only this exact identity enters the material terminal; ordinary
residents, fixture export and all other paths retain their existing behavior.
The terminal compares the fresh parents against the immutable parents before
reproduction. Only `/scenes/0/extras/chicago4d_human/master`, an actual absolute
build-path string with no runtime consumer, may differ. All other JSON and the
entire BIN remain exact. Source IDs/hashes/versions/licenses/body/style/units,
rig-valid booleans, unknown proof fields and all animation data are protected.
An incompatible fresh body, unknown active asset, partial family or changed FAR
fails before active writes. After full compatibility proof, the recorded
canonical parents remove only that ephemeral-path variability. A transactional
four-file install rolls back on an IO failure. It never restores an old parent
unconditionally over a changed body. Receipts bind fresh hashes and canonical
ref/Git blob/full SHA identities.

Explicit full reproduction, using a separately installed pinned dependency root,
creates only external outputs and verifies all four admitted hashes:

```sh
python3 tools/human_charles_coat.py --reproduce "$FRESH_OUTPUT" \
  --dependencies "$PINNED_NODE_MODULES" --parent-root "$VERIFIED_PARENT_CACHE"
```

The cheap derived owner writes only
`data/humans/materials/charles-coat-woven-v1.derivation.json`; assets and the
recipe/admission remain inputs. Its registered check independently raw-verifies
both MASTER children and checks all eight installed file hashes. It does not
pretend that this replaces native render, animation, fit, mobile or complete APP
gates. Actual writer and isolation measurements passed under the original
supervisor/resource limits: two writes reproduced the receipt, a deliberately
corrupt receipt failed the check and was repaired by the writer, and all five
declared gate tools wrote nothing in the live tree. The 19-file fixture used its
own clean Git index and no HEAD commit; it did not touch the application index.
See `docs/measurements/charles-coat-writer-2026-11-10.json`. The actual four-row native fixture update passed in 84.441 seconds at both
1280x800 and 390x780 with the original 30 timing frames. All 248 actual asset
hashes matched before/after; the 244 unselected rows and original full-corpus
date stayed exact. The global 248-file fixture check also passed. See
`docs/measurements/charles-coat-native-2026-11-10.json`.

## Fresh CI and offline bootstrap

The check/bake checkout has full history (`fetch-depth: 0`) but `filter: blob:none`;
full references do not imply the two historical MASTER blobs are cached. The
registered Node wrapper serializes acquisition of exactly those two recipe/tree
bound objects before the independent Python check and its real-parent controls.
Cached reads disable lazy fetching. Missing blobs require the explicit
`--acquire-reviewed-parents` option, the exact declared GitHub Chicago origin,
its `promisor=true` and `partialclonefilter=blob:none`, and no other promisor.
Each request has a 20-second timeout, a 16 MiB ceiling and exact size, Git blob
SHA1 and full SHA256 verification. There is no URL, identity or revision fallback,
and acquisition writes only Git's object cache. An absent immutable tree fails
before any acquisition or active write.

```sh
node tools/check_human_charles_coat.mjs --acquire-reviewed-parents -- \
  python3 tools/human_charles_coat.py --check --then \
  python3 tools/test_human_charles_coat_regeneration.py
```

The separate `tools/test_human_charles_coat_inputs.mjs --acquisition` control
uses a fresh real shallow/blobless Chicago repository, no checkout or alternates,
proves both blobs absent, acquires the two through this same helper, checks cached
offline reuse and corruption refusal. It is a separately admitted diagnostic,
not a repeated network control in the gate. The ordinary `--check` mode is offline.
The actual fresh blobless acquisition, offline reuse and corruption refusal
passed 13 controls. The complete focused cell closed in 17.901 seconds with
accepted original resource snapshots and complete descendant cleanup. Its first
4.735-second attempt remains NONPASS: Git preferred a valid packed blob over a
corrupt loose shadow. The corrected disposable fixture removes only packs added
by its two acquisitions, preserves the tree metadata, proves the object absent,
and proves Git actually returns the bad bytes before requiring refusal. The
production wrapper, recipe, producer and admitted output hashes did not change.

A canonical authoring/export run needs all eight original parents and the exact
fc5 tree. The human measurement workflow's default shallow checkout may lack that
tree, so an operator must first fetch the declared revision explicitly from the
trusted origin, then acquire the eight exact recipe blob IDs into Git's cache or
provide a verified cache at `--parent-root`. Even an explicit cache does not waive
immutable tree membership. The owner validates every full hash/size before any
output and never lazy-fetches on its own. This proposal does not edit workflows
or silently fetch arbitrary history during a body rebuild. A missing tree/cache
is an actionable refusal, not permission to overwrite current geometry.

## Runtime, provenance and remaining gates

Portable weave disables only the redundant common fine weave for this exact
marked, normal-mapped coat. Common dye heather is zero only while its base-color
map remains. Real exact-name recoloring clears only that map, retains normal/ORM,
restores dye heather and preserves shared texture ownership. Macro wear, rumple
and sheen stay. Skin/hair/eyes and every other resident are unchanged.

Source tools are GPL-3.0-or-later. Authored textile pixels and the existing Charles
family remain CC0-1.0; the official glTF-Transform/Mikk dependencies are MIT.
No historical source, paid map or retained Blender provenance is invented.
Complete four-part APP gate and ordinary DEV review,
current-world/mobile budgets and photographic/fit
acceptance remain pending. No APP commit, PR or adoption is claimed here.
