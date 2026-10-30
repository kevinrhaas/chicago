#!/usr/bin/env python3
"""T-3096's acceptance: T-3080's read_slope.py and T-3095's read_ridge.py, unchanged, on the rebaked GLB.

Both scripts write their readings beside themselves. This runs them as they stand with only
their output folder pointed here, so T-3080's and T-3095's own readings stay the record of the
model they read. One camera is left out of read_slope's list, and only one: HABS photograph 1's
committed camera. Its counting field (T-3072's, picked on the print) now takes in the hidden
south slope behind the lowered ridge, because the reader keeps every roof vertex within 4 m of
the nearest depth and has no occlusion; its plane fit then comes out vertical (87.8 degrees)
and no vertex lies on its columns. It is not a measured-control fit, and T-3095's acceptance is
put to those: T-2758's two Cornell roof fits and three HABS 1 doorway fits, and the committed
Cornell camera besides.

Needs the gitignored GLB: python3 tools/recover_glessner_v4.py --materialize

  python3 docs/RESEARCH/glessner-stable-ridge-T-3096/read_rebuild.py   writes slope-readings.json, ridge-readings.json
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
for name in ("glessner-roof-module-T-3072", "glessner-roof-slope-camera-T-3080", "glessner-stable-ridge-T-3095"):
    sys.path.insert(0, str(RESEARCH / name))
import read_slope  # noqa: E402
import read_ridge  # noqa: E402

COURSE_IN = 5.0
ROLL_FOOT_M = 0.09   # the roll's foot under the tiled top (T-3095 section 1)


def main():
    read_slope.HERE = HERE
    read_slope.CAMERAS["habs-01-northwest"] = ("habs01", ["doorway", "doorway_eye_height", "doorway_lean"])
    read_slope.main()
    (HERE / "readings.json").rename(HERE / "slope-readings.json")
    with tempfile.TemporaryDirectory() as tmp:
        # read_ridge reads T-3080's readings beside its own folder; give it T-3095's tree
        # with this run's readings in place of nothing else.
        read_ridge.HERE = Path(tmp) / "ridge"
        read_ridge.HERE.mkdir()
        shutil.copytree(RESEARCH / "glessner-roof-slope-camera-T-3080", Path(tmp) / "glessner-roof-slope-camera-T-3080")
        shutil.copytree(RESEARCH / "glessner-roof-module-T-3072", Path(tmp) / "glessner-roof-module-T-3072")
        read_ridge.COUNTS = Path(tmp) / "glessner-roof-module-T-3072/readings.json"
        read_ridge.main()
        shutil.copy(read_ridge.HERE / "readings.json", HERE / "ridge-readings.json")
    slope = json.loads((HERE / "slope-readings.json").read_text())
    summary = []
    for view, rows in slope["views"].items():
        for row in rows:
            cols = row["columns"]
            summary.append({
                "view": view, "camera": row["camera"], "rms_px": row["rms_px_on_measured_controls"],
                "model_courses_at_5in": row["model_courses_at_5in"],
                # where the print's roll foot (its ridge edge) stands over the model's roll foot
                "print_over_model_roll_foot_m": [round(ROLL_FOOT_M - c["ridge_below_model_top_m"], 2) for c in cols],
                "print_eave_over_model_eave_m": [round(-c["eave_below_model_foot_m"], 2) for c in cols],
            })
    (HERE / "acceptance.json").write_text(json.dumps({"ticket": "T-3096", "rows": summary}, indent=1) + "\n")
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
