#!/usr/bin/env python3
"""Seat the Michigan St tract's platted grid on the committed town grid.

    tools/seat_michigan_st_tract.py            print what it would write
    tools/seat_michigan_st_tract.py --write    write the streets file and the seating
    tools/seat_michigan_st_tract.py --check    the committed lines still re-derive

The reading is `data/traces/michigan_st_tract_grid.json` (T-1076) and none of it is
repeated here. That reading identified the tract's two streets: its east-west street,
the one Wright letters `Michigan St`, is Kinzie's Addition's Michigan Street, and its
north-south street is Market Street carried north. This tool takes the LADDER out of
that reading — how far each ruled line stands from those two streets, measured inside
one corner of one raster — and hangs it on the two committed lines the reading named,
`michigan_north` and `market_north`.

WHY NOT COMMIT THE PIXELS. Because the sheet's fit is local, and at this tract it is
badly local. Wright's fit puts Michigan Street 99 m north of the
committed Kinzie line here; the committed grid, which takes that tier from the Thompson
plat and from modern control over a baseline four times longer, puts it at 138 m. The
plat draws exactly ONE tier of North Division blocks in that span, so it has to hold a
block plus an 80 ft street — 453 ft does and 328 ft does not. The sheet is compressed in
y at its western margin, and the tract is seated on the grid rather than on the fit — the same trade `tools/seat_kinzie_addition_streets.py` makes, at three times
the size.

THE COST IS STATED RATHER THAN HIDDEN. Seated, the tract's south border stands 60.5 m
north of Kinzie Street where the sheet's fit draws 22.0 m. That 38.5 m is Wright's
compression, not a fact about the tract, and it is the reason this tool exists instead
of a paste of `local_enu_m` values. The alternative — hanging the ladder on `kinzie`
instead, whose drawn position the sheet does get right — would place a SECOND Michigan
Street 38 m south of the committed one, which is precisely what the reading refuses.

Nothing here is fitted to modern pavement and nothing is chosen to look right.
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
TRACE = ROOT / "data/traces/michigan_st_tract_grid.json"
SEATED = ROOT / "data/traces/michigan_st_tract_seated.json"

# The ladder, off Michigan Street northward and off Market Street eastward. Both are
# derived from the reading in `_ladder()`; these are only the names and the order.
EW_ORDER = ["north_border", "alley_north_tier", "michigan_st", "alley_south_tier",
            "south_border"]
NS_ORDER = ["west_border", "market_st", "east_border"]

DATUM_NOTE = (
    "THE TRACT IS SEATED, NOT PASTED. `tools/seat_michigan_st_tract.py` lays the ladder "
    "measured in data/traces/michigan_st_tract_grid.json off the two committed lines that "
    "reading identifies the tract's streets as — `michigan_north` and `market_north` — and "
    "the seating is re-derived by tools/check.sh every run. Wright's sheet draws the "
    "Kinzie-to-Michigan span at this longitude 39 m short of the committed grid's, too short "
    "for the one block tier plus street Thompson's plat draws in it; seated, the tract's "
    "south border stands {seated} m north of Kinzie Street where the fit draws {drawn} m. "
    "The {diff} m is the sheet's compression and is not a claim about the ground."
)

REACH_NOTE = (
    "{lead} THE LINE is the committed `{datum}` line itself, extended on its own bearing — "
    "not a second street beside it. It is carried as its own record and not as a longer "
    "`{datum}` because Wright leaves the {gap} m between this tract and {neighbour} BLANK: "
    "unsurveyed, unruled, and carrying the sheet's own title. A platted line across ground "
    "no sheet plats would be an invention, so the two reaches of one street are committed as "
    "two records and the note says they are one street. EXTENT is the tract's own borders, "
    "read as ruled lines on the sheet and seated with the rest of the ladder. STATUS follows "
    "`madison`'s and the Addition's: platted ground, not road — `track_width_m` is 0 because "
    "no wagon track is drawn or attested on it, and the confidences say `inferred` because "
    "the line is a committed street's bearing carrying a sheet-read ladder, not a trace of a "
    "plat this project holds. The blocks either side DO carry a mid-block alley, which no "
    "Original Town block on this sheet does, so `alleys` is true and the two alleys are "
    "committed beside this record. {datum_note} T-1079, piece 1 of T-1075."
)

ALLEY_NOTE = (
    "A MID-BLOCK ALLEY, and the tract's signature. Every block Wright rules inside this tract "
    "carries one and no Original Town block on the same sheet does, which with the small lot "
    "frontages is what marks the tract off from its whole-block neighbours. GEOMETRY: the rule "
    "is read at {off} m off the tract's Michigan Street in "
    "data/traces/michigan_st_tract_grid.json, in both block columns, and seated here parallel "
    "to `michigan_north`. WIDTH {corr} m is the reading's mean over its four measurements (sd "
    "{sd} m); the reading refuses to round it to a platted figure, because this sheet carries "
    "3.7-4.5 per cent local scale error and the gap between a 16 ft and an 18 ft alley is "
    "0.6 m, so 16 ft and 18 ft are both inside the read. NAME: the sheet letters none, and an "
    "alley of 1835 Chicago with no lettering has no name this project can give it. The "
    "centreline runs the full width of the tract and Market Street's corridor crosses it; an "
    "alley stops at a street, and the crossing is the renderer's to resolve as it resolves "
    "every other, not a claim that the alley runs through the roadway. {datum_note} "
    "T-1079, piece 1 of T-1075."
)

NAME_NOTE = (
    "`name_2026` is null because no source in this repository attests what this line is called "
    "today. A modern name is not evidence about 1835 and is not guessed at here."
)


def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d)
    return (d[0] / n, d[1] / n)


def _cross(p, u, q, v):
    det = u[0] * v[1] - u[1] * v[0]
    if abs(det) < 1e-12:
        raise SystemExit("the tract's two committed datum lines came out parallel")
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / det
    return (p[0] + t * u[0], p[1] + t * u[1])


def _ladder(trace):
    """The tract's ruled lines as offsets, in metres, off its own two streets.

    Every number is the mean of the reading's two block columns. Nothing is rounded to
    a module and nothing is fitted: the sheet is asked only how far one rule stands from
    the next inside one corner of one raster, which is the one thing it measures well."""
    ew = trace["readings"]["east_west"]
    ns = trace["readings"]["north_south"]

    def centre(rec):
        return rec.get("centre_local_enu_m") or rec["local_enu_m"]

    mich = {col: centre(ew["michigan_st"][col])[1] for col in ("col_west", "col_east")}
    off_ew = {}
    for key in EW_ORDER:
        vals = [centre(ew[key][col])[1] - mich[col] for col in ("col_west", "col_east")]
        off_ew[key] = round(sum(vals) / len(vals), 2)

    market = [ns[t]["north_south_street"]["centre_local_enu_m"][0] for t in sorted(ns)]
    market_mean = sum(market) / len(market)
    corners = trace["extent"]["corners"]
    west = [corners["nw"]["local_enu_m"][0], corners["sw"]["local_enu_m"][0]]
    east = [corners["ne"]["local_enu_m"][0], corners["se"]["local_enu_m"][0]]
    off_ns = {
        "west_border": round(sum(west) / len(west) - market_mean, 2),
        "market_st": 0.0,
        "east_border": round(sum(east) / len(east) - market_mean, 2),
    }
    return off_ew, off_ns


def build():
    trace = json.loads(TRACE.read_text())
    doc = json.loads(STREETS.read_text())
    by = {s["id"]: s for s in doc["streets"]}
    off_ew, off_ns = _ladder(trace)

    mich = by["michigan_north"]["path_local_enu_m"]
    mkt = by["market_north"]["path_local_enu_m"]
    u = _unit(mich[0], mich[-1])            # along Michigan Street, eastward
    nrm = (-u[1], u[0])                     # off it, northward
    v = _unit(mkt[0], mkt[-1])              # along Market Street, northward
    east = (v[1], -v[0])                    # off it, eastward
    origin = _cross(mich[0], u, mkt[0], v)  # where the tract's two streets cross

    def pt(a, b):
        return [round(origin[0] + a * nrm[0] + b * east[0], 2),
                round(origin[1] + a * nrm[1] + b * east[1], 2)]

    w, e = off_ns["west_border"], off_ns["east_border"]
    s, n = off_ew["south_border"], off_ew["north_border"]
    alley = trace["module"]["alley_width"]
    corr_ew = trace["module"]["michigan_st_corridor"]["read_m"]
    corr_ns = trace["module"]["north_south_street_corridor"]["read_m"]

    gap_e = round(mich[0][0] - pt(0, e)[0], 1)     # blank ground east of the tract
    gap_n = round(pt(s, 0)[1] - mkt[-1][1], 1)     # blank ground south of the tract

    seating = _seating(trace, off_ew, off_ns, pt, by, gap_e, gap_n)
    cost = seating["cost_of_seating_m"]
    datum_note = DATUM_NOTE.format(
        seated=cost["tract_south_border_north_of_kinzie_seated"],
        drawn=cost["tract_south_border_north_of_kinzie_on_the_sheets_fit"],
        diff=cost["disagreement"])

    out = [
        _entry("michigan_north_tract", "Michigan Street", [pt(0, w), pt(0, e)], corr_ew,
               True, REACH_NOTE.format(
                   lead="MICHIGAN STREET INSIDE THE TRACT, and it is Kinzie's Addition's "
                        "Michigan Street. The reading carried this street east on the "
                        "Addition's own fitted slope and landed 1.7 px — about a metre and a "
                        "half of ground — from the corridor centre the Addition's Michigan "
                        "Street was read at eleven hundred pixels away, which is why Wright's "
                        "second `Michigan St` is not a second street of that name.",
                   datum="michigan_north", gap=gap_e, neighbour="Kinzie's Addition",
                   datum_note=datum_note)),
        _entry("market_north_tract", "Market Street", [pt(s, 0), pt(n, 0)], corr_ns,
               True, REACH_NOTE.format(
                   lead="MARKET STREET INSIDE THE TRACT. The reading carried the tract's "
                        "north-south street south across Kinzie Street and landed 16.7 m from "
                        "the easting `market_north` already holds — inside this sheet's own "
                        "16.19 m RMS and well inside a street's width, with no other "
                        "north-south street within a hundred metres for it to be.",
                   datum="market_north", gap=gap_n, neighbour="the North Division's tier",
                   datum_note=datum_note)),
        _entry("michigan_st_tract_alley_north", "The tract's north-tier alley",
               [pt(off_ew["alley_north_tier"], w), pt(off_ew["alley_north_tier"], e)],
               round(alley["read_m"], 2), False,
               ALLEY_NOTE.format(off=off_ew["alley_north_tier"], datum_note=datum_note,
                                 corr=round(alley["read_m"], 2), sd=alley["sd_m"])),
        _entry("michigan_st_tract_alley_south", "The tract's south-tier alley",
               [pt(off_ew["alley_south_tier"], w), pt(off_ew["alley_south_tier"], e)],
               round(alley["read_m"], 2), False,
               ALLEY_NOTE.format(off=abs(off_ew["alley_south_tier"]), datum_note=datum_note,
                                 corr=round(alley["read_m"], 2), sd=alley["sd_m"])),
    ]
    return doc, by, out, seating


def _entry(sid, n1835, path, corridor, alleys, note):
    return {
        "id": sid,
        "name_1835": n1835,
        "name_2026": None,
        "name_changed": True,
        "path_local_enu_m": path,
        "corridor_width_m": corridor,
        "track_width_m": 0,
        "opened": False,
        "worn": False,
        "alleys": alleys,
        "status_1835": "platted, unopened, unworn",
        "surface": "unworn_prairie",
        "traffic": "none",
        "geometry_confidence": "inferred",
        "surface_confidence": "inferred",
        "wear_confidence": "inferred",
        "sources": ["wright_1834_nara_hup", "wright_1834", "thompson_plat_1830"],
        "note": note,
        "name_note": NAME_NOTE,
    }


def _seating(trace, off_ew, off_ns, pt, by, gap_e, gap_n):
    """The tract's ground, seated — what a tract layer (T-0792) will want and what the
    street records cannot carry: the polygon, the ladder it came from, and the size of
    the disagreement the seating accepts."""
    w, e = off_ns["west_border"], off_ns["east_border"]
    s, n = off_ew["south_border"], off_ew["north_border"]
    kz = by["kinzie"]["path_local_enu_m"]
    sb = pt(s, 0.0)

    def kinzie_at(x):
        for i in range(len(kz) - 1):
            a, b = kz[i], kz[i + 1]
            if min(a[0], b[0]) <= x <= max(a[0], b[0]):
                return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
        a, b = kz[-2], kz[-1]
        return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])

    seated_gap = round(sb[1] - kinzie_at(sb[0]), 2)
    fit_sb = trace["extent"]["corners"]["sw"]["local_enu_m"][1]
    fit_gap = round(fit_sb - kinzie_at(sb[0]), 2)
    # The check that decides which datum the ladder hangs on, in the one frame both
    # answers are already in: how far Michigan Street stands north of the committed
    # Kinzie line, on the committed grid and on this sheet's own fit.
    ew = trace["readings"]["east_west"]["michigan_st"]
    fit_mich = sum(ew[c]["centre_local_enu_m"][1] for c in ew) / len(ew)
    committed_span = round(pt(0.0, 0.0)[1] - kinzie_at(sb[0]), 2)
    fit_span = round(fit_mich - kinzie_at(sb[0]), 2)
    return {
        "_doc": SEATED_DOC,
        "ticket": "T-1079 (piece 1 of T-1075: the seating)",
        "reading": "data/traces/michigan_st_tract_grid.json",
        "tool": "tools/seat_michigan_st_tract.py",
        "datum": {
            "east_west": "michigan_north",
            "north_south": "market_north",
            "why": trace["identity"]["consequence"],
        },
        "ladder_m": {"off_michigan_northward": off_ew, "off_market_eastward": off_ns},
        "corners_local_enu_m": {"nw": pt(n, w), "ne": pt(n, e),
                                "sw": pt(s, w), "se": pt(s, e)},
        "blocks": {
            "columns": 2, "tiers": 2, "count": 4,
            "lots_per_block_row": trace["module"]["lots_per_block_row"],
            "note": "Two block columns either side of Market Street, two tiers either "
                    "side of Michigan Street, each block ruled through by a mid-block "
                    "alley. The lot LINES are read and committed in the reading; they "
                    "are not seated here because a lot line is a division of a block "
                    "and the block's own borders are what this file places.",
        },
        "detached_reaches_m": {
            "blank_ground_east_to_kinzies_addition": gap_e,
            "blank_ground_south_to_the_north_division": gap_n,
            "note": "Wright leaves both spans unsurveyed and unruled. Michigan Street and "
                    "Market Street are each committed as two records for that reason.",
        },
        "cost_of_seating_m": {
            "tract_south_border_north_of_kinzie_seated": seated_gap,
            "tract_south_border_north_of_kinzie_on_the_sheets_fit": fit_gap,
            "disagreement": round(seated_gap - fit_gap, 2),
            "kinzie_to_michigan_committed_m": committed_span,
            "kinzie_to_michigan_on_the_sheets_fit_m": fit_span,
            "note": "The seating is preferred and the disagreement is Wright's. Measured "
                    f"north of the committed Kinzie line in the one frame both answers are "
                    f"already in, the committed grid puts Michigan Street {committed_span} m "
                    f"away and this sheet's fit puts it {fit_span} m away. Thompson's plat "
                    "draws exactly ONE tier of North Division blocks in that span, fronting "
                    f"Kinzie on the south and Michigan on the north, so the span has to hold "
                    f"a block plus an 80 ft street: {round(committed_span * 3.28084)} ft "
                    f"does and {round(fit_span * 3.28084)} ft does not. Hanging the ladder "
                    "on `kinzie` instead would have kept the drawn frontage and committed a "
                    "second Michigan Street 38 m south of the first, which is exactly what "
                    "the reading's identification refuses.",
        },
        "open": [
            "T-1080 — the tract's NAME and who platted it: not settled. `Wolcott's "
            "Addition` is the one candidate the corpus raises and the corpus also refuses "
            "it on size. See docs/RESEARCH/michigan_st_tract.md.",
            "T-1080 — the curved road that leaves the Kinzie/North Water corner and runs "
            "north through this tract is drawn on the sheet and still unread.",
        ],
    }


SEATED_DOC = (
    "The Michigan St tract north of Kinzie Street, seated on the committed town grid.\n\n"
    "    tools/seat_michigan_st_tract.py --check\n\n"
    "DERIVED, NOT AUTHORED. Every number here is recomputed from "
    "data/traces/michigan_st_tract_grid.json and the committed lines of "
    "data/streets/1835.json by the tool above, and tools/check.sh re-derives it every run. "
    "A hand edit to this file fails the gate."
)


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


def _splice(text, entries):
    """Append to the array without re-serialising 51 hand-tended entries whose notes run
    to three thousand characters — a writer that re-emits the document changes a thousand
    lines of escaping to add four streets, and a reviewer should not have to read that."""
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="the committed lines and the seating still re-derive")
    a = ap.parse_args()
    doc, by, out, seating = build()

    if a.check:
        bad = []
        for s in out:
            have = by.get(s["id"])
            if have is None:
                bad.append(f"{s['id']} is not in data/streets/1835.json")
                continue
            for k in ("path_local_enu_m", "corridor_width_m", "name_1835", "name_2026",
                      "status_1835", "sources", "track_width_m", "surface", "traffic",
                      "alleys", "note"):
                if have.get(k) != s[k]:
                    bad.append(f"{s['id']}.{k}: committed {have.get(k)!r}, "
                               f"re-derived {s[k]!r}")
        if not SEATED.exists():
            bad.append(f"{SEATED.relative_to(ROOT)} is missing")
        elif json.loads(SEATED.read_text()) != seating:
            bad.append(f"{SEATED.relative_to(ROOT)} does not re-derive from the reading "
                       f"and the committed streets")
        for line in bad:
            print("RED  " + line)
        print(f"michigan st tract: {len(out)} line(s) and the seating re-derive from "
              f"data/traces/michigan_st_tract_grid.json"
              if not bad else f"{len(bad)} disagreement(s)")
        return 1 if bad else 0

    for s in out:
        print(f'{s["id"]:32s} {s["name_1835"]:28s} {s["path_local_enu_m"]}')
    c = seating["corners_local_enu_m"]
    print(f'tract corners  nw {c["nw"]}  ne {c["ne"]}  sw {c["sw"]}  se {c["se"]}')
    print(f'seated south border stands '
          f'{seating["cost_of_seating_m"]["tract_south_border_north_of_kinzie_seated"]} m '
          f'north of Kinzie; the sheet draws '
          f'{seating["cost_of_seating_m"]["tract_south_border_north_of_kinzie_on_the_sheets_fit"]} m')

    if a.write:
        fresh = [s for s in out if s["id"] not in by]
        seated = [s for s in out if s["id"] in by]
        text = _reseat(_splice(STREETS.read_text(), fresh), seated)
        STREETS.write_text(text)
        print(f"wrote {STREETS.relative_to(ROOT)} "
              f"(+{len(fresh)}, {len(seated)} re-seated)")
        SEATED.write_text(json.dumps(seating, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {SEATED.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
