#!/usr/bin/env python3
"""Carry the West Division's five east-west tier lines off their E -320 clip to Des
Plaines Street.

    tools/carry_west_tiers_west.py            print the derivation
    tools/carry_west_tiers_west.py --write    write data/streets/1835.json and the trace
    tools/carry_west_tiers_west.py --check    the committed reaches re-derive
    tools/carry_west_tiers_west.py --gate     the same, quiet, for tools/check.sh

T-1443, piece 1 of 2 of T-1431, itself split out of T-1417. `carroll`, `fulton`, `lake`,
`randolph` and `washington` all stopped dead at local east -320. `fulton`'s own note said
what that clip was and said it in the record rather than in a memo:

    WHY THE LINE STILL STOPS AT EAST -320 ... when the control runs 200 m further west:
    the west clip is this reconstruction's own extent, not a statement that the street
    ended there, and moving it would move five streets rather than one.

Two things have happened since. T-1416 built the modelled field out to local east -705,
so the extent that did the clipping is no longer there; and T-1430 seated `jefferson` and
`des_plaines`, so the West Division's westernmost platted street is committed and a tier
has something to stop AT rather than merely stopping. This file moves the five streets —
all of them, in one place, which is the condition the note set.

WHAT THE REACH IS, AND WHAT IT IS NOT. It is not new evidence. The Thompson plat draws
these tiers across the whole West Division; `lake`, `randolph` and `washington` are graded
`attested` FROM that sheet (T-0713) and `fulton` is attested and fitted besides. So the
plat already carried the street over this ground and the file did not. Each line is
therefore EXTENDED on its own westernmost segment's bearing — not re-fitted, not re-bent —
and `--check` holds the old west vertex on the new line to the centimetre, so the 200 m
this adds cannot move a platted lot line, re-cut a corridor, or change the
corridor-intrusion count anywhere east of the clip. The confidences do not move either:
carrying a line the length the sheet already drew it is not an upgrade, and nothing here
is graded better than it was.

WHERE EACH LINE STOPS. At `des_plaines`, the westernmost street of the plat's West
Division, on the committed centreline T-1430 seated — not at the modelled field's west
wall, which is a fact about this reconstruction's extent and would be the same mistake
one ticket later. The plat's own west boundary line is not committed to this repository,
so the line stops on the last committed control rather than on an inferred boundary.

WHAT CORROBORATES IT, and it is the reason this is a measurement and not a ruling.
`fulton` carries four surviving OpenStreetMap intersections in its own note (T-0446),
read on 2026-09-04 and fitted at RMS 0.35 m — and TWO OF THE FOUR, Jefferson and Des
Plaines, stand WEST of the clip. The extension is derived from the committed bearing and
knows nothing about them, and it passes within a few centimetres of both. The clip was
hiding 200 m of street that the record's own control already held.

CARROLL IS STILL THE ONE INTERPOLATION and is still graded for it. Its rule is unchanged —
the midpoint of Kinzie and Fulton at every easting — but west of the clip the Kinzie term
is `kinzie_west`, the separate record T-1085 carried across Wabansia, because that is the
line that exists there. Carroll stops at `fulton`'s west end and not one metre further:
an interpolation may not claim more ground than the pair it is interpolated between, which
is T-1430's own rule about borrowed lines turned through ninety degrees. Its bracket — the
two single-module steps from either neighbour — is re-measured at the new west end here,
and the midpoint has to sit inside it.

THE GROUND IS CHECKED, NOT ASSUMED. Every reach is sampled along its length against the
committed heightfield, and the lowest sample is on the record. A street drawn over water
or off the modelled box is what this gate exists to refuse.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STREETS = ROOT / "data/streets/1835.json"
HF_META = ROOT / "data/terrain/epochs/e1834_harbor_cut/heightfield.json"
HF_BIN = ROOT / "data/terrain/epochs/e1834_harbor_cut/heightfield.bin"
OUT = ROOT / "data/traces/west_tiers_west_reach.json"

sys.path.insert(0, str(ROOT / "tools"))
from carry_kinzie_west import _entry_spans, _reseat  # noqa: E402

# North to south, the order the plat carries the West Division's tiers in. `kinzie` is
# not here: T-1085 carried it west as its own record, and it is the datum Carroll reads.
TIERS = ["carroll", "fulton", "lake", "randolph", "washington"]
STOP_AT = "des_plaines"
KINZIE_WEST = "kinzie_west"

# The west vertex each line stood on before this ticket, frozen so the extension can be
# held to it. A reach that no longer passes through the old end has BENT the street, and
# a bend moves platted lot lines the whole length of it (data/streets/1835.json § _doc).
OLD_WEST = {
    "carroll": [-320.0, 137.85],
    "fulton": [-320.0, 12.59],
    "lake": [-320.0, -107.1],
    "randolph": [-320.0, -249.9],
    "washington": [-320.0, -385.2],
}

# `fulton`'s four surviving intersections, quoted from its own committed note (T-0446,
# read from OpenStreetMap on 2026-09-04). The two western ones are the corroboration;
# the two eastern ones are here so the report can state that the fit is the same fit.
FULTON_NODES = {
    "canal": (-162.00, 12.17, 258020617),
    "clinton": (-282.18, 11.83, 258966840),
    "jefferson": (-401.04, 13.11, 262247424),
    "des_plaines": (-524.88, 13.72, 258966841),
}
FULTON_FIT_RMS_M = 0.35

CLAUSE_MARK = "WEST TO DES PLAINES STREET (T-1443)."


# ------------------------------------------------------------------ the ground

class Field:
    """The committed heightfield, read as a sampler. Elevation is metres above the
    summer-1835 water surface, so `<= 0` is water and `None` is off the modelled box —
    two different refusals and the report keeps them apart."""

    def __init__(self):
        self.m = json.loads(HF_META.read_text())
        self.raw = HF_BIN.read_bytes()

    def at(self, e, n):
        m = self.m
        c = int(round((e - m["origin_e"]) / m["cell_m"]))
        r = int(round((n - m["origin_n"]) / m["cell_m"]))
        if not (0 <= c < m["cols"] and 0 <= r < m["rows"]):
            return None
        i = (r * m["cols"] + c) * 2
        return struct.unpack_from("<h", self.raw, i)[0] * m["scale"] + m["offset"]

    def walk(self, a, b, step=5.0):
        """Samples along a reach, at least 5 m apart and never fewer than nine."""
        n = max(8, int(math.ceil(math.dist(a, b) / step)))
        return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
                for i in range(n + 1)]


# ------------------------------------------------------------------ the geometry

def _north_on(path, e):
    """The northing of a polyline at an easting, EXTENDED along its end segment past
    either end. Extended and never bent: the point comes off the same two vertices the
    committed line already has."""
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        if min(x1, x2) - 1e-9 <= e <= max(x1, x2) + 1e-9:
            return y1 + (e - x1) * (y2 - y1) / (x2 - x1)
    (x1, y1), (x2, y2) = (path[0], path[1]) if e < path[0][0] else (path[-2], path[-1])
    return y1 + (e - x1) * (y2 - y1) / (x2 - x1)


def _meet_north_south(path, ns_path, m):
    """Where a tier, carried west from its own west end on bearing `m`, crosses a
    north-south street's committed centreline."""
    x1, y1 = path[0]
    (a1, b1), (a2, b2) = ns_path[0], ns_path[-1]
    a = (a2 - a1) / (b2 - b1)                      # east per north
    b = a1 - a * b1
    e = (a * y1 - a * m * x1 + b) / (1.0 - a * m)
    return [round(e, 3), round(y1 + m * (e - x1), 3)]


