"""Terrain for e1830_natural: the 1812 ground, generated as an overlay on the 1834 field (T-2003).

    # river.geojson + heightfield (numpy is the one dependency)
    python3 generators/terrain_gen_e1830.py

    # re-derive both in memory and compare with the committed bytes, writing nothing
    python3 generators/terrain_gen_e1830.py --check

    # river.geojson, heightfield AND the terrain / water GLBs
    blender -b -noaudio --factory-startup --python generators/terrain_gen_e1830.py -- --glb

T-2003, piece 2 of T-1243. `data/terrain/epochs/e1830_natural/terrain_spec.json` is not a
zone table of its own: it names every block of the 1834 spec and says what 1812 does with
it (T-2002). `tools/check_terrain_e1830.resolve()` turns that into the effective 1812 table
and this file is its one reader. It does three things and nothing else:

1. WRITES THE 1812 MOUTH into `e1830_natural/river.geojson`, out of committed lines only:
   the 1834 harbour-reach ring with the cut, the piers and the sand caught against them
   taken out, the spit's isthmus laid across the gap L240 left, and the lake shore north
   of the spit root joined smoothly to the outer bar as `north_lake_shore_1812` says
   (T-2171). Endpoints come from committed traces; the curve is reconstructed.

2. TRANSLATES the effective table into the shape `terrain_gen.build_field` reads and
   calls it, so the 1812 ground is the 1834 field's own arithmetic on the 1812 planform:
   the same grid, divisions, banks, sloughs, dunes and evidence limit.

3. SURFACES THE SPIT AND ITS NECK, which `build_field` cannot. It knows islands — land
   inside water — and builds each from its ring as a WATERLINE all round. A spit joined
   to the mainland has no waterline across its root, so an island ring would notch the
   neck to the water plane exactly where the isthmus decision says there is none
   (a lower neck is a breach, which is 1834's landform). So the spit and the neck are
   fed in as land the lake rules may not flood, and lifted to `spit_1812.crest_ft`
   across `spit_1812.face_m` here, after the field is built, grading into the mainland
   across the neck's own width where the two meet.

`terrain_gen.py` is not edited: its bytes are hashed into the 1834 and 1904 grounds, and
this epoch needs nothing of it that it does not already export.

Confidence, as `terrain_spec.json` states it: every land vertex is at best inferred (the
1834 field's own grade), every vertex south of Twelfth Street is conjectural
(`evidence_limit`), the spit and neck are conjectural (reconstructed), and so is every
vertex of the channel and of the ground within Harrison's worst separation west of it
between the adopted outlet and his old mouth (`channel_west_bank_ruling`). No vertex is
documented.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / "generators", ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import terrain_gen as tg  # noqa: E402  (flat, generators/ is on sys.path)
from check_terrain_e1830 import resolve  # noqa: E402  (T-2002: the effective 1812 table)

np = tg.np
FT = 0.3048
EPOCH = "e1830_natural"
BASE = "e1834_harbor_cut"
EP_DIR = ROOT / "data" / "terrain" / "epochs" / EPOCH
BASE_DIR = ROOT / "data" / "terrain" / "epochs" / BASE
# Every vector file the 1834 field loads. The 1812 field carries four of their water
# polygons and ten of their shore runs, so it loads the same set.
BASE_VECTORS = ("river.geojson", "hydrology.geojson", "shoreline.geojson", "branches.geojson",
                "south_branch_below_twelfth.geojson", "lake_shore_below_twelfth.geojson")
MOUTH_READINGS = ROOT / "data" / "terrain" / "1812_mouth_readings.json"
OUT_NAME = "river.geojson"

# The ids this file writes into river.geojson.
MOUTH_ID = "river_mouth_water_1812"
LAND_ID = "spit_and_isthmus_1812"
SHORE_ID = "spit_and_isthmus_shore_1812"
NORTH_ID = "north_lake_shore_1812"


def load(p: Path):
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# plane geometry, local ENU metres
# ---------------------------------------------------------------------------

def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def line_hits(p, d, pts, closed=False):
    """Every crossing of the infinite line p + t*d with the polyline `pts`.

    Returns (t, segment index, s) with s in [0, 1] along the segment.
    """
    out = []
    n = len(pts)
    for i in range(n if closed else n - 1):
        a, b = pts[i], pts[(i + 1) % n]
        e = (b[0] - a[0], b[1] - a[1])
        den = _cross(d, e)
        if abs(den) < 1e-12:
            continue
        w = (a[0] - p[0], a[1] - p[1])
        t = _cross(w, e) / den
        s = _cross(w, d) / den
        if -1e-9 <= s <= 1.0 + 1e-9:
            out.append((t, i, min(1.0, max(0.0, s))))
    return out


def at(p, d, t):
    return (p[0] + t * d[0], p[1] + t * d[1])


def to_local(coords, origin):
    return [(c[0] - origin[0], c[1] - origin[1]) for c in coords]


def to_utm(pts, origin):
    return [[round(x + origin[0], 3), round(y + origin[1], 3)] for x, y in pts]


def same(a, b, tol=1e-6):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def ring_index(ring, p):
    hit = [i for i, q in enumerate(ring) if same(q, p, 0.006)]
    if not hit:
        raise SystemExit(f"REFUSING: ({p[0]:.2f}, {p[1]:.2f}) is not a vertex of the 1834 "
                         f"harbour ring, so the splice it anchors cannot be made")
    return hit[0]


# ---------------------------------------------------------------------------
# 1. the 1812 mouth, from committed lines
# ---------------------------------------------------------------------------

def lake_curve(before, start, end, after, segments):
    """E(N) cubic Hermite: trace tangents, clamped to forbid a new inlet/overshoot.

    The shape is reconstructed, not a digitised 1812 survey. Northing is strictly
    increasing; eastings stay between the carried endpoints. 24 chords resolve the
    ~213 m join at less than the terrain's bank-face width.
    """
    span = end[1] - start[1]
    if span <= 0 or segments < 2 or end[0] >= start[0]:
        raise ValueError("outer lake join must run north and west")
    secant = (end[0] - start[0]) / span
    def slope(a, b):
        raw = (b[0] - a[0]) / (b[1] - a[1])
        return max(3 * secant, min(0, raw))
    m0, m1 = slope(before, start), slope(end, after)
    # Monotone cubic sufficient condition; preserve direction if tangents are steep.
    norm = math.hypot(m0 / secant, m1 / secant)
    if norm > 3:
        m0, m1 = m0 * 3 / norm, m1 * 3 / norm
    pts = []
    for i in range(segments + 1):
        t = i / segments
        e = ((2*t**3 - 3*t**2 + 1)*start[0] + (t**3 - 2*t**2 + t)*span*m0
             + (-2*t**3 + 3*t**2)*end[0] + (t**3 - t**2)*span*m1)
        pts.append((e, start[1] + t*span))
    return pts


def derive_mouth(base_feats, shore_1812, spec, origin):
    """The four features river.geojson carries, in local metres, with what each rests on."""
    f12 = {f["id"]: f for f in shore_1812["features"]}
    harbour = base_feats[spec["water_bodies_1812"]["mouth"]["from"]]["geometry"]["coordinates"]
    ring = to_local(harbour[0], origin)[:-1]
    n34 = to_local(base_feats["north_shore_harbor_reach"]["geometry"]["coordinates"], origin)
    bank = to_local(f12["north_shore_pre_cut_1812"]["geometry"]["coordinates"], origin)
    gap = to_local(f12[spec["isthmus_1812"]["feature"]]["geometry"]["coordinates"], origin)
    spit = to_local(f12[spec["spit_1812"]["feature"]]["geometry"]["coordinates"][0], origin)[:-1]

    root, corner = gap[0], gap[-1]
    if not same(root, bank[-1], 0.006):
        raise SystemExit("REFUSING: the isthmus line does not start at the north bank's last "
                         "vertex, so the spit root is not where both files say it is")
    # north_lake_shore_1812: the chord runs to the first 1834 vertex past the pier head.
    cp = load(MOUTH_READINGS)["cut_and_piers"]
    first = int(cp["accretion_bound_first_index"])
    if int(cp["north_shore_last_natural_vertex_index"]) != len(bank) - 1:
        raise SystemExit("REFUSING: the mouth readings and north_shore_pre_cut_1812 disagree about "
                         "which 1834 vertex is the spit root")
    if not same(n34[len(bank) - 1], root, 0.006):
        raise SystemExit("REFUSING: north_shore_pre_cut_1812 is no longer 1834 north_shore_harbor_reach "
                         "vertices 0..29, so the chord's indices do not name what the spec says")
    chord_end = n34[first]

    # The neck: a ribbon `width_ft` wide on the gap line. Its edges are carried back to the
    # shore they leave (the north bank on the river side, the chord on the lake side) and
    # forward to the spit ring they reach, so the neck meets both bodies of land exactly.
    half = 0.5 * float(spec["isthmus_1812"]["width_ft"]) * FT
    L = math.hypot(corner[0] - root[0], corner[1] - root[1])
    u = ((corner[0] - root[0]) / L, (corner[1] - root[1]) / L)
    n_sw, n_ne = (u[1], -u[0]), (-u[1], u[0])          # bearing + 90 and - 90 degrees
    p_sw0 = (root[0] + half * n_sw[0], root[1] + half * n_sw[1])
    p_ne0 = (root[0] + half * n_ne[0], root[1] + half * n_ne[1])

    # river side: the last crossing of the SW edge with the bank, behind the root
    # Each face is carried to the NEAREST crossing of its own line with the shore it leaves,
    # either side of the offset point: the river face meets the bank behind the root, the
    # lake face meets the chord a little ahead of it.
    hits = line_hits(p_sw0, u, bank)
    if not hits:
        raise SystemExit("REFUSING: the neck's south-west face never meets the north bank")
    t, i_bank, _ = min(hits, key=lambda h: abs(h[0]))
    p_sw = at(p_sw0, u, t)
    # Preserve the river-side neck exactly. Its old outer face and root-to-shore
    # chord made an unsupported V in the lake edge (T-2171). The lake face now
    # follows a monotone Hermite join between two carried trace vertices.
    hs = sorted(h for h in line_hits(p_sw0, u, spit, closed=True) if h[0] > t)
    if not hs:
        raise SystemExit("REFUSING: the river-side neck never reaches the spit")
    x_sw, i_sw = at(p_sw0, u, hs[0][0]), hs[0][1]
    curve = spec["north_lake_shore_1812"]["curve"]
    join = int(curve["spit_vertex_index"])
    n = len(spit)
    ic = min(range(n), key=lambda k: math.dist(spit[k], corner))
    arc_a = [spit[(i_sw + 1 + k) % n] for k in range((join - i_sw) % n)]
    arc_b = [spit[(i_sw - k) % n] for k in range((i_sw - join) % n + 1)]
    arc = arc_b if spit[ic] in arc_a else arc_a
    if not arc or not same(arc[-1], spit[join]) or spit[ic] in arc:
        raise SystemExit("REFUSING: the outer join must keep the long spit arc and southern tip")
    lake_join = lake_curve(arc[-2], arc[-1], chord_end, n34[first + 1],
                           int(curve["segments"]))
    shore = [p_sw, x_sw] + arc + lake_join[1:]
    p_ne = chord_end
    x_ne = arc[-1]
    bank_cut = bank[:i_bank + 1] + [p_sw]
    # The land the 1812 water goes round: the neck and the spit, closed against the
    # mainland along the 1834 shore it leaves.
    land = shore + [root] + list(reversed(bank[i_bank + 1:-1]))
    north = [chord_end] + n34[first + 1:]

    # The water: the 1834 harbour ring, spliced. It runs S68..S135 (the channel's west bank,
    # up to the forks window), N0..N62 (the north shore), the window, the lake edge, and
    # S0..S67. The 1812 ring keeps every vertex of it except the north shore's from the
    # bank's cut point to the pier head, which become the neck, the spit and the chord.
    i_root = ring_index(ring, n34[0])                   # where the north shore starts
    i_head = ring_index(ring, n34[first])
    if i_head <= i_root:
        raise SystemExit("REFUSING: the 1834 ring does not run the north shore west to east")
    mouth = ring[:i_root] + bank_cut + shore[1:] + ring[i_head + 1:]
    island = spec["spit_1812"]["feature"]
    holes = [r for r in harbour[1:]]
    if len(holes) != 1 or len(to_local(holes[0], origin)) - 1 != len(spit):
        raise SystemExit(f"REFUSING: the 1834 harbour ring's one hole is no longer the bar "
                         f"{island} carries whole")

    def prop_pt(fid, key):
        v = f12[fid]["properties"][key]
        return tuple(json.loads(v) if isinstance(v, str) else v)

    return {
        "outlet": prop_pt("channel_west_bank_1812", "outlet_station_local"),
        "bar_tip": prop_pt(spec["spit_1812"]["feature"], "south_tip_local"),
        # where the neck meets the mainland: the 1834 shore from one face to the other
        "root_line": [p_sw] + bank[i_bank + 1:-1] + [root, p_ne],
        "mouth": mouth, "land": land, "shore": shore, "north": north, "bank_cut": bank_cut,
        "root": root, "p_sw": p_sw, "p_ne": p_ne, "x_sw": x_sw, "x_ne": x_ne,
        "chord_end": chord_end, "first": first, "half_m": half, "lake_join": lake_join,
    }


def mouth_geojson(geo, spec, origin):
    def ring_closed(pts):
        return to_utm(pts + [pts[0]], origin)

    def loc(p):
        return [round(p[0], 2), round(p[1], 2)]

    prov = {"derived_by": "generators/terrain_gen_e1830.py",
            "spec": "data/terrain/epochs/e1830_natural/terrain_spec.json",
            "base_trace": "data/terrain/epochs/e1834_harbor_cut/shoreline.geojson",
            "ticket": "T-2171"}
    feats = [
        {"type": "Feature", "id": MOUTH_ID,
         "properties": {
             "kind": "water", "name": "The 1812 river: the main stem, the channel behind the spit, the "
                                      "mouth and the lake margin",
             "confidence": spec["water_bodies_1812"]["confidence"],
             "derivation": "1834 harbor_reach_water's outer ring, less the north shore from the cut on "
                           "the north bank to the pier head (1834 index " + str(geo["first"]) + "), which "
                           "becomes the neck's south-west face, the spit's ring and the neck's north-east "
                           "lake-facing curve; the 1834 interior ring (the bar) is gone because the bar is no longer "
                           "an island",
             "opens_between_local": json.dumps([loc(geo["outlet"]), loc(geo["bar_tip"])]),
             "sources": spec["water_bodies_1812"]["sources"],
             "provenance": prov},
         "geometry": {"type": "Polygon", "coordinates": [ring_closed(geo["mouth"])]}},
        {"type": "Feature", "id": LAND_ID,
         "properties": {
             "kind": "spit", "name": "The baymouth spit and the neck that joined it to the north shore",
             "confidence": "reconstructed",
             "derivation": "river-side neck offset by half isthmus_1812.width_ft from the gap line; "
                           "the long spit arc to north_lake_shore_1812.curve.spit_vertex_index; "
                           "a reconstructed monotone curve to the carried north shore; closed "
                           "against the mainland. width_ft controls the river face, not full land width",
             "river_side_offset_m": round(geo["half_m"], 3),
             "sources": spec["isthmus_1812"]["sources"],
             "provenance": prov},
         "geometry": {"type": "Polygon", "coordinates": [ring_closed(geo["land"])]}},
        {"type": "Feature", "id": SHORE_ID,
         "properties": {
             "kind": "shore", "name": "The waterline round the neck and the spit",
             "confidence": "reconstructed",
             "derivation": "the neck's south-west face from the north bank, the spit's ring the long "
                           "way round to the outer join, then the reconstructed lake curve to the north shore",
             "meets_north_bank_local": json.dumps(loc(geo["p_sw"])),
             "meets_north_lake_shore_local": json.dumps(loc(geo["p_ne"])),
             "sources": spec["isthmus_1812"]["sources"],
             "provenance": prov},
         "geometry": {"type": "LineString", "coordinates": to_utm(geo["shore"], origin)}},
        {"type": "Feature", "id": NORTH_ID,
         "properties": {
             "kind": "shore", "name": "The lake shore north of the spit root",
             "confidence": spec["north_lake_shore_1812"]["confidence"],
             "derivation": "1834 north_shore_harbor_reach from index " + str(geo["first"])
                           + " north; the reconstructed outer curve meets this run at its first vertex",
             "curve_from_local": json.dumps(loc(geo["x_ne"])),
             "curve_to_local": json.dumps(loc(geo["chord_end"])),
             "sources": spec["north_lake_shore_1812"]["sources"],
             "provenance": prov},
         "geometry": {"type": "LineString", "coordinates": to_utm(geo["north"], origin)}},
    ]
    return {"type": "FeatureCollection",
            "_doc": "GENERATED by generators/terrain_gen_e1830.py from the e1830_natural spec, its "
                    "shoreline.geojson and the 1834 harbour trace (T-2003) - do not hand-edit. "
                    "Coordinates are UTM 16N metres, as every other terrain vector file here.",
            "features": feats}


def spec_shore(_spec=None):
    return load(EP_DIR / "shoreline.geojson")


# ---------------------------------------------------------------------------
# 2. the effective table, in the shape build_field reads
# ---------------------------------------------------------------------------

# The figures of south_lake_sand_hills_1812 that build_field's dune pass reads; the same
# set terrain_inputs.CONSUMED declares for it.
SAND_HILL_KEYS = ("id", "n_range", "end_fade_m", "west_limit_e_m", "west_fade_m", "ridges",
                  "hollow", "wander_m", "wander_wavelength_m", "hummock_wavelength_m", "seed")


def field_spec(spec, base, eff):
    """The 1834 field's own spec keys, filled from the effective 1812 table."""
    fs = dict(eff)
    renames = {k: v for k, v in spec["inherits"]["rename_runs"].items() if not k.startswith("_")}
    wb = spec["water_bodies_1812"]
    fs["water_polygons"] = [wp for wp in base["water_polygons"] if wp["feature"] in wb["carried"]]
    if len(fs["water_polygons"]) != len(wb["carried"]):
        raise SystemExit("REFUSING: water_bodies_1812 carries a polygon the 1834 spec does not have")
    fs["water_polygons"] += [
        {"feature": MOUTH_ID},
        # The spit and neck enter as a body of land the lake rules may not flood. It is
        # written as a water polygon that is wholly its own island because that is the one
        # route build_field has for excluding ground from `open_lake` / `southern_lake`,
        # which run after the polygons; it adds no water.
        {"feature": LAND_ID, "island_rings": [0]},
    ]
    division_of = {s["id"]: s["division"] for s in base["shore_runs"]}
    runs = [s for s in base["shore_runs"] if s["id"] in spec["shore_runs_1812"]["carried"]]
    for old, new in renames.items():
        for r in new:
            if r in ("north_lake_shore_1812",) or r in spec["shore_runs_1812"]["from_shoreline_1812"]:
                runs.append({"id": r, "division": division_of[old]})
    # the neck and spit's waterline: land on it is lifted in step 3, so its division only
    # decides which profile the mainland beside the root is read from - the north shore's
    runs.append({"id": SHORE_ID, "division": division_of["north_shore_harbor_reach"]})
    fs["shore_runs"] = runs

    def renamed(ids):
        out = []
        for r in ids:
            out += renames.get(r, [r])
        return out

    for key in ("southern_lake", "northern_lake"):
        fs[key] = dict(fs[key], shore_runs=renamed(fs[key]["shore_runs"]))
    carries = []
    for cy in fs.get("trace_carries", []):
        if cy["run"] in renames:
            # a carry north to the wall lands on the renamed run that reaches furthest north
            cy = dict(cy, run=NORTH_ID)
        carries.append(cy)
    fs["trace_carries"] = carries
    oc = spec["outlet_channel_1812"]
    fs["reaches"] = list(eff["reaches"]) + [{
        "id": "outlet_channel_1812", "anchor_e": oc["anchor_e"], "anchor_n": oc["anchor_n"],
        "bed_ft": oc["bed_ft"], "e_fold_m": oc["e_fold_m"]}]
    fs["islands"] = []
    # The sand hills south of Twelfth Street (T-2066) are an 1812 reach of the 1834 dune
    # machinery, so they join the carried `dunes` list and build_field lays them exactly as
    # it lays north_lake_dunes. Only the build instructions go in; the block's grade,
    # sources and note stay on the block, where the Evidence panel reads them.
    hills = spec["south_lake_sand_hills_1812"]
    fs["dunes"] = list(fs.get("dunes", [])) + [
        {k: hills[k] for k in SAND_HILL_KEYS if k in hills}]
    for gone in ("approaches", "street_sections"):
        fs.pop(gone, None)
    return fs


