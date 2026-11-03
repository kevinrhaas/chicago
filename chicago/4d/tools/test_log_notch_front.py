#!/usr/bin/env python3
"""T-3268: a log front's mid-wall corner notches are on the front wall's reading, and
no flat board is hung across them.

Where a log_dwelling's END addition meets its core, the core's notched log ends (and
the addition's, where its lower storey is log) stand proud of the front in the middle
of the wall. `log_dwelling_params.front_wall` names them `log_notch`, so the signboard
generator keeps a board off them as it keeps one off a window. Before that, the T-2381
Miller House front (a 6 m log core beside a 9 m two-storey range) had its wall board
hung across the junction, and dev's desktop smoke part 1 found 4 of its 35 lettering
rays behind the log heads (0.170 m in front of the board's face).

Three things are held here, all without Blender:

  1. the params module's copy of the notch figures equals `common/logwork.py`'s, the
     module that lays the notches (read from its source: it imports bpy);
  2. Miller House's front wall names the notch at the junction, and it is not a hole;
  3. every committed flat board on a log_dwelling front clears every `log_notch` on
     that wall by the generator's own blank-face margin.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import facade_openings  # noqa: E402
from archetypes import log_dwelling_params as ldp  # noqa: E402

FAILS: list[str] = []


def check(ok: bool, what: str) -> None:
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILS.append(what)


def logwork_constants() -> dict:
    tree = ast.parse((ROOT / "generators" / "common" / "logwork.py").read_text())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant):
            out[node.targets[0].id] = node.value.value
    return out


def main() -> int:
    lw = logwork_constants()
    check(lw.get("NOTCH_D") == ldp.NOTCH_REACH_M,
          f"NOTCH_REACH_M {ldp.NOTCH_REACH_M} is logwork's NOTCH_D {lw.get('NOTCH_D')}")
    check(lw.get("NOTCH_OUT") == ldp.NOTCH_OUT_M,
          f"NOTCH_OUT_M {ldp.NOTCH_OUT_M} is logwork's NOTCH_OUT {lw.get('NOTCH_OUT')}")
    check("log_notch" not in facade_openings.HOLE_KINDS, "log_notch is not a hole kind")

    import generate_business_signboards as gbs  # noqa: E402,PLC0415
    wall = gbs._front_wall("miller_house")
    notches = [o for o in (wall or {}).get("openings", []) if o["kind"] == "log_notch"]
    check(wall is not None and len(notches) == 1,
          f"Miller House's front names one log_notch ({len(notches)} found)")
    if notches:
        n = notches[0]
        check(n["u0"] < 6.0 < n["u1"] and n["z1"] >= 2.6 - 1e-9,
              f"it straddles the core/range junction at u 6.0 up the log storey "
              f"(u {n['u0']:.2f}-{n['u1']:.2f}, z to {n['z1']:.2f})")

    rec = json.loads((ROOT / "data" / "signage" / "town_business_signboards.json").read_text())
    flat = 0
    for sg in rec["signs"]:
        fit = sg.get("opening_fit") or {}
        span = fit.get("board_span_local_m")
        if sg.get("mounting") not in ("wall_board", "facade_painted") or not span:
            continue
        for o in fit.get("openings", []):
            if o["kind"] != "log_notch":
                continue
            flat += 1
            clear = min(abs(span[0] - o["u1"]), abs(o["u0"] - span[1])) \
                if (span[1] <= o["u0"] or span[0] >= o["u1"]) else -1.0
            check(clear >= gbs.SIGN_CLEAR_M - 1e-6,
                  f"{sg['structure_id']}: board u {span[0]}-{span[1]} clears the log notch "
                  f"u {o['u0']}-{o['u1']} by {clear:.2f} m (needs {gbs.SIGN_CLEAR_M})")
    check(flat >= 1, f"{flat} flat board(s) read against a log notch")
    print(f"{'PASS' if not FAILS else 'FAIL'}: log notch front ({len(FAILS)} failure(s))")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
