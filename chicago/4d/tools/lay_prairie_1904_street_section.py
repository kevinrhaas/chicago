#!/usr/bin/env python3
"""Lay the 1904 district's street section: the curb's reveal, the walk's fall, and the
carriage walks and carriage blocks across the parkways (T-2474).

    python3 tools/lay_prairie_1904_street_section.py           # write data/street_section/1904.json
    python3 tools/lay_prairie_1904_street_section.py --check   # the committed file is what this writes

WHAT IT READS. The block faces and parcels of data/street_grid/1904.json (T-0474) and
nothing else. The renderer (street-grid.js) reads the section to set the roadway below
the curbs and to slope the sidewalk space toward them; the parkway elms
(tools/plant_prairie_1904_street_trees.py) read the carriage walks to keep clear of them.

THE SECTION. The 1905 code gives the sidewalk space's grade: "a uniform incline from the
street line toward the curb line, with a fall of one inch in every three feet" (the
'Slope' sections), carried to 1904 as inferred. No source read gives the curb's reveal;
the 1887-91 view south from 18th Street and the owner's second photograph of the avenue
show a dressed stone curb standing above the roadway by about one stoop riser, so the
reveal is 7 in, reconstructed (docs/LIBERTIES.md L-prairie-curb-reveal-2474). The lot
line stays where the ground is; the walk falls to the curb, and the roadway lies a
reveal below the curb's top.

THE CARRIAGE WALKS. The 1887-91 view shows a paved crossing of the parkway from the walk
to the curb; HABS shows one from the Glessner door to the curb c. 1923; the 1905 Views of
Chicago plate and the c. 1890 photograph show dressed stone carriage blocks at the curb.
Where each house's stood is not recorded, so: one crossing, 5 ft wide, at the middle of
every lot at least 40 ft wide (a detached house with a carriage; the narrower lots are
rows), and a carriage block beside it at the curb. All reconstructed, and recorded at
L-prairie-carriage-walks-2474.

THE CARRIAGE POSTS (T-3198). T-2474 also stood a 3 x 2 ft carriage block at the curb of every
one of those lots. The owner, 2026-10-27: "i dont need to have those carriage steps at every
house. i dont see that in photos of prarie anywhere ... what you keep you should vary them in
appearance so that they do not look like clones". Read again, the two pictures T-2474 cited show
the lot-line coping (Glessner's rounded-top granite curbing; a row of rounded copers along a
walk), not blocks at the curb. What the pictures DO show at the curb is a stone post, and only at
some houses: one square post with a domed cap beside 1815's carriage walk (its own photograph,
`chicagology_1815_sears_two_views`), and round-topped white posts in the 2100 block -- a pair at
2112's carriage walk and one at 2110 on the west parkway, and a row along the east curb opposite
(the Glessner House Museum's photograph of the block looking north-west,
`glessner_blog_2100_block_looking_nw_1890s`). So the rule-placed blocks are withdrawn and
`POSTS` below stands a post only where a picture puts one, each varied by its own seed in height,
girth, cap, lean, set and tone so no two are clones. A post keeps a trunk's width off every
parkway elm (data/street_trees/1904.json, read if present: the trees read only the walks, so the
two files never chase each other).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "data" / "street_grid" / "1904.json"
OUT = ROOT / "data" / "street_section" / "1904.json"

FT = 0.3048
IN = FT / 12
FALL_IN_PER_3FT = 1.0
REVEAL_IN = 7.0
MIN_FRONTAGE_FT = 40.0
WALK_WIDTH_FT = 5.0
TREES = ROOT / "data" / "street_trees" / "1904.json"
POST_FROM_CURB_M = 0.38        # a post's centre behind the curb's street face
POST_TRUNK_CLEAR_M = 0.85      # a post's centre off an elm's
POST_ROW_STEP_M = 2.6          # the east curb's row in the 2100-block photograph

# T-3198: every post stands because a picture shows it there. `at`: beside a carriage walk
# (`side` +1 = the walk's north side, -1 its south), `flank` (one each side of the walk), `mid`
# (the lot's middle, no walk), `row` (along the curb across the lot, the walk's mouth kept clear).
SRC_SEARS = "chicagology_1815_sears_two_views"
SRC_2100 = "glessner_blog_2100_block_looking_nw_1890s"
POSTS = [
    {"parcel": "prairie_1815", "at": "beside", "side": 1, "form": "square_domed", "tier": "attested",
     "sources": [SRC_SEARS], "picture": "a18-cgy-1815-sears-two-views",
     "note": "The left print: one square dressed-stone post with a domed cap, on the parkway at the curb, north of the paved crossing to the walk."},
    {"parcel": "prairie_2112", "at": "flank", "form": "round_domed", "tier": "attested",
     "sources": [SRC_2100], "picture": "a20-glessner-2100-block-west-side-1890s",
     "note": "Left foreground: two white round-topped posts at the curb either side of 2112's crossing of the parkway."},
    {"parcel": "prairie_2110", "at": "mid", "form": "round_domed", "tier": "attested",
     "sources": [SRC_2100], "picture": "a20-glessner-2100-block-west-side-1890s",
     "note": "One white round-topped post on the parkway at the curb before 2110 (the Rees house, the museum's arrow)."},
    {"parcel": "prairie_2115", "at": "row", "form": "round_domed", "tier": "inferred",
     "sources": [SRC_2100], "picture": "a20-glessner-2100-block-west-side-1890s",
     "note": "Right foreground: a row of white round-topped posts along the east curb, the camera near 2114-2120 looking north-north-west; which east-side lots the row fronts is read from the camera, not stated."},
    {"parcel": "prairie_2109", "at": "row", "form": "round_domed", "tier": "inferred",
     "sources": [SRC_2100], "picture": "a20-glessner-2100-block-west-side-1890s",
     "note": "The same row continuing north along the east curb toward 21st Street, beyond the carriage."},
]


def seeded(key: str) -> float:
    """A stable number in [0, 1) from a key, so a post's variation never moves between runs."""
    h = 2166136261
    for ch in key.encode():
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return (h % 100003) / 100003.0


