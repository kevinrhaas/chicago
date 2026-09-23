#!/usr/bin/env python3
"""Carry Kinzie Street west, from the town's last committed point to Wabansia's own
boundary rule.

    tools/carry_kinzie_west.py            print what it would write
    tools/carry_kinzie_west.py --write    write data/streets/1835.json and the trace
    tools/carry_kinzie_west.py --check    the committed reach re-derives from the readings

T-1085, found by T-1070. `kinzie` in `data/streets/1835.json` ends at local east -320,
attested off the Thompson plat (T-0713), which draws the Original Town and stops at its
west boundary. J. S. Wright's 1834 survey draws the same street on west, the whole length
of Wabansia: the corridor is read and committed at `data/traces/wabansia_streets.json`
§ streets `kinzie`, with Wright's own `Kinzie` lettering inside it at NA px 1150-1450,
y 2060-2110. So the reach exists on a sheet this project holds, and the committed line
was silent about it — while T-1070's seating had to EXTRAPOLATE that line 418 m west to
have something to hang Wabansia's ladder from, and said so in writing. Six streets stood
committed north of a line that did not reach them.

WHY IT IS ITS OWN RECORD AND NOT A LONGER `kinzie`. `data/streets/1835.json` § _doc:
"a bend added to the plat line moves platted lot lines the whole length of the street and
re-scores the corridor-intrusion count". This carries no bend — the reach is collinear
with the committed line by construction, and `--check` asserts it — so nothing moves. But
the two halves are NOT THE SAME CLAIM and a record carries one confidence, one surface and
one traffic:

  * EAST of -320 the Thompson plat draws the street and the town wears it: geometry
    `attested`, `worn_earth`, traffic `ordinary`.
  * WEST of it Wright draws the street and nothing in this corpus wears it: geometry
    `inferred`, `unworn_prairie`, traffic `none`.

The project already splits a street this way where the claim changes — `market` and
`market_north`, `michigan_north` and `michigan_north_tract` — and this follows them.

WHAT IS ATTESTED AND WHAT IS INFERRED, kept apart because the temptation is to trade one
for the other. Wright ATTESTS THAT the street runs here: he rules the corridor across the
whole tract and letters it. What this tool INFERS is WHERE it lies. Carried through the NA
sheet's own affine, Wright's Kinzie corridor centre lands about 21 m south of the committed
line at the tract's west end and about 9 m south at its east end, because the sheet's drawn
bearing in this corner is about 1.6 deg off the one the committed grid takes from modern
control over a baseline four times longer, against a registration admitting 16.02 m RMS
with no control point within 900 m of this tract. Every one of those figures is
MEASURED here and written into the record this tool generates, rather than quoted in
prose: T-1070 measured 9.1 m and about 1.2 deg through the eight-point fit T-1091
superseded, and when T-1092 re-seated this reach onto the eleven-point fit in force
the numbers moved and the prose would not have. So the same division of labour the
seating used holds here: the SHEET says the street is there and how far west it goes, the
COMMITTED GRID says where the line runs and which way it lies. `geometry_confidence` is
`inferred` for that reason and not because the reach is in doubt.

THE WEST END is Wabansia's own west boundary rule at tier 7 — the tier Kinzie Street
bounds on the south — read by T-1074 at `data/traces/wabansia_block_numbering.json`
§ west_margin, and it is the outer rule of that pair, which is the same bound
`seat_wabansia_streets.py` gives the six streets north of here. The reading stops where
the tract stops and this line stops with it: Wright carries Kinzie further west still,
off the tract and off T-1074's reading, and that ground is nobody's yet.

THE EAST END is `kinzie`'s own west end, to the centimetre, so the two records meet
without a gap and without an overlap.
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
TRACE = ROOT / "data/traces/wabansia_streets.json"
BLOCKS = ROOT / "data/traces/wabansia_block_numbering.json"
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
DATUM = ROOT / "data/datum.json"
OUT = ROOT / "data/traces/kinzie_west_reach.json"

DATUM_ID = "kinzie"          # the committed street this reach continues
NEW_ID = "kinzie_west"
TIER = "t7"                  # the tier Kinzie Street bounds on the south

NAME_NOTE = (
    "`name_2026` is null because this project commits a modern name only where its own "
    "control reaches, and none of it reaches this ground. `kinzie` carries `W/E Kinzie "
    "Street` on `osm_streets_2026`, which in this repository is a set of street-crossing "
    "NODES used as georeferencing control — every one of them in the Original Town or "
    "Kinzie's Addition, none within 900 m of Wabansia. So the modern street cannot be "
    "asked here by crossing, the way it was asked there. This is a refusal to commit a "
    "name, not a claim that the name changed: `name_changed` is false because nothing "
    "here attests a change either."
)

NOTE = (
    "KINZIE STREET WEST OF THE TOWN, the 430 m between the Original Town's west boundary "
    "and Wabansia's — a separate record from `kinzie` because the two halves are not the "
    "same claim (T-1085). WHAT EACH SHEET GIVES: the Thompson plat draws Kinzie Street to "
    "the town's west line and stops, which is why `kinzie` stops at local east -320 and is "
    "`attested` there (T-0713, the owner's ruling of 2026-09-04). J. S. Wright's 1834 "
    "survey rules this corridor across the whole of Wabansia and letters `Kinzie` inside "
    "it (NA px 1150-1450, y 2060-2110), read at data/traces/wabansia_streets.json. So THAT "
    "the street runs here is Wright's claim and this project takes it. WHERE it runs is "
    "derived: the line is the committed `kinzie` line carried west on its own bearing to "
    "the easting of Wabansia's west boundary rule, which T-1074 read at tier 7. Wright's "
    "own corridor centre, carried through the NA sheet's affine, lands {west_off} m south "
    "of that line at the tract's west end and {east_off} m south at its east end — a "
    "bearing {bearing} deg off, against a registration admitting {rms} m RMS with no "
    "control point within 900 m of this tract — so the sheet "
    "measures the extent and the committed grid holds the line. `geometry_confidence` is "
    "`inferred` for that derivation, not because the reach is doubtful. STATUS, argued "
    "rather than inherited from `kinzie`: east of -320 the street is a worn earth track "
    "with ordinary traffic, which is a claim about the town's own ground, where the "
    "buildings and the bridge approach are. West of it this corridor runs along the south "
    "line of a survey over prairie — Wabansia's six streets north of it are committed "
    "`platted, unopened, unworn` on the same reading, and the one household the sources "
    "put on that tract before this date is a single advertised dwelling. Nothing in this "
    "corpus attests a wagon track, a grade or ordinary traffic 430 m west of the town's "
    "last building, so none is drawn: `track_width_m` is 0 and the wear claim stops at the "
    "seam, which is exactly where the evidence stops. COLLINEAR WITH `kinzie` BY "
    "CONSTRUCTION and gated so: this record adds no bend to the plat line, so no platted "
    "lot line moves and the corridor-intrusion count is re-scored rather than assumed "
    "(T-1085 records both numbers). Generated by tools/carry_kinzie_west.py — do not "
    "hand-edit the path."
)


# ------------------------------------------------------------------ the frame

def _frame():
    g = json.loads(GCP.read_text())
    d = json.loads(DATUM.read_text())
    # T-1092 re-seated this trace onto the ELEVEN-POINT registration T-1091 adopted,
    # and re-baked what stands on the ground that moved. `fit` IS that registration;
    # the eight-point fit it superseded is kept beside it as `retained_fit` for the
    # adjudication that compares the two. Reading `retained_fit` here would seat the
    # ground on a fit this project no longer holds.
    c = g["fit"]["coefficients"]

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"] - d["origin_utm_e"],
                c["d"] * px + c["e"] * py + c["f"] - d["origin_utm_n"])

    return to_local


def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d)
    return (d[0] / n, d[1] / n)


# ------------------------------------------------------------------ the reach

def build():
    trace = json.loads(TRACE.read_text())
    blocks = json.loads(BLOCKS.read_text())
    doc = json.loads(STREETS.read_text())
    by = {s["id"]: s for s in doc["streets"]}
    to_local = _frame()
    shear = trace["method"]["shear_ew"]
    kz = {s["id"]: s for s in trace["streets"]}[DATUM_ID]
    margin = {w["tier"]: w for w in blocks["west_margin"]}

    kin = by[DATUM_ID]["path_local_enu_m"]
    u = _unit(kin[0], kin[-1])           # the committed line's own bearing, eastward

    def on_committed_line(east):
        """The committed `kinzie` line at this easting, extended if need be.

        Extended, not bent: every point comes off the same two-point bearing the seating
        used, so the reach cannot introduce a vertex the committed line does not have."""
        t = (east - kin[0][0]) / u[0]
        return [round(kin[0][0] + t * u[0], 2), round(kin[0][1] + t * u[1], 2)]

    # Wabansia's west boundary rule at the tier Kinzie bounds, on Kinzie's own corridor
    # row in that column — the rules lean (dy/dx 0.019) and a row read at x 700 is not the
    # same row at x 682.
    west_px = margin[TIER]["rule_px_x"][0]

    def sheet_py(px):
        return kz["centre_px_y"] + shear * (px - kz["ref_px_x"])

    def sheet_point(px):
        """Wright's Kinzie corridor centre at this sheet column, in local ENU."""
        return to_local(px, sheet_py(px))

    west_py = sheet_py(west_px)
    sheet_e, sheet_n = sheet_point(west_px)

    west = on_committed_line(sheet_e)
    east = [round(kin[0][0], 2), round(kin[0][1], 2)]
    path = [west, east]

    # THE SHEET'S OWN LINE AT BOTH ENDS, so the disagreement can be reported as what it
    # measures rather than as a figure carried forward in prose. Two points on Wright's
    # corridor centre give its bearing; where that bearing reaches the committed line's
    # east end is what the drawn street would do over the same reach.
    s0, s1 = sheet_point(west_px), sheet_point(west_px + 300)
    sv = _unit(s0, s1)
    sheet_n_at_east = s0[1] + (east[0] - s0[0]) / sv[0] * sv[1]
    bearing_deg = abs(math.degrees(math.atan2(sv[1], sv[0]) - math.atan2(u[1], u[0])))
    if bearing_deg > 180:
        bearing_deg = 360 - bearing_deg

    evidence = {
        "west_end": {
            "from": f"{BLOCKS.name} § west_margin {TIER} (T-1074), the outer rule of the pair",
            "px": [west_px, round(west_py, 2)],
            "sheet_local_enu_m": [round(sheet_e, 2), round(sheet_n, 2)],
            "committed_line_at_same_e_m": west,
            "sheet_south_of_committed_m": round(sheet_n - west[1], 2),
        },
        "east_end": {
            "from": f"{STREETS.name} § {DATUM_ID}, its own west end",
            "local_enu_m": east,
            "sheet_south_of_committed_m": round(sheet_n_at_east - east[1], 2),
        },
        "sheet_bearing_off_committed_deg": round(bearing_deg, 2),
        "reach_m": round(math.dist(west, east), 1),
        "bearing_from": f"{STREETS.name} § {DATUM_ID}, first point to last",
        "collinear_with_committed_kinzie": True,
        "sheet_registration_rms_m": trace["cross_check"]["sheet_registration_rms_m"],
        "reading": (
            "Wright's Kinzie corridor centre lands "
            f"{abs(round(sheet_n - west[1], 2))} m south of the committed line at the "
            f"tract's west boundary rule and {abs(round(sheet_n_at_east - east[1], 2))} m "
            "south of it at the committed line's own west end, so the drawn street runs "
            f"{round(bearing_deg, 2)} deg off the committed bearing over this reach, "
            "against a registration admitting "
            f"{trace['cross_check']['sheet_registration_rms_m']} m RMS over the eleven "
            "control points in force since T-1091, none of them within 900 m of this "
            "tract. The two readings agree that this is one street; the sheet is asked "
            "for the extent and the committed grid for the line, which is T-1070's own "
            "division of labour."
        ),
    }
    figures = dict(west_off=abs(round(sheet_n - west[1], 2)),
                   east_off=abs(round(sheet_n_at_east - east[1], 2)),
                   bearing=round(bearing_deg, 2),
                   rms=trace["cross_check"]["sheet_registration_rms_m"])
    return doc, by, _entry(path, figures), evidence, trace


