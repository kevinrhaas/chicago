#!/usr/bin/env python3
"""Lay the 1871 city's horse railways: the street tracks and the lines the cars run (T-3806).

    python3 tools/lay_horse_railways_1871.py           # write data/transport/horse_railways_1871.json
    python3 tools/lay_horse_railways_1871.py --check   # the committed file is what this writes

The owner, 2026-11-27 (T-3806): "1871 horse railways: tracks and running horse cars on the State,
Madison, Randolph and North Side lines".

WHAT THE SOURCES SAY (read for this ticket; each section below carries its own citation):

  * Edwards' 1871 directory, "City Railway and Omnibus Routes" (printed p. 53): the Chicago
    [City] horse railway's cars "leave cor. of State and Randolph, via State to 22d, every minute,
    and to Cottage Grove av. and Douglas place every four minutes ... Archer road every eight
    minutes"; the North Chicago Railway's "leave foot of North Water for city limits every twelve
    minutes; for Sedgwick every twelve minutes; for Clybourn av. and Larrabee every twelve
    minutes; for Chicago av. every fifteen minutes", and "leave city limits for Lake every twelve
    minutes"; the West Division Railway's "leave cor. of State and Randolph, along Randolph to
    Robey, every five minutes, and to western limits every five minutes ... westward along
    Madison, every five minutes ... for Blue Island av. every six minutes ... for Milwaukee av.
    every ten minutes ... for Clinton and Jefferson to C. B. & Q. R. R. depot, every twelve
    minutes ... for Clinton south to Van Buren, Van Buren westward to Wood, every fifteen minutes".
  * Andreas, History of Chicago vol. 2 (1885), "City Railways" pp. 119-121: State Street first
    laid "a single track, with turnouts at street crossings" (1859) to Twelfth, then the city
    limits; the Archer road branch from State (1864); the Madison and Randolph lines (1859), sold
    to the West Division company in 1863 "on Randolph and Madison streets, extending to Union
    Park"; Blue Island Avenue "to Twelfth Street by December 22, 1863", Milwaukee (1864), Clinton
    and Jefferson (1864); the North Chicago company's Clark Street line "from North Water Street",
    "laid double to Division Street; beyond that, a single track to Fullerton Avenue", the
    Clybourn Avenue and Chicago Avenue lines (1859), Larrabee from Chicago Avenue (1864); the first
    car from Eaton, Gilbert & Co. of Troy. It quotes the same 1871 timetable.
  * Andreas vol. 3 (1886), "Local Transportation" p. 164: the Wells Street line, "Randolph to
    North Clark", was built in 1875, after the fire, so no Wells Street track is laid here.
  * Colbert and Chamberlin, Chicago and the Great Conflagration (1871), p. 99: the Chicago City
    Railway "laid down rails on State from Lake Street south to the city limits, on Madison west
    ... and on Randolph Street nearly to the city limits", the North Chicago company "on north
    Clark Street from the river to the city limits; also on Larrabee Street and Clybourne Avenue".
  * Sheahan and Upton, The Great Conflagration (1871), p. 54: "The various horse railways had
    their common starting point on State street".

WHAT IS INFERRED OR RECONSTRUCTED. The streets each line runs are attested (above); where a line
starts and turns back downtown, and which sections were double, are stated only for Clark Street,
so: State Street double from Lake to Twenty-second is INFERRED (a car a minute each way cannot run
on one track with turnouts); Randolph and Madison double, every terminal stub and crossover, the
turnouts on the single lines, the gauge (4 ft 8 1/2 in) and the strap rail's look are
RECONSTRUCTED (docs/LIBERTIES.md L-1871-horse-railways-3806). The North Chicago cars cross the
Clark Street bridge to Lake Street on Edwards' "for Lake" (INFERRED). Where the context city's plan
does not carry a street a line ran on (Cottage Grove Avenue, the Little Fort road, Sedgwick north
of Division, Robey and Wood), the track stops where the plan's street does, and the file says so.

WHAT IT READS. data/context/1871.json: the streets' centrelines by name (the plan the city is
drawn on) and the bridge decks' axes. Writes the track centrelines (`rails`) the renderer draws as
strap rail flush with the paving (renderers/web/js/horse-railway-1871.js) and, for the four
double-track lines the cars run, each line's closed run (`loop`: out on the right-hand track, a
crossover and turn back at the far stub, back on the other track) and its timetable.
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "data" / "context" / "1871.json"
OUT = ROOT / "data" / "transport" / "horse_railways_1871.json"
LIBERTY = "L-1871-horse-railways-3806"
TICKET = "T-3806"

GAUGE_M = 1.435          # 4 ft 8 1/2 in, reconstructed
TRACK_HALF_M = 1.32      # double track: each track's centre this far either side of the crown
CORNER_R_M = 12.0        # a horse railway's street-corner curve, reconstructed
CROSSOVER_M = 14.0       # the diagonal of a terminal crossover
STUB_M = 12.0            # where a terminal crossover leaves the stub track (the car stands short of it)
STOP_BACK_M = 7.0        # a car turns back this far inside the end of its track (its horses stand beyond)
TURNOUT_EVERY_M = 420.0  # a passing turnout on a single line, about every fourth block
TURNOUT_LEN_M = 46.0

EDWARDS = {"id": "edwards_chicago_directory_1871", "locator": "City Railway and Omnibus Routes, printed p. 53"}
ANDREAS2 = {"id": "andreas_1885_v2", "locator": "City Railways, pp. 119-121"}
ANDREAS3 = {"id": "andreas_1886_v3", "locator": "Local Transportation, p. 164"}
COLBERT = {"id": "colbert_chamberlin_1871_great_conflagration", "locator": "p. 99"}
SHEAHAN = {"id": "sheahan_upton_1871_great_conflagration", "locator": "p. 54"}

COMPANIES = {
    "ccr": {"name": "Chicago City Railway", "short": "CHICAGO CITY RAILWAY",
            "livery": {"body": "#c9a54a", "panel": "#7a2a1c", "trim": "#2a1a12", "letter": "#e8d8a0"}},
    "wdr": {"name": "Chicago West Division Railway", "short": "WEST DIVISION RAILWAY",
            "livery": {"body": "#d8c79a", "panel": "#2f4a33", "trim": "#1c241c", "letter": "#e9dcae"}},
    "ncr": {"name": "North Chicago City Railway", "short": "NORTH CHICAGO CITY RAILWAY",
            "livery": {"body": "#cfb98a", "panel": "#5a2430", "trim": "#241418", "letter": "#ecdcb2"}},
}
LIVERY_BASIS = ("No source read for this ticket gives the companies' colours. Each company's car is painted in "
                "the manner of the period's Troy-built closed cars (a light body, a darker dash and lower panel, "
                "the company's name on the letter board), one colour per company so the three lines read apart: "
                "reconstructed (L-1871-horse-railways-3806).")

# Each line: legs of (street names, from, to). `from`/`to` name a cross street, or 'end:<w|e|n|s>' for
# the plan street's end that way. Double lines carry cars (`service`).
LINES = [
    {"id": "state_street", "operator": "ccr", "track": "double", "track_grade": "inferred",
     "name": "State Street line, Lake Street to Twenty-second Street",
     "legs": [(["State Street"], "Lake Street", "Twenty-second Street")],
     "route_grade": "attested", "sources": [COLBERT, EDWARDS, ANDREAS2, SHEAHAN],
     "note": "Colbert and Chamberlin: rails 'on State from Lake Street south to the city limits'; Edwards: cars from State and Randolph 'via State to 22d, every minute'. Double track is inferred from the one-minute headway (Andreas: single with turnouts as first laid in 1859).",
     "service": {"headway_s": 60, "board": "STATE ST. — 22D ST.", "terminal_a": "Lake Street", "terminal_b": "Twenty-second Street",
                 "basis": "Edwards' 1871 timetable: a car a minute from State and Randolph to Twenty-second; the cars that ran on to Cottage Grove Avenue and the Archer road share it here. They turn back at the Lake Street end of the track (Colbert's rails 'from Lake Street') and at Twenty-second."}},
    {"id": "state_street_south", "operator": "ccr", "track": "single", "track_grade": "reconstructed",
     "name": "State Street south of Twenty-second, to the city limits",
     "legs": [(["State Street"], "Twenty-second Street", "end:s")],
     "route_grade": "attested", "sources": [ANDREAS2, COLBERT],
     "note": "Andreas: cars to the city limits by June 1859. Single track with turnouts is reconstructed."},
    {"id": "twenty_second_street", "operator": "ccr", "track": "single", "track_grade": "reconstructed",
     "name": "Twenty-second Street, State Street east toward Cottage Grove Avenue",
     "legs": [(["Twenty-second Street"], "State Street", "end:e")],
     "route_grade": "attested", "sources": [ANDREAS2, EDWARDS],
     "note": "Andreas: the track 'extended, on Twenty-second Street and Cottage Grove Avenue' in 1859; Edwards: cars to Cottage Grove av. and Douglas place every four minutes. The context plan does not carry Cottage Grove Avenue, so the track stops at the plan's end of Twenty-second."},
    {"id": "archer_road", "operator": "ccr", "track": "single", "track_grade": "reconstructed",
     "name": "Archer road line, State Street to Bridgeport",
     "legs": [(["Archer Road"], "State Street", "end:w")],
     "route_grade": "attested", "sources": [ANDREAS2, EDWARDS],
     "note": "Andreas: 'a branch track was laid upon the Archer road from State Street' in 1864, completed to Bridgeport; Edwards: Archer road cars every eight minutes."},
    {"id": "randolph_street", "operator": "wdr", "track": "double", "track_grade": "reconstructed",
     "name": "Randolph Street line, State Street to the western limits",
     "legs": [(["Randolph Street"], "State Street", "end:w"), (["bridge:randolph_street_bridge"], "end:e", "end:w"),
              (["West Randolph Street"], "end:e", "end:w")],
     "route_grade": "attested", "sources": [EDWARDS, ANDREAS2, COLBERT],
     "note": "Edwards: cars from State and Randolph 'along Randolph to Robey, every five minutes, and to western limits every five minutes'. The plan does not name Robey Street; the track runs to the plan's end of West Randolph. Double track is reconstructed.",
     "service": {"headway_s": 150, "board": "RANDOLPH ST.", "terminal_a": "State Street", "terminal_b": "the western limits",
                 "basis": "Edwards' 1871 timetable: two services every five minutes, so a car about every two and a half minutes. They turn back at a stub in Randolph Street at State (reconstructed)."}},
    {"id": "madison_street", "operator": "wdr", "track": "double", "track_grade": "reconstructed",
     "name": "Madison Street line, State Street to the western limits",
     "legs": [(["Madison Street"], "State Street", "end:w"), (["bridge:madison_street_bridge"], "end:e", "end:w"),
              (["West Madison Street"], "end:e", "end:w")],
     "route_grade": "attested", "sources": [EDWARDS, ANDREAS2, COLBERT],
     "note": "Edwards: cars 'westward along Madison, every five minutes'; Colbert and Chamberlin: rails 'on Madison west'. How the Madison cars reached State and Randolph is not stated: here they turn back at State Street (reconstructed). Double track is reconstructed.",
     "service": {"headway_s": 300, "board": "MADISON ST.", "terminal_a": "State Street", "terminal_b": "the western limits",
                 "basis": "Edwards' 1871 timetable: every five minutes. They turn back at a stub in Madison Street at State (reconstructed)."}},
    {"id": "blue_island_avenue", "operator": "wdr", "track": "single", "track_grade": "reconstructed",
     "name": "Blue Island Avenue line, to Twelfth Street",
     "legs": [(["Blue Island Avenue"], "end:n", "West Twelfth Street")],
     "route_grade": "attested", "sources": [ANDREAS2, EDWARDS],
     "note": "Andreas: cars 'running to Twelfth Street by December 22, 1863'; Edwards: cars for Blue Island av. every six minutes. How they reached it from Madison or Randolph is not stated and is not drawn."},
    {"id": "milwaukee_avenue", "operator": "wdr", "track": "single", "track_grade": "reconstructed",
     "name": "Milwaukee Avenue line",
     "legs": [(["Milwaukee Avenue"], "end:s", "end:n")],
     "route_grade": "attested", "sources": [ANDREAS2, EDWARDS],
     "note": "Andreas: the Milwaukee line opened June 1864; Edwards: cars every ten minutes. Its extent in 1871 is not stated; the track runs the plan's length of the avenue (reconstructed)."},
    {"id": "clinton_street", "operator": "wdr", "track": "single", "track_grade": "reconstructed",
     "name": "Clinton Street line, Randolph to Van Buren",
     "legs": [(["North Clinton Street", "South Clinton Street"], "West Randolph Street", "West Van Buren Street")],
     "route_grade": "attested", "sources": [EDWARDS, ANDREAS2],
     "note": "Edwards: cars 'for Clinton south to Van Buren, Van Buren westward to Wood' and 'for Clinton and Jefferson to C. B. & Q. R. R. depot'. Where Clinton's track began is not stated: from Randolph here (reconstructed)."},
    {"id": "jefferson_street", "operator": "wdr", "track": "single", "track_grade": "reconstructed",
     "name": "Jefferson Street line, Randolph to Van Buren",
     "legs": [(["North Jefferson Street", "South Jefferson Street"], "West Randolph Street", "West Van Buren Street")],
     "route_grade": "attested", "sources": [EDWARDS, ANDREAS2],
     "note": "Edwards: cars 'for Clinton and Jefferson to C. B. & Q. R. R. depot' every twelve minutes; Andreas: the Clinton and Jefferson lines opened October 1864. The extent is reconstructed."},
    {"id": "van_buren_street", "operator": "wdr", "track": "single", "track_grade": "reconstructed",
     "name": "Van Buren Street line, Clinton westward to Wood",
     "legs": [(["West Van Buren Street"], "South Clinton Street", "e:-2790")],
     "route_grade": "attested", "sources": [EDWARDS],
     "note": "Edwards: 'Van Buren westward to Wood'. The plan does not name Wood Street; the track stops at 1800 west, where Wood Street runs (reconstructed)."},
    {"id": "clark_street", "operator": "ncr", "track": "double", "track_grade": "attested",
     "name": "Clark Street line, Lake Street to Division Street",
     "legs": [(["Clark Street"], "Lake Street", "end:n"), (["bridge:clark_street_bridge"], "end:s", "end:n"),
              (["North Clark Street"], "end:s", "Division Street")],
     "route_grade": "attested", "sources": [ANDREAS2, COLBERT, EDWARDS],
     "note": "Andreas: the North Chicago company's Clark Street line from North Water Street, 'laid double to Division Street'; Colbert and Chamberlin: 'on north Clark Street from the river'. Edwards' cars 'leave city limits for Lake': the run across the Clark Street bridge to Lake Street is inferred from that.",
     "service": {"headway_s": 180, "board": "N. CLARK ST.", "terminal_a": "Lake Street", "terminal_b": "Division Street",
                 "basis": "Edwards' 1871 timetable: cars every twelve minutes to the city limits, to Sedgwick and to Clybourn and Larrabee, and every fifteen to Chicago avenue, all up Clark Street: about one every three minutes. Run here between Lake Street and the end of the double track at Division (the single line beyond carries no car in this scene)."}},
    {"id": "north_clark_street_single", "operator": "ncr", "track": "single", "track_grade": "attested",
     "name": "North Clark Street, Division Street to Fullerton Avenue",
     "legs": [(["North Clark Street"], "Division Street", "Fullerton Avenue")],
     "route_grade": "attested", "sources": [ANDREAS2, COLBERT],
     "note": "Andreas: 'beyond that, a single track to Fullerton Avenue'. The turnouts are reconstructed."},
    {"id": "division_clybourn", "operator": "ncr", "track": "single", "track_grade": "reconstructed",
     "name": "Division Street and Clybourn Avenue line",
     "legs": [(["Division Street"], "North Clark Street", "Clybourn Avenue"), (["Clybourn Avenue"], "Division Street", "end:n")],
     "route_grade": "attested", "sources": [ANDREAS2, COLBERT, EDWARDS],
     "note": "Andreas: 'From Clark Street west, on Division, to Clybourn Avenue, and thence on Clybourn Avenue to city limits', completed 1859."},
    {"id": "chicago_avenue", "operator": "ncr", "track": "single", "track_grade": "reconstructed",
     "name": "Chicago Avenue line, Clark Street to the North Branch",
     "legs": [(["Chicago Avenue"], "North Clark Street", "end:w")],
     "route_grade": "attested", "sources": [ANDREAS2, EDWARDS],
     "note": "Andreas: 'West on Chicago Avenue ... to the North Branch', completed 1859; Edwards: cars for Chicago av. every fifteen minutes. Authorized from Rush Street; built from Clark here (reconstructed)."},
    {"id": "larrabee_street", "operator": "ncr", "track": "single", "track_grade": "reconstructed",
     "name": "Larrabee Street line, north from Chicago Avenue",
     "legs": [(["Larrabee Street"], "Chicago Avenue", "end:n")],
     "route_grade": "attested", "sources": [ANDREAS2, EDWARDS, COLBERT],
     "note": "Andreas: 'a single, or double, track on Larrabee Street, from Chicago Avenue to Little Fort road' (1864); Edwards: cars from 'corner Larrabee and Center'. The plan carries Larrabee only to Division Street, where the track stops."},
]
NOT_LAID = [
    {"line": "Wells Street", "why": "Andreas vol. 3 p. 164: 'two and one-fifth miles of double track on Wells Street from Randolph to North Clark, by November, 1875' was built after the fire.", "sources": [ANDREAS3]},
    {"line": "Sedgwick Street", "why": "Edwards: cars 'for Sedgwick' and from 'cor. N. av. and Sedgwick'; Andreas: the Sedgwick line of 1861. The context plan carries Sedgwick Street only south of Division, so the line north of Division is not drawn.", "sources": [EDWARDS, ANDREAS2]},
    {"line": "Cottage Grove Avenue", "why": "Not on the context plan; Twenty-second Street's track stops at the plan's end.", "sources": [ANDREAS2]},
    {"line": "Clark Street south of Lake", "why": "Andreas pp. 120: the company deferred Clark Street for ten years from 1860, the Michigan Southern holding it below Harrison; no line is in the 1871 timetable.", "sources": [ANDREAS2]},
]
FIRE = {
    "service_hours": [5.5, 24.0],
    "service_hours_basis": "No source read gives the 1871 hours of service; the cars run from half past five in the morning to midnight (reconstructed).",
    "fire_stop": "1871-10-08T22:00",
    "fire_basis": ("On the night of the fire no car runs from ten o'clock Sunday night, and none on the Monday. Andreas vol. 2 p. 706, of "
                   "the Saturday night's fire on the West Side: in Clinton Street near Adams 'were half a dozen isolated street-cars, utterly "
                   "unable to get back to their stables' for the crowd; p. 747: on the Monday 'the street cars, which had been run up there "
                   "for safety' stood at Graceland; p. 753 and Colbert and Chamberlin p. 389: after the fire the rails of Clark Street were "
                   "'warped and twisted ... forced up ... two feet above the ground'. The hour the service stopped on Sunday night is reconstructed."),
    "fire_sources": [{"id": "andreas_1885_v2", "locator": "The Burning of Chicago, pp. 706, 747, 753"},
                     {"id": "colbert_chamberlin_1871_great_conflagration", "locator": "p. 389"}],
}
CAR = {
    "body_m": 4.88, "platform_m": 1.0, "width_m": 2.13, "floor_m": 0.82, "eaves_m": 2.95, "roof_m": 3.35,
    "wheel_d_m": 0.76, "wheelbase_m": 1.9, "windows": 7, "speed_m_s": 2.35, "dwell_s": 45,
    "horses": 2, "horse_ahead_m": 5.1, "horse_half_spacing_m": 0.36,
    "basis": ("A closed four-wheel horse car of the 1860s of the Troy builders' pattern (Andreas: the first car came from Eaton, Gilbert & Co. "
              "of Troy): a body about sixteen feet long with open platforms and dashboards at both ends, a clerestory roof with a row of deck "
              "lights, seven windows a side, the company's name on the letter board, on two axles. Its dimensions, the pair of horses, the "
              "driver standing on the front platform and the conductor on the back one, and its pace of about five miles an hour are "
              "reconstructed (L-1871-horse-railways-3806)."),
}


def r2(v):
    return round(v, 2)


def load_plan():
    ctx = json.loads(CONTEXT.read_text())
    by = {}
    for s in ctx["streets"]:
        if s.get("name"):
            by.setdefault(s["name"], []).append((tuple(s["a"]), tuple(s["b"])))
    for d in ctx["walk_decks"]:
        if d.get("kind") == "bridge" and d.get("axis_endpoints"):
            a, b = d["axis_endpoints"]
            by[f"bridge:{d['id']}"] = [(tuple(a), tuple(b))]
    return by


def seg_closest(p, a, b):
    de, dn = b[0] - a[0], b[1] - a[1]
    L2 = de * de + dn * dn or 1e-9
    t = max(0.0, min(1.0, ((p[0] - a[0]) * de + (p[1] - a[1]) * dn) / L2))
    q = (a[0] + de * t, a[1] + dn * t)
    return q, math.hypot(p[0] - q[0], p[1] - q[1])


def seg_intersect(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1]); s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-9:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if -1e-6 <= t <= 1 + 1e-6 and -1e-6 <= u <= 1 + 1e-6:
        return (a[0] + r[0] * t, a[1] + r[1] * t)
    return None


def crossing(segs, other, tol=40.0):
    """Where the leg's street meets `other`: a true crossing, else the nearest approach of
    `other`'s points to the leg (a street that ends at it), within tol."""
    for a, b in segs:
        for c, d in other:
            x = seg_intersect(a, b, c, d)
            if x:
                return x
    best = None
    for c, d in other:
        for p in (c, d):
            for a, b in segs:
                q, dist = seg_closest(p, a, b)
                if dist <= tol and (best is None or dist < best[1]):
                    best = (q, dist)
    if best is None:
        raise SystemExit(f"lay_horse_railways_1871: no crossing within {tol} m")
    return best[0]


