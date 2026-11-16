#!/usr/bin/env python3
"""T-3612: the vessels a visitor can watch working and take the helm of, 1812 and 1835.

Kevin, 2026-11-16: "We have those boats in the river that we can ride and cross I would also
like you to have the option to drive the boat on your own and pilot each boat down the river
or in the lake. Also the schooners boats in 1835 we're not realistic they should phot match
correct boats for 1835 with realistic wood and working crews on the boats, which some may be
anchored but others move down and around the river up or down river making a circuit in and
up or out to lake paths, there are 1835 boats but also I would think there could be some
boats correct for 1812 too ... logically with time of day and season on boats and jaunts if
there are boats be reasonable and include them. Would be nice if I can board and pilot the
schooners and all boats".

Writes data/boats/vessels_1835.json and data/boats/vessels_1812.json. Each vessel row is
AUTHORED below (its hull, look, where it lies and what it does); everything else is DERIVED
here and refused if the committed ground will not carry it:

  - the harbour loop the two sailing schooners work, a closed Catmull-Rom curve through the
    authored marks, resampled every 4 m, with its heading and its turn radius;
  - every berth and every route sample checked against the scene's own water (the epoch
    heightfield, the water surface at 0), the navigation obstacles (the pier cribs, the
    bridges, the wharf decks) and the other hulls, each with its own clearance;
  - the navigation rules the pilot (renderers/web/js/boat-pilot.js) reads: the obstacles and
    which craft each one stops, the harbour channel (the cut between the piers, held at a
    working depth: L-vessels-3612) and the depth each kind of hull needs.

    python3 tools/lay_vessels.py          write both files
    python3 tools/lay_vessels.py --check  refuse files that are not what this writes
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = {"1835": DATA / "boats" / "vessels_1835.json", "1812": DATA / "boats" / "vessels_1812.json"}
EPOCH = {"1835": "e1834_harbor_cut", "1812": "e1830_natural"}
DATE = {"1835": "1835-07-01", "1812": "1812-08-14"}
LIBERTY = "L-vessels-3612"
TICKET = "T-3612"
STEP_M = 4.0                 # the loop is resampled this often
UNDER_KEEL_M = 0.15          # water a hull wants under its keel beyond its draft
CHANNEL_DEPTH_M = 0.30       # inside the harbour channel only real water is asked for
CLEAR_OBSTACLE_M = 2.0       # a hull's side to a crib, a deck or a bridge
CLEAR_HULL_M = 3.0           # a hull's side to another's
MIN_TURN_M = 12.0            # the tightest turn the loop may ask of a schooner (she slows for it)

# Depth each kind wants under it to move (its draft and a margin), read by the pilot too.
KINDS = {
    "topsail_schooner": {"draft_m": 1.5, "masted": True, "max_speed_m_s": 3.2, "turn_deg_s": 8.0, "accel": 0.3},
    "mackinaw_boat": {"draft_m": 0.5, "masted": False, "max_speed_m_s": 2.0, "turn_deg_s": 16.0, "accel": 0.35},
    "bateau": {"draft_m": 0.35, "masted": False, "max_speed_m_s": 1.7, "turn_deg_s": 18.0, "accel": 0.35},
    "rowboat": {"draft_m": 0.25, "masted": False, "max_speed_m_s": 1.6, "turn_deg_s": 24.0, "accel": 0.4},
    "bark_canoe": {"draft_m": 0.2, "masted": False, "max_speed_m_s": 1.8, "turn_deg_s": 26.0, "accel": 0.45},
    "dugout": {"draft_m": 0.2, "masted": False, "max_speed_m_s": 1.5, "turn_deg_s": 22.0, "accel": 0.35},
    "skiff": {"draft_m": 0.22, "masted": False, "max_speed_m_s": 1.6, "turn_deg_s": 24.0, "accel": 0.4},
}

# The wind the canvas is trimmed to: a working breeze off the land from the west-north-west,
# which lets a schooner reach out of the river and back in. Ours (L-vessels-3612): no column
# of the scene's papers prints the day's wind.
WIND_FROM_BEARING = 290.0

SCHOONER_HULL = {"length_m": 21.0, "beam_m": 5.8, "draft_m": 1.5, "freeboard_m": 1.2}


# ---------------------------------------------------------------------------------------
# the ground, as terrain.js reads it: the box heightfield, bilinear, and past its edge the
# edge's own height carried out (the apron does the same for the box's skirt)
# ---------------------------------------------------------------------------------------
class Ground:
    def __init__(self, scene: str) -> None:
        d = DATA / "terrain" / "epochs" / EPOCH[scene]
        self.grids = []
        names = ["heightfield.json"] + (["apron_south_branch.json"] if (d / "apron_south_branch.json").exists() else [])
        for name in names:
            meta = json.loads((d / name).read_text())
            raw = (d / meta["bin"]).read_bytes()
            count = meta["rows"] * meta["cols"]
            self.grids.append((meta, struct.unpack(f"<{count}h", raw[: count * 2])))

    @staticmethod
    def _bil(meta, vals, e, n, clamp=False):
        c = (e - meta["origin_e"]) / meta["cell_m"]
        r = (n - meta["origin_n"]) / meta["cell_m"]
        if clamp:
            c = min(max(c, 0.0), meta["cols"] - 1.0001)
            r = min(max(r, 0.0), meta["rows"] - 1.0001)
        c0, r0 = math.floor(c), math.floor(r)
        if c0 < 0 or r0 < 0 or c0 + 1 >= meta["cols"] or r0 + 1 >= meta["rows"]:
            return None
        fc, fr = c - c0, r - r0
        cols, s = meta["cols"], meta["scale"]
        v00 = vals[r0 * cols + c0]; v01 = vals[r0 * cols + c0 + 1]
        v10 = vals[(r0 + 1) * cols + c0]; v11 = vals[(r0 + 1) * cols + c0 + 1]
        return ((v00 * (1 - fc) + v01 * fc) * (1 - fr) + (v10 * (1 - fc) + v11 * fc) * fr) * s + meta["offset"]

    def h(self, e: float, n: float) -> float:
        h = self._bil(*self.grids[0], e, n)
        if h is not None:
            return h
        if len(self.grids) > 1:
            meta = self.grids[1][0]
            cut = meta.get("cut_local_enu_m")
            if cut and cut["e"][0] <= e <= cut["e"][1] and cut["n"][0] <= n <= cut["n"][1]:
                a = self._bil(*self.grids[1], e, n)
                if a is not None:
                    return a
        return self._bil(*self.grids[0], e, n, clamp=True)

    def box(self) -> dict:
        m = self.grids[0][0]
        return {"e": [r2(m["origin_e"]), r2(m["origin_e"] + (m["cols"] - 1) * m["cell_m"])],
                "n": [r2(m["origin_n"]), r2(m["origin_n"] + (m["rows"] - 1) * m["cell_m"])]}

    def depth(self, e: float, n: float) -> float:
        return -self.h(e, n)


# ---------------------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------------------
def r2(v: float) -> float:
    return round(v + 0.0, 2)


def unit(bearing: float) -> tuple[float, float]:
    r = math.radians(bearing)
    return math.sin(r), math.cos(r)


def sidecar_poly(scene: str, sid: str) -> list[tuple[float, float]]:
    s = json.loads((DATA / "sidecars" / scene / f"{sid}.json").read_text())
    pl, fp = s["placement"], s["footprint"]["polygon"]
    th = math.radians(pl.get("rotation_deg", 0.0))
    c, sn = math.cos(th), math.sin(th)
    return [(r2(pl["local_e"] + u * c + v * sn), r2(pl["local_n"] - u * sn + v * c)) for u, v in fp]


def inside(pt, poly) -> bool:
    x, y = pt
    hit = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def seg_dist(p, a, b) -> float:
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(p, poly) -> float:
    if inside(p, poly):
        return 0.0
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def hull_points(e, n, bearing, length, beam, step=2.0):
    """Points along the keel line and both sides at the waterline, for a hull at (e, n)."""
    fx, fy = unit(bearing)
    sx, sy = fy, -fx   # starboard
    out = []
    k = max(2, int(length / step))
    for i in range(k + 1):
        u = -length / 2 + length * i / k
        w = (beam / 2) * math.sin(math.pi * (0.04 + 0.92 * i / k)) ** 0.7
        for v in (-w, 0.0, w):
            out.append((e + fx * u + sx * v, n + fy * u + sy * v))
    return out


def catmull_closed(marks, step):
    """A closed centripetal-ish Catmull-Rom through `marks`, resampled every `step` metres."""
    dense = []
    m = len(marks)
    for i in range(m):
        p0, p1, p2, p3 = marks[(i - 1) % m], marks[i], marks[(i + 1) % m], marks[(i + 2) % m]
        for k in range(40):
            t = k / 40
            t2, t3 = t * t, t * t * t
            dense.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                      + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    dense.append(dense[0])
    cum = [0.0]
    for a, b in zip(dense, dense[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]
    count = max(8, round(total / step))
    out, j = [], 0
    for i in range(count):
        s = total * i / count
        while cum[j + 1] < s:
            j += 1
        f = (s - cum[j]) / max(1e-9, cum[j + 1] - cum[j])
        a, b = dense[j], dense[j + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out, total


def bearing_of(a, b) -> float:
    return (math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360.0) % 360.0


def turn_radius(a, b, c) -> float:
    ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
    cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    return float("inf") if cross < 1e-9 else ab * bc * ca / (2 * cross)


# ---------------------------------------------------------------------------------------
# the authored rows
# ---------------------------------------------------------------------------------------
MJ = "chicago_american_1835_07_04"
MJ_CLAIM = "chicago_american_1835_07_04:c008"
IN_PORT = DATA / "reconstruction" / "1835_vessels_in_port.json"

# The cut between the piers and its approaches, held at a working depth for a schooner. The
# committed heightfield's channel bed is conjectural (its spec says so), and it leaves barely
# a metre over the bar, yet the schooner Illinois came up this channel on 12 July 1834 and the
# Marine Journal enters vessels at the port all summer (1835_vessels_in_port.json,
# `the_reach_they_lay_in`). So inside this polygon real water is all that is asked; outside it
# a hull needs its draft. Ours: L-vessels-3612.
HARBOUR_CHANNEL_1835 = [
    (1040.0, 214.0), (1120.0, 236.0), (1215.0, 236.0), (1332.0, 206.0), (1520.0, 186.0), (1700.0, 176.0),
    (1700.0, 272.0), (1515.0, 262.0), (1246.0, 322.0), (1130.0, 300.0), (1040.0, 266.0),
]

# The marks the loop is drawn through, round the course a sailing schooner works: out of the
# river's wide reach below the bend, down the south side of the cut between the piers, a turn
# north in the open lake, and back in on the north side of the cut to turn in the basin.
HARBOUR_LOOP_MARKS = [
    (912.0, 112.0), (932.0, 96.0), (956.0, 120.0), (980.0, 162.0), (1004.0, 201.0),
    (1050.0, 242.0), (1112.0, 268.0), (1182.0, 272.0), (1262.0, 252.0), (1340.0, 236.0),
    (1420.0, 226.0), (1500.0, 212.0), (1600.0, 202.0), (1720.0, 200.0), (1830.0, 214.0),
    (1890.0, 252.0), (1885.0, 300.0), (1830.0, 326.0), (1730.0, 306.0), (1640.0, 262.0),
    (1545.0, 236.0), (1460.0, 245.0), (1380.0, 262.0), (1300.0, 282.0), (1220.0, 290.0),
    (1142.0, 290.0), (1078.0, 278.0), (1026.0, 242.0), (986.0, 212.0), (956.0, 174.0),
    (928.0, 140.0),
]


def vessels_1835():
    port = {v["id"]: v for v in json.loads(IN_PORT.read_text())["vessels"]}

    def named(pid, extra):
        v = port[pid]
        row = {
            "id": f"vessel_{pid}", "name": v["display_name"], "kind": "topsail_schooner",
            "rig_words": "a two-masted topsail schooner of the lakes",
            "master": v["master"]["surname"],
            "named_on": DATE["1835"],
            "existence": {"confidence": v["confidence"], "sources": v["sources"], "claim_ids": v["claim_ids"],
                          "entries": [e["verbatim"] for e in v["entries"]],
                          "note": "The Marine Journal of the Chicago American of 4 July 1835 enters her at this port across 1 July 1835. Her rig, size, build, colours, berth, crew and day are reconstructed (L-vessels-3612)."},
            "hull": dict(SCHOONER_HULL),
        }
        row.update(extra)
        return row

    rows = [
        named("schr_hiram", {
            "look": {"seed": 11, "topsides": "black", "stripe": "white"},
            "hull": {**SCHOONER_HULL, "length_m": 22.0, "beam_m": 6.0},
            "mode": "moored", "berth": {"e": 760.0, "n": 58.0, "bearing": 85.0},
            "winter": "laid_up", "crew": {"day": 3, "night": 1},
            "doing": "Moored in the reach below the drawbridge, her hands at the hatches: she came in with lumber from Michigan.",
        }),
        named("schr_philips", {
            "look": {"seed": 23, "topsides": "green", "stripe": "yellow"},
            "hull": {**SCHOONER_HULL, "length_m": 20.0, "beam_m": 5.6},
            "mode": "moored", "berth": {"e": 852.0, "n": 68.0, "bearing": 80.0},
            "winter": "absent", "crew": {"day": 3, "night": 1},
            "doing": "Moored in the reach below the drawbridge. The register advertises a Chicago & St. Joseph packet, the Phillips, for freight and passengers.",
        }),
        named("schr_whig", {
            "look": {"seed": 37, "topsides": "black", "stripe": "red"},
            "mode": "moored", "berth": {"e": 470.0, "n": 76.0, "bearing": 95.0},
            "winter": "absent", "crew": {"day": 3, "night": 1},
            "doing": "Lying in the stream off the merchants' landings with merchandize, the Journal says; which landing took it is not recorded.",
        }),
        named("schr_jesse_smith", {
            "look": {"seed": 41, "topsides": "blue", "stripe": "white"},
            "mode": "circuit", "circuit": {"route": "harbour_loop", "rest": "offing"},
            "winter": "laid_up", "winter_berth": {"e": 806.0, "n": 63.0, "bearing": 98.0},
            "crew": {"day": 3, "night": 1},
            "doing": "Cleared on 1 July: under sail between the river and the lake. At nightfall she lies at anchor in the offing.",
        }),
        named("schr_llewelling", {
            "look": {"seed": 53, "topsides": "white", "stripe": "green"},
            "mode": "circuit", "circuit": {"route": "harbour_loop", "rest": "basin"},
            "winter": "absent", "crew": {"day": 3, "night": 1},
            "doing": "The St. Joseph packet: under sail between the river and the lake, in and out again. At nightfall she lies in the basin below the bend.",
        }),
        {
            "id": "vessel_schooner_offing_1835", "name": None, "kind": "topsail_schooner",
            "rig_words": "a two-masted topsail schooner of the lakes",
            "existence": {"confidence": "reconstructed", "sources": ["hubbard_autobiography_1911"],
                          "claim_ids": ["bk_hub_016"],
                          "note": "No column names a vessel lying off the bar on 1 July 1835. Hubbard's editor tells of the brig Illinois lying off Chicago on 25 May 1835, unable to enter, her passengers and cargo carried ashore in Mackinaw boats; this hull stands for the vessels that waited in the offing so. Ours (L-vessels-3612)."},
            "hull": {**SCHOONER_HULL, "length_m": 23.0, "beam_m": 6.2, "draft_m": 1.7},
            "look": {"seed": 67, "topsides": "black", "stripe": "blue"},
            "mode": "anchored", "berth": {"e": 1790.0, "n": 360.0, "bearing": WIND_FROM_BEARING},
            "winter": "absent", "crew": {"day": 2, "night": 1},
            "doing": "At anchor in the offing, her head to the wind, discharging into a Mackinaw boat alongside.",
        },
        {
            "id": "vessel_lighter_offing_1835", "name": None, "kind": "mackinaw_boat",
            "rig_words": "a Mackinaw boat, lightering",
            "existence": {"confidence": "reconstructed", "sources": ["hubbard_autobiography_1911"],
                          "claim_ids": ["bk_hub_016"],
                          "note": "Hubbard's editor: in May 1835 French Canadians carried the brig Illinois's passengers ashore in Mackinaw boats, 'which also lightered the cargo'. This boat and where she lies are ours (L-vessels-3612)."},
            "hull": {"length_m": 11.0, "beam_m": 2.6, "draft_m": 0.5},
            "look": {"seed": 71},
            "laden": True,
            "mode": "alongside", "alongside": "vessel_schooner_offing_1835",
            "winter": "absent", "crew": {"day": 0, "night": 0},
            "doing": "Alongside the schooner in the offing, taking her cargo in for the river.",
        },
    ]
    # The river's rowboats and the fort's bark canoes, where data/boats/era_boats.json lays
    # them (T-0063, L146): drawn now as planked boats and bark that can be taken out.
    era = json.loads((DATA / "boats" / "era_boats.json").read_text())
    for i, b in enumerate(era["boats"]):
        if b["type"] == "schooner":
            continue
        canoe = b["type"] == "bark_canoe"
        e, n = b["position_local_enu_m"]
        rows.append({
            "id": f"vessel_{b['id'][len('boat_'):]}", "name": None, "kind": b["type"],
            "rig_words": "a bark canoe" if canoe else "a rowboat of the river",
            "title": b["name"],
            "from_record": b["id"],
            "existence": {"confidence": b["confidence"], "sources": [],
                          "note": b["note"] + " Its planking (or bark), size and look are reconstructed (L-vessels-3612)."},
            "hull": {"length_m": 6.0, "beam_m": 1.1, "draft_m": 0.2} if canoe else {"length_m": 5.4, "beam_m": 1.6, "draft_m": 0.25},
            "look": {"seed": 300 + i * 7},
            "mode": "beached" if b["state"] == "beached" else "moored",
            "berth": {"e": e, "n": n, "bearing": r2((90.0 - b["heading_deg"]) % 360.0)},
            "winter": "laid_up", "crew": {"day": 0, "night": 0},
            "doing": "Drawn up at the bank." if b["state"] == "beached" else "Moored on the water.",
        })
    return rows


def vessels_1812():
    return [
        {
            "id": "vessel_kinzie_boat_1812", "name": "The Kinzies' boat", "kind": "mackinaw_boat",
            "rig_words": "a Mackinaw boat of the trade",
            "existence": {"confidence": "attested", "sources": ["kinzie_waubun_1856", "moses_kirkland_history_of_chicago_v1"],
                          "note": "Wau-Bun: on the morning of 15 August 1812 Mrs. Kinzie's boat 'had scarcely reached the mouth of the river' when the family were stopped and held there, and on the third day after the battle 'the family of Mr. Kinzie, with the clerks of the establishment, were put into a boat' for St. Joseph. That it is a Mackinaw boat, its size, timber and where it lies on the 14th, made ready below the house, are ours (L-vessels-3612)."},
            "hull": {"length_m": 11.5, "beam_m": 2.7, "draft_m": 0.5},
            "look": {"seed": 1812},
            "laden": True,
            "mode": "moored", "berth": {"e": 1186.0, "n": 291.0, "bearing": 100.0},
            "winter": "laid_up", "crew": {"day": 0, "night": 0},
            "doing": "Made ready below the Kinzie house, laden: the family leaves by water in the morning.",
            # The battle jaunt's river-mouth stop: 'The Kinzie family's boat, warned, waits at
            # this river mouth.' Where in the mouth she lies is ours.
            "dated": [{"from": "1812-08-15", "to": "1812-08-15", "berth": {"e": 1212.0, "n": -425.0, "bearing": 340.0},
                       "doing": "Held at the river's mouth with the family aboard, as Wau-Bun tells it, while the column marches south along the beach."}],
        },
        {
            "id": "vessel_garrison_scow_1812", "name": "The garrison's scow", "kind": "bateau",
            "rig_words": "a flat-bottomed boat of the post",
            "existence": {"confidence": "attested", "sources": ["kinzie_waubun_1856"],
                          "note": "Wau-Bun, of 6 April 1812: Ensign Ronan and five or six soldiers 'ascended the river in a scow, and took the mother, with her infant of scarcely a day old, upon her bed to the boat'. That the post's scow was a flat-bottomed bateau, its size and where it lies by the wharf are ours (L-vessels-3612)."},
            "hull": {"length_m": 9.6, "beam_m": 2.0, "draft_m": 0.35},
            "look": {"seed": 1804},
            "laden": False,
            "mode": "moored", "berth": {"e": 1121.0, "n": 262.0, "bearing": 92.0},
            "winter": "laid_up", "crew": {"day": 0, "night": 0},
            "doing": "Lying off the fort's wharf.",
            # The battle jaunt's Burns stop, 6 April: Ronan's party takes Mrs. Burns 'upon her bed
            # to the boat'. The landing below the house is ours.
            "dated": [{"from": "1812-04-06", "to": "1812-04-06", "berth": {"e": 801.0, "n": 81.0, "bearing": 270.0},
                       "doing": "Brought up the river to the Burns landing by Ensign Ronan's party, to carry Mrs. Burns and her baby down to the fort."}],
        },
    ]


def obstacles(scene: str):
    out = []
    if scene == "1835":
        for sid, kind, stops in [
            ("north_pier", "pier", "all"), ("south_pier", "pier", "all"),
            ("dearborn_street_drawbridge", "drawbridge", "masted"),
            ("north_branch_bridge", "bridge", "masted"),
            ("south_branch_raft_bridge", "raft_bridge", "all"),
        ]:
            out.append({"id": sid, "kind": kind, "stops": stops, "pts": [list(p) for p in sidecar_poly(scene, sid)]})
        lands = json.loads((DATA / "wharves" / "river_landings.json").read_text())
        for w in lands["wharves"]:
            out.append({"id": w["structure_id"], "kind": "wharf", "stops": "all",
                        "pts": [[r2(a), r2(b)] for a, b in w["deck_quad_local_enu_m"]]})
    else:
        out.append({"id": "first_fort_wharf", "kind": "wharf", "stops": "all",
                    "pts": [list(p) for p in sidecar_poly(scene, "first_fort_wharf")]})
    return out


def other_boats(scene: str):
    """The hulls of the other boat layers, as (id, e, n, radius)."""
    out = []
    if scene == "1835":
        era = json.loads((DATA / "boats" / "era_boats.json").read_text())
        for b in era["boats"]:
            if b.get("superseded_by"):
                continue
            e, n = b["position_local_enu_m"]   # pragma: no cover - every era boat is drawn here now
            out.append((b["id"], e, n, 4.0 if b["type"] == "rowboat" else 3.5))
    else:
        cr = json.loads((DATA / "boats" / "crossings_1812.json").read_text())
        for b in cr["boats"]:
            for bank in b["banks"].values():
                out.append((b["id"], bank["rest"]["e"], bank["rest"]["n"], b["hull"]["length_m"] / 2))
    return out


# ---------------------------------------------------------------------------------------
# derive and check
# ---------------------------------------------------------------------------------------
def build(scene: str):
    ground = Ground(scene)
    obs = obstacles(scene)
    others = other_boats(scene)
    rows = vessels_1835() if scene == "1835" else vessels_1812()
    channel = HARBOUR_CHANNEL_1835 if scene == "1835" else []
    problems = []

    def water_ok(pts, draft, label):
        for p in pts:
            d = ground.depth(*p)
            need = CHANNEL_DEPTH_M if channel and inside(p, channel) else draft + UNDER_KEEL_M
            if d < need:
                problems.append(f"{label}: {d:.2f} m of water at ({p[0]:.1f}, {p[1]:.1f}), wants {need:.2f}")
                return False
        return True

    def clear_ok(pts, label, ignore=()):
        for o in obs:
            if o["id"] in ignore:
                continue
            for p in pts:
                if poly_dist(p, [tuple(q) for q in o["pts"]]) < CLEAR_OBSTACLE_M:
                    problems.append(f"{label}: within {CLEAR_OBSTACLE_M} m of {o['id']} at ({p[0]:.1f}, {p[1]:.1f})")
                    return False
        for bid, e, n, rad in others:
            for p in pts:
                if math.hypot(p[0] - e, p[1] - n) < rad + CLEAR_HULL_M:
                    problems.append(f"{label}: within {CLEAR_HULL_M} m of {bid}")
                    return False
        return True

    by_id = {r["id"]: r for r in rows}
    placed = []   # (id, pts) of the hulls at their berths, for the loop's clearance

    for r in rows:
        k = KINDS[r["kind"]]
        r["hull"].setdefault("draft_m", k["draft_m"])
        r["liberty"] = LIBERTY
        L, B, T = r["hull"]["length_m"], r["hull"]["beam_m"], r["hull"]["draft_m"]
        if r["mode"] == "alongside":
            host = by_id[r["alongside"]]
            hb = host["berth"]
            fx, fy = unit(hb["bearing"])
            sx, sy = fy, -fx
            off = host["hull"]["beam_m"] / 2 + 0.6 + B / 2
            r["berth"] = {"e": r2(hb["e"] + sx * off - fx * 2.0), "n": r2(hb["n"] + sy * off - fy * 2.0), "bearing": hb["bearing"]}
        dated = [(f"dated {d['from']}", d["berth"]) for d in r.get("dated", [])]
        for key, b in [(k, r.get(k)) for k in ("berth", "winter_berth")] + dated:
            if not b:
                continue
            pts = hull_points(b["e"], b["n"], b["bearing"], L, B)
            label = f"{r['id']} {key}"
            if r["mode"] != "beached":
                water_ok(pts, T, label)
            clear_ok(pts, label)
            b["depth_m"] = r2(min(ground.depth(*p) for p in hull_points(b["e"], b["n"], b["bearing"], L * 0.8, 0.0)))
            if key == "berth":
                placed.append((r["id"], pts))
        for nid, npts in placed:
            if nid == r["id"] or r.get("alongside") == nid or by_id[nid].get("alongside") == r["id"]:
                continue
            # Two small boats may lie a hand apart, as boats drawn up at one landing do.
            gap = 0.6 if L < 8 and by_id[nid]["hull"]["length_m"] < 8 else CLEAR_HULL_M
            if r.get("berth") and min(math.dist(p, q) for p in hull_points(r["berth"]["e"], r["berth"]["n"], r["berth"]["bearing"], L, B) for q in npts) < gap:
                problems.append(f"{r['id']}: berth within {gap} m of {nid}")

    routes = {}
    if scene == "1835":
        pts, total = catmull_closed(HARBOUR_LOOP_MARKS, STEP_M)
        n = len(pts)
        samples = []
        tightest = float("inf")
        for i, p in enumerate(pts):
            a, c = pts[(i - 1) % n], pts[(i + 1) % n]
            b = bearing_of(a, c)
            rad = turn_radius(pts[(i - 3) % n], p, pts[(i + 3) % n])
            tightest = min(tightest, rad)
            samples.append([r2(p[0]), r2(p[1]), round(b, 1)])
        if tightest < MIN_TURN_M:
            problems.append(f"harbour_loop: a turn of {tightest:.1f} m radius, tighter than {MIN_TURN_M}")
        B = SCHOONER_HULL["beam_m"]
        moored = [(nid, npts) for nid, npts in placed if by_id[nid]["mode"] != "circuit"]
        for i, (e, nn, b) in enumerate(samples):
            sx, sy = unit(b + 90)
            side = [(e + sx * B / 2, nn + sy * B / 2), (e, nn), (e - sx * B / 2, nn - sy * B / 2)]
            fx, fy = unit(b)
            ends = [(e + fx * 10.5, nn + fy * 10.5), (e - fx * 10.5, nn - fy * 10.5)]
            if not water_ok(side + ends, SCHOONER_HULL["draft_m"], f"harbour_loop sample {i}"):
                break
            if not clear_ok(side + ends, f"harbour_loop sample {i}"):
                break
            for nid, npts in moored:
                if min(math.dist(p, q) for p in side + ends for q in npts) < CLEAR_HULL_M:
                    problems.append(f"harbour_loop sample {i}: within {CLEAR_HULL_M} m of {nid}")
                    break
        # Where each sailing vessel rests at nightfall: the basin (the loop's first mark) and
        # the offing (the sample farthest east), so the two keep half a loop apart.
        def nearest(pt):
            return min(range(n), key=lambda i: math.dist(pt, samples[i][:2]))
        rests = {"basin": 0, "offing": max(range(n), key=lambda i: samples[i][0])}
        routes["harbour_loop"] = {
            "closed": True, "length_m": r2(total), "step_m": STEP_M, "rests": rests,
            "tightest_turn_m": r2(tightest),
            "marks": [list(m) for m in HARBOUR_LOOP_MARKS],
            "points": samples,
        }
        for r in rows:
            if r["mode"] == "circuit":
                rest = rests[r["circuit"]["rest"]]
                r["circuit"]["rest_index"] = rest
                r["circuit"]["speed_m_s"] = 2.4
                e, nn, b = samples[rest]
                r["berth"] = {"e": e, "n": nn, "bearing": b, "depth_m": r2(ground.depth(e, nn))}
        del nearest

    nav = {
        "kinds": KINDS,
        "under_keel_m": UNDER_KEEL_M,
        "channel": [[a, b] for a, b in channel],
        "channel_depth_m": CHANNEL_DEPTH_M,
        "obstacles": obs,
        "bounds": {"e": [-700.0, 3400.0], "n": [-3800.0, 2400.0]} if scene == "1835" else {"e": [-700.0, 3400.0], "n": [-3800.0, 1120.0]},
        # The measured box. Past it the browser's terrain answers a flat 0 (no depth at all),
        # so the helm reads the bed as this file was laid against: the box's edge carried out,
        # the open lake at its own edge depth.
        "ground_box": ground.box(),
    }
    counts = {"vessels": len(rows)}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    doc = {
        "_doc": ("GENERATED by tools/lay_vessels.py (T-3612) - do not hand-edit; --check re-derives it. "
                 "The vessels renderers/web/js/vessels.js draws and works (moored, at anchor, under sail round "
                 "the harbour loop) and the navigation rules renderers/web/js/boat-pilot.js steers every boat of "
                 "the scene by. Hulls are built at load by renderers/web/js/vessel-model.js; no texture or model "
                 "file is added. See L-vessels-3612."),
        "id": f"vessels_{scene}", "scene": scene, "target_date": DATE[scene],
        "coordinates": "Local East-North-Up metres from data/datum.json's origin; the water surface is 0. `bearing` is a compass bearing (clockwise from north) of the bow.",
        "liberty": LIBERTY, "ticket": TICKET,
        "wind": {"from_bearing": WIND_FROM_BEARING, "grade": "reconstructed"},
        "sailing_hours": {"from": 6.0, "to": 19.5, "grade": "reconstructed"},
        "counts": counts,
        "vessels": rows,
        "routes": routes,
        "navigation": nav,
    }
    return doc, problems


def dump(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    for scene in ("1835", "1812"):
        doc, problems = build(scene)
        for p in problems:
            print(f"lay_vessels {scene}: {p}", file=sys.stderr)
        bad += len(problems)
        text = dump(doc)
        if args.check:
            have = OUT[scene].read_text() if OUT[scene].exists() else ""
            if have != text:
                print(f"lay_vessels: {OUT[scene].relative_to(ROOT)} is not what tools/lay_vessels.py writes", file=sys.stderr)
                bad += 1
        elif not problems:
            OUT[scene].write_text(text)
    if bad:
        return 1
    print("lay_vessels: " + ", ".join(f"{s} {len(build(s)[0]['vessels'])} vessels" for s in ("1835", "1812"))
          + ("" if args.check else " written"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
