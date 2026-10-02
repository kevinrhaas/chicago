#!/usr/bin/env bash
# T-1801 — the 1835 fabric proof, end to end, in one foreground command:
#
#   tools/fabric_proof_1835.sh [work-dir] [review-out]
#     work-dir    default /tmp/fabric-proof-1835 (GLBs + packed maps; never committed)
#     review-out  default docs/RESEARCH/1835-fabric-proof (captures + review.json)
#
#   1. Blender (the pinned one, fetched and verified by tools/bake.sh's own rule)
#      builds the proof twice: with the recessed sash, and with the town's flat
#      opening for the comparison — tools/build_fabric_proof_1835.py.
#   2. Each master goes through the web-derivative step's EXACT flags
#      (tools/web_derivatives.sh: optimize --compress false --simplify false
#      --palette false, then meshopt --quantize-position 14, gltf-transform 4.5.0).
#      Leaving out --palette false folds every material into one PaletteMaterial —
#      measured on this proof — and the relief binding then has no name to key on.
#   3. tools/fabric_proof_1835_maps.py packs strategy A's relief pairs at 1024 and 512.
#   4. tools/fabric_proof_1835_review.mjs captures the comparison at 390x780 and
#      1280x800 and prices the tiers. It needs the published mirror for Glessner v4,
#      so run tools/publish.sh first if ../../site/4d is absent.
#
# Nothing here touches assets/, data/ or the town. See docs/RESEARCH/1835_fabric_proof.md.
set -euo pipefail
cd "$(dirname "$0")/.."

WORK="${1:-/tmp/fabric-proof-1835}"
OUT="${2:-docs/RESEARCH/1835-fabric-proof}"
mkdir -p "$WORK"

# shellcheck disable=SC1091
source generators/blender.pin
BIN="${BLENDER_CACHE:-/opt/blender-dl}/$BLENDER_DIR/blender"
[ -x "$BIN" ] || { echo "no Blender at $BIN — run tools/bake.sh once to fetch the pinned one"; exit 1; }

GT=(npx --yes --package "@gltf-transform/cli@4.5.0" --package "@gltf-transform/core@4.5.0"
    --package "@gltf-transform/functions@4.5.0" --package "@gltf-transform/extensions@4.5.0"
    gltf-transform)

for opening in recessed flat; do
  name="fabric_proof_1835"; [ "$opening" = flat ] && name="fabric_proof_1835.flat"
  echo "== build ($opening)"
  "$BIN" -b -noaudio --factory-startup --python tools/build_fabric_proof_1835.py -- \
    --out "$WORK/$name.glb" --opening "$opening" 2>&1 | grep '^PROOF' || { echo "blender build failed"; exit 1; }
  tmp="$(mktemp -t fabricproof.XXXXXX.glb)"
  "${GT[@]}" optimize "$WORK/$name.glb" "$tmp" --compress false --simplify false --palette false >/dev/null
  "${GT[@]}" meshopt "$tmp" "$WORK/$name.web.glb" --quantize-position 14 >/dev/null
  rm -f "$tmp"
  sha256sum "$WORK/$name.glb" "$WORK/$name.web.glb"
done

echo "== maps"
python3 tools/fabric_proof_1835_maps.py --out "$WORK/maps"

echo "== review"
node tools/fabric_proof_1835_review.mjs --work "$WORK" --out "$OUT"
