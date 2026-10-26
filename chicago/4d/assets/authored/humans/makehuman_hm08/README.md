# MakeHuman hm08 source and engineering preparation

Pinned CC0 graphical data from the official MakeHuman repository; see `SOURCE.json` for original URLs, exact SHA256 hashes, byte sizes and commit. Upstream files are preserved verbatim. The copied license texts explain the distinction between CC0 graphical assets/output and AGPL program logic. No MakeHuman program code has been copied.

Generate the engine-neutral authoring input with:

```
python tools/human_base_prepare.py --height-m 1.75
python tools/test_human_base_prepare.py
```

`prepared.json` is a generated CC0-1.0 engineering adaptation of the licensed graphical data. `tools/human_base_prepare.py` itself is original GPL-3.0-or-later code. The JSON supplies body-only UV-split positions/triangles/skin weights, all56 contract joints with actual helper-derived source anchors, a complete explicit163→56 collapse policy, and quantitative metrics. It feeds a canonical Blender authoring step; it is not a substitute glTF pipeline and is not a canonical `.blend` master.

The chosen1.75m height and metric ground registration are engineering decisions, not attested dimensions. The raw source has arms angled/bent and feet apart; it is not already the project's T pose. Preparation straightens the upper/lower arm, hand and leg chains using source helper lengths, flattens the digit plane, and transfers the body by linear blend transforms. Facial/tongue extensions collapse to head/jaw; individual toes collapse to ball. Sources are normalized before strongest-four pruning. See `prepared.report.json` for discarded-weight totals, affected vertex indices and pose displacement against unpruned transfer. The4.89mm maximum pruned/unpruned difference is a measurement, not a finished-deformation acceptance threshold.

This is an explicit **T-pose candidate**. Horizontal arms and straight leg joint chains are numerically checked, but that alone cannot prove anatomical shoulder/armpit/wrist/hip quality. The shortest-arc transfer does not constrain hand bone roll fully, so palms-down surface orientation must be solved/reviewed during canonical authoring. Finger flattening can require sculpt corrections. Face ARKit morphs, eye/teeth geometry, hair, period clothes, photographic skin, fourLOD outputs and animation/contact quality remain absent. Do not label this base a photographic adult or name it as a historical person's likeness.

The default `.mhmat` is a CC0 material-settings file, not a photographic texture. The official natural-male skin-pack metadata was found, but retrieval from `files2.makehumancommunity.org` was proxy-denied; no skin image from it is included or claimed cleared.


## Optional verified adult target recipes

`adult_25.recipe.json` and `adult_35.recipe.json` are explicit authoring recipes for reconstructed adult body components. They use only pinned CC0 graphical `.target` data, never copied MakeHuman program logic. The header-only universal target has no delta rows and is retained as provenance, not falsely treated as a male-body deformation. Real young/old macro targets change body and rig-helper vertices.

```
python tools/human_base_prepare.py --target-recipe assets/authored/humans/makehuman_hm08/adult_25.recipe.json --output assets/authored/humans/makehuman_hm08/prepared_adult_25.json
python tools/human_base_prepare.py --target-recipe assets/authored/humans/makehuman_hm08/adult_35.recipe.json --output assets/authored/humans/makehuman_hm08/prepared_adult_35.json
```

Each target file must be listed in `SOURCE.json`, match both manifest/recipe SHA256, and carry its own explicit CC0 graphical-asset header. Sparse deltas are applied to **all** source vertices before helper-based joint anchors, metric registration and the provisional T-pose transfer. Both recipes change all1,117 rig-helper vertices. Topology, face-corner UV mapping and original collapsed/pruned skin weights remain unchanged.

Age25 is a chosen point inside a20–29 source band; age35 is a chosen point inside a30–39 band. Neither establishes a precise age or birth year. The25 recipe averages three upstream shape categories equally; the35 recipe uses total young11/13 and old2/13, distributed equally across those categories, using25/90 authoring anchors. Upstream category filenames are provenance labels, **not** statements of residents' ethnicity, ancestry or likeness. This technical blend is an explicit liberty. All bodies retain reconstructed1.75m height. Named-resident appearance, age-specific skin, bone roll, face expression targets, clothing and photographic comparison remain separate gates.


## Verbatim upstream notice transport

The original upstream `LICENSE.md` is stored as deterministic `LICENSE.md.gz`, with fixed modification time and no archive filename. Its bytes are unchanged after decompression; the seven-equals setext title is genuine upstream text. Packing avoids treating that genuine notice as a repository conflict marker without altering the notice or the checker. `SOURCE.json` retains the actual upstream URL/path and original SHA256, plus stored gzip hash/size and decompressed hash/size. The preprocessor verifies both layers before accepting any graphical source. Read the notice with `gzip -dc assets/authored/humans/makehuman_hm08/LICENSE.md.gz`. Other graphical inputs remain plain and byte-preserved.


## Optional adult female source and dress assembly (T-1789)

`adult_female_25.recipe.json` blends the same pinned CC0 female-young graphical categories equally. The category names are software provenance, not a statement of resident ancestry. The1.65m height and chosen25-year authoring parameter are reconstructions. SOURCE-female.json is an explicitly selected complete manifest, leaving the original SOURCE.json and all existing male/neutral preparation bytes unchanged. The actual female body reproduces byte-for-byte with the native preparation command:

```sh
python3 tools/human_base_prepare.py --height-m 1.65 --source-manifest SOURCE-female.json \
  --target-recipe assets/authored/humans/makehuman_hm08/adult_female_25.recipe.json \
  --output assets/authored/humans/makehuman_hm08/prepared_adult_female_25.json
```

After a pinned `generators/blender.pin` executable is available, the separate explicit recipe is consumed by the same canonical human builder/exporter:

```sh
# Use the verified pinned binary, not a different system Blender.
source generators/blender.pin
"$BLENDER_CACHE/$BLENDER_DIR/blender" -b -noaudio --factory-startup --python-exit-code 1 \
  --python tools/human_teamster_blend.py -- \
  --recipe data/humans/recipes/adult_dress_1835.json \
  --variant flynn_mary_1835_dress_study --liberty L418 \
  --output assets/authored/humans/dress/flynn_mary_1835_dress_study/canonical.blend \
  --experimental-normal-probes --normal-probe-receipts /tmp/dress-normal-probes
bash tools/human_export.sh --master assets/authored/humans/dress/flynn_mary_1835_dress_study/canonical.blend
```

Those canonical commands are **prepared, not executed** in this source checkpoint. They do not waive normal, morph, hierarchy, sole, material, LOD, measurement or actual-browser gates. Existing reconstructed Mary Flynn is an optional model reference, not a historical portrait or personal wardrobe claim. No new biography, person, production-eligible asset or scene instance is minted. Skirt/apron are standing-only source constructions; walking, seated, clipping, LOD and photo acceptance remain open. Existing male Bronze skin and short04 hair are provisional reused inputs, not accepted female appearance. Source-array previews are not Blender exports.
