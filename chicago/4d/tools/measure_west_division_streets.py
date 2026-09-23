#!/usr/bin/env python3
"""West Water seated, and Jefferson and Des Plaines refused by the ground (T-0445).

T-0445 is piece 2 of 4 of T-0443. T-0444 measured the West Division's module and
found three of the plat's five north-south streets held by no committed file at
all — `west_water`, `jefferson`, `des_plaines`. Its own memo would not move
anything; this is the ticket that seats what can be seated and states, in
numbers, what cannot.

The three do not get the same answer, and the reason is the modelled ground:

1. **West Water is seatable and is seated.** It is the West Division's riverfront
   street, and the riverfront is committed — `data/terrain/epochs/e1834_harbor_cut/
   river.geojson` carries the west bank of the South Branch as a traced line. The
   centreline is that bank offset one half-corridor (12.192 m) west, so the
   street's EAST KERB stands on the 1834 waterline. That is the furthest east the
   street can be, which is what T-0444's swap test already leaned on; here it is
   the placement, and the note on the record says what would move it (any wharf
   strip between the kerb and the water, whose width no source reached gives).

2. **Jefferson and Des Plaines are refused, and the refusal is a measurement.**
   Both survive on the ground and their surviving control is already committed —
   `fulton`'s note carries the OpenStreetMap intersections T-0446 fitted it to,
   Jefferson at local east -401.04 and Des Plaines at -524.88. The modelled ground
   ends at local east -320.0 (`heightfield.json`, `box_local_enu_m.e`). Both lines
   lie WEST of that edge over their whole length. A street drawn there would hang
   off the end of the terrain, and the plat gate that already refuses a block for
   exactly this reason (`measure_southern_ground.py`) is the same rule. So they are
   refused with the number that refuses them, and the refusal names what would
   reverse it: extending the terrain box west, which is the same parcel that holds
   35 of the West Division's 55 recipe roofs (ROADMAP K15, LIBERTIES L90).

3. **What the seating says about the module, which is the finding.** T-0444 derived
   a 458 ft West Division module and measured the committed `clinton -> canal` gap
   at 405 ft, calling it 90 ft short; T-0446 then measured the West Division's
   east-west tier band at 405 ft too and put both readings on the table without
   choosing. The line seated here is a THIRD measurement of the same module, taken
   between two lines fitted to different instruments — the traced 1834 bank and
   modern intersection control — and it is not 405 ft. It is close to 458. That
   does not settle the question, but it moves the anomaly: what is unusual is the
   `canal -> clinton` gap, not the module.

    tools/measure_west_division_streets.py              -> print the derivation
    tools/measure_west_division_streets.py --self-test  -> the assertions
    tools/measure_west_division_streets.py --gate       -> the assertions, quietly
"""
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FT = 0.3048

# The plat's West Division north-south streets, east to west, as T-0443 carries
# the owner's reading of the sheet.
WEST_NS = ["west_water", "canal", "clinton", "jefferson", "des_plaines"]

# T-0444's module: 2 x 180 ft lot depth + 18 ft alley + 80 ft street.
MODULE_FT = 458.0

# The two the plat carries that this reconstruction does not draw, with the
# surviving control that locates them. Both eastings are read off `fulton`'s own
# committed note, where T-0446 recorded the OpenStreetMap nodes it fitted that
# tier to; they are quoted here rather than re-fetched so this module reads
# committed files only.
OFF_THE_GROUND = {
    "jefferson": (-401.04, "262247424"),
    "des_plaines": (-524.88, "258966841"),
}

# The reach of the committed west-bank line that is the South Branch's, from the
# scene's south edge to where the bank turns west at Wolf Point. Vertices past
# this one run along the junction pool and then north up the North Branch, and a
# street offset from them would cross the Wolf Point cluster.
BANK_REACH = 9

# T-0768 — THE REACH PAST THE TURN. T-0445 stopped at BANK_REACH because a bank-offset line
# past the turn runs through the Wolf Point cluster. It never measured how far past the turn
# the line gets FIRST, and that is the question this ticket answers: the corridor is carried
# along the bank's next segment — vertices 8 -> 9, the junction pool's south face — until a
# committed footprint enters it, and cut there. The cut distance is DERIVED from the
# structure tree below, never typed in, so a building that moves moves the street's end.
CONT_SEGMENT = (8, 9)

