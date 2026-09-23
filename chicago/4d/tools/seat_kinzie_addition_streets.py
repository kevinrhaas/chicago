#!/usr/bin/env python3
"""Seat the Kinzie's Addition street module on the committed town grid.

    tools/seat_kinzie_addition_streets.py            print what it would write
    tools/seat_kinzie_addition_streets.py --write    write data/streets/1835.json

The reading is `data/traces/kinzie_addition_street_grid.json` and it is not
repeated here: this tool takes the MODULE out of that file — the tier pitch, the
column pitch, the corridor width and the extents — and lays it off the two
committed streets the Addition shares with the town, Michigan Street
(`michigan_north`) and Wolcott Street (`wolcott`).

WHY NOT JUST COMMIT THE PIXELS. Because the same street would then stand in two
places. Wright's Michigan Street, read through the NA sheet's own affine, lands
19.8 m south of `michigan_north`, and `michigan_north` is Wright's Michigan
Street. The 19.8 m is the fit's, not the plat's: 16.19 m of RMS residual on eight
control points, and a drawn bearing about 1.2 deg off the one the committed grid
takes from modern control over a baseline four times longer. So the sheet is
asked for what it measures well — the distance from one ruled line to the next,
inside one corner of one raster — and the committed grid is asked for where that
ladder hangs.

Every new line is therefore PARALLEL to the committed street of its own family
and OFFSET from it by a whole number of measured modules. Nothing here is fitted
to modern pavement and nothing is chosen to look right.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STREETS = ROOT / "data/streets/1835.json"
TRACE = ROOT / "data/traces/kinzie_addition_street_grid.json"

# North of Michigan Street, in order; the number is the tier count.
EAST_WEST = [
    ("illinois_north", 1, "Illinois Street", "E Illinois Street",
     "the modern crossing the registration's G6 control point stands on is Illinois "
     "Street, so the name survives"),
    ("indiana_north", 2, "Indiana Street", None, None),
    ("ohio_north", 3, "Ohio Street", "E Ohio Street",
     "the modern crossings of the registration's G2 and G7 control points are both "
     "Ohio Street, so the name survives"),
    ("ontario_north", 4, "Ontario Street", None, None),
    ("erie_north", 5, "Erie Street", None, None),
    ("huron_north", 6, "Huron Street", None, None),
    ("superior_north", 7, "Superior Street", None, None),
]
# East of Wolcott Street, in order.
NORTH_SOUTH = [
    ("cass", 1, "Cass Street", "N Wabash Avenue",
     "the registration's G6 feature note: 'Cass is today's North Wabash Avenue'"),
    ("rush", 2, "Rush Street", "N Rush Street",
     "the modern crossing the registration's G7 control point stands on is Rush "
     "Street, so the name survives"),
    ("pine", 3, "Pine Street", None, None),
    ("sand", 4, "Sand Street", None, None),
]
# The north end of each north-south street, from the reading's `extent` block.
NS_TOP = {"cass": 7, "rush": 7, "pine": 7, "sand": 6}   # tier index of the last street it meets
# The east end of each east-west street: the last north-south street present at its tier.
EW_RIGHT = {"illinois_north": 4, "indiana_north": 4, "ohio_north": 4, "ontario_north": 4,
            "erie_north": 4, "huron_north": 4, "superior_north": 3}

NAME_NOTE = ("`name_2026` is null because no source in this repository attests what this "
             "street is called today. A modern name is not evidence about 1835 and is not "
             "guessed at here; `osm_streets_2026` would settle it and has not been asked.")

NOTE = (
    "Kinzie's Addition, surveyed 1833 and drawn complete on J. S. Wright's 1834 survey. "
    "GEOMETRY: the plat's module is measured off the sheet by "
    "tools/read_kinzie_addition_streets.py and recorded in "
    "data/traces/kinzie_addition_street_grid.json — {pitch} m from one {fam} corridor to "
    "the next (sd {sd} m over {n} spacings), read as ink projected onto one axis, not "
    "picked by eye. The line itself is that module laid off {datum}, parallel to it, "
    "because the sheet's own fit puts Wright's Michigan Street 19.8 m south of "
    "`michigan_north`, which is the same street: the sheet measures the ladder and the "
    "committed grid holds it. CORRIDOR: {corr} m. That is not the raw read. The method "
    "reads the Original Town's platted 80 ft corridors on the same sheet at 83.6 ft "
    "(three readings, sd 5.2), and the Addition's corridors at 75.1 ft (24 readings, sd "
    "4.9); the Addition's are 0.898 of the Original Town's, which against a platted 80 ft "
    "is 71.9 ft. So Wright's drafting does say the Addition's streets are narrower than "
    "the town's, by about a tenth — and it does not resolve onto a round platted figure: "
    "66 ft is outside the reading and so is 80 ft. The deed of the Addition would settle "
    "it and is not in the corpus. STATUS follows `madison`'s: platted ground, not road. "
    "In 1835 this tract is a survey over prairie — `track_width_m` is 0 because no wagon "
    "track is drawn or attested on it, `alleys` is false because the sheet rules none "
    "inside these blocks, and the confidences say `inferred` for the same reason "
    "`madison` does: the line is read off Wright's sheet as a ruled line and anchored on "
    "committed control, not traced from a plat this project holds. EXTENT is the "
    "reading's, and it stops where the reading stops: Wright carries these streets east "
    "of Sand Street over the shore-cut blocks to the lake, and that reach waits on the "
    "shore trace (T-0799, T-0800); the river tier south of Michigan Street and its water "
    "lots wait on T-1063. T-1060, piece 1 of T-0789."
)


def _render(entry, indent=4):
    """One street object, in the style the file is already written in: one key per
    line, and any array that holds no object on a single line."""
    text = json.dumps(entry, indent=2, ensure_ascii=False)
    def collapse(m):
        return re.sub(r"\s*\n\s*", " ", m.group(0)).replace("[ ", "[").replace(" ]", "]")
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\[[^\[\]{}]*\]", collapse, text)
    pad = " " * indent
    return "\n".join(pad + ln for ln in text.split("\n"))


def _entry_spans(text):
    """`(id, start, end)` for every object in the `streets` array, found by scanning
    braces rather than by matching the file's style: one committed entry
    (`fort_bank_track`) is indented unlike the other seventy-six and a shape regex
    walks straight past it."""
    i = text.index("[", text.index('"streets"'))
    spans, depth, start, in_str, esc = [], 0, None, False, False
    for j in range(i, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
            if depth == 1:
                start = j
        elif ch == "}":
            depth -= 1
            if depth == 0:
                spans.append((json.loads(text[start:j + 1])["id"], start, j + 1))
        elif ch == "]" and depth == 0:
            break
    return spans


def _reseat(text, entries):
    """Re-point streets this tool has ALREADY committed, in place, on the same argument
    _splice makes for appending: the entry is re-rendered, the rest of the file is not
    touched, and the diff is the lines that moved.

    Until T-1092 a seating tool could only append. That was enough while the
    registration never changed; when T-1091 put the eleven-point fit in force, every
    line these tools had seated through the old one stayed where it was and the tools'
    own --check went red against them. Re-running the generator is how this project
    moves a derived line, so the generator has to be able to."""
    at = {sid: (s, e) for sid, s, e in _entry_spans(text)}
    for entry in sorted(entries, key=lambda e: at[e["id"]][0], reverse=True):
        s, e = at[entry["id"]]
        text = text[:s] + _render(entry).lstrip() + text[e:]
    return text


def _splice(text, entries, edits):
    """Put the new streets at the end of the array and re-point the two carried ends,
    WITHOUT re-serialising the file.

    data/streets/1835.json is 40 hand-tended entries whose notes run to three
    thousand characters, and a writer that re-emits the whole document changes a
    thousand lines of escaping and indentation to add eleven streets. A reader
    cannot see the change in that, and a reviewer should not have to."""
    for ident, path in edits:
        pat = re.compile(r'("id": "' + ident + r'",.*?"path_local_enu_m": )(\[\[.*?\]\])', re.S)
        if not pat.search(text):
            raise SystemExit(f"{ident} has no inline path_local_enu_m to carry")
        text = pat.sub(lambda m: m.group(1) + json.dumps(path), text, count=1)
    if not entries:
        # A SECOND `--write` HAS NOTHING TO APPEND, and used to leave a trailing comma
        # behind that made data/streets/1835.json unparseable — seat_wabansia_streets.py
        # hit this under T-1086 and guarded it there; T-1092, which re-runs every seating
        # tool on the adopted registration, hit the same thing here.
        return text
    tail = re.compile(r'\n  \]\n\}\s*$')
    if not tail.search(text):
        raise SystemExit("data/streets/1835.json does not end in the shape this tool expects")
    body = ",\n".join(_render(e) for e in entries)
    return tail.sub(",\n" + body + "\n  ]\n}\n", text)


def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d)
    return (d[0] / n, d[1] / n)


def _cross(p, u, q, v):
    """Where the line p+t*u meets q+s*v."""
    det = u[0] * v[1] - u[1] * v[0]
    if abs(det) < 1e-12:
        raise SystemExit("two street lines of the Addition came out parallel")
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / det
    return (round(p[0] + t * u[0], 2), round(p[1] + t * u[1], 2))


def build():
    trace = json.loads(TRACE.read_text())
    doc = json.loads(STREETS.read_text())
    by = {s["id"]: s for s in doc["streets"]}
    P = trace["module"]["tier_pitch_m"]["mean"]
    Q = trace["module"]["column_pitch_m"]["mean"]
    corridor = trace["control_summary"]["addition_corridor_m"]

    mich = by["michigan_north"]["path_local_enu_m"]
    wol = by["wolcott"]["path_local_enu_m"]
    u = _unit(mich[0], mich[-1])          # along Michigan, eastward
    nrm = (-u[1], u[0])                   # off Michigan, northward
    v = _unit(wol[0], wol[-1])            # along Wolcott, northward
    off = (v[1], -v[0])                   # off Wolcott, eastward

    def ew_point(k):                      # a point on the k-th tier line
        return (mich[0][0] + k * P * nrm[0], mich[0][1] + k * P * nrm[1])

    def ns_point(j):
        return (wol[0][0] + j * Q * off[0], wol[0][1] + j * Q * off[1])

    out = []
    for sid, k, n1835, n2026, why in EAST_WEST:
        p = ew_point(k)
        west = _cross(p, u, ns_point(0), v)
        east = _cross(p, u, ns_point(EW_RIGHT[sid]), v)
        out.append(_entry(sid, n1835, n2026, why, [list(west), list(east)], corridor,
                          P, trace, "east-west", "michigan_north"))
    for sid, j, n1835, n2026, why in NORTH_SOUTH:
        q = ns_point(j)
        south = _cross(q, v, ew_point(0), u)
        north = _cross(q, v, ew_point(NS_TOP[sid]), u)
        out.append(_entry(sid, n1835, n2026, why, [list(south), list(north)], corridor,
                          Q, trace, "north-south", "wolcott"))
    return doc, by, out, P, Q


def _entry(sid, n1835, n2026, why, path, corridor, pitch, trace, fam, datum):
    key = "tier_pitch_m" if fam == "east-west" else "column_pitch_m"
    e = {
        "id": sid,
        "name_1835": n1835,
        "name_2026": n2026,
        "name_changed": bool(n2026 and n2026.split()[-2:] != n1835.split()[-2:]),
        "path_local_enu_m": path,
        "corridor_width_m": corridor,
        "track_width_m": 0,
        "opened": False,
        "worn": False,
        "alleys": False,
        "status_1835": "platted, unopened, unworn",
        "surface": "unworn_prairie",
        "traffic": "none",
        "geometry_confidence": "inferred",
        "surface_confidence": "inferred",
        "wear_confidence": "inferred",
        "sources": ["wright_1834_nara_hup", "wright_1834", "osm_streets_2026"],
        "note": NOTE.format(pitch=round(trace["module"][key]["mean"], 2),
                            sd=trace["module"][key]["sd"],
                            n=trace["module"][key]["n"],
                            fam=("east-west" if fam == "east-west" else "north-south"),
                            datum=f"`{datum}`", corr=corridor),
    }
    if n2026 is None:
        e["name_note"] = NAME_NOTE
    elif why:
        e["name_note"] = f"`name_2026` from {why}."
    return e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="the committed street lines still re-derive from the reading's module")
    a = ap.parse_args()
    doc, by, out, P, Q = build()
    if a.check:
        bad = []
        for s in out:
            have = by.get(s["id"])
            if have is None:
                bad.append(f"{s['id']} is not in data/streets/1835.json")
                continue
            # The line is checked to the centimetre, not to the byte: `michigan_north`
            # and `wolcott` are carried to the Addition's edge in the same write, so the
            # datum this re-derivation reads is a longer segment of the same line and the
            # unit vector comes back a float epsilon different.
            for a0, b0 in zip(have.get("path_local_enu_m", []), s["path_local_enu_m"]):
                if max(abs(a0[0] - b0[0]), abs(a0[1] - b0[1])) > 0.02:
                    bad.append(f"{s['id']}: committed {have['path_local_enu_m']}, "
                               f"re-derived {s['path_local_enu_m']}")
                    break
            for k in ("corridor_width_m", "name_1835", "name_2026", "status_1835",
                      "sources", "track_width_m", "surface", "traffic"):
                if have.get(k) != s[k]:
                    bad.append(f"{s['id']}.{k}: committed {have.get(k)}, re-derived {s[k]}")
        for line in bad:
            print("RED  " + line)
        print(f"kinzie addition streets: {len(out)} line(s) re-derive from the module in "
              f"data/traces/kinzie_addition_street_grid.json"
              if not bad else f"{len(bad)} disagreement(s)")
        return 1 if bad else 0

    ns = {s["id"]: s for s in out}
    mich, wol = by["michigan_north"], by["wolcott"]
    edits = []
    sand_e = ns["sand"]["path_local_enu_m"][0][0]
    u = _unit(mich["path_local_enu_m"][0], mich["path_local_enu_m"][-1])
    if mich["path_local_enu_m"][-1][0] < sand_e:
        p = mich["path_local_enu_m"][0]
        t = (sand_e - p[0]) / u[0]
        edits.append(("michigan_north", [p, [round(p[0] + t * u[0], 2),
                                             round(p[1] + t * u[1], 2)]]))
    sup_n = ns["superior_north"]["path_local_enu_m"][0][1]
    v = _unit(wol["path_local_enu_m"][0], wol["path_local_enu_m"][-1])
    if wol["path_local_enu_m"][-1][1] < sup_n:
        p = wol["path_local_enu_m"][0]
        t = (sup_n - p[1]) / v[1]
        edits.append(("wolcott", [p, [round(p[0] + t * v[0], 2),
                                      round(p[1] + t * v[1], 2)]]))
    for s in out:
        print(f'{s["id"]:16s} {s["name_1835"]:18s} {s["path_local_enu_m"]}')
    for ident, path in edits:
        print(f"{ident:16s} carried to {path[-1]}")
    print(f"tier pitch {P:.2f} m   column pitch {Q:.2f} m")
    if a.write:
        fresh = [s for s in out if s["id"] not in by]
        seated = [s for s in out if s["id"] in by]
        text = _splice(STREETS.read_text(), fresh, edits)
        STREETS.write_text(_reseat(text, seated))
        print(f"wrote {STREETS.relative_to(ROOT)} (+{len(fresh)}, {len(seated)} re-seated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
