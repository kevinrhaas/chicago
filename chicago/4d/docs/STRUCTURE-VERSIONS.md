# Structure versions — several builds of one structure, compared by URL (T-1727)

The owner wants competing builds of the same house on dev at once — the Glessner
House first (T-1729, T-1730) — opened side by side, one of them chosen, and only the
chosen one made the default. Separate branch deploys are not needed; the choice is
made with query parameters:

    https://chicago.polecat.live/4d/dev/1835/?structure=<id>&version=<label>

beside `?year=` and `?anchor=` (main.js: *further state belongs in further query
parameters, never in more path segments*). Open two tabs with two labels and compare.
`version=default` shows the canonical record with the HUD saying so, which is what
makes a pair of screenshots unambiguous.

## What a version is

One committed alternate of ONE structure: a whole structure record plus its own mesh.

| file | what it is |
|---|---|
| `data/structures/<id>.json` | the canonical record — **the default**, untouched by versions |
| `data/structures/versions/<id>/<label>.json` | one alternate: a full record with the same `id`, plus a `version` block |
| `assets/gltf/versions/<id>/<label>/<id>__<phase>.glb` | its master, baked by `generators/build.py` |
| `assets/web/versions/<id>/<label>/<id>__<phase>.glb` | its web derivative, by `tools/web_derivatives.sh` |
| `assets/manifest.versions.json` | data → master and master → derivative, for every version mesh |
| `data/sidecars/<year>/versions/<id>/<label>.json` | its sidecar, compiled by `tools/compile_scene.py` with the default's own builder |
| `data/sidecars/<year>/versions/index.json` | the scene's list of versions — fetched **only** when an address asks for one |

The `version` block is the only key a version adds, and a canonical record may not
carry one:

```json
"version": {"label": "v2", "summary": "What differs, in a sentence for the card.",
            "test_fixture": false}
```

The layout and the label rule live in one place, `generators/common/versions.py`, which
every tool below imports.

## The rules, and where each is enforced

- **A version is never less honest than the default.** `tools/validate.py`
  (`check_versions`) runs the structure gate over it: schema, the provenance pass, the
  evidence ladder, the geometry declarations, the liberties it owes, ground contact. An
  invention in a version owes `docs/LIBERTIES.md` an entry exactly as one in a canonical
  record does.
- **It swaps a building; it never adds one.** The file sits under a canonical record that
  exists, carries that id, and resolves in a scene where the default also stands.
- **No mesh, or a stale mesh, is red.** `validate.py --stale` (`run_version_stale_check`)
  recomputes the version record's inputs hash (the same `generators/mesh_inputs.py`
  recipe) against `assets/manifest.versions.json`, and checks the derivative was made from
  that master.
- **Labels are short neutral strings** — `v1`, `v2`, `b`, `hall-plan`: lower-case letters
  and digits in hyphen-separated runs, at most 24 characters, never `default`. **Never a
  model identifier**, which the repository forbids in any artifact; the owner keeps his own
  mapping from label to run. The refusal holds the names as digests so it does not have to
  write them down.
- **The boot payload does not grow.** The renderer reads the versions index only when the
  address carries `?version=`; a plain visit downloads nothing new.
- **An unknown id or label never fails silently.** The default loads and the HUD's version
  chip reads *default shown* in the warning tone; tapping it (and the hint on entry) gives
  the sentence — which structure, which label, what versions do exist.
- **The HUD and the card name the active version** — a chip in the year badge, and a flag
  at the head of the structure's card (plus `version <label>` on its Record pane).

`tools/test_structure_versions.py` provokes each validator red on a sandbox,
`tools/test_structure_versions.mjs` holds the address-bar rules, and the release smoke
(`tools/smoke_renderer.mjs` part 3, both viewports) boots the fixture in a second tab and
checks that exactly one registry entry changed.

## Adding a version (T-1730's path)

```sh
python3 tools/structure_versions.py seed <id> <label> --summary "what differs"
# edit data/structures/versions/<id>/<label>.json into the alternate it is for
tools/bake.sh --only <id>          # bakes <id> AND its versions (Blender), or dispatch
                                   # the chicago-4d-bake workflow with only=<id>
python3 tools/compile_scene.py --all
./tools/check.sh
```

`seed` copies the canonical record and adds the `version` block. If the copy's inputs
hash still equals the committed canonical bake's, it **adopts** that bake (copies master
and derivative under the version's paths, `adopted_from` in the manifest) — honest,
because freshness here is defined on inputs. As soon as the edit changes anything a
builder reads, the hash differs and `--stale` demands a real bake. A full rebake
(`tools/bake.sh` with no `--only`, the nightly) rebuilds every version with the town, so a
generators/ edit never strands one.

