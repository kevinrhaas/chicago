#!/usr/bin/env python3
"""measure_fort_gates.py — is the fort's gate actually shut?

T-0095. `generators/archetypes/palisade.py` says of the gate it builds, in terms:

    The leaves are hung shut. A fort with its gates standing open makes a claim
    about the hour of the day; a fort with them shut makes a claim about a
    garrison that is there, and the garrison IS attested for 1835-07-01.

The garrison is attested and the leaves were not shut. Stand on the north bank at
`p4_0`'s own station and look at Fort Dearborn's north gate: there is a slot of
daylight straight through the wall between the two leaves, wide enough to see the
grass of the parade and a building beyond it. Both documented gates carried it,
and it was in the committed GLB — so it was in the bytes a visitor downloaded.

**The arithmetic, because it is small enough to state.** Each leaf was placed by
computing a midpoint and then spanning half a gate width either side of it:

    a = (cx + ux * (half * (0.0 if s < 0 else 1.0)) * 1.0, ...)
    z = (cx + ux * half * s, ...)
    mid = ((a + z) / 2)
    _beam(mid - ux * half / 2, mid + ux * half / 2, ...)

For the left leaf (`s = -1`) `a` is the gate CENTRE and `z` is the left jamb, so
`mid` lands halfway between them and the leaf comes out right. For the right leaf
(`s = +1`) the selector makes `a` the right jamb as well — `a` and `z` are the SAME
POINT — so `mid` lands ON the jamb and the leaf is built centred there. On Fort
Dearborn's 3.6 m gateway that put the right leaf at 27.40–29.20 m where it belonged
at 26.50–28.30: **0.90 m of the gateway left open, and 0.50 m of leaf lying across
the picket curtain outside its own jamb.** A quarter of the gate.

The two halves failed differently and that is the whole reason it survived: the
left leaf is correct, so the gate looked like a gate. Only the right one was wrong,
and a gate with one good leaf reads as a gate with a shadow in it until you stand
close enough to see the ground through it.

WHAT THIS MEASURES, and why it reads the GLB rather than the code
-----------------------------------------------------------------
The fix is four lines in one archetype and a re-derivation of the same four lines
would prove nothing — the bug WAS the derivation. So this reads the committed
mesh: the bytes the renderer loads, which is the only artefact that can be wrong
in the way this was wrong.

For each side the record documents a gate on, it takes every triangle of the leaf
material lying in that wall's plane, projects it onto the wall's own along-axis,
and unions the projections. The union is what the shut gate covers. Then:

  1. **every documented gate side carries leaves at all** — a gate with no leaf is
     a hole, and the record's own note says these are hung shut;
  2. **the leaves cover the whole opening** — no gap wider than `TOL_M`;
  3. **no leaf reaches past the opening into the curtain** — the same tolerance,
     because a leaf overrunning its jamb is the other half of this same fault and
     a check that only looked for daylight would have called the overrun fine.

The opening itself is not read off the mesh. It comes from the RECORD — the
footprint polygon's bounding box and `form.gate_width_m` — so this asks whether the
geometry matches the data, which is the question, rather than whether the geometry
is self-consistent, which it always was.

Only the uncompressed master is read. The compressed web derivative is held to the
master by `tools/measure_web_derivatives.py`, which is its own gate; decoding
meshopt here to ask the same question twice would duplicate that one badly.

    tools/measure_fort_gates.py               the reading
    tools/measure_fort_gates.py --gate        exit 1 on any of the three
    tools/measure_fort_gates.py --self-test   break each assertion, in memory
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "data" / "structures" / "fort_dearborn_palisade.json"
GLB = ROOT / "assets" / "gltf" / "fort_dearborn_palisade__picket_1816.glb"

# The leaves are the only thing built from the `dark` material — see
# `palisade.py` M_DARK. Named rather than indexed because a primitive's order is
# not part of the glTF contract.
LEAF_MATERIAL = "dark"

# A ten-millimetre tolerance. Not a comfort margin: the fault this exists to catch
# was 900 mm, and the honest closure of two butted leaves is exactly zero. Ten
# millimetres is float noise on a 53 m enclosure and nothing else.
TOL_M = 0.010


class ReadError(RuntimeError):
    pass


# ----------------------------------------------------------------- glTF reading

def _load_glb(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if raw[:4] != b"glTF":
        raise ReadError(f"{path.name} is not a GLB")
    off, gj, bin_ = 12, None, b""
    while off < len(raw):
        clen, ctype = struct.unpack("<II", raw[off:off + 8])
        chunk = raw[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            gj = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bin_ = chunk
        off += 8 + clen
    if gj is None:
        raise ReadError(f"{path.name} has no JSON chunk")
    if gj.get("extensionsUsed"):
        raise ReadError(f"{path.name} uses {gj['extensionsUsed']} — this reader is for the "
                        f"uncompressed master, not a web derivative")
    return gj, bin_


_COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
              5125: ("I", 4), 5126: ("f", 4)}
_NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def _accessor(gj: dict, bin_: bytes, index: int) -> list:
    a = gj["accessors"][index]
    fmt, size = _COMPONENT[a["componentType"]]
    n = _NCOMP[a["type"]]
    bv = gj["bufferViews"][a["bufferView"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride") or size * n
    out = []
    for i in range(a["count"]):
        o = start + i * stride
        vals = struct.unpack_from("<" + fmt * n, bin_, o)
        out.append(vals[0] if n == 1 else vals)
    return out


def leaf_triangles(glb: Path = GLB) -> list:
    """Every triangle of the gate-leaf material, in the mesh's own local metres.

    glTF is Y-up and the exporter maps Blender +Y (the archetype's local +y, which
    docs/GLB-CONTRACT.md defines as north) onto glTF -Z. This puts both back, so
    everything below is in the same plan coordinates the footprint polygon uses.
    """
    gj, bin_ = _load_glb(glb)
    names = [m.get("name") for m in gj.get("materials", [])]
    tris = []
    for mesh in gj.get("meshes", []):
        for prim in mesh.get("primitives", []):
            mat = prim.get("material")
            if mat is None or names[mat] != LEAF_MATERIAL:
                continue
            if prim.get("mode", 4) != 4:
                raise ReadError(f"leaf primitive is mode {prim.get('mode')}, not triangles")
            pos = _accessor(gj, bin_, prim["attributes"]["POSITION"])
            idx = _accessor(gj, bin_, prim["indices"]) if "indices" in prim \
                else list(range(len(pos)))
            for i in range(0, len(idx) - 2, 3):
                tris.append([(pos[j][0], -pos[j][2], pos[j][1]) for j in idx[i:i + 3]])
    return tris


# --------------------------------------------------------------- the geometry

def _union(spans: list) -> list:
    """Merged, sorted intervals."""
    out = []
    for a, z in sorted(spans):
        if out and a <= out[-1][1] + 1e-9:
            out[-1][1] = max(out[-1][1], z)
        else:
            out.append([a, z])
    return [(a, z) for a, z in out]


def _subtract(interval: tuple, covered: list) -> list:
    """`interval` with every covered span removed."""
    keep = [list(interval)]
    for c0, c1 in covered:
        nxt = []
        for k0, k1 in keep:
            if c1 <= k0 or c0 >= k1:
                nxt.append([k0, k1])
                continue
            if c0 > k0:
                nxt.append([k0, min(c0, k1)])
            if c1 < k1:
                nxt.append([max(c1, k0), k1])
        keep = nxt
    return [(a, z) for a, z in keep if z - a > 1e-9]


def gate_geometry(record: dict | None = None, tris: list | None = None) -> dict:
    """What the record asks of each gate, and what the mesh covers there."""
    rec = record if record is not None else json.loads(RECORD.read_text(encoding="utf-8"))
    phase = rec["phases"][0]
    form = phase["form"]
    poly = phase["footprint"]["polygon"]
    w = max(p[0] for p in poly) - min(p[0] for p in poly)
    d = max(p[1] for p in poly) - min(p[1] for p in poly)
    sides = form["gate_sides"]["value"]
    gw = float(form["gate_width_m"]["value"])
    tris = leaf_triangles() if tris is None else tris

    # (the wall's fixed coordinate, which plan axis runs along it, its length)
    wall = {"s": (1, 0.0, 0, w), "n": (1, d, 0, w),
            "w": (0, 0.0, 1, d), "e": (0, w, 1, d)}

    out = {"enclosure": [round(w, 3), round(d, 3)], "gate_width_m": gw,
           "tolerance_m": TOL_M, "gates": {}}
    for side in sides:
        fixed_axis, fixed, along_axis, run = wall[side]
        lo, hi = run / 2.0 - gw / 2.0, run / 2.0 + gw / 2.0
        spans = []
        for tri in tris:
            # a triangle belongs to this wall if all three corners sit in its
            # plane; the leaves are 110 mm thick, so half a metre is generous
            # and still cannot reach the opposite wall 53 m away.
            if any(abs(v[fixed_axis] - fixed) > 0.5 for v in tri):
                continue
            a = [v[along_axis] for v in tri]
            spans.append([min(a), max(a)])
        covered = _union(spans)
        out["gates"][side] = {
            "opening": [round(lo, 3), round(hi, 3)],
            "covered": [[round(a, 3), round(z, 3)] for a, z in covered],
            "gaps": [[round(a, 3), round(z, 3)] for a, z in _subtract((lo, hi), covered)],
            "overrun": [[round(a, 3), round(z, 3)]
                        for a, z in _subtract((min([c[0] for c in covered], default=lo),
                                               max([c[1] for c in covered], default=hi)),
                                              [(lo, hi)])],
            "triangles": sum(1 for s in spans),
        }
    return out


def findings(result: dict) -> list:
    """The three assertions, as a list of failures."""
    bad = []
    tol = result["tolerance_m"]
    for side, g in sorted(result["gates"].items()):
        if not g["covered"]:
            bad.append(f"the {side} gate carries no leaf geometry at all — the record "
                       f"documents a gate there and the archetype hangs it shut")
            continue
        for a, z in g["gaps"]:
            if z - a > tol:
                bad.append(f"the {side} gate stands {z - a:.3f} m OPEN between {a:.2f} and "
                           f"{z:.2f} m along the wall — daylight through a gate the record "
                           f"says is shut")
        for a, z in g["overrun"]:
            if z - a > tol:
                bad.append(f"the {side} gate's leaf runs {z - a:.3f} m past its own jamb "
                           f"({a:.2f} to {z:.2f} m), lying across the picket curtain")
    return bad


# ----------------------------------------------------------------- self-test

def self_test() -> int:
    """Break each assertion in memory and confirm it is noticed."""
    ok = True

    def case(label: str, result: dict, expect: str) -> None:
        nonlocal ok
        found = findings(result)
        hit = any(expect in f for f in found)
        print(f"   {'ok  ' if hit else 'FAIL'}  {label}")
        if not hit:
            print(f"          expected a finding containing {expect!r}, got {found}")
            ok = False

    good = gate_geometry()
    if findings(good):
        print("   FAIL  the committed mesh does not pass, so the self-test has no "
              "clean starting point")
        for f in findings(good):
            print(f"          {f}")
        return 1
    print("   ok    the committed mesh passes, so a break below is this test's own doing")

    missing = json.loads(json.dumps(good))
    missing["gates"]["n"].update(covered=[], gaps=[], overrun=[])
    case("a gate with no leaves at all is caught", missing, "no leaf geometry")

    ajar = json.loads(json.dumps(good))
    lo, hi = ajar["gates"]["n"]["opening"]
    mid = (lo + hi) / 2.0
    ajar["gates"]["n"]["gaps"] = [[mid, mid + 0.9]]
    case("the 0.90 m slot this file was written for is caught", ajar, "stands 0.900 m OPEN")

    hair = json.loads(json.dumps(good))
    lo, hi = hair["gates"]["s"]["opening"]
    hair["gates"]["s"]["gaps"] = [[hi - 0.03, hi]]
    case("a 30 mm gap — three times the tolerance — is caught", hair, "0.030 m OPEN")

    proud = json.loads(json.dumps(good))
    lo, hi = proud["gates"]["s"]["opening"]
    proud["gates"]["s"]["overrun"] = [[hi, hi + 0.5]]
    case("a leaf lying across the curtain is caught", proud, "past its own jamb")

    snug = json.loads(json.dumps(good))
    lo, hi = snug["gates"]["n"]["opening"]
    snug["gates"]["n"]["gaps"] = [[hi - TOL_M * 0.5, hi]]
    found = findings(snug)
    inside = not found
    print(f"   {'ok  ' if inside else 'FAIL'}  a gap inside the tolerance is NOT called a fault")
    ok = ok and inside

    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# --------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true", help="exit 1 on any finding")
    ap.add_argument("--self-test", action="store_true", help="break each assertion")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    try:
        result = gate_geometry()
    except (ReadError, OSError, KeyError) as e:
        print(f"   FAIL cannot read the fort's gates: {e}")
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    bad = findings(result)
    if not args.quiet or bad:
        w, d = result["enclosure"]
        print(f"   Fort Dearborn's stockade, {w:.0f} x {d:.0f} m, "
              f"{len(result['gates'])} documented gate(s), "
              f"{result['gate_width_m']:.2f} m wide")
        for side, g in sorted(result["gates"].items()):
            lo, hi = g["opening"]
            cov = ", ".join(f"{a:.2f}-{z:.2f}" for a, z in g["covered"]) or "nothing"
            print(f"     {side}: opening {lo:.2f}-{hi:.2f} m   leaves cover {cov}"
                  f"   ({g['triangles']} triangles)")
    for f in bad:
        print(f"   FAIL {f}")
    if not bad and not args.quiet:
        print("   every documented gate is shut, leaf to leaf, jamb to jamb")
    return 1 if (bad and args.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
