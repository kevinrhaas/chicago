#!/usr/bin/env python3
"""Measure every published GLB the way the renderer measures it, and say which
buildings come out the wrong size.

This exists because the renderer's own smoke test only ever checked the TALLEST
building in the scene, so a scene with one correct structure and two hundred
broken ones passed it. This walks the glTF node tree itself — POSITION accessors
are required to carry min/max, so a bounding box needs no mesh decode and no
browser — and reports each structure against the footprint its record claims.

Two frames are computed for every structure node, because they are the two the
renderer has actually used:

  node   — geometry relative to the structure node (the historical rule)
  parent — geometry relative to the node's parent (the rule adopted to survive
           KHR_mesh_quantization, whose dequantisation rides on the node)

Under an uncompressed file the two agree. Where they disagree, the node carries
a transform, and exactly one of the two answers can be right.
"""
import json
import math
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FT = 0.3048


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError(f"{path}: not a GLB")
    off, js, bins = 12, None, {}
    idx = 0
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            bins[idx] = chunk
            idx += 1
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return js, bins


def mat_identity():
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def mat_mul(a, b):
    """Column-major 4x4, glTF convention: result = a * b."""
    out = [0.0] * 16
    for c in range(4):
        for r in range(4):
            out[c * 4 + r] = sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
    return out


def node_matrix(node):
    if "matrix" in node:
        return list(node["matrix"])
    t = node.get("translation", [0, 0, 0])
    r = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    x, y, z, w = r
    m = [
        (1 - 2 * (y * y + z * z)) * s[0], (2 * (x * y + z * w)) * s[0], (2 * (x * z - y * w)) * s[0], 0,
        (2 * (x * y - z * w)) * s[1], (1 - 2 * (x * x + z * z)) * s[1], (2 * (y * z + x * w)) * s[1], 0,
        (2 * (x * z + y * w)) * s[2], (2 * (y * z - x * w)) * s[2], (1 - 2 * (x * x + y * y)) * s[2], 0,
        t[0], t[1], t[2], 1,
    ]
    return m


def apply(m, p):
    x, y, z = p
    return (
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    )


# A normalized integer attribute stores value/MAX, not value. Reading the raw
# min/max and forgetting the divisor makes every quantised building measure in
# the hundreds of thousands of metres — which is a bug in the ruler, not in the
# town, and cost a diagnostic round the first time.
NORMALIZE_DIVISOR = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}


def mesh_box(js, mesh_index):
    """Local-space AABB of a mesh, from its POSITION accessor min/max."""
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for prim in js["meshes"][mesh_index].get("primitives", []):
        acc_i = prim.get("attributes", {}).get("POSITION")
        if acc_i is None:
            continue
        acc = js["accessors"][acc_i]
        amin, amax = acc.get("min"), acc.get("max")
        if not amin or not amax:
            continue
        div = NORMALIZE_DIVISOR.get(acc["componentType"], 1.0) if acc.get("normalized") else 1.0
        for k in range(3):
            lo[k] = min(lo[k], max(amin[k] / div, -1.0) if div != 1.0 else amin[k])
            hi[k] = max(hi[k], min(amax[k] / div, 1.0) if div != 1.0 else amax[k])
    if lo[0] is math.inf:
        return None
    return lo, hi


def corners(lo, hi):
    return [(lo[0] if i & 1 else hi[0],
             lo[1] if i & 2 else hi[1],
             lo[2] if i & 4 else hi[2]) for i in range(8)]


def collect(js, node_i, parent_m, out, depth=0):
    node = js["nodes"][node_i]
    m = mat_mul(parent_m, node_matrix(node))
    if "mesh" in node:
        box = mesh_box(js, node["mesh"])
        if box:
            out.append((m, box))
    for c in node.get("children", []):
        collect(js, c, m, out, depth + 1)


def find_structure_nodes(js):
    """Nodes carrying extras.structure_id, with their world matrix and parent's."""
    parent_of = {}
    for i, n in enumerate(js.get("nodes", [])):
        for c in n.get("children", []):
            parent_of[c] = i

    world = {}

    def walk(i, m):
        wm = mat_mul(m, node_matrix(js["nodes"][i]))
        world[i] = wm
        for c in js["nodes"][i].get("children", []):
            walk(c, wm)

    scene = js.get("scenes", [{}])[js.get("scene", 0)]
    for r in scene.get("nodes", []):
        walk(r, mat_identity())

    found = []
    for i, n in enumerate(js.get("nodes", [])):
        sid = (n.get("extras") or {}).get("structure_id")
        if sid:
            p = parent_of.get(i)
            found.append((sid, i, world[i], world[p] if p is not None else mat_identity()))
    return found, world