def chain(segs):
    """The street's segments as a graph (endpoints joined within 1.5 m)."""
    nodes, edges = [], {}

    def node(p):
        for i, q in enumerate(nodes):
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 1.5:
                return i
        nodes.append(p); edges[len(nodes) - 1] = []
        return len(nodes) - 1
    for a, b in segs:
        i, j = node(a), node(b)
        if i != j:
            w = math.hypot(a[0] - b[0], a[1] - b[1])
            edges[i].append((j, w)); edges[j].append((i, w))
    # The plan's runs of one street do not always meet end to end (a junction re-laid, a
    # mapped run beside a platted one): a loose end is joined to the nearest node within 30 m.
    for i in range(len(nodes)):
        if len(edges[i]) > 1:
            continue
        near = set(j for j, _ in edges[i]) | {i}
        best = None
        for j, q in enumerate(nodes):
            if j in near:
                continue
            d = math.hypot(nodes[i][0] - q[0], nodes[i][1] - q[1])
            if d < 30 and (best is None or d < best[0]):
                best = (d, j)
        if best:
            edges[i].append((best[1], best[0])); edges[best[1]].append((i, best[0]))
    # Pieces still apart (a run the plan breaks at a park or a railway) are joined at their
    # nearest pair of nodes, within 600 m.
    while True:
        comp, k = {}, 0
        for i in range(len(nodes)):
            if i in comp:
                continue
            st = [i]
            while st:
                u = st.pop()
                if u in comp:
                    continue
                comp[u] = k
                st += [v for v, _ in edges[u]]
            k += 1
        if k < 2:
            break
        best = None
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if comp[i] != comp[j]:
                    d = math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1])
                    if best is None or d < best[0]:
                        best = (d, i, j)
        if best[0] > 600:
            break
        _, i, j = best
        edges[i].append((j, best[0])); edges[j].append((i, best[0]))
    return nodes, edges


