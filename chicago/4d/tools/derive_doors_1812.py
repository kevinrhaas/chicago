#!/usr/bin/env python3
"""Where each 1812 building is entered: its door leaves, read off the built models (T-3463).

    python3 tools/derive_doors_1812.py            write data/humans/doors_1812.json
    python3 tools/derive_doors_1812.py --check    the gate: the file is what the models say
                                                  (cheap: a model's sha256 unchanged keeps
                                                  its doors; a changed one is re-read)

The owner, 2026-11-08: *"If they are inside I can walk to door and ask for any person
inside"*. The 1812 town's doors are drawn into each building's own model (no hung leaf, as
Glessner's house-doors.js has), so this reads them from there: every triangle of a `door` or
`door_panel` material (a plank `board_door`; an outbuilding's one `board`) that comes down to the sill (below SILL_M; a window's shutters and a
loft door stand higher) is a door leaf, leaves within LINK_M of one another are one door, and
the door is where the building's footprint edge nearest it runs. Out from that edge, STEP_M
past the leaf, is where someone who answers it stands: renderers/web/js/human-days.js brings
a person asked for out there and on to the visitor.

The model's frame is the sidecar footprint's: u = glTF x, v = -glTF z (the gate holds this
by the leaf lying on the footprint edge, within EDGE_M). Its placement turns it CLOCKWISE by
rotation_deg, as tools/check_structure_clearance.py's to_world.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from export_print_3mf import load_triangles  # noqa: E402

OUT = ROOT / "data/humans/doors_1812.json"
# Bump on any change to how doors are read: a cached row is kept only under the same format.
FORMAT = "c4d-doors-1812/3"   # /3 (T-3553): each built leaf door carries its passage `plan`
SIDECARS = ROOT / "data/sidecars/1812"
DOOR_MATERIALS = ("door", "door_panel", "board_door", "board_door_panel")
# An outbuilding (generators/archetypes) hangs one plank door, its only `board`.
OUTBUILDING_DOOR = ("board",)
SILL_M = 0.3      # a leaf comes down to the floor; windows and shutters stand above this
LINK_M = 0.6      # leaf triangles nearer than this are one door
EDGE_M = 0.35     # a door lies on its footprint's edge
STEP_M = 0.7      # where one who answers stands, out from the leaf
MIN_WIDTH_M = 0.5
# T-3553 (the owner, 2026-11-16: "people appear outside doors the doors don't open and close"):
# a built leaf is a passage, hung by renderers/web/js/house-doors.js to swing open as someone
# goes in or comes out, as 1904's are (derive_doors_scene.py passage_plan). These models hang
# the leaf on an uncut wall (nothing is modelled behind it), so it swings OUT, as 1904's back
# doors do, and the doorway's dark is a mouth over the wall's face while it stands open. The
# way runs straight out from the leaf's middle, and one waits clear of its swing.
WAY_CLEAR_M = 0.25       # past the swinging leaf's sweep, where one waits for it
WAY_FOOT_M = 1.0         # the way's foot, past that again
WAY_GROUND_M = 0.12      # a sill lower than this is the ground (the caller's ground answers)
# Lived-in buildings whose model draws no door leaf on an edge: the door is put at the middle
# of the footprint edge facing the given point (reconstructed; the model has no front). The
# south-west small house of the fort (the Holts', T-3461) is a 1.7 x 2.4 m box clad all round
# in `board`; it is entered from the parade, whose centre is the flagstaff's foot.
NO_LEAF = {"first_fort_dearborn_small_house_sw": (1152.0, 221.0)}


def to_world(u: float, v: float, pl: dict) -> tuple[float, float]:
    th = math.radians(float(pl.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)
    return (float(pl["local_e"]) + u * c + v * s, float(pl["local_n"]) - u * s + v * c)


def inside(p, poly) -> bool:
    x, y = p
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clusters(points: np.ndarray) -> list[list[int]]:
    left = set(range(len(points)))
    out = []
    while left:
        grp = [left.pop()]
        frontier = list(grp)
        while frontier:
            i = frontier.pop()
            near = [j for j in left if math.hypot(*(points[j] - points[i])) < LINK_M]
            for j in near:
                left.discard(j)
            grp += near
            frontier += near
        out.append(grp)
    return out


def lodge_doors(sidecar: dict, glb: Path) -> list[dict]:
    """A camp ground's lodges (generators/archetypes/lodge_camp.py): each doorway draws the dark
    inside (`camp_dark`) down to the ground; out from the lodge's own covering through it is out."""
    parts = load_triangles(glb)
    dark = [t for name, t in parts if name == "camp_dark"]
    cover = [t for name, t in parts if name in ("camp_cattail_mat", "camp_elm_bark")]
    if not dark or not cover:
        return []
    D = np.concatenate(dark)
    D = D[D[:, :, 1].min(axis=1) < SILL_M]
    C = np.concatenate(cover)
    cc = np.stack([C[:, :, 0].mean(1), -C[:, :, 2].mean(1)], 1)
    pl = sidecar["placement"]
    th = math.radians(float(pl.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)
    out = []
    for grp in clusters(np.stack([D[:, :, 0].mean(1), -D[:, :, 2].mean(1)], 1)):
        pts = np.stack([D[grp][:, :, 0].ravel(), -D[grp][:, :, 2].ravel()], 1)
        u, v = (pts.min(0) + pts.max(0)) / 2
        near = cc[np.hypot(cc[:, 0] - u, cc[:, 1] - v) < 3.5]
        if not len(near) or float(np.ptp(pts, axis=0).max()) < MIN_WIDTH_M:
            continue
        centre = near.mean(0)
        normal = np.array([u, v]) - centre
        normal = normal / max(1e-9, float(np.hypot(*normal)))
        su, sv = np.array([u, v]) + normal * STEP_M
        e, n = to_world(su, sv, pl)
        le, ln = to_world(u, v, pl)
        de, dn = normal[0] * c + normal[1] * s, -normal[0] * s + normal[1] * c
        out.append({"leaf": {"local_e": round(le, 2), "local_n": round(ln, 2)},
                    "step": {"local_e": round(e, 2), "local_n": round(n, 2)},
                    "outward_deg": round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1),
                    "width_m": round(float(np.ptp(pts, axis=0).max()), 2), "lodge": True})
    out.sort(key=lambda d: (d["leaf"]["local_e"], d["leaf"]["local_n"]))
    return [{"id": f"{sidecar['id']}:lodge{i + 1}", **d} for i, d in enumerate(out)]