def invert(m):
    """General 4x4 inverse (these are affine, but keep it honest)."""
    a = [m[c * 4 + r] for r in range(4) for c in range(4)]  # row-major
    n = 4
    aug = [a[r * 4:r * 4 + 4] + [1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[piv][col]) < 1e-12:
            raise ValueError("singular")
        aug[col], aug[piv] = aug[piv], aug[col]
        pv = aug[col][col]
        aug[col] = [v / pv for v in aug[col]]
        for r in range(n):
            if r == col:
                continue
            f = aug[r][col]
            if f:
                aug[r] = [v - f * w for v, w in zip(aug[r], aug[col])]
    inv_rows = [row[4:] for row in aug]
    return [inv_rows[r][c] for c in range(4) for r in range(4)]  # back to col-major


def box_of(entries, to_frame):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for m, (blo, bhi) in entries:
        rel = mat_mul(to_frame, m)
        for p in corners(blo, bhi):
            q = apply(rel, p)
            for k in range(3):
                lo[k] = min(lo[k], q[k])
                hi[k] = max(hi[k], q[k])
    if lo[0] is math.inf:
        return None
    return lo, hi


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "assets/web"
    gdir = ROOT / which
    records = {}
    for p in sorted((ROOT / "data" / "structures").glob("*.json")):
        try:
            r = json.loads(p.read_text())
        except Exception:
            continue
        if r.get("structure_id"):
            records[r["structure_id"]] = r

    rows = []
    for glb in sorted(gdir.glob("*.glb")):
        try:
            js, _ = read_glb(glb)
        except Exception as e:
            rows.append((glb.name, None, f"unreadable: {e}"))
            continue
        nodes, world = find_structure_nodes(js)
        if not nodes:
            rows.append((glb.name, None, "no extras.structure_id"))
            continue
        for sid, ni, wm, pm in nodes:
            entries = []
            collect(js, ni, mat_identity(), entries)  # geometry in node-LOCAL frame
            if not entries:
                rows.append((glb.name, sid, "no meshes"))
                continue
            # frame "node": the historical rule — subtree relative to the node itself.
            b_node = box_of(entries, mat_identity())
            # frame "parent": what the renderer does today — the node's own transform
            # survives, because under quantization it IS the dequantisation.
            b_parent = box_of(entries, node_matrix(js["nodes"][ni]))
            rows.append((glb.name, sid, (b_node, b_parent, js)))
    return rows, records


def fmt(b):
    lo, hi = b
    return (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])


if __name__ == "__main__":
    rows, records = main()
    bad = []
    print(f"{'structure':44s} {'node-frame (m)':>22s} {'parent-frame (m)':>22s}")
    for name, sid, payload in rows:
        if not isinstance(payload, tuple):
            print(f"{(sid or name):44s} !! {payload}")
            bad.append((sid or name, payload))
            continue
        b_node, b_parent, js = payload
        dn = fmt(b_node)
        dp = fmt(b_parent)
        flag = ""
        # Every dimension of a standing 1835 structure lives between a privy and
        # a courthouse. Anything outside that is not a judgement call.
        w, d, h = sorted(dp)[0], sorted(dp)[1], dp[2] if len(dp) > 2 else 0
        if max(dp) > 60 or max(dp) < 1.0:
            flag = "  <-- OUT OF RANGE"
            bad.append((sid, dp))
        ratio = max(dn) / max(dp) if max(dp) else 0
        if abs(ratio - 1) > 0.01:
            flag += f"  frames differ x{ratio:.2f}"
        print(f"{sid:44s} {dn[0]:6.1f}x{dn[1]:6.1f}x{dn[2]:6.1f} "
              f"{dp[0]:6.1f}x{dp[1]:6.1f}x{dp[2]:6.1f}{flag}")
    print(f"\n{len(rows)} structures, {len(bad)} out of range")