def vary(pid: str, form: str) -> dict:
    """One post's own shape: no two posts in the district share all of these."""
    r = [seeded(f"{pid}:{k}") for k in range(6)]
    if form == "square_domed":
        h, w = 0.92 + 0.14 * r[0], 0.24 + 0.05 * r[1]
    else:
        h, w = 0.78 + 0.16 * r[0], 0.22 + 0.06 * r[1]
    return {
        "height_m": round(h, 3), "width_m": round(w, 3),
        "cap": ["dome", "dome_collar", "dome_flat"][int(r[2] * 3)],
        "lean_deg": round(0.4 + 1.6 * r[3], 2), "lean_yaw_deg": round(360 * r[4], 1),
        "yaw_deg": round(-6 + 12 * r[5], 2),
        "tone": round(0.86 + 0.14 * seeded(f"{pid}:tone"), 3),
        "set_m": round(0.03 + 0.06 * seeded(f"{pid}:set"), 3),
    }


def unit(p, q):
    d = math.dist(p, q) or 1.0
    return ((q[0] - p[0]) / d, (q[1] - p[1]) / d)


def street_side(face):
    """The unit vector from the street line out into the street, read off the curb band."""
    line = face["street_line_local_m"]
    a, b = line[0], line[-1]
    t = unit(a, b)
    n = (-t[1], t[0])
    curb = face["bands"]["curb"][0]
    mid = [(curb[0][0] + curb[2][0]) / 2, (curb[0][1] + curb[2][1]) / 2]
    if (mid[0] - a[0]) * n[0] + (mid[1] - a[1]) * n[1] < 0:
        n = (-n[0], -n[1])
    return t, n


