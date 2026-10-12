#!/usr/bin/env python3
"""The K04 roof library holds to its data: every map a whole number of its own slates (T-2292).

    python3 tools/check_roof_library.py --check       refuse a drift; print the table
    python3 tools/check_roof_library.py --self-test   break each rule on a copy and watch it fail

WHY. `data/components/prairie_1904/k04_roofs.json` sizes every slate, tile, pan and
sheet, and `assets/textures/prairie_1904_roofs/` draws them. A K01 roof maps
TEXCOORD_0 = surface metres / tile_m (k01_contract.json `scale_uv`), so the whole
promise that a slate lands at its true size rests on one equality per fabric: the
tile is `columns x width` along the eave and `courses x exposure` up the slope. A
hand-edited tile_m, or a format changed in the data and not regenerated, scales every
slate on every roof that wears it, and nothing on screen says so — the
"oversized tiles" the K04 acceptance names. This holds:

  1. REGISTRATION. tile_m = columns x unit width and courses x exposure, to 0.1 mm.
  2. THE DOUBLE-LAP RULE. A slate's or tile's exposure = (length - headlap) / 2.
  3. A BROKEN JOINT WRAPS. Half-offset courses need an even number of courses, and
     staggered cross seams an even number of pans, or the tile's top edge meets its
     bottom edge out of bond and the seam shows on every roof.
  4. THE STARTING RANGE. A slate is 0.20-0.30 m wide and 0.15-0.25 m to the weather
     (RECONSTRUCTION-RULES.md § Starting ranges: Slate courses), so no fabric is a
     scaled-up slate passing for a format.
  5. THE MAP IS THE DATA'S. Each material.json repeats its fabric's tile_m and module
     exactly, the manifest lists exactly the fabrics, and every slot names a fabric.
  6. PROVENANCE. A fabric that is not `reconstructed` cites sources that resolve in
     data/sources/; a `documented_only` fabric names, for every roof it may go on, a
     source that resolves and whose rights let an asset be derived from it (AGENTS.md
     rule 6: a `check_required` source may be cited in text, never built from).
  7. SEAMLESS. Across each map's wrap edge (last column to first, last row to first)
     the step is no larger than its neighbouring steps inside the image.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k04_roofs.json"
LIB = ROOT / "assets" / "textures" / "prairie_1904_roofs"
SOURCES = ROOT / "data" / "sources"
TOL = 1e-4
SLATE_WIDTH = (0.20, 0.30)
SLATE_EXPOSURE = (0.15, 0.25)
SEAM_RATIO = 2.5
MAPS = ("basecolor.png", "normal_gl.png", "roughness.png", "orm.png",
        "basecolor_web.jpg", "normal_gl_web.jpg", "orm_web.jpg")
BARRED_RIGHTS = ("check_required", "restricted")


def unit_size(m):
    """(along the eave, up the slope) of one unit, in metres."""
    if "slate_width_m" in m:
        return m["slate_width_m"], m["exposure_m"]
    if "pan_width_m" in m:
        return m["pan_width_m"], m["cross_seam_m"]
    return m["sheet_u_m"], m["sheet_v_m"]


def seam_ratio(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    worst = 0.
    for axis in (0, 1):
        inner = np.abs(np.diff(a, axis=axis)).mean()
        first = np.take(a, 0, axis=axis)
        last = np.take(a, -1, axis=axis)
        wrap = np.abs(first - last).mean()
        # Half an 8-bit level: a near-flat map (a plain sheet's roughness) steps by
        # less than one level everywhere, and a ratio of two such steps is noise.
        worst = max(worst, wrap / max(float(inner), .5))
    return worst


def audit(data, materials, manifest, sources, seams):
    """Every refusal, as a list of strings. `materials` maps id -> material.json or None."""
    bad = []
    fabrics = {f["id"]: f for f in data["fabrics"]}
    for fid, f in fabrics.items():
        m, tile = f["module"], f["tile_m"]
        uw, uv = unit_size(m)
        if abs(m["columns"] * uw - tile[0]) > TOL or abs(m["courses"] * uv - tile[1]) > TOL:
            bad.append(f"{fid}: tile_m {tile} is not {m['columns']} x {uw} by {m['courses']} x {uv} "
                       f"— every slate on a roof wearing it would be scaled")
        if f["kind"] in ("slate", "tile"):
            want = (m["slate_length_m"] - m["headlap_m"]) / 2
            if abs(want - m["exposure_m"]) > TOL:
                bad.append(f"{fid}: exposure {m['exposure_m']} breaks the double-lap rule "
                           f"((length - headlap) / 2 = {want:.4f})")
        if m.get("bond") == "broken_half" and m["courses"] % 2:
            bad.append(f"{fid}: {m['courses']} half-offset courses do not wrap — the tile's top "
                       f"meets its bottom out of bond")
        if m.get("cross_seam_stagger") and m["columns"] % 2:
            bad.append(f"{fid}: {m['columns']} pans with staggered cross seams do not wrap")
        if f["kind"] == "slate":
            if not SLATE_WIDTH[0] <= m["slate_width_m"] <= SLATE_WIDTH[1] \
                    or not SLATE_EXPOSURE[0] <= m["exposure_m"] <= SLATE_EXPOSURE[1]:
                bad.append(f"{fid}: a {m['slate_width_m']} m slate at {m['exposure_m']} m to the weather "
                           f"is outside the starting range {SLATE_WIDTH} x {SLATE_EXPOSURE}")
        mat = materials.get(fid)
        if mat is None:
            bad.append(f"{fid}: no material.json under assets/textures/prairie_1904_roofs/{fid}/")
        elif mat.get("tile_m") != tile or mat.get("module") != m:
            bad.append(f"{fid}: material.json's tile or module is not the data file's — regenerate")
        if f["confidence"] != "reconstructed":
            cited = f.get("sources") or []
            if not cited:
                bad.append(f"{fid}: {f['confidence']} with no sources")
            for s in cited:
                if s not in sources:
                    bad.append(f"{fid}: source {s} does not resolve in data/sources/")
    listed = [x["id"] for x in manifest.get("materials", [])]
    if sorted(listed) != sorted(fabrics):
        bad.append(f"manifest lists {sorted(listed)}, the data file {sorted(fabrics)}")
    for slot, ids in data["slots"].items():
        if slot.startswith("_"):
            continue
        for fid in ids:
            if fid not in fabrics:
                bad.append(f"slot {slot} names {fid}, which is no fabric")
    for r in data.get("restrictions", []):
        if r["fabric"] not in fabrics:
            bad.append(f"restriction on {r['fabric']}, which is no fabric")
        if r["rule"] == "documented_only":
            if not r.get("documented_on"):
                bad.append(f"{r['fabric']}: documented_only, and documented on nothing")
            for d in r.get("documented_on", []):
                s = sources.get(d.get("source_id"))
                if s is None:
                    bad.append(f"{r['fabric']} on {d.get('structure_id')}: source "
                               f"{d.get('source_id')} does not resolve")
                elif s.get("rights_status") in BARRED_RIGHTS:
                    bad.append(f"{r['fabric']} on {d.get('structure_id')}: {d['source_id']} is "
                               f"{s['rights_status']} — cite it, never build from it")
    for name, ratio in seams.items():
        if ratio > SEAM_RATIO:
            bad.append(f"{name}: the wrap edge steps {ratio:.2f}x its neighbours — the tile shows a seam")
    return bad


def load_all():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    materials, seams, missing = {}, {}, []
    for f in data["fabrics"]:
        p = LIB / f["id"] / "material.json"
        materials[f["id"]] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        for suffix in MAPS:
            img = LIB / f["id"] / f"{f['id']}_{suffix}"
            if not img.exists():
                missing.append(f"{f['id']}: {img.name} is missing")
            elif suffix.endswith(".png"):
                seams[img.name] = seam_ratio(img)
    mp = LIB / "manifest.json"
    manifest = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
    sources = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in SOURCES.glob("*.json")}
    return data, materials, manifest, sources, seams, missing


def check() -> int:
    data, materials, manifest, sources, seams, missing = load_all()
    bad = missing + audit(data, materials, manifest, sources, seams)
    for f in data["fabrics"]:
        uw, uv = unit_size(f["module"])
        worst = max(v for k, v in seams.items() if k.startswith(f["id"] + "_"))
        print(f"   {f['id']:28s} {f['module']['columns']:>2} x {uw:.4f}  {f['module']['courses']:>2} x "
              f"{uv:.4f}  tile {f['tile_m'][0]:.4f} x {f['tile_m'][1]:.4f} m  wrap {worst:.2f}")
    for b in bad:
        print(f"   FAIL {b}")
    if bad:
        print(f"check_roof_library: {len(bad)} refusal(s)")
        return 1
    print(f"OK: {len(data['fabrics'])} K04 fabrics register to their data, wrap seamlessly and cite what they rest on")
    return 0


def self_test() -> int:
    data, materials, manifest, sources, seams, missing = load_all()
    if missing or audit(data, materials, manifest, sources, seams):
        print("   self-test | the committed library is not clean, so breaking it proves nothing")
        return 1
    pa = next(i for i, f in enumerate(data["fabrics"]) if f["id"] == "slate_pennsylvania")
    tile = next(i for i, f in enumerate(data["fabrics"]) if f["kind"] == "tile")

    def mutate(fn):
        d, mats, man, src, sm = (copy.deepcopy(x) for x in (data, materials, manifest, sources, seams))
        fn(d, mats, man, src, sm)
        return audit(d, mats, man, src, sm)

    def scaled(d, mats, *_):
        d["fabrics"][pa]["tile_m"] = [2.5, 1.7272]

    def lap(d, mats, *_):
        f = d["fabrics"][pa]
        f["module"]["exposure_m"] = 0.24
        f["tile_m"] = [f["tile_m"][0], round(8 * 0.24, 4)]

    def odd(d, mats, *_):
        f = d["fabrics"][pa]
        f["module"]["courses"] = 7
        f["tile_m"] = [f["tile_m"][0], round(7 * f["module"]["exposure_m"], 4)]

    def oversized(d, mats, *_):
        f = d["fabrics"][pa]
        f["module"].update(slate_width_m=0.4, slate_length_m=0.6096, exposure_m=0.2667)
        f["tile_m"] = [round(8 * 0.4, 4), round(8 * 0.2667, 4)]

    def stale(d, mats, *_):
        mats["slate_pennsylvania"]["tile_m"] = [9.9, 9.9]

    def unlisted(d, mats, man, *_):
        man["materials"] = man["materials"][1:]

    def no_source(d, mats, man, src, *_):
        src.pop(d["fabrics"][tile]["sources"][0])

    def barred(d, mats, man, src, *_):
        s = d["restrictions"][0]["documented_on"][0]["source_id"]
        src[s] = dict(src[s], rights_status="check_required")

    def seam(d, mats, man, src, sm):
        sm["slate_pennsylvania_basecolor.png"] = 6.0

    # Each case must be refused for ITS reason, not caught by a neighbouring rule.
    cases = [("a tile_m that scales every slate", scaled, "would be scaled"),
             ("an exposure that breaks the double-lap rule", lap, "double-lap"),
             ("an odd number of half-offset courses", odd, "do not wrap"),
             ("a slate outside the starting range", oversized, "starting range"),
             ("a material.json the data file has moved past", stale, "regenerate"),
             ("a fabric the manifest leaves out", unlisted, "manifest lists"),
             ("an inferred module whose source does not resolve", no_source, "does not resolve"),
             ("a documented-only fabric built from a check_required source", barred, "never build from"),
             ("a map whose wrap edge shows", seam, "shows a seam")]
    failed = 0
    for label, fn, why in cases:
        got = [g for g in mutate(fn) if why in g]
        mark = "FAIL (as it should)" if got else "PASSED — the gate is blind to this"
        print(f"   self-test | {label}: {mark}" + (f" — {got[0]}" if got else ""))
        failed += not got
    if failed:
        print(f"check_roof_library --self-test: {failed} case(s) went unrefused")
        return 1
    print(f"OK: check_roof_library refuses all {len(cases)} breakages")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    if "--check" in sys.argv:
        raise SystemExit(check())
    print(__doc__)
    raise SystemExit(2)
