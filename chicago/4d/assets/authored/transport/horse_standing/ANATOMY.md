# Source-bounded near anatomy — T-3088

This is the canonical authored-mesh source path for one generic working horse.
It uses the licensed selected d454 eye-UV parent, not the rejected procedural
horse regression fixture. The acquired original, b479 standing stage and d454
parent remain immutable. Original sevketkabatas/CC-BY-4.0 and Objaverse notices
remain applicable to the derived geometry and unchanged texture payloads.

The candidate revision `r3_original_cage_and_thinner_upper_margin` is
`925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48`,
4,158,016 bytes. This branch selects it after fresh native loader/clone/Mixer
65-key+64-midpoint physical qualification, including all refined faces and contact
witnesses. Final source/published scene, phone and photographic surface checks
remain required. It stays below the existing 4MiB asset cap; there is no budget
increase or borrowed old-body pass.

## Authoring and source boundary

`anatomy-v2-recipe.json` supplies per-feature cleared source IDs, exact image
hashes, reconstructed control dimensions and the hoof-refinement bounds.
The actual head/hoof/posterior plates and the two living-animal photographs were
inspected. They support anatomical relationships and continuity. Their pixels
are not sampled into the model; modern breed, markings, coat and measurements
are not transferred into an 1835 historical claim.

The upper-lid field lifts/recesses its margin while tapering over the brow and
retaining the lower lid. Normals follow the analytical deformation Jacobian.
The hoof wall, coronet and toe receive one adaptive, geometrically welded
subdivision. Old-vertex and edge masks use the same original cage; bounded
horizontal fairing rounds the near silhouette without arbitrary torso changes.
UV seams retain separate attribute rows and matching geometry. New skin rows
interpolate their declared original source edges without dropping influences.

The original eye globes, repaired eye-UV stream, all six embedded image payloads,
hair geometry, 26-joint hierarchy/inverse binds and 12s standing clip remain
protected. Original body weight rows remain exact in this candidate. The selected
body topology **does change**: 4,313→5,595 vertices and 7,390→9,794 triangles,
17,390 triangles for the whole three-material animal. Named support anchors and
the canonical ground datum are retained; the old toe/contact outline may move.
Every original contact-face descendant therefore belongs in the fresh proof.

The generator checks actual serialized parent/child triangle orientation as well
as local Jacobians. Those checks do not prove self-intersection freedom, dynamic
contact, gait, photographic appearance or performance.

## Repeatable build

Use the existing supported Python toolchain; this path requires no Blender
installation or alternate executable. The parent contact metadata is frozen at
`tools/fixtures/horse-anatomy-parent-sidecar-v1.json` (SHA256
`4ec44024d4fbefae88b8f0a1deb3be92503768b65dba590c5762691ce3b9c924`),
so updating the live sidecar cannot silently alter a later regeneration.

```sh
python3 assets/authored/transport/horse_standing/generate_anatomy_v2.py \
  --reference-dir /path/to/exact/cleared/Horse-plates \
  --output-dir /tmp/horse-anatomy-fresh-output
```

The immutable cleared-reference archive and exact member hashes are recorded in
the existing horse reference register and the recovered source packet. The command
verifies every supplied image hash and every source ID's permitted rights before
writing a separately versioned GLB and derivation receipt. It refuses to overwrite
an output directory or a source. The receipt distinguishes original parent, recipe,
generator, new body streams and outstanding acceptance.

## Review and remaining scope

Actual native parent/candidate views cover front, both profiles, quarter, rear,
head/front/quarter/both sides, fore/hind hooves and rear hocks. The corrected hoof
contour reads smoother while retaining the coherent body silhouette. The resting
eyelid still reads heavy. This selected asset has no material normal texture;
matched production and normal-map-off captures are identical. The broad upper
hood is a geometric discrepancy against the anatomical/photo reference, not a
normal-map explanation. T-3088 remains open; this checkpoint preserves the
rounded hoof and bounded body-authoring progress without claiming a finished
eyelid or full photographic acceptance.

External profile `50bd2059` and strip `5a2b2e87` prototypes were rejected by
actual proper-crossing checks and were never installed. The strip passed its
local topology/protected-data checks but crossed the surrounding body and eye
globes. Its preserved boundary itself includes points inside the original
embedded-eye interface, so an everywhere exterior globe-clearance constraint
cannot preserve that boundary. Future rim authoring needs an honest interface
and boundary design; neither those rejected prototypes nor their partial
qualifications are acceptance of this selected master.

The full anatomical review covers head/ears/muzzle, neck/withers/shoulder, barrel/
croup, fore/hind limbs and joints, hoof wall/pastern, mane/tail and source scale/
frame. Existing source-supported anatomy is retained where the views justify it.
Unseen soles, grooming, coat and absolute dimensions remain reconstructed. Surface,
portable LOD and full static photographic qualification remain T-3089; gait,
harness, riders/drivers and interactions retain their existing tickets. This work
does not activate walking, trot, tack, teams, riding or boarding.