def build():
    grid = json.loads(GRID.read_text())
    faces = {f["id"]: f for f in grid["faces"]}
    xs = grid["cross_sections"]
    walks = []
    for p in grid["parcels"]:
        if p["frontage_ft"] < MIN_FRONTAGE_FT:
            continue
        face = faces.get(p.get("street_face"))
        if not face:
            continue
        ends = [v for k, v in p["corners_local_m"].items() if k.endswith("_street")]
        if len(ends) != 2:
            continue
        t, n = street_side(face)
        mid = ((ends[0][0] + ends[1][0]) / 2, (ends[0][1] + ends[1][1]) / 2)
        bands = {b["band"]: b for b in xs[face["cross_section"]]["bands"]}
        walks.append({
            "id": f"{p['id']}.carriage_walk",
            "parcel": p["id"],
            "face": face["id"],
            "at": [round(mid[0], 2), round(mid[1], 2)],
            "along": [round(t[0], 5), round(t[1], 5)],
            "out": [round(n[0], 5), round(n[1], 5)],
            "from_ft": bands["parkway"]["from_ft"],
            "to_ft": bands["curb"]["from_ft"],
            "width_ft": WALK_WIDTH_FT,
        })
    walks.sort(key=lambda w: w["id"])
    posts = lay_posts(grid, faces, xs, {w["parcel"]: w for w in walks})
    return {
        "_doc": ("The 1904 district's street section and carriage walks (T-2474). GENERATED by "
                 "tools/lay_prairie_1904_street_section.py from data/street_grid/1904.json -- do not "
                 "hand-edit; re-run the tool. Local ENU metres of data/datum.json. Read by "
                 "renderers/web/js/street-grid.js; docs/LIBERTIES.md L-prairie-curb-reveal-2474 and "
                 "L-prairie-carriage-walks-2474 are the inventions."),
        "scene": "1904",
        "target_date": "1904-07-01",
        "ticket": "T-2474",
        "generated_by": "tools/lay_prairie_1904_street_section.py",
        "section": {
            "fall": {
                "in_per_3ft": FALL_IN_PER_3FT, "tier": "inferred",
                "sources": ["chicago_revised_municipal_code_1905"],
                "note": ("The 1905 code's grade across the sidewalk space: 'a uniform incline from the street "
                         "line toward the curb line, with a fall of one inch in every three feet'. A city-wide "
                         "rule eight months after the scene date, carried to 1 July 1904."),
            },
            "reveal": {
                "in": REVEAL_IN, "tier": "reconstructed",
                "sources": ["picturesque_chicago_1892_prairie_avenue"],
                "liberty": "L-prairie-curb-reveal-2474",
                "note": ("How far the curb's top stands above the roadway. No source read states it; the "
                         "1887-91 view and the owner's second photograph show a dressed stone curb about one "
                         "stoop riser above the roadway, so 7 in."),
            },
            "road_m": round(-(14.0 * FT * FALL_IN_PER_3FT / 36 + REVEAL_IN * IN), 4),
            "road_note": ("The roadway's level below the field, everywhere: the fall across a 14-ft sidewalk "
                          "space plus the reveal. On 50-ft 16th Street (a 10-ft space) the reveal comes out "
                          "1.3 in higher, so the two roadways meet level."),
        },
        "carriage_walks": {
            "tier": "reconstructed",
            "liberty": "L-prairie-carriage-walks-2474",
            "sources": ["picturesque_chicago_1892_prairie_avenue", "views_of_chicago_1905_prairie_michigan"],
            "min_frontage_ft": MIN_FRONTAGE_FT,
            "width_ft": WALK_WIDTH_FT,
            "note": ("One paved crossing of the parkway, walk to curb, at the middle of every lot at least "
                     "40 ft wide. The pictures show such crossings on these avenues (1815's, 2112's); which "
                     "house had one, and where, is not recorded. The carriage blocks T-2474 stood beside them "
                     "were withdrawn by T-3198: no picture shows one."),
            "walks": walks,
        },
        "carriage_posts": {
            "ticket": "T-3198",
            "liberty": "L-prairie-carriage-walks-2474",
            "from_curb_m": POST_FROM_CURB_M,
            "note": ("Stone posts at the curb, only where a picture shows them; each varied by its own seed. "
                     "Square with a domed cap (1815) or round-topped and painted white (the 2100 block)."),
            "posts": posts,
        },
    }