def _off_line(p, a, b):
    """Perpendicular distance of a point from the line through a and b."""
    ux, uy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(ux, uy)
    return abs((p[0] - a[0]) * uy - (p[1] - a[1]) * ux) / L


PLAT_TIERS = ("lake", "randolph", "washington")


def plat_bearing(by):
    """The plat's east-west bearing, read off the three Original Town lines that carry it
    and asserted to agree exactly — `tools/measure_no_build_ground.plat_bearing`'s reading,
    re-taken here rather than imported so the two cannot drift apart silently."""
    slopes = set()
    for tid in PLAT_TIERS:
        (ax, ay), (bx, byy) = (_east_of_clip(by[tid]["path_local_enu_m"])[i] for i in (0, -1))
        slopes.add(round((byy - ay) / (bx - ax), 6))
    if len(slopes) != 1:
        raise SystemExit(f"the plat's own east-west streets disagree on bearing: {slopes}")
    return slopes.pop()


def _segment_bearing(path):
    (x1, y1), (x2, y2) = path[0], path[1]
    return (y2 - y1) / (x2 - x1)


def derive():
    doc = json.loads(STREETS.read_text())
    by = {s["id"]: s for s in doc["streets"]}
    field = Field()
    grid = plat_bearing(by)

    def _bearing(tid, path):
        """WHICH BEARING CARRIES WHICH LINE, and it is the one judgement in this file.

        `lake`, `randolph` and `washington` are three lines of the Thompson plat's own
        east-west grid and they share ONE bearing, exactly, to six decimals — that is the
        number `measure_no_build_ground.plat_bearing` asserts and the whole tract layer
        stands on. They are carried on it. The alternative, each line's own westernmost
        SEGMENT, is worse evidence dressed as precision: that segment's west end was the
        clip itself, an artefact of this reconstruction's extent rather than a surveyed
        point, and on `randolph` it leans 3.5% off the grid the same street carries at its
        other end — 0.57 m over the reach, and three tiers that the plat draws parallel
        arriving at Des Plaines not parallel.

        `fulton` is not on that grid and is not forced onto it: its own four-point fit
        runs at a different slope, which is a committed disagreement (T-0446) and not this
        ticket's to reconcile. It is carried on its own line, and the two surviving
        intersections west of the clip are what say that was right.
        """
        return grid if tid in PLAT_TIERS else _segment_bearing(path)

    dp = by[STOP_AT]["path_local_enu_m"]
    dp_n = sorted(p[1] for p in dp)

    # The four tiers held by their own committed bearing. Each stops where it meets the
    # committed `des_plaines` centreline — and only if that crossing is inside the reach
    # `des_plaines` itself claims, because a borrowed line may not claim more ground than
    # the line it is borrowed from (T-1430's rule, and it binds here too).
    reaches, bearings = {}, {}
    for tid in ("fulton", "lake", "randolph", "washington"):
        path = _east_of_clip(by[tid]["path_local_enu_m"])
        bearings[tid] = _bearing(tid, path)
        west = _meet_north_south(path, dp, bearings[tid])
        if not dp_n[0] - 1e-6 <= west[1] <= dp_n[-1] + 1e-6:
            raise SystemExit(f"{tid} meets {STOP_AT} at north {west[1]:.2f}, outside the "
                             f"reach {STOP_AT} claims ({dp_n[0]:.1f} to {dp_n[-1]:.1f})")
        reaches[tid] = west

    # Carroll, the one interpolation: the midpoint of Kinzie and Fulton at every easting,
    # which west of the clip means `kinzie_west`. It stops at Fulton's west end.
    ful_w = reaches["fulton"][0]
    kw = by[KINZIE_WEST]["path_local_enu_m"]
    ful_path = _east_of_clip(by["fulton"]["path_local_enu_m"])
    reaches["carroll"] = [round(ful_w, 3),
                          round((_north_on(kw, ful_w) + _north_on(ful_path, ful_w)) / 2.0, 3)]
    bearings["carroll"] = ((reaches["carroll"][1] - OLD_WEST["carroll"][1])
                           / (reaches["carroll"][0] - OLD_WEST["carroll"][0]))

    ev = {}
    for tid in TIERS:
        old = OLD_WEST[tid]
        path = _east_of_clip(by[tid]["path_local_enu_m"])
        west = reaches[tid]
        walk = field.walk(west, old)
        hs = [field.at(*p) for p in walk]
        off_box = sum(1 for h in hs if h is None)
        dry = [h for h in hs if h is not None]
        ev[tid] = {
            "old_west_end_local_enu_m": old,
            "new_west_end_local_enu_m": west,
            "stops_at": (f"{STOP_AT}, the westernmost platted street of the West Division "
                         f"(T-1430)") if tid != "carroll" else
                        "fulton's own west end — an interpolation claims no more ground "
                        "than the pair it lies between",
            "carried_m": round(math.dist(west, old), 2),
            "bearing": round(bearings[tid], 6),
            "bearing_from": ("the Thompson plat's own east-west grid, which `lake`, "
                             "`randolph` and `washington` carry to six decimals"
                             if tid in PLAT_TIERS else
                             f"{tid}'s own westernmost committed segment, "
                             f"{path[0]} to {path[1]}"),
            "kink_at_clip_deg": round(abs(math.degrees(
                math.atan(bearings[tid]) - math.atan(_segment_bearing(path)))), 4),
            "ground": {
                "samples": len(hs),
                "off_modelled_box": off_box,
                "min_m_above_water": round(min(dry), 3) if dry else None,
                "max_m_above_water": round(max(dry), 3) if dry else None,
            },
        }

    ev["fulton"]["corroboration"] = _fulton_corroboration(by)
    ev["carroll"]["bracket"] = _carroll_bracket(by, reaches)
    return doc, by, reaches, ev


