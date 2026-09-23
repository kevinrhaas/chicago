#!/usr/bin/env bash
# Chicago 1835 — local CI gate. Must pass before any commit.
# Keep this fast. A gate that takes four minutes gets skipped.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 1/4  structure dataset"
python tools/validate_structures.py

echo "==> 2/4  asset licenses"
if [ -d assets ]; then
  missing=0
  while IFS= read -r f; do
    rel="${f#assets/}"
    grep -qF "$rel" assets/LICENSES.md 2>/dev/null || { echo "  ERROR  unlicensed asset: $rel"; missing=1; }
  done < <(find assets -type f ! -name 'LICENSES.md' ! -path 'assets/gltf/*' 2>/dev/null)
  [ "$missing" -eq 0 ] || { echo "FAIL: assets missing LICENSES.md entries"; exit 1; }
fi

echo "==> 3/4  generator dry run"
if [ -f generators/build.py ]; then python generators/build.py --dry-run; fi

echo "==> 4/4  web renderer"
if [ -f renderers/web/package.json ]; then (cd renderers/web && npm run build --silent); fi

echo "PASS"