def _entry(path, figures):
    return {
        "id": NEW_ID,
        "name_1835": "Kinzie Street",
        "name_2026": None,
        "name_changed": False,
        "path_local_enu_m": path,
        "corridor_width_m": 24.384,
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
        "sources": ["wright_1834_nara_hup", "wright_1834"],
        "note": NOTE.format(**figures),
        "name_note": NAME_NOTE,
    }


def _trace_doc(evidence, entry):
    return {
        "_doc": __doc__,
        "ticket": "T-1085",
        "street": NEW_ID,
        "continues": DATUM_ID,
        "committed_in": "data/streets/1835.json",
        "method": {
            "extent": ("Wright's 1834 survey, which rules and letters this corridor across "
                       "Wabansia; west end at the tract's own boundary rule (T-1074), east "
                       "end at the committed line's own west end"),
            "bearing": "the committed kinzie line's, not the sheet's — T-1070's argument",
            "bend": ("none. The reach is collinear with the committed line by construction, "
                     "so no platted lot line moves and no corridor is re-cut."),
        },
        "evidence": evidence,
        "path_local_enu_m": entry["path_local_enu_m"],
        "what_this_does_not_carry": {
            "further_west": ("Wright draws Kinzie Street on west past Wabansia's boundary "
                             "rule. T-1074's reading stops at the tract and so does this "
                             "line; the ground beyond it is unread."),
            "wear": ("`kinzie`'s worn earth and ordinary traffic are a claim about the "
                     "town's ground and are not carried west. See the record's own note."),
            "modern_name": ("no control on this reach; `name_2026` is null and the reason "
                            "is in `name_note`."),
        },
    }


