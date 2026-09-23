# Chicago 1835 — standalone Mac preview

This is a native Unreal renderer of the committed 1835 terrain and structure
glTF assets. It launches without Unreal Editor, a browser, or a streaming server.
It is a development preview of an evidence-bounded reconstruction, not a released
historical scene. Consult the source JSON sidecars for confidence and provenance.

## Playing

Open `Chicago4D.app` in the packaged `Mac` folder. Keep the packaged output
together when moving it. This first target is Apple Silicon (`arm64`); Intel Macs
and Windows have not been built or validated by this slice.

- WASD: walk; mouse: look.
- Space: jump.
- R: restart at the scene's starting point.
- Escape: quit.

The character has a walking collision capsule and camera, with no human mesh.
The app starts in Chicago with no gameplay debug overlays. Solid terrain and
buildings use triangle collision for this preview; water has no blocking collision.
Rigid structures sit on the lowest of 25 terrain samples across their rotated
footprint, matching the browser renderer. This fixes the fort palisade floating
above the downhill side when it was anchored only at its origin.
Structure bearings use explicitly named Unreal yaw; the garden fence stays upright
at its 53-degree ground bearing. The verifier checks every structure for zero pitch
and roll, and checks the garden fence world height remains below 1.5 metres.
R returns to the start if you leave the useful walkable area.

## Coverage

Included: the selected scene's committed terrain GLBs, structure GLBs, their
imported materials, sidecar positions/orientations, first-person walking, daylight,
and a small controls overlay.

Missing: browser-generated streets, flora, props and enclosures; research cards,
search, confidence visualization and time travel; a water-boundary gameplay policy;
full renderer parity and bridge-route validation. `import_report.json` names skipped
records and review-required records. Do not describe this as the full browser game
ported to Unreal, or mark the historical scene released on this build's account.

For subsequent update rounds, follow the [build-and-release runbook](../../docs/unreal/BUILD-AND-RELEASE.md): select a passing dev revision, build a fresh checkout, test, and publish a versioned prerelease. The [parity tracker](../../docs/unreal/PARITY.md) identifies features that a rebuild alone cannot add.

## Rebuild on a qualified local Mac

Prerequisites: a licensed Unreal Engine **5.8.2** installation, Apple Silicon Mac,
full Xcode selected as the developer directory, Python 3, and a clean checkout of
the repository's chosen `dev` revision. The local validation used Xcode 27.0.
Compilation and cooking need substantial free disk space and memory.
Cooked files are written directly to disk (`bUseZenStore=False`), so packaging
does not depend on an ephemeral local Zen storage process surviving the cook.

Run from this directory, choosing **new** output directories outside iCloud Drive
or synced Desktop/Documents folders:

```sh
python3 build_mac.py \
  --engine '/Users/Shared/Epic Games/UE_5.8' \
  --project-dir "$HOME/Chicago4D/build-project" \
  --archive-dir "$HOME/Chicago4D/build-output"
```

The script refuses existing output directories and an uncommitted source tree.
It builds the editor module, imports source GLBs into a fresh project, then uses
Unreal AutomationTool to build, cook, stage, package and archive the Mac app.
The existing Blender files and original Unreal prototype are untouched.
The receipt records the source revision, engine version, imported coverage and
executable hash. A successful package still requires a real play test.

Generated `.uasset`/`.umap` content, binaries and caches are not hand-authored assets:
recreate them with this script. The original glTF and license/provenance records
remain in the repository's `assets/` and `data/` directories. New source for this
adapter is confined to `renderers/unreal/`; no engine binaries are redistributed
in Git. This fresh-build workflow deliberately does not implement T-1358's
incremental bundle update/retirement contract.

## Signing and distribution

This configuration uses Apple's **Sign to Run Locally** setting and does not
require an Apple developer account to build on the local Mac. It is not a
Developer ID signed/notarized public download. Qualify signing, notarization,
license notices and a second-machine test before distributing it broadly.
Do not disable Gatekeeper to solve a distribution problem.

## Execution restriction

A generic remote web worker cannot build or validate this app. It needs the
engine installation, compatible SDK, local GPU and graphical session. A future
Mac build runner can automate packaging once those prerequisites are installed
and authorised; installing or renting a runner is not part of this ticket.
Streaming, server deployment and Windows packaging remain separate work.

## Packaged movement check

Run the packaged executable with
`-ChicagoWalkTest -RenderOffScreen -unattended -nosound > /absolute/path/walk.log 2>&1`.
This opt-in check ignores keyboard and mouse input, fixes the heading south,
waits for the character to settle, walks forward through the
normal character movement component, backs away, records position/speed/grounded
state each second, and quits after 21 seconds. It does not teleport, enable flight,
or disable collision. `CHICAGO_WALK_TEST_RESULT PASS` means the character finished
grounded, moved horizontally, and stayed near its starting elevation. It is a
spawn-route smoke check, not proof of every wall, bridge or river boundary.

Read the per-second readings to distinguish a wall stopping motion from a failure
to move. Also open the app normally to inspect materials and test mouse look,
restart and quit. This switch is off for an ordinary double-click launch.