def path_between(segs, x1, x2):
    nodes, edges = chain(segs)

    def nearest_seg(x):
        best = None
        for a, b in segs:
            q, d = seg_closest(x, a, b)
            if best is None or d < best[0]:
                best = (d, a, b)
        return best[1], best[2]
    a1, b1 = nearest_seg(x1); a2, b2 = nearest_seg(x2)
    idx = lambda p: min(range(len(nodes)), key=lambda i: math.hypot(nodes[i][0] - p[0], nodes[i][1] - p[1]))
    starts = {idx(a1), idx(b1)}; goals = {idx(a2), idx(b2)}
    best = None
    for s in starts:
        dist = {s: 0.0}; prev = {}; pq = [(0.0, s)]
        while pq:
            dd, u = heapq.heappop(pq)
            if dd > dist.get(u, 1e18):
                continue
            for v, w in edges[u]:
                nd = dd + w
                if nd < dist.get(v, 1e18):
                    dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
        for g in goals:
            if g in dist:
                pts = [g]
                while pts[-1] != s:
                    pts.append(prev[pts[-1]])
                pts.reverse()
                cost = dist[g] + math.hypot(nodes[s][0] - x1[0], nodes[s][1] - x1[1]) + math.hypot(nodes[g][0] - x2[0], nodes[g][1] - x2[1])
                if best is None or cost < best[0]:
                    best = (cost, [nodes[i] for i in pts])
    if best is None:
        raise SystemExit("lay_horse_railways_1871: no path along the street")
    pts = best[1]
    out = [x1]
    for p in pts:
        out.append(p)
    out.append(x2)
    # drop a first/last node that lies behind the cut point
    def behind(c, p, q):  # p lies between c and q's far side? keep only if c->p goes the way c->q goes
        return (p[0] - c[0]) * (q[0] - c[0]) + (p[1] - c[1]) * (q[1] - c[1]) < 0 or math.hypot(p[0] - c[0], p[1] - c[1]) < 0.5
    while len(out) > 2 and behind(out[0], out[1], out[2]):
        out.pop(1)
    while len(out) > 2 and behind(out[-1], out[-2], out[-3]):
        out.pop(-2)
    return out