# The five Wolf Point placements the continuation runs into, in the order the bank meets
# them. They are listed so the refusal is a table and not a sentence; their clearances are
# measured from committed files, not quoted here.
CLUSTER = [
    "james_kinzie_house",
    "robert_kinzie_store",
    "wolf_point_tavern",
    "wolf_point_tavern_stable",
    "robinson_caldwell_cabins",
    "walker_meeting_house",
]

# The cross street the 1839 address is given against: "W. Water st north of West Lake st".
CROSS_STREET = "lake"

# Northings at which the west_water -> canal module is measured. All three are
# inside the committed span of both lines.
MODULE_PROBES = [-400.0, -300.0, -250.0, -178.0, -120.0]


def load(rel):
    return json.loads((ROOT / rel).read_text())


def datum():
    d = load("data/datum.json")
    return d["origin_utm_e"], d["origin_utm_n"]


def west_bank():
    """The committed west bank of the South Branch, local ENU, south to north."""
    oe, on = datum()
    fc = load("data/terrain/epochs/e1834_harbor_cut/river.geojson")
    for f in fc["features"]:
        if "West Division shore" in str(f["properties"].get("name", "")):
            pts = [(c[0] - oe, c[1] - on) for c in f["geometry"]["coordinates"]]
            return pts, f["properties"].get("confidence")
    raise SystemExit("the West Division shore line is not in river.geojson")


def offset_west(path, half):
    """Offset a polyline by `half` metres to its left walking south to north.

    Segments are offset and their infinite lines intersected, which is the
    ordinary mitre: on this line the joints are shallow and every vertex lands
    within 0.11 m of `half` from the bank, which the assertions hold.
    """
    segs = []
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        segs.append(((x1 + nx * half, y1 + ny * half), (x2 + nx * half, y2 + ny * half)))

    def meet(a, b):
        (x1, y1), (x2, y2) = a
        (x3, y3), (x4, y4) = b
        den = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
        if abs(den) < 1e-9:
            return x2, y2
        t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / den
        return x1 + t * (x2 - x1), y1 + t * (y2 - y1)

    out = [segs[0][0]]
    for a, b in zip(segs, segs[1:]):
        out.append(meet(a, b))
    out.append(segs[-1][1])
    return out


def world_polygon(phase, oe, on):
    """A committed phase's footprint in local ENU, the GLB contract's own convention."""
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    th = math.radians(float(pos.get("rotation_deg") or 0.0))
    cos, sin = math.cos(th), math.sin(th)
    e0, n0 = float(pos["utm_e"]) - oe, float(pos["utm_n"]) - on
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def placed_phases():
    """(id, phase, world polygon) for every committed placed phase with a footprint."""
    oe, on = datum()
    out = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        for phase in record.get("phases") or []:
            pos = phase.get("position") or {}
            poly = (phase.get("footprint") or {}).get("polygon") or []
            if pos.get("utm_e") is None or len(poly) < 3:
                continue
            out.append((record["id"], phase, world_polygon(phase, oe, on)))
    return out


