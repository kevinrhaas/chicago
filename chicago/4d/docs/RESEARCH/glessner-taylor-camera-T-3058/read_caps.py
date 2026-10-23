#!/usr/bin/env python3
"""T-3058: the built stacks' caps against their record boxes, through Taylor 2135's cameras.

T-2858 read each stack through the camera as its record box (the shaft's plan at its top
height) plus a correction carried from T-2221's render: what that render drew minus where
T-2221's camera put the box, taken to be the cap's overhang. This projects the committed GLB's
own vertices at each stack's top instead, so the cap is read, not carried. If the cap and the
box agree, the carried correction was the render picks' scatter, not an overhang, and the box
alone is the stack.

Needs the gitignored GLB: python3 tools/recover_glessner_v4.py --materialize

  python3 docs/RESEARCH/glessner-taylor-camera-T-3058/read_caps.py     write caps.json
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import glessner_prairie_front as G  # noqa: E402

GLB = ROOT / "assets/gltf/glessner_house__as_built_1887.glb"
OUT = HERE / "caps.json"
MARGIN = 0.3     # m around the box in plan: takes in the cap's overhang
DROP = 0.45      # m below the top: the cap course; deeper takes in the shaft's rock faces


def positions():
    b = GLB.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    off = 20 + n + 8
    out = []
    for prim in j["meshes"][0]["primitives"]:
        a = j["accessors"][prim["attributes"]["POSITION"]]
        v = j["bufferViews"][a["bufferView"]]
        start = off + v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 12)
        raw = np.frombuffer(b, np.uint8, count=stride * a["count"], offset=start).reshape(-1, stride)
        out.append(raw[:, :12].copy().view("<f4").reshape(-1, 3))
    p = np.concatenate(out).astype(float)
    return np.column_stack((p[:, 0], -p[:, 2], p[:, 1]))     # glTF y-up to the cameras' (x, y, z up)


def main():
    P = positions()
    cams = {"T-2221 (T-2857's render)": G.TAYLOR_BEFORE,
            "T-3058": json.loads((G.VIEWS / "taylor-2135-ne.json").read_text())}
    out = {"ticket": "T-3058", "not_a_reading": "a check of the built caps against the record boxes; it rules on no unit",
           "glb": str(GLB.relative_to(ROOT)), "cameras": {}}
    for label, cam in cams.items():
        e, B, f, c = np.array(cam["eye"]), np.array(cam["basis_right_up_forward"]), cam["focal_px"], np.array(cam["principal_px"])
        rows = {}
        for name, box in G.stacks().items():
            box = np.array(box)
            lo, hi = box.min(0), box.max(0)
            k = ((P[:, 0] > lo[0] - MARGIN) & (P[:, 0] < hi[0] + MARGIN) & (P[:, 1] > lo[1] - MARGIN)
                 & (P[:, 1] < hi[1] + MARGIN) & (P[:, 2] > hi[2] - DROP) & (P[:, 2] < hi[2] + 0.3))
            cap = G.silhouette(P[k], e, B, f, c)
            bx = G.silhouette(box, e, B, f, c)
            rows[name] = {"vertices": int(k.sum()), "cap_left_right_top_px": [round(float(v), 1) for v in cap],
                          "box_left_right_top_px": [round(float(v), 1) for v in bx],
                          "cap_minus_box_px": [round(float(a - b), 1) for a, b in zip(cap, bx)],
                          "photograph_px": list(G.T2857.STACKS[name][0])}
        out["cameras"][label] = rows
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for label, rows in out["cameras"].items():
        print(label)
        for name, r in rows.items():
            print(f"  {name:<7} cap {r['cap_left_right_top_px']} box {r['box_left_right_top_px']} "
                  f"cap-box {r['cap_minus_box_px']} photo {r['photograph_px']}")


if __name__ == "__main__":
    main()
