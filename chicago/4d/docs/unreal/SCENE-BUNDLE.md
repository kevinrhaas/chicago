# The scene bundle — contract `chicago4d-scene-bundle/1`

T-1357 asked for a versioned, engine-neutral handoff that the owner can download today and
an Unreal or server worker can consume later. It was split in two: **T-2067** (this
document and `tools/scene_bundle.py`) is the contract, the packer, the fresh-consumer
verifier and the reproducibility check; **T-2068** attaches packing to the scheduled
content build (`chicago-4d-bake.yml`) and its manual dispatch, publishes it, and keeps a
latest-good pointer. That second half is a workflow change. Until it lands, a bundle is
something you make by hand from a commit, and nothing publishes one.

## Making one, checking one

```sh
cd chicago/4d
python3 tools/scene_bundle.py pack --scene 1835 --commit <sha> --out <dir> --receipt <dir>/receipt.json
python3 tools/scene_bundle.py verify <dir>/chicago4d-scene-1835-<sha12>-<digest12>.tar.gz --expect-digest <payload digest>
python3 tools/scene_bundle.py repro --scene 1835 --commit <sha>    # same commit twice: same bytes?
python3 tools/scene_bundle.py --self-test                            # check.sh runs this
```

`pack` takes a **validated** commit, meaning one whose gate passed. Choosing that commit
is the caller's job: BUILD-AND-RELEASE.md § "latest best" is the rule by hand, and T-2068
makes the content build pack the commit its own gate just passed.

First reading, 2026-10-04, dev at `f5542e3c9fa1`: 1,431 files, 544 structures, 87.3 MB of
payload in a 23.0 MB archive. It packs in about 3 s. Two builds gave the same archive
sha256 (`408df572…`) and the same payload digest (`c4b820ce…`). A copy in a fresh
directory verified against that digest.

## What is in it

```
chicago4d-scene-<scene>-<commit12>/
  BUNDLE.json      the manifest (below)
  SHA256SUMS       `sha256  payload/<path>` per file, sorted: `sha256sum -c` reads it
  payload/         the source layout, unchanged
    data/scenes/<scene>.json, data/datum.json, data/terrain/epochs.json
    data/terrain/epochs/<epoch>/heightfield.json + heightfield.bin
    data/sidecars/<scene>/index.json, one sidecar per structure, sources/ (runtime provenance)
    assets/gltf/<every master GLB the index names>, terrain__<epoch>.glb, water__<epoch>.glb
    assets/manifest.json (the bake's build record), assets/LICENSES.md
    generators/blender.pin
```

**Keeping the source layout is deliberate.** The Unreal adapter
(`renderers/unreal/Scripts/import_scene.py`) reads a checkout through `CHICAGO_SOURCE`.
Point that variable at an extracted `payload/` and the adapter reads a bundle with no
change. Textures are embedded in every GLB, so no external image is referenced.

**What it never carries:** `data/research/`, source deposits under `data/sources/`, secrets,
`assets/textures/` (bake inputs), `assets/web/` (web derivatives; the bundle ships the
masters), structure versions, jaunt routes, and engine binaries of any kind.

## `BUNDLE.json`

| field | what it says |
|---|---|
| `schema` | `chicago4d-scene-bundle/1`. A consumer refuses any schema it does not read. |
| `scene` | id, title, target date, terrain epoch |
| `source` | repository, full commit, commit time, and `read_from`. Every byte comes from the git objects of that ONE commit and never from a working tree, so mixed-commit output cannot be built. |
| `build` | the Blender pin (version + sha256) and the packer's own sha256 |
| `coverage.carried` | structure count, terrain and water GLBs, heightfield, sidecar index, source-record count |
| `coverage.structures_without_glb` | each indexed structure with no mesh, and what draws it instead. It is listed, not dropped. |
| `coverage.omitted_layers` | every row of GLB-CONTRACT § Layers drawn at load, **read from that table**, with the reason it is absent |
| `coverage.partial` | true when `--only` cut the structure list. A published bundle is never partial. |
| `review_required` | the ids carrying the flag, and whether each `touches_removal`. The flags travel inside their sidecars. |
| `files[]` | path, bytes, sha256 and the **licence basis** of every file |
| `payload_digest` | sha256 of SHA256SUMS: the bundle's identity |

## Refusals

**Packing refuses** in three cases: a commit that lacks a file the scene names; a GLB that no
recorded bake produced and that has no `assets/LICENSES.md` row (unknown rights do not
ship); and any source whose `rights_status` is `check_required`/`restricted` and whose
`asset_use` is `geometry`. The last two are `validate.py`'s own release refusals, held
again at the point of release.

**Verifying refuses** any of these:
- a member path that is absolute, contains `..`, or is a link or device;
- more than one top-level directory, or a missing `BUNDLE.json`;
- a file listed but absent, or present but unlisted;
- a byte that disagrees with its sha256;
- a payload digest or SHA256SUMS that disagrees with the listing;
- a GLB whose size disagrees with the build record that came with it (a mesh from another
  build);
- a sidecar naming a mesh the bundle lacks;
- with `--expect-digest`, any digest but the one asked for.

A forger who re-hashes the whole manifest gets past every check except the last one. **A
consumer downloads by digest for that reason**, and T-2068's discovery manifest is where
it gets the digest. The self-test demonstrates each refusal on a real packed bundle.

## Reproducibility, and where the timestamps went

The archive holds no wall-clock time. Each member's mtime is the commit's time, owner
and group are zero, the gzip header carries no name or time, and members are sorted. On
one toolchain, the same commit therefore packs to the same bytes, and `repro` asserts
that. **Across machines, the payload digest is the identity**: a different zlib may
compress the same payload differently, but the digest is computed over the files and
does not move. The build instant goes in the `--receipt` file beside the archive and is
deliberately kept out of the archive.

## How T-1358 consumes it

1. Read the latest-good digest from T-2068's discovery manifest. Download the archive and
   run `verify --expect-digest`. Refuse the update on any failure, and keep the current
   import.
2. Extract the archive into a NEW directory named by digest. Point `CHICAGO_SOURCE` at
   `payload/` and record the source commit from `BUNDLE.json` as `CHICAGO_COMMIT`.
3. Plan the incremental update by diffing `files[]` against the bundle already imported.
   An unchanged sha256 means an unchanged asset: skip it. A changed one is reimported. A
   path that is gone is a retired asset: remove it, because the prototype never did.
4. Switch to the new import only after it verifies, so the previous digest stays the
   rollback.

## When T-0252's layer exports arrive

GLB-CONTRACT § Layers drawn at load decides that each load-drawn layer is exported by the
module that draws it, **into this bundle**, stamped with its heightfield. When the first
export lands (T-1360's street corridor):

- the bundle adds `payload/exports/<scene>/<layer>.glb`;
- that layer moves from `coverage.omitted_layers` to `coverage.carried`, together with its
  stamp, and the table row stays put;
- `verify` additionally checks that each export's `heightfield_sha256` matches the
  heightfield in the same bundle. An export frozen against a ground that has since moved
  is T-0001's fault, and it is refused;
- the schema moves to `/2` only if an existing field changes meaning. Adding a carried
  layer does not change any field's meaning.

The card layers (fauna, residents, businesses) would ship as the JSON they already are,
with review flags intact, and never as figures (L1).