def segment_frame(a, b):
    """Unit along-vector and unit WEST normal of a bank segment walked south to north."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dx / L, dy / L), (-dy / L, dx / L), L


def band_entry(polygon, a, along, west, width):
    """Where a footprint first and last enters the corridor riverward of a bank segment.

    The corridor is the strip 0..`width` WEST of the segment — its east kerb on the
    waterline, which is how this street is placed. Edges are sampled rather than clipped:
    a corner is not enough, because a wall can cross the strip between two corners.
    """
    hits = []
    for i in range(len(polygon)):
        p1, p2 = polygon[i], polygon[(i + 1) % len(polygon)]
        for k in range(101):
            t = k / 100.0
            q = (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
            d = (q[0] - a[0], q[1] - a[1])
            off = d[0] * west[0] + d[1] * west[1]
            al = d[0] * along[0] + d[1] * along[1]
            if 0.0 <= off <= width and al >= 0.0:
                hits.append((al, off))
    if not hits:
        return None
    return (min(h[0] for h in hits), max(h[0] for h in hits),
            min(h[1] for h in hits), max(h[1] for h in hits))


def continuation():
    """The reach past the turn: where it may be carried, and what stops it.

    Returns the derived two-vertex tail — the mitre at the turn and the cut — together
    with the obstruction that sets the cut and the cluster clearances that refuse the rest.
    """
    corridor = load("data/streets/1835.json")["corridor_width_m"]
    bank, _conf = west_bank()
    i, j = CONT_SEGMENT
    a, b = bank[i], bank[j]
    along, west, seg_len = segment_frame(a, b)

    rows = []
    for sid, phase, poly in placed_phases():
        hit = band_entry(poly, a, along, west, corridor)
        if hit and hit[0] <= seg_len:
            rows.append((hit[0], sid, phase["id"], hit[1], hit[2], hit[3],
                         phase["position"].get("confidence")))
    rows.sort()
    cut_along = rows[0][0] if rows else seg_len

    half = corridor / 2.0
    mitre = offset_west(bank[:j + 1], half)[-2]
    cut = (a[0] + along[0] * cut_along + west[0] * half,
           a[1] + along[1] * cut_along + west[1] * half)

    # The clearance that refuses the rest: how close the cluster stands to the traced bank,
    # measured against the bank ITSELF rather than one straightened segment, because past
    # the junction pool the bank turns again and a single frame would flatter the answer.
    clearances = []
    for sid in CLUSTER:
        path = ROOT / "data" / "structures" / f"{sid}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        oe, on = datum()
        for phase in record.get("phases") or []:
            if (phase.get("position") or {}).get("utm_e") is None:
                continue
            poly = world_polygon(phase, oe, on)
            near = min(dist_to_polyline(v, bank) for v in poly)
            far = max(dist_to_polyline(v, bank) for v in poly)
            clearances.append((sid, phase["id"], near, far,
                               phase["position"].get("confidence")))
    return dict(corridor=corridor, seg_len=seg_len, obstructions=rows,
                cut_along=cut_along, mitre=mitre, cut=cut, clearances=clearances)


def lake_kerb_gap(tail):
    """How much of the reach lies north of West Lake Street's north kerb, old and new."""
    st = streets()
    corridor = load("data/streets/1835.json")["corridor_width_m"]
    lake = st[CROSS_STREET]["path_local_enu_m"]

    def lake_north_at(e):
        for (x1, y1), (x2, y2) in zip(lake, lake[1:]):
            if min(x1, x2) - 1e-9 <= e <= max(x1, x2) + 1e-9:
                return y1 + (e - x1) / (x2 - x1) * (y2 - y1)
        return None

    kerb_at_old = lake_north_at(-9.34) + corridor / 2.0
    old_gap = kerb_at_old - (-104.2)
    # The new reach's length north of the kerb, walked segment by segment.
    north = 0.0
    path = st["west_water"]["path_local_enu_m"]
    for (x1, y1), (x2, y2) in zip(path[-3:-1], path[-2:]):
        for k in range(1000):
            t0, t1 = k / 1000.0, (k + 1) / 1000.0
            m0 = (x1 + t0 * (x2 - x1), y1 + t0 * (y2 - y1))
            m1 = (x1 + t1 * (x2 - x1), y1 + t1 * (y2 - y1))
            kerb = lake_north_at((m0[0] + m1[0]) / 2)
            if kerb is not None and (m0[1] + m1[1]) / 2 > kerb + corridor / 2.0:
                north += math.dist(m0, m1)
    return old_gap, north


def dist_to_polyline(p, poly):
    best = float("inf")
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / L2))
        best = min(best, math.hypot(p[0] - (x1 + t * dx), p[1] - (y1 + t * dy)))
    return best


def streets():
    return {s["id"]: s for s in load("data/streets/1835.json")["streets"]}


def east_at(st, northing):
    """Where a north-south street stands at a northing, along its committed path."""
    path = st["path_local_enu_m"]
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        lo, hi = min(y1, y2), max(y1, y2)
        if lo - 1e-9 <= northing <= hi + 1e-9:
            if abs(y2 - y1) < 1e-9:
                return x1
            t = (northing - y1) / (y2 - y1)
            return x1 + t * (x2 - x1)
    return None


def fit_line(pts):
    """Least squares east = a*north + b, with residuals."""
    n = len(pts)
    mn = sum(p[1] for p in pts) / n
    me = sum(p[0] for p in pts) / n
    num = sum((p[1] - mn) * (p[0] - me) for p in pts)
    den = sum((p[1] - mn) ** 2 for p in pts)
    a = num / den
    b = me - a * mn
    res = [p[0] - (a * p[1] + b) for p in pts]
    rms = math.sqrt(sum(r * r for r in res) / n)
    return a, b, res, rms


def ground_box():
    hf = load("data/terrain/epochs/e1834_harbor_cut/heightfield.json")
    return hf["box_local_enu_m"]["e"]