# ---------------------------------------------------------------------------
# 3. the field, and the spit lifted onto it
# ---------------------------------------------------------------------------

def micro_relief(E, N, mr):
    """terrain_gen.build_field's micro-relief, term for term, so the spit carries the same
    texture as the ground it joins."""
    amp = float(mr.get("amplitude_ft", 0.0))
    micro = np.zeros(E.shape)
    if amp > 0:
        waves = mr.get("wavelengths_m", [50.0])
        seed = int(mr.get("seed", 1))
        for k, wl in enumerate(waves):
            micro += tg.value_noise(E, N, float(wl), seed + 977 * k) / (k + 1)
        micro *= amp / max(1e-9, sum(1.0 / (k + 1) for k in range(len(waves))))
        if mr.get("south_limit_n_m") is not None:
            micro = np.where(N < float(mr["south_limit_n_m"]), 0.0, micro)
    return micro


def build(spec, base):
    datum = load(ROOT / "data" / "datum.json")
    origin = (datum["origin_utm_e"], datum["origin_utm_n"])
    feats = {}
    for name in BASE_VECTORS:
        for f in load(BASE_DIR / name)["features"]:
            feats[f["id"]] = f
    shore12 = spec_shore(spec)
    geo = derive_mouth(feats, shore12, spec, origin)
    river = mouth_geojson(geo, spec, origin)
    for f in shore12["features"]:
        feats[f["id"]] = f
    for f in river["features"]:
        feats[f["id"]] = f
    # The north bank is read to where the neck's south-west face leaves it. Read to its
    # last vertex - the spit root, which is mid-neck - it would stand a waterline in the
    # middle of the isthmus and notch it to the water plane.
    feats["north_shore_pre_cut_1812"] = dict(
        feats["north_shore_pre_cut_1812"],
        geometry={"type": "LineString", "coordinates": to_utm(geo["bank_cut"], origin)})

    eff = resolve(spec, base)
    fs = field_spec(spec, base, eff)
    h_m, conf, water, meta, geom = tg.build_field(fs, feats, origin, None)
    E, N = geom["E"], geom["N"]

    # the spit and the neck, at the spit's crest across the spit's face
    sp, isth = spec["spit_1812"], spec["isthmus_1812"]
    if isth["decision"] != "surfaced":
        raise SystemExit("REFUSING: isthmus_1812 is not surfaced, and this generator only builds "
                         "the surfaced neck")
    land = tg.point_in_ring(E, N, geo["land"]) & ~water
    crest_ft, face_m = float(sp["crest_ft"]), float(sp["face_m"])
    if float(isth["crest_ft"]) != crest_ft or float(isth["face_m"]) != face_m:
        raise SystemExit("REFUSING: the neck and the spit state different surfaces; this generator "
                         "lays one, and check_terrain_e1830.py says why they must agree")
    t_bank = np.clip(geom["d_land"] / face_m, 0.0, 1.0)
    ramp = 1.0 - (1.0 - t_bank) ** 2
    spit_ft = (crest_ft + micro_relief(E, N, eff.get("micro_relief", {}))) * ramp
    # Where the neck meets the mainland it grades into the ground already there across the
    # neck's own width, rather than standing as a step against the beach ridge it joins.
    d_root = tg.seg_distance(E, N, geo["root_line"])
    w = tg.smoothstep(np.clip(d_root / (2.0 * geo["half_m"]), 0.0, 1.0))
    h_ft = h_m / FT
    h_ft = np.where(land, w * spit_ft + (1.0 - w) * h_ft, h_ft)
    conf = np.where(land, tg.CONF_CONJECTURAL, conf)
    geom["bands"]["spit_1812"] = land

    # channel_west_bank_ruling: undecided, so the channel, its bank and the ground within
    # Harrison's worst separation west of it are emitted at the lowest grade, between the
    # adopted outlet and his old mouth.
    rule = spec["channel_west_bank_ruling"]
    if rule["verdict"] == "undecided" and rule["ground_confidence"] == "conjectural":
        lo, hi = sorted(float(v) for v in rule["band_n_m"])
        bank_run = to_local(feats[rule["bank_run"]]["geometry"]["coordinates"], origin)
        sel = (N[:, 0] >= lo) & (N[:, 0] <= hi)
        bank_e = np.full(N.shape[0], np.nan)
        for (x1, y1), (x2, y2) in zip(bank_run, bank_run[1:]):
            if y1 == y2:
                continue
            a, b = min(y1, y2), max(y1, y2)
            rows = sel & (N[:, 0] >= a) & (N[:, 0] <= b)
            tt = (N[rows, 0] - y1) / (y2 - y1)
            bank_e[rows] = np.fmin(bank_e[rows], x1 + tt * (x2 - x1))
        # From the bank's westmost crossing of the row, west by Harrison's worst separation,
        # east across the channel to the spit's west face.
        sep = float(rule["west_band_m"])
        spit_w = np.where(land & (E > np.nan_to_num(bank_e, nan=np.inf)[:, None]), E, np.inf).min(axis=1)
        band = (sel[:, None] & np.isfinite(bank_e)[:, None] & np.isfinite(spit_w)[:, None]
                & (E >= (bank_e - sep)[:, None]) & (E < spit_w[:, None]))
        conf = np.where(band, tg.CONF_CONJECTURAL, conf)
        geom["bands"]["channel_west_bank_ruling"] = band

    h_m = h_ft * FT
    meta.update({
        "min_m": float(h_m.min()), "max_m": float(h_m.max()),
        "land_min_ft": float(h_ft[~water].min()), "land_max_ft": float(h_ft[~water].max()),
    })
    audit = tg.gradient_audit(h_m, water, geom, fs)
    audit["rule"] = ("docs/research/01-terrain-hydrology.md modelling rule 1: outside the zones "
                     "that earn relief, hold local gradients under 0.5 ft per 300 ft")
    meta["gradient_audit"] = audit
    g = fs["grid"]
    margin, k = tg.skirt_margin_m(max(float(g["e_max_m"]) - float(g["e_min_m"]),
                                      float(g["n_max_m"]) - float(g["n_min_m"])), float(g["cell_m"]))
    rung = float(g["cell_m"]) / k
    meta["skirt"] = {
        "_doc": "The apron outside the modelled box; see generators/terrain_gen.skirt_terminations "
                "and T-0939. The 1812 ground uses the 1834 box and the 1834 apron rule.",
        "margin_m": round(margin, 6), "position_rung_m": round(rung, 9),
        "terminations": tg.skirt_terminations(fs, feats, origin, h_m, rung),
    }
    stats = {
        "land_cells": int(land.sum()), "spit_crest_ft": crest_ft,
        "river_side_offset_m": round(geo["half_m"], 3),
        "conjectural_share": float((conf == tg.CONF_CONJECTURAL).mean()),
        "documented_cells": int((conf == tg.CONF_DOCUMENTED).sum()),
    }
    return river, h_m, conf, water, meta, fs, stats


