#!/usr/bin/env python3
"""Hold `frame_tavern_params.front_wall` to the builder it copies (T-3359).

The owner, 2026-11-03, had the 1835 hung signs fixed flat on their fronts, and
fourteen of them are on frame taverns, whose front elevation nothing could read
without Blender. `generators/archetypes/frame_tavern_params.front_wall` now states the
frontage scheme's sash, door, shutter and frontispiece rectangles so
`tools/generate_business_signboards.py` can stand a board clear of them — but it
states them as COPIES of `frame_tavern.py`'s literals, because the builder imports
Blender and the commit gate has none. A copy drifts the day somebody moves a sash in
the builder and not here, and the board it was keeping off that sash lands on it.

So this reads the builder's SOURCE, finds each literal the reader copies in the line
that draws it, and fails naming the one that moved. `--self-test` proves the check
can fail: it re-runs it against a builder source with one sash moved.

  python3 tools/check_tavern_front_reader.py [--self-test]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
from archetypes import frame_tavern_params as P  # noqa: E402
from common import openings  # noqa: E402

BUILDER = ROOT / "generators" / "archetypes" / "frame_tavern.py"


def _body(src: str, name: str) -> str:
    m = re.search(rf"^def {name}\(.*?(?=^def |\Z)", src, re.S | re.M)
    if not m:
        raise SystemExit(f"FAIL frame_tavern.py has no {name}() — the reader copies it")
    return m.group(0)


def check(src: str) -> list[str]:
    fen = _body(src, "_fenestration")
    fp = _body(src, "_frontispiece")
    pfe = _body(src, "_pictured_front_entrance")
    want = [
        ("_fenestration", fen, f"win_w, win_h, depth = {P.TAVERN_WIN_W_M}, "
                               f"{P.TAVERN_WIN_H_M}", "the sash size"),
        ("_fenestration", fen, f"story_h * {P.TAVERN_SILL_FRACTION:.2f}",
         "the sill at a share of the storey"),
        ("_fenestration", fen, f"else {P.TAVERN_GROUND_BAYS}", "the ground bays"),
        ("_fenestration", fen, "i == bays // 2", "the entrance in the centre bay"),
        ("_fenestration", fen, f"cx - {P.TAVERN_DOOR_HALF_W_M:.1f}, cx + "
                               f"{P.TAVERN_DOOR_HALF_W_M:.1f}, 0.0, "
                               f"{P.TAVERN_DOOR_H_M:.1f}", "the door"),
        ("_fenestration", fen, f"sash_w * {P.TAVERN_SHUTTER_SHARE}", "the shutter leaf"),
        ("_fenestration", fen, "sash_w / 2 + openings.CASING_W_M + 0.01",
         "the leaf's hinge line"),
        ("_fenestration", fen, 'params.front_lower_sash if story == 0 and sgn > 0',
         "the pictured lower sash, ground front only"),
        ("_fenestration", fen, 'sash["sill_m"] if sash else z0', "the pictured sash's sill"),
        ("_pictured_front_entrance", pfe, 'half = g["case_width_m"] / 2',
         "the pictured entrance case's width"),
        ("_pictured_front_entrance", pfe, 'outer = g["jamb_outer_width_m"] / 2',
         "the pictured entrance jambs"),
        ("_pictured_front_entrance", pfe, 'crown = g["cornice_top_m"]',
         "the pictured entrance's cornice head"),
        ("_frontispiece", fp, f"cx - {P.TAVERN_FRONTISPIECE_HALF_W_M:.2f}",
         "the frontispiece crown's width"),
        ("_frontispiece", fp, f"{P.TAVERN_FRONTISPIECE_TOP_M:.2f}",
         "the frontispiece crown's head"),
    ]
    bad = []
    for fn, body, lit, what in want:
        if lit not in body:
            bad.append(f"{what}: frame_tavern.{fn} no longer carries `{lit}`, which "
                       "frame_tavern_params.front_wall copies — move both together")
    if abs(P.TAVERN_CASING_W_M - openings.CASING_W_M) > 1e-9:
        bad.append(f"the casing: common/openings.CASING_W_M is {openings.CASING_W_M}, "
                   f"the reader copies {P.TAVERN_CASING_W_M}")
    return bad


def main() -> int:
    src = BUILDER.read_text(encoding="utf-8")
    if "--self-test" in sys.argv:
        broken = src.replace("win_w, win_h, depth = 0.85, 1.35",
                             "win_w, win_h, depth = 0.95, 1.35")
        if broken == src:
            print("FAIL self-test: could not find the sash literal to move")
            return 1
        got = check(broken)
        if not got:
            print("FAIL self-test: a moved sash went unnoticed")
            return 1
        print(f"self-test | caught: {got[0]}")
        print("ok self-test: a sash moved in the builder alone is refused")
        return 0
    bad = check(src)
    for b in bad:
        print("FAIL", b)
    if bad:
        return 1
    print("ok frame_tavern_params.front_wall matches frame_tavern.py's frontage "
          "scheme literals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