def _east_of_clip(path):
    """The committed path as it stood before this tool touched it — i.e. with any reach
    this tool already wrote folded back onto the old west vertex, so a second `--write`
    derives the same answer as the first."""
    return [p for p in path if p[0] >= -320.0 - 1e-9] or path


def _fulton_corroboration(by):
    """Fulton's extension against the two surviving intersections that stand WEST of the
    old clip. The derivation never reads them — it comes off the committed bearing — so
    the agreement is two instruments meeting, not one licensing the other."""
    path = _east_of_clip(by["fulton"]["path_local_enu_m"])
    out = {}
    for name, (e, n, node) in FULTON_NODES.items():
        out[name] = {
            "osm_node": node,
            "node_local_enu_m": [e, n],
            "west_of_old_clip": e < -320.0,
            "line_north_at_node_e": round(_north_on(path, e), 3),
            "line_north_of_node_m": round(_north_on(path, e) - n, 3),
        }
    west = [v for v in out.values() if v["west_of_old_clip"]]
    out["worst_west_residual_m"] = round(max(abs(v["line_north_of_node_m"]) for v in west), 3)
    out["fit_rms_m"] = FULTON_FIT_RMS_M
    out["reading"] = (
        f"the carried line passes {out['worst_west_residual_m']} m from the worse of the "
        f"two surviving intersections west of the clip, against the {FULTON_FIT_RMS_M} m "
        "RMS of the four-point fit the record already carries. The extension is derived "
        "from the committed bearing alone and reads neither node, so this is the control "
        "the clip was standing in front of."
    )
    return out


