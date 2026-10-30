#!/usr/bin/env python3
"""Plant the 1904 Prairie Avenue district's parkway elms (T-2473).

    python3 tools/plant_prairie_1904_street_trees.py           # write data/street_trees/1904.json
    python3 tools/plant_prairie_1904_street_trees.py --check   # the committed file is what this writes

WHAT IT READS. The parkway band of every block face in data/street_grid/1904.json
(T-0474: the grass strip between the walk and the curb, inside the 14-ft sidewalk space
the 1905 code gives a 66-ft street), the alleys whose mouths cross a cross-street face,
the carriage walks data/street_section/1904.json lays across the parkways (T-2474: a
tree that would stand on one moves to its nearer side), and nothing else. No position is read off a picture: the pictures say WHAT stood in the
parkway, and this file says where a reconstruction puts each tree.

WHAT THE PICTURES SAY (docs/RESEARCH/prairie_1904_street_trees.md, the reading):
the west-walk view south from 18th Street beside Glessner (negative Dec. 1887-1891, printed
1891-93, reissued as the Holzman postcard postmarked 1908) shows one file of tall elms in
the parkway, standing nearer the curb than the walk, at an irregular spacing of roughly
25-35 ft, clear boles to about a third of their height, and a row on the far side too; the
1905 "Views of Chicago" plate shows the same single file of closely spaced elms; the 1901
photograph of 1700-1706 shows a freshly planted sapling in a gap. So: one file per face,
about 30 ft apart, a mix of mature trees and the odd young replacement and gap.

WHAT IS INVENTED, and recorded as liberty L-prairie-parkway-elms-2473: every position,
the 30-ft spacing and its jitter, the share of young trees and gaps, the elms on every
face beyond the Prairie Avenue blocks the pictures show, and the setback of 10.5 m from each face's end (the
parkway runs on to the cross street's curb, so about 6 m past that street's line). Deterministic: one seed per face, so a re-run plants the same trees.

WHERE A PICTURE PLACES THE TREES (T-1934). data/street_trees/pictured_1904.json names stretches
of a face's parkway that solved pictures see. On a stretch the rule's trees are withdrawn and the
trees read off the pictures stand in their place, each at its distance along the same planting
line; a stretch with no tree in it is a reading too. The rule's draws are taken all the same, so
every tree off a stretch keeps its place. Pictured trees are ids `<face>#pNN`, marked
`"placed": "pictured"`, their crowns drawn from their own seed. 1729 Prairie's 18th Street
(L-pullman-18th-street-trees-1934) is the first. A pictured tree may carry a `scale` read off
its trunk's width in a picture (T-3164: the renderer's elm draws its bole about 0.66 m across at
scale 1); without one its scale is drawn like any other tree's.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "data" / "street_grid" / "1904.json"
SECTION = ROOT / "data" / "street_section" / "1904.json"
OUT = ROOT / "data" / "street_trees" / "1904.json"
PICTURED = ROOT / "data" / "street_trees" / "pictured_1904.json"

FT = 0.3048
SPACING_M = 30 * FT          # about 30 ft between trees, the photograph's rhythm
JITTER_M = 0.9               # +/- along the face, so the file is not a ruled line
CORNER_SETBACK_M = 10.5      # the parkway runs on to the cross street's curb (14 ft); 6 m past its street line
ALLEY_CLEAR_M = 3.5          # clear of an alley mouth's edge
ACROSS = 0.62                # 0 = the walk's edge, 1 = the curb's: nearer the curb
YOUNG_SHARE = 0.08           # replacement saplings (the 1901 photograph's)
GAP_SHARE = 0.04             # a tree lost and not yet replaced
VARIANTS = 12                # mature crowns the renderer builds and shares
WALK_CLEAR_M = 3.0           # either side of a carriage walk's centre: the walk, its block and a trunk


def rng(seed: str):
    """A small deterministic stream from a string, so a face always plants alike."""
    state = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)

    def nxt() -> float:
        nonlocal state
        state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return ((state >> 11) & ((1 << 53) - 1)) / float(1 << 53)
    return nxt


def lerp(p, q, f):
    return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)


def parkway_line(quads):
    """The planting line along a face's parkway: ACROSS of the way from the walk's
    edge to the curb's, as a polyline. A quad is [a, b, c, d] with a->b on the walk's
    side and d->c on the curb's (T-0474's band order)."""
    pts = []
    for i, (a, b, c, d) in enumerate(quads):
        p0 = lerp(a, d, ACROSS)
        p1 = lerp(b, c, ACROSS)
        if i == 0:
            pts.append(p0)
        pts.append(p1)
    return pts


def along(pts):
    acc = [0.0]
    for p, q in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(p, q))
    return acc


def at(pts, acc, s):
    for i in range(1, len(pts)):
        if s <= acc[i] or i == len(pts) - 1:
            seg = acc[i] - acc[i - 1] or 1.0
            p = lerp(pts[i - 1], pts[i], (s - acc[i - 1]) / seg)
            dx, dy = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            return p, math.degrees(math.atan2(dx, dy)) % 360
    return pts[-1], 0.0


def project(pts, acc, q):
    """Distance along the polyline of the point nearest q."""
    best, best_s = float("inf"), 0.0
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        vx, vy = b[0] - a[0], b[1] - a[1]
        L2 = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, ((q[0] - a[0]) * vx + (q[1] - a[1]) * vy) / L2))
        p = (a[0] + vx * t, a[1] + vy * t)
        d = math.dist(p, q)
        if d < best:
            best, best_s = d, acc[i - 1] + math.sqrt(L2) * t
    return best, best_s


def alley_blocks(pts, acc, alleys):
    """Intervals along the face that an alley mouth crosses."""
    out = []
    for a in alleys:
        hits = [project(pts, acc, p) for p in a["polygon_local_m"]]
        near = [s for d, s in hits if d < 12.0]
        if len(near) >= 2:
            out.append((min(near) - ALLEY_CLEAR_M, max(near) + ALLEY_CLEAR_M, a["id"]))
    return out


def walk_marks(pts, acc, walks):
    """Intervals along the face that a carriage walk and its block take (T-2474)."""
    out = []
    for w in walks:
        mid = (w["at"][0] + w["out"][0] * 3.0, w["at"][1] + w["out"][1] * 3.0)
        _, s = project(pts, acc, mid)
        out.append((s - WALK_CLEAR_M, s + WALK_CLEAR_M))
    return out


def pictured_trees(face_id, pts, acc, stretch, views=None, liberty="", first=0):
    """The trees a picture places on one stretch of a face (T-1934). `first` numbers them on
    from the face's earlier stretches (T-1881: 18th Street's north parkway has two), so every
    id stays unique."""
    views = views or {}
    out = []
    for k, t in enumerate(sorted(stretch["trees"], key=lambda t: t["at_m"]), start=first):
        s = t["at_m"]
        if not (stretch["from_m"] <= s <= stretch["to_m"] and 0.0 <= s <= acc[-1]):
            raise ValueError(f"{face_id}: pictured tree at {s} m is off its stretch or its face")
        r = rng(f"T-1934|{face_id}|{s}")
        (e, nn), _ = at(pts, acc, s)
        young = t["kind"] == "young"
        variant, yaw = int(r() * VARIANTS), round(r() * 360, 1)
        drawn = (0.42 + r() * 0.16) if young else (0.88 + r() * 0.22)
        out.append({
            "id": f"{face_id}#p{k:02d}",
            "face": face_id,
            "e": round(e, 2),
            "n": round(nn, 2),
            "kind": t["kind"],
            "variant": variant,
            "yaw_deg": yaw,
            # a trunk measured in a picture sets the scale (T-3164); the draw is taken all the same
            "scale": round(t.get("scale", drawn), 3),
            "placed": "pictured",
            "sources": sorted({views[r.split(" ")[0]]["source_id"] for r in t["read"]
                               if r.split(" ")[0] in views}),
            "note": " ".join(["Read off " + "; ".join(t["read"]) + "."]
                             + ([t["note"]] if t.get("note") else []) + ([liberty] if liberty else [])),
        })
    return out


def plant(grid, walks_by_face=None, pictured=None):
    trees = []
    faces_out = []
    walks_by_face = walks_by_face or {}
    stretches = {}
    for st in (pictured or {}).get("stretches", []):
        stretches.setdefault(st["face"], []).append(st)
    for face in grid["faces"]:
        quads = face["bands"].get("parkway") or []
        if not quads:
            continue
        pts = parkway_line(quads)
        acc = along(pts)
        length = acc[-1]
        blocked = alley_blocks(pts, acc, grid.get("alleys", []))
        marks = walk_marks(pts, acc, walks_by_face.get(face["id"], []))
        r = rng(f"T-2473|{face['id']}")
        usable = length - 2 * CORNER_SETBACK_M
        if usable <= 0:
            continue
        n = max(1, int(usable // SPACING_M) + 1)
        step = usable / max(1, n - 1) if n > 1 else 0.0
        planted = 0
        for i in range(n):
            s = CORNER_SETBACK_M + i * step + (r() - 0.5) * 2 * JITTER_M
            s = min(max(s, CORNER_SETBACK_M), length - CORNER_SETBACK_M)
            pick = r()
            for lo, hi in marks:
                if lo < s < hi:
                    s = lo if s - lo < hi - s else hi
            if not CORNER_SETBACK_M <= s <= length - CORNER_SETBACK_M:
                continue
            if any(lo <= s <= hi for lo, hi, _ in blocked):
                continue
            if pick < GAP_SHARE:
                continue
            (e, nn), bearing = at(pts, acc, s)
            young = pick > 1 - YOUNG_SHARE
            tree = {
                "id": f"{face['id']}#{i:02d}",
                "face": face["id"],
                "e": round(e, 2),
                "n": round(nn, 2),
                "kind": "young" if young else "mature",
                "variant": int(r() * VARIANTS),
                "yaw_deg": round(r() * 360, 1),
                "scale": round((0.42 + r() * 0.16) if young else (0.88 + r() * 0.22), 3),
            }
            # a pictured stretch withdraws the rule's tree only after its draws, so the
            # face's other trees keep their places
            if any(st["from_m"] <= s <= st["to_m"] for st in stretches.get(face["id"], [])):
                continue
            trees.append(tree)
            planted += 1
        first = 0
        for st in sorted(stretches.get(face["id"], []), key=lambda st: st["from_m"]):
            got = pictured_trees(face["id"], pts, acc, st, (pictured or {}).get("views"),
                                 (pictured or {}).get("liberty", ""), first)
            first += len(got)
            trees.extend(got)
            planted += len(got)
        faces_out.append({"face": face["id"], "street": face["street"], "length_m": round(length, 1),
                          "trees": planted,
                          "alley_mouths": [x[2] for x in blocked]})
    return trees, faces_out


def build():
    grid = json.loads(GRID.read_text())
    walks_by_face = {}
    if SECTION.exists():
        for w in json.loads(SECTION.read_text())["carriage_walks"]["walks"]:
            walks_by_face.setdefault(w["face"], []).append(w)
    pictured = json.loads(PICTURED.read_text()) if PICTURED.exists() else None
    if pictured:
        known = {f["id"] for f in grid["faces"]}
        for st in pictured["stretches"]:
            if st["face"] not in known:
                raise ValueError(f"pictured_1904.json: no face {st['face']} in the grid")
    trees, faces = plant(grid, walks_by_face, pictured)
    return {
        "_doc": ("The 1904 Prairie Avenue district's parkway trees (T-2473). GENERATED by "
                 "tools/plant_prairie_1904_street_trees.py from the parkway bands of "
                 "data/street_grid/1904.json -- do not hand-edit; re-run the tool. Local ENU metres "
                 "of data/datum.json. Drawn by renderers/web/js/street-trees.js with trees.js's own "
                 "tree builder (the 1835 American elm). docs/RESEARCH/prairie_1904_street_trees.md "
                 "is the reading; docs/LIBERTIES.md L-prairie-parkway-elms-2473 the inventions."),
        "scene": "1904",
        "target_date": "1904-07-01",
        "ticket": "T-2473",
        "generated_by": "tools/plant_prairie_1904_street_trees.py",
        "species": {
            "id": "ulmus_americana",
            "common": "American elm",
            "tier": "inferred",
            "sources": ["picturesque_chicago_1892_prairie_avenue", "views_of_chicago_1905_prairie_michigan"],
            "note": ("The one file of tall, high-crowned elms in the parkway of the 1887-91 west-walk "
                     "photograph at 18th Street (printed 1891-93, reissued on a postcard postmarked "
                     "1908), and the 'single row of closely spaced elms' of the 1905 Views of Chicago "
                     "plate. Elm is the reading of the crown and bark in those prints and the street "
                     "tree Chicago planted; it is inferred, not named by any record read."),
        },
        "placement": {
            "tier": "reconstructed",
            "liberty": "L-prairie-parkway-elms-2473",
            "spacing_ft": 30,
            "jitter_m": JITTER_M,
            "corner_setback_m": CORNER_SETBACK_M,
            "alley_clear_m": ALLEY_CLEAR_M,
            "across_parkway": ACROSS,
            "young_share": YOUNG_SHARE,
            "gap_share": GAP_SHARE,
            "variants": VARIANTS,
            "pictured": ("data/street_trees/pictured_1904.json: stretches whose trees are read off "
                         "solved pictures and stand in place of the rule's (T-1934, "
                         "L-pullman-18th-street-trees-1934)."),
            "note": ("Every position off a pictured stretch is reconstructed: one file per face at about 30 ft, nearer the "
                     "curb than the walk, kept 10.5 m from each face's end (about 6 m past the cross street's line) and 3.5 m of an alley mouth, "
                     "with about one young replacement tree in twelve and one gap in twenty-five, as "
                     "the photographs show such a file. Faces beyond the Prairie Avenue blocks the "
                     "pictures show are planted the same way and are reconstructed outright."),
        },
        "summary": {"trees": len(trees), "faces": len(faces),
                    "young": sum(t["kind"] == "young" for t in trees)},
        "faces": faces,
        "trees": trees,
    }


def dump(doc):
    """Indented, with one tree and one face to a line: the file diffs by tree."""
    rows = {k: doc.pop(k) for k in ("faces", "trees")}
    head = json.dumps(doc, indent=1)[:-2]
    parts = [head]
    for k, items in rows.items():
        body = ",\n".join("  " + json.dumps(x, separators=(", ", ": ")) for x in items)
        parts.append(f',\n "{k}": [\n{body}\n ]')
    doc.update(rows)
    return "".join(parts) + "\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = dump(doc)
    if a.check:
        have = OUT.read_text() if OUT.exists() else ""
        if have != text:
            print(f"street trees: {OUT.relative_to(ROOT)} is not what the tool writes -- re-run "
                  "python3 tools/plant_prairie_1904_street_trees.py")
            return 1
        print(f"street trees: {doc['summary']['trees']} trees on {doc['summary']['faces']} faces, as written")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {doc['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