def end_point(segs, way):
    pts = [p for s in segs for p in s]
    key = {"w": lambda p: p[0], "e": lambda p: -p[0], "s": lambda p: p[1], "n": lambda p: -p[1]}[way]
    return min(pts, key=key)


def leg_points(plan, names, frm, to, prev_end):
    segs = [s for nm in names for s in plan.get(nm, [])]
    if not segs:
        raise SystemExit(f"lay_horse_railways_1871: the plan has no {names}")

    def where(spec, first):
        if spec.startswith("end:"):
            p = end_point(segs, spec[4:])
            if first and prev_end is not None:
                # the leg continues the last one: start from its own end nearest the last point
                ends = [p for s in segs for p in s]
                p = min(ends, key=lambda q: math.hypot(q[0] - prev_end[0], q[1] - prev_end[1]))
            return p
        if spec.startswith("e:"):
            e = float(spec[2:])
            hits = [seg_intersect(a, b, (e, -1e5), (e, 1e5)) for a, b in segs]
            hits = [h for h in hits if h]
            if not hits:
                raise SystemExit(f"lay_horse_railways_1871: {names} does not reach e={e}")
            return hits[0]
        other = [s for nm in [spec] for s in plan.get(nm, [])]
        if not other:
            raise SystemExit(f"lay_horse_railways_1871: the plan has no {spec}")
        return crossing(segs, other)
    x1, x2 = where(frm, True), where(to, False)
    return path_between(segs, x1, x2)