`python3 tools/structure_versions.py list` shows what exists; `status <id>` names any mesh
of a structure or its versions that needs a bake.

## Promoting the chosen version (the owner's final call)

```sh
node tools/promote_version.mjs <id> <label> [--keep-as <old-label>] [--dry-run] [--bake]
```

The chosen version's record becomes `data/structures/<id>.json` (its `version` block
dropped); the old default is kept as `data/structures/versions/<id>/<keep>.json`
(default label `pre-<label>`), so the comparison still works afterwards; both meshes,
both derivatives and all three build records move with them; the sidecars are
recompiled. Nothing is re-baked in the ordinary case — the inputs hash does not depend on
the directory or on the `version` block — and `status` is asked afterwards anyway: a
version that was never baked is baked with `--bake`, or named with the command to run.
Then `./tools/check.sh`, a changelog entry, and ONE pull request into `dev`: the owner's
choice, reviewable line by line. `node tools/promote_version.mjs --self-test` proves the
round trip, byte for byte.

## The smoke's fixture — test-only, and labelled so

`data/structures/versions/bates_auction_room/fixture.json` is a **test fixture**, not an
alternative reading: the Bates auction room's default record copied unchanged
(`test_fixture: true`, and its summary says so), with the canonical mesh adopted. It exists
so the release smoke can prove the switch on a real 1835 structure until the Glessner
versions land. A visitor never sees it unless the address asks for
`?structure=bates_auction_room&version=fixture`, and the card then says it is a test
fixture. Retire it once real versions exist and the smoke points at one of them.


## Glessner v4 detail derivatives (T-1730)

### Owner selection, September 29, 2026

The owner selected v4 as the default and authorized dev-to-production promotion.
The package-aware promotion moves the canonical record, master, full derivative,
light derivative and their manifests together; the old default is `pre-v4`.
V2 and v3 remain unchanged. The three-file recovery archive now materializes the
canonical paths, so a clean checkout and the normal nightly derivative producer
both retain the same full/light contract. The light recipe is regenerated against
the promoted record; the full master geometry is unchanged.

The default loader recognizes the explicitly declared canonical light asset and
uses the same measured Full allowance as the former comparison version. Unknown
or older versions do not inherit that allowance. A future replacement must handle
the package explicitly; the promotion front end refuses to strand it.

The remainder of this section records the original alternate-version design.

The selected v4 uses its canonical detailed mesh in Full and a separately
produced mesh in Balanced and Light. Both consume the same version record and
architectural opening functions. The reduced profile keeps the envelope, all
172 scheduled openings, doors, roof intersections, chimneys and confidence.
It reduces stone-face sampling, carving, roof-course sampling and grass blades.
Omitted microrelief changes the measured horizontal bounds by at most 25.7 mm;
roof crowns, chimney height and ground extrema are retained.

The optional sidecar field `asset_lods.light` names an ordinary glTF asset,
relative to the same asset base as `asset`. Only this exact comparison version
opts in. A light boot downloads only the reduced file. A later detail change
prepares a replacement before swapping the visible building, preserves record
identity and placement, and keeps the prior model on a failed request.

`tools/web_derivatives.sh` produces both files before recording freshness. The
standard-library producer `tools/structure_versions.py build-light` copies the
current full master's materials and images into the reduced geometry; it needs
no Blender. `assets/manifest.versions.json` records the master, recipe and output
hashes. The light GLB also carries a receipt checked against those inputs and a
200,000-triangle ceiling before it can be recorded. Failed production cannot
stamp a previous light file as fresh.

The recovery archive contains exactly the full master, full web derivative and
light web derivative. Restore writes only missing files and refuses divergent
existing bytes. An ordinary producer updates the archive; `--out` measurements
do not. Promotion to default must explicitly retarget or retire this alternate
package and its LOD contract; the generic promotion command refuses it until
that lifecycle is handled.

The selected v4 Full allowance is 3,800,000 rendered triangles, measured from
a five-stand price whose maximum was 3,430,985. The ordinary town and all Light
(825,000), Balanced (1,280,000) and draw-call (215) allowances remain unchanged.
This is a measured allowance for the requested inspection detail, not a claim
about frame rate on every device. The final published browser receipt is kept
with the visual review in `docs/RESEARCH/glessner-v4-qa/`.