def lay_posts(grid, faces, xs, walk_of):
    """The pictured carriage posts, at the curb, clear of every walk mouth and elm."""
    trunks = []
    if TREES.exists():
        trunks = [(t["e"], t["n"]) for t in json.loads(TREES.read_text()).get("trees", [])]
    parcels = {p["id"]: p for p in grid["parcels"]}
    out = []
    for spec in POSTS:
        p = parcels[spec["parcel"]]
        face = faces[p["street_face"]]
        t, n = street_side(face)
        bands = {b["band"]: b for b in xs[face["cross_section"]]["bands"]}
        s = bands["curb"]["from_ft"] * FT - POST_FROM_CURB_M
        ends = [v for k, v in p["corners_local_m"].items() if k.endswith("_street")]
        mid = ((ends[0][0] + ends[1][0]) / 2, (ends[0][1] + ends[1][1]) / 2)
        L = math.dist(ends[0], ends[1])
        north = 1 if t[1] >= 0 else -1           # the sign of `along` that runs north
        w = walk_of.get(p["id"])
        half = WALK_WIDTH_FT * FT / 2
        if spec["at"] == "beside":
            ks = [spec["side"] * north * (half + 0.75)]
        elif spec["at"] == "flank":
            ks = [-(half + 0.45), half + 0.45]
        elif spec["at"] == "mid":
            ks = [0.0]
        else:
            m = int((L - 2.0) // POST_ROW_STEP_M)
            ks = [(-m / 2 + i) * POST_ROW_STEP_M for i in range(m + 1)]
            if w:
                ks = [k for k in ks if abs(k) > half + 0.35]
        for i, k in enumerate(ks):
            e = mid[0] + n[0] * s + t[0] * k
            nn = mid[1] + n[1] * s + t[1] * k
            if any(math.dist((e, nn), tr) < POST_TRUNK_CLEAR_M for tr in trunks):
                continue
            pid = f"{p['id']}.post{i + 1}"
            out.append({
                "id": pid, "parcel": p["id"], "face": face["id"],
                "at": [round(e, 2), round(nn, 2)], "along": [round(t[0], 5), round(t[1], 5)],
                "form": spec["form"], **vary(pid, spec["form"]),
                "tier": spec["tier"], "sources": spec["sources"], "picture": spec["picture"],
                "note": spec["note"],
            })
    return out


def dump(doc):
    walks = doc["carriage_walks"].pop("walks")
    posts = doc.pop("carriage_posts")
    head = json.dumps(doc, indent=1, ensure_ascii=False)
    doc["carriage_walks"]["walks"] = walks
    doc["carriage_posts"] = posts
    line = lambda xs: ",\n".join("   " + json.dumps(x, separators=(", ", ": "), ensure_ascii=False) for x in xs)
    # Re-open the carriage_walks object to append its one-walk-per-line list.
    i = head.rindex("}", 0, head.rindex("}"))
    text = head[:i].rstrip() + f',\n  "walks": [\n{line(walks)}\n  ]\n ' + head[i:]
    # Then the posts, the last key, their list one post per line.
    plist = posts.pop("posts")
    phead = json.dumps(posts, indent=1, ensure_ascii=False)
    posts["posts"] = plist
    pbody = "\n".join(" " + ln for ln in phead.splitlines())
    pbody = pbody[:pbody.rindex("}")].rstrip() + f',\n  "posts": [\n{line(plist)}\n  ]\n }}'
    return text[:text.rindex("}")].rstrip() + f',\n "carriage_posts": {pbody.lstrip()}\n}}\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = dump(doc)
    json.loads(text)
    n = len(doc["carriage_walks"]["walks"])
    m = len(doc["carriage_posts"]["posts"])
    if a.check:
        have = OUT.read_text() if OUT.exists() else ""
        if have != text:
            print(f"street section: {OUT.relative_to(ROOT)} is not what the tool writes -- re-run "
                  "python3 tools/lay_prairie_1904_street_section.py")
            return 1
        print(f"street section: {n} carriage walks, {m} carriage posts, as written")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {n} carriage walks, {m} carriage posts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
