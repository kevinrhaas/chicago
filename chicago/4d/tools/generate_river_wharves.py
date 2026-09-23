#!/usr/bin/env python3
"""Derive the town's river wharves from the records that state one.

    python3 tools/generate_river_wharves.py            write the record
    python3 tools/generate_river_wharves.py --check    re-derive and diff, write nothing

WHY THIS EXISTS. `docs/ROADMAP.md` K5 (e) asks for *"docks/wharves at the
forwarding houses"* and ticket T-0041 is that clause. Two records in this dataset
state a dock and both of them state it in the same sentence of the same dossier —
*"Kinzie & Hunter and Dole & Newberry each had a warehouse with its dock along the
river front"* (docs/research/03-structures-north.md §3.10) — and Andreas names
*"Newberry & Dole's wharf"* independently, as the place the schooner *Illinois*
was cheered on 12 July 1834 (scan p. 503). Until now BOTH docks carried
`geometry: "absent"`: the strongest chip this project hands out, over nothing at
all, in front of a bare bank. `docs/LIBERTIES.md` L66 recorded that as owed.

So the FACT of a wharf at these two frontages is the best-attested thing on this
layer, and every dimension of it is invented. That is `reconstructed` in this
project's third tier, which AGENTS.md § RECONSTRUCTED IS A TIER says is a licence
to build rather than an admission of defeat.

THE RULE, and it is the whole answer to "why these frontages and no others":

    a sidecar standing on the scene date whose own `dock` attribute is true.

T-0041 shipped that rule with a grade clause — attested or inferred only, no
`reconstructed`, because a dock resting on a reconstructed dock read as an
invention on an invention — and it selected exactly two records. On 2026-08-18
the owner overruled the rationing, verbatim "you can add more docks!" (T-0062,
with the standing ruling in AGENTS.md § RECONSTRUCTED IS A TIER), so five South
Water merchant records now STATE a reconstructed landing, each with its bound in
its own note, and this generator draws them. The selection still lives in the
data: a record with no dock statement — the Temple Building's meeting house on
the same frontage, the lumber landing, the ferry — still gets no wharf, and
"why this frontage" is still answered by a record rather than by this file.

THE WEST BANK WAS OUT OF THAT PASS BY CONSTRUCTION, NOT BY MEASUREMENT (T-0107).
T-0062 stated its five docks on *South Water merchants*, so the town's other two
shores were never asked the question — the North Division shore only carried a
wharf because Kinzie & Hunter's dock happens to be attested, and the west bank at
Wolf Point carried none at all. That is a fact about which records were edited on
2026-08-19, not a finding about Wolf Point. So the trade test now runs on every
river frontage in the town, whichever bank it stands on, and on the west bank it
selects exactly ONE record: Robert A. Kinzie's storehouse, "dealing in groceries
and Indian goods", whose own position note had already reasoned that "a storehouse
trading goods off canoes has a positive reason to face the landing" and set its
facade due east onto the water on that reading. The other four buildings in that
row — Wentworth's tavern, James Kinzie's residence, the Robinson and Caldwell
cabins, Father Walker's log meeting house — state no dock and get none: lodging,
dwelling and worship take nothing off a canoe, which is the Temple Building's
exclusion carried across the river.

AND THE BANK BENDS AT WOLF POINT, which is what clause 6 is for. This layer's
deck is a RECTANGLE set on the bank's own tangent — one standard form, so its
dimensions are invented once (L132) rather than once per site — and a rectangle
run against a curve can put the far end of its face behind the bank, on dry
ground. PR #258 measured that at Hogan's store, whose face runs from 1.10 m of
water at one end to −0.34 m at the other, and refused it rather than invent a
bespoke outline for one frontage. That refusal is now a clause with the measured
figure on the record, the same way the trace-reach refusals carry theirs.

WHAT IS DERIVED AND WHAT IS INVENTED — the division this file exists to keep
auditable:

  DERIVED, from committed data, no free numbers at all
    * the wall the wharf serves: the footprint's own max-`v` edge and the
      committed facade bearing, through `docs/GLB-CONTRACT.md`'s frame — the same
      three lines `tools/generate_business_signboards.py` composes.
    * WHERE the wharf stands: the traced 1834 bank line, nearest point to the
      part of it IN FRONT OF that wall (clause 3b). The deck runs ALONG the
      bank's own tangent, not square to the building — a wharf follows the
      river, and the two differ by 20° here. That bank is TWO TRACING WINDOWS of
      the Wright 1834 sheet joined at a seam they agree on to under a metre —
      `river.geojson` at the forks and `shoreline.geojson` through the harbour
      reach — which is the composition `terrain_spec.json` declares in
      `shore_runs` and `terrain_gen.py` already measures a shore with (T-0106).
      See `bank_lines()`.
    * how deep the water is at its face, and how far it stands clear of the
      building it serves: sampled from the committed heightfield, reported rather
      than assumed, so what the invented outline implies is on the record.

  INVENTED, and every one of them is in `form` with its bound stated
    * how far out the face stands (6.0 m), how far the heel ties back into the
      bank (2.0 m), how far the deck runs past the building each way (3.0 m),
      the deck's thickness, its freeboard rule and its snubbing posts.

Nothing here is baked. A deck on cribs is a box on boxes standing on ground and
water this project already draws, so it is derived from committed numbers and
drawn at load by `renderers/web/js/wharves.js` — the argument that already lets
`data/enclosures/` draw a fence from a perimeter, `data/signage/` hang a board off
a wall and `data/yard/` stand a barrel on the footway. `tools/check.sh` re-derives
this file's output byte for byte, because "which frontage gets a wharf" is a rule
and a rule has to be auditable.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIDECARS = ROOT / "data" / "sidecars" / "1835"
EPOCH = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
OUT = ROOT / "data" / "wharves" / "river_landings.json"

sys.path.insert(0, str(ROOT / "tools"))
from heightfield import Heightfield          # noqa: E402  (path set above)

# The grades a dock statement may carry. T-0041 shipped this tuple WITHOUT
# `reconstructed` — a dock resting on a reconstructed dock read as an invention
# on an invention — and the owner overruled that reading on 2026-08-18, verbatim
# "you can add more docks!", with the general ruling recorded in AGENTS.md
# § RECONSTRUCTED IS A TIER: be liberal with reconstructed items when asked,
# label them as such. So a sidecar may now STATE a reconstructed dock (T-0062
# authored five, each with its bound in its own note) and this generator draws
# it. What has not changed: the selection still lives in the DATA — a sidecar
# with no dock statement still gets no wharf, so "why this frontage" is still
# answered by a record and never by this file.
DOCK_GRADES = ("attested", "documented", "inferred", "reconstructed")

# --- the invented figures, all of them, in one place ------------------------ #
# They are copied into the record's `form` block with their reasons; they are
# here as constants so the generator and the record cannot come to disagree.
FACE_OUT_M = 6.0        # how far the deck's face stands beyond the traced bank
HEEL_IN_M = 2.0         # how far its landward edge ties back into the bank
APRON_M = 3.0           # how far it runs past the building it serves, each way
DECK_T_M = 0.14         # the plank deck's thickness
FREEBOARD_M = 0.90      # the least the deck top may stand above the water plane
POST_SIDE_M = 0.22      # a snubbing post, square
POST_HEIGHT_M = 0.75    # and how far it stands proud of the deck
STAIR_WIDTH_M = 2.4     # the boarding stair at the landward edge, across
STAIR_TREAD_M = 0.75    # each tread's depth, landward
STAIR_RISE_M = 0.30     # the most any one tread may rise
CRIB_W_M = 1.20         # the crib wall under the deck's outer face and its ends

# The least water a drawn landing may have at its face. NOT a new number: it is
# the floor `tools/smoke_renderer.mjs` has asserted on every drawn wharf since
# T-0041 ("no deck floats and every crib reaches the bed"), moved here so the
# record refuses in writing with the sounding rather than leaving the browser
# test to discover it. One figure, stated once, read by both instruments.
MIN_DEPTH_M = 0.50


# Weakest first. A run composed of two traced windows carries the weaker of the
# two grades, never the better one: a line is only as good as its worst stretch.
CONF_ORDER = ("conjectural", "reconstructed", "inferred", "documented", "attested")


def _depth_span(wharves: list) -> str:
    """How much water the drawn faces actually stand in, as a sentence fragment.

    Derived rather than written down: the figure in this note used to be "about
    1.2 m of water at both sites", true of the two wharves that existed when it
    was typed and quietly false of every one added since.
    """
    d = sorted(x for w in wharves for x in w["depth_at_face_m"])
    if not d:
        return "no drawn face to measure"
    return (f"between {d[0]:.2f} m and {d[-1]:.2f} m of water across the "
            f"{len(wharves)} drawn faces (measured per wharf in depth_at_face_m)")


def _weakest(grades) -> str:
    """The weakest grade present, or the first one if the model does not know it."""
    known = [g for g in grades if g in CONF_ORDER]
    return CONF_ORDER[min(CONF_ORDER.index(g) for g in known)] if known else "inferred"


def _seam(run: list, p: tuple) -> tuple[float, int, float]:
    """(distance, segment index, parameter) of the foot of `p` on `run`."""
    best = (float("inf"), 0, 0.0)
    for i, (a, b) in enumerate(zip(run, run[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx
                                                   + (p[1] - a[1]) * dy) / L2))
        d = math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))
        if d < best[0]:
            best = (d, i, t)
    return best


def _traced_in(bank: dict, foot_s: float) -> str | None:
    """Which of a composed run's tracing windows the foot at `foot_s` lies in.

    `None` for a bank that is not composed — including the ones `selftest()`
    builds by hand, which have no window at all.
    """
    members = bank.get("members") or []
    if len(members) < 2:
        return members[0]["id"] if members else None
    s0 = bank.get("base_s0", 0.0)
    return (members[0]["id"] if s0 <= foot_s <= s0 + bank.get("base_len", 0.0)
            else members[1]["id"])


def _run_length(points: list) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1])
               for a, b in zip(points, points[1:]))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _round(x: float, places: int = 2) -> float:
    """Round toward a stable decimal so `--check` diffs bytes, not float noise."""
    return round(x + 0.0, places) + 0.0


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres.

    `docs/GLB-CONTRACT.md`: polygon `u` → +X, polygon `v` → −Z, ENU `local_e` → +X
    and `local_n` → −Z, and the node's yaw is `-rotation_deg` about +Y. Identical
    to `tools/generate_business_signboards.py::_to_enu`, deliberately: two layers
    reading the same frame two ways is how a building grows two front walls.
    """
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def _front_edge(polygon: list) -> tuple[float, float, float]:
    """The wall the record faces out of: the footprint's max-`v` edge."""
    vmax = max(p[1] for p in polygon)
    on = [p[0] for p in polygon if abs(p[1] - vmax) < 1e-6]
    if len(on) < 2:
        return 0.0, 0.0, vmax
    return min(on), max(on), vmax


