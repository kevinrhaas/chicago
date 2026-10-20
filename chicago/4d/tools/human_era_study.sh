#!/usr/bin/env bash
# Opt-in authoring artifacts only. Existing1835/fixture commands stay unchanged.
set -euo pipefail
cd "$(dirname "$0")/.."
ERA=""
LIBERTY=""
OUTPUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --era-study|--liberty|--output-dir)
      [ $# -ge 2 ] && [ -n "$2" ] && [[ "$2" != --* ]] || { echo "$1 requires a value" >&2; exit 2; }
      case "$1" in
        --era-study) ERA="$2" ;;
        --liberty) LIBERTY="$2" ;;
        --output-dir) OUTPUT="$2" ;;
      esac
      shift 2 ;;
    *) echo "Unknown era-study argument: $1" >&2; exit 2 ;;
  esac
done
[[ "$ERA" = 1812 || "$ERA" = 1904 || "$ERA" = both ]] || { echo "Explicit --era-study 1812|1904|both required" >&2; exit 2; }
[[ "$LIBERTY" =~ ^L[0-9]+$ ]] || { echo "Real integrator-supplied --liberty required" >&2; exit 2; }
[[ "$OUTPUT" = /* ]] && [ ! -e "$OUTPUT" ] || { echo "Absolute fresh --output-dir required" >&2; exit 2; }
source generators/blender.pin
STUDY_BIN="${BLENDER_CACHE:-/opt/blender-dl}/$BLENDER_DIR/blender"
[ -x "$STUDY_BIN" ] || { echo "Run the existing pinned fixture verification on the CI worker first; this caller does not install Blender" >&2; exit 2; }
eras=("$ERA")
[ "$ERA" = both ] && eras=(1812 1904)
for era in "${eras[@]}"; do
  python3 tools/human_era_study_blend.py --era-study "$era" --liberty "$LIBERTY" --check-source-only
done
mkdir "$OUTPUT"
for era in "${eras[@]}"; do
  directory="$OUTPUT/$era"
  mkdir "$directory"
  master="$directory/canonical.blend"
  export HUMAN_EXPORT_EVIDENCE_DIR="$directory/export-evidence"
  timeout --signal=TERM --kill-after=5s 600s "$STUDY_BIN" -b -noaudio --factory-startup --python-exit-code 1 \
    --python tools/human_era_study_blend.py -- --era-study "$era" --liberty "$LIBERTY" \
    --output "$master" --receipt "$directory/master-receipt.json" \
    --experimental-normal-probes --normal-probe-receipts "$directory/normal-probes" \
    2>&1 | tee "$directory/build.log"
  timeout --signal=TERM --kill-after=5s 600s bash tools/human_export.sh \
    --master "$master" --output-dir "$directory/exports" \
    2>&1 | tee "$directory/export.log"
  python3 tools/audit_human_animation_times.py "$directory"/exports/*.glb "$directory"/exports/web/*.glb \
    2>&1 | tee "$directory/animation-times.log"
done
echo "Era-study masters and gated export artifacts written to $OUTPUT; photographic, fit, source/published browser and scene acceptance remain open."