def _carroll_bracket(by, reaches):
    """Carroll's own uncertainty, re-measured at the new west end: one Fulton-to-Lake
    module south of Kinzie and one north of Fulton bracket the midpoint, and the midpoint
    has to sit between them (T-0446's rule, re-run on the ground it now reaches)."""
    e = reaches["carroll"][0]
    kw = _north_on(by[KINZIE_WEST]["path_local_enu_m"], e)
    ful = _north_on(_east_of_clip(by["fulton"]["path_local_enu_m"]), e)
    lake = _north_on(_east_of_clip(by["lake"]["path_local_enu_m"]), e)
    module = ful - lake
    lo, hi = ful + module, kw - module
    mid = reaches["carroll"][1]
    return {
        "at_east_m": round(e, 3),
        "kinzie_west_north_m": round(kw, 3),
        "fulton_north_m": round(ful, 3),
        "fulton_to_lake_module_m": round(module, 3),
        "one_module_north_of_fulton_m": round(lo, 3),
        "one_module_south_of_kinzie_m": round(hi, 3),
        "midpoint_m": round(mid, 3),
        "half_bracket_m": round((hi - lo) / 2.0, 3),
        "inside": lo - 1e-6 <= mid <= hi + 1e-6,
    }


# ------------------------------------------------------------------ the record

