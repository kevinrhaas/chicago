#!/usr/bin/env python3
"""Is there ground on the south bank at the Dearborn reach a building could stand on?

T-0134. The plate the town was built from here — image 3 of the owner's brief of
2026-08-18 — draws low warehouses on BOTH banks of the reach below the drawbridge.
T-0133 built the north side, four freight sheds standing back from North Water Street,
and left the south side empty with a sentence in every one of their records: the
platted South Water Street corridor reaches to within about 1.7 m of the traced 1834
waterline, so there is no ground there that is not the street.

That sentence was one spot reading taken by hand at one station, and the whole south
bank of the reach was refused on it. This is the reading as a command, over the whole
reach and at every tolerance the refusal could turn on, so the refusal reproduces —
and so it FAILS the day the ground changes and the question is genuinely open again.

**What it asks.** Over the south bank from the Dearborn crossing east to the United
States Reservation's west line, can the smallest footprint family F1 allows — 18 x 32 ft,
the freight shed of the plate — be put down at all, on ground that is

* above the water surface in the committed heightfield (`WATER_SURFACE_M`, the same
  zero `measure_no_build_ground.py` uses),
* outside every platted street corridor (`plat_corridors`, the module the placement
  gate itself asks), and
* off the refused ground of the Reservation and the sand bar
  (`measure_no_build_ground`, so the two answers cannot disagree), and
* out of the travelled way of a committed street `plat_corridors` cannot see, because
  that module carries the PLATTED grid and the road to the fort was never platted.
  Added 2026-09-26 by T-1636, when the filled slough mouth opened 91 flat positions on
  this reach and every one of them stood in the fort road. A reading that reports the
  town's only way to the fort as free ground is not a reading, and the number it produced
  would have been spent building in the road.
* and clear of WHAT ALREADY STANDS. Added 2026-09-27 by T-1642, which is the same class
  of correction one day later: the road's move released the 81 positions it had masked,
  and 76 of the 91 that then read free were the ground `south_bank_shed_dearborn_e1`
  stands on, because this reading had never known that a building was there. That is not
  a bound being tightened — every bound below is still the permissive one — it is the
  committed tree's own occupancy. Ground a building occupies is not ground another
  building can stand on, and a count that reports one shed's footprint 76 ways is a count
  that would be spent building the shed again. It is reported apart, so the reading with
  the buildings switched off is still legible.
* and off the boards of a committed frontage WALK, for exactly the same reason and one
  the reading learned the hard way. Added 2026-09-27 by T-1643: the position this
  reading admitted for `south_bank_shed_dearborn_e1` stood across the full 1.83 m width
  of the riverside plank walk's east end, and nothing in the dataset could say so — a
  walk is boards laid on committed ground and a building is a mesh seated on the same
  ground, and no gate compared them. The published walker smoke found it, by being
  pushed out of the shed's collision footprint instead of walking west along the bank.
  The walk mask is applied BEFORE T-1642's occupancy mask, so a position under boards is
  counted against the boards and not against the shed that also stands there.

**AND HOW MANY MORE IT TAKES, WHICH IS THE QUESTION A COUNT OF POSITIONS CANNOT ANSWER.**
T-1642 again. 15 free positions on a 1 m lattice are not 15 buildings; they are 15 ways of
putting down the same one. `takes_more` is the largest set of the free positions that do
not overlap EACH OTHER — an exact maximum, not a greedy pack — so the reading says how
many more sheds this ground holds rather than how many ways one of them could be nudged.

**Every bound is the permissive one, on purpose.** A refusal is only worth having if it
survives the most generous reading of its own inputs: the rectangle may stand at ANY
bearing rather than square to the street, it is the SMALLEST the family allows rather
than the median, dry means one millimetre above the water rather than a freeboard, and
the relief clause is reported at the generators' own 0.30 m, at the 0.35 m the north
bank sheds quoted, at a metre, and with no relief clause at all. If the answer is still
zero with the clause switched off, the finding does not rest on the clause.

**A corridor is not the travelled way** — L79, and `plat_corridors` says so at length.
This tool does not decide whether a building may stand inside the legal corridor; that
question is the ticket's, and the ticket's answer is written up in
`docs/RESEARCH/south_bank_dearborn_ground.md`. What this measures is the narrower and
purely physical half: whether the question can be side-stepped by finding ground
outside the corridor. It cannot.

    tools/measure_south_bank_ground.py            the table
    tools/measure_south_bank_ground.py --gate     the ratchet check.sh runs
    tools/measure_south_bank_ground.py --self-test   the assertions still fire
    tools/measure_south_bank_ground.py --json     the readings, machine-readable
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from heightfield import Heightfield  # noqa: E402
from measure_no_build_ground import (  # noqa: E402
    EPOCH, WATER_SURFACE_M, bar_ring, inside, reservation_ring,
)
from plat_corridors import corridors, intrusion  # noqa: E402

# WHICH LINE THIS READER'S ANSWER STANDS ON (T-0419, the owner's ruling of
# 2026-09-21). See `plat_corridors.LINES` for the three words and
# `tools/check_corridor_line.py` for the check that every reader declares.
CORRIDOR_LINE = "drawn"
CORRIDOR_LINE_WHY = "it asks whether a building could stand somewhere, and a building stands on the block grid"

BASELINE = ROOT / "tools" / "south_bank_ground_baseline.json"
DATA = ROOT / "data"

# THE REACH. Its west end is the Dearborn Street drawbridge — the crossing the plate is
# drawn from and the thing that makes this reach the one the plate shows. Its east end is
# the Reservation's west line, because east of that the ground was never open to a private
# builder and `measure_no_build_ground.py` already refuses it. Both are RESOLVED from
# committed records below rather than typed here, for the reason `data/datum.json` is
# re-derived rather than stored: a typed vertex cannot be wrong loudly.
BRIDGE = "dearborn_street_drawbridge"
# The north edge of the box. The south bank's ground and the river are both under it; the
# NORTH bank is not, and that is the whole job of this number — the north shore of the main
# stem at this reach stands past local N 90, so a rectangle cannot wander across the water
# and report itself as south-bank ground. It is not a claim about where the bank is.
BOX_N_M = 45.0
BOX_S_M = 0.0

# The smallest footprint family F1 — freight or storage shed — is allowed, from the
# reconstruction spec's own band, in feet. The smallest, because a refusal has to refuse
# the easiest case.
INVENTORY = DATA / "reconstruction" / "1835_building_inventory.json"
FAMILY = "F1"
FT_M = 0.3048

# The sweep. A half-metre mask and a metre of position step is finer than the 2.5 m
# heightfield cell the ground itself is committed at, so the grid is not what decides this.
MASK_M = 0.5
STEP_M = 1.0
BEARING_STEP_DEG = 15

# The relief clauses this is reported at. 0.30 is `generate_block_infill.MAX_RELIEF_M`,
# the walker's step tolerance three infill generators hold themselves to; 0.35 is the
# figure the north bank sheds' own notes quote; 1.00 and None are there so the finding
# can be seen not to rest on either.
RELIEF_TOLERANCES = [0.30, 0.35, 1.00, None]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def reach() -> tuple[float, float]:
    """(west, east) of the reach in local ENU metres, resolved from committed records."""
    datum = load(DATA / "datum.json")
    bridge = load(DATA / "structures" / f"{BRIDGE}.json")
    placed = [p for p in bridge["phases"] if (p.get("position") or {}).get("utm_e")]
    if not placed:
        raise SystemExit(f"{BRIDGE} carries no placed phase; the reach has no west end")
    west = float(placed[0]["position"]["utm_e"]) - float(datum["origin_utm_e"])
    ring, _, _ = reservation_ring()
    # The Reservation's west line is its westernmost edge; where that line meets this
    # bank is the east end of the reach.
    east = min(e for e, n in ring if BOX_S_M <= n <= BOX_N_M)
    if not (west < east):
        raise SystemExit(f"the reach reads backwards: {west:.1f} to {east:.1f}")
    return west, east


def platted_end() -> float:
    """The east end of South Water Street's committed platted line, in local ENU.

    The reach runs past it. West of this the question is "is there ground outside the
    street"; east of it there IS no street, and ground there answers a different
    question — which is why the two are reported apart rather than averaged into one
    count that would read as ground the plate's warehouses could have used.
    """
    for street in load(DATA / "streets" / "1835.json")["streets"]:
        if street["id"] == "south_water":
            return float(street["path_local_enu_m"][-1][0])
    raise SystemExit("data/streets/1835.json no longer carries south_water")


def footprint_m() -> tuple[float, float]:
    """The smallest F1 footprint the reconstruction spec allows, in metres."""
    bands = load(INVENTORY)["family_bands_ft"]
    if FAMILY not in bands:
        raise SystemExit(f"the inventory carries no band for family {FAMILY}")
    # `[lo_w, lo_d, hi_w, hi_d]`, the order `generate_inferred_infill.dimensions` reads.
    w_lo, d_lo, _, _ = bands[FAMILY]
    return round(w_lo * FT_M, 4), round(d_lo * FT_M, 4)


# How far outside the reach a track segment is still worth carrying: a road that passes
# near the box can still put its travelled way inside it, and a segment whose ends are
# both well clear of the box cannot. 40 m is more than the widest committed track.
TRACK_MARGIN_M = 40.0


def unplatted_tracks(west: float, east: float) -> list[dict]:
    """The travelled ways of committed streets `plat_corridors` does not carry.

    T-1636. `plat_corridors.corridors()` is the PLATTED grid — 33 streets off James
    Thompson's plat and its additions — and it is the right module for the question
    "is this in a platted street". It is the wrong module for the question this reading
    actually asks, which is whether a building could stand somewhere, because a road
    that is not on the plat is still a road. On this reach that is `fort_road`: South
    Water Street stops at the United States Reservation, and the way from the town's
    east end to the fort gate runs across exactly the ground the filled slough mouth
    opened.

    The mask is the TRAVELLED WAY (`track_width_m`), not the reconstructed corridor,
    because every bound in this reading is the permissive one and the corridor of an
    unplatted road is an invention twice over. What the 12 m corridor would refuse is
    reported beside it rather than gated on.
    """
    lanes = corridors()
    lo_e, hi_e = west - TRACK_MARGIN_M, east + TRACK_MARGIN_M
    lo_n, hi_n = BOX_S_M - TRACK_MARGIN_M, BOX_N_M + TRACK_MARGIN_M
    out = []
    for street in load(DATA / "streets" / "1835.json")["streets"]:
        if street["id"] in lanes:
            continue
        path = [(float(e), float(n)) for e, n in street.get("path_local_enu_m") or []]
        segments = [(a, b) for a, b in zip(path, path[1:])
                    if min(a[0], b[0]) <= hi_e and max(a[0], b[0]) >= lo_e
                    and min(a[1], b[1]) <= hi_n and max(a[1], b[1]) >= lo_n]
        if not segments:
            continue
        track = street.get("track_width_m")
        if track is None:
            raise SystemExit(f"{street['id']} reaches this reach and carries no "
                             "track_width_m, so its travelled way cannot be masked")
        out.append({"id": street["id"], "track_width_m": float(track),
                    "corridor_width_m": street.get("corridor_width_m"),
                    "segments": segments})
    return out


def in_a_track(e: float, n: float, tracks: list[dict], half: str = "track") -> bool:
    """Is the point inside the masked half-width of any of these travelled ways?"""
    for road in tracks:
        key = "track_width_m" if half == "track" else "corridor_width_m"
        width = road.get(key) or road["track_width_m"]
        limit = (width / 2.0) ** 2
        for (e1, n1), (e2, n2) in road["segments"]:
            de, dn = e2 - e1, n2 - n1
            span = de * de + dn * dn
            t = 0.0 if span == 0 else ((e - e1) * de + (n - n1) * dn) / span
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            pe, pn = e1 + t * de, n1 + t * dn
            if (e - pe) ** 2 + (n - pn) ** 2 < limit:
                return True
    return False


# The frontage manifest, which is a manifest and not a glob: `data/frontage/index.json`
# says so itself — a static host cannot be globbed — so this reader reads exactly what
# the renderer reads.
FRONTAGE = DATA / "frontage"


def committed_walks(west: float, east: float) -> list[dict]:
    """The committed frontage walks whose boards reach this stretch of bank.

    T-1643. `plat_corridors` carries the platted grid; `unplatted_tracks` carries the
    roads that were never platted; `standing_footprints` carries what is built. NONE of
    them carries a plank walk, and a plank walk is a built surface a person stands on.
    So this reading admitted a station standing across the whole width of the riverside
    walk's east end, and `south_bank_shed_dearborn_e1` was seated on it — a building on
    the town's own riverside walk, found by the published walker smoke and not by any
    gate.

    The mask is the walk's OWN width, the same rectangle `renderers/web/js/frontage.js`
    publishes as that walk's keep-out. Unlike a road there is nothing else it could be:
    a corridor is a reservation around a travelled way and can be argued about, and
    boards are the surface itself.
    """
    lo_e, hi_e = west - TRACK_MARGIN_M, east + TRACK_MARGIN_M
    lo_n, hi_n = BOX_S_M - TRACK_MARGIN_M, BOX_N_M + TRACK_MARGIN_M
    out = []
    for entry in load(FRONTAGE / "index.json")["frontage"]:
        record = load(FRONTAGE / entry["file"])
        for walk in record.get("walks") or []:
            line = [(float(e), float(n))
                    for e, n in walk.get("centreline_local_enu_m") or []]
            segments = [(a, b) for a, b in zip(line, line[1:])
                        if min(a[0], b[0]) <= hi_e and max(a[0], b[0]) >= lo_e
                        and min(a[1], b[1]) <= hi_n and max(a[1], b[1]) >= lo_n]
            if not segments:
                continue
            width = walk.get("width_m")
            if width is None:
                raise SystemExit(f"{walk['id']} lays boards on this reach and carries "
                                 "no width_m, so they cannot be masked")
            out.append({"id": walk["id"], "belongs_to": walk.get("belongs_to"),
                        "width_m": float(width), "segments": segments})
    return out


def on_a_walk(e: float, n: float, walks: list[dict]) -> bool:
    """Is the point on the boards of any of these committed walks?"""
    for walk in walks:
        limit = (walk["width_m"] / 2.0) ** 2
        for (e1, n1), (e2, n2) in walk["segments"]:
            de, dn = e2 - e1, n2 - n1
            span = de * de + dn * dn
            t = 0.0 if span == 0 else ((e - e1) * de + (n - n1) * dn) / span
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            pe, pn = e1 + t * de, n1 + t * dn
            if (e - pe) ** 2 + (n - pn) ** 2 < limit:
                return True
    return False


def world_polygon(phase: dict, datum: dict) -> list[tuple[float, float]]:
    """A placed phase's committed footprint in local ENU metres.

    The same four lines every generator in this project carries (`generate_block_infill`,
    `generate_inferred_infill`, `plat_occupancy`), and it is written out here rather than
    imported because those modules are generators: importing one to ask a question about
    the tree would pull a writer into a reader.
    """
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg") or 0.0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def standing_footprints(west: float, east: float) -> list[dict]:
    """Every committed placed footprint that reaches this reach's box.

    T-1642. What stands on the ground is a fact about the ground, and until this was
    added the reading did not have it: `south_bank_shed_dearborn_e1` had stood on the
    released strip since the day before and 76 of the 91 positions the reading called
    free were its own footprint, re-counted at every lattice offset and bearing that
    would have put a second shed inside the first.

    No category filter. A bridge deck is not a building and a rectangle cannot stand on
    one either, so anything the tree places with a footprint masks the ground it covers.
    """
    datum = load(DATA / "datum.json")
    lo_e, hi_e = west - TRACK_MARGIN_M, east + TRACK_MARGIN_M
    lo_n, hi_n = BOX_S_M - TRACK_MARGIN_M, BOX_N_M + TRACK_MARGIN_M
    out = []
    for path in sorted((DATA / "structures").glob("*.json")):
        record = load(path)
        for phase in record.get("phases") or []:
            position = phase.get("position") or {}
            polygon = (phase.get("footprint") or {}).get("polygon") or []
            if position.get("utm_e") is None or len(polygon) < 3:
                continue
            ring = world_polygon(phase, datum)
            if (min(e for e, _ in ring) <= hi_e and max(e for e, _ in ring) >= lo_e
                    and min(n for _, n in ring) <= hi_n and max(n for _, n in ring) >= lo_n):
                out.append({"structure": record["id"], "phase": phase["id"], "ring": ring})
    return out


def _axes(ring: list[tuple[float, float]]):
    """The outward normals of a convex ring's edges, for the separating-axis test."""
    for i in range(len(ring)):
        (e1, n1), (e2, n2) = ring[i], ring[(i + 1) % len(ring)]
        de, dn = e2 - e1, n2 - n1
        span = math.hypot(de, dn)
        if span:
            yield (-dn / span, de / span)