# ------------------------------------------------------------------ the write

def _render(entry, indent=4):
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


def _splice(text, entry):
    """Append the street WITHOUT re-serialising the file — seat_kinzie_addition_streets.py's
    argument, and seat_wabansia_streets.py's: a writer that re-emits this document changes a
    thousand lines of escaping to add one street, and a reviewer cannot see that."""
    tail = re.compile(r'\n  \]\n\}\s*$')
    if not tail.search(text):
        raise SystemExit("data/streets/1835.json does not end in the shape this tool expects")
    return tail.sub(",\n" + _render(entry) + "\n  ]\n}\n", text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="the committed reach still re-derives from the readings")
    a = ap.parse_args()
    doc, by, entry, evidence, trace = build()

    if a.check:
        bad = []
        have = by.get(NEW_ID)
        if have is None:
            bad.append(f"{NEW_ID} is not in data/streets/1835.json")
        else:
            for a0, b0 in zip(have.get("path_local_enu_m", []), entry["path_local_enu_m"]):
                if max(abs(a0[0] - b0[0]), abs(a0[1] - b0[1])) > 0.02:
                    bad.append(f"{NEW_ID}: committed {have['path_local_enu_m']}, "
                               f"re-derived {entry['path_local_enu_m']}")
                    break
            if len(have.get("path_local_enu_m", [])) != len(entry["path_local_enu_m"]):
                bad.append(f"{NEW_ID}: committed path has "
                           f"{len(have.get('path_local_enu_m', []))} point(s), re-derived "
                           f"{len(entry['path_local_enu_m'])}")
            for k in ("name_1835", "name_2026", "corridor_width_m", "track_width_m",
                      "status_1835", "surface", "traffic", "geometry_confidence",
                      "sources", "note", "name_note"):
                if have.get(k) != entry[k]:
                    bad.append(f"{NEW_ID}.{k}: committed {have.get(k)!r}, "
                               f"re-derived {entry[k]!r}")

        # THE SEAM AND THE BEND, which is the reason T-1085 is a ticket of its own. The
        # reach meets `kinzie` at its west end and lies on `kinzie`'s own bearing; if
        # either stops being true, a platted lot line has moved somewhere down the street
        # and the corridor-intrusion count this PR re-scored no longer holds.
        kin = by[DATUM_ID]["path_local_enu_m"]
        if have is not None:
            seam = have["path_local_enu_m"][-1]
            if max(abs(seam[0] - kin[0][0]), abs(seam[1] - kin[0][1])) > 0.02:
                bad.append(f"{NEW_ID} does not meet {DATUM_ID}: seam {seam}, "
                           f"{DATUM_ID} west end {kin[0]}")
            u = _unit(kin[0], kin[-1])
            off = abs((have["path_local_enu_m"][0][0] - kin[0][0]) * u[1]
                      - (have["path_local_enu_m"][0][1] - kin[0][1]) * u[0])
            if off > 0.02:
                bad.append(f"{NEW_ID} is not collinear with {DATUM_ID}: west end stands "
                           f"{off:.2f} m off the committed bearing")

        if OUT.exists():
            was = json.loads(OUT.read_text())
            now = _trace_doc(evidence, entry)
            for key in ("evidence", "path_local_enu_m"):
                if json.dumps(was.get(key), sort_keys=True) != \
                   json.dumps(now[key], sort_keys=True):
                    bad.append(f"{OUT.name} § {key} does not re-derive from the readings")
        else:
            bad.append(f"{OUT.name} is missing")

        for line in bad:
            print("RED  " + line)
        print(f"kinzie west reach: {evidence['reach_m']} m re-derives from "
              f"{BLOCKS.name} and the committed {DATUM_ID} line"
              if not bad else f"{len(bad)} disagreement(s)")
        return 1 if bad else 0

    print(f'{entry["id"]:12s} {entry["name_1835"]:14s} {evidence["reach_m"]:7.1f} m  '
          f'{entry["path_local_enu_m"]}')
    print(f'{"":12s} Wright\'s corridor centre vs the committed line at the tract\'s west '
          f'rule: {evidence["west_end"]["sheet_south_of_committed_m"]:+.2f} m '
          f'(registration {evidence["sheet_registration_rms_m"]} m RMS)')
    if a.write:
        # Until T-1092 this refused a second write outright. It now RE-POINTS the
        # record it owns instead, because the line is carried west off `kinzie` to a
        # Wabansia rule that moves when the registration does, and a generator that
        # cannot re-derive its own output leaves the committed line on a superseded fit.
        text = STREETS.read_text()
        text = _reseat(text, [entry]) if NEW_ID in by else _splice(text, entry)
        STREETS.write_text(text)
        OUT.write_text(json.dumps(_trace_doc(evidence, entry), indent=2,
                                  ensure_ascii=False) + "\n")
        print(f"wrote {STREETS.relative_to(ROOT)} and {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