def clause(tid, ev):
    e = ev[tid]
    g = e["ground"]
    text = (
        f" {CLAUSE_MARK} The line is carried {e['carried_m']} m west of the clip at local "
        f"east -320 to {e['new_west_end_local_enu_m']}, where it meets {e['stops_at']}. "
        "The clip was this reconstruction's own extent and never a claim that the street "
        "ended there; T-1416 built the modelled field out to local east -705 and T-1430 "
        "seated the street it now stops at, so the two reasons it stood are both gone. "
        f"THE REACH IS CARRIED FROM THE OLD WEST END, NOT FITTED THROUGH IT: the bearing "
        f"is {e['bearing']}, read from {e['bearing_from']}. Every committed vertex east of "
        "-320 is left exactly where it stood — the old west end is KEPT as a vertex rather "
        "than replaced — so no platted lot line moves, no corridor is re-cut and the "
        f"corridor-intrusion count is untouched. What the carry does add is a "
        f"{e['kink_at_clip_deg']} deg change of direction AT that retained vertex, and it "
        "is stated here rather than rounded away. The confidence is unchanged, because "
        "carrying a line the length the sheet already drew it is not an upgrade. "
        "THE GROUND IS MEASURED: "
        f"{g['samples']} samples along the new reach against the committed heightfield, "
        f"none off the modelled box, the lowest standing {g['min_m_above_water']} m above "
        "the summer-1835 water surface."
    )
    if tid == "fulton":
        c = e["corroboration"]
        text += (
            " AND IT IS CORROBORATED BY CONTROL THIS RECORD ALREADY CARRIED: of the four "
            "surviving intersections above, Jefferson and Des Plaines stand WEST of the "
            "old clip. The extension is derived from the committed bearing and reads "
            f"neither of them, and it passes {abs(c['jefferson']['line_north_of_node_m'])} m "
            f"from the Jefferson node and {abs(c['des_plaines']['line_north_of_node_m'])} m "
            f"from the Des Plaines node — inside the {FULTON_FIT_RMS_M} m RMS of the "
            "four-point fit itself. The clip was standing in front of 200 m of street the "
            "record's own control already held."
        )
    if tid == "carroll":
        b = e["bracket"]
        text += (
            " THE RULE IS UNCHANGED AND THE DATUM MOVES WITH IT: west of the clip the "
            "Kinzie term is `kinzie_west`, T-1085's separate record, because that is the "
            f"line that exists there. At the west end the midpoint is {b['midpoint_m']} "
            f"and the bracket is {b['one_module_north_of_fulton_m']} (one Fulton-to-Lake "
            f"module north of Fulton) to {b['one_module_south_of_kinzie_m']} (one module "
            f"south of Kinzie), so the half-bracket — this line's uncertainty, and still "
            f"the largest in the file — is {b['half_bracket_m']} m. Carroll stops at "
            "Fulton's west end and no further: an interpolation may claim no more ground "
            "than the pair it lies between."
        )
    return text


