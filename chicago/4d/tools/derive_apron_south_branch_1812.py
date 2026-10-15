"""The 1812 ground carried down the South Branch to Lee's Place: an apron sampler (T-2502).

    python3 tools/derive_apron_south_branch_1812.py            # write the apron
    python3 tools/derive_apron_south_branch_1812.py --check    # re-derive, compare, write nothing
    python3 tools/derive_apron_south_branch_1812.py --self-test

T-2502, piece 2 of 3 of T-2488. T-2501 traced the South Branch off Rees & Rucker 1849 from
the box floor to the forks and ruled Lee's Place a reach of its north-west bank, about
930 m west of the e1830_natural box and 450 m south of it. Out there the renderer had
nothing to stand on: `Heightfield.sample()` answered its 0 m constant, and the drawn ground
was the box's south-west corner carried outward flat at 1.31 m with the floor's last
channel section extruded due south as a straight trench.

WHY AN APRON AND NOT A WIDER BOX. Widening e1830_natural would regenerate the 1812 ground
on a grid that is not the 1834 one, and the 1834 field's arithmetic is the whole of that
ground (generators/terrain_gen_e1830.py runs `build_field` on the 1834 grid). West of
E -705 that arithmetic runs past the tracing window: the main stem's and the branches'
water polygons stop at the box wall, so a box carried west to the site would draw them
ending in a bank there. It would also double a 3.8 MB field the 1812 scene loads whole,
and the meshes would need a full Blender bake. So the box is left byte for byte as it is,
and the ground to the site is a SECOND, small field the 1812 scene loads beside it, the
way 1904's `contextCoast` stands beside Prairie Avenue's. Outside the box the renderer's
sampler consults it before falling back (renderers/web/js/terrain.js § Heightfield).

WHAT THE APRON'S GROUND IS, and none of it is a new claim:

* LAND is the box's own floor row carried, which is what the drawn apron already showed
  there: south of `evidence_limit` the 1812 field is one evidenced row carried south
  (T-0464), and the skirt carries the box's boundary outward at its own height. Across
  the floor's channel the row is bridged straight from bank crest to bank crest, so the
  trench is not carried a second time.
* WATER AND BANKS follow T-2501's trace, joined to the committed reach above it
  (`south_branch_below_twelfth`, Rees 1849) where the two abut below the box floor. The
  channel is cut with the 1834 field's own cross-section (terrain_spec `channel_profile`:
  depth = bed * (1 - exp(-d_in / e_fold))) to the bed the committed reach reaches at the
  floor, and the bank rises over the spec's `bank.face_m` with its ease-out ramp.
* EVERY SAMPLE IS CONJECTURAL, the grade of every vertex south of `evidence_limit`.
* AT ITS EDGES it is the ground beside it: the north row is the box's floor row itself,
  the west and east columns are the carried 1.31 m the apron there already stands at, and
  the south row is carried on south to the apron's outer edge (`skirt_to_n_m`) by the
  renderer, exactly as the box's own skirt carries its floor. The channel leaves through
  the south row, below the ruled reach and short of the forks, so the river runs on past
  the edge of the drawn ground rather than ending in a bank.

The renderer cuts the box's own apron out over `cut_local_enu_m` (terrain.js, the T-2474
ground cut) and draws this field there instead, so the two never stand over each other.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / "generators", ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import terrain_gen as tg  # noqa: E402

EPOCH = "e1830_natural"
EP_DIR = ROOT / "data" / "terrain" / "epochs" / EPOCH
BASE_DIR = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
TRACE = ROOT / "data" / "terrain" / "1812_south_branch_to_bridgeport.geojson"
COMMITTED = BASE_DIR / "south_branch_below_twelfth.geojson"
SITE = ROOT / "data" / "terrain" / "1812_hardscrabble_site.json"
OUT_META = EP_DIR / "apron_south_branch.json"
OUT_BIN = EP_DIR / "apron_south_branch.bin"

# The apron's rectangle, local ENU metres. North is the box floor; west and south take in
# the whole of T-2501's ruled reach with room for the farm T-2503 builds on it; east stops
# where the floor row is back on its carried 1.31 m, past the channel's east bank.
E_MIN, E_MAX = -2200.0, -100.0
N_MIN, N_MAX = -4600.0, -3800.0
CELL_M = 5.0
SCALE_M = 0.005
# Over this many metres from the north row the cut channel is blended onto the box's own
# floor row, so the two surfaces meet sample for sample.
NORTH_BLEND_M = 25.0


def load(p: Path):
    return json.loads(p.read_text())


def local(coords, origin):
    return [(float(x) - origin[0], float(y) - origin[1]) for x, y in coords]


def spec_limit_n(base_spec):
    lim = base_spec["evidence_limit"]["south_of_n_m"]
    if not float(lim) > N_MAX:
        raise SystemExit("REFUSING: evidence_limit no longer lies north of the apron")
    return lim


def core_field():
    meta = load(EP_DIR / "heightfield.json")
    raw = np.fromfile(EP_DIR / meta["bin"], dtype="<i2").reshape(meta["rows"], meta["cols"])
    return meta, raw.astype(np.float64) * float(meta["scale"]) + float(meta.get("offset", 0.0))


def banks(origin):
    """West (north-west) and east (south-east) banks, box to forks, as one line each."""
    trace = {f["id"]: f for f in load(TRACE)["features"]}
    above = {f["id"]: f for f in load(COMMITTED)["features"]}
    nw = local(trace["south_branch_to_forks_nw_bank"]["geometry"]["coordinates"], origin)
    se = local(trace["south_branch_to_forks_se_bank"]["geometry"]["coordinates"], origin)
    w_up = local(above["south_branch_west_bank_below_twelfth"]["geometry"]["coordinates"], origin)
    e_up = local(above["south_branch_east_bank_below_twelfth"]["geometry"]["coordinates"], origin)
    # The committed reach runs 40-50 m past the floor and T-2501 starts on its last
    # centreline vertex, so the two overlap there: each bank keeps the committed vertices
    # north of the trace's first, then the trace.
    west = [p for p in w_up if p[1] > nw[0][1]] + nw
    east = [p for p in e_up if p[1] > se[0][1]] + se
    return west, east


def derive():
    datum = load(ROOT / "data" / "datum.json")
    origin = (datum["origin_utm_e"], datum["origin_utm_n"])
    base_spec = load(BASE_DIR / "terrain_spec.json")
    face_m = float(base_spec["bank"]["face_m"])
    e_fold_m = float(base_spec["channel_profile"]["e_fold_m"])
    meta, core = core_field()
    c_e0, c_n0, c_cell = float(meta["origin_e"]), float(meta["origin_n"]), float(meta["cell_m"])
    if abs(c_n0 - N_MAX) > 1e-9:
        raise SystemExit(f"REFUSING: the box floor moved to N {c_n0}; the apron's north row "
                         f"is written against N {N_MAX}")
    west, east = banks(origin)

    # ---- the floor row, and the land carried from it --------------------------------
    row0 = core[0]
    core_e = c_e0 + np.arange(core.shape[1]) * c_cell

    def bank_e_at(line, n):
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            if (y1 - n) * (y2 - n) <= 0 and y1 != y2:
                return x1 + (n - y1) / (y2 - y1) * (x2 - x1)
        raise SystemExit(f"REFUSING: a bank does not cross the box floor at N {n}")

    w_floor, e_floor = bank_e_at(west, N_MAX), bank_e_at(east, N_MAX)
    lo_e, hi_e = min(w_floor, e_floor) - face_m - c_cell, max(w_floor, e_floor) + face_m + c_cell
    lo_c = int(math.floor((lo_e - c_e0) / c_cell))
    hi_c = int(math.ceil((hi_e - c_e0) / c_cell))
    land_row = row0.copy()
    land_row[lo_c:hi_c + 1] = np.linspace(row0[lo_c], row0[hi_c], hi_c - lo_c + 1)
    # The channel's bed where the committed reach leaves the box: its deepest sample in
    # the last 100 m of the box, inside the floor's channel window.
    tail = core[: int(round(100.0 / c_cell)) + 1, lo_c:hi_c + 1]
    bed_m = float(tail.min())
    if not bed_m < 0:
        raise SystemExit("REFUSING: no channel below the water surface at the box floor")

    # ---- the grid -------------------------------------------------------------------
    cols = int(round((E_MAX - E_MIN) / CELL_M)) + 1
    rows = int(round((N_MAX - N_MIN) / CELL_M)) + 1
    E1 = E_MIN + np.arange(cols) * CELL_M
    N1 = N_MIN + np.arange(rows) * CELL_M
    E, N = np.meshgrid(E1, N1)
    land = np.interp(np.clip(E1, core_e[0], core_e[-1]), core_e, land_row)[None, :] * np.ones((rows, 1))

    ring = west + east[::-1]
    water = tg.point_in_ring(E, N, ring)
    d_bank = np.minimum(tg.seg_distance(E, N, west), tg.seg_distance(E, N, east))
    t = np.clip(d_bank / face_m, 0.0, 1.0)
    h = np.where(water, bed_m * (1.0 - np.exp(-d_bank / e_fold_m)), land * (1.0 - (1.0 - t) ** 2))

    # ---- the north row is the floor row --------------------------------------------
    floor_here = np.interp(np.clip(E1, core_e[0], core_e[-1]), core_e, row0)
    s = tg.smoothstep(np.clip((N_MAX - N) / NORTH_BLEND_M, 0.0, 1.0))
    h = s * h + (1.0 - s) * floor_here[None, :]

    q = np.round(h / SCALE_M)
    if q.min() < -32768 or q.max() > 32767:
        raise SystemExit("REFUSING: the apron does not fit int16 at the 5 mm step")
    q = q.astype("<i2")
    hq = q.astype(np.float64) * SCALE_M

    # ---- what it says about itself --------------------------------------------------
    site = load(SITE)["site"]
    reach = site["reach_nw_bank_local"]
    inside = lambda e, n: E_MIN <= e <= E_MAX and N_MIN <= n <= N_MAX  # noqa: E731
    if not all(inside(e, n) for e, n in reach):
        raise SystemExit("REFUSING: T-2501's ruled reach leaves the apron")
    south_wet = E1[hq[0] < 0]
    if not len(south_wet):
        raise SystemExit("REFUSING: the channel does not leave through the apron's south row")
    for side, col in (("west", hq[:, 0]), ("east", hq[:, -1])):
        if (col < 0).any():
            raise SystemExit(f"REFUSING: the channel crosses the apron's {side} column, where "
                             "the ground beside it is carried flat")
    margin = float(meta["skirt"]["margin_m"])
    sx, sy = site["local"]
    gx, gy = (sx - E_MIN) / CELL_M, (sy - N_MIN) / CELL_M
    i, j = int(gx), int(gy)
    fx, fy = gx - i, gy - j
    at_site = ((hq[j, i] * (1 - fx) + hq[j, i + 1] * fx) * (1 - fy)
               + (hq[j + 1, i] * (1 - fx) + hq[j + 1, i + 1] * fx) * fy)

    doc = {
        "_doc": "GENERATED by tools/derive_apron_south_branch_1812.py (T-2502) - do not hand-edit; "
                "--check re-derives it. A second heightfield the 1812 scene loads beside "
                "e1830_natural's box: the ground carried down the South Branch from the box floor "
                "to Lee's Place (T-2501's ruled reach). Same layout as heightfield.json: row 0 is "
                "the SOUTH edge, column 0 the WEST edge, the sample at [0][0] on (origin_e, "
                "origin_n), y = raw * scale + offset in metres above the 1812 water surface. "
                "renderers/web/js/terrain.js samples it outside the box, cuts the box's own apron "
                "out over cut_local_enu_m and draws this there, its south row carried on to "
                "skirt_to_n_m. Every sample is conjectural. See the tool's docstring.",
        "epoch": EPOCH,
        "ticket": "T-2502",
        "parent": "T-2488",
        "bin": OUT_BIN.name,
        "encoding": "int16",
        "scale": SCALE_M,
        "offset": 0.0,
        "cols": cols,
        "rows": rows,
        "cell_m": CELL_M,
        "origin_e": E_MIN,
        "origin_n": N_MIN,
        "box_local_enu_m": {"e": [E_MIN, E_MAX], "n": [N_MIN, N_MAX]},
        "cut_local_enu_m": {"e": [E_MIN, E_MAX], "n": [round(N_MAX - margin, 6), N_MAX]},
        "skirt_to_n_m": round(N_MAX - margin, 6),
        "confidence": "conjectural",
        "sources": ["rees_rucker_1849"],
        "inputs": {
            "box": f"data/terrain/epochs/{EPOCH}/heightfield.json",
            "trace": "data/terrain/1812_south_branch_to_bridgeport.geojson",
            "reach_above": "data/terrain/epochs/e1834_harbor_cut/south_branch_below_twelfth.geojson",
            "site": "data/terrain/1812_hardscrabble_site.json",
        },
        "ground": {
            "land_m": round(float(land[0, 0]), 4),
            "land_note": "The box's floor row carried: what the apron already stood at here. "
                         "Across the floor's channel window (E %.1f..%.1f) the row is bridged "
                         "straight from crest to crest, so the trench is not carried twice."
                         % (core_e[lo_c], core_e[hi_c]),
            "bed_m": round(bed_m, 4),
            "bed_note": "The committed reach's deepest sample in the box's last 100 m, inside the "
                        "floor's channel window: the channel is carried at the depth it leaves the "
                        "box with, and no source gives it a different one.",
            "e_fold_m": e_fold_m,
            "bank_face_m": face_m,
            "profile_note": "terrain_spec channel_profile and bank, the 1834 field's own "
                            "cross-section: depth = bed * (1 - exp(-d_in / e_fold)) inside the "
                            "banks, land * (1 - (1 - d / face)^2) outside them.",
            "north_blend_m": NORTH_BLEND_M,
            "confidence_note": "Every sample lies south of the 1812 field's evidence_limit "
                               "(N %.1f), where every vertex is conjectural; so is every "
                               "sample here." % float(spec_limit_n(base_spec)),
        },
        "measured": {
            "min_m": round(float(hq.min()), 4),
            "max_m": round(float(hq.max()), 4),
            "water_fraction": round(float((hq < 0).mean()), 4),
            "channel_leaves_south_row_e": [round(float(south_wet.min()), 2),
                                           round(float(south_wet.max()), 2)],
            "site_local": [round(sx, 2), round(sy, 2)],
            "ground_at_site_m": round(float(at_site), 4),
            "reach_ground_min_m": round(float(min(
                hq[int(round((n - N_MIN) / CELL_M)), int(round((e - E_MIN) / CELL_M))]
                for e, n in reach)), 4),
        },
    }
    return doc, q


def write(doc, q, meta_path=OUT_META, bin_path=OUT_BIN):
    meta_path.write_text(json.dumps(doc, indent=1) + "\n")
    bin_path.write_bytes(q.tobytes())


def self_test() -> bool:
    fails = []

    def ok(name, cond):
        if not cond:
            fails.append(name)

    doc, q = derive()
    hq = q.astype(np.float64) * doc["scale"]
    meta, core = core_field()
    step = int(round(doc["cell_m"] / meta["cell_m"]))
    c0 = int(round((max(doc["origin_e"], meta["origin_e"]) - meta["origin_e"]) / meta["cell_m"]))
    p0 = int(round((meta["origin_e"] - doc["origin_e"]) / doc["cell_m"]))
    ok("the north row is the box's floor row where they share an easting",
       np.abs(hq[-1, p0:] - core[0, c0::step][: hq.shape[1] - p0]).max() <= doc["scale"])
    ok("the west and east columns stand at the carried land", np.abs(hq[:, 0] - doc["ground"]["land_m"]).max()
       <= doc["scale"] and np.abs(hq[:, -1] - doc["ground"]["land_m"]).max() <= doc["scale"])
    # T-2501's station is ON the north-west bank, so it is the waterline: at or above the
    # water surface, and never the 1.3 m under the drawn ground the flat apron left it.
    ok("the site's bank point is at or above the water surface", doc["measured"]["ground_at_site_m"] >= 0.0)
    ok("the land behind the bank stands at the carried height",
       abs(doc["ground"]["land_m"] - float(core[0, 0])) <= doc["scale"])
    ok("there is a channel below the water surface", doc["measured"]["water_fraction"] > 0.01)
    ok("no sample is below the bed", hq.min() >= doc["ground"]["bed_m"] - doc["scale"])
    for name in fails:
        print(f"FAIL  {name}")
    print("derive_apron_south_branch_1812 self-test: " + (f"{len(fails)} failure(s)" if fails
                                                          else "all rules hold"))
    return not fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="re-derive and compare, writing nothing")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return 0 if self_test() else 1
    doc, q = derive()
    if a.check:
        want_meta = json.dumps(doc, indent=1) + "\n"
        bad = []
        if not OUT_META.exists() or OUT_META.read_text() != want_meta:
            bad.append(OUT_META.name)
        if not OUT_BIN.exists() or OUT_BIN.read_bytes() != q.tobytes():
            bad.append(OUT_BIN.name)
        if bad:
            print(f"FAIL {', '.join(bad)} is not what the box floor, T-2501's trace and the reach "
                  "above it derive; re-run tools/derive_apron_south_branch_1812.py")
            return 1
        m = doc["measured"]
        print(f"OK the South Branch apron re-derives byte for byte: {doc['cols']}x{doc['rows']} at "
              f"{doc['cell_m']} m, ground at the site {m['ground_at_site_m']} m, water "
              f"{100 * m['water_fraction']:.1f}%")
        return 0
    write(doc, q)
    m = doc["measured"]
    print(f"wrote {OUT_META.relative_to(ROOT)} + .bin: {doc['cols']}x{doc['rows']} at {doc['cell_m']} m; "
          f"land {doc['ground']['land_m']} m, bed {doc['ground']['bed_m']} m; water "
          f"{100 * m['water_fraction']:.1f}%; channel leaves the south row at E "
          f"{m['channel_leaves_south_row_e']}; ground at the site {m['ground_at_site_m']} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
