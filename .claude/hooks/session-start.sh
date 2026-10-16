#!/bin/bash
# Cloud sessions only: install the Python packages 4D Chicago's gate reads with,
# so `chicago/4d/tools/check.sh` does not go red for a missing module (scipy was
# missing on 2026-10-16, T-2552). The list is CI's own install line — keep it in
# step with `.github/workflows/chicago-4d-check.yml` (see AGENTS.md, "Both gates";
# tools/check_gate_readers.py asserts the raster readers among them).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PACKAGES=(jsonschema pyproj openpyxl pypdf numpy scipy Pillow)
MODULES=(jsonschema pyproj openpyxl pypdf numpy scipy PIL)

# Idempotent: skip pip entirely when every module already imports.
missing=0
for m in "${MODULES[@]}"; do
  python3 -c "import $m" 2>/dev/null || { missing=1; break; }
done
if [ "$missing" = 0 ]; then
  exit 0
fi

python3 -m pip install --quiet --disable-pip-version-check --root-user-action=ignore "${PACKAGES[@]}"