def overlaps(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    """Do two convex rings share any area? Separating axis, exact for rectangles.

    Touching is not overlapping: two sheds wall to wall are two sheds. The comparison is
    `<=` on the projections for that reason.
    """
    for axis in list(_axes(a)) + list(_axes(b)):
        pa = [e * axis[0] + n * axis[1] for e, n in a]
        pb = [e * axis[0] + n * axis[1] for e, n in b]
        if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
            return False
    return True


def takes_more(placements: list[dict]) -> list[dict]:
    """The largest set of these positions that do not overlap each other.

    EXACT, not greedy, because the number is a finding and a greedy pack is only a floor:
    a maximum independent set over the overlap graph, by branch and bound on the position
    with the most conflicts. The candidate sets here are tens of rectangles inside a nine
    metre strip, so the graph is dense and the search closes at once.
    """
    if not placements:
        return []
    rings = [p["ring"] for p in placements]
    n = len(rings)
    conflicts = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if overlaps(rings[i], rings[j]):
                conflicts[i].add(j)
                conflicts[j].add(i)

    best: list[int] = []

    def search(candidates: set[int], chosen: list[int]) -> None:
        nonlocal best
        if len(chosen) + len(candidates) <= len(best):
            return
        if not candidates:
            if len(chosen) > len(best):
                best = list(chosen)
            return
        pivot = max(candidates, key=lambda i: len(conflicts[i] & candidates))
        # Either the pivot is in the set, or it is not.
        search(candidates - {pivot} - conflicts[pivot], chosen + [pivot])
        search(candidates - {pivot}, chosen)

    search(set(range(n)), [])
    return [placements[i] for i in sorted(best)]


class Ground:
    """Is a point buildable at all — dry, out of the roadway, and not refused ground.

    The unplatted travelled ways are NOT applied here, on purpose: `strip()` reports the
    physical free ground and that reading did not change when T-1636 taught this tool
    about the fort road. The road is applied to the FOOTPRINT, in `fits()`, which is
    where the question "could a building stand here" is actually asked.
    """

    def __init__(self) -> None:
        self.hf = Heightfield.load(EPOCH)
        if self.hf is None:
            raise SystemExit("the 1834 epoch carries no committed heightfield")
        self.lanes = corridors()
        ring, _, _ = reservation_ring()
        self.refused = [ring, bar_ring()]

    def height(self, e: float, n: float) -> float | None:
        return self.hf.height(e, n) if self.hf.covers(e, n) else None

    def free(self, e: float, n: float) -> bool:
        h = self.height(e, n)
        if h is None or h <= WATER_SURFACE_M:
            return False
        if intrusion([(e, n)], self.lanes)[0] is not None:
            return False
        return not any(inside((e, n), ring) for ring in self.refused)


def strip(ground: Ground, west: float, east: float) -> list[dict]:
    """Per station, the run of buildable ground on the river side of the corridor."""
    rows = []
    e = west
    while e <= east + 1e-9:
        run, best = [], []
        n = BOX_S_M
        while n <= BOX_N_M + 1e-9:
            if ground.free(e, n):
                run.append(n)
            else:
                if len(run) > len(best):
                    best = run
                run = []
            n += MASK_M
        if len(run) > len(best):
            best = run
        if best:
            heights = [ground.height(e, n) for n in best]
            rows.append({"e": round(e, 1), "n_from": round(best[0], 2),
                         "n_to": round(best[-1], 2),
                         "width_m": round(best[-1] - best[0] + MASK_M, 2),
                         "relief_m": round(max(heights) - min(heights), 2)})
        else:
            rows.append({"e": round(e, 1), "n_from": None, "n_to": None,
                         "width_m": 0.0, "relief_m": None})
        e += STEP_M
    return rows


def fits(ground: Ground, west: float, east: float, width: float, depth: float,
         tracks: list[dict] | None = None, standing: list[dict] | None = None,
         walks: list[dict] | None = None) -> list[dict]:
    """Every position and bearing at which the smallest F1 footprint would stand.

    The rectangle is sampled on a half-metre lattice INCLUDING its corners, because a
    footprint whose middle is dry and whose corner is in the river is not a building.

    Each accepted position is ANNOTATED with whether it stands in an unplatted travelled
    way (`in_track`), whether it stands in one of those roads' reconstructed corridors
    (`in_track_corridor`), whether it stands on the boards of a committed frontage walk
    (`on_walk`), and whether it stands on a footprint the tree already places
    (`on_what_stands`), rather than being dropped. The caller counts them apart, so the
    corrections T-1636, T-1642 and T-1643 made are legible in the reading instead of
    hidden inside a smaller number.
    """
    tracks = tracks or []
    standing = standing or []
    walks = walks or []
    out = []
    us = [i * MASK_M for i in range(int(width / MASK_M) + 1)]
    vs = [i * MASK_M for i in range(int(depth / MASK_M) + 1)]
    us = sorted(set(us + [width]))
    vs = sorted(set(vs + [depth]))
    # THE FULL TURN, AND NOT A HALF ONE (T-1640). A rectangle is its own shape at
    # `theta` and at `theta + 180`, and this swept 0-165 for that reason. The
    # rectangle is not anchored at its centre, though — it is anchored at its (0, 0)
    # corner — so turning it 180 degrees does not leave it where it was, it reflects
    # it through the station onto the opposite quadrant. Sweeping the half turn
    # therefore expresses only the placements that lie NORTH of their own station,
    # and the equivalent bearing-0 station for one lying south of the box floor
    # (`BOX_S_M`) is not on the lattice at all. What that cost is measured: on
    # 2026-09-27 the only position this reading would admit at the generators' own
    # 0.30 m clause stood 15 degrees off the riverside walk and 0.111 m from
    # `south_bank_shed_dearborn_e1`'s south wall, while a rectangle SQUARE to the
    # walk stands on the same ground at 0.089 m of relief with 2.00 m between the
    # two sheds — a placement the reading could not name. Every bound in this
    # reading is the permissive one and its own anchor was not.
    bearings = [math.radians(d) for d in range(0, 360, BEARING_STEP_DEG)]
    e0 = west
    while e0 <= east + 1e-9:
        n0 = BOX_S_M
        while n0 <= BOX_N_M + 1e-9:
            for theta in bearings:
                cos, sin = math.cos(theta), math.sin(theta)
                heights, ok = [], True
                for u in us:
                    for v in vs:
                        e = e0 + u * cos - v * sin
                        n = n0 + u * sin + v * cos
                        if not (west - width - depth <= e <= east + width + depth):
                            ok = False
                            break
                        if not ground.free(e, n):
                            ok = False
                            break
                        heights.append(ground.height(e, n))
                    if not ok:
                        break
                if ok:
                    lattice = [(e0 + u * cos - v * sin, n0 + u * sin + v * cos)
                               for u in us for v in vs]
                    # The rectangle's own corners, in order, so an overlap against what
                    # stands is an area test rather than a lattice test: a footprint
                    # whose corner clips a standing wall is on that building's ground.
                    ring = [(e0 + u * cos - v * sin, n0 + u * sin + v * cos)
                            for u, v in ((0.0, 0.0), (width, 0.0),
                                         (width, depth), (0.0, depth))]
                    on_what = [s for s in standing if overlaps(ring, s["ring"])]
                    out.append({"e": round(e0, 1), "n": round(n0, 1),
                                "bearing_deg": round(math.degrees(theta), 1),
                                "relief_m": round(max(heights) - min(heights), 3),
                                "ring": [(round(e, 3), round(n, 3)) for e, n in ring],
                                "in_track": any(in_a_track(e, n, tracks)
                                                for e, n in lattice),
                                "in_track_corridor": any(
                                    in_a_track(e, n, tracks, half="corridor")
                                    for e, n in lattice),
                                "on_walk": any(on_a_walk(e, n, walks)
                                               for e, n in lattice),
                                "on_what_stands": sorted(s["structure"] for s in on_what)})
            n0 += STEP_M
        e0 += STEP_M
    return out


SIDECARS = DATA / "sidecars" / "1835"


def world_footprint(sidecar: dict) -> list[tuple[float, float]]:
    """A sidecar's footprint polygon in local ENU, oriented and placed.

    The same two lines `generate_plat_lots.world_footprint` uses, and the same sign as
    `world_polygon` above: `rotation_deg` is a compass bearing, so it turns the polygon
    CLOCKWISE. It is written separately from `world_polygon` because the inputs are
    different — that one reads a structure record's placed phase in UTM, this one reads
    the sidecar the renderer seats a mesh from, already in local ENU.
    """
    place = sidecar["placement"]
    theta = math.radians(float(place.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0, n0 = float(place["local_e"]), float(place["local_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos)
            for u, v in sidecar["footprint"]["polygon"]]


def inside_polygon(point: tuple[float, float],
                   poly: list[tuple[float, float]]) -> bool:
    """Ray cast. `measure_no_build_ground.inside` wants a closed ring; this does not."""
    e, n = point
    hit = False
    for (e1, n1), (e2, n2) in zip(poly, poly[1:] + poly[:1]):
        if (n1 > n) != (n2 > n):
            cut = e1 + (n - n1) * (e2 - e1) / (n2 - n1)
            if e < cut:
                hit = not hit
    return hit


def on_the_boards(west: float, east: float) -> list[tuple[str, str]]:
    """Every committed building on this reach that stands on a committed walk.

    T-1643, and it is the ratchet on what went wrong rather than on the ground. The
    sidecars are asked and not the records, because the sidecars are what the renderer
    seats a mesh from — `check.sh` already holds them to the records — so this reads the
    same numbers the walker's collision footprint is compiled from.

    BOTH containments are tested. A building standing across a walk is caught by
    sampling the footprint and asking whether any of it is on the boards; a walk running
    wholly INSIDE a large footprint is caught by sampling the centreline and asking
    whether any of it is in the building. Either way the visitor is stopped.
    """
    walks = committed_walks(west, east)
    if not walks or not SIDECARS.is_dir():
        return []
    out = []
    for path in sorted(SIDECARS.glob("*.json")):
        if path.name == "index.json":
            continue
        record = load(path)
        place = record.get("placement") or {}
        poly = record.get("footprint") or {}
        if place.get("local_e") is None or not poly.get("polygon"):
            continue
        ring = world_footprint(record)
        es = [e for e, _ in ring]
        ns = [n for _, n in ring]
        if max(es) < west - TRACK_MARGIN_M or min(es) > east + TRACK_MARGIN_M:
            continue
        if max(ns) < BOX_S_M - TRACK_MARGIN_M or min(ns) > BOX_N_M + TRACK_MARGIN_M:
            continue
        for walk in walks:
            caught = False
            e = min(es)
            while e <= max(es) + 1e-9 and not caught:
                n = min(ns)
                while n <= max(ns) + 1e-9:
                    if inside_polygon((e, n), ring) and on_a_walk(e, n, [walk]):
                        caught = True
                        break
                    n += MASK_M
                e += MASK_M
            if not caught:
                for (e1, n1), (e2, n2) in walk["segments"]:
                    span = math.dist((e1, n1), (e2, n2))
                    steps = max(1, int(span / MASK_M))
                    for i in range(steps + 1):
                        t = i / steps
                        if inside_polygon((e1 + (e2 - e1) * t, n1 + (n2 - n1) * t),
                                          ring):
                            caught = True
                            break
                    if caught:
                        break
            if caught:
                out.append((record.get("id") or path.stem, walk["id"]))
                break
    return out


def measure() -> dict:
    west, east = reach()
    width, depth = footprint_m()
    ground = Ground()
    tracks = unplatted_tracks(west, east)
    standing = standing_footprints(west, east)
    walks = committed_walks(west, east)
    rows = strip(ground, west, east)
    all_placements = fits(ground, west, east, width, depth, tracks, standing, walks)
    off_road = [p for p in all_placements if not p["in_track"]]
    in_track = [p for p in all_placements if p["in_track"]]
    # T-1642 and T-1643: the three masks are applied in this order and reported apart,
    # so the reading says which of them is holding a position out. A position in the
    # road is counted against the road even if boards or a building also cover it, and
    # one under boards against the boards; nothing here is double-held.
    on_walk = [p for p in off_road if p["on_walk"]]
    off_walk = [p for p in off_road if not p["on_walk"]]
    on_what_stands = [p for p in off_walk if p["on_what_stands"]]
    placements = [p for p in off_walk if not p["on_what_stands"]]
    widest = max(rows, key=lambda r: r["width_m"])
    end = platted_end()
    platted_rows = [r for r in rows if r["e"] <= end]
    widest_platted = max(platted_rows, key=lambda r: r["width_m"])

    def counted(subset):
        out = {}
        for tol in RELIEF_TOLERANCES:
            key = "none" if tol is None else f"{tol:.2f}"
            out[key] = sum(1 for p in subset if tol is None or p["relief_m"] <= tol)
        return out

    by_tolerance = counted(placements)
    on_street = counted([p for p in placements if p["e"] <= end])

    # HOW MANY MORE SHEDS THE GROUND TAKES, per relief clause: the largest set of the
    # free positions that do not overlap each other. This is the number the question
    # "does anything more of the plate belong here" is actually about, and a count of
    # positions is not it.
    more = {}
    more_where = {}
    for tol in RELIEF_TOLERANCES:
        key = "none" if tol is None else f"{tol:.2f}"
        subset = [p for p in placements if tol is None or p["relief_m"] <= tol]
        pack = takes_more(subset)
        more[key] = len(pack)
        more_where[key] = [{"e": q["e"], "n": q["n"], "bearing_deg": q["bearing_deg"],
                            "relief_m": q["relief_m"]} for q in pack]
    return {
        "reach": {"west_m": round(west, 2), "east_m": round(east, 2),
                  "west_is": BRIDGE, "east_is": "the Reservation's west line"},
        "footprint_m": {"width": width, "depth": depth, "family": FAMILY},
        "widest_free_strip": widest,
        "free_stations": sum(1 for r in rows if r["width_m"] > 0),
        "stations": len(rows),
        "fits": by_tolerance,
        "platted_end_m": round(end, 2),
        "widest_free_strip_beside_the_street": widest_platted,
        "fits_beside_the_street": on_street,
        "unplatted_tracks_masked": [
            {"id": t["id"], "track_width_m": t["track_width_m"],
             "corridor_width_m": t["corridor_width_m"]} for t in tracks],
        "fits_in_an_unplatted_track": counted(in_track),
        "fits_in_an_unplatted_corridor": counted(
            [p for p in placements if p["in_track_corridor"]]),
        "committed_walks_masked": [
            {"id": w["id"], "belongs_to": w["belongs_to"],
             "width_m": w["width_m"]} for w in walks],
        "fits_on_a_committed_walk": counted(on_walk),
        "standing_footprints_masked": [
            {"structure": s["structure"], "phase": s["phase"],
             "e_from": round(min(e for e, _ in s["ring"]), 2),
             "e_to": round(max(e for e, _ in s["ring"]), 2),
             "n_from": round(min(n for _, n in s["ring"]), 2),
             "n_to": round(max(n for _, n in s["ring"]), 2)}
            # EVERY FOOTPRINT THE MASK ACTUALLY USED, and not the ones that happen to
            # sit inside the strip's own box (T-1640). `standing_footprints` collects
            # what reaches the box plus `TRACK_MARGIN_M`, because a building outside the
            # box still covers ground a rectangle anchored inside it would stand on —
            # and this list then filtered that set back down to the box, so a refusal
            # could be reported with the building that caused it left unnamed. Measured
            # on the day: `south_bank_shed_dearborn_e2` stands wholly south of N 0 and
            # refused 15 of the reading's positions while appearing nowhere in the
            # transcript. The count and the list are now the same claim.
            for s in standing],
        "fits_on_what_stands": counted(on_what_stands),
        "takes_more": more,
        "takes_more_where": more_where,
        "strip": rows,
    }


def report(result: dict, json_out: bool = False) -> str:
    if json_out:
        return json.dumps(result, indent=1)
    r, f = result["reach"], result["footprint_m"]
    widest = result["widest_free_strip"]
    lines = [
        f"   the south bank from {r['west_is']} (local E {r['west_m']:.1f}) east to "
        f"{r['east_is']} (E {r['east_m']:.1f})",
        f"   {result['free_stations']} of {result['stations']} stations carry ANY dry "
        f"ground outside a platted corridor",
        f"   the widest such strip is {widest['width_m']:.2f} m, at E {widest['e']:.1f} "
        f"(N {widest['n_from']} to {widest['n_to']}, {widest['relief_m']:.2f} m of relief)",
        f"   the smallest footprint family {f['family']} allows is "
        f"{f['width']:.3f} x {f['depth']:.3f} m; positions it would stand at, "
        f"at any bearing:",
    ]
    for key, count in result["fits"].items():
        clause = "no relief clause" if key == "none" else f"relief <= {key} m"
        lines.append(f"      {clause:<22} {count}")
    beside = result["widest_free_strip_beside_the_street"]
    lines += [
        f"   BESIDE THE PLATTED STREET — west of South Water's own east end "
        f"(E {result['platted_end_m']:.1f}), which is the frontage the plate draws:",
        f"      the widest free strip is {beside['width_m']:.2f} m, at E {beside['e']:.1f}",
    ]
    for key, count in result["fits_beside_the_street"].items():
        clause = "no relief clause" if key == "none" else f"relief <= {key} m"
        lines.append(f"      {clause:<22} {count}")
    masked = result["unplatted_tracks_masked"]
    if masked:
        named = ", ".join(f"{t['id']} ({t['track_width_m']:.1f} m)" for t in masked)
        lines.append(f"   REFUSED FOR STANDING IN AN UNPLATTED TRAVELLED WAY — "
                     f"{named}, which plat_corridors does not carry:")
        for key, count in result["fits_in_an_unplatted_track"].items():
            clause = "no relief clause" if key == "none" else f"relief <= {key} m"
            lines.append(f"      {clause:<22} {count}")
        lines.append("   and of the positions above, those the same roads' "
                     "RECONSTRUCTED corridors would also refuse (reported, not gated):")
        for key, count in result["fits_in_an_unplatted_corridor"].items():
            clause = "no relief clause" if key == "none" else f"relief <= {key} m"
            lines.append(f"      {clause:<22} {count}")
    boards = result.get("committed_walks_masked") or []
    if boards:
        named = ", ".join(f"{w['id']} ({w['width_m']:.2f} m)" for w in boards)
        lines.append(f"   REFUSED FOR STANDING ON A COMMITTED WALK'S BOARDS — {named}:")
        for key, count in result["fits_on_a_committed_walk"].items():
            clause = "no relief clause" if key == "none" else f"relief <= {key} m"
            lines.append(f"      {clause:<22} {count}")
    stands = result.get("standing_footprints_masked") or []
    if stands:
        named = ", ".join(f"{s['structure']} (E {s['e_from']:.1f}-{s['e_to']:.1f}, "
                          f"N {s['n_from']:.1f}-{s['n_to']:.1f})" for s in stands)
        lines.append(f"   REFUSED FOR STANDING WHERE A BUILDING ALREADY STANDS — {named}:")
        for key, count in result["fits_on_what_stands"].items():
            clause = "no relief clause" if key == "none" else f"relief <= {key} m"
            lines.append(f"      {clause:<22} {count}")
    lines.append("   HOW MANY MORE THE GROUND TAKES — the largest set of the free "
                 "positions that do not overlap each other:")
    for key, count in result["takes_more"].items():
        clause = "no relief clause" if key == "none" else f"relief <= {key} m"
        where = result.get("takes_more_where", {}).get(key) or []
        at = ", ".join(f"E {q['e']:.1f} N {q['n']:.1f} @ {q['bearing_deg']:.0f} deg"
                       for q in where[:4])
        tail = ", ..." if len(where) > 4 else ""
        lines.append(f"      {clause:<22} {count}"
                     + (f"   ({at}{tail})" if at else ""))
    return "\n".join(lines)


def gate(quiet: bool = False) -> int:
    result = measure()
    baseline = load(BASELINE)
    failures: list[str] = []

    for key, count in result["fits"].items():
        was = baseline["fits"].get(key)
        if was is None:
            failures.append(f"the baseline carries no reading at relief {key}")
        elif count != was:
            failures.append(
                f"the smallest F1 footprint now stands at {count} position(s) with "
                f"relief {key}, and the baseline recorded {was} — T-0134's finding is "
                f"that this reach carries NO ground outside its own street, so a change "
                f"here re-opens the question rather than being a number to update")

    for key, count in result["fits_beside_the_street"].items():
        was = (baseline.get("fits_beside_the_street") or {}).get(key)
        if was is None:
            failures.append(f"the baseline carries no beside-the-street reading at {key}")
        elif count != was:
            failures.append(
                f"beside the platted street the smallest F1 footprint now stands at "
                f"{count} position(s) with relief {key}, and the baseline recorded "
                f"{was} — this is the frontage the plate draws, and a fit appearing "
                f"here is T-0134 re-opening")

    for key, count in result["fits_in_an_unplatted_track"].items():
        was = (baseline.get("fits_in_an_unplatted_track") or {}).get(key)
        if was is None:
            failures.append(f"the baseline carries no in-the-road reading at {key}")
        elif count != was:
            failures.append(
                f"{count} position(s) with relief {key} now stand in an unplatted "
                f"travelled way, and the baseline recorded {was} — the road moved, or "
                f"the ground under it did, and either way the finding is re-read before "
                f"this is banked")

    for key, count in result["fits_on_a_committed_walk"].items():
        was = (baseline.get("fits_on_a_committed_walk") or {}).get(key)
        if was is None:
            failures.append(f"the baseline carries no on-the-boards reading at {key}")
        elif count != was:
            failures.append(
                f"{count} position(s) with relief {key} now stand on a committed "
                f"walk's boards, and the baseline recorded {was} — a walk moved, or "
                f"the ground under it did, and a building seated on one of these is "
                f"what T-1643 had to undo")

    # AND THE THING THAT WENT WRONG, RATCHETED: no committed building on this reach
    # stands on a committed walk. T-1643. The counts above say how much of the reach
    # the boards take; this says whether anything is standing on them, which is the
    # question the reading failed to ask on 2026-09-26 and the smoke answered instead.
    for sid, walk in on_the_boards(result["reach"]["west_m"],
                                   result["reach"]["east_m"]):
        failures.append(f"{sid} stands on {walk}'s boards — a committed walk is a "
                        f"surface a visitor walks on, and a building seated across it "
                        f"blocks the walk and cannot be re-derived from anything")

    for key, count in result["fits_on_what_stands"].items():
        was = (baseline.get("fits_on_what_stands") or {}).get(key)
        if was is None:
            failures.append(f"the baseline carries no on-what-stands reading at {key}")
        elif count != was:
            failures.append(
                f"{count} position(s) with relief {key} now stand on a footprint the "
                f"tree already places, and the baseline recorded {was} — a building on "
                f"this reach was added, moved or removed, and the reading of what ground "
                f"is left is re-read before it is banked")

    for key, count in result["takes_more"].items():
        was = (baseline.get("takes_more") or {}).get(key)
        if was is None:
            failures.append(f"the baseline carries no takes-more reading at {key}")
        elif count != was:
            failures.append(
                f"the ground now takes {count} more shed(s) at relief {key}, and the "
                f"baseline recorded {was} — T-1642's finding is that this reach takes "
                f"ONE more and that nothing of the plate belongs on it, so a change here "
                f"re-opens that refusal rather than being a number to update")

    for field in ("widest_free_strip", "widest_free_strip_beside_the_street"):
        widest = result[field]["width_m"]
        was = baseline[field]["width_m"]
        if abs(widest - was) > 0.01:
            failures.append(f"{field} moved {was:.2f} -> {widest:.2f} m; re-read the "
                            f"finding before banking it")

    if not quiet or failures:
        print(report(result))
    for line in failures:
        print(f"   {line}")
    return 1 if failures else 0


def self_test() -> int:
    """The assertions still fire when the ground under them moves."""
    problems = []
    ground = Ground()
    west, east = reach()
    width, depth = footprint_m()

    # 1. A rectangle standing in the middle of the river is refused.
    wet = fits(ground, 760.0, 760.0, width, depth)
    if any(p for p in wet if p["n"] > 30):
        problems.append("a footprint standing in open water was accepted")

    # 2. The sweep is not vacuous: the same rectangle DOES stand on the plateau south of
    #    the corridor, which is where the town's own South Water frontage is built.
    class Unplatted(Ground):
        def free(self, e, n):
            h = self.height(e, n)
            return h is not None and h > WATER_SURFACE_M
    loose = fits(Unplatted(), 770.0, 780.0, width, depth)
    if not loose:
        problems.append("with the corridor rule off, nothing fits anywhere on the "
                        "reach — the sweep is refusing for the wrong reason")

    # 3. The reach's own ends are resolved, not typed.
    if not (west < east):
        problems.append("the reach does not read west to east")

    # 4. The unplatted travelled ways are found, and the fort road is one of them —
    #    plat_corridors carries the platted grid and cannot see it (T-1636).
    tracks = unplatted_tracks(west, east)
    if "fort_road" not in [t["id"] for t in tracks]:
        problems.append("fort_road is not masked on this reach, so the reading would "
                        "report the town's only way to the fort as free ground")

    # 5. The mask is not vacuous: a point on the fort road's own centreline is in it,
    #    and a point 30 m north of the road on the same station is not.
    if tracks:
        on_road = [(e, n) for (e, n), _ in tracks[0]["segments"]][:1]
        if on_road:
            e, n = on_road[0]
            if not in_a_track(e, n, tracks):
                problems.append("a point on an unplatted centreline is not in its track")
            if in_a_track(e, n + 30.0, tracks):
                problems.append("a point 30 m off the centreline is inside the track")

    # 6. What already stands is found on this reach, and the shed the released ground
    #    carries is one of them (T-1642). Without this the reading counts one building's
    #    own footprint as free ground, once per lattice offset and bearing.
    standing = standing_footprints(west, east)
    on_reach = [s["structure"] for s in standing
                if min(n for _, n in s["ring"]) <= BOX_N_M
                and max(n for _, n in s["ring"]) >= BOX_S_M]
    if "south_bank_shed_dearborn_e1" not in on_reach:
        problems.append("the freight shed standing on the released strip is not masked, "
                        "so its own footprint would be reported as free ground")

    # 7. The mask is not vacuous, and it refuses the right thing: a rectangle laid down
    #    ON a standing footprint is flagged, and the same rectangle 40 m north is not.
    shed = [s for s in standing if s["structure"] == "south_bank_shed_dearborn_e1"]
    if shed:
        ring = shed[0]["ring"]
        if not overlaps(ring, ring):
            problems.append("a footprint does not overlap itself")
        shifted = [(e, n + 40.0) for e, n in ring]
        if overlaps(ring, shifted):
            problems.append("a footprint 40 m away overlaps the one it was copied from")
        wall_to_wall = [(e, n + 11.0) for e, n in ring]
        if overlaps(ring, wall_to_wall):
            problems.append("two sheds clear of each other are reported as overlapping")

    # 8. The pack is a maximum and not a count: a set of positions that all overlap each
    #    other takes ONE building, however many ways it could be nudged.
    if shed:
        ring = shed[0]["ring"]
        nudged = [{"ring": [(e + i * 0.5, n) for e, n in ring]} for i in range(6)]
        if len(takes_more(nudged)) != 1:
            problems.append("six offsets of one rectangle were packed as more than one "
                            "building")
        apart = nudged + [{"ring": [(e + 60.0, n) for e, n in ring]}]
        if len(takes_more(apart)) != 2:
            problems.append("a rectangle 60 m clear of the rest was not packed beside it")

    # 9. The committed walks are found, and the riverside walk's east end is one of
    #    them — it is the run `south_bank_shed_dearborn_e1` was seated across (T-1643).
    walks = committed_walks(west, east)
    if "river_plank_walk_crossing_footway" not in [w["id"] for w in walks]:
        problems.append("the riverside walk's east end is not masked on this reach, so "
                        "the reading would report its boards as free ground")

    # 10. The board mask is not vacuous: the walk's own centreline is on it, and a point
    #     ten metres north of the same station — out in the river — is not.
    if walks:
        (e, n), _ = walks[0]["segments"][0]
        if not on_a_walk(e, n, walks):
            problems.append("a point on a committed walk's centreline is not on it")
        if on_a_walk(e, n + 10.0, walks):
            problems.append("a point 10 m off the centreline is on the boards")

    # 11. The standing-on-the-boards gate fires when a building is put on them. The
    #     committed tree must be clean, and the shed moved back to where T-1636 seated
    #     it must be caught — that is the exact defect, asserted rather than trusted.
    if on_the_boards(west, east):
        problems.append("a committed building on this reach stands on a walk, and the "
                        "gate that says so is being asserted against a dirty tree")
    if walks:
        seat = {"id": "self_test_shed", "placement": {"local_e": 810.896,
                "local_n": 18.455, "rotation_deg": 173.774},
                "footprint": {"polygon": [[0, 0], [5.4864, 0], [5.4864, 9.7536],
                                          [0, 9.7536]]}}
        ring = world_footprint(seat)
        hit = any(inside_polygon((e, n), ring) and on_a_walk(e, n, walks)
                  for e in [805.5 + i * MASK_M for i in range(14)]
                  for n in [8.0 + i * MASK_M for i in range(22)])
        if not hit:
            problems.append("T-1636's own seating for south_bank_shed_dearborn_e1 is "
                            "not read as standing on the riverside walk, so the gate "
                            "would not have caught the thing it was written for")

    for line in problems:
        print(f"   {line}")
    if not problems:
        print("   11 assertions fire")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true", help="the ratchet check.sh runs")
    parser.add_argument("--self-test", action="store_true", dest="self_test",
                        help="the assertions still fire")
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--write-baseline", action="store_true", dest="write",
                        help="record the reading, only when the finding is re-read")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.gate:
        return gate(quiet=args.quiet)
    result = measure()
    if args.write:
        payload = {k: v for k, v in result.items() if k != "strip"}
        payload["$note"] = (
            "T-0134. The reading this project's refusal of the plate's south-bank "
            "warehouses stands on. Written by "
            "tools/measure_south_bank_ground.py --write-baseline, and only when the "
            "finding has been re-read: a fit appearing on this reach is the question "
            "re-opening, not a number to bank."
        )
        BASELINE.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        print(f"   wrote {BASELINE.relative_to(ROOT)}")
    print(report(result, json_out=args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