def simplify(pts, tol=0.08):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, p, b = out[-1], pts[i], pts[i + 1]
        q, d = seg_closest(p, a, b)
        if d > tol:
            out.append(p)
    out.append(pts[-1])
    # drop near-duplicates
    res = [out[0]]
    for p in out[1:]:
        if math.hypot(p[0] - res[-1][0], p[1] - res[-1][1]) > 0.3:
            res.append(p)
    if len(res) == 1:
        res.append(out[-1])
    return res


def fillet(pts, R=CORNER_R_M, min_deg=12.0):
    """Round each corner sharper than min_deg with an arc of radius R (cut back to fit)."""
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, p, b = pts[i - 1], pts[i], pts[i + 1]
        d1 = (p[0] - a[0], p[1] - a[1]); d2 = (b[0] - p[0], b[1] - p[1])
        L1, L2 = math.hypot(*d1), math.hypot(*d2)
        u1 = (d1[0] / L1, d1[1] / L1); u2 = (d2[0] / L2, d2[1] / L2)
        turn = math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])
        if abs(math.degrees(turn)) < min_deg:
            out.append(p); continue
        t = R * math.tan(abs(turn) / 2)
        t = min(t, L1 * 0.45, L2 * 0.45)
        r = t / math.tan(abs(turn) / 2)
        s = (p[0] - u1[0] * t, p[1] - u1[1] * t)
        sign = 1 if turn > 0 else -1  # left turn: centre to the left
        c = (s[0] - u1[1] * r * sign, s[1] + u1[0] * r * sign)
        a0 = math.atan2(s[1] - c[1], s[0] - c[0])
        n = max(3, int(abs(turn) / math.radians(7)))
        for k in range(n + 1):
            ang = a0 + turn * k / n
            out.append((c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)))
    out.append(pts[-1])
    return out