def derive():
    st = streets()
    corridor = load("data/streets/1835.json")["corridor_width_m"]
    traced, bank_conf = west_bank()
    bank = traced[:BANK_REACH]
    tail = continuation()
    # The seated line is the South Branch reach mitred into the reach past the turn, so the
    # joint at the turn is the mitre and not the old perpendicular end (T-0768).
    centre = offset_west(traced[:CONT_SEGMENT[1] + 1], corridor / 2.0)[:-1] + [tail["cut"]]
    clearances = [dist_to_polyline(p, traced) for p in centre]
    a, b, res, rms = fit_line(bank)
    box_e = ground_box()

    modules = []
    for n in MODULE_PROBES:
        ww = east_at(st["west_water"], n) if "west_water" in st else None
        ca = east_at(st["canal"], n)
        if ww is None or ca is None:
            continue
        modules.append((n, ww, ca, ww - ca))
    return dict(
        corridor=corridor, bank=bank, bank_conf=bank_conf, centre=centre,
        clearances=clearances, fit=(a, b, res, rms), box_e=box_e,
        modules=modules, streets=st, traced=traced, tail=tail,
        lake=lake_kerb_gap(tail),
    )


def report(d):
    print("== 1. the anchor: the committed west bank of the South Branch")
    print(f"   {len(d['bank'])} vertices, local north {d['bank'][0][1]:.1f} to "
          f"{d['bank'][-1][1]:.1f}, graded {d['bank_conf']} (wright_1834)")
    a, b, res, rms = d["fit"]
    print(f"   a straight line through them: slope {a:.6f}, RMS {rms:.2f} m, "
          f"max residual {max(abs(r) for r in res):.2f} m")
    print()
    print("== 2. west_water — the bank offset one half-corridor west")
    print(f"   corridor {d['corridor']:.3f} m, so the centreline stands "
          f"{d['corridor'] / 2:.3f} m west of the waterline")
    for (e, n), c in zip(d["centre"], d["clearances"]):
        print(f"   [{e:8.2f}, {n:9.2f}]   {c:.3f} m from the bank")
    print()
    print("== 2b. the reach past the turn, and where it stops (T-0768)")
    tail = d["tail"]
    print(f"   the bank's Wolf Point segment runs {tail['seg_len']:.2f} m past the turn;")
    print(f"   the riverward corridor is clear for {tail['cut_along']:.2f} m of it")
    for al_in, sid, pid, al_out, off_lo, off_hi, conf in tail["obstructions"]:
        print(f"   first obstruction: {sid} ({pid}, {conf}) enters at {al_in:.2f} m and "
              f"leaves at {al_out:.2f} m, spanning {off_lo:.2f}-{off_hi:.2f} m west of "
              f"the bank — the roadway is 0-{d['corridor']:.2f} m")
    print(f"   so the line is cut at [{tail['cut'][0]:.2f}, {tail['cut'][1]:.2f}] — "
          f"{math.dist(tail['mitre'], tail['cut']):.2f} m of new centreline")
    old_gap, north = d["lake"]
    print(f"   the old end stood {old_gap:.2f} m SOUTH of West Lake Street's north kerb, "
          f"so the attested reach had zero length")
    print(f"   the new reach carries {north:.2f} m north of that kerb")
    print()
    print("== 2c. why no line fits past the cut — the clearance, structure by structure")
    print(f"   an 80 ft street needs {d['corridor']:.3f} m; "
          f"riverward of the cluster there is at most "
          f"{min(c[2] for c in tail['clearances']):.2f} m")
    for sid, pid, near, far, conf in tail["clearances"]:
        print(f"   {sid:26s} {conf:13s} nearest corner {near:6.2f} m from the bank, "
              f"furthest {far:6.2f} m")
    print()
    print("== 3. jefferson and des_plaines — refused by the modelled ground")
    print(f"   the heightfield's west edge is local east {d['box_e'][0]:.1f} m")
    for sid, (e, node) in OFF_THE_GROUND.items():
        print(f"   {sid:12s} surviving control at east {e:8.2f} "
              f"(OSM node {node}) — {d['box_e'][0] - e:6.1f} m past the edge")
    print()
    print("== 4. the module the seating measures")
    print(f"   the plat's module (T-0444): {MODULE_FT:.0f} ft = {MODULE_FT * FT:.2f} m")
    for n, ww, ca, gap in d["modules"]:
        print(f"   at north {n:7.1f}   west_water {ww:7.2f}   canal {ca:7.2f}"
              f"   gap {gap:6.2f} m = {gap / FT:5.1f} ft")
    if d["modules"]:
        mean = sum(m[3] for m in d["modules"]) / len(d["modules"])
        print(f"   mean {mean:.2f} m = {mean / FT:.1f} ft "
              f"({mean / FT - MODULE_FT:+.1f} ft against the plat's module)")
    st = d["streets"]
    cl = [east_at(st["clinton"], n) for n in MODULE_PROBES]
    ca = [east_at(st["canal"], n) for n in MODULE_PROBES]
    gaps = [c - k for c, k in zip(ca, cl) if c is not None and k is not None]
    if gaps:
        m = sum(gaps) / len(gaps)
        print(f"   for comparison, canal -> clinton over the same probes: "
              f"{m:.2f} m = {m / FT:.1f} ft")