def hull(points: np.ndarray) -> list[tuple[float, float]]:
    """The convex hull of 2D points, counter-clockwise (Andrew's monotone chain)."""
    pts = sorted(set(map(tuple, np.round(points, 3).tolist())))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


WALL_LINK_M = 1.2   # covering triangles nearer than this are one lodge's wall
WALL_FOOT_M = 0.4   # a wall comes down to the ground: covering lower than this


def lodge_walls(sidecar: dict, glb: Path) -> list[list[list[float]]]:
    """T-3520: where each lodge's walls stand on the ground, in local E/N (the owner, 2026-11-08:
    "people can stand and break the wall of the mat walls"). The hull of the lodge's own covering
    (mats or bark) where it comes down to the ground; an arbor's roof, up on its posts, is not a wall."""
    parts = load_triangles(glb)
    cover = [t for name, t in parts if name in ("camp_cattail_mat", "camp_elm_bark")]
    if not cover:
        return []
    C = np.concatenate(cover)
    C = C[C[:, :, 1].min(axis=1) < WALL_FOOT_M]
    if not len(C):
        return []
    centres = np.stack([C[:, :, 0].mean(1), -C[:, :, 2].mean(1)], 1)
    pl = sidecar["placement"]
    out = []
    for grp in clusters_within(centres, WALL_LINK_M):
        pts = np.stack([C[grp][:, :, 0].ravel(), -C[grp][:, :, 2].ravel()], 1)
        if float(np.ptp(pts, axis=0).max()) < 1.0:
            continue
        ring = [list(map(lambda x: round(x, 2), to_world(u, v, pl))) for u, v in hull(pts)]
        if len(ring) >= 3:
            out.append(ring)
    out.sort(key=lambda r: (min(p[0] for p in r), min(p[1] for p in r)))
    return out