def write_outputs(out_dir: Path, river, h_m, meta, fs, sha):
    (out_dir / OUT_NAME).write_text(json.dumps(river, indent=1) + "\n")
    doc = tg.write_heightfield(out_dir, h_m, meta, fs, sha)
    doc["_doc"] = ("Runtime heightfield meta for terrain epoch e1830_natural, the ground of "
                   "1812-08-15. Row 0 is the SOUTH edge and column 0 the WEST edge; the sample at "
                   "[0][0] sits exactly on (origin_e, origin_n) in local ENU metres from "
                   "data/datum.json. Elevation in metres above the summer-1835 water surface, at "
                   "which lake_stage_1812 stands the 1812 lake: y = raw * scale + offset. GENERATED "
                   "by generators/terrain_gen_e1830.py - do not hand-edit.")
    (out_dir / "heightfield.json").write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", action="store_true", help="also build the GLBs (needs Blender)")
    ap.add_argument("--check", action="store_true",
                    help="re-derive river.geojson and the heightfield and compare with the committed bytes")
    ap.add_argument("--decimate-deg", type=float, default=0.03)
    ap.add_argument("--out", default=str(ROOT / "assets" / "gltf"))
    args = ap.parse_args(tg.argv_after_ddash())
    if np is None:
        print("REFUSING: numpy is required")
        return 2
    spec = load(EP_DIR / "terrain_spec.json")
    base = load(BASE_DIR / "terrain_spec.json")
    river, h_m, conf, water, meta, fs, stats = build(spec, base)
    import terrain_inputs  # noqa: PLC0415

    names = (OUT_NAME, "heightfield.json", "heightfield.bin")
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            # the hash covers river.geojson, so it is taken over the re-derived one
            for n in ("terrain_spec.json", "shoreline.geojson"):
                (Path(tmp) / n).write_bytes((EP_DIR / n).read_bytes())
            (Path(tmp) / OUT_NAME).write_text(json.dumps(river, indent=1) + "\n")
            sha = terrain_inputs.terrain_inputs_sha(Path(tmp), epoch=EPOCH)
            write_outputs(Path(tmp), river, h_m, meta, fs, sha)
            bad = [n for n in names
                   if not (EP_DIR / n).exists() or (Path(tmp) / n).read_bytes() != (EP_DIR / n).read_bytes()]
        print("OK the 1812 mouth and heightfield re-derive byte for byte from the e1830_natural "
              "overlay and the 1834 trace" if not bad else
              f"FAIL {', '.join(bad)} is not what the e1830_natural overlay derives; re-run "
              f"generators/terrain_gen_e1830.py and re-bake the meshes under Blender with --glb")
        return 0 if not bad else 1
    (EP_DIR / OUT_NAME).write_text(json.dumps(river, indent=1) + "\n")
    sha = terrain_inputs.terrain_inputs_sha(EP_DIR)
    doc = write_outputs(EP_DIR, river, h_m, meta, fs, sha)
    print(f"grid {doc['cols']}x{doc['rows']} @ {doc['cell_m']} m; land {doc['relief_ft']['land_min']}.."
          f"{doc['relief_ft']['land_max']} ft; channel floor {doc['relief_ft']['channel_min']} ft; water "
          f"{100 * doc['water_fraction']:.1f}%; quantisation {doc['quantisation_error_m'] * 1000:.2f} mm")
    print(f"spit and neck: {stats['land_cells']} cells at +{stats['spit_crest_ft']} ft, river-side offset "
          f"{stats['river_side_offset_m']} m; conjectural {100 * stats['conjectural_share']:.1f}% of the box; "
          f"documented vertices {stats['documented_cells']}")
    ga = meta["gradient_audit"]
    print(f"gradient audit: plain max {ga['plain_block_max']} ft - "
          f"{'PASS' if ga['passes'] else 'OVER THE 0.5 RULE'}")
    if not args.glb:
        print("\nheightfield only; re-run under Blender with --glb for the meshes")
        return 0
    if not tg.HAVE_BPY:
        print("--glb needs Blender")
        return 2
    built = tg.build_meshes(h_m, conf, fs, EPOCH, Path(args.out), args.decimate_deg,
                            meta["skirt"]["terminations"])
    import bpy  # noqa: PLC0415
    from mesh_inputs import SCHEME  # noqa: PLC0415
    manifest_path = ROOT / "assets" / "manifest.json"
    manifest = load(manifest_path)
    manifest["inputs_scheme"] = SCHEME
    for b in built:
        pth = b["path"]
        manifest["assets"][pth.name] = {
            "kind": "generated", "generator": "generators/terrain_gen_e1830.py", "terrain_epoch": EPOCH,
            "layer": "water" if pth.name.startswith("water__") else "ground", "inputs_sha256": sha,
            "bytes": pth.stat().st_size, "triangles": b["tris"],
            **({"mesh_vs_heightfield": b["fit"]} if "fit" in b else {}), "baked_ao": False,
        }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"manifest updated: {len(built)} terrain asset(s) (blender {bpy.app.version_string})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