def self_test(quiet=False):
    d = derive()
    fails = []

    def check(label, ok):
        if not ok:
            fails.append(label)
        if not quiet:
            print(f"  {'ok  ' if ok else 'FAIL'} {label}")

    st = d["streets"]
    check("west_water is committed to data/streets/1835.json", "west_water" in st)
    if "west_water" in st:
        ww = st["west_water"]
        committed = [tuple(p) for p in ww["path_local_enu_m"]]
        derived = [(round(e, 2), round(n, 2)) for e, n in d["centre"]]
        check("its committed path is the derived bank offset, to the centimetre",
              committed == derived)
        check("its geometry is graded no better than the bank it is offset from",
              ww["geometry_confidence"] == d["bank_conf"])
        check("wright_1834 — the bank's own source — is cited on it",
              "wright_1834" in ww["sources"])
        check("the plat that carries the street is cited on it",
              "thompson_plat_1830" in ww["sources"])

    tail = d["tail"]
    check("the reach past the turn is cut where a committed footprint enters the corridor",
          bool(tail["obstructions"])
          and abs(tail["cut_along"] - tail["obstructions"][0][0]) < 1e-9)
    check("james_kinzie_house is what stops it, and it stands ACROSS the roadway",
          bool(tail["obstructions"])
          and tail["obstructions"][0][1] == "james_kinzie_house"
          and tail["obstructions"][0][4] > 0.0
          and tail["obstructions"][0][5] < d["corridor"])
    check("the cut is inside the bank segment it is measured along, not past its end",
          tail["cut_along"] < tail["seg_len"])
    old_gap, north = d["lake"]
    check(f"T-0445's end stood SOUTH of West Lake Street's north kerb "
          f"({old_gap:.2f} m), so the attested reach had zero length", old_gap > 0)
    check(f"the seated continuation carries real frontage north of that kerb "
          f"({north:.2f} m)", north > 15.0)
    worst = min(c[2] for c in tail["clearances"])
    check(f"no line fits riverward of the cluster: the widest clear strip between the "
          f"water and it is {worst:.2f} m against {d['corridor']:.3f} m",
          worst < d["corridor"])
    check("and the refusal is measured on every one of the cluster's placements",
          sorted({c[0] for c in tail["clearances"]}) == sorted(CLUSTER))

    check("every vertex stands one half-corridor from the bank, within 0.15 m",
          all(abs(c - d["corridor"] / 2) <= 0.15 for c in d["clearances"]))
    check("the street's east kerb therefore reaches the waterline and no further",
          max(d["clearances"]) - d["corridor"] / 2 < 0.15)

    box_w = d["box_e"][0]
    for sid, (e, _node) in OFF_THE_GROUND.items():
        check(f"{sid} is west of the modelled ground's edge and is refused",
              e < box_w)
        check(f"{sid} is not committed to data/streets/1835.json", sid not in st)
    check("the two refused streets are the only West Division lines still absent",
          sorted(s for s in WEST_NS if s not in st) == sorted(OFF_THE_GROUND))

    if d["modules"]:
        mean_ft = sum(m[3] for m in d["modules"]) / len(d["modules"]) / FT
        check(f"west_water -> canal measures within 40 ft of the plat's module "
              f"({mean_ft:.1f} ft against {MODULE_FT:.0f})",
              abs(mean_ft - MODULE_FT) <= 40.0)
        check("…and it is a wider gap than canal -> clinton, which is the anomaly",
              mean_ft > 420.0)
    else:
        check("the module probes found both lines", False)

    a, _b, res, rms = d["fit"]
    check("the bank's straight-line residual is stated and under 4 m", rms < 4.0)

    if not quiet:
        print()
        print("FAIL" if fails else "self-test OK — every assertion holds")
    if fails:
        for f in fails:
            print(f"  failed: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    if "--gate" in sys.argv:
        raise SystemExit(self_test(quiet=True))
    report(derive())