def clusters_within(points: np.ndarray, link: float) -> list[list[int]]:
    """Groups of points each within `link` of another of its group (a grid keeps it quick)."""
    cell = {}
    for i, (x, y) in enumerate(points):
        cell.setdefault((int(x // link), int(y // link)), []).append(i)
    seen, out = set(), []
    for i in range(len(points)):
        if i in seen:
            continue
        seen.add(i)
        grp, frontier = [i], [i]
        while frontier:
            j = frontier.pop()
            cx, cy = int(points[j][0] // link), int(points[j][1] // link)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for k in cell.get((cx + dx, cy + dy), []):
                        if k not in seen and math.hypot(*(points[k] - points[j])) < link:
                            seen.add(k)
                            grp.append(k)
                            frontier.append(k)
        out.append(grp)
    return out


def passage_plan(leaf, mats, normal) -> dict:
    """A built leaf as house-doors.js hangs a passage, in the model's plan (u = x, v = -z):
    d out of the wall along `normal`, s along it (`normal` turned a quarter left)."""
    along = np.array([-normal[1], normal[0]])
    uv = np.stack([leaf[:, :, 0].ravel(), -leaf[:, :, 2].ravel()], 1)
    y = leaf[:, :, 1].ravel()
    c = (uv.min(0) + uv.max(0)) / 2
    d, s = (uv - c) @ normal, (uv - c) @ along
    front, back = float(d.max()), float(d.min())
    s0, s1 = float(s.min()), float(s.max())
    sm = (s0 + s1) / 2
    origin = c + normal * front + along * sm
    sill, head = float(y.min()), float(y.max())
    r = lambda x: round(float(x), 3)
    clear = (s1 - s0) + WAY_CLEAR_M
    at = lambda dd: [r(origin[0] + normal[0] * dd), r(origin[1] + normal[1] * dd)]
    return {
        'name': 'Door', 'origin': [r(origin[0]), r(origin[1])], 'outward': [r(normal[0]), r(normal[1])],
        'along': [r(along[0]), r(along[1])],
        'jambs': [r(s0 - sm - 0.01), r(s1 - sm + 0.01)], 'sill': r(sill), 'head': r(head),
        'leaf': {'front': 0, 'back': r(back - front), 's': [r(s0 - sm), r(s1 - sm)], 'foot': r(sill), 'top': r(head)},
        'hinge': 'right', 'pair': False, 'openDeg': -95, 'vestibule': False, 'mouth': True,
        'revealBack': -0.005, 'leafBoxBack': r(back - front - 0.03),
        'leafMaterials': sorted(mats),
        'way': [at(clear + WAY_FOOT_M) + [None], at(clear) + [None if sill < WAY_GROUND_M else r(sill)]],
        'grades': {'leaf': 'inferred', 'hinge': 'reconstructed', 'swing': 'reconstructed', 'vestibule': 'reconstructed', 'treads': 'reconstructed'},
    }


def doors_of(sidecar: dict, glb: Path, plans: bool = False) -> tuple[list[dict], list[str]]:
    """`plans`: each built leaf also carries its passage plan (1812's doors file only)."""
    problems = []
    if sidecar.get("archetype") == "lodge_camp" or sidecar["id"].startswith("potawatomi_camp_1812"):
        return lodge_doors(sidecar, glb), problems
    poly = [tuple(map(float, p)) for p in (sidecar.get("footprint") or {}).get("polygon") or []]
    pl = sidecar["placement"]
    names = DOOR_MATERIALS + (OUTBUILDING_DOOR if sidecar.get("archetype") == "outbuilding" else ())
    got = [(name, t) for name, t in load_triangles(glb) if name.lower() in names]
    tris = [t for _, t in got]
    if not tris or len(poly) < 3:
        return [], problems
    if sidecar["id"] in NO_LEAF:
        return [edge_door(sidecar, poly, NO_LEAF[sidecar["id"]])], problems
    T = np.concatenate(tris)
    M = np.concatenate([[name] * len(t) for name, t in got])
    low = T[:, :, 1].min(axis=1) < SILL_M
    T, M = T[low], M[low]
    if not len(T):
        return [], problems
    # Each triangle's points, in the footprint's frame.
    uv = np.stack([T[:, :, 0].ravel(), -T[:, :, 2].ravel()], 1)
    centres = np.stack([T[:, :, 0].mean(1), -T[:, :, 2].mean(1)], 1)
    out = []
    for grp in clusters(centres):
        pts = uv[np.concatenate([np.arange(3 * i, 3 * i + 3) for i in grp])]
        u, v = (pts.min(0) + pts.max(0)) / 2
        # The edge it lies on.
        best = None
        for a, b in zip(poly, poly[1:] + poly[:1]):
            a, b = np.array(a), np.array(b)
            ab = b - a
            L = float(np.hypot(*ab))
            if L < 1e-6:
                continue
            t = float(np.clip(np.dot([u, v] - a, ab) / (L * L), 0, 1))
            d = float(np.hypot(*(a + t * ab - [u, v])))
            if best is None or d < best[0]:
                best = (d, ab / L)
        d, along = best
        width = float(np.ptp(pts @ along))
        if width < MIN_WIDTH_M:
            continue
        if d > EDGE_M:
            problems.append(f"{sidecar['id']}: a door at u {u:.2f}, v {v:.2f} lies {d:.2f} m off the footprint edge")
            continue
        normal = np.array([along[1], -along[0]])
        if inside(tuple(np.array([u, v]) + normal * 0.5), poly):
            normal = -normal
        su, sv = np.array([u, v]) + normal * STEP_M
        e, n = to_world(su, sv, pl)
        le, ln = to_world(u, v, pl)
        th = math.radians(float(pl.get("rotation_deg") or 0.0))
        c, s = math.cos(th), math.sin(th)
        de, dn = normal[0] * c + normal[1] * s, -normal[0] * s + normal[1] * c
        row = {
            "leaf": {"local_e": round(le, 2), "local_n": round(ln, 2)},
            "step": {"local_e": round(e, 2), "local_n": round(n, 2)},
            "outward_deg": round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1),
            "width_m": round(width, 2),
        }
        plan = passage_plan(T[grp], set(M[grp].tolist()), normal) if plans else None
        if plan is not None:
            row.update({"passage": True, "plan": plan,
                        "reconstructed": "Leaf read from the built door material. It is hung to swing open as someone goes in "
                                         "or comes out (house-doors.js passages, T-3553); its hinge side and its outward swing "
                                         "are reconstructed, and the model has no opening behind it, so the doorway's dark is drawn "
                                         "over the wall while it stands open."})
        out.append(row)
    out.sort(key=lambda d: (-d["width_m"], d["leaf"]["local_e"], d["leaf"]["local_n"]))
    for i, d in enumerate(out):
        d["id"] = f"{sidecar['id']}:{'front' if i == 0 else f'door{i + 1}'}"
    return [{"id": d.pop("id"), **d} for d in out], problems


def edge_door(sidecar: dict, poly: list, toward: tuple[float, float],
              why: str = "the model draws no door leaf on an edge; put at the middle of the side facing the parade") -> dict:
    """A door at the middle of the footprint edge whose outward side faces `toward`."""
    pl = sidecar["placement"]
    best = None
    for a, b in zip(poly, poly[1:] + poly[:1]):
        a, b = np.array(a), np.array(b)
        mid = (a + b) / 2
        along = (b - a) / max(1e-9, float(np.hypot(*(b - a))))
        normal = np.array([along[1], -along[0]])
        if inside(tuple(mid + normal * 0.3), poly):
            normal = -normal
        e, n = to_world(*(mid + normal * STEP_M), pl)
        k = math.hypot(e - toward[0], n - toward[1])
        if best is None or k < best[0]:
            best = (k, mid, normal)
    _, mid, normal = best
    th = math.radians(float(pl.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)
    de, dn = normal[0] * c + normal[1] * s, -normal[0] * s + normal[1] * c
    le, ln = to_world(*mid, pl)
    e, n = to_world(*(mid + normal * STEP_M), pl)
    return {"id": f"{sidecar['id']}:front", "leaf": {"local_e": round(le, 2), "local_n": round(ln, 2)},
            "step": {"local_e": round(e, 2), "local_n": round(n, 2)},
            "outward_deg": round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1), "width_m": None,
            "reconstructed": why}


def derive(previous: dict | None = None) -> tuple[dict, list[str]]:
    same = (previous or {}).get("format") == FORMAT
    prev = {s["structure"]: s for s in (previous or {}).get("structures", [])} if same else {}
    rows, problems = [], []
    for f in sorted(SIDECARS.glob("*.json")):
        sc = json.loads(f.read_text())
        if not isinstance(sc, dict) or "asset" not in sc or "placement" not in sc:
            continue
        glb = ROOT / "assets" / sc["asset"]
        if not glb.exists():
            continue
        h = sha256(glb)
        old = prev.get(sc["id"])
        lodges = sc.get("archetype") == "lodge_camp" or sc["id"].startswith("potawatomi_camp_1812")
        if old and old.get("asset_sha256") == h and old.get("placement") == _placement(sc) and (not lodges or "walls" in old):
            rows.append(old)
            continue
        doors, p = doors_of(sc, glb, plans=True)
        problems += p
        if doors:
            row = {"structure": sc["id"], "name": sc.get("name") or sc["id"], "asset_sha256": h,
                   "placement": _placement(sc), "doors": doors}
            if lodges:
                row["walls"] = lodge_walls(sc, glb)   # T-3520: no one stands in a lodge's wall
            rows.append(row)
    return {
        "format": FORMAT,
        "ticket": "T-3463",
        "generated_by": "tools/derive_doors_1812.py",
        "note": "Where each 1812 building's door leaves are (read off its model) and where one who answers stands. Asking at a door: renderers/web/js/human-days.js.",
        "structures": rows,
    }, problems


def _placement(sc: dict) -> dict:
    pl = sc["placement"]
    return {k: pl.get(k) for k in ("local_e", "local_n", "rotation_deg")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    previous = json.loads(OUT.read_text()) if OUT.exists() else None
    data, problems = derive(previous)
    for p in problems:
        print(f"doors_1812: {p}", file=sys.stderr)
    text = json.dumps(data, indent=1) + "\n"
    if args.check:
        if previous is None or OUT.read_text() != text:
            print("FAIL doors_1812: data/humans/doors_1812.json is not what the 1812 models say; run python3 tools/derive_doors_1812.py", file=sys.stderr)
            return 1
        n = sum(len(s["doors"]) for s in data["structures"])
        print(f"doors_1812: {n} doors on {len(data['structures'])} buildings, as the models have them")
        return 1 if problems else 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {sum(len(s['doors']) for s in data['structures'])} doors")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