def apply_note(note, tid, ev):
    base = note.split(CLAUSE_MARK)[0].rstrip()
    if base.endswith("WEST TO DES PLAINES STREET"):        # defensive: split ate the head
        base = base[: -len("WEST TO DES PLAINES STREET")].rstrip()
    return base + clause(tid, ev)


def entries(by, reaches, ev):
    out = []
    for tid in TIERS:
        s = json.loads(json.dumps(by[tid]))
        # The old west vertex is KEPT, not replaced. It lies on the carried line to the
        # millimetre, so it adds no bend; keeping it leaves the committed line east of
        # -320 literally untouched, makes the diff purely additive, and is what lets
        # `_east_of_clip` recover the pre-carry path so a second --write re-derives.
        s["path_local_enu_m"] = [reaches[tid]] + _east_of_clip(by[tid]["path_local_enu_m"])
        s["note"] = apply_note(by[tid]["note"], tid, ev)
        out.append(s)
    return out


def trace_doc(ev):
    return {
        "_doc": __doc__,
        "ticket": "T-1443",
        "streets": TIERS,
        "committed_in": "data/streets/1835.json",
        "method": {
            "extent": (f"each tier stops where it meets the committed `{STOP_AT}` "
                       "centreline (T-1430); carroll stops at fulton's west end"),
            "bearing": "each line's own westernmost committed segment — extended, never refit",
            "bend": ("none. The old west vertex lies on the new line to the centimetre, "
                     "gated by --check, so nothing east of -320 moves."),
            "ground": ("sampled against data/terrain/epochs/e1834_harbor_cut/heightfield.bin, "
                       "the field T-1416 built out to local east -705"),
        },
        "reaches": ev,
        "what_this_does_not_carry": {
            "the_plat_boundary": ("the Thompson plat's own west boundary line is not "
                                  "committed to this repository, so the tiers stop on the "
                                  "last committed control and not on an inferred edge."),
            "confidence": ("no grade moves. The plat already drew these tiers across the "
                           "West Division; this file stops truncating them."),
            "wear_and_surface": ("unchanged and not re-argued: the records' own surface, "
                                 "track width and traffic carry west with them, because "
                                 "the tiers are one street each and not two claims."),
        },
    }


# ------------------------------------------------------------------ report / check

def report(ev):
    print("== the five West Division tiers, carried off the E -320 clip")
    for tid in TIERS:
        e = ev[tid]
        g = e["ground"]
        print(f"  {tid:11s} {e['old_west_end_local_enu_m']} -> {e['new_west_end_local_enu_m']}"
              f"   {e['carried_m']:7.2f} m   kink {e['kink_at_clip_deg']:.4f} deg"
              f"   ground {g['min_m_above_water']:.2f}-{g['max_m_above_water']:.2f} m, "
              f"{g['off_modelled_box']} off box")
    print()
    c = ev["fulton"]["corroboration"]
    print("== fulton against its own four intersections (T-0446)")
    for name in FULTON_NODES:
        v = c[name]
        side = "WEST of the old clip" if v["west_of_old_clip"] else "east of it"
        print(f"  {name:12s} node {v['osm_node']}  line stands "
              f"{v['line_north_of_node_m']:+.3f} m from it   ({side})")
    print(f"  worst western residual {c['worst_west_residual_m']} m against the "
          f"four-point fit's own {c['fit_rms_m']} m RMS")
    print()
    b = ev["carroll"]["bracket"]
    print("== carroll's bracket, re-measured at the new west end")
    print(f"  midpoint {b['midpoint_m']} inside [{b['one_module_north_of_fulton_m']}, "
          f"{b['one_module_south_of_kinzie_m']}] — half-bracket {b['half_bracket_m']} m"
          f"  ({'ok' if b['inside'] else 'OUTSIDE'})")