def offset(pts, h):
    """The polyline moved h to the right of its direction (negative: left), mitred."""
    out = []
    n = len(pts)
    for i in range(n):
        if i == 0:
            d = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
        elif i == n - 1:
            d = (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
        else:
            d1 = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); L1 = math.hypot(*d1)
            d2 = (pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); L2 = math.hypot(*d2)
            u1 = (d1[0] / L1, d1[1] / L1); u2 = (d2[0] / L2, d2[1] / L2)
            m = (u1[0] + u2[0], u1[1] + u2[1]); Lm = math.hypot(*m) or 1e-9
            m = (m[0] / Lm, m[1] / Lm)
            cos = max(0.5, m[0] * u1[0] + m[1] * u1[1])
            rt = (m[1], -m[0])
            out.append((pts[i][0] + rt[0] * h / cos, pts[i][1] + rt[1] * h / cos)); continue
        L = math.hypot(*d); rt = (d[1] / L, -d[0] / L)
        out.append((pts[i][0] + rt[0] * h, pts[i][1] + rt[1] * h))
    return out


def cum(pts):
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return c


def at(pts, c, s):
    s = max(0.0, min(c[-1], s))
    for i in range(1, len(pts)):
        if c[i] >= s:
            f = (s - c[i - 1]) / ((c[i] - c[i - 1]) or 1e-9)
            return (pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f)
    return pts[-1]


