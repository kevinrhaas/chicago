#!/usr/bin/env python3
"""What Prairie Avenue's sidewalks see of the district behind it, 1904 (T-2983).

    python3 tools/census_prairie_1904_background.py            write the census
    python3 tools/census_prairie_1904_background.py --check    re-derive, refuse a drift
    python3 tools/census_prairie_1904_background.py --self-test

The district draft (T-2159 to T-2163) stands every Prairie Avenue house, and T-2982 the
named context buildings off it. Behind them lie the Indiana and Calumet frontages, the
end-street lots and the Illinois Central side, which the 1904 scene leaves as bare ground.
This tool is the VISIBILITY CENSUS that says which of that ground a visitor on Prairie
Avenue can actually see, so the background is drafted where it is seen and recorded as
open where it is not, instead of guessed at.

THE STANDS. Every 6 m along the centre line of both of Prairie Avenue's sidewalks, 16th
to 22nd Street (the `walk` band of every `prairie__*` face of data/street_grid/1904.json),
an eye 1.6 m over the walk. The ground is taken as flat: the lake plain falls well under a
metre across these three blocks, inside the georeference.

THE TARGETS. Every parcel of the 1904 grid that does not front Prairie Avenue (Indiana,
Calumet, the end streets), sampled on a 4 m grid inside its lot lines at two heights,
2 m (a ground storey) and 9 m (the top of a two- to three-storey house); and the ground
of each block that no parcel covers (the Indiana half of the 18th-20th block, which
T-1745 has not yet lotted, and the strip between Prairie's east lots and the Illinois
Central), sampled the same way.

THE FABRIC IN THE WAY. Every building the Sanborn traces carry (data/traces/
prairie_1904_footprints_s<sheet>.json), as a prism of its traced outline up to a height
from its sheet census's printed storeys (HEIGHTS below; a raised basement, 3.9 m storeys,
an allowance for the roof). A sight line is blocked when it passes through a wall below
that height. A target's own buildings never hide it. Trees, fences and carriages are not
counted, so the census errs toward SEEN, which is the safe side for a background.

THE VERDICT. A target is `seen` when at least one of its samples is visible from at least
one stand within REACH_M; its `seen_share`, `stands` and `nearest_m` rank how much. The
census measures; it does not draft. What stands on each seen lot is read off the sheet by
the ticket that drafts that block face.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parents[1]
GRID = ROOT / "data" / "street_grid" / "1904.json"
TRACES = ["20", "28", "35", "35x"]
CENSUS = {
    "20": REPO / "chicago" / "prairie_1904_v1" / "data" / "sheet_census" / "sheet-20.json",
    "28": REPO / "chicago" / "prairie_1904_v1" / "data" / "sheet_census" / "sheet-28.json",
    "35": REPO / "chicago" / "prairie_1904_v1" / "data" / "sheet_census" / "sheet-35.json",
    "35x": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s35.json",
}
OUT = ROOT / "data" / "components" / "prairie_1904" / "background_census.json"

STAND_STEP_M = 6.0
EYE_M = 1.6
SAMPLE_M = 4.0
SAMPLE_Z_M = (2.0, 9.0)
REACH_M = 450.0
HEIGHTS = {"basement_m": 1.0, "storey_m": 3.9, "half_m": 2.5, "roof_m": 1.5,
           "service_storey_m": 3.3, "front_default_m": 10.0, "service_default_m": 6.0}


def rel(p: Path) -> str:
    return str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p)


def inside(px: np.ndarray, py: np.ndarray, poly) -> np.ndarray:
    """Even-odd point-in-polygon for arrays of points."""
    poly = np.asarray(poly, float)
    x0, y0 = poly[:, 0], poly[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    res = np.zeros(px.shape, bool)
    for a, b, c, d in zip(x0, y0, x1, y1):
        cond = (b > py) != (d > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            xs = a + (py - b) * (c - a) / (d - b)
        res ^= cond & (px < xs)
    return res


def grid_in(poly, step=SAMPLE_M, exclude=()):
    p = np.asarray(poly, float)
    xs = np.arange(p[:, 0].min() + step / 2, p[:, 0].max(), step)
    ys = np.arange(p[:, 1].min() + step / 2, p[:, 1].max(), step)
    gx, gy = np.meshgrid(xs, ys)
    gx, gy = gx.ravel(), gy.ravel()
    keep = inside(gx, gy, p)
    for q in exclude:
        keep &= ~inside(gx, gy, q)
    return np.stack([gx[keep], gy[keep]], 1)


def height_of(kind: str, reading: str | None) -> tuple[float, str]:
    h = HEIGHTS
    if kind == "detached_service":
        m = re.search(r"(\d)(½)?-storey", reading or "")
        if not m:
            return h["service_default_m"], "service, no storey figure read: the default"
        return int(m.group(1)) * h["service_storey_m"] + (h["half_m"] if m.group(2) else h["roof_m"]), "service storeys"
    m = re.match(r"\s*(\d)(½)?", reading or "")
    if not m:
        return h["front_default_m"], "no storey figure read: the default"
    return (h["basement_m"] + int(m.group(1)) * h["storey_m"]
            + (h["half_m"] if m.group(2) else h["roof_m"])), "printed storeys"


def load():
    grid = json.loads(GRID.read_text())
    readings = {}
    for sheet, path in CENSUS.items():
        c = json.loads(path.read_text())
        for f in c.get("frontages", []):
            for pg in f.get("polygons", []):
                readings[pg["id"]] = pg.get("reading_1911")
    fabric = []
    for sheet in TRACES:
        t = json.loads((ROOT / "data" / "traces" / f"prairie_1904_footprints_s{sheet}.json").read_text())
        for parcel in t["parcels"]:
            for b in parcel["buildings"]:
                if b.get("for_1904") not in (None, "as_mapped", "backcast", "present"):
                    if str(b.get("for_1904")).startswith(("absent", "removed", "not_")):
                        continue
                reading = next((readings.get(i) for i in b.get("census_ids", []) if readings.get(i)), None)
                hh, basis = height_of(b.get("kind", ""), reading)
                fabric.append({"id": b["id"], "parcel": parcel["parcel_id"], "sheet": sheet,
                               "poly": np.asarray(b["polygon_local_m"], float), "h": hh, "basis": basis})
    return grid, fabric


def stands_of(grid):
    out = []
    for f in grid["faces"]:
        if f["street"] != "prairie":
            continue
        for q in f["bands"]["walk"]:
            q = np.asarray(q, float)
            a, b = (q[0] + q[3]) / 2, (q[1] + q[2]) / 2
            n = max(2, int(np.ceil(np.linalg.norm(b - a) / STAND_STEP_M)) + 1)
            for i, t in enumerate(np.linspace(0, 1, n)):
                p = a + (b - a) * t
                out.append({"face": f["id"], "i": i, "xy": p})
    return out


def targets_of(grid, fabric):
    tg = []
    lots = [p for p in grid["parcels"]]
    for p in lots:
        if p["street"] == "prairie":
            continue
        pts = grid_in(p["polygon_local_m"])
        if not len(pts):
            c = np.mean(np.asarray(p["polygon_local_m"], float), 0)
            pts = c[None, :]
        tg.append({"id": p["id"], "kind": "parcel", "street": p["street"], "side": p.get("side"),
                   "block": p["block"], "where": p.get("where"), "pts": pts})
    covered = [p["polygon_local_m"] for p in lots] + [a["polygon_local_m"] for a in grid["alleys"]]
    for b in grid["blocks"]:
        pts = grid_in(b["outline_local_m"], exclude=covered)
        if len(pts) < 8:  # slivers between lot lines and the block outline
            continue
        tg.append({"id": f"unparcelled:{b['id']}", "kind": "unparcelled", "street": None, "side": None,
                   "block": b["id"], "where": f"ground of {b['where']} that no 1904 parcel covers",
                   "pts": pts})
    return tg


def census():
    grid, fabric = load()
    stands = stands_of(grid)
    targets = targets_of(grid, fabric)
    # every sample of every target, at both heights
    P, Z, owner = [], [], []
    for k, t in enumerate(targets):
        for z in SAMPLE_Z_M:
            P.append(t["pts"])
            Z.append(np.full(len(t["pts"]), z))
            owner.append(np.full(len(t["pts"]), k))
    P, Z, owner = np.concatenate(P), np.concatenate(Z), np.concatenate(owner)
    parcel_of_owner = np.array([t["id"] for t in targets])
    fab_parcel = [f["parcel"] for f in fabric]
    seen_by = np.zeros((len(stands), len(P)), bool)
    for si, s in enumerate(stands):
        S = s["xy"]
        d = P - S
        dist = np.hypot(d[:, 0], d[:, 1])
        ok = dist <= REACH_M
        lo, hi = np.minimum(P, S), np.maximum(P, S)
        for fi, f in enumerate(fabric):
            poly = f["poly"]
            pmin, pmax = poly.min(0), poly.max(0)
            m = ok & (lo[:, 0] <= pmax[0]) & (hi[:, 0] >= pmin[0]) & (lo[:, 1] <= pmax[1]) & (hi[:, 1] >= pmin[1])
            m &= parcel_of_owner[owner] != fab_parcel[fi]
            idx = np.nonzero(m)[0]
            if not len(idx):
                continue
            A = poly
            E = np.roll(poly, -1, 0) - poly
            dd = d[idx][:, None, :]
            AS = (A - S)[None, :, :]
            den = dd[..., 0] * E[None, :, 1] - dd[..., 1] * E[None, :, 0]
            with np.errstate(divide="ignore", invalid="ignore"):
                t = (AS[..., 0] * E[None, :, 1] - AS[..., 1] * E[None, :, 0]) / den
                u = (AS[..., 0] * dd[..., 1] - AS[..., 1] * dd[..., 0]) / den
            hit = (den != 0) & (t > 0) & (t < 1) & (u >= 0) & (u <= 1)
            z = EYE_M + (Z[idx][:, None] - EYE_M) * t
            blocked = (hit & (z < f["h"])).any(1)
            ok[idx[blocked]] = False
        seen_by[si] = ok
    rows = []
    for k, t in enumerate(targets):
        mine = owner == k
        n = int(mine.sum())
        vis = seen_by[:, mine]
        any_sample = vis.any(0)
        stand_hits = vis.any(1)
        near = None
        best = None
        if stand_hits.any():
            c = t["pts"].mean(0)
            ds = [(float(np.hypot(*(stands[i]["xy"] - c))), i) for i in np.nonzero(stand_hits)[0]]
            near, bi = min(ds)
            best = {"face": stands[bi]["face"], "at_m": [round(float(v), 1) for v in stands[bi]["xy"]],
                    "sees_share": round(float(vis[bi].mean()), 3)}
        low = vis[:, : n // 2].any(0) if n else any_sample
        rows.append({
            "id": t["id"], "kind": t["kind"], "street": t["street"], "side": t["side"], "block": t["block"],
            "where": t["where"], "samples": n,
            "seen": bool(any_sample.any()),
            "seen_share": round(float(any_sample.mean()), 3) if n else 0.0,
            "seen_share_ground_storey": round(float(low.mean()), 3) if n else 0.0,
            "stands": int(stand_hits.sum()),
            "nearest_m": round(near, 1) if near is not None else None,
            "best_stand": best,
        })
    groups = {}
    for r in rows:
        key = f"{r['street']}:{r['block']}" if r["kind"] == "parcel" else r["id"]
        g = groups.setdefault(key, {"group": key, "targets": 0, "seen": 0, "stands_max": 0, "ids_seen": []})
        g["targets"] += 1
        if r["seen"]:
            g["seen"] += 1
            g["ids_seen"].append(r["id"])
        g["stands_max"] = max(g["stands_max"], r["stands"])
    inputs = hashlib.sha256()
    for p in [GRID, *CENSUS.values(), *[ROOT / "data" / "traces" / f"prairie_1904_footprints_s{s}.json" for s in TRACES]]:
        inputs.update(p.read_bytes())
    return {
        "_doc": "GENERATED by tools/census_prairie_1904_background.py — do not hand-edit; re-run the tool. The visibility census of the district behind Prairie Avenue for 1904 (T-2983): which Indiana, Calumet, end-street and unparcelled ground a visitor on Prairie Avenue's sidewalks can see past the traced fabric. It measures; it does not draft.",
        "ticket": "T-2983",
        "target_date": "1904-07-01",
        "inputs_sha256": inputs.hexdigest(),
        "method": {
            "stands": f"every {STAND_STEP_M:g} m along the centre line of both Prairie Avenue walks (16th-22nd), eye {EYE_M:g} m, flat ground",
            "targets": f"every non-Prairie parcel of data/street_grid/1904.json and every block's unparcelled ground, sampled on a {SAMPLE_M:g} m grid at {', '.join(f'{z:g}' for z in SAMPLE_Z_M)} m",
            "fabric": "every traced building of sheets " + ", ".join(TRACES) + " as a prism to a height from its census storeys",
            "heights": HEIGHTS,
            "reach_m": REACH_M,
            "seen": "at least one sample visible from at least one stand",
            "limits": "Trees, fences, carriages and roof pitch are not counted, so the census errs toward seen. Heights are a rule over the printed storeys, not a measurement. A target's own buildings never hide it.",
        },
        "counts": {"stands": len(stands), "fabric": len(fabric), "targets": len(rows),
                   "seen": sum(r["seen"] for r in rows)},
        "groups": sorted(groups.values(), key=lambda g: (-g["seen"], g["group"])),
        "targets": sorted(rows, key=lambda r: (not r["seen"], -r["stands"], r["id"])),
    }


def self_test():
    sq = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert inside(np.array([5.0, 15.0]), np.array([5.0, 5.0]), sq).tolist() == [True, False]
    assert len(grid_in(sq, 4.0)) == 4
    assert height_of("front", "3B brick dwelling")[0] == 1.0 + 3 * 3.9 + 1.5
    assert height_of("front", "2½B frame")[0] == 1.0 + 2 * 3.9 + 2.5
    assert height_of("detached_service", "2-storey brick BARN")[0] == 2 * 3.3 + 1.5
    print("census_prairie_1904_background: self-test ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return 0
    text = json.dumps(census(), indent=1, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{rel(OUT)} differs from what the tool derives: re-run it", file=sys.stderr)
            return 1
        print(f"{rel(OUT)}: current")
        return 0
    OUT.write_text(text)
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
