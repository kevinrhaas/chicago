#!/usr/bin/env bash
# The portable-human export path, Blender -> GLB -> web derivative (T-1787).
#
#   tools/human_export.sh                    rebuild the CI fixture: its master from
#                                            tools/human_fixture_blend.py, its four
#                                            LODs into assets/humans/, their Meshopt
#                                            derivatives into assets/humans/web/
#   tools/human_export.sh --verify           the same into a scratch tree, then hold
#                                            it to the committed files BYTE FOR BYTE
#                                            (what .github/workflows/chicago-4d-humans.yml
#                                            runs). A difference fails, by file
#   tools/human_export.sh --master F.blend   export an authored master (T-1789 on):
#                                            same exporter, same derivative, same gate
#
# Each step is one command and none is a dialog (docs/HUMAN-ASSET-CONTRACT.md § 13):
#
#   1. Blender, the pinned binary (generators/blender.pin, sha256-verified exactly as
#      tools/bake.sh does), runs tools/human_export.py over the master. Every exporter
#      setting the contract depends on is written there with its reason.
#   2. gltf-transform, THE SAME PIN as tools/web_derivatives.sh (read from that file,
#      so there is one pin and not two), writes `meshopt` derivatives. Meshopt is the
#      only compression the renderer decodes; KTX2 and Draco are refused by the
#      contract, so nothing here asks for either.
#   3. tools/human_contract.py --glb gates the masters and the derivatives. A
#      derivative's quantised frame is read beside its master (check_glb's `master`).
#
# The browser half — skinning deforms, both clips play, a morph moves, materials and
# the texture load, every LOD opens with no console error, at 1280x800 and 390x780 —
# is tools/human_fixture.mjs, which also measures the per-LOD costs it records.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE=fixture
MASTER=""
while [ $# -gt 0 ]; do
  case "$1" in
    --verify) MODE=verify; shift ;;
    --master) MODE=master; MASTER="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# shellcheck disable=SC1091
source generators/blender.pin
CACHE="${BLENDER_CACHE:-/opt/blender-dl}"
BIN="$CACHE/$BLENDER_DIR/blender"
TARBALL="$CACHE/$(basename "$BLENDER_URL")"
if [ ! -x "$BIN" ]; then
  mkdir -p "$CACHE"
  [ -f "$TARBALL" ] || { echo "fetching Blender $BLENDER_VERSION ..."; curl -fL --retry 3 -o "$TARBALL" "$BLENDER_URL"; }
  echo "$BLENDER_SHA256  $TARBALL" | sha256sum -c - || {
    echo "SHA256 MISMATCH on the Blender tarball — refusing to run (see tools/bake.sh)." >&2
    exit 1
  }
  tar -xf "$TARBALL" -C "$CACHE"
fi
"$BIN" --version | head -1

eval "$(grep -E '^GT_(CLI|CORE|FUNCTIONS|EXTENSIONS)_VERSION=' tools/web_derivatives.sh)"
GT_NPX=(npx --yes
  --package "@gltf-transform/cli@$GT_CLI_VERSION"
  --package "@gltf-transform/core@$GT_CORE_VERSION"
  --package "@gltf-transform/functions@$GT_FUNCTIONS_VERSION"
  --package "@gltf-transform/extensions@$GT_EXTENSIONS_VERSION")

SCRATCH="$(mktemp -d -t humanexport.XXXXXX)"
trap 'rm -rf "$SCRATCH"' EXIT
OUT=assets/humans
[ "$MODE" = "verify" ] && OUT="$SCRATCH/out"

if [ "$MODE" != "master" ]; then
  MASTER="$SCRATCH/c4d_fixture.blend"
  echo "== master: tools/human_fixture_blend.py"
  "$BIN" -b -noaudio --factory-startup --python-exit-code 1 \
    --python tools/human_fixture_blend.py -- "$MASTER" | grep -E '^wrote ' || true
  [ -f "$MASTER" ] || { echo "the fixture master was not written" >&2; exit 1; }
fi

echo "== export: tools/human_export.py"
mkdir -p "$SCRATCH/lods"
"$BIN" -b -noaudio "$MASTER" --python-exit-code 1 --python tools/human_export.py -- "$SCRATCH/lods" \
  | grep -E '^wrote ' | sed "s#$SCRATCH/lods/##"
mkdir -p "$OUT/web"
written=()
for f in "$SCRATCH"/lods/*.glb; do
  name="$(basename "$f")"
  cp "$f" "$OUT/$name"
  "${GT_NPX[@]}" gltf-transform meshopt "$OUT/$name" "$OUT/web/$name" 2>&1 | grep -E '→' | sed 's/^info: //' || true
  written+=("$OUT/$name" "$OUT/web/$name")
done

echo "== gate: tools/human_contract.py --glb"
python3 tools/human_contract.py --glb "${written[@]}"

if [ "$MODE" = "verify" ]; then
  echo "== reproduction: the rebuilt bytes against the committed ones"
  bad=0
  for f in "${written[@]}"; do
    rel="${f#"$OUT"/}"
    if ! cmp -s "$f" "assets/humans/$rel"; then
      echo "   DIFFERS: assets/humans/$rel — rebuild with tools/human_export.sh and commit it" >&2
      bad=1
    fi
  done
  [ "$bad" = "0" ] && echo "   all ${#written[@]} files reproduce byte for byte"
  exit "$bad"
fi