def bank_lines() -> list[dict]:
    """The traced 1834 bank of each division, in local ENU metres.

    THE BANK IS TWO TRACING WINDOWS, NOT ONE, AND THIS LAYER USED TO READ ONLY
    THE FIRST (T-0106). `tools/trace_river.py` works a 1120 px window of the
    Wright 1834 sheet centred on the forks, so the bank polylines it writes into
    `river.geojson` stop at local E +390 — where the WINDOW closed, not where the
    bank did. `tools/trace_shoreline.py` picks the same waterline up off the same
    sheet at E +314 and carries it east past the Dearborn drawbridge (E +699) to
    the lake, and `shoreline.geojson` has held that trace since 2026-08-10. The
    two windows overlap between E +314 and E +390 and AGREE THERE TO UNDER A
    METRE at the seam, which is what licenses reading them as one line.

    So nothing here is extended by eye and nothing new is traced: the run is the
    composition `terrain_spec.json` already declares in `shore_runs`, which is
    also how `generators/terrain_gen.py::build_field` measures a division's
    waterline — it takes the minimum distance over every run of that division,
    across both files. Two consumers of one waterline reading it two ways is how
    a river grows two banks; before this, the wharf layer believed the south bank
    ended 309 m short of the drawbridge and refused three stated landings for
    standing beyond a trace that was there all along.

    The join, stated so it cannot drift:

      1. the division's `river.geojson` run is taken WHOLE and oriented so its
         last vertex is the end nearer the harbour-reach run — no committed
         vertex is dropped, moved or resampled, so every wharf already standing
         keeps the bank foot it had;
      2. the harbour-reach run is oriented to continue away from that end;
      3. the foot of the forks run's terminal vertex is found on it, and only the
         vertices BEYOND that foot are appended. The overlap is therefore
         corroboration, never geometry — the seam offset is the distance between
         the two windows' readings of one bank and is reported in the record.

    `river.geojson` is EPSG:26916 and the scene is local ENU from
    `data/datum.json`'s origin, which is the one conversion this file makes.
    """
    datum = _load(ROOT / "data" / "datum.json")
    oe, on = float(datum["origin_utm_e"]), float(datum["origin_utm_n"])
    spec = _load(EPOCH / "terrain_spec.json")

    feats: dict[str, tuple[str, dict]] = {}
    for fname in ("river.geojson", "shoreline.geojson"):
        for f in _load(EPOCH / fname).get("features", []):
            if (f.get("geometry") or {}).get("type") == "LineString":
                feats[f.get("id")] = (fname, f)

    def local(fid: str) -> list:
        _, f = feats[fid]
        return [(x - oe, y - on) for x, y in f["geometry"]["coordinates"]]

    def member(fid: str) -> dict:
        fname, f = feats[fid]
        props = f.get("properties") or {}
        return {
            "id": fid,
            "from": f"data/terrain/epochs/{EPOCH.name}/{fname}",
            "traced_by": ("tools/trace_river.py" if fname == "river.geojson"
                          else "tools/trace_shoreline.py"),
            "name": props.get("name"),
            "confidence": props.get("confidence"),
            "sources": props.get("sources") or [],
        }

    by_div: dict[str, list] = {}
    for run in spec.get("shore_runs", []):
        by_div.setdefault(run.get("division"), []).append(run)

    out: list[dict] = []
    for division, runs in by_div.items():
        base = [r for r in runs if r.get("from") == "river.geojson"]
        ext = [r for r in runs if r.get("from") == "shoreline.geojson"]
        if not base or base[0]["id"] not in feats:
            continue
        pts = local(base[0]["id"])
        members = [member(base[0]["id"])]
        seam = None
        base_s0, base_len = 0.0, _run_length(pts)
        if ext and ext[0]["id"] in feats:
            tail = local(ext[0]["id"])
            # WHICH END of the forks run the harbour reach continues from. The
            # forks run itself is never reversed: its direction is the committed
            # trace's, and a deck's tangent — and therefore the corner order of
            # every quad already drawn off it — comes straight off that.
            d_head = min(math.hypot(pts[0][0] - q[0], pts[0][1] - q[1])
                         for q in (tail[0], tail[-1]))
            d_foot = min(math.hypot(pts[-1][0] - q[0], pts[-1][1] - q[1])
                         for q in (tail[0], tail[-1]))
            at_head = d_head < d_foot
            end = pts[0] if at_head else pts[-1]
            if (math.hypot(end[0] - tail[-1][0], end[1] - tail[-1][1])
                    < math.hypot(end[0] - tail[0][0], end[1] - tail[0][1])):
                tail = tail[::-1]               # orient it to lead away from the seam
            gap, i, t = _seam(tail, end)        # append only past the foot
            beyond = tail[i + 1:] if t < 1.0 else tail[i + 2:]
            if beyond:
                members.append(member(ext[0]["id"]))
                seam = {
                    "at_local_enu_m": [_round(end[0]), _round(end[1])],
                    "windows_disagree_m": _round(gap),
                    "vertices_appended": len(beyond),
                    "joined_at": "head" if at_head else "tail",
                }
                if at_head:
                    pts = beyond[::-1] + pts
                    base_s0 = _run_length(beyond) + math.hypot(
                        beyond[0][0] - end[0], beyond[0][1] - end[1])
                else:
                    pts = pts + beyond
        out.append({
            "id": division,
            "name": (feats[base[0]["id"]][1].get("properties") or {}).get("name"),
            "confidence": _weakest(m["confidence"] for m in members),
            "sources": sorted({s for m in members for s in m["sources"]}),
            "members": members,
            "seam": seam,
            "base_s0": base_s0,
            "base_len": base_len,
            "points": pts,
        })
    out.sort(key=lambda b: b["id"])
    return out


