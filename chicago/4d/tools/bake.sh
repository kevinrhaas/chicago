#!/usr/bin/env bash
# The content build. Minutes, not seconds — runs on demand and nightly, NOT on
# every commit. tools/check.sh is the per-commit gate and needs no Blender.
#
#   tools/bake.sh                 build everything
#   tools/bake.sh --only <id>     build one structure
#   tools/bake.sh --no-bake       skip the UV unwrap (fast iteration)
#
# AO is NOT baked here and never has been in the nightly: `--ao` is opt-in on
# generators/build.py and nothing passes it (T-0015). This line used to say
# `--no-bake` skips "AO baking", which read as though AO were on by default.
#
# Blender is pinned by exact version + sha256 in generators/blender.pin. Version
# pinning is what buys back determinism from a stateful tool; determinism itself
# is defined on INPUTS (see assets/manifest.json), because Cycles AO is not
# bit-reproducible across hardware.
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source generators/blender.pin

CACHE="${BLENDER_CACHE:-/opt/blender-dl}"
BIN="$CACHE/$BLENDER_DIR/blender"
TARBALL="$CACHE/$(basename "$BLENDER_URL")"

fetch_blender() {
  mkdir -p "$CACHE"
  if [ ! -x "$BIN" ]; then
    if [ ! -f "$TARBALL" ]; then
      echo "fetching Blender $BLENDER_VERSION ..."
      curl -fL --retry 3 -o "$TARBALL" "$BLENDER_URL"
    fi
    echo "$BLENDER_SHA256  $TARBALL" | sha256sum -c - || {
      echo "SHA256 MISMATCH on the Blender tarball — refusing to run."
      echo "Either the download is corrupt or blender.pin is wrong. Do not 'fix'"
      echo "this by updating the hash without knowing why it changed."
      exit 1
    }
    tar -xf "$TARBALL" -C "$CACHE"
  fi
  "$BIN" --version | head -1
}

echo "== Blender"
fetch_blender

echo
echo "== generate + bake"
"$BIN" -b -noaudio --factory-startup --python generators/build.py -- "$@"

echo
echo "== web derivatives"
# Lifted out whole by K36(b) into `tools/web_derivatives.sh`, so a
# Blender-free runner can regenerate the derivatives from the committed
# masters and MEASURE the result. The flags, the bit depths and the reasons
# all live over there, and this is their only caller.
tools/web_derivatives.sh

echo
echo "== sidecars"
python3 tools/compile_scene.py --all

echo
echo "== publish"
tools/publish.sh

echo
echo "== gate"
tools/check.sh

# The smoke runs against the PUBLISHED mirror, not the source tree, and it runs
# here because this is the step that just produced the compressed derivatives.
#
# The two trees do not load the same geometry: a sidecar's `gltf/<name>.glb`
# resolves to the uncompressed masters in the source tree and to the meshopt +
# quantised derivatives on the site. For as long as the smoke only ran against
# the source tree it never loaded a compressed asset, and a bug that collapsed
# every building to a two-metre box shipped past a fully green gate — twice.
# Whatever else is true, the bytes a visitor downloads have to be the bytes
# something tested.
#
# T-0165 — AND IN CI THAT PROPERTY IS NOW KEPT SOMEWHERE ELSE, so read the next
# paragraph before concluding the nightly stopped testing itself.
# `chicago-4d-bake.yml` sets SKIP_SMOKE=1 and runs the smoke as its own JOB,
# which takes the published mirror from this run as an ARTIFACT and drives it at
# both viewports in parallel. The reason is a ceiling, not a change of mind: run
# #261 was cancelled at 43m51s of a 45-minute job, inside the desktop half, and
# ~12 minutes of baking plus ~13 a viewport never fitted. Splitting it gives each
# part its own budget and still refuses to open a bake PR until both viewports
# are green. The bytes a visitor downloads are still the bytes something tested —
# tested one job later, by a job that cannot run unless this one succeeded.
#
# Run WITHOUT SKIP_SMOKE (the default, below) and the smoke happens here, inline,
# which is what you want locally: there is no artifact to hand anything to.
if [ "${SKIP_SMOKE:-0}" = "1" ]; then
  echo
  echo "== smoke (skipped: SKIP_SMOKE=1)"
else
  echo
  echo "== smoke (published mirror)"
  node tools/smoke_renderer.mjs --published
fi
