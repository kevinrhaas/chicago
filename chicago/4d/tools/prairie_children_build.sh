#!/usr/bin/env bash
# Canonical remote authoring only. No branch write, scene placement or automatic acceptance.
set -euo pipefail
cd "$(dirname "$0")/.."
out=${1:?absolute fresh output directory required}
[[ "$out" = /* && ! -e "$out" ]] || { echo 'An absolute fresh output directory is required' >&2; exit 2; }
source generators/blender.pin
prairie_blender="${BLENDER_CACHE:-/opt/blender-dl}/$BLENDER_DIR/blender"
[[ -x "$prairie_blender" ]] || { echo 'Run the canonical fixture verification on the CI worker first' >&2; exit 2; }
mkdir -p "$out"
git rev-parse HEAD > "$out/source-sha.txt"
for role in child_boy_1904 child_girl_1904 child_toddler_1904 teen_boy_1904 teen_girl_1904; do
  dest="$out/$role"
  mkdir "$dest"
  export HUMAN_EXPORT_EVIDENCE_DIR="$dest/export-evidence"
  # Reuse the established child-body short2 normal readback bound (1812 children
  # dossier, section 4: the same boy body measures 0.0036919). The default adult
  # builder bound and all exported-geometry/animation gates remain unchanged.
  timeout --signal=TERM --kill-after=5s 600s "$prairie_blender" -b -noaudio --factory-startup --python-exit-code 1 \
    --python tools/human_teamster_blend.py -- --recipe "data/humans/recipes/$role.json" \
    --variant "$role" --liberty L-prairie-people-3548 --normal-tolerance 5e-3 --output "$dest/canonical.blend" \
    2>&1 | tee "$dest/build.log"
  timeout --signal=TERM --kill-after=5s 600s bash tools/human_export.sh \
    --master "$dest/canonical.blend" --output-dir "$dest/exports" \
    2>&1 | tee "$dest/export.log"
  python3 - "$role" "$dest" <<'AUDIT_CHILD' | tee "$dest/animation-times.log"
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from human_child_1812 import child_walk
from audit_human_animation_times import inspect_file
role, dest = sys.argv[1:]
recipe = json.loads(Path(f'data/humans/recipes/{role}.json').read_text())
body_bytes = Path(recipe['proof_variants'][0]['body_input']).read_bytes()
assert hashlib.sha256(body_bytes).hexdigest() == recipe['child_components']['body_sha256']
speed = child_walk(json.loads(body_bytes))['speed_m_s']
files = sorted((Path(dest)/'exports').glob('*.glb')) + sorted((Path(dest)/'exports/web').glob('*.glb'))
assert len(files) == 8, 'all four master and four web LODs must be audited'
results = [inspect_file(f, expected_speed_m_s=speed) for f in files]
for result in results:
    print(json.dumps({**result, 'expected_child_speed_m_s': speed}))
assert all(r['passed'] for r in results), 'child animation declaration failed'
AUDIT_CHILD
done
echo 'Canonical exports complete. Visual inspection and scene acceptance remain required.'
