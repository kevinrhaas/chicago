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
