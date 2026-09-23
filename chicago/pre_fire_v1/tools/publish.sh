#!/usr/bin/env bash
# Copy the parts of pre_fire_v1 the published viewer needs into site/chicago/pre-fire/.
#
# The mirror used to be a hand copy with no script behind it, which is how it
# came to hold 14 map images to the source's 15 for four months (T-0801). What
# ships is: the viewer, the map CSVs, every map image map_references.csv
# actually names, and the media the records link to. Nothing else — the CSVs
# under data/, the docs and these tools are research inputs, not site payload.
#
#   tools/publish.sh           copy
#   tools/publish.sh --check   fail if the mirror differs from a fresh copy
#
# site/chicago/pre-fire/index.html is the mirror's own bare-path redirect and
# has no counterpart in the source, so it is left alone either way.
#
# Run from the pre_fire_v1 directory.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$(cd "$SRC/../.." && pwd)/site/chicago/pre-fire"
CHECK=${1:-}

[ -d "$DEST" ] || { echo "no mirror at $DEST" >&2; exit 1; }

# The images the viewer can actually show, read off the CSV rather than globbed:
# maps/images also holds 1834-wright-map-lg.jpg, a byte-identical duplicate of
# the sheet, and shipping it would put 4.8 MiB in the tree twice.
mapfile -t IMAGES < <(cd "$SRC" && python3 -c '
import csv, sys
for r in csv.DictReader(open("maps/map_references.csv")):
    if r["local_image_path"]: print(r["local_image_path"])
' | sort -u)

copy() {  # copy <target-root>
  local out=$1
  mkdir -p "$out/viewer" "$out/maps/images" "$out/media"
  cp "$SRC"/viewer/* "$out/viewer/"
  cp "$SRC"/maps/*.csv "$out/maps/"
  for img in "${IMAGES[@]}"; do cp "$SRC/$img" "$out/maps/images/"; done
  cp -R "$SRC"/media/. "$out/media/"
}

if [ "$CHECK" = "--check" ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  copy "$tmp"
  # Compare against the mirror minus its own index.html, which the source has no
  # copy of. diff's own exit status is useless here because that one line always
  # trips it, and the status of the pipeline is not the status of the filter, so
  # the answer is whether anything SURVIVES the filter. `|| true` keeps diff's
  # exit 1 from killing the script under `set -e`.
  drift=$(diff -r --brief "$tmp" "$DEST" 2>&1 | grep -v "^Only in $DEST: index\.html$" || true)
  if [ -n "$drift" ]; then
    echo "$drift"
    echo "STALE: site/chicago/pre-fire differs from the source. Run tools/publish.sh." >&2
    exit 1
  fi
  echo "site/chicago/pre-fire is current"
else
  copy "$DEST"
  echo "published ${#IMAGES[@]} map images + viewer + media to site/chicago/pre-fire"
fi