def in_front_of(points: list, wall_a: tuple, wall_b: tuple, half: float) -> list:
    """The stretches of bank that lie IN FRONT OF the wall, as sub-polylines.

    "In front of" is the strip of the wall's own line the deck will occupy:
    a bank point counts when its projection onto that line falls within
    ±`half` of the wall's middle, which is the deck's own run (the frontage
    plus its apron at each end).

    WHY THE FOOT NEEDS THIS AT ALL (T-0106). The rule used to be the nearest
    point on the bank, full stop, and on the forks-window trace — a smooth
    curve in front of a row of warehouses — the nearest point is always the
    bank the wall faces. The harbour-reach trace is not smooth: it carries
    re-entrants, and one of them is a 10 m-wide slot cutting 32 m into the
    south bank at local E +463. Peck's store fronts the river 29 m west of
    that slot, and the slot's tip is 30.3 m from its river wall against 41.2 m
    for the bank the wall actually faces — so a nearest-point rule laid an
    18 m deck ACROSS THE HEAD OF THE SLOT, square to the river, with a third of
    its face standing 0.37 m above the water on dry ground. That is the same
    class of thing clause 4 refuses when a deck laps the wall it serves.

    Clipping is done on SEGMENTS and not on vertices: the trace's vertices are
    tens of metres apart, so a 9 m band usually contains none of them while the
    bank runs straight through it. Endpoints are interpolated, so the returned
    stretches are the bank itself and not a subsample of it.
    """
    L = math.hypot(wall_b[0] - wall_a[0], wall_b[1] - wall_a[1]) or 1.0
    ux, uy = (wall_b[0] - wall_a[0]) / L, (wall_b[1] - wall_a[1]) / L
    mx, my = (wall_a[0] + wall_b[0]) / 2.0, (wall_a[1] + wall_b[1]) / 2.0

    def s_of(p):
        return (p[0] - mx) * ux + (p[1] - my) * uy

    runs: list[list] = []
    run: list = []
    for a, b in zip(points, points[1:]):
        sa, sb = s_of(a), s_of(b)
        ds = sb - sa
        if abs(ds) < 1e-12:                       # parallel to the wall
            lo, hi = (0.0, 1.0) if abs(sa) <= half else (1.0, 0.0)
        else:
            t1, t2 = (half - sa) / ds, (-half - sa) / ds
            lo, hi = max(0.0, min(t1, t2)), min(1.0, max(t1, t2))
        if hi <= lo:                              # this segment misses the band
            if len(run) > 1:
                runs.append(run)
            run = []
            continue
        pa = (a[0] + lo * (b[0] - a[0]), a[1] + lo * (b[1] - a[1]))
        pb = (a[0] + hi * (b[0] - a[0]), a[1] + hi * (b[1] - a[1]))
        if run and math.hypot(run[-1][0] - pa[0], run[-1][1] - pa[1]) > 1e-9:
            if len(run) > 1:
                runs.append(run)
            run = []
        run = (run or [pa]) + [pb]
        if hi < 1.0 - 1e-12:                      # the band closed inside [a,b]
            runs.append(run)
            run = []
    if len(run) > 1:
        runs.append(run)
    return runs


def nearest_on(points: list, p: tuple) -> tuple[float, tuple, tuple, float, float]:
    """(distance, foot point, unit tangent, arclength at foot, total arclength)
    for the nearest segment of a polyline. The two arclengths exist for clause
    4b: a deck may only stand where the bank is actually TRACED, and the test is
    its run against the trace's own extent rather than a guess about endpoints.
    """
    best = None
    s = 0.0
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                for a, b in zip(points, points[1:]))
    for a, b in zip(points, points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        L = math.sqrt(L2) or 1.0
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx
                                                   + (p[1] - a[1]) * dy) / L2))
        q = (a[0] + t * dx, a[1] + t * dy)
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        if best is None or d < best[0]:
            best = (d, q, (dx / L, dy / L), s + t * L, total)
        s += L
    return best


