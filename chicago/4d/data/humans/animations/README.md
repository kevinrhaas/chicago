# Natural standing animation derivative

`natural-standing-v1.json` authors a plain eight-second standing loop on Otis
Bardwell's existing portable rig: breathing and a modest head/neck look. The
original arm/elbow and lower-body channels remain unchanged. It creates no new
identity, observed action, gesture, dialogue or historical likeness.

This is an animation-only CPU derivative of the exact qualified canonical parents
named in the recipe. It appends a genuine glTF `idle_natural_v1` clip to four master
LODs and four web LODs. All original BIN bytes, compressed web views, geometry,
images, skins, inverse binds, nodes, material values and old clips survive. New
uncompressed animation accessors coexist with the original Meshopt geometry.
Canonical run/artifact metadata describes the parents; it is not a qualification
of the appended clip.

The clip's `canonical_rig_pose_parent_sha256` names the common master-LOD0 pose
used to author all eight clips. Each file's distinct canonical parent identity is
preserved in `natural-standing-v1.derivation.json`. The initial finite CPU
qualification names its exact tested bytes; the separate metadata bridge records
the later clip-metadata repair and proves that the entire BIN and every other
decoded JSON value are unchanged. It does not relabel the old qualification as a
new run or provide photographic acceptance.

Generate into a fresh, separate directory:

```sh
python3 tools/human_natural_idle.py --output /tmp/natural-standing-new
```

The generator reads a local parent only if its pinned SHA matches. After a child
occupies that filename it reads the exact parent blob at the recipe's Git revision.
That revision must already be available locally; this command never fetches,
checks out, rewrites or prunes Git history. No Blender installation is needed for
this animation derivative. The pure `authored_angles` recipe is the source for
future shared-rig canonical authoring; a future Blender/export run needs its own
actual qualification and does not inherit these results.

The actual native CPU inspection is separately executable:

```sh
node tools/human_natural_idle_cpu.cjs \
  --candidate /tmp/natural-standing-new --output /tmp/natural-standing-readback
```

It uses the native GLTFLoader, Meshopt decoder, AnimationMixer, skinning and human
actor lifecycle without requesting WebGL. It samples all 65 new keys and 64
midpoints, compares every footwear vertex, and probes shirt/waistcoat vertices
against the original idle's actual key/midpoint distance envelope. Potential
changes use agreeing BODY ray parities instead of treating a nearest-face normal
as a global inside test. Known injected penetration and shoe drift must be
rejected. Its 10 micrometre numerical allowance is an observer parameter, not a
project tailoring budget. Inherited garment penetrations remain disclosed.

These finite CPU checks do not establish continuous surface fit or photographic
quality. Actual published desktop/phone motion and clothing review, the existing
all-asset native browser measurement, complete app gates and ordinary DEV PR
checks remain required. Walking, gestures, populated routes, mounted riders,
drivers and boarding remain separate unfinished work.

## Seated driver looking animation

`seated-driver-look-v2.json` appends an original eight-second head/neck action to the exact seated Otis and Hans exports used by the town transport layer: master/web LOD0 and LOD3 for each resident. The old `sit_drive`, walking and standing clips and every original BIN byte remain. LOD1 and LOD2 are unchanged. This keeps the standing regeneration chain exact: its selected original standing children must reproduce before the subsequent seated derivative can match.

Generate separately with `python3 tools/human_seated_look.py --output /tmp/seated-looking-new`; verify installed children with `python3 tools/human_seated_look.py --check`. The recipe pins the immutable public parents and the matching master pose for each resident and LOD. The new curves are authored only for `neck_01` and `head`; all other local channels remain original. The jaw and eyes move with their head while their own local channels stay fixed.

The derivation record contains exact parent/child SHA256s. The separate native record covers 65 keys and 64 midpoints per child through actual GLTFLoader, Meshopt and AnimationMixer with real CPU image decoding. Every protected body world transform and Float32 skin palette is exact, and selected Hans web LOD0/3 palms retain the original measured barycentric points. The binding-refresh record changes only four active child payload hashes; original triangle, barycentric, point, pose and source-proof fields remain historical measurements. These finite CPU results do not provide browser/WebGL, garment, scene-contact or photographic acceptance.

The existing browser measurement command is `node tools/human_fixture.mjs --write`; it has no selective-file flag and measures all 24 human GLBs at desktop and phone sizes before writing `data/humans/fixture.measure.json`. Until that command and the actual scene checks pass, the prepared seated increment remains unqualified for delivery. Older natural-standing receipts, metadata bridges and standalone resident measurements remain immutable parent evidence; their earlier accepted hashes are not retargeted to the new children.
