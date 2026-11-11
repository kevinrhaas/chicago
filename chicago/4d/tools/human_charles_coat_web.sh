#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Source proposal only. Run ONLY after source packet review; no Blender.
# Existing canonical image/codec commands, two near Charles children only.
set -euo pipefail
cd "$(dirname "$0")/.."
[ "$#" = 5 ] || { echo 'usage: tools/human_charles_coat_web.sh RECIPE INPUT_ROOT MASTER_CHILD_DIR FRESH_EXTERNAL_WEB NODE_MODULES' >&2; exit 2; }
recipe="$(realpath "$1")"
inputs="$(realpath "$2")"
masters="$(realpath "$3")"
out="$(realpath -m "$4")"
deps="$(realpath "$5")"
case "$out" in "$PWD"|"$PWD"/*) echo 'fresh external output required' >&2; exit 1;; esac
[ ! -e "$out" ] || { echo 'refusing existing output' >&2; exit 1; }
# Read the actual owner pin instead of creating a second version policy.
eval "$(sed -n -E '/^GT_(CLI|CORE|FUNCTIONS|EXTENSIONS)_VERSION=/p' tools/web_derivatives.sh)"
[ "$GT_CLI_VERSION/$GT_CORE_VERSION/$GT_FUNCTIONS_VERSION/$GT_EXTENSIONS_VERSION" = '4.5.0/4.5.0/4.5.0/4.5.0' ]
node -e 'for(const n of ["cli","core","functions","extensions"]){if(require(process.argv[1]+"/@gltf-transform/"+n+"/package.json").version!=="4.5.0")throw Error("pinned toolchain mismatch");}' "$deps"
cli="$deps/@gltf-transform/cli/bin/cli.js"
[ -f "$cli" ] || { echo 'pinned CLI missing' >&2; exit 1; }
scratch="$(mktemp -d -t charles-coat-web.XXXXXX)"
trap 'rm -rf "$scratch"' EXIT
mkdir "$scratch/web"
mkdir "$scratch/canonical-color"
for lod in 0 1; do
  name="nelson_charles_1904_coachman.lod${lod}.glb"
  python3 tools/verify_human_charles_coat.py "$recipe" "$inputs/assets/humans/$name" "$masters/$name" --lod "$lod" > "$scratch/master${lod}.json"
  cap=2048; [ "$lod" = 0 ] || cap=1024
  # Same owner route as human_export.sh: current MASTER GLB already carries its
  # canonical bindings. Do NOT repeat Blender or skin canonicalization.
  python3 tools/human_web_texture_inputs.py "$masters/$name" "$scratch/labeled.glb"
  node "$cli" resize "$scratch/labeled.glb" "$scratch/resized.glb" --width "$cap" --height "$cap"
  node "$cli" jpeg "$scratch/resized.glb" "$scratch/color.glb" --formats '*' --quality 92 --pattern 'c4d_web_opaque_*' --slots '{baseColorTexture,emissiveTexture}'
  cp "$scratch/color.glb" "$scratch/canonical-color/$name"
  node "$cli" meshopt "$scratch/color.glb" "$scratch/web/$name" --quantization-volume scene --level medium --quantize-normal 16
done
node tools/human_charles_coat_semantics.mjs "$recipe" "$inputs" "$masters" "$scratch/web" "$deps" "$scratch/canonical-color" > "$scratch/semantics.json"
# Only independently checked files reach the requested external output.
mkdir "$out"
cp "$scratch/web/"*.glb "$out/"
cp "$scratch/semantics.json" "$scratch/master0.json" "$scratch/master1.json" "$out/"
echo 'UNQUALIFIED portable WEB children; native loader/render/fit/budget/photo gates remain mandatory'