def _face_stations(face: tuple, tangent: tuple, half: float) -> list[tuple]:
    """Where the depth under the deck's face is sampled, at about 1 m intervals.

    THREE POINTS WERE NOT ENOUGH AND THE BEND AT WOLF POINT IS WHY (T-0107). The
    record has always reported the depth at the face's two ends and its middle,
    and that is what it still reports; but a deck outline is a RECTANGLE run
    against a bank that curves, so the shallowest metre of a face is not obliged
    to be one of those three. Sampling the run is what lets clause 6 answer "is
    this deck afloat" about the whole face instead of about three points of it.
    """
    n = max(3, int(round(2.0 * half)) + 1)
    return [(face[0] + tangent[0] * t, face[1] + tangent[1] * t)
            for t in (-half + 2.0 * half * i / (n - 1) for i in range(n))]


def derive_one(sid: str, sc: dict, banks: list, field) -> tuple[str | None, dict | None]:
    """One candidate through the clause table: ('wharf'|'refused'|None, row).

    Split out of `build_record` by T-0107 so the clauses can be fired on
    constructed frontages by `selftest()` as well as on the committed sidecars. A
    refusal clause that never fires on the dataset is a clause nobody has seen
    work, and clause 6 refuses nothing in the town as it stands — every drawn
    face is afloat by a metre. So it is proved on a stand built for it instead of
    being taken on trust.
    """
    dock = (sc.get("attributes") or {}).get("dock")
    if not isinstance(dock, dict) or not dock.get("value"):
        return None, None                                        # clause 1
    grade = dock.get("confidence")
    if grade not in DOCK_GRADES:
        return "refused", {"structure_id": sid, "why": (
            f"its dock is graded {grade!r}, which is not a grade this "
            "project's confidence model has. A statement this layer cannot "
            "classify is a statement it does not draw.")}         # clause 2

    place = sc.get("placement") or {}
    poly = (sc.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3:
        return "refused", {"structure_id": sid,
                           "why": "no footprint polygon — no wall to serve."}
    u0, u1, vmax = _front_edge(poly)                              # clause 3
    wall_a = _to_enu(u0, vmax, place)
    wall_b = _to_enu(u1, vmax, place)
    mid = ((wall_a[0] + wall_b[0]) / 2.0, (wall_a[1] + wall_b[1]) / 2.0)
    frontage = math.hypot(wall_b[0] - wall_a[0], wall_b[1] - wall_a[1])

    half = frontage / 2.0 + APRON_M

    # CLAUSE 3b (T-0106): the foot is the nearest bank IN FRONT OF the wall, not
    # the nearest bank anywhere. See `in_front_of` for the re-entrant that made
    # the difference. The choice is made on the clipped stretches; the tangent
    # and the two arclengths are then read off the FULL run, so clause 4b still
    # measures the deck against the whole traced bank.
    candidates = [(nearest_on(run, mid), b)
                  for b in banks
                  for run in in_front_of(b["points"], wall_a, wall_b, half)]
    if not candidates:
        return "refused", {"structure_id": sid, "why": (
            "no traced bank stands in front of its river wall — nothing within "
            "the deck's own run of the wall's line — so there is no frontage "
            "here for a landing to be derived from.")}            # clause 3b
    (_d, chosen, _t, _s, _l), bank = min(candidates, key=lambda r: r[0][0])
    _d, foot, tangent, foot_s, bank_len = nearest_on(bank["points"], chosen)
    dist = math.hypot(mid[0] - foot[0], mid[1] - foot[1])
    # Outward is across the bank, away from the building it serves. Deriving
    # it from the building rather than from the polygon's winding is what
    # keeps a wharf on the water when a bank line is re-traced the other way.
    nx, ny = -tangent[1], tangent[0]
    if (foot[0] - mid[0]) * nx + (foot[1] - mid[1]) * ny < 0:
        nx, ny = -nx, -ny

    # CLAUSE 4b (T-0062): every metre of the deck must stand off a traced
    # metre of bank. The 1834 bank polylines end at local E 390 and three
    # stated South Water landings lie east of that; without this clause all
    # three snapped to the trace's terminal vertex and stacked on one point
    # — a modelling error wearing three wharves' clothes. A landing refused
    # here is STATED AND NOT DRAWN until the trace reaches it (T-0106),
    # because a deck derived from a bank that is not there is derived from
    # nothing.
    if foot_s - half < 0.0 or foot_s + half > bank_len:
        return "refused", {"structure_id": sid, "why": (
            "its frontage lies beyond the traced 1834 bank line, so part of "
            "its deck would stand off bank nobody traced. The dock "
            "statement stands; the landing is drawn when the trace reaches "
            "this reach (T-0106).")}                              # clause 4b

    heel = (foot[0] - nx * HEEL_IN_M, foot[1] - ny * HEEL_IN_M)
    face = (foot[0] + nx * FACE_OUT_M, foot[1] + ny * FACE_OUT_M)
    corners = [                       # heel-left, heel-right, face-right, face-left
        (heel[0] - tangent[0] * half, heel[1] - tangent[1] * half),
        (heel[0] + tangent[0] * half, heel[1] + tangent[1] * half),
        (face[0] + tangent[0] * half, face[1] + tangent[1] * half),
        (face[0] - tangent[0] * half, face[1] - tangent[1] * half),
    ]

    # The deck may not reach the building it serves: a wharf that laps a wall
    # is a modelling error wearing a wharf's clothes, and the two placements
    # were authored with exactly this strip left clear ("about 8 m back from
    # the traced bank to leave the dock its ground"; "about 14 m back ... so
    # the strip between it and the water can carry the dock").
    clearance = min(nearest_on([wall_a, wall_b], c)[0] for c in corners[:2])
    if clearance < 1.0:
        return "refused", {"structure_id": sid, "why": (
            f"its heel would come within {clearance:.2f} m of the building's "
            "own river wall. A wharf that laps the wall it serves is a "
            "modelling error, and this record refuses to draw one.")}  # clause 4

    # What the invented outline implies, measured on the committed bed rather
    # than assumed: how much water a vessel lying at this face would have. The
    # three the record reports are the face's ends and its middle; the run at
    # 1 m is what clauses 5 and 6 are decided on.
    stations = _face_stations(face, tangent, half)
    run = [-field.height(e, n) if field and field.covers(e, n) else None
           for e, n in stations]
    depths = [run[0], run[len(run) // 2], run[-1]]
    if any(d is None for d in run):
        off = next(i for i, d in enumerate(run) if d is None)
        where = -half + 2.0 * half * off / (len(run) - 1)
        return "refused", {"structure_id": sid, "why": (
            "its face falls outside the modelled ground "
            f"{abs(where):.1f} m from its centre, so the depth at it "
            "cannot be measured and the wharf is not drawn.")}    # clause 5

    # CLAUSE 6 (T-0107): THE FACE HAS TO BE AFLOAT ALONG ITS WHOLE RUN. The deck
    # outline is a rectangle set on the bank's own tangent, and THE BANK BENDS —
    # at Wolf Point and again in the wedge where Lake Street runs out at the
    # South Branch. Where it bends away from the deck, the far end of a face
    # standing 6 m off the tangent lands BEHIND the bank, on dry ground: PR #258
    # measured exactly that at Hogan's store, whose face runs from 1.10 m of
    # water at one end to −0.34 m at the other, and refused it rather than invent
    # a bespoke outline for one frontage. That refusal is the rule now. A deck
    # whose face is not in water is not a landing; the alternative — a bespoke
    # outline per bend — would make every wharf's shape a judgement instead of a
    # derivation, and the standard form is the whole reason this layer can claim
    # its dimensions are invented ONCE (L132) rather than once per site.
    least = min(run)
    if least <= 0.0:
        off = min(range(len(run)), key=lambda i: run[i])
        where = -half + 2.0 * half * off / (len(run) - 1)
        return "refused", {"structure_id": sid, "why": (
            f"its deck's face would stand on dry ground: the bed rises to "
            f"{-least:.2f} m ABOVE the water plane {abs(where):.1f} m from the "
            "face's centre, because the bank bends away from the standard "
            "rectangular outline here. The dock statement stands; a landing is "
            "drawn when a deck of the standard form is afloat along its whole "
            "face, and this project will not invent a bespoke outline for one "
            "frontage.")}                                          # clause 6

    # CLAUSE 5b (T-0106): AFLOAT IS NOT THE SAME AS WORKING. Clause 6 asks
    # whether the face is in water at all; this asks whether there is enough of
    # it to lie at. `tools/smoke_renderer.mjs` has required more than 0.50 m at
    # every drawn face since T-0041 and the generator never read the number
    # back — until T-0106 the two could not disagree, because the only bank this
    # layer could see was the forks window, where the channel gives 1.5-1.7 m
    # six metres out. THE DRAWBRIDGE REACH IS SHALLOWER: the committed terrain
    # gives 0.76-0.88 m six metres off the south bank between E +560 and E +700,
    # and where the traced bank also carries a step across a frontage, one corner
    # of a straight deck ends up nearer the bank than its foot is and shallower
    # still. Harmon & Loomis's face reads 0.48 m and is refused here.
    #
    # THIS CLAUSE AND CLAUSE 6 OVERLAP, AND THIS IS THE STRICTER OF THE TWO —
    # 0.50 m against 0.0 m, on the same 1 m stations. Both are kept, in this
    # order, because they diagnose different things and clause 6 names the worse
    # one: a face on DRY GROUND is a bent outline and says so, while a face
    # afloat in too little water is a frontage the river does not serve. Merging
    # them into one clause would either lose clause 6's reading or slacken this
    # one to 0.0 m, and neither is a trade this layer should make.
    if least < MIN_DEPTH_M:
        off = min(range(len(run)), key=lambda i: run[i])
        where = -half + 2.0 * half * off / (len(run) - 1)
        return "refused", {"structure_id": sid, "why": (
            f"the modelled channel gives only {least:.2f} m of water under its "
            f"face {abs(where):.1f} m from the centre, under the "
            f"{MIN_DEPTH_M:.2f} m this layer requires of a working landing. Its "
            "frontage IS reached by the traced bank; what refuses it is a "
            "sounding and not a gap in the trace. The dock statement stands and "
            "the landing is not drawn.")}                          # clause 5b

    return "wharf", {
        "structure_id": sid,
        "name": sc.get("name"),
        "dock_confidence": grade,
        "dock_sources": dock.get("sources") or [],
        "confidence": "reconstructed",
        "bank": bank["name"],
        "bank_confidence": bank["confidence"],
        "bank_sources": bank["sources"],
        # WHICH TRACING WINDOW this particular deck stands on (T-0106). The bank
        # is two windows of one sheet joined at a seam they agree on to under a
        # metre, and a reader should not have to work out from an easting which
        # of the two carried any given landing. `.get` because `selftest()`
        # builds a bank by hand, and a constructed stand has no window.
        "bank_traced_in": _traced_in(bank, foot_s),
        "bank_foot_local_enu_m": [_round(foot[0]), _round(foot[1])],
        "bank_tangent": [_round(tangent[0], 4), _round(tangent[1], 4)],
        "waterward_normal": [_round(nx, 4), _round(ny, 4)],
        "deck_quad_local_enu_m": [[_round(c[0]), _round(c[1])] for c in corners],
        "deck_length_m": _round(2 * half),
        "deck_width_m": _round(FACE_OUT_M + HEEL_IN_M),
        "frontage_served_m": _round(frontage),
        "wall_to_bank_m": _round(dist),
        "clearance_to_wall_m": _round(clearance),
        "depth_at_face_m": [_round(d) for d in depths],
        # The shallowest of the 1 m stations, which is the figure clause 6 is
        # decided on. Reported so the margin a drawn landing passes by is on the
        # record rather than in the generator's head — the same reason
        # depth_at_face_m is reported rather than assumed.
        "least_depth_at_face_m": _round(min(run)),
        "face_stations": len(run),
        "facade_bearing_deg": _round(place.get("rotation_deg") or 0.0, 1),
    }


def build_record() -> tuple[list, list, list]:
    index = _load(SIDECARS / "index.json")
    banks = bank_lines()
    field = Heightfield.load(EPOCH)
    wharves: list[dict] = []
    refused: list[dict] = []

    for entry in index.get("structures", []):
        sid = entry.get("id")
        path = SIDECARS / f"{sid}.json"
        if not sid or not path.exists():
            continue
        kind, row = derive_one(sid, _load(path), banks, field)
        if kind == "wharf":
            wharves.append(row)
        elif kind == "refused":
            refused.append(row)

    wharves.sort(key=lambda w: w["structure_id"])
    refused.sort(key=lambda r: r["structure_id"])
    return wharves, refused, banks


def record(wharves: list, refused: list, banks: list) -> dict:
    return {
        "_doc": (
            "The town's river wharves and landings — a plank deck on timber "
            "cribs at each frontage whose own record states a dock: the two "
            "forwarding warehouses whose dock the dossier states (T-0041), "
            "the five South Water merchant landings reconstructed under the "
            "owner's ruling of 2026-08-18 (T-0062), and Robert A. Kinzie's "
            "storehouse on the WEST bank at Wolf Point, the first landing this "
            "layer has put on that shore (T-0107). NOT structure "
            "records and NOT geometry that comes out of Blender: a deck on cribs "
            "is a box on boxes standing on ground and water this project already "
            "draws, so it is derived from the committed footprint, the traced "
            "bank and the committed heightfield and drawn at load by "
            "renderers/web/js/wharves.js — the same argument that lets the "
            "enclosure layer draw a fence from a perimeter and the yard layer "
            "stand a barrel on the footway. Generated by "
            "tools/generate_river_wharves.py and re-derived byte for byte by "
            "tools/check.sh, because 'which frontage gets a wharf' is a rule and "
            "a rule has to be auditable."
        ),
        "id": "river_landings",
        "name": "The river wharves and the South Water landings",
        "kind": "wharves",
        "scene": "1835",
        "target_date": "1835-07-01",
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin, the same "
            "frame data/enclosures/, data/signage/, data/yard/ and the sidecars' "
            "placement.local_e / local_n use. The water surface is Z = 0 by "
            "construction (data/datum.json § vertical)."
        ),
        "counts": {"wharves": len(wharves), "refused": len(refused)},
        "bank_runs": {
            "note": (
                "THE BANK THIS LAYER STANDS ITS DECKS ON, AND WHERE EVERY METRE "
                "OF IT WAS TRACED. It is not one polyline but two tracing windows "
                "of one sheet — the Wright 1834 survey — joined at a seam the two "
                "windows agree on to under a metre. tools/trace_river.py works a "
                "1120 px window centred on the forks, so the bank polylines in "
                "river.geojson stop at local E +390: that is where the WINDOW "
                "closed, not where the bank did. tools/trace_shoreline.py picks "
                "the same waterline up off the same sheet at E +314 and carries "
                "it east past the Dearborn drawbridge (E +699) to the lake. "
                "NOTHING IS EXTENDED BY EYE AND NOTHING NEW IS TRACED HERE: the "
                "composition is the one terrain_spec.json already declares in "
                "shore_runs and generators/terrain_gen.py already measures a "
                "division's waterline with. Until T-0106 this layer read only the "
                "first window, believed the south bank ended 309 m short of the "
                "drawbridge, and refused three stated landings for standing "
                "beyond a trace that was there all along. The forks run is taken "
                "WHOLE — no committed vertex dropped, moved or resampled — and "
                "only the harbour-reach vertices beyond its terminal foot are "
                "appended, so the overlap is corroboration and never geometry."
            ),
            "runs": [{
                "division": b["id"],
                "confidence": b["confidence"],
                "sources": b["sources"],
                "traced_windows": b["members"],
                "seam": b["seam"],
                "vertices": len(b["points"]),
                "length_m": _round(_run_length(b["points"]), 1),
                "local_e_range_m": [_round(min(p[0] for p in b["points"]), 1),
                                    _round(max(p[0] for p in b["points"]), 1)],
            } for b in banks],
        },
        "existence": {
            "value": True,
            "confidence": "reconstructed",
            "sources": ["andreas_1884_v1"],
            "note": (
                "THE FACT OF A WHARF AT THESE TWO FRONTAGES IS THE BEST-ATTESTED "
                "THING ON THIS LAYER AND EVERY DIMENSION OF IT IS INVENTED. What "
                "is held: docs/research/03-structures-north.md §3.10 — 'Kinzie & "
                "Hunter and Dole & Newberry each had a warehouse WITH ITS DOCK "
                "ALONG THE RIVER FRONT' — which is the clause that attests the "
                "Kinzie & Hunter building at all; and Andreas independently names "
                "'Newberry & Dole's wharf' as the place the schooner Illinois, "
                "the first vessel through the new cut, was cheered on 12 July "
                "1834 (scan p. 503). What is NOT held, anywhere in this project: "
                "the length, the width, the height, the construction or the "
                "condition of either dock. Both records carried "
                "geometry: 'absent' over that statement until this layer existed "
                "— the strongest confidence chip in the dataset, over a bare bank "
                "— which docs/LIBERTIES.md L66 recorded as owed and L132 now "
                "claims. NOTHING HERE IS PROMOTED ABOVE reconstructed on the "
                "strength of the sentence: a dock is stated, and this is what a "
                "dock is drawn as. THE FIVE SOUTH WATER LANDINGS (T-0062) STAND "
                "ONE TIER LOWER STILL: no source states a dock at any of them, "
                "and their existence is itself reconstructed under the owner's "
                "ruling of 2026-08-18 ('you can add more docks!'), bounded per "
                "frontage in each record's own dock note — the trade that takes "
                "goods off the water, the working reach the 2026-08-18 brief "
                "shows crowded with masts, and the wharfing-out practice of the "
                "south bank. Claimed at docs/LIBERTIES.md L145. THE WEST BANK'S "
                "ONE LANDING (T-0107) STANDS ON THE SAME FOOTING AND IS BOUNDED "
                "BY ITS OWN RECORD'S TRADE: Robert A. Kinzie's storehouse at "
                "Wolf Point dealt in 'groceries and Indian goods' (chicagology) "
                "and its keeper is Andreas's 'Indian Traders — Robert A. "
                "Kinzie, near Wentworth's tavern' (scan p. 235); the record's "
                "committed position note had already reasoned that 'a "
                "storehouse trading goods off canoes has a positive reason to "
                "face the landing', which is why its facade was set due east "
                "onto the water before any wharf layer existed. NO SOURCE "
                "STATES A DOCK, WHARF OR LANDING ANYWHERE AT WOLF POINT. Each "
                "wharf row "
                "below reports its own dock_confidence, which is the honest "
                "division between the stated docks and the invented ones."
            ),
        },
        "rule": {
            "note": (
                "A sidecar standing on the scene date whose own `dock` attribute "
                "is true. T-0041 shipped the rule with a grade clause — attested "
                "or inferred only — and it selected exactly two records; the "
                "owner overruled the rationing on 2026-08-18 ('you can add more "
                "docks!'), so five South Water merchant records now state a "
                "reconstructed landing, each bounded in its own note, and the "
                "rule draws them too. The selection still lives in the data: a "
                "record with no dock statement — the Temple Building's meeting "
                "house on the same frontage, the lumber landing, the ferry — "
                "still gets no wharf. SINCE T-0107 THE TEST RUNS ON EVERY RIVER "
                "FRONTAGE IN THE TOWN, WHICHEVER BANK IT STANDS ON. T-0062 "
                "stated its docks on South Water merchants, so the other two "
                "shores were never asked: the North Division shore carried a "
                "wharf only because Kinzie & Hunter's dock is attested, and the "
                "WEST bank at Wolf Point carried none at all — which was a fact "
                "about which records had been edited, not a finding about Wolf "
                "Point. On the west bank the trade test selects exactly one "
                "record, Robert A. Kinzie's storehouse; the row's other four — "
                "Wentworth's tavern, James Kinzie's residence, the Robinson and "
                "Caldwell cabins and Father Walker's log meeting house — state "
                "no dock and get none, because lodging, dwelling and worship "
                "take nothing off a canoe. Read the clauses and their reasons in "
                "tools/generate_river_wharves.py."
            ),
            "dock_grades": list(DOCK_GRADES),
            "afloat_clause": (
                "CLAUSE 6, ADDED BY T-0107: the deck's face must stand in water "
                "along its whole run, sampled at about 1 m on the committed "
                "heightfield, and a face that would stand on dry ground is "
                "refused with the measured rise on the record. The deck outline "
                "is a rectangle set on the bank's own tangent — one standard "
                "form, so its dimensions are invented once (L132) rather than "
                "once per site — and THE BANK BENDS, at Wolf Point and again in "
                "the wedge where Lake Street runs out at the South Branch, so a "
                "rectangle run against the curve can put the far end of its face "
                "behind the bank. PR #258 measured that at Hogan's store (1.10 m "
                "of water at one end of the face, −0.34 m at the other) and "
                "refused it rather than invent a bespoke outline for one "
                "frontage; this clause is that refusal made a rule. It refuses "
                "nothing in the town as it stands — every drawn face is afloat "
                "by more than a metre, the least of them 1.06 m at Robert "
                "Kinzie's — so it is proved on constructed frontages instead: "
                "`python3 tools/generate_river_wharves.py --selftest`, which "
                "`--check` runs, and which tools/check.sh already invokes."
            ),
        },
        "form": {
            "face_out_m": {
                "value": FACE_OUT_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. The deck's face stands 6.0 m beyond the traced 1834 "
                    "bank line. No source gives the reach of any of these docks. "
                    "What bounds it is the bed this project has already modelled: "
                    f"at 6 m out the channel gives {_depth_span(wharves)}, so a lighter or a "
                    "scow lies at the face and a loaded lake schooner does not — "
                    "the restrained reading, chosen because a longer deck would be "
                    "a claim about the river trade's tonnage as well as about the "
                    "dock. THE DEPTH IS REPORTED RATHER THAN ASSUMED so that what "
                    "the invented reach implies is on the record and not in "
                    "somebody's head, and the span is recomputed from the "
                    "committed heightfield every time this record is derived "
                    "so it cannot go stale behind a new landing."
                ),
            },
            "heel_in_m": {
                "value": HEEL_IN_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. The deck's landward edge ties 2.0 m back into the "
                    "bank, so the platform meets ground rather than ending on the "
                    "waterline. Nothing attests it; it is the least that reads as "
                    "a wharf built off a bank instead of a raft moored against one."
                ),
            },
            "apron_m": {
                "value": APRON_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. The deck runs 3.0 m past the building's river wall "
                    "at each end, so its length is the frontage it serves plus "
                    "6.0 m. No source gives a length. The bound is the building: a "
                    "dock belonging to one warehouse is about as long as the "
                    "warehouse, with enough deck past the doors to work a cargo "
                    "round it."
                ),
            },
            "deck_thickness_m": {
                "value": DECK_T_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A 0.14 m plank deck — the same course this project "
                    "already uses for sawn boards (CLAPBOARD_COURSE_M in three "
                    "archetypes, docs/RESEARCH/materials.md). No plank in any "
                    "Chicago dock is described anywhere this project has reached."
                ),
            },
            "freeboard_m": {
                "value": FREEBOARD_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED, AND IT IS A FLOOR RATHER THAN A HEIGHT. The deck "
                    "top is the GROUND'S OWN height along the landward edge, "
                    "sampled from the terrain by the renderer — the bridge deck's "
                    "lesson (T-0001), where a height authored beside the mesh "
                    "instead of taken from it put a walker 1.8 m over the planks. "
                    "Where the bank is lower than 0.90 m above the water plane, "
                    "which it is at both of these sites, the deck holds 0.90 m "
                    "instead: a working deck stands clear of its own river, and "
                    "this project's water surface is a summer-1835 mean with no "
                    "stage record behind it (data/datum.json § vertical). Nothing "
                    "attests the figure."
                ),
            },
            "crib_width_m": {
                "value": CRIB_W_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. The deck stands on a timber crib 1.20 m thick under "
                    "its outer face and its two ends, stepped down to the bed the "
                    "heightfield gives at each bent. Crib construction is what "
                    "this project already models on the harbour works "
                    "(generators/archetypes/pier_crib.py, docs/RESEARCH/"
                    "north_pier.md), so the town has one way of standing timber in "
                    "water rather than two; no source says either river dock was "
                    "built that way. NO STONE FILL IS DRAWN: a crib is a box of "
                    "timber filled with rubble and the fill is not visible from "
                    "outside it, so drawing it would spend triangles on a claim "
                    "nobody can see."
                ),
            },
            "post_side_m": {
                "value": POST_SIDE_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. Three snubbing posts stand along each face, 0.22 m "
                    "square. Nothing attests a post, its spacing or its size. A "
                    "vessel makes fast to something, and a deck with nothing to "
                    "make fast to reads as a platform rather than as a dock."
                ),
            },
            "post_height_m": {
                "value": POST_HEIGHT_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 0.75 m proud of the deck, which is a working height "
                    "for a line rather than a measurement of anything."
                ),
            },
            "boarding_stair_width_m": {
                "value": STAIR_WIDTH_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED (T-0058, docs/LIBERTIES.md). The deck top is a FLOOR "
                    "and the freeboard figure above is a floor over the water, so "
                    "at every one of these sites the planks stand proud of the "
                    "bank they tie into \u2014 measured from the committed "
                    "heightfield at load, between 0.3 and 0.8 m of it. Something "
                    "got a man from the ground onto the deck and no source says "
                    "what. A stair of plank treads is the least of the "
                    "possibilities: it invents timber this layer already draws "
                    "rather than regrading the bank, which would be a claim about "
                    "the LAND. 2.4 m across is a two-man width with a barrel "
                    "between them; nothing attests it."
                ),
            },
            "boarding_stair_tread_m": {
                "value": STAIR_TREAD_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 0.75 m of tread, landward, per step. Nothing "
                    "attests it; it is a comfortable going for the rise below and "
                    "keeps the whole stair inside the 2.0 m the deck already ties "
                    "back into the bank plus a metre of approach."
                ),
            },
            "boarding_stair_rise_m": {
                "value": STAIR_RISE_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED, AND IT IS A CEILING RATHER THAN A HEIGHT. The stair "
                    "divides whatever rise the terrain leaves between the bank and "
                    "the deck into equal treads, as many as it takes for none to "
                    "exceed this. 0.30 m is under the walker's own 0.35 m step-up "
                    "rule (renderers/web/js/walker.js WALK.stepUp) with margin, "
                    "which is what makes the deck boardable rather than a platform "
                    "you can see and not reach; it is also an ordinary stair rise. "
                    "How many treads that comes to is the terrain's answer at each "
                    "site, taken at load, never authored here."
                ),
            },
        },
        "geometry_note": (
            "The record owns the OUTLINE — where the deck stands, how long and "
            "how wide it is, and the figures above. How that outline becomes "
            "triangles is the renderer's: how many bents the crib is stepped "
            "into, where the three posts stand along the face, and the timber's "
            "tone are in renderers/web/js/wharves.js, the same division "
            "data/yard/ makes with yard.js. THE DECK'S HEIGHT IS NEITHER'S: it "
            "is the terrain's, sampled at the landward edge at load \u2014 and so "
            "is the HEIGHT OF THE BOARDING STAIR and the number of treads it "
            "takes, which is why this record states the stair's width, going and "
            "greatest rise and states no stair height anywhere."
        ),
        "not_drawn": (
            "NO VESSEL, NO CARGO, NO CRANE, NO GANGWAY AND NO NAME. The schooner "
            "Illinois was cheered at one of these two wharves in July 1834 and is "
            "not drawn at either: this project holds no description of any vessel "
            "in Chicago at the scene date, and a hull is a larger invention than "
            "the deck it would lie at. Goods are drawn only where the yard layer's "
            "own rule puts them (data/yard/), which is on the town's trading "
            "frontages and not out here. THE BOARDING STAIR IS NOT A GANGWAY: "
            "the gangway refused here is the plank to a hull, and the stair "
            "stated in `form` is the landward one, off the bank onto the deck."
        ),
        "wharves": wharves,
        "refused": refused,
        "research_note": (
            "WHAT WOULD MOVE ANY OF THIS OFF RECONSTRUCTION: the Chicago Democrat's "
            "advertising columns, where a forwarding house states its street and "
            "sometimes its wharf; the harbour engineers' reports of 1833-1836, "
            "which measure the river's depth and might carry a private wharf line; "
            "a marine list giving the Illinois's draught, which would say whether "
            "she could have lain at a face in 1.2 m of water or was warped in to a "
            "deeper one; or the c. 1835 view that docs/research/03-structures-"
            "north.md describes and this project has never been able to cite. Any "
            "of them would also bear on L66's open question, which is which BANK "
            "each of these two warehouses stood on."
        ),
    }