def cut(pts, c, s0, s1):
    out = [at(pts, c, s0)]
    for i, p in enumerate(pts):
        if s0 < c[i] < s1:
            out.append(p)
    out.append(at(pts, c, s1))
    return out


def rnd(pts):
    return [[r2(p[0]), r2(p[1])] for p in pts]


def build():
    plan = load_plan()
    rails, sections, services = [], [], []
    for line in LINES:
        pts, prev = [], None
        for names, frm, to in line["legs"]:
            leg = leg_points(plan, names, frm, to, prev)
            if pts and math.hypot(leg[0][0] - pts[-1][0], leg[0][1] - pts[-1][1]) < 0.3:
                leg = leg[1:]
            pts += leg
            prev = pts[-1]
        centre = fillet(simplify(pts))
        c = cum(centre)
        sec = {"id": line["id"], "operator": line["operator"], "name": line["name"], "track": line["track"],
               "route_grade": line["route_grade"], "track_grade": line["track_grade"],
               "streets": [n for names, _, _ in line["legs"] for n in names if not n.startswith("bridge:")],
               "length_m": round(c[-1], 1), "sources": line["sources"], "note": line["note"]}
        sections.append(sec)
        if line["track"] == "double":
            right, left = offset(centre, TRACK_HALF_M), offset(centre, -TRACK_HALF_M)
            rails.append({"section": line["id"], "pts": rnd(right)})
            rails.append({"section": line["id"], "pts": rnd(left)})
            cr, cl = cum(right), cum(left)
            L = c[-1]
            # terminal crossovers: at A from the left (inbound) track to the right; at B from the right to the left
            xa = [at(left, cl, STUB_M), at(right, cr, STUB_M + CROSSOVER_M)]
            xb = [at(right, cr, L - STUB_M), at(left, cl, L - STUB_M - CROSSOVER_M)]
            rails.append({"section": line["id"], "pts": rnd(xa), "crossover": True})
            rails.append({"section": line["id"], "pts": rnd(xb), "crossover": True})
            if "service" in line:
                sv = line["service"]
                s0, s1 = STOP_BACK_M, L - STOP_BACK_M
                # out: from the stub end on the inbound (left) track, back through the crossover, out on the right
                out = [at(left, cl, s0)] + cut(left, cl, s0, STUB_M)[1:] + cut(right, cr, STUB_M + CROSSOVER_M, s1)
                back_r = cut(right, cr, L - STUB_M, s1)  # from the far stub (s1) back to the crossover start, reversed below
                back = list(reversed(back_r)) if False else None
                # back: from the far stub end on the right track (s1) back along it to the crossover, over to the left track, home
                seg1 = list(reversed(cut(right, cr, L - STUB_M, s1)))
                seg2 = list(reversed(cut(left, cl, s0, L - STUB_M - CROSSOVER_M)))
                back = seg1 + seg2
                loop = simplify(out, 0.02)[:-1] + simplify(back, 0.02)
                cl_loop = cum(loop)
                services.append({"id": line["id"], "operator": line["operator"], "section": line["id"],
                                 "board": sv["board"], "terminal_a": sv["terminal_a"], "terminal_b": sv["terminal_b"],
                                 "headway_s": sv["headway_s"], "basis": sv["basis"], "grade": "reconstructed",
                                 "loop": rnd(loop), "cusp_m": [0.0, round(cum(simplify(out, 0.02))[-1], 2)],
                                 "length_m": round(cl_loop[-1] + math.hypot(loop[-1][0] - loop[0][0], loop[-1][1] - loop[0][1]), 2),
                                 "sources": [EDWARDS] + [s for s in line["sources"] if s is not EDWARDS]})
        else:
            # single track with passing turnouts about every fourth block
            L = c[-1]
            n = int(L // TURNOUT_EVERY_M)
            marks = [TURNOUT_EVERY_M * (k + 0.5) for k in range(n) if TURNOUT_EVERY_M * (k + 0.5) + TURNOUT_LEN_M < L - 20]
            s = 0.0
            for m in marks:
                rails.append({"section": line["id"], "pts": rnd(cut(centre, c, s, m))})
                for h in (TRACK_HALF_M, -TRACK_HALF_M):
                    side = offset(centre, h); cs = cum(side)
                    mid = cut(side, cs, m + 12, m + TURNOUT_LEN_M - 12)
                    rails.append({"section": line["id"], "pts": rnd([at(centre, c, m)] + mid + [at(centre, c, m + TURNOUT_LEN_M)]), "turnout": True})
                s = m + TURNOUT_LEN_M
            rails.append({"section": line["id"], "pts": rnd(cut(centre, c, s, L))})
    return {
        "format": "chicago4d_horse_railways_1871_v1", "ticket": TICKET, "scene": "1871",
        "generated_by": "tools/lay_horse_railways_1871.py", "liberty": LIBERTY,
        "doc": ("The 1871 city's horse railways (T-3806): the track centrelines (`rails`; the renderer lays two strap rails "
                "on each, flush with the paving) on every street a source gives a line, and the four double-track lines the cars "
                "run (`services`), each a closed run out on the right-hand track and back on the other with a crossover at each "
                "stub, and a car every `headway_s`. Each section cites its sources; the grades are the route's (where the line ran) "
                "and the track's (single or double, and the turnouts)."),
        "corridor_line": "drawn",
        "corridor_line_why": "The tracks lie on the context city's drawn street centrelines (data/context/1871.json streets), the lines the roadway ribbons are laid on.",
        "gauge_m": GAUGE_M, "gauge_grade": "reconstructed",
        "gauge_basis": "No source read gives the Chicago companies' gauge; 4 ft 8 1/2 in, the gauge of the Troy-built cars' eastern street railways, is reconstructed.",
        "rail": {"kind": "strap rail on longitudinal timbers, flush with the paving", "head_m": 0.065, "grade": "reconstructed",
                 "basis": "Andreas vol. 2 p. 121: on Clark Street 'the first railway was laid, by spiking the rails to the planks, an additional thickness of plank being placed in the horse-path'; the flat rail's width and colour are reconstructed."},
        "track_half_spacing_m": TRACK_HALF_M,
        "companies": COMPANIES, "livery_grade": "reconstructed", "livery_basis": LIVERY_BASIS,
        "car": CAR, "hours": FIRE, "sections": sections, "not_laid": NOT_LAID,
        "services": services, "rails": rails,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print("lay_horse_railways_1871: data/transport/horse_railways_1871.json differs; run python3 tools/lay_horse_railways_1871.py", file=sys.stderr)
            return 1
        print(f"lay_horse_railways_1871: {len(doc['sections'])} sections, {len(doc['services'])} services current")
        return 0
    OUT.write_text(text)
    tot = sum(s["length_m"] for s in doc["sections"])
    print(f"lay_horse_railways_1871: {len(doc['sections'])} sections ({tot / 1000:.1f} km), {len(doc['rails'])} rails, {len(doc['services'])} services")
    for s in doc["sections"]:
        print(f"  {s['id']}: {s['length_m']} m ({s['track']})")
    for s in doc["services"]:
        print(f"  service {s['id']}: loop {s['length_m']} m, every {s['headway_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