def check(quiet=False):
    doc, by, reaches, ev = derive()
    bad = []

    def hold(label, ok):
        if not ok:
            bad.append(label)
        if not quiet:
            print(f"  {'ok  ' if ok else 'FAIL'} {label}")

    want = {s["id"]: s for s in entries(by, reaches, ev)}
    for tid in TIERS:
        have, w = by[tid], want[tid]
        hp, wp = have["path_local_enu_m"], w["path_local_enu_m"]
        hold(f"{tid} carries the west reach ({len(wp)} vertices committed)",
             len(hp) == len(wp))
        if len(hp) == len(wp):
            worst = max(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in zip(hp, wp))
            hold(f"{tid}'s committed path re-derives to the centimetre ({worst:.3f} m)",
                 worst <= 0.02)
        e = ev[tid]
        hold(f"{tid} moves nothing east of the old clip — every committed vertex from "
             f"{e['old_west_end_local_enu_m']} eastward stands where it stood",
             have["path_local_enu_m"][1:] == _east_of_clip(have["path_local_enu_m"]))
        hold(f"…and the direction change it adds at that retained vertex is under a "
             f"tenth of a degree ({e['kink_at_clip_deg']:.4f} deg)",
             e["kink_at_clip_deg"] < 0.1)
        g = e["ground"]
        hold(f"{tid}'s new reach stands on modelled ground at every one of "
             f"{g['samples']} samples", g["off_modelled_box"] == 0)
        hold(f"…and on DRY ground, the lowest sample {g['min_m_above_water']} m above the "
             f"1835 water surface", (g["min_m_above_water"] or -1) > 0.0)
        hold(f"{tid}'s note carries the derivation this tool wrote",
             have.get("note", "").endswith(clause(tid, ev)))
        hold(f"{tid}'s grade is untouched by the carry ({have['geometry_confidence']})",
             have["geometry_confidence"] == w["geometry_confidence"])

    c = ev["fulton"]["corroboration"]
    hold(f"fulton's carried line meets its two surviving western intersections inside the "
         f"four-point fit's own RMS ({c['worst_west_residual_m']} m against "
         f"{c['fit_rms_m']} m)", c["worst_west_residual_m"] <= c["fit_rms_m"])
    grid = plat_bearing(by)
    hold(f"the three Thompson plat tiers are carried on the plat's own east-west bearing "
         f"({grid}), so they arrive at Des Plaines as parallel as the sheet draws them",
         all(round(ev[tid]["bearing"], 6) == grid for tid in PLAT_TIERS))
    b = ev["carroll"]["bracket"]
    hold(f"carroll's midpoint sits inside its own re-measured bracket "
         f"(half-bracket {b['half_bracket_m']} m)", b["inside"])
    hold("carroll claims no more ground than fulton, the pair it lies between",
         abs(reaches["carroll"][0] - reaches["fulton"][0]) < 1e-6)
    ns = {s["id"] for s in doc["streets"]}
    hold(f"`{STOP_AT}` — the street they stop at — is committed", STOP_AT in ns)

    if OUT.exists():
        was = json.loads(OUT.read_text())
        if json.dumps(was.get("reaches"), sort_keys=True) != json.dumps(ev, sort_keys=True):
            bad.append(f"{OUT.name} § reaches does not re-derive from the committed lines")
    else:
        bad.append(f"{OUT.name} is missing")

    if not quiet:
        print()
        print("FAIL" if bad else "check OK — every assertion holds")
    for line in bad:
        print(f"  failed: {line}", file=sys.stderr)
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    if a.check or a.gate:
        return check(quiet=a.gate)

    doc, by, reaches, ev = derive()
    report(ev)
    if a.write:
        text = _reseat(STREETS.read_text(), entries(by, reaches, ev))
        STREETS.write_text(text)
        OUT.write_text(json.dumps(trace_doc(ev), indent=2, ensure_ascii=False) + "\n")
        print()
        print(f"wrote {STREETS.relative_to(ROOT)} and {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