# --- proving the clauses fire ---------------------------------------------- #
#
# CLAUSE 6 REFUSES NOTHING IN THE TOWN AS IT STANDS. Every drawn face is afloat
# by more than a metre, so on the committed data the new clause is indistinguishable
# from no clause at all — and a refusal nobody has ever seen work is a refusal this
# project has only been told about. So the clause table is fired here on frontages
# built for it: a straight bank, a flat bed, and one thing wrong at a time. It runs
# inside `--check`, which `tools/check.sh` already invokes, so it costs no new gate
# and cannot rot unnoticed.


class _StubBed:
    """A constructed bed: flat water, optionally dry or unmodelled past a line."""

    def __init__(self, depth=1.2, dry_from_n=None, dry_to_n=None, rise=0.35,
                 uncovered_from_n=None):
        self.depth, self.rise = depth, rise
        self.dry_from_n, self.dry_to_n = dry_from_n, dry_to_n
        self.uncovered_from_n = uncovered_from_n

    def covers(self, e, n):
        return self.uncovered_from_n is None or n < self.uncovered_from_n

    def height(self, e, n):
        if self.dry_from_n is not None and n >= self.dry_from_n and (
                self.dry_to_n is None or n <= self.dry_to_n):
            return self.rise                 # ground standing above the water plane
        return -self.depth


_TEST_BANK = [{
    "name": "self-test bank", "confidence": "reconstructed", "sources": [],
    "points": [(0.0, -100.0), (0.0, 100.0)],
}]

# A bank that is TRACED and real but runs nowhere near the frontage — every
# metre of it lies past the end of the wall's own line. Clause 3b is what tells
# it apart from the bank in front of the wall; without that clause the nearest
# point on this line is still "the nearest bank" and a deck gets built off it.
_TEST_BANK_ASIDE = [{
    "name": "self-test bank, off to one side", "confidence": "reconstructed",
    "sources": [], "points": [(0.0, 60.0), (0.0, 160.0)],
}]


def _stand(local_n=0.0, frontage=7.0, grade="reconstructed", dock=True):
    """A frontage whose river wall stands 12 m west of the self-test bank."""
    sc = {"name": "self-test frontage", "attributes": {},
          "placement": {"local_e": -18.0, "local_n": local_n, "rotation_deg": 90.0},
          "footprint": {"polygon": [[0, 0], [frontage, 0], [frontage, 6], [0, 6]]}}
    if dock:
        sc["attributes"]["dock"] = {"value": True, "confidence": grade, "sources": []}
    return sc


def selftest() -> int:
    cases = [
        # (label, sidecar, bed, expected kind, a phrase the reason must carry,
        #  and the bank to run it against)
        ("a frontage in open water is drawn",
         _stand(), _StubBed(), "wharf", None, _TEST_BANK),
        ("CLAUSE 6: a face that runs onto dry ground at its end is refused",
         _stand(), _StubBed(dry_from_n=2.0), "refused", "dry ground", _TEST_BANK),
        ("CLAUSE 6: and a dry patch BETWEEN the reported three is refused too",
         _stand(), _StubBed(dry_from_n=0.5, dry_to_n=1.5), "refused", "dry ground", _TEST_BANK),
        ("CLAUSE 5: a face off the modelled ground is refused",
         _stand(), _StubBed(uncovered_from_n=2.0), "refused", "modelled ground", _TEST_BANK),
        ("CLAUSE 4b: a deck running past the trace's end is refused",
         _stand(local_n=99.0), _StubBed(), "refused", "traced 1834 bank", _TEST_BANK),
        ("CLAUSE 2: a dock graded outside the confidence model is refused",
         _stand(grade="probably"), _StubBed(), "refused", "not a grade", _TEST_BANK),
        ("CLAUSE 1: a record that states no dock is not a candidate",
         _stand(dock=False), _StubBed(), None, None, _TEST_BANK),
        # T-0106's two. Neither refuses anything in the town as it stands —
        # clause 3b MOVES a foot rather than refusing one, and clause 5b refuses
        # exactly one frontage — so both are fired here for the same reason
        # T-0107 gave: a refusal nobody has watched work is one taken on trust.
        ("CLAUSE 3b: a bank that runs nowhere near the wall is not its frontage",
         _stand(), _StubBed(), "refused", "in front of", _TEST_BANK_ASIDE),
        ("CLAUSE 5b: a face afloat but under the working depth is refused",
         _stand(), _StubBed(depth=0.30), "refused", "working landing", _TEST_BANK),
    ]
    bad = 0
    for label, sc, bed, want, phrase, bank in cases:
        kind, row = derive_one("selftest_frontage", sc, bank, bed)
        ok = kind == want and (phrase is None or phrase in (row or {}).get("why", ""))
        detail = (row or {}).get("why", "") if kind == "refused" else (
            f"least {row['least_depth_at_face_m']} m over {row['face_stations']} "
            f"station(s)" if kind == "wharf" else "not a candidate")
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}\n          {detail[:150]}")
        if not ok:
            bad += 1
    # The density itself is the claim in case 3: with the three points the record
    # reports — the face's ends and its middle — that bed reads as open water.
    bed = _StubBed(dry_from_n=0.5, dry_to_n=1.5)
    three_look_wet = all(bed.height(6.0, n) < 0 for n in (-10.0, -3.5, 3.0))
    print(f"  {'ok  ' if three_look_wet else 'FAIL'}  and the three reported points "
          f"read that bed as open water, which is why the run is sampled at 1 m")
    if not three_look_wet:
        bad += 1
    print("WHARF CLAUSES PASS" if not bad else f"WHARF CLAUSES FAIL — {bad} case(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    ap.add_argument("--selftest", action="store_true",
                    help="fire the refusal clauses on constructed frontages")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    wharves, refused, banks = build_record()
    text = json.dumps(record(wharves, refused, banks), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists():
            print(f"WHARF DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"WHARF DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from the rule "
                  f"in tools/generate_river_wharves.py")
            return 1
        print(f"verified {len(wharves)} river wharf/wharves "
              f"({len(refused)} frontage(s) refused with a reason)")
        return selftest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(wharves)} river wharf/wharves "
          f"({len(refused)} refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
